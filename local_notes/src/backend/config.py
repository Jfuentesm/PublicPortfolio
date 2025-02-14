#!/usr/bin/env python3
# config.py
"""
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

    # Daily notes subfolder inside the vault.
    DAILY_NOTES_DIR: Path = Path(VAULT_DIR, "daily")

    # A default daily note template file (optional).
    # If you don't have a template, simply ignore or remove it.
    # e.g., place your template at: storage/vault/templates/daily_template.md
    DAILY_NOTES_TEMPLATE: Path = Path(VAULT_DIR, "templates", "daily_template.md")

    # Date format to use for daily notes filename.
    DAILY_NOTES_DATE_FORMAT: str = "%Y-%m-%d"

    # -------------------------
    # NEW PERIODIC SNAPSHOT SETTINGS
    # -------------------------
    # Enable or disable periodic vault snapshots
    ENABLE_PERIODIC_SNAPSHOTS: bool = True

    # Interval (in minutes) between automatic snapshots
    SNAPSHOT_INTERVAL_MINUTES: int = 5

