from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import logging

# Make sure this import is present and spelled correctly
from core.config import settings

from models.user import User
from core.database import get_db

# Configure logging
logger = logging.getLogger("vendor_classification.auth")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    """Verify password against hashed version."""
    try:
        logger.debug(f"Verifying password. Plain: '{plain_password}' | Hashed prefix: '{hashed_password[:12]}...'")
        result = pwd_context.verify(plain_password, hashed_password)
        logger.debug(f"Password verification result: {result}")
        return result
    except Exception as e:
        logger.error(f"Password verification error: {str(e)}")
        return False

def get_password_hash(password):
    """Generate password hash."""
    try:
        hashed = pwd_context.hash(password)
        logger.debug(f"Generated password hash for password='{password}'. Hash prefix='{hashed[:12]}...'")
        return hashed
    except Exception as e:
        logger.error(f"Password hashing error: {str(e)}")
        raise

def authenticate_user(db, username: str, password: str):
    """
    Look up the user in the DB by username.
    Then attempt password verification.
    Return user object if successful, else False.
    """
    try:
        logger.info(f"Authenticating user: {username}")
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            logger.warning(f"Authentication failed: No user found with username='{username}'")
            return False
        
        logger.debug(f"User record found in DB: {user.username}. Checking password now...")
        if not verify_password(password, user.hashed_password):
            logger.warning(f"Authentication failed: Invalid password for user='{username}'")
            return False
        
        logger.info(f"User '{username}' authenticated successfully.")
        return user
    except Exception as e:
        logger.error(f"Unexpected error in authenticate_user: {str(e)}")
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    try:
        # Make sure 'settings' is recognized here
        logger.debug("Creating access token. Confirming settings import:")
        logger.debug(f"SECRET_KEY is present: {bool(settings.SECRET_KEY)}")
        logger.debug(f"ALGORITHM is: {settings.ALGORITHM}")
        
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        logger.debug(f"Access token created for user: {data.get('sub')} (expires at {expire})")
        return encoded_jwt
    except Exception as e:
        logger.error(f"Token creation error: {str(e)}")
        raise

async def get_current_user(token: str = Depends(oauth2_scheme), db = Depends(get_db)):
    """Get current user from the JWT token."""
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
        logger.debug(f"Token decoded successfully. username='{username}'")
    except JWTError as e:
        logger.error(f"JWT decode error: {str(e)}")
        raise credentials_exception
    
    try:
        logger.debug(f"Looking up user in database: {username}")
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            logger.warning(f"User not found in DB: {username}")
            raise credentials_exception
        logger.debug(f"User found, returning user object: {user.username}")
        return user
    except Exception as e:
        logger.error(f"Database error in get_current_user: {str(e)}")
        raise credentials_exception