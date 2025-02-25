# src/backend/file_handler.py
"""
file_handler.py

This module implements the NoteManager class which provides methods for managing
Markdown note files. It supports listing, reading, writing, and creating notes
within the designated vault directory.
"""

import os
from pathlib import Path
from typing import List, Optional

# Updated import for config
from src.backend.config import Config


class NoteManager:
    """
    Manages file operations for Markdown notes stored in the vault directory.
    """

    def __init__(self, vault_dir: Optional[str] = None) -> None:
        """
        Initialize the NoteManager with the specified vault directory.

        Args:
            vault_dir: Optional custom path to the vault directory. If not provided,
                       the default from Config.VAULT_DIR is used.
        """
        self.vault_dir: Path = Path(vault_dir) if vault_dir else Path(Config.VAULT_DIR)
        # Create the vault directory if it does not exist.
        self.vault_dir.mkdir(parents=True, exist_ok=True)

    def list_notes(self) -> List[str]:
        """
        Recursively list all Markdown note files in the vault directory.

        Returns:
            List[str]: A list of note file paths (relative to the vault directory).
        """
        notes: List[str] = []
        # Recursively search for files ending with the Markdown extension.
        for file_path in self.vault_dir.rglob(f"*{Config.NOTE_EXTENSION}"):
            # Append the relative file path to the notes list.
            notes.append(str(file_path.relative_to(self.vault_dir)))
        return notes

    def read_note(self, note_path: str) -> str:
        """
        Read the content of a Markdown note file.

        Args:
            note_path: Relative path to the note file within the vault.

        Returns:
            str: The content of the note.

        Raises:
            FileNotFoundError: If the specified note file does not exist.
        """
        full_path: Path = self.vault_dir / note_path
        # Verify the file exists and is a file.
        if not full_path.exists() or not full_path.is_file():
            raise FileNotFoundError(f"Note not found: {note_path}")
        # Open and read the file content.
        with full_path.open("r", encoding="utf-8") as file:
            content: str = file.read()
        return content

    def write_note(self, note_path: str, content: str) -> None:
        """
        Write content to a Markdown note file. Creates the file if it does not exist.

        Args:
            note_path: Relative path to the note file within the vault.
            content: The content to write into the note.
        """
        full_path: Path = self.vault_dir / note_path
        # Ensure the parent directory exists.
        full_path.parent.mkdir(parents=True, exist_ok=True)
        # Write the provided content to the file.
        with full_path.open("w", encoding="utf-8") as file:
            file.write(content)

    def create_note(self, note_name: str, content: str = "") -> str:
        """
        Create a new Markdown note with the specified name and optional initial content.

        Args:
            note_name: The name of the new note file (without any path).
            content: Optional initial content for the note.

        Returns:
            str: The relative path of the newly created note.

        Raises:
            FileExistsError: If a note with the given name already exists.
        """
        # Append the proper Markdown extension if not already present.
        note_filename: str = (
            note_name if note_name.endswith(Config.NOTE_EXTENSION)
            else note_name + Config.NOTE_EXTENSION
        )
        full_path: Path = self.vault_dir / note_filename
        # Check if the note file already exists.
        if full_path.exists():
            raise FileExistsError(f"Note already exists: {note_filename}")
        # Create the note by writing the initial content.
        self.write_note(note_filename, content)
        return note_filename
