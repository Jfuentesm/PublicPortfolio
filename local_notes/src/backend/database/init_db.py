# src/backend/database/init_db.py
"""
init_db.py

Initializes the database by creating all necessary tables.
Imports all model definitions so they are registered with the SQLAlchemy metadata.
"""

# Updated imports for database and tasks
from src.backend.database.sessions import engine
from src.backend.database.base import Base
from src.backend.tasks.models import Task  # Import Task model to register it with the metadata


def init_db() -> None:
    """
    Create all tables in the database.
    """
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
