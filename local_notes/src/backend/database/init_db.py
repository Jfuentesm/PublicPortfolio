# src/backend/database/init_db.py
"""
init_db.py

Initializes the database by creating all necessary tables.
Imports all model definitions so they are registered with the SQLAlchemy metadata.
"""

from database.sessions import engine  # Updated import: use "sessions" (plural)
from database.base import Base
from tasks.models import Task  # Import Task model to register it with the metadata


def init_db() -> None:
    """
    Create all tables in the database.
    """
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()