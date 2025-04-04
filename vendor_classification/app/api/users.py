# app/api/users.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any
import uuid

from core.database import get_db
from schemas.user import UserCreate, UserUpdate, UserResponse
from services import user_service
from api.auth import get_current_active_user, get_current_active_superuser
from models.user import User as UserModel # Import the model for type hinting
from core.logging_config import get_logger, set_log_context

logger = get_logger("vendor_classification.api.users")

router = APIRouter()

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
    current_user: UserModel = Depends(get_current_active_superuser) # Require admin
):
    """
    Create new user. Requires superuser privileges.
    """
    set_log_context({"admin_user": current_user.username})
    logger.info(f"Admin '{current_user.username}' attempting to create user '{user_in.username}'")
    # Service layer handles potential duplicate username/email via HTTPException
    user = user_service.create_user(db=db, user_in=user_in)
    logger.info(f"User '{user.username}' created successfully by admin '{current_user.username}'")
    return user

@router.get("/", response_model=List[UserResponse])
def read_users(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    current_user: UserModel = Depends(get_current_active_superuser) # Require admin
):
    """
    Retrieve users. Requires superuser privileges.
    """
    set_log_context({"admin_user": current_user.username})
    logger.info(f"Admin '{current_user.username}' requesting user list", extra={"skip": skip, "limit": limit})
    users = user_service.get_users(db, skip=skip, limit=limit)
    logger.info(f"Returning {len(users)} users to admin '{current_user.username}'")
    return users

@router.get("/me", response_model=UserResponse)
def read_user_me(
    current_user: UserModel = Depends(get_current_active_user) # Just need active user
):
    """
    Get current user details.
    """
    set_log_context({"requesting_user": current_user.username})
    logger.info(f"User '{current_user.username}' requesting their own details.")
    # The dependency already fetches the user object
    return current_user

@router.get("/{user_id}", response_model=UserResponse)
def read_user_by_id(
    user_id: str,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific user by ID. Requires admin privileges or the user themselves.
    """
    set_log_context({"requesting_user": current_user.username, "target_user_id": user_id})
    logger.info(f"User '{current_user.username}' requesting details for user ID '{user_id}'")
    user = user_service.get_user(db, user_id=user_id)
    if not user:
        logger.warning(f"Target user not found", extra={"target_user_id": user_id})
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Check permissions
    if user.id != current_user.id and not current_user.is_superuser:
        logger.warning(f"Authorization failed: User '{current_user.username}' cannot access details for user '{user.username}'")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    logger.info(f"Returning details for user '{user.username}'")
    return user

@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    *,
    db: Session = Depends(get_db),
    user_id: str,
    user_in: UserUpdate,
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Update a user. Requires admin privileges or the user themselves.
    Non-admins cannot change their own is_superuser status or activate/deactivate themselves.
    """
    set_log_context({"requesting_user": current_user.username, "target_user_id": user_id})
    logger.info(f"User '{current_user.username}' attempting to update user ID '{user_id}'")
    db_user = user_service.get_user(db, user_id=user_id)
    if not db_user:
        logger.warning(f"Target user not found for update", extra={"target_user_id": user_id})
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Check permissions
    if db_user.id != current_user.id and not current_user.is_superuser:
        logger.warning(f"Authorization failed: User '{current_user.username}' cannot update user '{db_user.username}'")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions to update this user")

    # Non-admins cannot make themselves superuser or change their active status
    if not current_user.is_superuser:
        if user_in.is_superuser is not None and user_in.is_superuser != db_user.is_superuser:
                logger.warning(f"User '{current_user.username}' attempted to change their own superuser status.")
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot change superuser status")
        if user_in.is_active is not None and user_in.is_active != db_user.is_active:
                logger.warning(f"User '{current_user.username}' attempted to change their own active status.")
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot change own active status")

    # Service layer handles update logic and potential integrity errors
    updated_user = user_service.update_user(db=db, user_id=user_id, user_in=user_in)
    if not updated_user: # Should be handled by service, but double check
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found after update attempt")

    logger.info(f"User '{db_user.username}' updated successfully by '{current_user.username}'")
    return updated_user


@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
def delete_user(
    *,
    db: Session = Depends(get_db),
    user_id: str,
    current_user: UserModel = Depends(get_current_active_superuser) # Require admin
):
    """
    Delete a user. Requires superuser privileges.
    """
    set_log_context({"admin_user": current_user.username, "target_user_id": user_id})
    logger.info(f"Admin '{current_user.username}' attempting to delete user ID '{user_id}'")

    # Prevent admin from deleting themselves?
    if str(current_user.id) == user_id:
            logger.error(f"Admin '{current_user.username}' attempted to delete themselves.")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins cannot delete themselves.")

    deleted = user_service.delete_user(db=db, user_id=user_id)
    if not deleted:
        # Service layer already logged warning
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    logger.info(f"User ID '{user_id}' deleted successfully by admin '{current_user.username}'")
    return {"message": "User deleted successfully"}
