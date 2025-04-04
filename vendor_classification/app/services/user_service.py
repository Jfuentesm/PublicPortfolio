# app/services/user_service.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from typing import List, Optional
import uuid

from models.user import User
from schemas.user import UserCreate, UserUpdate
from api.auth import get_password_hash # Assuming auth.py is in api directory
from core.logging_config import get_logger

logger = get_logger("vendor_classification.user_service")

def create_user(db: Session, user_in: UserCreate) -> User:
    """
    Creates a new user in the database.
    Handles password hashing and potential integrity errors.
    """
    logger.info(f"Attempting to create user", extra={"username": user_in.username, "email": user_in.email})
    hashed_password = get_password_hash(user_in.password)
    db_user = User(
        id=str(uuid.uuid4()), # Generate UUID string for ID
        username=user_in.username,
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=hashed_password,
        is_active=user_in.is_active if user_in.is_active is not None else True,
        is_superuser=user_in.is_superuser if user_in.is_superuser is not None else False,
    )
    db.add(db_user)
    try:
        db.commit()
        db.refresh(db_user)
        logger.info(f"User created successfully", extra={"user_id": db_user.id, "username": db_user.username})
        return db_user
    except IntegrityError as e:
        db.rollback()
        logger.warning(f"Failed to create user due to integrity error (duplicate username/email?)",
                        extra={"username": user_in.username, "email": user_in.email, "error": str(e)})
        # Determine if it's username or email conflict (crude check)
        detail = "Username or email already registered."
        if "users_username_key" in str(e).lower():
            detail = f"Username '{user_in.username}' is already taken."
        elif "users_email_key" in str(e).lower():
            detail = f"Email '{user_in.email}' is already registered."
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error creating user", exc_info=True, extra={"username": user_in.username})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create user.")


def get_user(db: Session, user_id: str) -> Optional[User]:
    """Retrieves a user by their ID."""
    logger.debug(f"Fetching user by ID", extra={"user_id": user_id})
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        logger.debug(f"User found", extra={"user_id": user_id, "username": user.username})
    else:
        logger.debug(f"User not found", extra={"user_id": user_id})
    return user

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Retrieves a user by their username."""
    logger.debug(f"Fetching user by username", extra={"username": username})
    user = db.query(User).filter(User.username == username).first()
    if user:
        logger.debug(f"User found", extra={"user_id": user.id, "username": username})
    else:
        logger.debug(f"User not found", extra={"username": username})
    return user

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Retrieves a user by their email."""
    logger.debug(f"Fetching user by email", extra={"email": email})
    user = db.query(User).filter(User.email == email).first()
    if user:
        logger.debug(f"User found", extra={"user_id": user.id, "username": user.username, "email": email})
    else:
        logger.debug(f"User not found", extra={"email": email})
    return user


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """Retrieves a list of users with pagination."""
    logger.info(f"Fetching list of users", extra={"skip": skip, "limit": limit})
    users = db.query(User).offset(skip).limit(limit).all()
    logger.info(f"Retrieved {len(users)} users.")
    return users


def update_user(db: Session, user_id: str, user_in: UserUpdate) -> Optional[User]:
    """Updates an existing user."""
    logger.info(f"Attempting to update user", extra={"user_id": user_id})
    db_user = get_user(db, user_id)
    if not db_user:
        logger.warning(f"User not found for update", extra={"user_id": user_id})
        return None

    update_data = user_in.model_dump(exclude_unset=True) # Pydantic v2
    # update_data = user_in.dict(exclude_unset=True) # Pydantic v1

    if "password" in update_data and update_data["password"]:
        logger.info(f"Updating password for user", extra={"user_id": user_id})
        hashed_password = get_password_hash(update_data["password"])
        db_user.hashed_password = hashed_password
        del update_data["password"] # Remove plain password from update dict

    for field, value in update_data.items():
        setattr(db_user, field, value)

    try:
        db.commit()
        db.refresh(db_user)
        logger.info(f"User updated successfully", extra={"user_id": user_id})
        return db_user
    except IntegrityError as e:
        db.rollback()
        logger.warning(f"Failed to update user due to integrity error (duplicate username/email?)",
                        extra={"user_id": user_id, "error": str(e)})
        detail = "Username or email already registered by another user."
        if "users_username_key" in str(e).lower():
            detail = f"Username '{update_data.get('username', db_user.username)}' is already taken."
        elif "users_email_key" in str(e).lower():
            detail = f"Email '{update_data.get('email', db_user.email)}' is already registered."
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error updating user", exc_info=True, extra={"user_id": user_id})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not update user.")


def delete_user(db: Session, user_id: str) -> bool:
    """Deletes a user."""
    logger.info(f"Attempting to delete user", extra={"user_id": user_id})
    db_user = get_user(db, user_id)
    if not db_user:
        logger.warning(f"User not found for deletion", extra={"user_id": user_id})
        return False

    # Prevent deleting the default admin? (Optional safeguard)
    # if db_user.username == 'admin':
    #     logger.error("Attempted to delete the default admin user.", extra={"user_id": user_id})
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot delete the primary admin user.")

    try:
        db.delete(db_user)
        db.commit()
        logger.info(f"User deleted successfully", extra={"user_id": user_id})
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting user", exc_info=True, extra={"user_id": user_id})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not delete user.")
