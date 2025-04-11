# <file path='app/schemas/password_reset.py'>
# app/schemas/password_reset.py
from pydantic import BaseModel, EmailStr, Field

class PasswordRecoveryRequest(BaseModel):
    email: EmailStr

class PasswordResetRequest(BaseModel):
    token: str = Field(..., description="The password reset token received via email")
    new_password: str = Field(..., min_length=8, description="The desired new password")

class MessageResponse(BaseModel):
    """Generic message response"""
    message: str