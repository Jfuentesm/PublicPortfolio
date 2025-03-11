from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import logging

from models.user import User
from core.database import get_db
from core.config import settings

# Configure logging
logger = logging.getLogger("vendor_classification.auth")

# Security configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    """Verify password against hashed version."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification error: {str(e)}")
        return False

def get_password_hash(password):
    """Generate password hash."""
    return pwd_context.hash(password)

def authenticate_user(db, username: str, password: str):
    """Authenticate user with username and password."""
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            logger.warning(f"Authentication failed: User not found: {username}")
            return False
        if not verify_password(password, user.hashed_password):
            logger.warning(f"Authentication failed: Invalid password for user: {username}")
            return False
        logger.debug(f"User authenticated successfully: {username}")
        return user
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    try:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        logger.debug(f"Access token created for user: {data.get('sub')}")
        return encoded_jwt
    except Exception as e:
        logger.error(f"Token creation error: {str(e)}")
        raise

async def get_current_user(token: str = Depends(oauth2_scheme), db = Depends(get_db)):
    """Get current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        logger.debug("Decoding JWT token")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            logger.warning("JWT token missing 'sub' claim")
            raise credentials_exception
        logger.debug(f"Token decoded successfully for user: {username}")
    except JWTError as e:
        logger.error(f"JWT decode error: {str(e)}")
        raise credentials_exception
    
    try:
        logger.debug(f"Looking up user in database: {username}")
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            logger.warning(f"User not found: {username}")
            raise credentials_exception
        return user
    except Exception as e:
        logger.error(f"Database error in get_current_user: {str(e)}")
        raise credentials_exception