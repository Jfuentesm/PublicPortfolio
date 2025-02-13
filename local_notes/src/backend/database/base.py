# src/backend/database/base.py
"""
base.py

Defines the declarative base for all SQLAlchemy models.
This base is used for all model definitions to ensure a consistent ORM layer.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()
