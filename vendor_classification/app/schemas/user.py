# app/schemas/user.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
import uuid # Import uuid

# --- Base User Info ---
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    username: str = Field(..., min_length=3, max_length=50)

# --- Properties to receive via API on creation ---
class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

# --- Properties to receive via API on update ---
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8) # Allow password update
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None

# --- Properties stored in DB ---
# This is technically represented by the User model itself,
# but can be useful for internal representation if needed.
class UserInDBBase(UserBase):
    id: uuid.UUID # Use UUID for ID
    hashed_password: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True # Pydantic v2 way
        # orm_mode = True # Pydantic v1 way

# --- Properties to return to client ---
class UserResponse(UserBase):
    id: uuid.UUID # Use UUID for ID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True # Pydantic v2 way
        # orm_mode = True # Pydantic v1 way