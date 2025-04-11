# <file path='app/api/password_reset.py'>
# app/api/password_reset.py
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Any

from core.database import get_db
from core.config import settings
from core.logging_config import get_logger
from schemas.password_reset import PasswordRecoveryRequest, PasswordResetRequest, MessageResponse
from services import user_service
from services import email_service
from api import auth as auth_service # Renamed import for clarity
from models.user import User as UserModel

logger = get_logger("vendor_classification.api.password_reset")

router = APIRouter()

@router.post(
    "/password-recovery",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK # Return 200 even if user not found to prevent email enumeration
)
async def request_password_recovery(
    recovery_data: PasswordRecoveryRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> Any:
    """
    Initiates the password recovery process for a user based on their email.
    Sends an email with a password reset link if the user exists.
    Always returns a success message to prevent user enumeration.
    """
    email = recovery_data.email
    logger.info(f"Password recovery requested", extra={"email": email})

    user = user_service.get_user_by_email(db, email=email)

    if not user:
        # IMPORTANT: Do not reveal that the user doesn't exist.
        logger.warning(f"Password recovery requested for non-existent email", extra={"email": email})
        # Still return a success-like message.
        return MessageResponse(message="If an account with that email exists, a password reset link has been sent.")

    if not user.is_active:
        logger.warning(f"Password recovery requested for inactive user", extra={"email": email, "username": user.username})
        # You might choose to prevent inactive users from resetting, or allow it.
        # Let's prevent it for now.
        # Still return the generic success message.
        return MessageResponse(message="If an account with that email exists and is active, a password reset link has been sent.")

    # Generate the password reset token
    password_reset_token = auth_service.create_password_reset_token(subject=user.id) # Use user ID as subject

    # Send email in the background
    background_tasks.add_task(
        email_service.send_password_reset_email,
        email_to=user.email,
        username=user.username,
        token=password_reset_token
    )
    logger.info(f"Password recovery email task added to background", extra={"email": email, "username": user.username})

    return MessageResponse(message="If an account with that email exists and is active, a password reset link has been sent.")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    reset_data: PasswordResetRequest,
    db: Session = Depends(get_db)
) -> Any:
    """
    Resets the user's password using a valid token.
    """
    token = reset_data.token
    new_password = reset_data.new_password
    logger.info(f"Attempting password reset with token", extra={"token_preview": token[:10]+"..."})

    try:
        # Verify the token and get the user ID
        user_id = auth_service.verify_password_reset_token(token)
        if not user_id:
            # This case should be caught by JWTError, but double-check
            logger.warning("Password reset token verification failed (no user_id returned)", extra={"token_preview": token[:10]+"..."})
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired password reset token.",
            )

        logger.info(f"Password reset token verified successfully", extra={"user_id": user_id})

        # Use the user service to update the password
        success = user_service.reset_password(db=db, user_id=user_id, new_password=new_password)

        if not success:
            # This might happen if the user was deleted between token generation and reset attempt
            logger.error(f"Failed to reset password: User not found after token verification", extra={"user_id": user_id})
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        logger.info(f"Password reset successful", extra={"user_id": user_id})
        return MessageResponse(message="Password has been reset successfully.")

    except HTTPException as http_exc:
        # Re-raise known HTTP exceptions (like 400 from verify_password_reset_token)
        raise http_exc
    except Exception as e:
        # Catch unexpected errors during the process
        logger.error(f"Unexpected error during password reset", exc_info=True, extra={"token_preview": token[:10]+"..."})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while resetting the password."
        )
