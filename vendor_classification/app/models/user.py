from sqlalchemy import Column, String, Boolean, DateTime, Index # <<< ADDED Index
from sqlalchemy.sql import func

from core.database import Base

class User(Base):
    """User model for authentication."""

    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now()) # Consider index if tracking sign-up trends
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # --- ADDED: Potential Indexes ---
    __table_args__ = (
        Index('ix_users_created_at', 'created_at'), # For potential user sign-up trend analysis
    )
    # --- END ADDED ---