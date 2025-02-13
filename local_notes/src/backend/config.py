# src/backend/config.py
"""
config.py

This module provides configuration settings for the note-taking application.
It centralizes all constants including file paths, file extensions, and server settings.
"""

import os
from pathlib import Path


class Config:
    """
    Configuration class for application-wide constants.
    """
    # Directory where Markdown notes (the vault) are stored.
    VAULT_DIR: str = os.getenv("VAULT_DIR", str(Path(os.getcwd(), "storage", "vault")))
    
    # File extension for Markdown note files.
    NOTE_EXTENSION: str = ".md"
    
    # Host address for the FastAPI server.
    HOST: str = os.getenv("HOST", "127.0.0.1")
    
    # Port number for the FastAPI server.
    PORT: int = int(os.getenv("PORT", 8000))
