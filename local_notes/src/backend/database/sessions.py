# src/backend/database/sessions.py
"""
sessions.py

Sets up the SQLAlchemy engine and session factory for database interactions.
The SQLite database file is stored in the local storage directory.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import Config for centralized configuration values.
from src.backend.config import Config

# Use the DATABASE_PATH from the configuration for the SQLite database file.
DATABASE_URL = f"sqlite:///{Config.DATABASE_PATH}"

# Create the SQLAlchemy engine with SQLite-specific options.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite-specific option for multi-threading.
)

# Create a session factory bound to the engine.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
