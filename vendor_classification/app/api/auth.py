
# app/api/auth.py
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
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

@log_function_call(logger)
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    try:
        with LogTimer(logger, "JWT token creation", include_in_stats=True):
            subject = data.get("sub")
            logger.debug("Creating access token", extra={"subject": subject})
            to_encode = data.copy()
            if expires_delta:
                expire = datetime.utcnow() + expires_delta
            else:
                expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            to_encode.update({"exp": expire})
            encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
            logger.debug(f"Access token created", extra={"subject": subject, "expires_at": expire.isoformat()})
            return encoded_jwt
    except Exception as e:
        logger.error(f"Token creation error", exc_info=True)
        raise

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

    payload = None
    username = None
    try:
        logger.debug("Attempting JWT decode...")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: Optional[str] = payload.get("sub")
        logger.debug(f"Token decoded successfully", extra={"username": username, "payload_keys": list(payload.keys()) if payload else []})
        if username is None:
            logger.warning("JWT token missing 'sub' (username) claim after decode")
            raise credentials_exception
    except JWTError as jwt_err:
        logger.error(f"JWT decode error (JWTError): {str(jwt_err)}", exc_info=False, extra={"error_details": str(jwt_err), "token_preview": token_preview})
        detail = "Could not validate credentials"
        if "expired" in str(jwt_err).lower():
            detail = "Token has expired"
        elif "invalid signature" in str(jwt_err).lower():
            detail = "Invalid token signature"
        credentials_exception.detail = detail
        raise credentials_exception
    except Exception as decode_err:
        logger.error(f"Unexpected error during JWT decode", exc_info=True, extra={"error_details": str(decode_err)})
        raise credentials_exception

    user = None
    try:
        logger.debug(f"Looking up user in database", extra={"username": username})
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            logger.warning(f"User '{username}' not found in database after token decode")
            raise credentials_exception

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