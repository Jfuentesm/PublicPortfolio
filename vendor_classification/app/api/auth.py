
# --- file path='api/auth.py' ---
# app/api/auth.py
from fastapi import Depends, HTTPException, status, Request # Added Request
from fastapi.security import OAuth2PasswordBearer # Keep for credentials_exception header
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional

from core.config import settings
from core.logging_config import get_logger, LogTimer, log_function_call, set_user, get_user, get_correlation_id # Added context helpers

from models.user import User
from core.database import get_db

# Configure logging using our custom logger
logger = get_logger("vendor_classification.auth")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# Keep oauth2_scheme instance for potential use elsewhere or headers in exception
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") # tokenUrl='token' should match your login endpoint path

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
        # Log the error type, but not the password details
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
                return None # Return None instead of False for clarity
            logger.debug(f"User found in database", extra={"username": user.username, "user_id": user.id})
            if not verify_password(password, user.hashed_password):
                logger.warning(f"Authentication failed: invalid password", extra={"username": username})
                return None # Return None instead of False
            logger.info(f"Authentication successful", extra={"username": username, "user_id": user.id})
            return user
    except Exception as e:
        logger.error(f"Authentication error", exc_info=True, extra={"username": username})
        return None # Return None on error

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

# --- Using manual header read version of get_current_user ---
# Removed @log_function_call here as it might interfere (relying on manual logs inside)
async def get_current_user(request: Request, db = Depends(get_db)):
    """Get current user from the JWT token by manually reading header."""
    # Use correlation ID from middleware if available, otherwise generate one
    correlation_id = get_correlation_id() or str(uuid.uuid4())
    logger.debug(f"===> Entered get_current_user function (manual header read)", extra={'correlation_id': correlation_id})

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer", "X-Correlation-ID": correlation_id}, # Add correlation ID header
    )

    token: Optional[str] = None
    try:
        # Manually extract token
        logger.debug("Attempting to manually get Authorization header...")
        auth_header: Optional[str] = request.headers.get("Authorization")
        if not auth_header:
            logger.warning("Authorization header missing")
            raise credentials_exception

        parts = auth_header.split()
        if len(parts) == 1 or parts[0].lower() != "bearer":
             logger.warning(f"Invalid Authorization header format. Header starts with: '{auth_header[:20]}...'")
             # Handle case where token might be missing 'Bearer ' prefix
             if len(parts) == 1 and len(parts[0]) > 20: # Assume it might be the token itself
                  token = parts[0]
                  logger.warning("Assuming token was provided without 'Bearer ' prefix.")
             else:
                  raise credentials_exception
        elif len(parts) > 2:
             logger.warning(f"Authorization header has too many parts. Header starts with: '{auth_header[:40]}...'")
             raise credentials_exception
        else: # Correct format: Bearer <token>
            token = parts[1]

        token_preview = token[:10] + "..." if token else "None"
        logger.debug(f"Manually extracted token: {token_preview}")

    except HTTPException: # Re-raise credentials_exception directly
        raise
    except Exception as header_err:
        logger.error(f"Error manually extracting token from header", exc_info=True, extra={"error_details": str(header_err)})
        raise credentials_exception

    # Proceed with JWT decoding
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
        # Log specific JWT errors
        logger.error(f"JWT decode error (JWTError): {str(jwt_err)}", exc_info=False, extra={"error_details": str(jwt_err), "token_preview": token_preview})
        # Map specific errors to user-friendly messages if desired
        detail = "Could not validate credentials"
        if "expired" in str(jwt_err).lower():
            detail = "Token has expired"
        elif "invalid signature" in str(jwt_err).lower():
            detail = "Invalid token signature"
        credentials_exception.detail = detail
        raise credentials_exception # Re-raise consistent exception
    except Exception as decode_err:
        logger.error(f"Unexpected error during JWT decode", exc_info=True, extra={"error_details": str(decode_err)})
        raise credentials_exception

    # Database lookup
    user = None
    try:
        logger.debug(f"Looking up user in database", extra={"username": username})
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            logger.warning(f"User '{username}' not found in database after token decode")
            raise credentials_exception

        # Check if user is active
        if not user.is_active:
            logger.warning(f"Authentication failed: User '{username}' is inactive.")
            credentials_exception.detail = "Inactive user"
            raise credentials_exception

        logger.debug(f"User found and active, returning user object.", extra={"username": user.username, "user_id": user.id})
        # --- Set user context HERE after successful validation ---
        set_user(user)
        # --- End set user context ---
        return user
    except HTTPException: # Re-raise credentials_exception directly
         raise
    except Exception as db_err:
        logger.error(f"Database error during user lookup in get_current_user", exc_info=True, extra={"error_details": str(db_err)})
        credentials_exception.detail = "Database error during authentication"
        raise credentials_exception
# --- END get_current_user ---

# --- ADDED: Import UUID for correlation ID generation if needed ---
import uuid
# --- END ADDED ---