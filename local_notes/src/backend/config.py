"""
config.py

Provides application-wide configuration settings.
All constant values and paths are defined here.
"""

import os
from pathlib import Path

class Config:
    """
    Configuration class for the note-taking application.
    """
    # Directory where Markdown notes (the vault) are stored.
    VAULT_DIR: str = os.getenv("VAULT_DIR", str(Path(os.getcwd(), "storage", "vault")))
    
    # Default file extension for note files.
    NOTE_EXTENSION: str = ".md"

    # Host address for the FastAPI server.
    HOST: str = os.getenv("HOST", "127.0.0.1")
    
    # Port number for the FastAPI server.
    PORT: int = int(os.getenv("PORT", 8000))
    
    # Directory for storing the SQLite database.
    STORAGE_DIR: Path = Path(os.getcwd(), "storage")
    
    # Path for database file.
    DATABASE_PATH: Path = STORAGE_DIR / "database.db"
    
    # Directory for search index.
    SEARCH_INDEX_DIR: Path = STORAGE_DIR / "search_index"
    
    # Directory for backups.
    BACKUP_DIR: Path = STORAGE_DIR / "backups"
    
    # Directory for canvas data.
    CANVAS_DIR: Path = STORAGE_DIR / "canvas"