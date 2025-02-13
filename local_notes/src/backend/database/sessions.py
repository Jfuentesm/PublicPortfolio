# src/backend/database/sessions.py
"""
sessions.py

Sets up the SQLAlchemy engine and session factory for database interactions.
The SQLite database file is stored in the local storage directory.
"""

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Updated import for config
from src.backend.config import Config

# Define the SQLite database file path.
DATABASE_PATH = Path(os.getcwd(), "storage", "database.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Create the SQLAlchemy engine with SQLite-specific options.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Required for SQLite with multiple threads
)

# Create a session factory bound to the engine.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
