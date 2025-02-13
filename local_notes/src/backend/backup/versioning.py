# src/backend/backup/versioning.py
"""
versioning.py

Provides functionality for managing version history of Markdown notes.
It allows listing available versions and restoring a note to a previous version.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import List

# Directory for backups
BACKUP_DIR = Path(os.getcwd(), "storage", "backups")
BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def list_versions(note_path: str) -> List[str]:
    """
    List all backup versions for a given note.

    Args:
        note_path (str): Relative path to the note within the vault.

    Returns:
        List[str]: A list of backup file names.
    """
    note_backup_dir = BACKUP_DIR / note_path.replace(os.sep, "_")
    if not note_backup_dir.exists():
        return []
    return sorted([f.name for f in note_backup_dir.iterdir() if f.is_file()])


def create_version(note_path: str) -> None:
    """
    Create a backup version of a note by copying the current file to a backup directory.

    Args:
        note_path (str): Relative path to the note within the vault.
    """
    from file_handler import NoteManager  # Import here to avoid circular dependency
    note_manager = NoteManager()
    full_note_path = note_manager.vault_dir / note_path
    if not full_note_path.exists():
        raise FileNotFoundError(f"Note not found: {note_path}")

    note_backup_dir = BACKUP_DIR / note_path.replace(os.sep, "_")
    note_backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = note_backup_dir / f"{timestamp}.bak"
    shutil.copy(full_note_path, backup_file)


def restore_version(note_path: str, version_file: str) -> None:
    """
    Restore a note to a previous version from backup.

    Args:
        note_path (str): Relative path to the note within the vault.
        version_file (str): The backup file name to restore.
    """
    from file_handler import NoteManager  # Import here to avoid circular dependency
    note_manager = NoteManager()
    note_backup_dir = BACKUP_DIR / note_path.replace(os.sep, "_")
    backup_file = note_backup_dir / version_file
    if not backup_file.exists():
        raise FileNotFoundError(f"Backup version not found: {version_file}")

    # Overwrite the current note with the backup version.
    full_note_path = note_manager.vault_dir / note_path
    shutil.copy(backup_file, full_note_path)
