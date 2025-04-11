# <file path='app/api/auth.py'>

# app/api/auth.py
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone # Added timezone
from typing import Optional, Dict, Any # Added Dict, Any
import uuid

from core.config import settings
# Import logger and context functions from refactored modules
from core.logging_config import get_logger
from core.log_context import set_user, get_user, get_correlation_id
# Import log helpers from utils
from utils.log_utils import LogTimer, log_function_call

from models.user import User
from core.database import get_db

# Configure logging using our custom logger
logger = get_logger("vendor_classification.auth")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- Constants ---
PASSWORD_RESET_TOKEN_TYPE = "password_reset"
ACCESS_TOKEN_TYPE = "access"

@log_function_call(logger, include_args=False) # Don't log passwords
def verify_password(plain_password, hashed_password):
    """Verify password against hashed version."""
    try:
        with LogTimer(logger, "Password verification", include_in_stats=True):
            hash_prefix = hashed_password[:5] if hashed_password else None
            logger.debug(f"Verifying password", extra={"hash_prefix": hash_prefix})
            result = pwd_context.verify(plain_password, hashed_password)
            logger.debug(f"Password verification result", extra={"result": result})
            return result
    except Exception as e:
        logger.error(f"Password verification error: {type(e).__name__}", exc_info=False)
        return False

@log_function_call(logger, include_args=False) # Don't log password
def get_password_hash(password):
    """Generate password hash."""
    try:
        with LogTimer(logger, "Password hashing", include_in_stats=True):
            hashed = pwd_context.hash(password)
            logger.debug(f"Generated password hash", extra={"hash_prefix": hashed[:5] if hashed else None})
            return hashed
    except Exception as e:
        logger.error(f"Password hashing error", exc_info=True)
        raise

@log_function_call(logger, include_args=False) # Don't log password
def authenticate_user(db, username: str, password: str):
    """Authenticate user."""
    try:
        logger.info(f"Authentication attempt", extra={"username": username})
        with LogTimer(logger, f"User authentication", include_in_stats=True):
            user = db.query(User).filter(User.username == username).first()
            if not user:
                logger.warning(f"Authentication failed: user not found", extra={"username": username})
                return None
            logger.debug(f"User found in database", extra={"username": user.username, "user_id": user.id})
            if not verify_password(password, user.hashed_password):
                logger.warning(f"Authentication failed: invalid password", extra={"username": username})
                return None
            logger.info(f"Authentication successful", extra={"username": username, "user_id": user.id})
            return user
    except Exception as e:
        logger.error(f"Authentication error", exc_info=True, extra={"username": username})
        return None

# --- UPDATED: Generic Token Creation ---
@log_function_call(logger)
def _create_jwt_token(
    subject: str,
    expires_delta: timedelta,
    token_type: str,
    additional_claims: Optional[Dict[str, Any]] = None
) -> str:
    """Internal function to create a JWT token with specific type and claims."""
    try:
        with LogTimer(logger, f"{token_type} token creation", include_in_stats=True):
            logger.debug(f"Creating {token_type} token", extra={"subject": subject, "expires_in_seconds": expires_delta.total_seconds()})
            expire = datetime.now(timezone.utc) + expires_delta
            to_encode: Dict[str, Any] = {
                "sub": str(subject), # Ensure subject is string (e.g., user ID)
                "exp": expire,
                "iat": datetime.now(timezone.utc),
                "type": token_type, # Add token type claim
                "jti": str(uuid.uuid4()) # Add unique token identifier
            }
            if additional_claims:
                to_encode.update(additional_claims)

            encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
            logger.debug(f"{token_type} token created successfully", extra={"subject": subject, "expires_at": expire.isoformat(), "jti": to_encode["jti"]})
            return encoded_jwt
    except Exception as e:
        logger.error(f"{token_type} token creation error", exc_info=True, extra={"subject": subject})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not create {token_type} token")

# --- Access Token Creation (uses generic function) ---
@log_function_call(logger)
def create_access_token(subject: str) -> str:
    """Creates a standard JWT access token."""
    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return _create_jwt_token(
        subject=subject,
        expires_delta=expires_delta,
        token_type=ACCESS_TOKEN_TYPE
        # Add roles or other claims if needed: additional_claims={"roles": ["user"]}
    )

# --- ADDED: Password Reset Token Creation ---
@log_function_call(logger)
def create_password_reset_token(subject: str) -> str:
    """Creates a JWT token specifically for password reset."""
    expires_delta = timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)
    return _create_jwt_token(
        subject=subject,
        expires_delta=expires_delta,
        token_type=PASSWORD_RESET_TOKEN_TYPE
    )

# --- ADDED: Generic Token Verification ---
def _verify_jwt_token(token: str, expected_token_type: str) -> Optional[str]:
    """
    Internal function to verify a JWT token, check its type, and return the subject.
    Raises HTTPException on validation errors.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_preview = token[:10] + "..." if token else "None"

    try:
        logger.debug(f"Attempting JWT decode for {expected_token_type} token", extra={"token_preview": token_preview})
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        subject: Optional[str] = payload.get("sub")
        token_type: Optional[str] = payload.get("type")
        jti: Optional[str] = payload.get("jti") # Get unique identifier

        log_extra = {"subject": subject, "token_type": token_type, "jti": jti, "payload_keys": list(payload.keys()) if payload else []}

        if subject is None:
            logger.warning("JWT token missing 'sub' (subject) claim", extra=log_extra)
            credentials_exception.detail = "Invalid token: Missing subject."
            raise credentials_exception
        if token_type != expected_token_type:
            logger.warning(f"JWT token type mismatch. Expected '{expected_token_type}', got '{token_type}'", extra=log_extra)
            credentials_exception.detail = f"Invalid token type. Expected {expected_token_type}."
            raise credentials_exception

        # Optional: Check against a token blacklist (e.g., in Redis) using jti if implementing revocation
        # if is_token_revoked(jti):
        #    logger.warning(f"{expected_token_type} token has been revoked", extra=log_extra)
        #    credentials_exception.detail = "Token has been revoked."
        #    raise credentials_exception

        logger.debug(f"{expected_token_type} token decoded successfully", extra=log_extra)
        return subject

    except jwt.ExpiredSignatureError:
        logger.warning(f"{expected_token_type} token has expired", extra={"token_preview": token_preview})
        credentials_exception.detail = f"{expected_token_type.replace('_', ' ').title()} token has expired."
        raise credentials_exception
    except jwt.JWTClaimsError as claims_err:
        logger.error(f"JWT claims error during {expected_token_type} token decode: {str(claims_err)}", exc_info=False, extra={"error_details": str(claims_err), "token_preview": token_preview})
        credentials_exception.detail = f"Invalid token claims: {str(claims_err)}"
        raise credentials_exception
    except JWTError as jwt_err:
        logger.error(f"JWT decode error (JWTError) for {expected_token_type} token: {str(jwt_err)}", exc_info=False, extra={"error_details": str(jwt_err), "token_preview": token_preview})
        credentials_exception.detail = "Could not validate token credentials."
        if "invalid signature" in str(jwt_err).lower():
            credentials_exception.detail = "Invalid token signature."
        raise credentials_exception
    except Exception as decode_err:
        logger.error(f"Unexpected error during {expected_token_type} token JWT decode", exc_info=True, extra={"error_details": str(decode_err)})
        credentials_exception.detail = "An unexpected error occurred during token validation."
        raise credentials_exception


# --- ADDED: Password Reset Token Verification ---
def verify_password_reset_token(token: str) -> Optional[str]:
    """
    Verifies a password reset token and returns the user ID (subject).
    Raises HTTPException on errors.
    """
    logger.info("Verifying password reset token.")
    # Use the generic verification function, expecting the specific type
    # Note: We are returning the subject (user_id) directly here.
    # The calling function (/reset-password endpoint) will handle user lookup.
    return _verify_jwt_token(token, expected_token_type=PASSWORD_RESET_TOKEN_TYPE)


async def get_current_user(request: Request, db = Depends(get_db)):
    """Get current user from the JWT token by manually reading header."""
    correlation_id = get_correlation_id() or str(uuid.uuid4())
    logger.debug(f"===> Entered get_current_user function (manual header read)", extra={'correlation_id': correlation_id})

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer", "X-Correlation-ID": correlation_id},
    )

    token: Optional[str] = None
    try:
        logger.debug("Attempting to manually get Authorization header...")
        auth_header: Optional[str] = request.headers.get("Authorization")
        if not auth_header:
            logger.warning("Authorization header missing")
            raise credentials_exception

        parts = auth_header.split()
        if len(parts) == 1 or parts[0].lower() != "bearer":
                logger.warning(f"Invalid Authorization header format. Header starts with: '{auth_header[:20]}...'")
                if len(parts) == 1 and len(parts[0]) > 20:
                    token = parts[0]
                    logger.warning("Assuming token was provided without 'Bearer ' prefix.")
                else:
                    raise credentials_exception
        elif len(parts) > 2:
                logger.warning(f"Authorization header has too many parts. Header starts with: '{auth_header[:40]}...'")
                raise credentials_exception
        else:
            token = parts[1]

        token_preview = token[:10] + "..." if token else "None"
        logger.debug(f"Manually extracted token: {token_preview}")

    except HTTPException:
        raise
    except Exception as header_err:
        logger.error(f"Error manually extracting token from header", exc_info=True, extra={"error_details": str(header_err)})
        raise credentials_exception

    # --- Use generic verification for access token ---
    username = _verify_jwt_token(token, expected_token_type=ACCESS_TOKEN_TYPE)
    # _verify_jwt_token raises HTTPException on failure, so no need to check username is None here
    # --- End generic verification ---

    user = None
    try:
        logger.debug(f"Looking up user in database", extra={"username": username})
        # --- MODIFIED: Fetch user by username from token ---
        user = db.query(User).filter(User.username == username).first()
        # --- END MODIFIED ---
        if user is None:
            logger.warning(f"User '{username}' not found in database after token decode")
            # Reuse the credentials exception from _verify_jwt_token if possible, or create new
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User associated with token not found.",
                headers={"WWW-Authenticate": "Bearer"},
            )


        # --- Set user context HERE after successful validation ---
        set_user(user) # Store the full user object in context
        # --- End set user context ---
        logger.debug(f"User found, returning user object.", extra={"username": user.username, "user_id": user.id})
        return user
    except HTTPException:
            raise
    except Exception as db_err:
        logger.error(f"Database error during user lookup in get_current_user", exc_info=True, extra={"error_details": str(db_err)})
        credentials_exception.detail = "Database error during authentication"
        raise credentials_exception

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    """Dependency to get the current user and ensure they are active."""
    if not current_user.is_active:
        logger.warning(f"Authentication failed: User '{current_user.username}' is inactive.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    logger.debug(f"User '{current_user.username}' is active.")
    return current_user

async def get_current_active_superuser(current_user: User = Depends(get_current_active_user)):
    """Dependency to get the current active user and ensure they are a superuser."""
    if not current_user.is_superuser:
        logger.warning(f"Authorization failed: User '{current_user.username}' is not a superuser.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    logger.debug(f"User '{current_user.username}' is an active superuser.")
    return current_user
#</file>