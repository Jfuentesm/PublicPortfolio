from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
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
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@log_function_call(logger, include_args=False)  # Don't log password
def verify_password(plain_password, hashed_password):
    """Verify password against hashed version."""
    try:
        with LogTimer(logger, "Password verification", include_in_stats=True):
            # Don't log the actual passwords, just the first few chars of the hash for debugging
            hash_prefix = hashed_password[:5] if hashed_password else None
            logger.debug(f"Verifying password", extra={"hash_prefix": hash_prefix})
            
            result = pwd_context.verify(plain_password, hashed_password)
            logger.debug(f"Password verification result", extra={"result": result})
            return result
    except Exception as e:
        logger.error(f"Password verification error", exc_info=True)
        return False

@log_function_call(logger, include_args=False)  # Don't log password
def get_password_hash(password):
    """Generate password hash."""
    try:
        with LogTimer(logger, "Password hashing", include_in_stats=True):
            hashed = pwd_context.hash(password)
            # Don't log the full hash, just the beginning for debugging
            logger.debug(f"Generated password hash", extra={"hash_prefix": hashed[:5] if hashed else None})
            return hashed
    except Exception as e:
        logger.error(f"Password hashing error", exc_info=True)
        raise

@log_function_call(logger, include_args=False)  # Don't log password
def authenticate_user(db, username: str, password: str):
    """
    Look up the user in the DB by username.
    Then attempt password verification.
    Return user object if successful, else False.
    """
    try:
        logger.info(f"Authentication attempt", extra={"username": username})
        
        with LogTimer(logger, f"User authentication", include_in_stats=True):
            user = db.query(User).filter(User.username == username).first()
            
            if not user:
                logger.warning(f"Authentication failed: user not found", 
                              extra={"username": username})
                return False
            
            logger.debug(f"User found in database", 
                        extra={"username": user.username, "user_id": user.id})
            
            if not verify_password(password, user.hashed_password):
                logger.warning(f"Authentication failed: invalid password", 
                              extra={"username": username})
                return False
            
            logger.info(f"Authentication successful", 
                       extra={"username": username, "user_id": user.id})
            return user
    except Exception as e:
        logger.error(f"Authentication error", exc_info=True,
                    extra={"username": username})
        return False

@log_function_call(logger)
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    try:
        with LogTimer(logger, "JWT token creation", include_in_stats=True):
            # Log token creation data (excluding sensitive info)
            logger.debug("Creating access token", 
                        extra={"subject": data.get("sub")})
            
            to_encode = data.copy()
            if expires_delta:
                expire = datetime.utcnow() + expires_delta
            else:
                expire = datetime.utcnow() + timedelta(minutes=15)
            to_encode.update({"exp": expire})
            
            encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
            
            logger.debug(f"Access token created", 
                        extra={"subject": data.get("sub"), "expires_at": expire.isoformat()})
            return encoded_jwt
    except Exception as e:
        logger.error(f"Token creation error", exc_info=True)
        raise

@log_function_call(logger)
async def get_current_user(token: str = Depends(oauth2_scheme), db = Depends(get_db)):
    """Get current user from the JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        logger.debug("Decoding JWT token")
        
        with LogTimer(logger, "JWT token validation", include_in_stats=True):
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                logger.warning("JWT token missing 'sub' claim")
                raise credentials_exception
            logger.debug(f"Token decoded successfully", extra={"username": username})
    except JWTError as e:
        logger.error(f"JWT decode error", exc_info=True)
        raise credentials_exception
    
    try:
        logger.debug(f"Looking up user in database", extra={"username": username})
        
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            logger.warning(f"User not found in database", extra={"username": username})
            raise credentials_exception
            
        logger.debug(f"User found", extra={"username": user.username, "user_id": user.id})
        return user
    except Exception as e:
        logger.error(f"Database error in get_current_user", exc_info=True)
        raise credentials_exception