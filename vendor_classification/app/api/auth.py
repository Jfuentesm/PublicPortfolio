# app/api/auth.py
from fastapi import Depends, HTTPException, status, Request # Added Request
from fastapi.security import OAuth2PasswordBearer # Keep for credentials_exception header
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional

from core.config import settings
from core.logging_config import get_logger, LogTimer, log_function_call

from models.user import User
from core.database import get_db

# Configure logging using our custom logger
logger = get_logger("vendor_classification.auth")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# Keep oauth2_scheme instance for potential use elsewhere or headers in exception
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@log_function_call(logger, include_args=False)
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
        logger.error(f"Password verification error", exc_info=True)
        return False

@log_function_call(logger, include_args=False)
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

@log_function_call(logger, include_args=False)
def authenticate_user(db, username: str, password: str):
    """Authenticate user."""
    try:
        logger.info(f"Authentication attempt", extra={"username": username})
        with LogTimer(logger, f"User authentication", include_in_stats=True):
            user = db.query(User).filter(User.username == username).first()
            if not user:
                logger.warning(f"Authentication failed: user not found", extra={"username": username})
                return False
            logger.debug(f"User found in database", extra={"username": user.username, "user_id": user.id})
            if not verify_password(password, user.hashed_password):
                logger.warning(f"Authentication failed: invalid password", extra={"username": username})
                return False
            logger.info(f"Authentication successful", extra={"username": username, "user_id": user.id})
            return user
    except Exception as e:
        logger.error(f"Authentication error", exc_info=True, extra={"username": username})
        return False

@log_function_call(logger)
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    try:
        with LogTimer(logger, "JWT token creation", include_in_stats=True):
            logger.debug("Creating access token", extra={"subject": data.get("sub")})
            to_encode = data.copy()
            if expires_delta:
                expire = datetime.utcnow() + expires_delta
            else:
                expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            to_encode.update({"exp": expire})
            encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
            logger.debug(f"Access token created", extra={"subject": data.get("sub"), "expires_at": expire.isoformat()})
            return encoded_jwt
    except Exception as e:
        logger.error(f"Token creation error", exc_info=True)
        raise

# --- Using manual header read version of get_current_user ---
# Removed @log_function_call here as it might interfere (relying on manual logs inside)
async def get_current_user(request: Request, db = Depends(get_db)):
    """Get current user from the JWT token by manually reading header."""
    logger.debug("===> Entered get_current_user function (manual header read)")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
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
        if len(parts) != 2 or parts[0].lower() != "bearer":
            logger.warning(f"Invalid Authorization header format: '{auth_header[:20]}...'")
            raise credentials_exception

        token = parts[1]
        token_preview = token[:10] + "..." if token else "None"
        logger.debug(f"Manually extracted token: {token_preview}")

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
        logger.debug(f"Token decoded successfully", extra={"username": username, "payload": payload})
        if username is None:
            logger.warning("JWT token missing 'sub' claim after decode")
            raise credentials_exception
    except JWTError as jwt_err:
        logger.error(f"JWT decode error (JWTError): {str(jwt_err)}", exc_info=True, extra={"error_details": str(jwt_err)})
        raise credentials_exception # Re-raise consistent exception
    except Exception as decode_err:
        logger.error(f"Unexpected error during JWT decode", exc_info=True, extra={"error_details": str(decode_err)})
        raise credentials_exception

    # Database lookup
    try:
        logger.debug(f"Looking up user in database", extra={"username": username})
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            logger.warning(f"User '{username}' not found in database after token decode")
            raise credentials_exception
        logger.debug(f"User found, returning user object.", extra={"username": user.username, "user_id": user.id})
        return user
    except Exception as db_err:
        logger.error(f"Database error during user lookup in get_current_user", exc_info=True, extra={"error_details": str(db_err)})
        raise credentials_exception
# --- END get_current_user ---