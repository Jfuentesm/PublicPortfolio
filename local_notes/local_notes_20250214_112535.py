<goal>
IMPLEMENT TipTap Editor to replace the split editor by a single unified WUSIWYG editor

</goal>

'''
Included Files:
- local_notes_20250214_112235.py
- package-lock.json
- requirements.txt
- run_all.sh
- src/backend/__init__.py
- src/backend/backup/__init__.py
- src/backend/backup/routes.py
- src/backend/backup/snapshotter.py
- src/backend/backup/versioning.py
- src/backend/canvas/__init__.py
- src/backend/canvas/canvas_store.py
- src/backend/canvas/node_processor.py
- src/backend/canvas/routes.py
- src/backend/config.py
- src/backend/database/__init__.py
- src/backend/database/base.py
- src/backend/database/init_db.py
- src/backend/database/sessions.py
- src/backend/file_handler.py
- src/backend/main.py
- src/backend/search/__init__.py
- src/backend/search/indexer.py
- src/backend/search/query_parser.py
- src/backend/search/routes.py
- src/backend/tasks/__init__.py
- src/backend/tasks/models.py
- src/backend/tasks/recurrence.py
- src/backend/tasks/routes.py
- src/frontend/index.html
- src/frontend/package-lock.json
- src/frontend/package.json
- src/frontend/src/App.vue
- src/frontend/src/components/CanvasView.vue
- src/frontend/src/components/EditorPane.vue
- src/frontend/src/components/KanbanBoard.vue
- src/frontend/src/components/NoteExplorer.vue
- src/frontend/src/components/PreviewPane.vue
- src/frontend/src/components/TaskPanel.vue
- src/frontend/src/main.js
- src/frontend/storage/vault/2.md
- src/frontend/storage/vault/test note 1.md
- src/frontend/vite.config.js
- storage/vault/Test note 1.md

'''

# Concatenated Source Code

<file path='local_notes_20250214_112235.py'>
'''
Included Files:
- package-lock.json
- requirements.txt
- run_all.sh
- src/backend/__init__.py
- src/backend/backup/__init__.py
- src/backend/backup/routes.py
- src/backend/backup/snapshotter.py
- src/backend/backup/versioning.py
- src/backend/canvas/__init__.py
- src/backend/canvas/canvas_store.py
- src/backend/canvas/node_processor.py
- src/backend/canvas/routes.py
- src/backend/config.py
- src/backend/database/__init__.py
- src/backend/database/base.py
- src/backend/database/init_db.py
- src/backend/database/sessions.py
- src/backend/file_handler.py
- src/backend/main.py
- src/backend/search/__init__.py
- src/backend/search/indexer.py
- src/backend/search/query_parser.py
- src/backend/search/routes.py
- src/backend/tasks/__init__.py
- src/backend/tasks/models.py
- src/backend/tasks/recurrence.py
- src/backend/tasks/routes.py
- src/frontend/index.html
- src/frontend/package-lock.json
- src/frontend/package.json
- src/frontend/src/App.vue
- src/frontend/src/components/CanvasView.vue
- src/frontend/src/components/EditorPane.vue
- src/frontend/src/components/KanbanBoard.vue
- src/frontend/src/components/NoteExplorer.vue
- src/frontend/src/components/PreviewPane.vue
- src/frontend/src/components/TaskPanel.vue
- src/frontend/src/main.js
- src/frontend/storage/vault/2.md
- src/frontend/storage/vault/test note 1.md
- src/frontend/vite.config.js
- storage/vault/Test note 1.md

'''

# Concatenated Source Code

<file path='package-lock.json'>
{
  "name": "local_notes",
  "lockfileVersion": 3,
  "requires": true,
  "packages": {}
}

</file>

<file path='requirements.txt'>
# requirements.txt
SQLAlchemy
fastapi
pydantic
uvicorn
whoosh

</file>

<file path='run_all.sh'>
#!/usr/bin/env bash
set -e

#
# 1) Install Python dependencies
#
#echo "Installing Python dependencies..."
#pip install -r requirements.txt

#
# 2) Install Node dependencies in src/frontend
#
echo "Installing Node dependencies..."
cd src/frontend
npm install

#
# 3) Launch both FastAPI & Vite via 'npm run dev'
#
echo "Launching backend & frontend concurrently..."
npm run dev
</file>

<file path='src/backend/__init__.py'>

</file>

<file path='src/backend/backup/__init__.py'>

</file>

<file path='src/backend/backup/routes.py'>
# src/backend/backup/routes.py
"""
routes.py

Defines FastAPI endpoints for backup and versioning operations.
Provides endpoints to list backup versions and restore a note to a previous version.
"""

from fastapi import APIRouter, HTTPException, Path, Body
from fastapi.responses import JSONResponse
from typing import List

from .versioning import list_versions, create_version, restore_version

router = APIRouter(
    prefix="/backup",
    tags=["backup"],
    responses={404: {"description": "Not found"}}
)


@router.get("/versions/{note_path:path}", summary="List backup versions")
async def get_versions(note_path: str) -> JSONResponse:
    """
    List all backup versions for a given note.

    Args:
        note_path (str): Relative path to the note.

    Returns:
        JSONResponse: A JSON response containing a list of backup version filenames.
    """
    try:
        versions = list_versions(note_path)
        return JSONResponse(content={"versions": versions})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/versions/{note_path:path}", summary="Create a backup version")
async def backup_note(note_path: str) -> JSONResponse:
    """
    Create a backup version of a note.

    Args:
        note_path (str): Relative path to the note.

    Returns:
        JSONResponse: A confirmation message.
    """
    try:
        create_version(note_path)
        return JSONResponse(content={"message": "Backup created successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restore/{note_path:path}", summary="Restore a note version")
async def restore_note(
    note_path: str,
    version: str = Body(..., embed=True, description="Version filename to restore")
) -> JSONResponse:
    """
    Restore a note to a previous version.

    Args:
        note_path (str): Relative path to the note.
        version (str): The backup version filename to restore.

    Returns:
        JSONResponse: A confirmation message.
    """
    try:
        restore_version(note_path, version)
        return JSONResponse(content={"message": "Note restored successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

</file>

<file path='src/backend/backup/snapshotter.py'>
#!/usr/bin/env python3
# snapshotter.py
"""
snapshotter.py

Implements a simple snapshot mechanism for creating periodic backups of the vault.
This module can be integrated with a scheduler (or background thread) to run every
N minutes, as configured in config.py.

Example usage from another module:
    from src.backend.backup.snapshotter import create_snapshot
    create_snapshot()
"""

import shutil
from pathlib import Path
from datetime import datetime

from src.backend.config import Config

# Use the backup directory defined in the configuration and create a "snapshots" subfolder.
SNAPSHOT_DIR = Config.BACKUP_DIR / "snapshots"
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

def create_snapshot() -> None:
    """
    Create a snapshot backup of the entire vault.
    
    The snapshot is a copy of the vault directory stored with a timestamp.
    """
    vault_path = Path(Config.VAULT_DIR)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot_path = SNAPSHOT_DIR / f"vault_snapshot_{timestamp}"
    shutil.copytree(vault_path, snapshot_path)

</file>

<file path='src/backend/backup/versioning.py'>
# src/backend/backup/versioning.py
"""
versioning.py

Provides functionality for managing version history of Markdown notes.
It allows listing available versions and restoring a note to a previous version.
"""

import shutil
from pathlib import Path
from datetime import datetime
from typing import List
import os

# Import NoteManager to handle note file operations.
from src.backend.file_handler import NoteManager
# Import Config for centralized configuration values.
from src.backend.config import Config

# Use the backup directory from Config.
BACKUP_DIR = Config.BACKUP_DIR
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

def list_versions(note_path: str) -> List[str]:
    """
    List all backup versions for a given note.
    
    Args:
        note_path (str): Relative path to the note within the vault.
        
    Returns:
        List[str]: A sorted list of backup file names.
    """
    # Replace OS-specific path separators with underscores to form the backup folder name.
    note_backup_dir = BACKUP_DIR / note_path.replace(os.sep, "_")
    if not note_backup_dir.exists():
        return []
    return sorted([f.name for f in note_backup_dir.iterdir() if f.is_file()])

def create_version(note_path: str) -> None:
    """
    Create a backup version of a note by copying the current file to a backup directory.
    
    Args:
        note_path (str): Relative path to the note within the vault.
    
    Raises:
        FileNotFoundError: If the note does not exist.
    """
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
        
    Raises:
        FileNotFoundError: If the backup version is not found.
    """
    note_manager = NoteManager()
    note_backup_dir = BACKUP_DIR / note_path.replace(os.sep, "_")
    backup_file = note_backup_dir / version_file
    if not backup_file.exists():
        raise FileNotFoundError(f"Backup version not found: {version_file}")

    # Overwrite the current note with the backup version.
    full_note_path = note_manager.vault_dir / note_path
    shutil.copy(backup_file, full_note_path)

</file>

<file path='src/backend/canvas/__init__.py'>

</file>

<file path='src/backend/canvas/canvas_store.py'>
# src/backend/canvas/canvas_store.py
"""
canvas_store.py

This module defines the CanvasStore class which handles the persistence
of the canvas layout data in a JSON file. The canvas layout includes nodes
and edges representing the infinite canvas workspace.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict

# Constant for the canvas storage file
CANVAS_FILE = Path(os.getcwd(), "storage", "canvas", "canvas_layout.json")


class CanvasStore:
    """
    Manages storage and retrieval of canvas layout data.
    """

    def __init__(self) -> None:
        """
        Initialize the CanvasStore and ensure the storage directory exists.
        """
        canvas_dir = CANVAS_FILE.parent
        canvas_dir.mkdir(parents=True, exist_ok=True)

    def save_canvas(self, layout: Dict[str, Any]) -> None:
        """
        Save the canvas layout data to a JSON file.

        Args:
            layout (Dict[str, Any]): The canvas layout data including nodes and edges.
        """
        with open(CANVAS_FILE, "w", encoding="utf-8") as f:
            json.dump(layout, f, indent=4)

    def load_canvas(self) -> Dict[str, Any]:
        """
        Load the canvas layout data from the JSON file.

        Returns:
            Dict[str, Any]: The canvas layout data. Returns an empty layout if file does not exist.
        """
        if not CANVAS_FILE.exists():
            return {"nodes": [], "edges": []}
        with open(CANVAS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

</file>

<file path='src/backend/canvas/node_processor.py'>
# src/backend/canvas/node_processor.py
"""
node_processor.py

This module provides functionality to process nodes and their relationships
within the canvas. It supports operations such as grouping nodes and validating
connections between nodes.
"""

from typing import List, Dict, Any


class NodeProcessor:
    """
    Processes nodes and connections in the canvas layout.
    """

    def group_nodes(self, nodes: List[Dict[str, Any]], group_key: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group nodes based on a specific key.

        Args:
            nodes (List[Dict[str, Any]]): List of node dictionaries.
            group_key (str): The key to group nodes by.

        Returns:
            Dict[str, List[Dict[str, Any]]]: A dictionary with group_key values as keys and lists of nodes as values.
        """
        grouped = {}
        for node in nodes:
            key = node.get(group_key, "ungrouped")
            grouped.setdefault(key, []).append(node)
        return grouped

    def validate_connection(self, source_node: Dict[str, Any], target_node: Dict[str, Any], connection_type: str) -> bool:
        """
        Validate a connection between two nodes based on connection type.

        Args:
            source_node (Dict[str, Any]): The source node data.
            target_node (Dict[str, Any]): The target node data.
            connection_type (str): Type of connection (e.g., "arrow", "line").

        Returns:
            bool: True if the connection is valid, False otherwise.
        """
        # Example validation: ensure nodes are not the same and connection type is supported
        if source_node.get("id") == target_node.get("id"):
            return False
        if connection_type not in ["arrow", "line"]:
            return False
        return True

</file>

<file path='src/backend/canvas/routes.py'>
# src/backend/canvas/routes.py
"""
routes.py

Defines FastAPI endpoints for canvas operations.
Provides endpoints to retrieve and update the infinite canvas layout.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Any, Dict

from .canvas_store import CanvasStore

router = APIRouter(
    prefix="/canvas",
    tags=["canvas"],
    responses={404: {"description": "Not found"}}
)

canvas_store = CanvasStore()


@router.get("/", summary="Retrieve canvas layout")
async def get_canvas() -> JSONResponse:
    """
    Retrieve the current canvas layout.

    Returns:
        JSONResponse: A JSON response containing the canvas layout.
    """
    try:
        layout = canvas_store.load_canvas()
        return JSONResponse(content=layout)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", summary="Update canvas layout")
async def update_canvas(layout: Dict[str, Any]) -> JSONResponse:
    """
    Update the canvas layout with new data.

    Args:
        layout (Dict[str, Any]): The new canvas layout data.

    Returns:
        JSONResponse: A JSON response confirming the update.
    """
    try:
        canvas_store.save_canvas(layout)
        return JSONResponse(content={"message": "Canvas updated successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

</file>

<file path='src/backend/config.py'>
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


</file>

<file path='src/backend/database/__init__.py'>

</file>

<file path='src/backend/database/base.py'>
# src/backend/database/base.py
"""
base.py

Defines the declarative base for all SQLAlchemy models.
This base is used for all model definitions to ensure a consistent ORM layer.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

</file>

<file path='src/backend/database/init_db.py'>
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

</file>

<file path='src/backend/database/sessions.py'>
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

</file>

<file path='src/backend/file_handler.py'>
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

</file>

<file path='src/backend/main.py'>
#!/usr/bin/env python3
# main.py
"""
main.py

The entry point for the local note-taking and task management application backend.
This module sets up the FastAPI application, integrates:
 - Notes endpoints (CRUD + daily notes)
 - Task endpoints (CRUD + recurrence)
 - Canvas endpoints
 - Search functionality
 - Backup/versioning endpoints
 - Periodic snapshots (NEW)

It starts the local development server with uvicorn.

Usage:
    python main.py
or:
    uvicorn main:app --host 127.0.0.1 --port 8000 --reload
"""

import threading
import time
import datetime

from fastapi import FastAPI, HTTPException, Path, Body
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from src.backend.config import Config
from src.backend.file_handler import NoteManager
from src.backend.tasks.routes import router as tasks_router
from src.backend.canvas.routes import router as canvas_router
from src.backend.search.routes import router as search_router
from src.backend.backup.routes import router as backup_router
from src.backend.database.init_db import init_db
from src.backend.backup.snapshotter import create_snapshot


app = FastAPI(
    title="Local Note-Taking & Task Management App",
    version="0.3.0",
    description="A local, file-based note-taking and task management application inspired by Obsidian."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

note_manager = NoteManager()


# -----------------------------
#  BACKGROUND SNAPSHOT THREAD
# -----------------------------
def run_snapshots_in_background() -> None:
    """
    Runs periodic snapshots of the vault in a background thread,
    using the interval specified in Config.
    """
    while True:
        time.sleep(Config.SNAPSHOT_INTERVAL_MINUTES * 60)
        try:
            create_snapshot()
            print(f"[{datetime.datetime.now()}] Snapshot created.")
        except Exception as ex:
            print(f"Error creating snapshot: {ex}")


@app.on_event("startup")
def on_startup() -> None:
    """
    Automatically create database tables if they do not exist,
    and optionally start a background thread for periodic snapshots.
    """
    init_db()

    # Start the periodic snapshot thread if enabled
    if Config.ENABLE_PERIODIC_SNAPSHOTS:
        thread = threading.Thread(target=run_snapshots_in_background, daemon=True)
        thread.start()
        print(f"Periodic snapshots enabled (every {Config.SNAPSHOT_INTERVAL_MINUTES} min).")


# -----------------------------
# NOTE ENDPOINTS
# -----------------------------

@app.get("/notes", summary="List all notes")
async def list_notes() -> JSONResponse:
    """
    Retrieve a list of all Markdown notes in the vault.
    """
    try:
        notes = note_manager.list_notes()
        return JSONResponse(content={"notes": notes})
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@app.get("/notes/{note_path:path}", summary="Retrieve a note")
async def get_note(
    note_path: str = Path(..., description="Relative path to the note file")
) -> JSONResponse:
    """
    Retrieve the content of a specific Markdown note.
    """
    try:
        content = note_manager.read_note(note_path)
        return JSONResponse(content={"note": note_path, "content": content})
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Note not found")
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@app.post("/notes", summary="Create a new note")
async def create_note(
    note_name: str = Body(..., embed=True, description="Name of the new note"),
    content: str = Body("", embed=True, description="Initial content for the note")
) -> JSONResponse:
    """
    Create a new Markdown note with the specified name and optional content.
    """
    try:
        note_path = note_manager.create_note(note_name, content)
        return JSONResponse(content={"message": "Note created", "note": note_path})
    except FileExistsError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@app.put("/notes/{note_path:path}", summary="Update an existing note")
async def update_note(
    note_path: str = Path(..., description="Relative path to the note file"),
    content: str = Body(..., embed=True, description="New content for the note")
) -> JSONResponse:
    """
    Update an existing Markdown note.
    """
    try:
        _ = note_manager.read_note(note_path)  # Ensure it exists
        note_manager.write_note(note_path, content)
        return JSONResponse(content={"message": "Note updated", "note": note_path})
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Note not found")
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


# -------------------------------------------------------------------------
#       DAILY NOTE ENDPOINT
# -------------------------------------------------------------------------
@app.post("/notes/daily", summary="Create or open a daily note")
async def create_daily_note(
    date_str: str = Body(None, embed=True, description="YYYY-MM-DD format; defaults to today")
) -> JSONResponse:
    """
    Create (if missing) and return a daily note, stored in the 'daily' subfolder.
    If date_str is not provided, today's date is used.
    If a daily template is configured, it will be used when creating a new note.
    """
    try:
        if date_str is None:
            date_str = datetime.date.today().strftime(Config.DAILY_NOTES_DATE_FORMAT)

        daily_filename = date_str + Config.NOTE_EXTENSION

        # We create a dedicated NoteManager pointing to daily subfolder:
        daily_manager = NoteManager(str(Config.DAILY_NOTES_DIR))

        # Check if note already exists
        existing_notes = daily_manager.list_notes()
        if daily_filename in existing_notes:
            # If it exists, just read and return
            content = daily_manager.read_note(daily_filename)
            return JSONResponse(content={
                "message": f"Daily note for {date_str} already exists.",
                "note": f"daily/{daily_filename}",
                "content": content
            })

        # If it doesn't exist, try to load template
        template_content = ""
        if Config.DAILY_NOTES_TEMPLATE.exists():
            try:
                template_content = Config.DAILY_NOTES_TEMPLATE.read_text(encoding="utf-8")
            except Exception:
                template_content = ""
        else:
            # Fallback to minimal
            template_content = f"# {date_str} Daily Note\n\n"

        # Create the note with the template
        note_path = daily_manager.create_note(daily_filename, template_content)
        return JSONResponse(content={
            "message": f"Daily note created for {date_str}.",
            "note": f"daily/{daily_filename}",
            "content": template_content
        })
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


if __name__ == "__main__":
    uvicorn.run("main:app", host=Config.HOST, port=Config.PORT, reload=True)

</file>

<file path='src/backend/search/__init__.py'>

</file>

<file path='src/backend/search/indexer.py'>
# src/backend/search/indexer.py
"""
indexer.py

Provides full-text indexing functionality for Markdown notes using Whoosh.
Builds and maintains a search index for fast querying of note content.
"""

from whoosh import index
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import QueryParser
from pathlib import Path

# Import Config for centralized configuration values.
from src.backend.config import Config
from src.backend.file_handler import NoteManager

# Use the search index directory from configuration.
INDEX_DIR = Config.SEARCH_INDEX_DIR
INDEX_DIR.mkdir(parents=True, exist_ok=True)

def get_schema():
    """
    Define and return the Whoosh schema for indexing notes.
    
    Returns:
        Schema: A Whoosh Schema object defining the fields for indexing.
    """
    return Schema(
        path=ID(stored=True, unique=True),
        content=TEXT(stored=True)
    )

def create_index() -> index.Index:
    """
    Create a new index if one doesn't exist, or open the existing index.
    
    Returns:
        index.Index: The Whoosh index object.
    """
    if not index.exists_in(INDEX_DIR):
        schema = get_schema()
        idx = index.create_in(INDEX_DIR, schema)
    else:
        idx = index.open_dir(INDEX_DIR)
    return idx

def build_index() -> None:
    """
    Build or rebuild the search index by indexing all Markdown notes.
    """
    idx = create_index()
    writer = idx.writer()
    note_manager = NoteManager()
    # Iterate through all notes and add or update them in the index.
    for note_path in note_manager.list_notes():
        try:
            content = note_manager.read_note(note_path)
            writer.update_document(path=note_path, content=content)
        except Exception as e:
            # Log the error for debugging purposes.
            print(f"Error indexing {note_path}: {e}")
    writer.commit()

def search_notes(query_str: str) -> list:
    """
    Search the index for notes matching the query string.
    
    Args:
        query_str (str): The search query.
    
    Returns:
        list: A list of note paths that match the search query.
    """
    idx = create_index()
    qp = QueryParser("content", schema=idx.schema)
    query = qp.parse(query_str)
    results = []
    with idx.searcher() as searcher:
        hits = searcher.search(query, limit=10)
        for hit in hits:
            results.append(hit["path"])
    return results

</file>

<file path='src/backend/search/query_parser.py'>
# src/backend/search/query_parser.py
"""
query_parser.py

Provides advanced query parsing for search functionality.
This module can be extended to support parsing of tags, dates, and other metadata.
"""

def parse_query(query_str: str) -> dict:
    """
    Parse the search query string and extract components such as text, tags, and dates.

    Args:
        query_str (str): The raw search query string.

    Returns:
        dict: A dictionary with parsed query components.
    """
    # For simplicity, this implementation splits the query into words.
    # Future enhancements can include regex-based extraction of tags or dates.
    components = query_str.split()
    return {"text": " ".join(components), "raw": query_str}

</file>

<file path='src/backend/search/routes.py'>
# src/backend/search/routes.py
"""
routes.py

Defines FastAPI endpoints for search functionality.
Provides an endpoint to search through Markdown notes.
This updated version integrates advanced query parsing using query_parser.
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List

from .indexer import search_notes, build_index
from .query_parser import parse_query  # Import advanced query parser

router = APIRouter(
    prefix="/search",
    tags=["search"],
    responses={404: {"description": "Not found"}}
)

@router.post("/reindex", summary="Rebuild search index")
async def reindex() -> JSONResponse:
    """
    Rebuild the full-text search index for Markdown notes.

    Returns:
        JSONResponse: A confirmation message.
    """
    try:
        build_index()
        return JSONResponse(content={"message": "Search index rebuilt successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", summary="Search notes", response_model=List[str])
async def search(query: str = Query(..., description="Search query string")) -> JSONResponse:
    """
    Search for notes matching the provided query string.
    The query is parsed to extract text components and then passed to the search index.
    
    Args:
        query (str): The raw search query string.
        
    Returns:
        JSONResponse: A JSON response containing a list of matching note paths.
    """
    try:
        # Parse the query to extract search text and metadata
        parsed_query = parse_query(query)
        # Use the text component for full-text search
        results = search_notes(parsed_query.get("text", ""))
        return JSONResponse(content={"results": results})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

</file>

<file path='src/backend/tasks/__init__.py'>

</file>

<file path='src/backend/tasks/models.py'>
# src/backend/tasks/models.py
"""
models.py

Defines the SQLAlchemy model for task management.
This module includes the Task model and the TaskStatus enumeration.
"""

import datetime
import enum
from sqlalchemy import Column, Integer, String, DateTime, Enum

# Updated import path for Base
from src.backend.database.base import Base  # Shared SQLAlchemy declarative base


class TaskStatus(str, enum.Enum):
    """
    Enumeration for task status values.
    Updated to match the short uppercase strings used by the frontend.
    """
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class Task(Base):
    """
    Represents a task with properties such as title, description, due date,
    priority, status, recurrence rule, and an optional link to a note.
    """
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, default="")
    due_date = Column(DateTime, nullable=True)
    priority = Column(Integer, default=2)  # 1: High, 2: Medium, 3: Low
    status = Column(Enum(TaskStatus), default=TaskStatus.TODO)
    recurrence = Column(String, nullable=True)  # e.g., "daily", "weekly", "monthly"
    note_path = Column(String, nullable=True)  # Optional link to a related note
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow
    )
</file>

<file path='src/backend/tasks/recurrence.py'>
# src/backend/tasks/recurrence.py
"""
recurrence.py

Provides simple recurrence logic for tasks.
Contains functions to calculate the next due date based on a given recurrence rule.
"""

import datetime


def get_next_due_date(current_due_date: datetime.datetime, recurrence: str) -> datetime.datetime:
    """
    Calculate the next due date based on the current due date and recurrence rule.

    Args:
        current_due_date (datetime.datetime): The current due date.
        recurrence (str): The recurrence rule ("daily", "weekly", "monthly").

    Returns:
        datetime.datetime: The computed next due date.
    """
    recurrence_lower = recurrence.lower()
    if recurrence_lower == "daily":
        return current_due_date + datetime.timedelta(days=1)
    elif recurrence_lower == "weekly":
        return current_due_date + datetime.timedelta(weeks=1)
    elif recurrence_lower == "monthly":
        # For simplicity, approximate a month as 30 days.
        return current_due_date + datetime.timedelta(days=30)
    else:
        # Return the unchanged due date if the recurrence rule is unrecognized.
        return current_due_date

</file>

<file path='src/backend/tasks/routes.py'>
# src/backend/tasks/routes.py
"""
routes.py

Defines FastAPI routes for task management.
Provides endpoints to create, read, update, and delete tasks, plus a custom endpoint for
completing recurring tasks.

Wave 2 Enhancements:
- Added a 'complete_task' endpoint to handle recurring tasks more gracefully.
  If a task has a recurrence rule, this endpoint will complete the current task
  and create a new task instance with the next due date.
"""

import datetime
from typing import List, Optional, Generator

from fastapi import APIRouter, Depends, HTTPException, Path, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Updated imports for database and tasks
from src.backend.database.sessions import SessionLocal
from src.backend.tasks.models import Task, TaskStatus
from src.backend.tasks.recurrence import get_next_due_date

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    responses={404: {"description": "Not found"}}
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session.
    
    Yields:
        Session: SQLAlchemy session object.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class TaskCreate(BaseModel):
    """
    Pydantic model for creating a new task.
    """
    title: str
    description: Optional[str] = ""
    due_date: Optional[datetime.datetime] = None
    priority: Optional[int] = 2  # 1: High, 2: Medium, 3: Low
    recurrence: Optional[str] = None
    note_path: Optional[str] = None


class TaskUpdate(BaseModel):
    """
    Pydantic model for updating an existing task.
    All fields are optional to allow partial updates.
    """
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime.datetime] = None
    priority: Optional[int] = None
    status: Optional[TaskStatus] = None
    recurrence: Optional[str] = None
    note_path: Optional[str] = None


class TaskResponse(BaseModel):
    """
    Pydantic model for task responses.
    """
    id: int
    title: str
    description: Optional[str]
    due_date: Optional[datetime.datetime]
    priority: int
    status: TaskStatus
    recurrence: Optional[str]
    note_path: Optional[str]
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True  # Allows Pydantic to read from SQLAlchemy model attributes


@router.post("/", response_model=TaskResponse, summary="Create a new task")
def create_task(task: TaskCreate, db: Session = Depends(get_db)) -> Task:
    """
    Create a new task with the provided details.
    
    Args:
        task (TaskCreate): Task data from the request body.
        db (Session): Database session dependency.

    Returns:
        Task: The newly created SQLAlchemy Task object.
    """
    new_task = Task(
        title=task.title,
        description=task.description,
        due_date=task.due_date,
        priority=task.priority,
        recurrence=task.recurrence,
        note_path=task.note_path
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task


@router.get("/", response_model=List[TaskResponse], summary="Retrieve all tasks")
def read_tasks(db: Session = Depends(get_db)) -> List[Task]:
    """
    Retrieve a list of all tasks from the database.

    Args:
        db (Session): Database session dependency.

    Returns:
        List[Task]: A list of SQLAlchemy Task objects.
    """
    tasks = db.query(Task).all()
    return tasks


@router.get("/{task_id}", response_model=TaskResponse, summary="Retrieve a task by ID")
def read_task(
    task_id: int = Path(..., description="The ID of the task"),
    db: Session = Depends(get_db)
) -> Task:
    """
    Retrieve a specific task by its ID.
    
    Args:
        task_id (int): The ID of the task to retrieve.
        db (Session): Database session dependency.
    
    Returns:
        Task: The requested SQLAlchemy Task object.
    
    Raises:
        HTTPException: If the task is not found.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{task_id}", response_model=TaskResponse, summary="Update a task")
def update_task(
    task_id: int = Path(..., description="The ID of the task to update"),
    task_update: TaskUpdate = Body(...),
    db: Session = Depends(get_db)
) -> Task:
    """
    Update an existing task with new data.

    Args:
        task_id (int): The ID of the task to update.
        task_update (TaskUpdate): Updated task data.
        db (Session): Database session dependency.

    Returns:
        Task: The updated SQLAlchemy Task object.

    Raises:
        HTTPException: If the task is not found.
    """
    existing_task = db.query(Task).filter(Task.id == task_id).first()
    if not existing_task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = task_update.dict(exclude_unset=True)

    # Update existing fields with new values.
    for key, value in update_data.items():
        setattr(existing_task, key, value)

    db.commit()
    db.refresh(existing_task)
    return existing_task


@router.delete("/{task_id}", summary="Delete a task")
def delete_task(
    task_id: int = Path(..., description="The ID of the task to delete"),
    db: Session = Depends(get_db)
) -> dict:
    """
    Delete a task by its ID.
    
    Args:
        task_id (int): The ID of the task to delete.
        db (Session): Database session dependency.
    
    Returns:
        dict: A message confirming the task deletion.

    Raises:
        HTTPException: If the task is not found.
    """
    task_obj = db.query(Task).filter(Task.id == task_id).first()
    if not task_obj:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task_obj)
    db.commit()
    return {"message": "Task deleted successfully"}


class CompleteTaskResponse(BaseModel):
    """
    Pydantic model for the response of completing a task.
    """
    completed_task: TaskResponse
    new_task: Optional[TaskResponse] = None


@router.post("/{task_id}/complete", response_model=CompleteTaskResponse, summary="Complete a task")
def complete_task(
    task_id: int = Path(..., description="The ID of the task to complete"),
    db: Session = Depends(get_db)
) -> CompleteTaskResponse:
    """
    Mark a task as completed. If the task has a recurrence rule, this endpoint will:
     - Complete the current task by setting its status to 'COMPLETED'.
     - Create a new task with the same title, description, priority, and recurrence,
       but with a due date shifted according to the recurrence rule.

    Args:
        task_id (int): The ID of the task to complete.
        db (Session): Database session.

    Returns:
        CompleteTaskResponse: A Pydantic model containing the completed task and the new task
                              (if recurrence is applied).

    Raises:
        HTTPException: If the task is not found.
    """
    existing_task = db.query(Task).filter(Task.id == task_id).first()
    if not existing_task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Mark current task as completed
    existing_task.status = TaskStatus.COMPLETED
    db.commit()
    db.refresh(existing_task)

    new_task_obj = None

    # If the task has a recurrence rule and a valid due_date, create a new task
    if existing_task.recurrence and existing_task.due_date:
        next_due = get_next_due_date(existing_task.due_date, existing_task.recurrence)
        # Build a new task using the existing task's data
        new_task_obj = Task(
            title=existing_task.title,
            description=existing_task.description,
            due_date=next_due,
            priority=existing_task.priority,
            status=TaskStatus.TODO,  # New cycle starts in TODO status
            recurrence=existing_task.recurrence,
            note_path=existing_task.note_path
        )
        db.add(new_task_obj)
        db.commit()
        db.refresh(new_task_obj)

    return CompleteTaskResponse(
        completed_task=existing_task,
        new_task=new_task_obj
    )

</file>

<file path='src/frontend/index.html'>
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <title>Local Notes Vue App</title>
  </head>
  <body>
    <!-- Important: The ID here must match app.mount('#app') in main.js -->
    <div id="app"></div>
    <!-- Vite expects to load main.js from /src/main.js or /src/main.ts -->
    <script type="module" src="/src/main.js"></script>
  </body>
</html>
</file>

<file path='src/frontend/package-lock.json'>
{
  "name": "local-notes-app",
  "version": "0.1.0",
  "lockfileVersion": 3,
  "requires": true,
  "packages": {
    "": {
      "name": "local-notes-app",
      "version": "0.1.0",
      "dependencies": {
        "axios": "^1.3.2",
        "d3": "^7.8.2",
        "marked": "^5.1.0",
        "vue": "^3.2.47"
      },
      "devDependencies": {
        "@vitejs/plugin-vue": "^4.0.0",
        "concurrently": "^7.6.0",
        "vite": "^4.0.0"
      }
    },
    "node_modules/@babel/helper-string-parser": {
      "version": "7.25.9",
      "resolved": "https://registry.npmjs.org/@babel/helper-string-parser/-/helper-string-parser-7.25.9.tgz",
      "integrity": "sha512-4A/SCr/2KLd5jrtOMFzaKjVtAei3+2r/NChoBNoZ3EyP/+GlhoaEGoWOZUmFmoITP7zOJyHIMm+DYRd8o3PvHA==",
      "engines": {
        "node": ">=6.9.0"
      }
    },
    "node_modules/@babel/helper-validator-identifier": {
      "version": "7.25.9",
      "resolved": "https://registry.npmjs.org/@babel/helper-validator-identifier/-/helper-validator-identifier-7.25.9.tgz",
      "integrity": "sha512-Ed61U6XJc3CVRfkERJWDz4dJwKe7iLmmJsbOGu9wSloNSFttHV0I8g6UAgb7qnK5ly5bGLPd4oXZlxCdANBOWQ==",
      "engines": {
        "node": ">=6.9.0"
      }
    },
    "node_modules/@babel/parser": {
      "version": "7.26.8",
      "resolved": "https://registry.npmjs.org/@babel/parser/-/parser-7.26.8.tgz",
      "integrity": "sha512-TZIQ25pkSoaKEYYaHbbxkfL36GNsQ6iFiBbeuzAkLnXayKR1yP1zFe+NxuZWWsUyvt8icPU9CCq0sgWGXR1GEw==",
      "dependencies": {
        "@babel/types": "^7.26.8"
      },
      "bin": {
        "parser": "bin/babel-parser.js"
      },
      "engines": {
        "node": ">=6.0.0"
      }
    },
    "node_modules/@babel/runtime": {
      "version": "7.26.7",
      "resolved": "https://registry.npmjs.org/@babel/runtime/-/runtime-7.26.7.tgz",
      "integrity": "sha512-AOPI3D+a8dXnja+iwsUqGRjr1BbZIe771sXdapOtYI531gSqpi92vXivKcq2asu/DFpdl1ceFAKZyRzK2PCVcQ==",
      "dev": true,
      "dependencies": {
        "regenerator-runtime": "^0.14.0"
      },
      "engines": {
        "node": ">=6.9.0"
      }
    },
    "node_modules/@babel/types": {
      "version": "7.26.8",
      "resolved": "https://registry.npmjs.org/@babel/types/-/types-7.26.8.tgz",
      "integrity": "sha512-eUuWapzEGWFEpHFxgEaBG8e3n6S8L3MSu0oda755rOfabWPnh0Our1AozNFVUxGFIhbKgd1ksprsoDGMinTOTA==",
      "dependencies": {
        "@babel/helper-string-parser": "^7.25.9",
        "@babel/helper-validator-identifier": "^7.25.9"
      },
      "engines": {
        "node": ">=6.9.0"
      }
    },
    "node_modules/@esbuild/android-arm": {
      "version": "0.18.20",
      "resolved": "https://registry.npmjs.org/@esbuild/android-arm/-/android-arm-0.18.20.tgz",
      "integrity": "sha512-fyi7TDI/ijKKNZTUJAQqiG5T7YjJXgnzkURqmGj13C6dCqckZBLdl4h7bkhHt/t0WP+zO9/zwroDvANaOqO5Sw==",
      "cpu": [
        "arm"
      ],
      "dev": true,
      "optional": true,
      "os": [
        "android"
      ],
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/@esbuild/android-arm64": {
      "version": "0.18.20",
      "resolved": "https://registry.npmjs.org/@esbuild/android-arm64/-/android-arm64-0.18.20.tgz",
      "integrity": "sha512-Nz4rJcchGDtENV0eMKUNa6L12zz2zBDXuhj/Vjh18zGqB44Bi7MBMSXjgunJgjRhCmKOjnPuZp4Mb6OKqtMHLQ==",
      "cpu": [
        "arm64"
      ],
      "dev": true,
      "optional": true,
      "os": [
        "android"
      ],
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/@esbuild/android-x64": {
      "version": "0.18.20",
      "resolved": "https://registry.npmjs.org/@esbuild/android-x64/-/android-x64-0.18.20.tgz",
      "integrity": "sha512-8GDdlePJA8D6zlZYJV/jnrRAi6rOiNaCC/JclcXpB+KIuvfBN4owLtgzY2bsxnx666XjJx2kDPUmnTtR8qKQUg==",
      "cpu": [
        "x64"
      ],
      "dev": true,
      "optional": true,
      "os": [
        "android"
      ],
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/@esbuild/darwin-arm64": {
      "version": "0.18.20",
      "resolved": "https://registry.npmjs.org/@esbuild/darwin-arm64/-/darwin-arm64-0.18.20.tgz",
      "integrity": "sha512-bxRHW5kHU38zS2lPTPOyuyTm+S+eobPUnTNkdJEfAddYgEcll4xkT8DB9d2008DtTbl7uJag2HuE5NZAZgnNEA==",
      "cpu": [
        "arm64"
      ],
      "dev": true,
      "optional": true,
      "os": [
        "darwin"
      ],
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/@esbuild/darwin-x64": {
      "version": "0.18.20",
      "resolved": "https://registry.npmjs.org/@esbuild/darwin-x64/-/darwin-x64-0.18.20.tgz",
      "integrity": "sha512-pc5gxlMDxzm513qPGbCbDukOdsGtKhfxD1zJKXjCCcU7ju50O7MeAZ8c4krSJcOIJGFR+qx21yMMVYwiQvyTyQ==",
      "cpu": [
        "x64"
      ],
      "dev": true,
      "optional": true,
      "os": [
        "darwin"
      ],
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/@esbuild/freebsd-arm64": {
      "version": "0.18.20",
      "resolved": "https://registry.npmjs.org/@esbuild/freebsd-arm64/-/freebsd-arm64-0.18.20.tgz",
      "integrity": "sha512-yqDQHy4QHevpMAaxhhIwYPMv1NECwOvIpGCZkECn8w2WFHXjEwrBn3CeNIYsibZ/iZEUemj++M26W3cNR5h+Tw==",
      "cpu": [
        "arm64"
      ],
      "dev": true,
      "optional": true,
      "os": [
        "freebsd"
      ],
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/@esbuild/freebsd-x64": {
      "version": "0.18.20",
      "resolved": "https://registry.npmjs.org/@esbuild/freebsd-x64/-/freebsd-x64-0.18.20.tgz",
      "integrity": "sha512-tgWRPPuQsd3RmBZwarGVHZQvtzfEBOreNuxEMKFcd5DaDn2PbBxfwLcj4+aenoh7ctXcbXmOQIn8HI6mCSw5MQ==",
      "cpu": [
        "x64"
      ],
      "dev": true,
      "optional": true,
      "os": [
        "freebsd"
      ],
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/@esbuild/linux-arm": {
      "version": "0.18.20",
      "resolved": "https://registry.npmjs.org/@esbuild/linux-arm/-/linux-arm-0.18.20.tgz",
      "integrity": "sha512-/5bHkMWnq1EgKr1V+Ybz3s1hWXok7mDFUMQ4cG10AfW3wL02PSZi5kFpYKrptDsgb2WAJIvRcDm+qIvXf/apvg==",
      "cpu": [
        "arm"
      ],
      "dev": true,
      "optional": true,
      "os": [
        "linux"
      ],
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/@esbuild/linux-arm64": {
      "version": "0.18.20",
      "resolved": "https://registry.npmjs.org/@esbuild/linux-arm64/-/linux-arm64-0.18.20.tgz",
      "integrity": "sha512-2YbscF+UL7SQAVIpnWvYwM+3LskyDmPhe31pE7/aoTMFKKzIc9lLbyGUpmmb8a8AixOL61sQ/mFh3jEjHYFvdA==",
      "cpu": [
        "arm64"
      ],
      "dev": true,
      "optional": true,
      "os": [
        "linux"
      ],
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/@esbuild/linux-ia32": {
      "version": "0.18.20",
      "resolved": "https://registry.npmjs.org/@esbuild/linux-ia32/-/linux-ia32-0.18.20.tgz",
      "integrity": "sha512-P4etWwq6IsReT0E1KHU40bOnzMHoH73aXp96Fs8TIT6z9Hu8G6+0SHSw9i2isWrD2nbx2qo5yUqACgdfVGx7TA==",
      "cpu": [
        "ia32"
      ],
      "dev": true,
      "optional": true,
      "os": [
        "linux"
      ],
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/@esbuild/linux-loong64": {
      "version": "0.18.20",
      "resolved": "https://registry.npmjs.org/@esbuild/linux-loong64/-/linux-loong64-0.18.20.tgz",
      "integrity": "sha512-nXW8nqBTrOpDLPgPY9uV+/1DjxoQ7DoB2N8eocyq8I9XuqJ7BiAMDMf9n1xZM9TgW0J8zrquIb/A7s3BJv7rjg==",
      "cpu": [
        "loong64"
      ],
      "dev": true,
      "optional": true,
      "os": [
        "linux"
      ],
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/@esbuild/linux-mips64el": {
      "version": "0.18.20",
      "resolved": "https://registry.npmjs.org/@esbuild/linux-mips64el/-/linux-mips64el-0.18.20.tgz",
      "integrity": "sha512-d5NeaXZcHp8PzYy5VnXV3VSd2D328Zb+9dEq5HE6bw6+N86JVPExrA6O68OPwobntbNJ0pzCpUFZTo3w0GyetQ==",
      "cpu": [
        "mips64el"
      ],
      "dev": true,
      "optional": true,
      "os": [
        "linux"
      ],
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/@esbuild/linux-ppc64": {
      "version": "0.18.20",
      "resolved": "https://registry.npmjs.org/@esbuild/linux-ppc64/-/linux-ppc64-0.18.20.tgz",
      "integrity": "sha512-WHPyeScRNcmANnLQkq6AfyXRFr5D6N2sKgkFo2FqguP44Nw2eyDlbTdZwd9GYk98DZG9QItIiTlFLHJHjxP3FA==",
      "cpu": [
        "ppc64"
      ],
      "dev": true,
      "optional": true,
      "os": [
        "linux"
      ],
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/@esbuild/linux-riscv64": {
      "version": "0.18.20",
      "resolved": "https://registry.npmjs.org/@esbuild/linux-riscv64/-/linux-riscv64-0.18.20.tgz",
      "integrity": "sha512-WSxo6h5ecI5XH34KC7w5veNnKkju3zBRLEQNY7mv5mtBmrP/MjNBCAlsM2u5hDBlS3NGcTQpoBvRzqBcRtpq1A==",
      "cpu": [
        "riscv64"
      ],
      "dev": true,
      "optional": true,
      "os": [
        "linux"
      ],
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/@esbuild/linux-s390x": {
      "version": "0.18.20",
      "resolved": "https://registry.npmjs.org/@esbuild/linux-s390x/-/linux-s390x-0.18.20.tgz",
      "integrity": "sha512-+8231GMs3mAEth6Ja1iK0a1sQ3ohfcpzpRLH8uuc5/KVDFneH6jtAJLFGafpzpMRO6DzJ6AvXKze9LfFMrIHVQ==",
      "cpu": [
        "s390x"
      ],
      "dev": true,
      "optional": true,
      "os": [
        "linux"
      ],
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/@esbuild/linux-x64": {
      "version": "0.18.20",
      "resolved": "https://registry.npmjs.org/@esbuild/linux-x64/-/linux-x64-0.18.20.tgz",
      "integrity": "sha512-UYqiqemphJcNsFEskc73jQ7B9jgwjWrSayxawS6UVFZGWrAAtkzjxSqnoclCXxWtfwLdzU+vTpcNYhpn43uP1w==",
      "cpu": [
        "x64"
      ],
      "dev": true,
      "optional": true,
      "os": [
        "linux"
      ],
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/@esbuild/netbsd-x64": {
      "version": "0.18.20",
      "resolved": "https://registry.npmjs.org/@esbuild/netbsd-x64/-/netbsd-x64-0.18.20.tgz",
      "integrity": "sha512-iO1c++VP6xUBUmltHZoMtCUdPlnPGdBom6IrO4gyKPFFVBKioIImVooR5I83nTew5UOYrk3gIJhbZh8X44y06A==",
      "cpu": [
        "x64"
      ],
      "dev": true,
      "optional": true,
      "os": [
        "netbsd"
      ],
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/@esbuild/openbsd-x64": {
      "version": "0.18.20",
      "resolved": "https://registry.npmjs.org/@esbuild/openbsd-x64/-/openbsd-x64-0.18.20.tgz",
      "integrity": "sha512-e5e4YSsuQfX4cxcygw/UCPIEP6wbIL+se3sxPdCiMbFLBWu0eiZOJ7WoD+ptCLrmjZBK1Wk7I6D/I3NglUGOxg==",
      "cpu": [
        "x64"
      ],
      "dev": true,
      "optional": true,
      "os": [
        "openbsd"
      ],
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/@esbuild/sunos-x64": {
      "version": "0.18.20",
      "resolved": "https://registry.npmjs.org/@esbuild/sunos-x64/-/sunos-x64-0.18.20.tgz",
      "integrity": "sha512-kDbFRFp0YpTQVVrqUd5FTYmWo45zGaXe0X8E1G/LKFC0v8x0vWrhOWSLITcCn63lmZIxfOMXtCfti/RxN/0wnQ==",
      "cpu": [
        "x64"
      ],
      "dev": true,
      "optional": true,
      "os": [
        "sunos"
      ],
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/@esbuild/win32-arm64": {
      "version": "0.18.20",
      "resolved": "https://registry.npmjs.org/@esbuild/win32-arm64/-/win32-arm64-0.18.20.tgz",
      "integrity": "sha512-ddYFR6ItYgoaq4v4JmQQaAI5s7npztfV4Ag6NrhiaW0RrnOXqBkgwZLofVTlq1daVTQNhtI5oieTvkRPfZrePg==",
      "cpu": [
        "arm64"
      ],
      "dev": true,
      "optional": true,
      "os": [
        "win32"
      ],
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/@esbuild/win32-ia32": {
      "version": "0.18.20",
      "resolved": "https://registry.npmjs.org/@esbuild/win32-ia32/-/win32-ia32-0.18.20.tgz",
      "integrity": "sha512-Wv7QBi3ID/rROT08SABTS7eV4hX26sVduqDOTe1MvGMjNd3EjOz4b7zeexIR62GTIEKrfJXKL9LFxTYgkyeu7g==",
      "cpu": [
        "ia32"
      ],
      "dev": true,
      "optional": true,
      "os": [
        "win32"
      ],
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/@esbuild/win32-x64": {
      "version": "0.18.20",
      "resolved": "https://registry.npmjs.org/@esbuild/win32-x64/-/win32-x64-0.18.20.tgz",
      "integrity": "sha512-kTdfRcSiDfQca/y9QIkng02avJ+NCaQvrMejlsB3RRv5sE9rRoeBPISaZpKxHELzRxZyLvNts1P27W3wV+8geQ==",
      "cpu": [
        "x64"
      ],
      "dev": true,
      "optional": true,
      "os": [
        "win32"
      ],
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/@jridgewell/sourcemap-codec": {
      "version": "1.5.0",
      "resolved": "https://registry.npmjs.org/@jridgewell/sourcemap-codec/-/sourcemap-codec-1.5.0.tgz",
      "integrity": "sha512-gv3ZRaISU3fjPAgNsriBRqGWQL6quFx04YMPW/zD8XMLsU32mhCCbfbO6KZFLjvYpCZ8zyDEgqsgf+PwPaM7GQ=="
    },
    "node_modules/@vitejs/plugin-vue": {
      "version": "4.6.2",
      "resolved": "https://registry.npmjs.org/@vitejs/plugin-vue/-/plugin-vue-4.6.2.tgz",
      "integrity": "sha512-kqf7SGFoG+80aZG6Pf+gsZIVvGSCKE98JbiWqcCV9cThtg91Jav0yvYFC9Zb+jKetNGF6ZKeoaxgZfND21fWKw==",
      "dev": true,
      "engines": {
        "node": "^14.18.0 || >=16.0.0"
      },
      "peerDependencies": {
        "vite": "^4.0.0 || ^5.0.0",
        "vue": "^3.2.25"
      }
    },
    "node_modules/@vue/compiler-core": {
      "version": "3.5.13",
      "resolved": "https://registry.npmjs.org/@vue/compiler-core/-/compiler-core-3.5.13.tgz",
      "integrity": "sha512-oOdAkwqUfW1WqpwSYJce06wvt6HljgY3fGeM9NcVA1HaYOij3mZG9Rkysn0OHuyUAGMbEbARIpsG+LPVlBJ5/Q==",
      "dependencies": {
        "@babel/parser": "^7.25.3",
        "@vue/shared": "3.5.13",
        "entities": "^4.5.0",
        "estree-walker": "^2.0.2",
        "source-map-js": "^1.2.0"
      }
    },
    "node_modules/@vue/compiler-dom": {
      "version": "3.5.13",
      "resolved": "https://registry.npmjs.org/@vue/compiler-dom/-/compiler-dom-3.5.13.tgz",
      "integrity": "sha512-ZOJ46sMOKUjO3e94wPdCzQ6P1Lx/vhp2RSvfaab88Ajexs0AHeV0uasYhi99WPaogmBlRHNRuly8xV75cNTMDA==",
      "dependencies": {
        "@vue/compiler-core": "3.5.13",
        "@vue/shared": "3.5.13"
      }
    },
    "node_modules/@vue/compiler-sfc": {
      "version": "3.5.13",
      "resolved": "https://registry.npmjs.org/@vue/compiler-sfc/-/compiler-sfc-3.5.13.tgz",
      "integrity": "sha512-6VdaljMpD82w6c2749Zhf5T9u5uLBWKnVue6XWxprDobftnletJ8+oel7sexFfM3qIxNmVE7LSFGTpv6obNyaQ==",
      "dependencies": {
        "@babel/parser": "^7.25.3",
        "@vue/compiler-core": "3.5.13",
        "@vue/compiler-dom": "3.5.13",
        "@vue/compiler-ssr": "3.5.13",
        "@vue/shared": "3.5.13",
        "estree-walker": "^2.0.2",
        "magic-string": "^0.30.11",
        "postcss": "^8.4.48",
        "source-map-js": "^1.2.0"
      }
    },
    "node_modules/@vue/compiler-ssr": {
      "version": "3.5.13",
      "resolved": "https://registry.npmjs.org/@vue/compiler-ssr/-/compiler-ssr-3.5.13.tgz",
      "integrity": "sha512-wMH6vrYHxQl/IybKJagqbquvxpWCuVYpoUJfCqFZwa/JY1GdATAQ+TgVtgrwwMZ0D07QhA99rs/EAAWfvG6KpA==",
      "dependencies": {
        "@vue/compiler-dom": "3.5.13",
        "@vue/shared": "3.5.13"
      }
    },
    "node_modules/@vue/reactivity": {
      "version": "3.5.13",
      "resolved": "https://registry.npmjs.org/@vue/reactivity/-/reactivity-3.5.13.tgz",
      "integrity": "sha512-NaCwtw8o48B9I6L1zl2p41OHo/2Z4wqYGGIK1Khu5T7yxrn+ATOixn/Udn2m+6kZKB/J7cuT9DbWWhRxqixACg==",
      "dependencies": {
        "@vue/shared": "3.5.13"
      }
    },
    "node_modules/@vue/runtime-core": {
      "version": "3.5.13",
      "resolved": "https://registry.npmjs.org/@vue/runtime-core/-/runtime-core-3.5.13.tgz",
      "integrity": "sha512-Fj4YRQ3Az0WTZw1sFe+QDb0aXCerigEpw418pw1HBUKFtnQHWzwojaukAs2X/c9DQz4MQ4bsXTGlcpGxU/RCIw==",
      "dependencies": {
        "@vue/reactivity": "3.5.13",
        "@vue/shared": "3.5.13"
      }
    },
    "node_modules/@vue/runtime-dom": {
      "version": "3.5.13",
      "resolved": "https://registry.npmjs.org/@vue/runtime-dom/-/runtime-dom-3.5.13.tgz",
      "integrity": "sha512-dLaj94s93NYLqjLiyFzVs9X6dWhTdAlEAciC3Moq7gzAc13VJUdCnjjRurNM6uTLFATRHexHCTu/Xp3eW6yoog==",
      "dependencies": {
        "@vue/reactivity": "3.5.13",
        "@vue/runtime-core": "3.5.13",
        "@vue/shared": "3.5.13",
        "csstype": "^3.1.3"
      }
    },
    "node_modules/@vue/server-renderer": {
      "version": "3.5.13",
      "resolved": "https://registry.npmjs.org/@vue/server-renderer/-/server-renderer-3.5.13.tgz",
      "integrity": "sha512-wAi4IRJV/2SAW3htkTlB+dHeRmpTiVIK1OGLWV1yeStVSebSQQOwGwIq0D3ZIoBj2C2qpgz5+vX9iEBkTdk5YA==",
      "dependencies": {
        "@vue/compiler-ssr": "3.5.13",
        "@vue/shared": "3.5.13"
      },
      "peerDependencies": {
        "vue": "3.5.13"
      }
    },
    "node_modules/@vue/shared": {
      "version": "3.5.13",
      "resolved": "https://registry.npmjs.org/@vue/shared/-/shared-3.5.13.tgz",
      "integrity": "sha512-/hnE/qP5ZoGpol0a5mDi45bOd7t3tjYJBjsgCsivow7D48cJeV5l05RD82lPqi7gRiphZM37rnhW1l6ZoCNNnQ=="
    },
    "node_modules/ansi-regex": {
      "version": "5.0.1",
      "resolved": "https://registry.npmjs.org/ansi-regex/-/ansi-regex-5.0.1.tgz",
      "integrity": "sha512-quJQXlTSUGL2LH9SUXo8VwsY4soanhgo6LNSm84E1LBcE8s3O0wpdiRzyR9z/ZZJMlMWv37qOOb9pdJlMUEKFQ==",
      "dev": true,
      "engines": {
        "node": ">=8"
      }
    },
    "node_modules/ansi-styles": {
      "version": "4.3.0",
      "resolved": "https://registry.npmjs.org/ansi-styles/-/ansi-styles-4.3.0.tgz",
      "integrity": "sha512-zbB9rCJAT1rbjiVDb2hqKFHNYLxgtk8NURxZ3IZwD3F6NtxbXZQCnnSi1Lkx+IDohdPlFp222wVALIheZJQSEg==",
      "dev": true,
      "dependencies": {
        "color-convert": "^2.0.1"
      },
      "engines": {
        "node": ">=8"
      },
      "funding": {
        "url": "https://github.com/chalk/ansi-styles?sponsor=1"
      }
    },
    "node_modules/asynckit": {
      "version": "0.4.0",
      "resolved": "https://registry.npmjs.org/asynckit/-/asynckit-0.4.0.tgz",
      "integrity": "sha512-Oei9OH4tRh0YqU3GxhX79dM/mwVgvbZJaSNaRk+bshkj0S5cfHcgYakreBjrHwatXKbz+IoIdYLxrKim2MjW0Q=="
    },
    "node_modules/axios": {
      "version": "1.7.9",
      "resolved": "https://registry.npmjs.org/axios/-/axios-1.7.9.tgz",
      "integrity": "sha512-LhLcE7Hbiryz8oMDdDptSrWowmB4Bl6RCt6sIJKpRB4XtVf0iEgewX3au/pJqm+Py1kCASkb/FFKjxQaLtxJvw==",
      "dependencies": {
        "follow-redirects": "^1.15.6",
        "form-data": "^4.0.0",
        "proxy-from-env": "^1.1.0"
      }
    },
    "node_modules/chalk": {
      "version": "4.1.2",
      "resolved": "https://registry.npmjs.org/chalk/-/chalk-4.1.2.tgz",
      "integrity": "sha512-oKnbhFyRIXpUuez8iBMmyEa4nbj4IOQyuhc/wy9kY7/WVPcwIO9VA668Pu8RkO7+0G76SLROeyw9CpQ061i4mA==",
      "dev": true,
      "dependencies": {
        "ansi-styles": "^4.1.0",
        "supports-color": "^7.1.0"
      },
      "engines": {
        "node": ">=10"
      },
      "funding": {
        "url": "https://github.com/chalk/chalk?sponsor=1"
      }
    },
    "node_modules/chalk/node_modules/supports-color": {
      "version": "7.2.0",
      "resolved": "https://registry.npmjs.org/supports-color/-/supports-color-7.2.0.tgz",
      "integrity": "sha512-qpCAvRl9stuOHveKsn7HncJRvv501qIacKzQlO/+Lwxc9+0q2wLyv4Dfvt80/DPn2pqOBsJdDiogXGR9+OvwRw==",
      "dev": true,
      "dependencies": {
        "has-flag": "^4.0.0"
      },
      "engines": {
        "node": ">=8"
      }
    },
    "node_modules/cliui": {
      "version": "8.0.1",
      "resolved": "https://registry.npmjs.org/cliui/-/cliui-8.0.1.tgz",
      "integrity": "sha512-BSeNnyus75C4//NQ9gQt1/csTXyo/8Sb+afLAkzAptFuMsod9HFokGNudZpi/oQV73hnVK+sR+5PVRMd+Dr7YQ==",
      "dev": true,
      "dependencies": {
        "string-width": "^4.2.0",
        "strip-ansi": "^6.0.1",
        "wrap-ansi": "^7.0.0"
      },
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/color-convert": {
      "version": "2.0.1",
      "resolved": "https://registry.npmjs.org/color-convert/-/color-convert-2.0.1.tgz",
      "integrity": "sha512-RRECPsj7iu/xb5oKYcsFHSppFNnsj/52OVTRKb4zP5onXwVF3zVmmToNcOfGC+CRDpfK/U584fMg38ZHCaElKQ==",
      "dev": true,
      "dependencies": {
        "color-name": "~1.1.4"
      },
      "engines": {
        "node": ">=7.0.0"
      }
    },
    "node_modules/color-name": {
      "version": "1.1.4",
      "resolved": "https://registry.npmjs.org/color-name/-/color-name-1.1.4.tgz",
      "integrity": "sha512-dOy+3AuW3a2wNbZHIuMZpTcgjGuLU/uBL/ubcZF9OXbDo8ff4O8yVp5Bf0efS8uEoYo5q4Fx7dY9OgQGXgAsQA==",
      "dev": true
    },
    "node_modules/combined-stream": {
      "version": "1.0.8",
      "resolved": "https://registry.npmjs.org/combined-stream/-/combined-stream-1.0.8.tgz",
      "integrity": "sha512-FQN4MRfuJeHf7cBbBMJFXhKSDq+2kAArBlmRBvcvFE5BB1HZKXtSFASDhdlz9zOYwxh8lDdnvmMOe/+5cdoEdg==",
      "dependencies": {
        "delayed-stream": "~1.0.0"
      },
      "engines": {
        "node": ">= 0.8"
      }
    },
    "node_modules/commander": {
      "version": "7.2.0",
      "resolved": "https://registry.npmjs.org/commander/-/commander-7.2.0.tgz",
      "integrity": "sha512-QrWXB+ZQSVPmIWIhtEO9H+gwHaMGYiF5ChvoJ+K9ZGHG/sVsa6yiesAD1GC/x46sET00Xlwo1u49RVVVzvcSkw==",
      "engines": {
        "node": ">= 10"
      }
    },
    "node_modules/concurrently": {
      "version": "7.6.0",
      "resolved": "https://registry.npmjs.org/concurrently/-/concurrently-7.6.0.tgz",
      "integrity": "sha512-BKtRgvcJGeZ4XttiDiNcFiRlxoAeZOseqUvyYRUp/Vtd+9p1ULmeoSqGsDA+2ivdeDFpqrJvGvmI+StKfKl5hw==",
      "dev": true,
      "dependencies": {
        "chalk": "^4.1.0",
        "date-fns": "^2.29.1",
        "lodash": "^4.17.21",
        "rxjs": "^7.0.0",
        "shell-quote": "^1.7.3",
        "spawn-command": "^0.0.2-1",
        "supports-color": "^8.1.0",
        "tree-kill": "^1.2.2",
        "yargs": "^17.3.1"
      },
      "bin": {
        "conc": "dist/bin/concurrently.js",
        "concurrently": "dist/bin/concurrently.js"
      },
      "engines": {
        "node": "^12.20.0 || ^14.13.0 || >=16.0.0"
      },
      "funding": {
        "url": "https://github.com/open-cli-tools/concurrently?sponsor=1"
      }
    },
    "node_modules/csstype": {
      "version": "3.1.3",
      "resolved": "https://registry.npmjs.org/csstype/-/csstype-3.1.3.tgz",
      "integrity": "sha512-M1uQkMl8rQK/szD0LNhtqxIPLpimGm8sOBwU7lLnCpSbTyY3yeU1Vc7l4KT5zT4s/yOxHH5O7tIuuLOCnLADRw=="
    },
    "node_modules/d3": {
      "version": "7.9.0",
      "resolved": "https://registry.npmjs.org/d3/-/d3-7.9.0.tgz",
      "integrity": "sha512-e1U46jVP+w7Iut8Jt8ri1YsPOvFpg46k+K8TpCb0P+zjCkjkPnV7WzfDJzMHy1LnA+wj5pLT1wjO901gLXeEhA==",
      "dependencies": {
        "d3-array": "3",
        "d3-axis": "3",
        "d3-brush": "3",
        "d3-chord": "3",
        "d3-color": "3",
        "d3-contour": "4",
        "d3-delaunay": "6",
        "d3-dispatch": "3",
        "d3-drag": "3",
        "d3-dsv": "3",
        "d3-ease": "3",
        "d3-fetch": "3",
        "d3-force": "3",
        "d3-format": "3",
        "d3-geo": "3",
        "d3-hierarchy": "3",
        "d3-interpolate": "3",
        "d3-path": "3",
        "d3-polygon": "3",
        "d3-quadtree": "3",
        "d3-random": "3",
        "d3-scale": "4",
        "d3-scale-chromatic": "3",
        "d3-selection": "3",
        "d3-shape": "3",
        "d3-time": "3",
        "d3-time-format": "4",
        "d3-timer": "3",
        "d3-transition": "3",
        "d3-zoom": "3"
      },
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-array": {
      "version": "3.2.4",
      "resolved": "https://registry.npmjs.org/d3-array/-/d3-array-3.2.4.tgz",
      "integrity": "sha512-tdQAmyA18i4J7wprpYq8ClcxZy3SC31QMeByyCFyRt7BVHdREQZ5lpzoe5mFEYZUWe+oq8HBvk9JjpibyEV4Jg==",
      "dependencies": {
        "internmap": "1 - 2"
      },
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-axis": {
      "version": "3.0.0",
      "resolved": "https://registry.npmjs.org/d3-axis/-/d3-axis-3.0.0.tgz",
      "integrity": "sha512-IH5tgjV4jE/GhHkRV0HiVYPDtvfjHQlQfJHs0usq7M30XcSBvOotpmH1IgkcXsO/5gEQZD43B//fc7SRT5S+xw==",
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-brush": {
      "version": "3.0.0",
      "resolved": "https://registry.npmjs.org/d3-brush/-/d3-brush-3.0.0.tgz",
      "integrity": "sha512-ALnjWlVYkXsVIGlOsuWH1+3udkYFI48Ljihfnh8FZPF2QS9o+PzGLBslO0PjzVoHLZ2KCVgAM8NVkXPJB2aNnQ==",
      "dependencies": {
        "d3-dispatch": "1 - 3",
        "d3-drag": "2 - 3",
        "d3-interpolate": "1 - 3",
        "d3-selection": "3",
        "d3-transition": "3"
      },
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-chord": {
      "version": "3.0.1",
      "resolved": "https://registry.npmjs.org/d3-chord/-/d3-chord-3.0.1.tgz",
      "integrity": "sha512-VE5S6TNa+j8msksl7HwjxMHDM2yNK3XCkusIlpX5kwauBfXuyLAtNg9jCp/iHH61tgI4sb6R/EIMWCqEIdjT/g==",
      "dependencies": {
        "d3-path": "1 - 3"
      },
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-color": {
      "version": "3.1.0",
      "resolved": "https://registry.npmjs.org/d3-color/-/d3-color-3.1.0.tgz",
      "integrity": "sha512-zg/chbXyeBtMQ1LbD/WSoW2DpC3I0mpmPdW+ynRTj/x2DAWYrIY7qeZIHidozwV24m4iavr15lNwIwLxRmOxhA==",
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-contour": {
      "version": "4.0.2",
      "resolved": "https://registry.npmjs.org/d3-contour/-/d3-contour-4.0.2.tgz",
      "integrity": "sha512-4EzFTRIikzs47RGmdxbeUvLWtGedDUNkTcmzoeyg4sP/dvCexO47AaQL7VKy/gul85TOxw+IBgA8US2xwbToNA==",
      "dependencies": {
        "d3-array": "^3.2.0"
      },
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-delaunay": {
      "version": "6.0.4",
      "resolved": "https://registry.npmjs.org/d3-delaunay/-/d3-delaunay-6.0.4.tgz",
      "integrity": "sha512-mdjtIZ1XLAM8bm/hx3WwjfHt6Sggek7qH043O8KEjDXN40xi3vx/6pYSVTwLjEgiXQTbvaouWKynLBiUZ6SK6A==",
      "dependencies": {
        "delaunator": "5"
      },
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-dispatch": {
      "version": "3.0.1",
      "resolved": "https://registry.npmjs.org/d3-dispatch/-/d3-dispatch-3.0.1.tgz",
      "integrity": "sha512-rzUyPU/S7rwUflMyLc1ETDeBj0NRuHKKAcvukozwhshr6g6c5d8zh4c2gQjY2bZ0dXeGLWc1PF174P2tVvKhfg==",
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-drag": {
      "version": "3.0.0",
      "resolved": "https://registry.npmjs.org/d3-drag/-/d3-drag-3.0.0.tgz",
      "integrity": "sha512-pWbUJLdETVA8lQNJecMxoXfH6x+mO2UQo8rSmZ+QqxcbyA3hfeprFgIT//HW2nlHChWeIIMwS2Fq+gEARkhTkg==",
      "dependencies": {
        "d3-dispatch": "1 - 3",
        "d3-selection": "3"
      },
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-dsv": {
      "version": "3.0.1",
      "resolved": "https://registry.npmjs.org/d3-dsv/-/d3-dsv-3.0.1.tgz",
      "integrity": "sha512-UG6OvdI5afDIFP9w4G0mNq50dSOsXHJaRE8arAS5o9ApWnIElp8GZw1Dun8vP8OyHOZ/QJUKUJwxiiCCnUwm+Q==",
      "dependencies": {
        "commander": "7",
        "iconv-lite": "0.6",
        "rw": "1"
      },
      "bin": {
        "csv2json": "bin/dsv2json.js",
        "csv2tsv": "bin/dsv2dsv.js",
        "dsv2dsv": "bin/dsv2dsv.js",
        "dsv2json": "bin/dsv2json.js",
        "json2csv": "bin/json2dsv.js",
        "json2dsv": "bin/json2dsv.js",
        "json2tsv": "bin/json2dsv.js",
        "tsv2csv": "bin/dsv2dsv.js",
        "tsv2json": "bin/dsv2json.js"
      },
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-ease": {
      "version": "3.0.1",
      "resolved": "https://registry.npmjs.org/d3-ease/-/d3-ease-3.0.1.tgz",
      "integrity": "sha512-wR/XK3D3XcLIZwpbvQwQ5fK+8Ykds1ip7A2Txe0yxncXSdq1L9skcG7blcedkOX+ZcgxGAmLX1FrRGbADwzi0w==",
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-fetch": {
      "version": "3.0.1",
      "resolved": "https://registry.npmjs.org/d3-fetch/-/d3-fetch-3.0.1.tgz",
      "integrity": "sha512-kpkQIM20n3oLVBKGg6oHrUchHM3xODkTzjMoj7aWQFq5QEM+R6E4WkzT5+tojDY7yjez8KgCBRoj4aEr99Fdqw==",
      "dependencies": {
        "d3-dsv": "1 - 3"
      },
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-force": {
      "version": "3.0.0",
      "resolved": "https://registry.npmjs.org/d3-force/-/d3-force-3.0.0.tgz",
      "integrity": "sha512-zxV/SsA+U4yte8051P4ECydjD/S+qeYtnaIyAs9tgHCqfguma/aAQDjo85A9Z6EKhBirHRJHXIgJUlffT4wdLg==",
      "dependencies": {
        "d3-dispatch": "1 - 3",
        "d3-quadtree": "1 - 3",
        "d3-timer": "1 - 3"
      },
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-format": {
      "version": "3.1.0",
      "resolved": "https://registry.npmjs.org/d3-format/-/d3-format-3.1.0.tgz",
      "integrity": "sha512-YyUI6AEuY/Wpt8KWLgZHsIU86atmikuoOmCfommt0LYHiQSPjvX2AcFc38PX0CBpr2RCyZhjex+NS/LPOv6YqA==",
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-geo": {
      "version": "3.1.1",
      "resolved": "https://registry.npmjs.org/d3-geo/-/d3-geo-3.1.1.tgz",
      "integrity": "sha512-637ln3gXKXOwhalDzinUgY83KzNWZRKbYubaG+fGVuc/dxO64RRljtCTnf5ecMyE1RIdtqpkVcq0IbtU2S8j2Q==",
      "dependencies": {
        "d3-array": "2.5.0 - 3"
      },
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-hierarchy": {
      "version": "3.1.2",
      "resolved": "https://registry.npmjs.org/d3-hierarchy/-/d3-hierarchy-3.1.2.tgz",
      "integrity": "sha512-FX/9frcub54beBdugHjDCdikxThEqjnR93Qt7PvQTOHxyiNCAlvMrHhclk3cD5VeAaq9fxmfRp+CnWw9rEMBuA==",
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-interpolate": {
      "version": "3.0.1",
      "resolved": "https://registry.npmjs.org/d3-interpolate/-/d3-interpolate-3.0.1.tgz",
      "integrity": "sha512-3bYs1rOD33uo8aqJfKP3JWPAibgw8Zm2+L9vBKEHJ2Rg+viTR7o5Mmv5mZcieN+FRYaAOWX5SJATX6k1PWz72g==",
      "dependencies": {
        "d3-color": "1 - 3"
      },
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-path": {
      "version": "3.1.0",
      "resolved": "https://registry.npmjs.org/d3-path/-/d3-path-3.1.0.tgz",
      "integrity": "sha512-p3KP5HCf/bvjBSSKuXid6Zqijx7wIfNW+J/maPs+iwR35at5JCbLUT0LzF1cnjbCHWhqzQTIN2Jpe8pRebIEFQ==",
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-polygon": {
      "version": "3.0.1",
      "resolved": "https://registry.npmjs.org/d3-polygon/-/d3-polygon-3.0.1.tgz",
      "integrity": "sha512-3vbA7vXYwfe1SYhED++fPUQlWSYTTGmFmQiany/gdbiWgU/iEyQzyymwL9SkJjFFuCS4902BSzewVGsHHmHtXg==",
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-quadtree": {
      "version": "3.0.1",
      "resolved": "https://registry.npmjs.org/d3-quadtree/-/d3-quadtree-3.0.1.tgz",
      "integrity": "sha512-04xDrxQTDTCFwP5H6hRhsRcb9xxv2RzkcsygFzmkSIOJy3PeRJP7sNk3VRIbKXcog561P9oU0/rVH6vDROAgUw==",
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-random": {
      "version": "3.0.1",
      "resolved": "https://registry.npmjs.org/d3-random/-/d3-random-3.0.1.tgz",
      "integrity": "sha512-FXMe9GfxTxqd5D6jFsQ+DJ8BJS4E/fT5mqqdjovykEB2oFbTMDVdg1MGFxfQW+FBOGoB++k8swBrgwSHT1cUXQ==",
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-scale": {
      "version": "4.0.2",
      "resolved": "https://registry.npmjs.org/d3-scale/-/d3-scale-4.0.2.tgz",
      "integrity": "sha512-GZW464g1SH7ag3Y7hXjf8RoUuAFIqklOAq3MRl4OaWabTFJY9PN/E1YklhXLh+OQ3fM9yS2nOkCoS+WLZ6kvxQ==",
      "dependencies": {
        "d3-array": "2.10.0 - 3",
        "d3-format": "1 - 3",
        "d3-interpolate": "1.2.0 - 3",
        "d3-time": "2.1.1 - 3",
        "d3-time-format": "2 - 4"
      },
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-scale-chromatic": {
      "version": "3.1.0",
      "resolved": "https://registry.npmjs.org/d3-scale-chromatic/-/d3-scale-chromatic-3.1.0.tgz",
      "integrity": "sha512-A3s5PWiZ9YCXFye1o246KoscMWqf8BsD9eRiJ3He7C9OBaxKhAd5TFCdEx/7VbKtxxTsu//1mMJFrEt572cEyQ==",
      "dependencies": {
        "d3-color": "1 - 3",
        "d3-interpolate": "1 - 3"
      },
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-selection": {
      "version": "3.0.0",
      "resolved": "https://registry.npmjs.org/d3-selection/-/d3-selection-3.0.0.tgz",
      "integrity": "sha512-fmTRWbNMmsmWq6xJV8D19U/gw/bwrHfNXxrIN+HfZgnzqTHp9jOmKMhsTUjXOJnZOdZY9Q28y4yebKzqDKlxlQ==",
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-shape": {
      "version": "3.2.0",
      "resolved": "https://registry.npmjs.org/d3-shape/-/d3-shape-3.2.0.tgz",
      "integrity": "sha512-SaLBuwGm3MOViRq2ABk3eLoxwZELpH6zhl3FbAoJ7Vm1gofKx6El1Ib5z23NUEhF9AsGl7y+dzLe5Cw2AArGTA==",
      "dependencies": {
        "d3-path": "^3.1.0"
      },
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-time": {
      "version": "3.1.0",
      "resolved": "https://registry.npmjs.org/d3-time/-/d3-time-3.1.0.tgz",
      "integrity": "sha512-VqKjzBLejbSMT4IgbmVgDjpkYrNWUYJnbCGo874u7MMKIWsILRX+OpX/gTk8MqjpT1A/c6HY2dCA77ZN0lkQ2Q==",
      "dependencies": {
        "d3-array": "2 - 3"
      },
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-time-format": {
      "version": "4.1.0",
      "resolved": "https://registry.npmjs.org/d3-time-format/-/d3-time-format-4.1.0.tgz",
      "integrity": "sha512-dJxPBlzC7NugB2PDLwo9Q8JiTR3M3e4/XANkreKSUxF8vvXKqm1Yfq4Q5dl8budlunRVlUUaDUgFt7eA8D6NLg==",
      "dependencies": {
        "d3-time": "1 - 3"
      },
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-timer": {
      "version": "3.0.1",
      "resolved": "https://registry.npmjs.org/d3-timer/-/d3-timer-3.0.1.tgz",
      "integrity": "sha512-ndfJ/JxxMd3nw31uyKoY2naivF+r29V+Lc0svZxe1JvvIRmi8hUsrMvdOwgS1o6uBHmiz91geQ0ylPP0aj1VUA==",
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-transition": {
      "version": "3.0.1",
      "resolved": "https://registry.npmjs.org/d3-transition/-/d3-transition-3.0.1.tgz",
      "integrity": "sha512-ApKvfjsSR6tg06xrL434C0WydLr7JewBB3V+/39RMHsaXTOG0zmt/OAXeng5M5LBm0ojmxJrpomQVZ1aPvBL4w==",
      "dependencies": {
        "d3-color": "1 - 3",
        "d3-dispatch": "1 - 3",
        "d3-ease": "1 - 3",
        "d3-interpolate": "1 - 3",
        "d3-timer": "1 - 3"
      },
      "engines": {
        "node": ">=12"
      },
      "peerDependencies": {
        "d3-selection": "2 - 3"
      }
    },
    "node_modules/d3-zoom": {
      "version": "3.0.0",
      "resolved": "https://registry.npmjs.org/d3-zoom/-/d3-zoom-3.0.0.tgz",
      "integrity": "sha512-b8AmV3kfQaqWAuacbPuNbL6vahnOJflOhexLzMMNLga62+/nh0JzvJ0aO/5a5MVgUFGS7Hu1P9P03o3fJkDCyw==",
      "dependencies": {
        "d3-dispatch": "1 - 3",
        "d3-drag": "2 - 3",
        "d3-interpolate": "1 - 3",
        "d3-selection": "2 - 3",
        "d3-transition": "2 - 3"
      },
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/date-fns": {
      "version": "2.30.0",
      "resolved": "https://registry.npmjs.org/date-fns/-/date-fns-2.30.0.tgz",
      "integrity": "sha512-fnULvOpxnC5/Vg3NCiWelDsLiUc9bRwAPs/+LfTLNvetFCtCTN+yQz15C/fs4AwX1R9K5GLtLfn8QW+dWisaAw==",
      "dev": true,
      "dependencies": {
        "@babel/runtime": "^7.21.0"
      },
      "engines": {
        "node": ">=0.11"
      },
      "funding": {
        "type": "opencollective",
        "url": "https://opencollective.com/date-fns"
      }
    },
    "node_modules/delaunator": {
      "version": "5.0.1",
      "resolved": "https://registry.npmjs.org/delaunator/-/delaunator-5.0.1.tgz",
      "integrity": "sha512-8nvh+XBe96aCESrGOqMp/84b13H9cdKbG5P2ejQCh4d4sK9RL4371qou9drQjMhvnPmhWl5hnmqbEE0fXr9Xnw==",
      "dependencies": {
        "robust-predicates": "^3.0.2"
      }
    },
    "node_modules/delayed-stream": {
      "version": "1.0.0",
      "resolved": "https://registry.npmjs.org/delayed-stream/-/delayed-stream-1.0.0.tgz",
      "integrity": "sha512-ZySD7Nf91aLB0RxL4KGrKHBXl7Eds1DAmEdcoVawXnLD7SDhpNgtuII2aAkg7a7QS41jxPSZ17p4VdGnMHk3MQ==",
      "engines": {
        "node": ">=0.4.0"
      }
    },
    "node_modules/emoji-regex": {
      "version": "8.0.0",
      "resolved": "https://registry.npmjs.org/emoji-regex/-/emoji-regex-8.0.0.tgz",
      "integrity": "sha512-MSjYzcWNOA0ewAHpz0MxpYFvwg6yjy1NG3xteoqz644VCo/RPgnr1/GGt+ic3iJTzQ8Eu3TdM14SawnVUmGE6A==",
      "dev": true
    },
    "node_modules/entities": {
      "version": "4.5.0",
      "resolved": "https://registry.npmjs.org/entities/-/entities-4.5.0.tgz",
      "integrity": "sha512-V0hjH4dGPh9Ao5p0MoRY6BVqtwCjhz6vI5LT8AJ55H+4g9/4vbHx1I54fS0XuclLhDHArPQCiMjDxjaL8fPxhw==",
      "engines": {
        "node": ">=0.12"
      },
      "funding": {
        "url": "https://github.com/fb55/entities?sponsor=1"
      }
    },
    "node_modules/esbuild": {
      "version": "0.18.20",
      "resolved": "https://registry.npmjs.org/esbuild/-/esbuild-0.18.20.tgz",
      "integrity": "sha512-ceqxoedUrcayh7Y7ZX6NdbbDzGROiyVBgC4PriJThBKSVPWnnFHZAkfI1lJT8QFkOwH4qOS2SJkS4wvpGl8BpA==",
      "dev": true,
      "hasInstallScript": true,
      "bin": {
        "esbuild": "bin/esbuild"
      },
      "engines": {
        "node": ">=12"
      },
      "optionalDependencies": {
        "@esbuild/android-arm": "0.18.20",
        "@esbuild/android-arm64": "0.18.20",
        "@esbuild/android-x64": "0.18.20",
        "@esbuild/darwin-arm64": "0.18.20",
        "@esbuild/darwin-x64": "0.18.20",
        "@esbuild/freebsd-arm64": "0.18.20",
        "@esbuild/freebsd-x64": "0.18.20",
        "@esbuild/linux-arm": "0.18.20",
        "@esbuild/linux-arm64": "0.18.20",
        "@esbuild/linux-ia32": "0.18.20",
        "@esbuild/linux-loong64": "0.18.20",
        "@esbuild/linux-mips64el": "0.18.20",
        "@esbuild/linux-ppc64": "0.18.20",
        "@esbuild/linux-riscv64": "0.18.20",
        "@esbuild/linux-s390x": "0.18.20",
        "@esbuild/linux-x64": "0.18.20",
        "@esbuild/netbsd-x64": "0.18.20",
        "@esbuild/openbsd-x64": "0.18.20",
        "@esbuild/sunos-x64": "0.18.20",
        "@esbuild/win32-arm64": "0.18.20",
        "@esbuild/win32-ia32": "0.18.20",
        "@esbuild/win32-x64": "0.18.20"
      }
    },
    "node_modules/escalade": {
      "version": "3.2.0",
      "resolved": "https://registry.npmjs.org/escalade/-/escalade-3.2.0.tgz",
      "integrity": "sha512-WUj2qlxaQtO4g6Pq5c29GTcWGDyd8itL8zTlipgECz3JesAiiOKotd8JU6otB3PACgG6xkJUyVhboMS+bje/jA==",
      "dev": true,
      "engines": {
        "node": ">=6"
      }
    },
    "node_modules/estree-walker": {
      "version": "2.0.2",
      "resolved": "https://registry.npmjs.org/estree-walker/-/estree-walker-2.0.2.tgz",
      "integrity": "sha512-Rfkk/Mp/DL7JVje3u18FxFujQlTNR2q6QfMSMB7AvCBx91NGj/ba3kCfza0f6dVDbw7YlRf/nDrn7pQrCCyQ/w=="
    },
    "node_modules/follow-redirects": {
      "version": "1.15.9",
      "resolved": "https://registry.npmjs.org/follow-redirects/-/follow-redirects-1.15.9.tgz",
      "integrity": "sha512-gew4GsXizNgdoRyqmyfMHyAmXsZDk6mHkSxZFCzW9gwlbtOW44CDtYavM+y+72qD/Vq2l550kMF52DT8fOLJqQ==",
      "funding": [
        {
          "type": "individual",
          "url": "https://github.com/sponsors/RubenVerborgh"
        }
      ],
      "engines": {
        "node": ">=4.0"
      },
      "peerDependenciesMeta": {
        "debug": {
          "optional": true
        }
      }
    },
    "node_modules/form-data": {
      "version": "4.0.1",
      "resolved": "https://registry.npmjs.org/form-data/-/form-data-4.0.1.tgz",
      "integrity": "sha512-tzN8e4TX8+kkxGPK8D5u0FNmjPUjw3lwC9lSLxxoB/+GtsJG91CO8bSWy73APlgAZzZbXEYZJuxjkHH2w+Ezhw==",
      "dependencies": {
        "asynckit": "^0.4.0",
        "combined-stream": "^1.0.8",
        "mime-types": "^2.1.12"
      },
      "engines": {
        "node": ">= 6"
      }
    },
    "node_modules/fsevents": {
      "version": "2.3.3",
      "resolved": "https://registry.npmjs.org/fsevents/-/fsevents-2.3.3.tgz",
      "integrity": "sha512-5xoDfX+fL7faATnagmWPpbFtwh/R77WmMMqqHGS65C3vvB0YHrgF+B1YmZ3441tMj5n63k0212XNoJwzlhffQw==",
      "dev": true,
      "hasInstallScript": true,
      "optional": true,
      "os": [
        "darwin"
      ],
      "engines": {
        "node": "^8.16.0 || ^10.6.0 || >=11.0.0"
      }
    },
    "node_modules/get-caller-file": {
      "version": "2.0.5",
      "resolved": "https://registry.npmjs.org/get-caller-file/-/get-caller-file-2.0.5.tgz",
      "integrity": "sha512-DyFP3BM/3YHTQOCUL/w0OZHR0lpKeGrxotcHWcqNEdnltqFwXVfhEBQ94eIo34AfQpo0rGki4cyIiftY06h2Fg==",
      "dev": true,
      "engines": {
        "node": "6.* || 8.* || >= 10.*"
      }
    },
    "node_modules/has-flag": {
      "version": "4.0.0",
      "resolved": "https://registry.npmjs.org/has-flag/-/has-flag-4.0.0.tgz",
      "integrity": "sha512-EykJT/Q1KjTWctppgIAgfSO0tKVuZUjhgMr17kqTumMl6Afv3EISleU7qZUzoXDFTAHTDC4NOoG/ZxU3EvlMPQ==",
      "dev": true,
      "engines": {
        "node": ">=8"
      }
    },
    "node_modules/iconv-lite": {
      "version": "0.6.3",
      "resolved": "https://registry.npmjs.org/iconv-lite/-/iconv-lite-0.6.3.tgz",
      "integrity": "sha512-4fCk79wshMdzMp2rH06qWrJE4iolqLhCUH+OiuIgU++RB0+94NlDL81atO7GX55uUKueo0txHNtvEyI6D7WdMw==",
      "dependencies": {
        "safer-buffer": ">= 2.1.2 < 3.0.0"
      },
      "engines": {
        "node": ">=0.10.0"
      }
    },
    "node_modules/internmap": {
      "version": "2.0.3",
      "resolved": "https://registry.npmjs.org/internmap/-/internmap-2.0.3.tgz",
      "integrity": "sha512-5Hh7Y1wQbvY5ooGgPbDaL5iYLAPzMTUrjMulskHLH6wnv/A+1q5rgEaiuqEjB+oxGXIVZs1FF+R/KPN3ZSQYYg==",
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/is-fullwidth-code-point": {
      "version": "3.0.0",
      "resolved": "https://registry.npmjs.org/is-fullwidth-code-point/-/is-fullwidth-code-point-3.0.0.tgz",
      "integrity": "sha512-zymm5+u+sCsSWyD9qNaejV3DFvhCKclKdizYaJUuHA83RLjb7nSuGnddCHGv0hk+KY7BMAlsWeK4Ueg6EV6XQg==",
      "dev": true,
      "engines": {
        "node": ">=8"
      }
    },
    "node_modules/lodash": {
      "version": "4.17.21",
      "resolved": "https://registry.npmjs.org/lodash/-/lodash-4.17.21.tgz",
      "integrity": "sha512-v2kDEe57lecTulaDIuNTPy3Ry4gLGJ6Z1O3vE1krgXZNrsQ+LFTGHVxVjcXPs17LhbZVGedAJv8XZ1tvj5FvSg==",
      "dev": true
    },
    "node_modules/magic-string": {
      "version": "0.30.17",
      "resolved": "https://registry.npmjs.org/magic-string/-/magic-string-0.30.17.tgz",
      "integrity": "sha512-sNPKHvyjVf7gyjwS4xGTaW/mCnF8wnjtifKBEhxfZ7E/S8tQ0rssrwGNn6q8JH/ohItJfSQp9mBtQYuTlH5QnA==",
      "dependencies": {
        "@jridgewell/sourcemap-codec": "^1.5.0"
      }
    },
    "node_modules/marked": {
      "version": "5.1.2",
      "resolved": "https://registry.npmjs.org/marked/-/marked-5.1.2.tgz",
      "integrity": "sha512-ahRPGXJpjMjwSOlBoTMZAK7ATXkli5qCPxZ21TG44rx1KEo44bii4ekgTDQPNRQ4Kh7JMb9Ub1PVk1NxRSsorg==",
      "bin": {
        "marked": "bin/marked.js"
      },
      "engines": {
        "node": ">= 16"
      }
    },
    "node_modules/mime-db": {
      "version": "1.52.0",
      "resolved": "https://registry.npmjs.org/mime-db/-/mime-db-1.52.0.tgz",
      "integrity": "sha512-sPU4uV7dYlvtWJxwwxHD0PuihVNiE7TyAbQ5SWxDCB9mUYvOgroQOwYQQOKPJ8CIbE+1ETVlOoK1UC2nU3gYvg==",
      "engines": {
        "node": ">= 0.6"
      }
    },
    "node_modules/mime-types": {
      "version": "2.1.35",
      "resolved": "https://registry.npmjs.org/mime-types/-/mime-types-2.1.35.tgz",
      "integrity": "sha512-ZDY+bPm5zTTF+YpCrAU9nK0UgICYPT0QtT1NZWFv4s++TNkcgVaT0g6+4R2uI4MjQjzysHB1zxuWL50hzaeXiw==",
      "dependencies": {
        "mime-db": "1.52.0"
      },
      "engines": {
        "node": ">= 0.6"
      }
    },
    "node_modules/nanoid": {
      "version": "3.3.8",
      "resolved": "https://registry.npmjs.org/nanoid/-/nanoid-3.3.8.tgz",
      "integrity": "sha512-WNLf5Sd8oZxOm+TzppcYk8gVOgP+l58xNy58D0nbUnOxOWRWvlcCV4kUF7ltmI6PsrLl/BgKEyS4mqsGChFN0w==",
      "funding": [
        {
          "type": "github",
          "url": "https://github.com/sponsors/ai"
        }
      ],
      "bin": {
        "nanoid": "bin/nanoid.cjs"
      },
      "engines": {
        "node": "^10 || ^12 || ^13.7 || ^14 || >=15.0.1"
      }
    },
    "node_modules/picocolors": {
      "version": "1.1.1",
      "resolved": "https://registry.npmjs.org/picocolors/-/picocolors-1.1.1.tgz",
      "integrity": "sha512-xceH2snhtb5M9liqDsmEw56le376mTZkEX/jEb/RxNFyegNul7eNslCXP9FDj/Lcu0X8KEyMceP2ntpaHrDEVA=="
    },
    "node_modules/postcss": {
      "version": "8.5.2",
      "resolved": "https://registry.npmjs.org/postcss/-/postcss-8.5.2.tgz",
      "integrity": "sha512-MjOadfU3Ys9KYoX0AdkBlFEF1Vx37uCCeN4ZHnmwm9FfpbsGWMZeBLMmmpY+6Ocqod7mkdZ0DT31OlbsFrLlkA==",
      "funding": [
        {
          "type": "opencollective",
          "url": "https://opencollective.com/postcss/"
        },
        {
          "type": "tidelift",
          "url": "https://tidelift.com/funding/github/npm/postcss"
        },
        {
          "type": "github",
          "url": "https://github.com/sponsors/ai"
        }
      ],
      "dependencies": {
        "nanoid": "^3.3.8",
        "picocolors": "^1.1.1",
        "source-map-js": "^1.2.1"
      },
      "engines": {
        "node": "^10 || ^12 || >=14"
      }
    },
    "node_modules/proxy-from-env": {
      "version": "1.1.0",
      "resolved": "https://registry.npmjs.org/proxy-from-env/-/proxy-from-env-1.1.0.tgz",
      "integrity": "sha512-D+zkORCbA9f1tdWRK0RaCR3GPv50cMxcrz4X8k5LTSUD1Dkw47mKJEZQNunItRTkWwgtaUSo1RVFRIG9ZXiFYg=="
    },
    "node_modules/regenerator-runtime": {
      "version": "0.14.1",
      "resolved": "https://registry.npmjs.org/regenerator-runtime/-/regenerator-runtime-0.14.1.tgz",
      "integrity": "sha512-dYnhHh0nJoMfnkZs6GmmhFknAGRrLznOu5nc9ML+EJxGvrx6H7teuevqVqCuPcPK//3eDrrjQhehXVx9cnkGdw==",
      "dev": true
    },
    "node_modules/require-directory": {
      "version": "2.1.1",
      "resolved": "https://registry.npmjs.org/require-directory/-/require-directory-2.1.1.tgz",
      "integrity": "sha512-fGxEI7+wsG9xrvdjsrlmL22OMTTiHRwAMroiEeMgq8gzoLC/PQr7RsRDSTLUg/bZAZtF+TVIkHc6/4RIKrui+Q==",
      "dev": true,
      "engines": {
        "node": ">=0.10.0"
      }
    },
    "node_modules/robust-predicates": {
      "version": "3.0.2",
      "resolved": "https://registry.npmjs.org/robust-predicates/-/robust-predicates-3.0.2.tgz",
      "integrity": "sha512-IXgzBWvWQwE6PrDI05OvmXUIruQTcoMDzRsOd5CDvHCVLcLHMTSYvOK5Cm46kWqlV3yAbuSpBZdJ5oP5OUoStg=="
    },
    "node_modules/rollup": {
      "version": "3.29.5",
      "resolved": "https://registry.npmjs.org/rollup/-/rollup-3.29.5.tgz",
      "integrity": "sha512-GVsDdsbJzzy4S/v3dqWPJ7EfvZJfCHiDqe80IyrF59LYuP+e6U1LJoUqeuqRbwAWoMNoXivMNeNAOf5E22VA1w==",
      "dev": true,
      "bin": {
        "rollup": "dist/bin/rollup"
      },
      "engines": {
        "node": ">=14.18.0",
        "npm": ">=8.0.0"
      },
      "optionalDependencies": {
        "fsevents": "~2.3.2"
      }
    },
    "node_modules/rw": {
      "version": "1.3.3",
      "resolved": "https://registry.npmjs.org/rw/-/rw-1.3.3.tgz",
      "integrity": "sha512-PdhdWy89SiZogBLaw42zdeqtRJ//zFd2PgQavcICDUgJT5oW10QCRKbJ6bg4r0/UY2M6BWd5tkxuGFRvCkgfHQ=="
    },
    "node_modules/rxjs": {
      "version": "7.8.1",
      "resolved": "https://registry.npmjs.org/rxjs/-/rxjs-7.8.1.tgz",
      "integrity": "sha512-AA3TVj+0A2iuIoQkWEK/tqFjBq2j+6PO6Y0zJcvzLAFhEFIO3HL0vls9hWLncZbAAbK0mar7oZ4V079I/qPMxg==",
      "dev": true,
      "dependencies": {
        "tslib": "^2.1.0"
      }
    },
    "node_modules/safer-buffer": {
      "version": "2.1.2",
      "resolved": "https://registry.npmjs.org/safer-buffer/-/safer-buffer-2.1.2.tgz",
      "integrity": "sha512-YZo3K82SD7Riyi0E1EQPojLz7kpepnSQI9IyPbHHg1XXXevb5dJI7tpyN2ADxGcQbHG7vcyRHk0cbwqcQriUtg=="
    },
    "node_modules/shell-quote": {
      "version": "1.8.2",
      "resolved": "https://registry.npmjs.org/shell-quote/-/shell-quote-1.8.2.tgz",
      "integrity": "sha512-AzqKpGKjrj7EM6rKVQEPpB288oCfnrEIuyoT9cyF4nmGa7V8Zk6f7RRqYisX8X9m+Q7bd632aZW4ky7EhbQztA==",
      "dev": true,
      "engines": {
        "node": ">= 0.4"
      },
      "funding": {
        "url": "https://github.com/sponsors/ljharb"
      }
    },
    "node_modules/source-map-js": {
      "version": "1.2.1",
      "resolved": "https://registry.npmjs.org/source-map-js/-/source-map-js-1.2.1.tgz",
      "integrity": "sha512-UXWMKhLOwVKb728IUtQPXxfYU+usdybtUrK/8uGE8CQMvrhOpwvzDBwj0QhSL7MQc7vIsISBG8VQ8+IDQxpfQA==",
      "engines": {
        "node": ">=0.10.0"
      }
    },
    "node_modules/spawn-command": {
      "version": "0.0.2",
      "resolved": "https://registry.npmjs.org/spawn-command/-/spawn-command-0.0.2.tgz",
      "integrity": "sha512-zC8zGoGkmc8J9ndvml8Xksr1Amk9qBujgbF0JAIWO7kXr43w0h/0GJNM/Vustixu+YE8N/MTrQ7N31FvHUACxQ==",
      "dev": true
    },
    "node_modules/string-width": {
      "version": "4.2.3",
      "resolved": "https://registry.npmjs.org/string-width/-/string-width-4.2.3.tgz",
      "integrity": "sha512-wKyQRQpjJ0sIp62ErSZdGsjMJWsap5oRNihHhu6G7JVO/9jIB6UyevL+tXuOqrng8j/cxKTWyWUwvSTriiZz/g==",
      "dev": true,
      "dependencies": {
        "emoji-regex": "^8.0.0",
        "is-fullwidth-code-point": "^3.0.0",
        "strip-ansi": "^6.0.1"
      },
      "engines": {
        "node": ">=8"
      }
    },
    "node_modules/strip-ansi": {
      "version": "6.0.1",
      "resolved": "https://registry.npmjs.org/strip-ansi/-/strip-ansi-6.0.1.tgz",
      "integrity": "sha512-Y38VPSHcqkFrCpFnQ9vuSXmquuv5oXOKpGeT6aGrr3o3Gc9AlVa6JBfUSOCnbxGGZF+/0ooI7KrPuUSztUdU5A==",
      "dev": true,
      "dependencies": {
        "ansi-regex": "^5.0.1"
      },
      "engines": {
        "node": ">=8"
      }
    },
    "node_modules/supports-color": {
      "version": "8.1.1",
      "resolved": "https://registry.npmjs.org/supports-color/-/supports-color-8.1.1.tgz",
      "integrity": "sha512-MpUEN2OodtUzxvKQl72cUF7RQ5EiHsGvSsVG0ia9c5RbWGL2CI4C7EpPS8UTBIplnlzZiNuV56w+FuNxy3ty2Q==",
      "dev": true,
      "dependencies": {
        "has-flag": "^4.0.0"
      },
      "engines": {
        "node": ">=10"
      },
      "funding": {
        "url": "https://github.com/chalk/supports-color?sponsor=1"
      }
    },
    "node_modules/tree-kill": {
      "version": "1.2.2",
      "resolved": "https://registry.npmjs.org/tree-kill/-/tree-kill-1.2.2.tgz",
      "integrity": "sha512-L0Orpi8qGpRG//Nd+H90vFB+3iHnue1zSSGmNOOCh1GLJ7rUKVwV2HvijphGQS2UmhUZewS9VgvxYIdgr+fG1A==",
      "dev": true,
      "bin": {
        "tree-kill": "cli.js"
      }
    },
    "node_modules/tslib": {
      "version": "2.8.1",
      "resolved": "https://registry.npmjs.org/tslib/-/tslib-2.8.1.tgz",
      "integrity": "sha512-oJFu94HQb+KVduSUQL7wnpmqnfmLsOA/nAh6b6EH0wCEoK0/mPeXU6c3wKDV83MkOuHPRHtSXKKU99IBazS/2w==",
      "dev": true
    },
    "node_modules/vite": {
      "version": "4.5.9",
      "resolved": "https://registry.npmjs.org/vite/-/vite-4.5.9.tgz",
      "integrity": "sha512-qK9W4xjgD3gXbC0NmdNFFnVFLMWSNiR3swj957yutwzzN16xF/E7nmtAyp1rT9hviDroQANjE4HK3H4WqWdFtw==",
      "dev": true,
      "dependencies": {
        "esbuild": "^0.18.10",
        "postcss": "^8.4.27",
        "rollup": "^3.27.1"
      },
      "bin": {
        "vite": "bin/vite.js"
      },
      "engines": {
        "node": "^14.18.0 || >=16.0.0"
      },
      "funding": {
        "url": "https://github.com/vitejs/vite?sponsor=1"
      },
      "optionalDependencies": {
        "fsevents": "~2.3.2"
      },
      "peerDependencies": {
        "@types/node": ">= 14",
        "less": "*",
        "lightningcss": "^1.21.0",
        "sass": "*",
        "stylus": "*",
        "sugarss": "*",
        "terser": "^5.4.0"
      },
      "peerDependenciesMeta": {
        "@types/node": {
          "optional": true
        },
        "less": {
          "optional": true
        },
        "lightningcss": {
          "optional": true
        },
        "sass": {
          "optional": true
        },
        "stylus": {
          "optional": true
        },
        "sugarss": {
          "optional": true
        },
        "terser": {
          "optional": true
        }
      }
    },
    "node_modules/vue": {
      "version": "3.5.13",
      "resolved": "https://registry.npmjs.org/vue/-/vue-3.5.13.tgz",
      "integrity": "sha512-wmeiSMxkZCSc+PM2w2VRsOYAZC8GdipNFRTsLSfodVqI9mbejKeXEGr8SckuLnrQPGe3oJN5c3K0vpoU9q/wCQ==",
      "dependencies": {
        "@vue/compiler-dom": "3.5.13",
        "@vue/compiler-sfc": "3.5.13",
        "@vue/runtime-dom": "3.5.13",
        "@vue/server-renderer": "3.5.13",
        "@vue/shared": "3.5.13"
      },
      "peerDependencies": {
        "typescript": "*"
      },
      "peerDependenciesMeta": {
        "typescript": {
          "optional": true
        }
      }
    },
    "node_modules/wrap-ansi": {
      "version": "7.0.0",
      "resolved": "https://registry.npmjs.org/wrap-ansi/-/wrap-ansi-7.0.0.tgz",
      "integrity": "sha512-YVGIj2kamLSTxw6NsZjoBxfSwsn0ycdesmc4p+Q21c5zPuZ1pl+NfxVdxPtdHvmNVOQ6XSYG4AUtyt/Fi7D16Q==",
      "dev": true,
      "dependencies": {
        "ansi-styles": "^4.0.0",
        "string-width": "^4.1.0",
        "strip-ansi": "^6.0.0"
      },
      "engines": {
        "node": ">=10"
      },
      "funding": {
        "url": "https://github.com/chalk/wrap-ansi?sponsor=1"
      }
    },
    "node_modules/y18n": {
      "version": "5.0.8",
      "resolved": "https://registry.npmjs.org/y18n/-/y18n-5.0.8.tgz",
      "integrity": "sha512-0pfFzegeDWJHJIAmTLRP2DwHjdF5s7jo9tuztdQxAhINCdvS+3nGINqPd00AphqJR/0LhANUS6/+7SCb98YOfA==",
      "dev": true,
      "engines": {
        "node": ">=10"
      }
    },
    "node_modules/yargs": {
      "version": "17.7.2",
      "resolved": "https://registry.npmjs.org/yargs/-/yargs-17.7.2.tgz",
      "integrity": "sha512-7dSzzRQ++CKnNI/krKnYRV7JKKPUXMEh61soaHKg9mrWEhzFWhFnxPxGl+69cD1Ou63C13NUPCnmIcrvqCuM6w==",
      "dev": true,
      "dependencies": {
        "cliui": "^8.0.1",
        "escalade": "^3.1.1",
        "get-caller-file": "^2.0.5",
        "require-directory": "^2.1.1",
        "string-width": "^4.2.3",
        "y18n": "^5.0.5",
        "yargs-parser": "^21.1.1"
      },
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/yargs-parser": {
      "version": "21.1.1",
      "resolved": "https://registry.npmjs.org/yargs-parser/-/yargs-parser-21.1.1.tgz",
      "integrity": "sha512-tVpsJW7DdjecAiFpbIB1e3qxIQsE6NoPc5/eTdrbbIC4h0LVsWhnoa3g+m2HclBIujHzsxZ4VJVA+GUuc2/LBw==",
      "dev": true,
      "engines": {
        "node": ">=12"
      }
    }
  }
}

</file>

<file path='src/frontend/package.json'>
{
  "name": "local-notes-app",
  "version": "0.1.0",
  "private": true,
  "scripts": {
      "dev": "concurrently \"uvicorn src.backend.main:app --host 127.0.0.1 --port 8000 --reload --app-dir ../..\" \"vite\"",
      "build": "vite build",
      "preview": "vite preview"
  },
  "dependencies": {
      "axios": "^1.3.2",
      "vue": "^3.2.47",
      "marked": "^5.1.0",
      "d3": "^7.8.2"
  },
  "devDependencies": {
      "@vitejs/plugin-vue": "^4.0.0",
      "vite": "^4.0.0",
      "concurrently": "^7.6.0"
  }
}

</file>

<file path='src/frontend/src/App.vue'>
<template>
    <div class="app-container">
        <div class="header-bar">
            <h1>Local Notes App</h1>

            <!-- The view-toggle container still has the same buttons -->
            <div class="view-toggle">
                <button @click="setViewMode('notes')" :class="{ active: viewMode === 'notes' }">
                    Notes View
                </button>
                <button @click="setViewMode('kanban')" :class="{ active: viewMode === 'kanban' }">
                    Kanban Board
                </button>
                <button @click="setViewMode('canvas')" :class="{ active: viewMode === 'canvas' }">
                    Infinite Canvas
                </button>

                <!-- NEW Daily Note button -->
                <button @click="createDailyNote">
                    Daily Note
                </button>
            </div>
        </div>

        <!-- Notes view: File explorer, editor/preview, and task panel -->
        <div class="layout" v-if="viewMode === 'notes'">
            <!-- Left Pane: Note Explorer -->
            <section class="pane side">
                <NoteExplorer 
                    :notes="notesList" 
                    @selectNote="handleNoteSelected"
                    @reloadNotes="fetchNotes"
                />
            </section>

            <!-- Center Pane: Editor + Preview -->
            <section class="pane main">
                <div class="editor-preview-container">
                    <EditorPane
                        v-if="currentNotePath"
                        :currentNoteContent="currentNoteContent"
                        @updateContent="updateNoteContent"
                    />
                    <PreviewPane
                        v-if="currentNoteContent"
                        :markdownText="currentNoteContent"
                    />
                </div>
            </section>

            <!-- Right Pane: Task Panel -->
            <section class="pane side tasks-side">
                <TaskPanel />
            </section>
        </div>

        <!-- Kanban view -->
        <div v-else-if="viewMode === 'kanban'">
            <KanbanBoard />
        </div>

        <!-- Infinite Canvas view -->
        <div v-else-if="viewMode === 'canvas'" class="canvas-view-container">
            <CanvasView />
        </div>
    </div>
</template>

<script>
import axios from 'axios'
import NoteExplorer from './components/NoteExplorer.vue'
import EditorPane from './components/EditorPane.vue'
import PreviewPane from './components/PreviewPane.vue'
import TaskPanel from './components/TaskPanel.vue'
import KanbanBoard from './components/KanbanBoard.vue'
import CanvasView from './components/CanvasView.vue'

/**
 * App.vue
 *
 * The top-level component that manages the main layout.
 * It supports multiple views: Notes view, Kanban board, and Infinite Canvas.
 *
 * NEW: Adds 'createDailyNote()' method to integrate the daily note feature.
 */
export default {
    name: 'App',

    components: {
        NoteExplorer,
        EditorPane,
        PreviewPane,
        TaskPanel,
        KanbanBoard,
        CanvasView
    },

    data() {
        return {
            notesList: [],
            currentNotePath: null,
            currentNoteContent: '',
            viewMode: 'notes'  // 'notes', 'kanban', or 'canvas'
        }
    },

    mounted() {
        this.fetchNotes()
    },

    methods: {
        /**
         * Sets the current view mode ('notes', 'kanban', or 'canvas').
         */
        setViewMode(mode) {
            this.viewMode = mode
        },

        /**
         * Fetches the list of notes from the backend.
         */
        async fetchNotes() {
            try {
                const response = await axios.get('http://localhost:8000/notes')
                this.notesList = response.data.notes || []
            } catch (err) {
                console.error('App.vue: Failed to fetch notes:', err)
            }
        },

        /**
         * Handles the event when a note is selected from the NoteExplorer.
         * @param {String} notePath - The relative path of the selected note.
         */
        handleNoteSelected(notePath) {
            this.currentNotePath = notePath
            this.fetchNoteContent(notePath)
        },

        /**
         * Fetches the content of the selected note from the backend.
         * @param {String} notePath - The relative path of the note.
         */
        async fetchNoteContent(notePath) {
            try {
                const response = await axios.get(`http://localhost:8000/notes/${notePath}`)
                this.currentNoteContent = response.data.content
            } catch (err) {
                console.error('App.vue: Failed to load note content:', err)
            }
        },

        /**
         * Updates the content of the current note by sending a PUT request to the backend.
         * @param {String} newContent - The updated markdown content.
         */
        async updateNoteContent(newContent) {
            if (!this.currentNotePath) {
                return
            }
            try {
                await axios.put(`http://localhost:8000/notes/${this.currentNotePath}`, {
                    content: newContent
                })
                this.currentNoteContent = newContent
            } catch (err) {
                console.error('App.vue: Failed to update note content:', err)
            }
        },

        /**
         * NEW: Creates (or opens) today's daily note by calling the '/notes/daily' endpoint.
         * Upon success, sets the new note path/content and refreshes the notes list.
         */
        async createDailyNote() {
            try {
                // If you want to create a daily note for a custom date, you could do:
                //   const customDateStr = '2025-02-14' // or user input
                //   const response = await axios.post('http://localhost:8000/notes/daily', { date_str: customDateStr })
                // For now, we default to "today" by sending no date_str.
                const response = await axios.post('http://localhost:8000/notes/daily')
                const { note, content } = response.data

                // e.g. note might be "daily/2025-02-14.md"
                this.currentNotePath = note
                this.currentNoteContent = content

                // Reload notes so the new daily note shows up in the explorer.
                this.fetchNotes()

                // Switch to notes view in case the user was on Kanban or Canvas.
                this.viewMode = 'notes'
            } catch (err) {
                console.error('App.vue: Failed to create or open daily note:', err)
            }
        }
    }
}
</script>

<style scoped>
.app-container {
    height: 100vh;
    display: flex;
    flex-direction: column;
    margin: 0;
    font-family: sans-serif;
    box-sizing: border-box;
}

.header-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: #f3f3f3;
    padding: 0.5rem;
    border-bottom: 1px solid #ccc;
}

.view-toggle {
    display: flex;
    gap: 0.5rem;
}

.view-toggle button {
    padding: 0.5rem 1rem;
    cursor: pointer;
}

.view-toggle button.active {
    background-color: #007acc;
    color: #fff;
    border: none;
}

.layout {
    flex: 1;
    display: flex;
    flex-direction: row;
}

.pane {
    border: 1px solid #ccc;
    box-sizing: border-box;
    padding: 0.5rem;
}

.side {
    width: 20%;
    overflow-y: auto;
}

.tasks-side {
    width: 25%;
}

.main {
    flex: 1;
    display: flex;
    flex-direction: column;
}

.editor-preview-container {
    display: flex;
    flex-direction: row;
    height: 100%;
}

.editor-preview-container > * {
    width: 50%;
    padding: 0.5rem;
    box-sizing: border-box;
    border-right: 1px dashed #ccc;
}

.editor-preview-container > *:last-child {
    border-right: none;
}

.canvas-view-container {
    flex: 1;
    padding: 1rem;
}
</style>

</file>

<file path='src/frontend/src/components/CanvasView.vue'>
<!-- src/frontend/src/components/CanvasView.vue -->
<template>
    <div class="canvas-view">
        <h2>Infinite Canvas</h2>
        <!-- Container for D3.js rendered canvas -->
        <div ref="canvasContainer" class="canvas-container"></div>
    </div>
  </template>
  
  <script>
  import * as d3 from 'd3'
  
  /**
   * CanvasView.vue
   *
   * A component that implements an infinite canvas using D3.js.
   * Users can pan and zoom to explore the canvas.
   * Nodes and edges can be added for visual note/task layout.
   */
  export default {
    name: 'CanvasView',
    data() {
        return {
            svg: null,     // D3 selection for the SVG element
            svgGroup: null // D3 group element inside SVG for panning and zooming
        }
    },
    mounted() {
        this.initCanvas()
    },
    methods: {
        /**
         * Initializes the infinite canvas using D3.js.
         * Sets up the SVG element, zoom behavior, and adds sample nodes.
         */
        initCanvas() {
            // Reference to the canvas container DOM element
            const container = this.$refs.canvasContainer
  
            // Create an SVG element that fills the container
            this.svg = d3.select(container)
                .append('svg')
                .attr('width', '100%')
                .attr('height', '100%')
  
            // Append a group element for panning and zooming
            this.svgGroup = this.svg.append('g')
  
            // Define zoom behavior with scale limits
            const zoomBehavior = d3.zoom()
                .scaleExtent([0.5, 5])
                .on('zoom', (event) => {
                    // Apply transformation to the group element
                    this.svgGroup.attr('transform', event.transform)
                })
  
            // Apply the zoom behavior to the SVG element
            this.svg.call(zoomBehavior)
  
            // Add a sample node to demonstrate functionality
            this.addSampleNode(100, 100, 'Sample Node')
        },
  
        /**
         * Adds a sample node to the canvas for demonstration.
         *
         * @param {Number} cx - X-coordinate of the node center.
         * @param {Number} cy - Y-coordinate of the node center.
         * @param {String} label - Label text for the node.
         */
        addSampleNode(cx, cy, label) {
            // Create a group element for the node
            const nodeGroup = this.svgGroup.append('g')
                .attr('class', 'canvas-node')
                .attr('transform', `translate(${cx}, ${cy})`)
  
            // Append a circle to represent the node
            nodeGroup.append('circle')
                .attr('r', 30)
                .attr('fill', 'steelblue')
  
            // Append text to label the node
            nodeGroup.append('text')
                .attr('y', 5)
                .attr('text-anchor', 'middle')
                .attr('fill', '#fff')
                .text(label)
        }
    }
  }
  </script>
  
  <style scoped>
  .canvas-view {
    display: flex;
    flex-direction: column;
    height: 100%;
  }
  
  .canvas-container {
    flex: 1;
    border: 1px solid #ccc;
    overflow: hidden;
    position: relative;
  }
  </style>
  
</file>

<file path='src/frontend/src/components/EditorPane.vue'>
<template>
    <div class="editor-pane">
      <h3>Editor</h3>
      <textarea
        v-model="editorContent"
        class="editor-textarea"
        @input="onContentChange"
      />
    </div>
  </template>
  
  <script>
  export default {
    name: 'EditorPane',
    props: {
      currentNoteContent: {
        type: String,
        default: ''
      }
    },
    data() {
      return {
        editorContent: this.currentNoteContent
      }
    },
    watch: {
      // If the prop changes externally (e.g. when selecting a different note),
      // sync it back to the local data
      currentNoteContent(newVal) {
        this.editorContent = newVal
      }
    },
    methods: {
      onContentChange() {
        // Emit event to update note content in the parent
        this.$emit('updateContent', this.editorContent)
      }
    }
  }
  </script>
  
  <style scoped>
  .editor-pane {
    display: flex;
    flex-direction: column;
    height: 100%;
  }
  
  .editor-textarea {
    flex: 1;
    resize: none;
    width: 100%;
    height: calc(100% - 2rem);
    font-family: monospace;
    font-size: 14px;
    padding: 8px;
    box-sizing: border-box;
  }
  </style>
  
</file>

<file path='src/frontend/src/components/KanbanBoard.vue'>
<template>
    <div class="kanban-container">
        <h2>Kanban Board</h2>
        <p class="kanban-instructions">
            Drag and drop tasks between columns to update their status.
        </p>

        <div class="columns">
            <!-- TODO Column -->
            <div class="column" @drop.prevent="onDrop('TODO')" @dragover.prevent>
                <h3>TODO</h3>
                <div
                    v-for="task in todoTasks"
                    :key="task.id"
                    class="task-card"
                    :draggable="true"
                    @dragstart="onDragStart(task)"
                >
                    <strong>{{ task.title }}</strong>
                    <p v-if="task.description">{{ task.description }}</p>
                    <small v-if="task.due_date">
                        Due: {{ formatDate(task.due_date) }}
                    </small>
                    <small>
                        Priority: {{ formatPriority(task.priority) }}
                    </small>
                    <small v-if="task.recurrence">
                        Recurrence: {{ task.recurrence }}
                    </small>
                    <small>Status: {{ task.status }}</small>
                </div>
            </div>

            <!-- In Progress Column -->
            <div class="column" @drop.prevent="onDrop('IN_PROGRESS')" @dragover.prevent>
                <h3>In Progress</h3>
                <div
                    v-for="task in inProgressTasks"
                    :key="task.id"
                    class="task-card"
                    :draggable="true"
                    @dragstart="onDragStart(task)"
                >
                    <strong>{{ task.title }}</strong>
                    <p v-if="task.description">{{ task.description }}</p>
                    <small v-if="task.due_date">
                        Due: {{ formatDate(task.due_date) }}
                    </small>
                    <small>
                        Priority: {{ formatPriority(task.priority) }}
                    </small>
                    <small v-if="task.recurrence">
                        Recurrence: {{ task.recurrence }}
                    </small>
                    <small>Status: {{ task.status }}</small>
                </div>
            </div>

            <!-- Completed Column -->
            <div class="column" @drop.prevent="onDrop('COMPLETED')" @dragover.prevent>
                <h3>Completed</h3>
                <div
                    v-for="task in completedTasks"
                    :key="task.id"
                    class="task-card"
                    :draggable="true"
                    @dragstart="onDragStart(task)"
                >
                    <strong>{{ task.title }}</strong>
                    <p v-if="task.description">{{ task.description }}</p>
                    <small v-if="task.due_date">
                        Due: {{ formatDate(task.due_date) }}
                    </small>
                    <small>
                        Priority: {{ formatPriority(task.priority) }}
                    </small>
                    <small v-if="task.recurrence">
                        Recurrence: {{ task.recurrence }}
                    </small>
                    <small>Status: {{ task.status }}</small>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import axios from 'axios'

/**
 * KanbanBoard.vue
 *
 * This component implements a Kanban board for task management.
 * Tasks are grouped by their status (TODO, IN_PROGRESS, COMPLETED) and can be
 * dragged between columns to update their status. Additional task metadata
 * (due date, priority, recurrence) is also displayed.
 */
export default {
    name: 'KanbanBoard',
    data() {
        return {
            tasks: [],        // Array to store all tasks from the backend
            draggedTask: null // Currently dragged task object
        }
    },
    computed: {
        /**
         * Returns tasks with status 'TODO'.
         */
        todoTasks() {
            return this.tasks.filter(task => task.status === 'TODO')
        },
        /**
         * Returns tasks with status 'IN_PROGRESS'.
         */
        inProgressTasks() {
            return this.tasks.filter(task => task.status === 'IN_PROGRESS')
        },
        /**
         * Returns tasks with status 'COMPLETED'.
         */
        completedTasks() {
            return this.tasks.filter(task => task.status === 'COMPLETED')
        }
    },
    mounted() {
        // Fetch tasks when component is mounted.
        this.fetchTasks()
    },
    methods: {
        /**
         * Fetch tasks from the backend and update local tasks array.
         */
        async fetchTasks() {
            try {
                const response = await axios.get('http://localhost:8000/tasks')
                this.tasks = response.data
            } catch (error) {
                console.error('KanbanBoard: Failed to fetch tasks:', error)
            }
        },

        /**
         * Handler for dragstart event.
         * Sets the current dragged task.
         *
         * @param {Object} task - The task object that is being dragged.
         */
        onDragStart(task) {
            this.draggedTask = task
        },

        /**
         * Handler for drop event on a column.
         * Updates the dragged task's status based on the column dropped into.
         *
         * @param {String} newStatus - The status representing the target column.
         */
        async onDrop(newStatus) {
            if (!this.draggedTask) {
                return
            }
            if (this.draggedTask.status === newStatus) {
                this.draggedTask = null
                return
            }
            try {
                // For recurring tasks, use the complete endpoint if moving to COMPLETED.
                if (this.draggedTask.recurrence && this.draggedTask.due_date) {
                    if (newStatus === 'COMPLETED') {
                        await axios.post(
                            `http://localhost:8000/tasks/${this.draggedTask.id}/complete`
                        )
                    } else {
                        await axios.put(
                            `http://localhost:8000/tasks/${this.draggedTask.id}`,
                            { status: newStatus }
                        )
                    }
                } else {
                    await axios.put(
                        `http://localhost:8000/tasks/${this.draggedTask.id}`,
                        { status: newStatus }
                    )
                }
                // Refresh tasks after updating.
                this.fetchTasks()
            } catch (error) {
                console.error('KanbanBoard: Error updating task status:', error)
            }
            this.draggedTask = null
        },

        /**
         * Formats a date string into a locale-specific date.
         *
         * @param {String} dateStr - The date string.
         * @returns {String} Formatted date.
         */
        formatDate(dateStr) {
            const date = new Date(dateStr)
            return date.toLocaleDateString()
        },

        /**
         * Converts numeric priority to a human-readable string.
         *
         * @param {Number} priority - The task priority.
         * @returns {String} The formatted priority string.
         */
        formatPriority(priority) {
            switch (priority) {
                case 1:
                    return 'High'
                case 2:
                    return 'Medium'
                case 3:
                    return 'Low'
                default:
                    return priority
            }
        }
    }
}
</script>

<style scoped>
.kanban-container {
    display: flex;
    flex-direction: column;
    padding: 1rem;
    height: 100%;
    box-sizing: border-box;
    font-family: sans-serif;
}

.kanban-instructions {
    font-size: 0.9rem;
    color: #666;
    margin-bottom: 1rem;
}

.columns {
    display: flex;
    gap: 1rem;
    flex: 1;
}

.column {
    flex: 1;
    border: 1px solid #ccc;
    min-height: 300px;
    padding: 0.5rem;
    box-sizing: border-box;
    background-color: #fafafa;
}

.task-card {
    background: #fff;
    margin-bottom: 0.5rem;
    padding: 0.5rem;
    border: 1px solid #ddd;
    cursor: grab;
}

.task-card:active {
    cursor: grabbing;
}
</style>

</file>

<file path='src/frontend/src/components/NoteExplorer.vue'>
<template>
  <div class="note-explorer">
    <h2>Notes</h2>

    <div class="notes-list">
      <ul>
        <li
          v-for="(note, idx) in notes"
          :key="idx"
          @click="select(note)"
          class="note-item"
        >
          {{ note }}
        </li>
      </ul>
    </div>
    <div class="actions">
      <input
        v-model="newNoteName"
        placeholder="New note name..."
        @keydown.enter="createNote"
      />
      <button @click="createNote">Create Note</button>
      <button @click="reloadNotes">Reload</button>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'NoteExplorer',
  props: {
    notes: {
      type: Array,
      required: true
    }
  },
  data() {
    return {
      newNoteName: ''
    }
  },
  methods: {
    select(notePath) {
      // Notify parent that a note was selected
      this.$emit('selectNote', notePath)
    },
    createNote() {
      if (!this.newNoteName) return
      axios.post('http://localhost:8000/notes', {
        note_name: this.newNoteName
      })
      .then(() => {
        this.newNoteName = ''
        // Refresh the parent’s note list
        this.$emit('reloadNotes')
      })
      .catch(err => {
        console.error('Failed to create note:', err)
      })
    },
    reloadNotes() {
      this.$emit('reloadNotes')
    }
  }
}
</script>

<style scoped>
.note-explorer {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.notes-list {
  flex: 1;
  overflow-y: auto;
}

.note-item {
  cursor: pointer;
  padding: 4px;
  border-bottom: 1px solid #eee;
}

.note-item:hover {
  background: #fafafa;
}

.actions {
  margin-top: 0.5rem;
}

.actions input {
  width: 60%;
  padding: 4px;
  margin-right: 0.5rem;
}
</style>

</file>

<file path='src/frontend/src/components/PreviewPane.vue'>
<template>
    <div class="preview-pane">
      <h3>Preview</h3>
      <div
        class="preview-content"
        v-html="renderedMarkdown"
      />
    </div>
  </template>
  
  <script>
  import { marked } from 'marked'
  
  export default {
    name: 'PreviewPane',
    props: {
      markdownText: {
        type: String,
        default: ''
      }
    },
    computed: {
      renderedMarkdown() {
        // Use 'marked' to convert the raw markdown text into HTML
        return marked(this.markdownText || '')
      }
    }
  }
  </script>
  
  <style scoped>
  .preview-pane {
    display: flex;
    flex-direction: column;
    height: 100%;
  }
  
  .preview-content {
    flex: 1;
    overflow-y: auto;
    padding: 0.5rem;
    background: #f9f9f9;
    border: 1px solid #ddd;
  }
  </style>
  
</file>

<file path='src/frontend/src/components/TaskPanel.vue'>
<template>
  <div class="task-panel">
      <h2>Tasks</h2>
      <!-- Task creation form with extended fields -->
      <div class="task-form">
          <input
              v-model="newTaskTitle"
              placeholder="New task title..."
          />
          <input
              v-model="newTaskDescription"
              placeholder="Description"
          />
          <input
              type="date"
              v-model="newTaskDueDate"
              placeholder="Due Date"
          />
          <select v-model="newTaskPriority">
              <option value="1">High</option>
              <option value="2">Medium</option>
              <option value="3">Low</option>
          </select>
          <input
              v-model="newTaskRecurrence"
              placeholder="Recurrence (daily, weekly, monthly)"
          />
          <button @click="createTask">Add Task</button>
          <button @click="fetchTasks">Reload</button>
      </div>

      <!-- Task list display -->
      <div class="task-list">
          <div
              v-for="task in tasks"
              :key="task.id"
              class="task-item"
          >
              <label>
                  <input
                      type="checkbox"
                      :checked="task.status === 'COMPLETED'"
                      @change="handleComplete(task)"
                  />
                  <strong>{{ task.title }}</strong>
              </label>
              <p v-if="task.description">{{ task.description }}</p>
              <small v-if="task.due_date">
                  Due: {{ formatDate(task.due_date) }}
              </small>
              <small>
                  Priority: {{ formatPriority(task.priority) }}
              </small>
              <small v-if="task.recurrence">
                  Recurrence: {{ task.recurrence }}
              </small>
              <small>Status: {{ task.status }}</small>
          </div>
      </div>
  </div>
</template>

<script>
import axios from 'axios'

/**
* TaskPanel.vue
*
* This component displays a panel for managing tasks.
* It allows users to create new tasks with extended fields (description,
* due date, priority, recurrence) and displays the list of tasks.
* It also handles marking tasks complete using the appropriate backend endpoint.
*/
export default {
  name: 'TaskPanel',
  data() {
      return {
          tasks: [],                // Array holding all tasks from the backend
          newTaskTitle: '',         // Title for new task
          newTaskDescription: '',   // Description for new task
          newTaskDueDate: '',       // Due date (as a string) for new task
          newTaskPriority: '2',     // Default priority (2 = Medium)
          newTaskRecurrence: ''     // Recurrence rule (if any)
      }
  },
  mounted() {
      // Fetch tasks once the component is mounted
      this.fetchTasks()
  },
  methods: {
      /**
       * Fetch all tasks from the backend.
       */
      async fetchTasks() {
          try {
              const response = await axios.get('http://localhost:8000/tasks')
              this.tasks = response.data
          } catch (error) {
              console.error('TaskPanel: Failed to fetch tasks:', error)
          }
      },

      /**
       * Create a new task with the given details.
       * Converts the due date to a Date object if provided.
       */
      async createTask() {
          if (!this.newTaskTitle) {
              return
          }
          try {
              const payload = {
                  title: this.newTaskTitle,
                  description: this.newTaskDescription,
                  due_date: this.newTaskDueDate
                      ? new Date(this.newTaskDueDate)
                      : null,
                  priority: parseInt(this.newTaskPriority),
                  recurrence: this.newTaskRecurrence || null
              }
              await axios.post('http://localhost:8000/tasks', payload)
              // Reset form fields
              this.newTaskTitle = ''
              this.newTaskDescription = ''
              this.newTaskDueDate = ''
              this.newTaskPriority = '2'
              this.newTaskRecurrence = ''
              // Refresh the task list
              this.fetchTasks()
          } catch (error) {
              console.error('TaskPanel: Failed to create task:', error)
          }
      },

      /**
       * Handle the task completion toggle.
       * If the task has a recurrence rule and a due date, call the complete endpoint.
       * Otherwise, simply update the status.
       *
       * @param {Object} task - The task object to update.
       */
      async handleComplete(task) {
          try {
              if (task.recurrence && task.due_date) {
                  // For recurring tasks, use the dedicated complete endpoint.
                  await axios.post(`http://localhost:8000/tasks/${task.id}/complete`)
              } else {
                  // Toggle the status between TODO and COMPLETED.
                  if (task.status !== 'COMPLETED') {
                      await axios.put(`http://localhost:8000/tasks/${task.id}`, {
                          status: 'COMPLETED'
                      })
                  } else {
                      await axios.put(`http://localhost:8000/tasks/${task.id}`, {
                          status: 'TODO'
                      })
                  }
              }
              // Refresh tasks after update.
              this.fetchTasks()
          } catch (error) {
              console.error('TaskPanel: Failed to update task status:', error)
          }
      },

      /**
       * Format a date string into a locale-specific date.
       *
       * @param {String} dateStr - The date string.
       * @returns {String} Formatted date.
       */
      formatDate(dateStr) {
          const date = new Date(dateStr)
          return date.toLocaleDateString()
      },

      /**
       * Format the numeric priority into a human-readable string.
       *
       * @param {Number} priority - The priority value.
       * @returns {String} Formatted priority.
       */
      formatPriority(priority) {
          switch (priority) {
              case 1:
                  return 'High'
              case 2:
                  return 'Medium'
              case 3:
                  return 'Low'
              default:
                  return priority
          }
      }
  }
}
</script>

<style scoped>
.task-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  font-family: sans-serif;
  padding: 0.5rem;
  box-sizing: border-box;
}

.task-form {
  margin-bottom: 1rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.task-form input,
.task-form select {
  padding: 4px;
  font-size: 0.9rem;
}

.task-form button {
  padding: 4px 8px;
  cursor: pointer;
}

.task-list {
  flex: 1;
  overflow-y: auto;
}

.task-item {
  border-bottom: 1px solid #eee;
  padding: 0.5rem 0;
}
</style>

</file>

<file path='src/frontend/src/main.js'>
/**
 * main.js
 *
 * The main entry point for the Vue app. Creates the Vue application,
 * mounts it to #app in index.html, and configures global dependencies.
 */

import { createApp } from 'vue'
import App from './App.vue'

// Create the app instance
const app = createApp(App)

// Mount it to <div id="app"> in index.html
app.mount('#app')
</file>

<file path='src/frontend/storage/vault/2.md'>
# hello


</file>

<file path='src/frontend/storage/vault/test note 1.md'>
# bye
## 2

</file>

<file path='src/frontend/vite.config.js'>
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    // Optional: The proxy ensures requests to "/notes", "/tasks", etc. go to http://127.0.0.1:8000
    proxy: {
      '/notes': 'http://127.0.0.1:8000',
      '/tasks': 'http://127.0.0.1:8000',
      '/backup': 'http://127.0.0.1:8000',
      '/search': 'http://127.0.0.1:8000'
    }
  }
})
</file>

<file path='storage/vault/Test note 1.md'>

# Tile
## Sub-title
Here I am testing this app I built!
</file>

"""
<goal>


</goal>


<output instruction>
1) Explain 
2) Give me the COMPLETE UPDATED VERSION of each script that needs to be updated
</output instruction>
"""

</file>

<file path='package-lock.json'>
{
  "name": "local_notes",
  "lockfileVersion": 3,
  "requires": true,
  "packages": {}
}

</file>

<file path='requirements.txt'>
# requirements.txt
SQLAlchemy
fastapi
pydantic
uvicorn
whoosh

</file>

<file path='run_all.sh'>
#!/usr/bin/env bash
set -e

#
# 1) Install Python dependencies
#
#echo "Installing Python dependencies..."
#pip install -r requirements.txt

#
# 2) Install Node dependencies in src/frontend
#
echo "Installing Node dependencies..."
cd src/frontend
npm install

#
# 3) Launch both FastAPI & Vite via 'npm run dev'
#
echo "Launching backend & frontend concurrently..."
npm run dev
</file>

<file path='src/backend/__init__.py'>

</file>

<file path='src/backend/backup/__init__.py'>

</file>

<file path='src/backend/backup/routes.py'>
# src/backend/backup/routes.py
"""
routes.py

Defines FastAPI endpoints for backup and versioning operations.
Provides endpoints to list backup versions and restore a note to a previous version.
"""

from fastapi import APIRouter, HTTPException, Path, Body
from fastapi.responses import JSONResponse
from typing import List

from .versioning import list_versions, create_version, restore_version

router = APIRouter(
    prefix="/backup",
    tags=["backup"],
    responses={404: {"description": "Not found"}}
)


@router.get("/versions/{note_path:path}", summary="List backup versions")
async def get_versions(note_path: str) -> JSONResponse:
    """
    List all backup versions for a given note.

    Args:
        note_path (str): Relative path to the note.

    Returns:
        JSONResponse: A JSON response containing a list of backup version filenames.
    """
    try:
        versions = list_versions(note_path)
        return JSONResponse(content={"versions": versions})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/versions/{note_path:path}", summary="Create a backup version")
async def backup_note(note_path: str) -> JSONResponse:
    """
    Create a backup version of a note.

    Args:
        note_path (str): Relative path to the note.

    Returns:
        JSONResponse: A confirmation message.
    """
    try:
        create_version(note_path)
        return JSONResponse(content={"message": "Backup created successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restore/{note_path:path}", summary="Restore a note version")
async def restore_note(
    note_path: str,
    version: str = Body(..., embed=True, description="Version filename to restore")
) -> JSONResponse:
    """
    Restore a note to a previous version.

    Args:
        note_path (str): Relative path to the note.
        version (str): The backup version filename to restore.

    Returns:
        JSONResponse: A confirmation message.
    """
    try:
        restore_version(note_path, version)
        return JSONResponse(content={"message": "Note restored successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

</file>

<file path='src/backend/backup/snapshotter.py'>
#!/usr/bin/env python3
# snapshotter.py
"""
snapshotter.py

Implements a simple snapshot mechanism for creating periodic backups of the vault.
This module can be integrated with a scheduler (or background thread) to run every
N minutes, as configured in config.py.

Example usage from another module:
    from src.backend.backup.snapshotter import create_snapshot
    create_snapshot()
"""

import shutil
from pathlib import Path
from datetime import datetime

from src.backend.config import Config

# Use the backup directory defined in the configuration and create a "snapshots" subfolder.
SNAPSHOT_DIR = Config.BACKUP_DIR / "snapshots"
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

def create_snapshot() -> None:
    """
    Create a snapshot backup of the entire vault.
    
    The snapshot is a copy of the vault directory stored with a timestamp.
    """
    vault_path = Path(Config.VAULT_DIR)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot_path = SNAPSHOT_DIR / f"vault_snapshot_{timestamp}"
    shutil.copytree(vault_path, snapshot_path)

</file>

<file path='src/backend/backup/versioning.py'>
# src/backend/backup/versioning.py
"""
versioning.py

Provides functionality for managing version history of Markdown notes.
It allows listing available versions and restoring a note to a previous version.
"""

import shutil
from pathlib import Path
from datetime import datetime
from typing import List
import os

# Import NoteManager to handle note file operations.
from src.backend.file_handler import NoteManager
# Import Config for centralized configuration values.
from src.backend.config import Config

# Use the backup directory from Config.
BACKUP_DIR = Config.BACKUP_DIR
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

def list_versions(note_path: str) -> List[str]:
    """
    List all backup versions for a given note.
    
    Args:
        note_path (str): Relative path to the note within the vault.
        
    Returns:
        List[str]: A sorted list of backup file names.
    """
    # Replace OS-specific path separators with underscores to form the backup folder name.
    note_backup_dir = BACKUP_DIR / note_path.replace(os.sep, "_")
    if not note_backup_dir.exists():
        return []
    return sorted([f.name for f in note_backup_dir.iterdir() if f.is_file()])

def create_version(note_path: str) -> None:
    """
    Create a backup version of a note by copying the current file to a backup directory.
    
    Args:
        note_path (str): Relative path to the note within the vault.
    
    Raises:
        FileNotFoundError: If the note does not exist.
    """
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
        
    Raises:
        FileNotFoundError: If the backup version is not found.
    """
    note_manager = NoteManager()
    note_backup_dir = BACKUP_DIR / note_path.replace(os.sep, "_")
    backup_file = note_backup_dir / version_file
    if not backup_file.exists():
        raise FileNotFoundError(f"Backup version not found: {version_file}")

    # Overwrite the current note with the backup version.
    full_note_path = note_manager.vault_dir / note_path
    shutil.copy(backup_file, full_note_path)

</file>

<file path='src/backend/canvas/__init__.py'>

</file>

<file path='src/backend/canvas/canvas_store.py'>
# src/backend/canvas/canvas_store.py
"""
canvas_store.py

This module defines the CanvasStore class which handles the persistence
of the canvas layout data in a JSON file. The canvas layout includes nodes
and edges representing the infinite canvas workspace.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict

# Constant for the canvas storage file
CANVAS_FILE = Path(os.getcwd(), "storage", "canvas", "canvas_layout.json")


class CanvasStore:
    """
    Manages storage and retrieval of canvas layout data.
    """

    def __init__(self) -> None:
        """
        Initialize the CanvasStore and ensure the storage directory exists.
        """
        canvas_dir = CANVAS_FILE.parent
        canvas_dir.mkdir(parents=True, exist_ok=True)

    def save_canvas(self, layout: Dict[str, Any]) -> None:
        """
        Save the canvas layout data to a JSON file.

        Args:
            layout (Dict[str, Any]): The canvas layout data including nodes and edges.
        """
        with open(CANVAS_FILE, "w", encoding="utf-8") as f:
            json.dump(layout, f, indent=4)

    def load_canvas(self) -> Dict[str, Any]:
        """
        Load the canvas layout data from the JSON file.

        Returns:
            Dict[str, Any]: The canvas layout data. Returns an empty layout if file does not exist.
        """
        if not CANVAS_FILE.exists():
            return {"nodes": [], "edges": []}
        with open(CANVAS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

</file>

<file path='src/backend/canvas/node_processor.py'>
# src/backend/canvas/node_processor.py
"""
node_processor.py

This module provides functionality to process nodes and their relationships
within the canvas. It supports operations such as grouping nodes and validating
connections between nodes.
"""

from typing import List, Dict, Any


class NodeProcessor:
    """
    Processes nodes and connections in the canvas layout.
    """

    def group_nodes(self, nodes: List[Dict[str, Any]], group_key: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group nodes based on a specific key.

        Args:
            nodes (List[Dict[str, Any]]): List of node dictionaries.
            group_key (str): The key to group nodes by.

        Returns:
            Dict[str, List[Dict[str, Any]]]: A dictionary with group_key values as keys and lists of nodes as values.
        """
        grouped = {}
        for node in nodes:
            key = node.get(group_key, "ungrouped")
            grouped.setdefault(key, []).append(node)
        return grouped

    def validate_connection(self, source_node: Dict[str, Any], target_node: Dict[str, Any], connection_type: str) -> bool:
        """
        Validate a connection between two nodes based on connection type.

        Args:
            source_node (Dict[str, Any]): The source node data.
            target_node (Dict[str, Any]): The target node data.
            connection_type (str): Type of connection (e.g., "arrow", "line").

        Returns:
            bool: True if the connection is valid, False otherwise.
        """
        # Example validation: ensure nodes are not the same and connection type is supported
        if source_node.get("id") == target_node.get("id"):
            return False
        if connection_type not in ["arrow", "line"]:
            return False
        return True

</file>

<file path='src/backend/canvas/routes.py'>
# src/backend/canvas/routes.py
"""
routes.py

Defines FastAPI endpoints for canvas operations.
Provides endpoints to retrieve and update the infinite canvas layout.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Any, Dict

from .canvas_store import CanvasStore

router = APIRouter(
    prefix="/canvas",
    tags=["canvas"],
    responses={404: {"description": "Not found"}}
)

canvas_store = CanvasStore()


@router.get("/", summary="Retrieve canvas layout")
async def get_canvas() -> JSONResponse:
    """
    Retrieve the current canvas layout.

    Returns:
        JSONResponse: A JSON response containing the canvas layout.
    """
    try:
        layout = canvas_store.load_canvas()
        return JSONResponse(content=layout)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", summary="Update canvas layout")
async def update_canvas(layout: Dict[str, Any]) -> JSONResponse:
    """
    Update the canvas layout with new data.

    Args:
        layout (Dict[str, Any]): The new canvas layout data.

    Returns:
        JSONResponse: A JSON response confirming the update.
    """
    try:
        canvas_store.save_canvas(layout)
        return JSONResponse(content={"message": "Canvas updated successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

</file>

<file path='src/backend/config.py'>
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


</file>

<file path='src/backend/database/__init__.py'>

</file>

<file path='src/backend/database/base.py'>
# src/backend/database/base.py
"""
base.py

Defines the declarative base for all SQLAlchemy models.
This base is used for all model definitions to ensure a consistent ORM layer.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

</file>

<file path='src/backend/database/init_db.py'>
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

</file>

<file path='src/backend/database/sessions.py'>
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

</file>

<file path='src/backend/file_handler.py'>
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

</file>

<file path='src/backend/main.py'>
#!/usr/bin/env python3
# main.py
"""
main.py

The entry point for the local note-taking and task management application backend.
This module sets up the FastAPI application, integrates:
 - Notes endpoints (CRUD + daily notes)
 - Task endpoints (CRUD + recurrence)
 - Canvas endpoints
 - Search functionality
 - Backup/versioning endpoints
 - Periodic snapshots (NEW)

It starts the local development server with uvicorn.

Usage:
    python main.py
or:
    uvicorn main:app --host 127.0.0.1 --port 8000 --reload
"""

import threading
import time
import datetime

from fastapi import FastAPI, HTTPException, Path, Body
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from src.backend.config import Config
from src.backend.file_handler import NoteManager
from src.backend.tasks.routes import router as tasks_router
from src.backend.canvas.routes import router as canvas_router
from src.backend.search.routes import router as search_router
from src.backend.backup.routes import router as backup_router
from src.backend.database.init_db import init_db
from src.backend.backup.snapshotter import create_snapshot


app = FastAPI(
    title="Local Note-Taking & Task Management App",
    version="0.3.0",
    description="A local, file-based note-taking and task management application inspired by Obsidian."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

note_manager = NoteManager()


# -----------------------------
#  BACKGROUND SNAPSHOT THREAD
# -----------------------------
def run_snapshots_in_background() -> None:
    """
    Runs periodic snapshots of the vault in a background thread,
    using the interval specified in Config.
    """
    while True:
        time.sleep(Config.SNAPSHOT_INTERVAL_MINUTES * 60)
        try:
            create_snapshot()
            print(f"[{datetime.datetime.now()}] Snapshot created.")
        except Exception as ex:
            print(f"Error creating snapshot: {ex}")


@app.on_event("startup")
def on_startup() -> None:
    """
    Automatically create database tables if they do not exist,
    and optionally start a background thread for periodic snapshots.
    """
    init_db()

    # Start the periodic snapshot thread if enabled
    if Config.ENABLE_PERIODIC_SNAPSHOTS:
        thread = threading.Thread(target=run_snapshots_in_background, daemon=True)
        thread.start()
        print(f"Periodic snapshots enabled (every {Config.SNAPSHOT_INTERVAL_MINUTES} min).")


# -----------------------------
# NOTE ENDPOINTS
# -----------------------------

@app.get("/notes", summary="List all notes")
async def list_notes() -> JSONResponse:
    """
    Retrieve a list of all Markdown notes in the vault.
    """
    try:
        notes = note_manager.list_notes()
        return JSONResponse(content={"notes": notes})
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@app.get("/notes/{note_path:path}", summary="Retrieve a note")
async def get_note(
    note_path: str = Path(..., description="Relative path to the note file")
) -> JSONResponse:
    """
    Retrieve the content of a specific Markdown note.
    """
    try:
        content = note_manager.read_note(note_path)
        return JSONResponse(content={"note": note_path, "content": content})
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Note not found")
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@app.post("/notes", summary="Create a new note")
async def create_note(
    note_name: str = Body(..., embed=True, description="Name of the new note"),
    content: str = Body("", embed=True, description="Initial content for the note")
) -> JSONResponse:
    """
    Create a new Markdown note with the specified name and optional content.
    """
    try:
        note_path = note_manager.create_note(note_name, content)
        return JSONResponse(content={"message": "Note created", "note": note_path})
    except FileExistsError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@app.put("/notes/{note_path:path}", summary="Update an existing note")
async def update_note(
    note_path: str = Path(..., description="Relative path to the note file"),
    content: str = Body(..., embed=True, description="New content for the note")
) -> JSONResponse:
    """
    Update an existing Markdown note.
    """
    try:
        _ = note_manager.read_note(note_path)  # Ensure it exists
        note_manager.write_note(note_path, content)
        return JSONResponse(content={"message": "Note updated", "note": note_path})
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Note not found")
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


# -------------------------------------------------------------------------
#       DAILY NOTE ENDPOINT
# -------------------------------------------------------------------------
@app.post("/notes/daily", summary="Create or open a daily note")
async def create_daily_note(
    date_str: str = Body(None, embed=True, description="YYYY-MM-DD format; defaults to today")
) -> JSONResponse:
    """
    Create (if missing) and return a daily note, stored in the 'daily' subfolder.
    If date_str is not provided, today's date is used.
    If a daily template is configured, it will be used when creating a new note.
    """
    try:
        if date_str is None:
            date_str = datetime.date.today().strftime(Config.DAILY_NOTES_DATE_FORMAT)

        daily_filename = date_str + Config.NOTE_EXTENSION

        # We create a dedicated NoteManager pointing to daily subfolder:
        daily_manager = NoteManager(str(Config.DAILY_NOTES_DIR))

        # Check if note already exists
        existing_notes = daily_manager.list_notes()
        if daily_filename in existing_notes:
            # If it exists, just read and return
            content = daily_manager.read_note(daily_filename)
            return JSONResponse(content={
                "message": f"Daily note for {date_str} already exists.",
                "note": f"daily/{daily_filename}",
                "content": content
            })

        # If it doesn't exist, try to load template
        template_content = ""
        if Config.DAILY_NOTES_TEMPLATE.exists():
            try:
                template_content = Config.DAILY_NOTES_TEMPLATE.read_text(encoding="utf-8")
            except Exception:
                template_content = ""
        else:
            # Fallback to minimal
            template_content = f"# {date_str} Daily Note\n\n"

        # Create the note with the template
        note_path = daily_manager.create_note(daily_filename, template_content)
        return JSONResponse(content={
            "message": f"Daily note created for {date_str}.",
            "note": f"daily/{daily_filename}",
            "content": template_content
        })
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


if __name__ == "__main__":
    uvicorn.run("main:app", host=Config.HOST, port=Config.PORT, reload=True)

</file>

<file path='src/backend/search/__init__.py'>

</file>

<file path='src/backend/search/indexer.py'>
# src/backend/search/indexer.py
"""
indexer.py

Provides full-text indexing functionality for Markdown notes using Whoosh.
Builds and maintains a search index for fast querying of note content.
"""

from whoosh import index
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import QueryParser
from pathlib import Path

# Import Config for centralized configuration values.
from src.backend.config import Config
from src.backend.file_handler import NoteManager

# Use the search index directory from configuration.
INDEX_DIR = Config.SEARCH_INDEX_DIR
INDEX_DIR.mkdir(parents=True, exist_ok=True)

def get_schema():
    """
    Define and return the Whoosh schema for indexing notes.
    
    Returns:
        Schema: A Whoosh Schema object defining the fields for indexing.
    """
    return Schema(
        path=ID(stored=True, unique=True),
        content=TEXT(stored=True)
    )

def create_index() -> index.Index:
    """
    Create a new index if one doesn't exist, or open the existing index.
    
    Returns:
        index.Index: The Whoosh index object.
    """
    if not index.exists_in(INDEX_DIR):
        schema = get_schema()
        idx = index.create_in(INDEX_DIR, schema)
    else:
        idx = index.open_dir(INDEX_DIR)
    return idx

def build_index() -> None:
    """
    Build or rebuild the search index by indexing all Markdown notes.
    """
    idx = create_index()
    writer = idx.writer()
    note_manager = NoteManager()
    # Iterate through all notes and add or update them in the index.
    for note_path in note_manager.list_notes():
        try:
            content = note_manager.read_note(note_path)
            writer.update_document(path=note_path, content=content)
        except Exception as e:
            # Log the error for debugging purposes.
            print(f"Error indexing {note_path}: {e}")
    writer.commit()

def search_notes(query_str: str) -> list:
    """
    Search the index for notes matching the query string.
    
    Args:
        query_str (str): The search query.
    
    Returns:
        list: A list of note paths that match the search query.
    """
    idx = create_index()
    qp = QueryParser("content", schema=idx.schema)
    query = qp.parse(query_str)
    results = []
    with idx.searcher() as searcher:
        hits = searcher.search(query, limit=10)
        for hit in hits:
            results.append(hit["path"])
    return results

</file>

<file path='src/backend/search/query_parser.py'>
# src/backend/search/query_parser.py
"""
query_parser.py

Provides advanced query parsing for search functionality.
This module can be extended to support parsing of tags, dates, and other metadata.
"""

def parse_query(query_str: str) -> dict:
    """
    Parse the search query string and extract components such as text, tags, and dates.

    Args:
        query_str (str): The raw search query string.

    Returns:
        dict: A dictionary with parsed query components.
    """
    # For simplicity, this implementation splits the query into words.
    # Future enhancements can include regex-based extraction of tags or dates.
    components = query_str.split()
    return {"text": " ".join(components), "raw": query_str}

</file>

<file path='src/backend/search/routes.py'>
# src/backend/search/routes.py
"""
routes.py

Defines FastAPI endpoints for search functionality.
Provides an endpoint to search through Markdown notes.
This updated version integrates advanced query parsing using query_parser.
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List

from .indexer import search_notes, build_index
from .query_parser import parse_query  # Import advanced query parser

router = APIRouter(
    prefix="/search",
    tags=["search"],
    responses={404: {"description": "Not found"}}
)

@router.post("/reindex", summary="Rebuild search index")
async def reindex() -> JSONResponse:
    """
    Rebuild the full-text search index for Markdown notes.

    Returns:
        JSONResponse: A confirmation message.
    """
    try:
        build_index()
        return JSONResponse(content={"message": "Search index rebuilt successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", summary="Search notes", response_model=List[str])
async def search(query: str = Query(..., description="Search query string")) -> JSONResponse:
    """
    Search for notes matching the provided query string.
    The query is parsed to extract text components and then passed to the search index.
    
    Args:
        query (str): The raw search query string.
        
    Returns:
        JSONResponse: A JSON response containing a list of matching note paths.
    """
    try:
        # Parse the query to extract search text and metadata
        parsed_query = parse_query(query)
        # Use the text component for full-text search
        results = search_notes(parsed_query.get("text", ""))
        return JSONResponse(content={"results": results})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

</file>

<file path='src/backend/tasks/__init__.py'>

</file>

<file path='src/backend/tasks/models.py'>
# src/backend/tasks/models.py
"""
models.py

Defines the SQLAlchemy model for task management.
This module includes the Task model and the TaskStatus enumeration.
"""

import datetime
import enum
from sqlalchemy import Column, Integer, String, DateTime, Enum

# Updated import path for Base
from src.backend.database.base import Base  # Shared SQLAlchemy declarative base


class TaskStatus(str, enum.Enum):
    """
    Enumeration for task status values.
    Updated to match the short uppercase strings used by the frontend.
    """
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class Task(Base):
    """
    Represents a task with properties such as title, description, due date,
    priority, status, recurrence rule, and an optional link to a note.
    """
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, default="")
    due_date = Column(DateTime, nullable=True)
    priority = Column(Integer, default=2)  # 1: High, 2: Medium, 3: Low
    status = Column(Enum(TaskStatus), default=TaskStatus.TODO)
    recurrence = Column(String, nullable=True)  # e.g., "daily", "weekly", "monthly"
    note_path = Column(String, nullable=True)  # Optional link to a related note
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow
    )
</file>

<file path='src/backend/tasks/recurrence.py'>
# src/backend/tasks/recurrence.py
"""
recurrence.py

Provides simple recurrence logic for tasks.
Contains functions to calculate the next due date based on a given recurrence rule.
"""

import datetime


def get_next_due_date(current_due_date: datetime.datetime, recurrence: str) -> datetime.datetime:
    """
    Calculate the next due date based on the current due date and recurrence rule.

    Args:
        current_due_date (datetime.datetime): The current due date.
        recurrence (str): The recurrence rule ("daily", "weekly", "monthly").

    Returns:
        datetime.datetime: The computed next due date.
    """
    recurrence_lower = recurrence.lower()
    if recurrence_lower == "daily":
        return current_due_date + datetime.timedelta(days=1)
    elif recurrence_lower == "weekly":
        return current_due_date + datetime.timedelta(weeks=1)
    elif recurrence_lower == "monthly":
        # For simplicity, approximate a month as 30 days.
        return current_due_date + datetime.timedelta(days=30)
    else:
        # Return the unchanged due date if the recurrence rule is unrecognized.
        return current_due_date

</file>

<file path='src/backend/tasks/routes.py'>
# src/backend/tasks/routes.py
"""
routes.py

Defines FastAPI routes for task management.
Provides endpoints to create, read, update, and delete tasks, plus a custom endpoint for
completing recurring tasks.

Wave 2 Enhancements:
- Added a 'complete_task' endpoint to handle recurring tasks more gracefully.
  If a task has a recurrence rule, this endpoint will complete the current task
  and create a new task instance with the next due date.
"""

import datetime
from typing import List, Optional, Generator

from fastapi import APIRouter, Depends, HTTPException, Path, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Updated imports for database and tasks
from src.backend.database.sessions import SessionLocal
from src.backend.tasks.models import Task, TaskStatus
from src.backend.tasks.recurrence import get_next_due_date

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    responses={404: {"description": "Not found"}}
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session.
    
    Yields:
        Session: SQLAlchemy session object.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class TaskCreate(BaseModel):
    """
    Pydantic model for creating a new task.
    """
    title: str
    description: Optional[str] = ""
    due_date: Optional[datetime.datetime] = None
    priority: Optional[int] = 2  # 1: High, 2: Medium, 3: Low
    recurrence: Optional[str] = None
    note_path: Optional[str] = None


class TaskUpdate(BaseModel):
    """
    Pydantic model for updating an existing task.
    All fields are optional to allow partial updates.
    """
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime.datetime] = None
    priority: Optional[int] = None
    status: Optional[TaskStatus] = None
    recurrence: Optional[str] = None
    note_path: Optional[str] = None


class TaskResponse(BaseModel):
    """
    Pydantic model for task responses.
    """
    id: int
    title: str
    description: Optional[str]
    due_date: Optional[datetime.datetime]
    priority: int
    status: TaskStatus
    recurrence: Optional[str]
    note_path: Optional[str]
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True  # Allows Pydantic to read from SQLAlchemy model attributes


@router.post("/", response_model=TaskResponse, summary="Create a new task")
def create_task(task: TaskCreate, db: Session = Depends(get_db)) -> Task:
    """
    Create a new task with the provided details.
    
    Args:
        task (TaskCreate): Task data from the request body.
        db (Session): Database session dependency.

    Returns:
        Task: The newly created SQLAlchemy Task object.
    """
    new_task = Task(
        title=task.title,
        description=task.description,
        due_date=task.due_date,
        priority=task.priority,
        recurrence=task.recurrence,
        note_path=task.note_path
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task


@router.get("/", response_model=List[TaskResponse], summary="Retrieve all tasks")
def read_tasks(db: Session = Depends(get_db)) -> List[Task]:
    """
    Retrieve a list of all tasks from the database.

    Args:
        db (Session): Database session dependency.

    Returns:
        List[Task]: A list of SQLAlchemy Task objects.
    """
    tasks = db.query(Task).all()
    return tasks


@router.get("/{task_id}", response_model=TaskResponse, summary="Retrieve a task by ID")
def read_task(
    task_id: int = Path(..., description="The ID of the task"),
    db: Session = Depends(get_db)
) -> Task:
    """
    Retrieve a specific task by its ID.
    
    Args:
        task_id (int): The ID of the task to retrieve.
        db (Session): Database session dependency.
    
    Returns:
        Task: The requested SQLAlchemy Task object.
    
    Raises:
        HTTPException: If the task is not found.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{task_id}", response_model=TaskResponse, summary="Update a task")
def update_task(
    task_id: int = Path(..., description="The ID of the task to update"),
    task_update: TaskUpdate = Body(...),
    db: Session = Depends(get_db)
) -> Task:
    """
    Update an existing task with new data.

    Args:
        task_id (int): The ID of the task to update.
        task_update (TaskUpdate): Updated task data.
        db (Session): Database session dependency.

    Returns:
        Task: The updated SQLAlchemy Task object.

    Raises:
        HTTPException: If the task is not found.
    """
    existing_task = db.query(Task).filter(Task.id == task_id).first()
    if not existing_task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = task_update.dict(exclude_unset=True)

    # Update existing fields with new values.
    for key, value in update_data.items():
        setattr(existing_task, key, value)

    db.commit()
    db.refresh(existing_task)
    return existing_task


@router.delete("/{task_id}", summary="Delete a task")
def delete_task(
    task_id: int = Path(..., description="The ID of the task to delete"),
    db: Session = Depends(get_db)
) -> dict:
    """
    Delete a task by its ID.
    
    Args:
        task_id (int): The ID of the task to delete.
        db (Session): Database session dependency.
    
    Returns:
        dict: A message confirming the task deletion.

    Raises:
        HTTPException: If the task is not found.
    """
    task_obj = db.query(Task).filter(Task.id == task_id).first()
    if not task_obj:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task_obj)
    db.commit()
    return {"message": "Task deleted successfully"}


class CompleteTaskResponse(BaseModel):
    """
    Pydantic model for the response of completing a task.
    """
    completed_task: TaskResponse
    new_task: Optional[TaskResponse] = None


@router.post("/{task_id}/complete", response_model=CompleteTaskResponse, summary="Complete a task")
def complete_task(
    task_id: int = Path(..., description="The ID of the task to complete"),
    db: Session = Depends(get_db)
) -> CompleteTaskResponse:
    """
    Mark a task as completed. If the task has a recurrence rule, this endpoint will:
     - Complete the current task by setting its status to 'COMPLETED'.
     - Create a new task with the same title, description, priority, and recurrence,
       but with a due date shifted according to the recurrence rule.

    Args:
        task_id (int): The ID of the task to complete.
        db (Session): Database session.

    Returns:
        CompleteTaskResponse: A Pydantic model containing the completed task and the new task
                              (if recurrence is applied).

    Raises:
        HTTPException: If the task is not found.
    """
    existing_task = db.query(Task).filter(Task.id == task_id).first()
    if not existing_task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Mark current task as completed
    existing_task.status = TaskStatus.COMPLETED
    db.commit()
    db.refresh(existing_task)

    new_task_obj = None

    # If the task has a recurrence rule and a valid due_date, create a new task
    if existing_task.recurrence and existing_task.due_date:
        next_due = get_next_due_date(existing_task.due_date, existing_task.recurrence)
        # Build a new task using the existing task's data
        new_task_obj = Task(
            title=existing_task.title,
            description=existing_task.description,
            due_date=next_due,
            priority=existing_task.priority,
            status=TaskStatus.TODO,  # New cycle starts in TODO status
            recurrence=existing_task.recurrence,
            note_path=existing_task.note_path
        )
        db.add(new_task_obj)
        db.commit()
        db.refresh(new_task_obj)

    return CompleteTaskResponse(
        completed_task=existing_task,
        new_task=new_task_obj
    )

</file>

<file path='src/frontend/index.html'>
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <title>Local Notes Vue App</title>
  </head>
  <body>
    <!-- Important: The ID here must match app.mount('#app') in main.js -->
    <div id="app"></div>
    <!-- Vite expects to load main.js from /src/main.js or /src/main.ts -->
    <script type="module" src="/src/main.js"></script>
  </body>
</html>
</file>

<file path='src/frontend/package-lock.json'>
{
  "name": "local-notes-app",
  "version": "0.1.0",
  "lockfileVersion": 3,
  "requires": true,
  "packages": {
    "": {
      "name": "local-notes-app",
      "version": "0.1.0",
      "dependencies": {
        "axios": "^1.3.2",
        "d3": "^7.8.2",
        "marked": "^5.1.0",
        "vue": "^3.2.47"
      },
      "devDependencies": {
        "@vitejs/plugin-vue": "^4.0.0",
        "concurrently": "^7.6.0",
        "vite": "^4.0.0"
      }
    },
    "node_modules/@babel/helper-string-parser": {
      "version": "7.25.9",
      "resolved": "https://registry.npmjs.org/@babel/helper-string-parser/-/helper-string-parser-7.25.9.tgz",
      "integrity": "sha512-4A/SCr/2KLd5jrtOMFzaKjVtAei3+2r/NChoBNoZ3EyP/+GlhoaEGoWOZUmFmoITP7zOJyHIMm+DYRd8o3PvHA==",
      "engines": {
        "node": ">=6.9.0"
      }
    },
    "node_modules/@babel/helper-validator-identifier": {
      "version": "7.25.9",
      "resolved": "https://registry.npmjs.org/@babel/helper-validator-identifier/-/helper-validator-identifier-7.25.9.tgz",
      "integrity": "sha512-Ed61U6XJc3CVRfkERJWDz4dJwKe7iLmmJsbOGu9wSloNSFttHV0I8g6UAgb7qnK5ly5bGLPd4oXZlxCdANBOWQ==",
      "engines": {
        "node": ">=6.9.0"
      }
    },
    "node_modules/@babel/parser": {
      "version": "7.26.8",
      "resolved": "https://registry.npmjs.org/@babel/parser/-/parser-7.26.8.tgz",
      "integrity": "sha512-TZIQ25pkSoaKEYYaHbbxkfL36GNsQ6iFiBbeuzAkLnXayKR1yP1zFe+NxuZWWsUyvt8icPU9CCq0sgWGXR1GEw==",
      "dependencies": {
        "@babel/types": "^7.26.8"
      },
      "bin": {
        "parser": "bin/babel-parser.js"
      },
      "engines": {
        "node": ">=6.0.0"
      }
    },
    "node_modules/@babel/runtime": {
      "version": "7.26.7",
      "resolved": "https://registry.npmjs.org/@babel/runtime/-/runtime-7.26.7.tgz",
      "integrity": "sha512-AOPI3D+a8dXnja+iwsUqGRjr1BbZIe771sXdapOtYI531gSqpi92vXivKcq2asu/DFpdl1ceFAKZyRzK2PCVcQ==",
      "dev": true,
      "dependencies": {
        "regenerator-runtime": "^0.14.0"
      },
      "engines": {
        "node": ">=6.9.0"
      }
    },
    "node_modules/@babel/types": {
      "version": "7.26.8",
      "resolved": "https://registry.npmjs.org/@babel/types/-/types-7.26.8.tgz",
      "integrity": "sha512-eUuWapzEGWFEpHFxgEaBG8e3n6S8L3MSu0oda755rOfabWPnh0Our1AozNFVUxGFIhbKgd1ksprsoDGMinTOTA==",
      "dependencies": {
        "@babel/helper-string-parser": "^7.25.9",
        "@babel/helper-validator-identifier": "^7.25.9"
      },
      "engines": {
        "node": ">=6.9.0"
      }
    },
    "node_modules/@esbuild/android-arm": {
      "version": "0.18.20",
      "resolved": "https://registry.npmjs.org/@esbuild/android-arm/-/android-arm-0.18.20.tgz",
      "integrity": "sha512-fyi7TDI/ijKKNZTUJAQqiG5T7YjJXgnzkURqmGj13C6dCqckZBLdl4h7bkhHt/t0WP+zO9/zwroDvANaOqO5Sw==",
      "cpu": [
        "arm"
      ],
      "dev": true,
      "optional": true,
      "os": [
        "android"
      ],
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/@esbuild/android-arm64": {
      "version": "0.18.20",
      "resolved": "https://registry.npmjs.org/@esbuild/android-arm64/-/android-arm64-0.18.20.tgz",
      "integrity": "sha512-Nz4rJcchGDtENV0eMKUNa6L12zz2zBDXuhj/Vjh18zGqB44Bi7MBMSXjgunJgjRhCmKOjnPuZp4Mb6OKqtMHLQ==",
      "cpu": [
        "arm64"
      ],
      "dev": true,
      "optional": true,
      "os": [
        "android"
      ],
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/@esbuild/android-x64": {
      "version": "0.18.20",
      "resolved": "https://registry.npmjs.org/@esbuild/android-x64/-/android-x64-0.18.20.tgz",
      "integrity": "sha512-8GDdlePJA8D6zlZYJV/jnrRAi6rOiNaCC/JclcXpB+KIuvfBN4owLtgzY2bsxnx666XjJx2kDPUmnTtR8qKQUg==",
      "cpu": [
        "x64"
      ],
      "dev": true,
      "optional": true,
      "os": [
        "android"
      ],
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/@esbuild/darwin-arm64": {
      "version": "0.18.20",
      "resolved": "https://registry.npmjs.org/@esbuild/darwin-arm64/-/darwin-arm64-0.18.20.tgz",
      "integrity": "sha512-bxRHW5kHU38zS2lPTPOyuyTm+S+eobPUnTNkdJEfAddYgEcll4xkT8DB9d2008DtTbl7uJag2HuE5NZAZgnNEA==",
      "cpu": [
        "arm64"
      ],
      "dev": true,
      "optional": true,
      "os": [
        "darwin"
      ],
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/@esbuild/darwin-x64": {
      "version": "0.18.20",
      "resolved": "https://registry.npmjs.org/@esbuild/darwin-x64/-/darwin-x64-0.18.20.tgz",
      "integrity": "sha512-pc5gxlMDxzm513qPGbCbDukOdsGtKhfxD1zJKXjCCcU7ju50O7MeAZ8c4krSJcOIJGFR+qx21yMMVYwiQvyTyQ==",
      "cpu": [
        "x64"
      ],
      "dev": true,
      "optional": true,
      "os": [
        "darwin"
      ],
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/@esbuild/freebsd-arm64": {
      "version": "0.18.20",
      "resolved": "https://registry.npmjs.org/@esbuild/freebsd-arm64/-/freebsd-arm64-0.18.20.tgz",
      "integrity": "sha512-yqDQHy4QHevpMAaxhhIwYPMv1NECwOvIpGCZkECn8w2WFHXjEwrBn3CeNIYsibZ/iZEUemj++M26W3cNR5h+Tw==",
      "cpu": [
        "arm64"
      ],
      "dev": true,
      "optional": true,
      "os": [
        "freebsd"
      ],
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/@esbuild/freebsd-x64": {
      "version": "0.18.20",
      "resolved": "https://registry.npmjs.org/@esbuild/freebsd-x64/-/freebsd-x64-0.18.20.tgz",
      "integrity": "sha512-tgWRPPuQsd3RmBZwarGVHZQvtzfEBOreNuxEMKFcd5DaDn2PbBxfwLcj4+aenoh7ctXcbXmOQIn8HI6mCSw5MQ==",
      "cpu": [
        "x64"
      ],
      "dev": true,
      "optional": true,
      "os": [
        "freebsd"
      ],
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/@esbuild/linux-arm": {
      "version": "0.18.20",
      "resolved": "https://registry.npmjs.org/@esbuild/linux-arm/-/linux-arm-0.18.20.tgz",
      "integrity": "sha512-/5bHkMWnq1EgKr1V+Ybz3s1hWXok7mDFUMQ4cG10AfW3wL02PSZi5kFpYKrptDsgb2WAJIvRcDm+qIvXf/apvg==",
      "cpu": [
        "arm"
      ],
      "dev": true,
      "optional": true,
      "os": [
        "linux"
      ],
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/@esbuild/linux-arm64": {
      "version": "0.18.20",
      "resolved": "https://registry.npmjs.org/@esbuild/linux-arm64/-/linux-arm64-0.18.20.tgz",
      "integrity": "sha512-2YbscF+UL7SQAVIpnWvYwM+3LskyDmPhe31pE7/aoTMFKKzIc9lLbyGUpmmb8a8AixOL61sQ/mFh3jEjHYFvdA==",
      "cpu": [
        "arm64"
      ],
      "dev": true,
      "optional": true,
      "os": [
        "linux"
      ],
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/@esbuild/linux-ia32": {
      "version": "0.18.20",
      "resolved": "https://registry.npmjs.org/@esbuild/linux-ia32/-/linux-ia32-0.18.20.tgz",
      "integrity": "sha512-P4etWwq6IsReT0E1KHU40bOnzMHoH73aXp96Fs8TIT6z9Hu8G6+0SHSw9i2isWrD2nbx2qo5yUqACgdfVGx7TA==",
      "cpu": [
        "ia32"
      ],
      "dev": true,
      "optional": true,
      "os": [
        "linux"
      ],
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/@esbuild/linux-loong64": {
      "version": "0.18.20",
      "resolved": "https://registry.npmjs.org/@esbuild/linux-loong64/-/linux-loong64-0.18.20.tgz",
      "integrity": "sha512-nXW8nqBTrOpDLPgPY9uV+/1DjxoQ7DoB2N8eocyq8I9XuqJ7BiAMDMf9n1xZM9TgW0J8zrquIb/A7s3BJv7rjg==",
      "cpu": [
        "loong64"
      ],
      "dev": true,
      "optional": true,
      "os": [
        "linux"
      ],
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/@esbuild/linux-mips64el": {
      "version": "0.18.20",
      "resolved": "https://registry.npmjs.org/@esbuild/linux-mips64el/-/linux-mips64el-0.18.20.tgz",
      "integrity": "sha512-d5NeaXZcHp8PzYy5VnXV3VSd2D328Zb+9dEq5HE6bw6+N86JVPExrA6O68OPwobntbNJ0pzCpUFZTo3w0GyetQ==",
      "cpu": [
        "mips64el"
      ],
      "dev": true,
      "optional": true,
      "os": [
        "linux"
      ],
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/@esbuild/linux-ppc64": {
      "version": "0.18.20",
      "resolved": "https://registry.npmjs.org/@esbuild/linux-ppc64/-/linux-ppc64-0.18.20.tgz",
      "integrity": "sha512-WHPyeScRNcmANnLQkq6AfyXRFr5D6N2sKgkFo2FqguP44Nw2eyDlbTdZwd9GYk98DZG9QItIiTlFLHJHjxP3FA==",
      "cpu": [
        "ppc64"
      ],
      "dev": true,
      "optional": true,
      "os": [
        "linux"
      ],
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/@esbuild/linux-riscv64": {
      "version": "0.18.20",
      "resolved": "https://registry.npmjs.org/@esbuild/linux-riscv64/-/linux-riscv64-0.18.20.tgz",
      "integrity": "sha512-WSxo6h5ecI5XH34KC7w5veNnKkju3zBRLEQNY7mv5mtBmrP/MjNBCAlsM2u5hDBlS3NGcTQpoBvRzqBcRtpq1A==",
      "cpu": [
        "riscv64"
      ],
      "dev": true,
      "optional": true,
      "os": [
        "linux"
      ],
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/@esbuild/linux-s390x": {
      "version": "0.18.20",
      "resolved": "https://registry.npmjs.org/@esbuild/linux-s390x/-/linux-s390x-0.18.20.tgz",
      "integrity": "sha512-+8231GMs3mAEth6Ja1iK0a1sQ3ohfcpzpRLH8uuc5/KVDFneH6jtAJLFGafpzpMRO6DzJ6AvXKze9LfFMrIHVQ==",
      "cpu": [
        "s390x"
      ],
      "dev": true,
      "optional": true,
      "os": [
        "linux"
      ],
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/@esbuild/linux-x64": {
      "version": "0.18.20",
      "resolved": "https://registry.npmjs.org/@esbuild/linux-x64/-/linux-x64-0.18.20.tgz",
      "integrity": "sha512-UYqiqemphJcNsFEskc73jQ7B9jgwjWrSayxawS6UVFZGWrAAtkzjxSqnoclCXxWtfwLdzU+vTpcNYhpn43uP1w==",
      "cpu": [
        "x64"
      ],
      "dev": true,
      "optional": true,
      "os": [
        "linux"
      ],
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/@esbuild/netbsd-x64": {
      "version": "0.18.20",
      "resolved": "https://registry.npmjs.org/@esbuild/netbsd-x64/-/netbsd-x64-0.18.20.tgz",
      "integrity": "sha512-iO1c++VP6xUBUmltHZoMtCUdPlnPGdBom6IrO4gyKPFFVBKioIImVooR5I83nTew5UOYrk3gIJhbZh8X44y06A==",
      "cpu": [
        "x64"
      ],
      "dev": true,
      "optional": true,
      "os": [
        "netbsd"
      ],
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/@esbuild/openbsd-x64": {
      "version": "0.18.20",
      "resolved": "https://registry.npmjs.org/@esbuild/openbsd-x64/-/openbsd-x64-0.18.20.tgz",
      "integrity": "sha512-e5e4YSsuQfX4cxcygw/UCPIEP6wbIL+se3sxPdCiMbFLBWu0eiZOJ7WoD+ptCLrmjZBK1Wk7I6D/I3NglUGOxg==",
      "cpu": [
        "x64"
      ],
      "dev": true,
      "optional": true,
      "os": [
        "openbsd"
      ],
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/@esbuild/sunos-x64": {
      "version": "0.18.20",
      "resolved": "https://registry.npmjs.org/@esbuild/sunos-x64/-/sunos-x64-0.18.20.tgz",
      "integrity": "sha512-kDbFRFp0YpTQVVrqUd5FTYmWo45zGaXe0X8E1G/LKFC0v8x0vWrhOWSLITcCn63lmZIxfOMXtCfti/RxN/0wnQ==",
      "cpu": [
        "x64"
      ],
      "dev": true,
      "optional": true,
      "os": [
        "sunos"
      ],
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/@esbuild/win32-arm64": {
      "version": "0.18.20",
      "resolved": "https://registry.npmjs.org/@esbuild/win32-arm64/-/win32-arm64-0.18.20.tgz",
      "integrity": "sha512-ddYFR6ItYgoaq4v4JmQQaAI5s7npztfV4Ag6NrhiaW0RrnOXqBkgwZLofVTlq1daVTQNhtI5oieTvkRPfZrePg==",
      "cpu": [
        "arm64"
      ],
      "dev": true,
      "optional": true,
      "os": [
        "win32"
      ],
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/@esbuild/win32-ia32": {
      "version": "0.18.20",
      "resolved": "https://registry.npmjs.org/@esbuild/win32-ia32/-/win32-ia32-0.18.20.tgz",
      "integrity": "sha512-Wv7QBi3ID/rROT08SABTS7eV4hX26sVduqDOTe1MvGMjNd3EjOz4b7zeexIR62GTIEKrfJXKL9LFxTYgkyeu7g==",
      "cpu": [
        "ia32"
      ],
      "dev": true,
      "optional": true,
      "os": [
        "win32"
      ],
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/@esbuild/win32-x64": {
      "version": "0.18.20",
      "resolved": "https://registry.npmjs.org/@esbuild/win32-x64/-/win32-x64-0.18.20.tgz",
      "integrity": "sha512-kTdfRcSiDfQca/y9QIkng02avJ+NCaQvrMejlsB3RRv5sE9rRoeBPISaZpKxHELzRxZyLvNts1P27W3wV+8geQ==",
      "cpu": [
        "x64"
      ],
      "dev": true,
      "optional": true,
      "os": [
        "win32"
      ],
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/@jridgewell/sourcemap-codec": {
      "version": "1.5.0",
      "resolved": "https://registry.npmjs.org/@jridgewell/sourcemap-codec/-/sourcemap-codec-1.5.0.tgz",
      "integrity": "sha512-gv3ZRaISU3fjPAgNsriBRqGWQL6quFx04YMPW/zD8XMLsU32mhCCbfbO6KZFLjvYpCZ8zyDEgqsgf+PwPaM7GQ=="
    },
    "node_modules/@vitejs/plugin-vue": {
      "version": "4.6.2",
      "resolved": "https://registry.npmjs.org/@vitejs/plugin-vue/-/plugin-vue-4.6.2.tgz",
      "integrity": "sha512-kqf7SGFoG+80aZG6Pf+gsZIVvGSCKE98JbiWqcCV9cThtg91Jav0yvYFC9Zb+jKetNGF6ZKeoaxgZfND21fWKw==",
      "dev": true,
      "engines": {
        "node": "^14.18.0 || >=16.0.0"
      },
      "peerDependencies": {
        "vite": "^4.0.0 || ^5.0.0",
        "vue": "^3.2.25"
      }
    },
    "node_modules/@vue/compiler-core": {
      "version": "3.5.13",
      "resolved": "https://registry.npmjs.org/@vue/compiler-core/-/compiler-core-3.5.13.tgz",
      "integrity": "sha512-oOdAkwqUfW1WqpwSYJce06wvt6HljgY3fGeM9NcVA1HaYOij3mZG9Rkysn0OHuyUAGMbEbARIpsG+LPVlBJ5/Q==",
      "dependencies": {
        "@babel/parser": "^7.25.3",
        "@vue/shared": "3.5.13",
        "entities": "^4.5.0",
        "estree-walker": "^2.0.2",
        "source-map-js": "^1.2.0"
      }
    },
    "node_modules/@vue/compiler-dom": {
      "version": "3.5.13",
      "resolved": "https://registry.npmjs.org/@vue/compiler-dom/-/compiler-dom-3.5.13.tgz",
      "integrity": "sha512-ZOJ46sMOKUjO3e94wPdCzQ6P1Lx/vhp2RSvfaab88Ajexs0AHeV0uasYhi99WPaogmBlRHNRuly8xV75cNTMDA==",
      "dependencies": {
        "@vue/compiler-core": "3.5.13",
        "@vue/shared": "3.5.13"
      }
    },
    "node_modules/@vue/compiler-sfc": {
      "version": "3.5.13",
      "resolved": "https://registry.npmjs.org/@vue/compiler-sfc/-/compiler-sfc-3.5.13.tgz",
      "integrity": "sha512-6VdaljMpD82w6c2749Zhf5T9u5uLBWKnVue6XWxprDobftnletJ8+oel7sexFfM3qIxNmVE7LSFGTpv6obNyaQ==",
      "dependencies": {
        "@babel/parser": "^7.25.3",
        "@vue/compiler-core": "3.5.13",
        "@vue/compiler-dom": "3.5.13",
        "@vue/compiler-ssr": "3.5.13",
        "@vue/shared": "3.5.13",
        "estree-walker": "^2.0.2",
        "magic-string": "^0.30.11",
        "postcss": "^8.4.48",
        "source-map-js": "^1.2.0"
      }
    },
    "node_modules/@vue/compiler-ssr": {
      "version": "3.5.13",
      "resolved": "https://registry.npmjs.org/@vue/compiler-ssr/-/compiler-ssr-3.5.13.tgz",
      "integrity": "sha512-wMH6vrYHxQl/IybKJagqbquvxpWCuVYpoUJfCqFZwa/JY1GdATAQ+TgVtgrwwMZ0D07QhA99rs/EAAWfvG6KpA==",
      "dependencies": {
        "@vue/compiler-dom": "3.5.13",
        "@vue/shared": "3.5.13"
      }
    },
    "node_modules/@vue/reactivity": {
      "version": "3.5.13",
      "resolved": "https://registry.npmjs.org/@vue/reactivity/-/reactivity-3.5.13.tgz",
      "integrity": "sha512-NaCwtw8o48B9I6L1zl2p41OHo/2Z4wqYGGIK1Khu5T7yxrn+ATOixn/Udn2m+6kZKB/J7cuT9DbWWhRxqixACg==",
      "dependencies": {
        "@vue/shared": "3.5.13"
      }
    },
    "node_modules/@vue/runtime-core": {
      "version": "3.5.13",
      "resolved": "https://registry.npmjs.org/@vue/runtime-core/-/runtime-core-3.5.13.tgz",
      "integrity": "sha512-Fj4YRQ3Az0WTZw1sFe+QDb0aXCerigEpw418pw1HBUKFtnQHWzwojaukAs2X/c9DQz4MQ4bsXTGlcpGxU/RCIw==",
      "dependencies": {
        "@vue/reactivity": "3.5.13",
        "@vue/shared": "3.5.13"
      }
    },
    "node_modules/@vue/runtime-dom": {
      "version": "3.5.13",
      "resolved": "https://registry.npmjs.org/@vue/runtime-dom/-/runtime-dom-3.5.13.tgz",
      "integrity": "sha512-dLaj94s93NYLqjLiyFzVs9X6dWhTdAlEAciC3Moq7gzAc13VJUdCnjjRurNM6uTLFATRHexHCTu/Xp3eW6yoog==",
      "dependencies": {
        "@vue/reactivity": "3.5.13",
        "@vue/runtime-core": "3.5.13",
        "@vue/shared": "3.5.13",
        "csstype": "^3.1.3"
      }
    },
    "node_modules/@vue/server-renderer": {
      "version": "3.5.13",
      "resolved": "https://registry.npmjs.org/@vue/server-renderer/-/server-renderer-3.5.13.tgz",
      "integrity": "sha512-wAi4IRJV/2SAW3htkTlB+dHeRmpTiVIK1OGLWV1yeStVSebSQQOwGwIq0D3ZIoBj2C2qpgz5+vX9iEBkTdk5YA==",
      "dependencies": {
        "@vue/compiler-ssr": "3.5.13",
        "@vue/shared": "3.5.13"
      },
      "peerDependencies": {
        "vue": "3.5.13"
      }
    },
    "node_modules/@vue/shared": {
      "version": "3.5.13",
      "resolved": "https://registry.npmjs.org/@vue/shared/-/shared-3.5.13.tgz",
      "integrity": "sha512-/hnE/qP5ZoGpol0a5mDi45bOd7t3tjYJBjsgCsivow7D48cJeV5l05RD82lPqi7gRiphZM37rnhW1l6ZoCNNnQ=="
    },
    "node_modules/ansi-regex": {
      "version": "5.0.1",
      "resolved": "https://registry.npmjs.org/ansi-regex/-/ansi-regex-5.0.1.tgz",
      "integrity": "sha512-quJQXlTSUGL2LH9SUXo8VwsY4soanhgo6LNSm84E1LBcE8s3O0wpdiRzyR9z/ZZJMlMWv37qOOb9pdJlMUEKFQ==",
      "dev": true,
      "engines": {
        "node": ">=8"
      }
    },
    "node_modules/ansi-styles": {
      "version": "4.3.0",
      "resolved": "https://registry.npmjs.org/ansi-styles/-/ansi-styles-4.3.0.tgz",
      "integrity": "sha512-zbB9rCJAT1rbjiVDb2hqKFHNYLxgtk8NURxZ3IZwD3F6NtxbXZQCnnSi1Lkx+IDohdPlFp222wVALIheZJQSEg==",
      "dev": true,
      "dependencies": {
        "color-convert": "^2.0.1"
      },
      "engines": {
        "node": ">=8"
      },
      "funding": {
        "url": "https://github.com/chalk/ansi-styles?sponsor=1"
      }
    },
    "node_modules/asynckit": {
      "version": "0.4.0",
      "resolved": "https://registry.npmjs.org/asynckit/-/asynckit-0.4.0.tgz",
      "integrity": "sha512-Oei9OH4tRh0YqU3GxhX79dM/mwVgvbZJaSNaRk+bshkj0S5cfHcgYakreBjrHwatXKbz+IoIdYLxrKim2MjW0Q=="
    },
    "node_modules/axios": {
      "version": "1.7.9",
      "resolved": "https://registry.npmjs.org/axios/-/axios-1.7.9.tgz",
      "integrity": "sha512-LhLcE7Hbiryz8oMDdDptSrWowmB4Bl6RCt6sIJKpRB4XtVf0iEgewX3au/pJqm+Py1kCASkb/FFKjxQaLtxJvw==",
      "dependencies": {
        "follow-redirects": "^1.15.6",
        "form-data": "^4.0.0",
        "proxy-from-env": "^1.1.0"
      }
    },
    "node_modules/chalk": {
      "version": "4.1.2",
      "resolved": "https://registry.npmjs.org/chalk/-/chalk-4.1.2.tgz",
      "integrity": "sha512-oKnbhFyRIXpUuez8iBMmyEa4nbj4IOQyuhc/wy9kY7/WVPcwIO9VA668Pu8RkO7+0G76SLROeyw9CpQ061i4mA==",
      "dev": true,
      "dependencies": {
        "ansi-styles": "^4.1.0",
        "supports-color": "^7.1.0"
      },
      "engines": {
        "node": ">=10"
      },
      "funding": {
        "url": "https://github.com/chalk/chalk?sponsor=1"
      }
    },
    "node_modules/chalk/node_modules/supports-color": {
      "version": "7.2.0",
      "resolved": "https://registry.npmjs.org/supports-color/-/supports-color-7.2.0.tgz",
      "integrity": "sha512-qpCAvRl9stuOHveKsn7HncJRvv501qIacKzQlO/+Lwxc9+0q2wLyv4Dfvt80/DPn2pqOBsJdDiogXGR9+OvwRw==",
      "dev": true,
      "dependencies": {
        "has-flag": "^4.0.0"
      },
      "engines": {
        "node": ">=8"
      }
    },
    "node_modules/cliui": {
      "version": "8.0.1",
      "resolved": "https://registry.npmjs.org/cliui/-/cliui-8.0.1.tgz",
      "integrity": "sha512-BSeNnyus75C4//NQ9gQt1/csTXyo/8Sb+afLAkzAptFuMsod9HFokGNudZpi/oQV73hnVK+sR+5PVRMd+Dr7YQ==",
      "dev": true,
      "dependencies": {
        "string-width": "^4.2.0",
        "strip-ansi": "^6.0.1",
        "wrap-ansi": "^7.0.0"
      },
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/color-convert": {
      "version": "2.0.1",
      "resolved": "https://registry.npmjs.org/color-convert/-/color-convert-2.0.1.tgz",
      "integrity": "sha512-RRECPsj7iu/xb5oKYcsFHSppFNnsj/52OVTRKb4zP5onXwVF3zVmmToNcOfGC+CRDpfK/U584fMg38ZHCaElKQ==",
      "dev": true,
      "dependencies": {
        "color-name": "~1.1.4"
      },
      "engines": {
        "node": ">=7.0.0"
      }
    },
    "node_modules/color-name": {
      "version": "1.1.4",
      "resolved": "https://registry.npmjs.org/color-name/-/color-name-1.1.4.tgz",
      "integrity": "sha512-dOy+3AuW3a2wNbZHIuMZpTcgjGuLU/uBL/ubcZF9OXbDo8ff4O8yVp5Bf0efS8uEoYo5q4Fx7dY9OgQGXgAsQA==",
      "dev": true
    },
    "node_modules/combined-stream": {
      "version": "1.0.8",
      "resolved": "https://registry.npmjs.org/combined-stream/-/combined-stream-1.0.8.tgz",
      "integrity": "sha512-FQN4MRfuJeHf7cBbBMJFXhKSDq+2kAArBlmRBvcvFE5BB1HZKXtSFASDhdlz9zOYwxh8lDdnvmMOe/+5cdoEdg==",
      "dependencies": {
        "delayed-stream": "~1.0.0"
      },
      "engines": {
        "node": ">= 0.8"
      }
    },
    "node_modules/commander": {
      "version": "7.2.0",
      "resolved": "https://registry.npmjs.org/commander/-/commander-7.2.0.tgz",
      "integrity": "sha512-QrWXB+ZQSVPmIWIhtEO9H+gwHaMGYiF5ChvoJ+K9ZGHG/sVsa6yiesAD1GC/x46sET00Xlwo1u49RVVVzvcSkw==",
      "engines": {
        "node": ">= 10"
      }
    },
    "node_modules/concurrently": {
      "version": "7.6.0",
      "resolved": "https://registry.npmjs.org/concurrently/-/concurrently-7.6.0.tgz",
      "integrity": "sha512-BKtRgvcJGeZ4XttiDiNcFiRlxoAeZOseqUvyYRUp/Vtd+9p1ULmeoSqGsDA+2ivdeDFpqrJvGvmI+StKfKl5hw==",
      "dev": true,
      "dependencies": {
        "chalk": "^4.1.0",
        "date-fns": "^2.29.1",
        "lodash": "^4.17.21",
        "rxjs": "^7.0.0",
        "shell-quote": "^1.7.3",
        "spawn-command": "^0.0.2-1",
        "supports-color": "^8.1.0",
        "tree-kill": "^1.2.2",
        "yargs": "^17.3.1"
      },
      "bin": {
        "conc": "dist/bin/concurrently.js",
        "concurrently": "dist/bin/concurrently.js"
      },
      "engines": {
        "node": "^12.20.0 || ^14.13.0 || >=16.0.0"
      },
      "funding": {
        "url": "https://github.com/open-cli-tools/concurrently?sponsor=1"
      }
    },
    "node_modules/csstype": {
      "version": "3.1.3",
      "resolved": "https://registry.npmjs.org/csstype/-/csstype-3.1.3.tgz",
      "integrity": "sha512-M1uQkMl8rQK/szD0LNhtqxIPLpimGm8sOBwU7lLnCpSbTyY3yeU1Vc7l4KT5zT4s/yOxHH5O7tIuuLOCnLADRw=="
    },
    "node_modules/d3": {
      "version": "7.9.0",
      "resolved": "https://registry.npmjs.org/d3/-/d3-7.9.0.tgz",
      "integrity": "sha512-e1U46jVP+w7Iut8Jt8ri1YsPOvFpg46k+K8TpCb0P+zjCkjkPnV7WzfDJzMHy1LnA+wj5pLT1wjO901gLXeEhA==",
      "dependencies": {
        "d3-array": "3",
        "d3-axis": "3",
        "d3-brush": "3",
        "d3-chord": "3",
        "d3-color": "3",
        "d3-contour": "4",
        "d3-delaunay": "6",
        "d3-dispatch": "3",
        "d3-drag": "3",
        "d3-dsv": "3",
        "d3-ease": "3",
        "d3-fetch": "3",
        "d3-force": "3",
        "d3-format": "3",
        "d3-geo": "3",
        "d3-hierarchy": "3",
        "d3-interpolate": "3",
        "d3-path": "3",
        "d3-polygon": "3",
        "d3-quadtree": "3",
        "d3-random": "3",
        "d3-scale": "4",
        "d3-scale-chromatic": "3",
        "d3-selection": "3",
        "d3-shape": "3",
        "d3-time": "3",
        "d3-time-format": "4",
        "d3-timer": "3",
        "d3-transition": "3",
        "d3-zoom": "3"
      },
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-array": {
      "version": "3.2.4",
      "resolved": "https://registry.npmjs.org/d3-array/-/d3-array-3.2.4.tgz",
      "integrity": "sha512-tdQAmyA18i4J7wprpYq8ClcxZy3SC31QMeByyCFyRt7BVHdREQZ5lpzoe5mFEYZUWe+oq8HBvk9JjpibyEV4Jg==",
      "dependencies": {
        "internmap": "1 - 2"
      },
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-axis": {
      "version": "3.0.0",
      "resolved": "https://registry.npmjs.org/d3-axis/-/d3-axis-3.0.0.tgz",
      "integrity": "sha512-IH5tgjV4jE/GhHkRV0HiVYPDtvfjHQlQfJHs0usq7M30XcSBvOotpmH1IgkcXsO/5gEQZD43B//fc7SRT5S+xw==",
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-brush": {
      "version": "3.0.0",
      "resolved": "https://registry.npmjs.org/d3-brush/-/d3-brush-3.0.0.tgz",
      "integrity": "sha512-ALnjWlVYkXsVIGlOsuWH1+3udkYFI48Ljihfnh8FZPF2QS9o+PzGLBslO0PjzVoHLZ2KCVgAM8NVkXPJB2aNnQ==",
      "dependencies": {
        "d3-dispatch": "1 - 3",
        "d3-drag": "2 - 3",
        "d3-interpolate": "1 - 3",
        "d3-selection": "3",
        "d3-transition": "3"
      },
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-chord": {
      "version": "3.0.1",
      "resolved": "https://registry.npmjs.org/d3-chord/-/d3-chord-3.0.1.tgz",
      "integrity": "sha512-VE5S6TNa+j8msksl7HwjxMHDM2yNK3XCkusIlpX5kwauBfXuyLAtNg9jCp/iHH61tgI4sb6R/EIMWCqEIdjT/g==",
      "dependencies": {
        "d3-path": "1 - 3"
      },
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-color": {
      "version": "3.1.0",
      "resolved": "https://registry.npmjs.org/d3-color/-/d3-color-3.1.0.tgz",
      "integrity": "sha512-zg/chbXyeBtMQ1LbD/WSoW2DpC3I0mpmPdW+ynRTj/x2DAWYrIY7qeZIHidozwV24m4iavr15lNwIwLxRmOxhA==",
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-contour": {
      "version": "4.0.2",
      "resolved": "https://registry.npmjs.org/d3-contour/-/d3-contour-4.0.2.tgz",
      "integrity": "sha512-4EzFTRIikzs47RGmdxbeUvLWtGedDUNkTcmzoeyg4sP/dvCexO47AaQL7VKy/gul85TOxw+IBgA8US2xwbToNA==",
      "dependencies": {
        "d3-array": "^3.2.0"
      },
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-delaunay": {
      "version": "6.0.4",
      "resolved": "https://registry.npmjs.org/d3-delaunay/-/d3-delaunay-6.0.4.tgz",
      "integrity": "sha512-mdjtIZ1XLAM8bm/hx3WwjfHt6Sggek7qH043O8KEjDXN40xi3vx/6pYSVTwLjEgiXQTbvaouWKynLBiUZ6SK6A==",
      "dependencies": {
        "delaunator": "5"
      },
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-dispatch": {
      "version": "3.0.1",
      "resolved": "https://registry.npmjs.org/d3-dispatch/-/d3-dispatch-3.0.1.tgz",
      "integrity": "sha512-rzUyPU/S7rwUflMyLc1ETDeBj0NRuHKKAcvukozwhshr6g6c5d8zh4c2gQjY2bZ0dXeGLWc1PF174P2tVvKhfg==",
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-drag": {
      "version": "3.0.0",
      "resolved": "https://registry.npmjs.org/d3-drag/-/d3-drag-3.0.0.tgz",
      "integrity": "sha512-pWbUJLdETVA8lQNJecMxoXfH6x+mO2UQo8rSmZ+QqxcbyA3hfeprFgIT//HW2nlHChWeIIMwS2Fq+gEARkhTkg==",
      "dependencies": {
        "d3-dispatch": "1 - 3",
        "d3-selection": "3"
      },
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-dsv": {
      "version": "3.0.1",
      "resolved": "https://registry.npmjs.org/d3-dsv/-/d3-dsv-3.0.1.tgz",
      "integrity": "sha512-UG6OvdI5afDIFP9w4G0mNq50dSOsXHJaRE8arAS5o9ApWnIElp8GZw1Dun8vP8OyHOZ/QJUKUJwxiiCCnUwm+Q==",
      "dependencies": {
        "commander": "7",
        "iconv-lite": "0.6",
        "rw": "1"
      },
      "bin": {
        "csv2json": "bin/dsv2json.js",
        "csv2tsv": "bin/dsv2dsv.js",
        "dsv2dsv": "bin/dsv2dsv.js",
        "dsv2json": "bin/dsv2json.js",
        "json2csv": "bin/json2dsv.js",
        "json2dsv": "bin/json2dsv.js",
        "json2tsv": "bin/json2dsv.js",
        "tsv2csv": "bin/dsv2dsv.js",
        "tsv2json": "bin/dsv2json.js"
      },
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-ease": {
      "version": "3.0.1",
      "resolved": "https://registry.npmjs.org/d3-ease/-/d3-ease-3.0.1.tgz",
      "integrity": "sha512-wR/XK3D3XcLIZwpbvQwQ5fK+8Ykds1ip7A2Txe0yxncXSdq1L9skcG7blcedkOX+ZcgxGAmLX1FrRGbADwzi0w==",
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-fetch": {
      "version": "3.0.1",
      "resolved": "https://registry.npmjs.org/d3-fetch/-/d3-fetch-3.0.1.tgz",
      "integrity": "sha512-kpkQIM20n3oLVBKGg6oHrUchHM3xODkTzjMoj7aWQFq5QEM+R6E4WkzT5+tojDY7yjez8KgCBRoj4aEr99Fdqw==",
      "dependencies": {
        "d3-dsv": "1 - 3"
      },
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-force": {
      "version": "3.0.0",
      "resolved": "https://registry.npmjs.org/d3-force/-/d3-force-3.0.0.tgz",
      "integrity": "sha512-zxV/SsA+U4yte8051P4ECydjD/S+qeYtnaIyAs9tgHCqfguma/aAQDjo85A9Z6EKhBirHRJHXIgJUlffT4wdLg==",
      "dependencies": {
        "d3-dispatch": "1 - 3",
        "d3-quadtree": "1 - 3",
        "d3-timer": "1 - 3"
      },
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-format": {
      "version": "3.1.0",
      "resolved": "https://registry.npmjs.org/d3-format/-/d3-format-3.1.0.tgz",
      "integrity": "sha512-YyUI6AEuY/Wpt8KWLgZHsIU86atmikuoOmCfommt0LYHiQSPjvX2AcFc38PX0CBpr2RCyZhjex+NS/LPOv6YqA==",
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-geo": {
      "version": "3.1.1",
      "resolved": "https://registry.npmjs.org/d3-geo/-/d3-geo-3.1.1.tgz",
      "integrity": "sha512-637ln3gXKXOwhalDzinUgY83KzNWZRKbYubaG+fGVuc/dxO64RRljtCTnf5ecMyE1RIdtqpkVcq0IbtU2S8j2Q==",
      "dependencies": {
        "d3-array": "2.5.0 - 3"
      },
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-hierarchy": {
      "version": "3.1.2",
      "resolved": "https://registry.npmjs.org/d3-hierarchy/-/d3-hierarchy-3.1.2.tgz",
      "integrity": "sha512-FX/9frcub54beBdugHjDCdikxThEqjnR93Qt7PvQTOHxyiNCAlvMrHhclk3cD5VeAaq9fxmfRp+CnWw9rEMBuA==",
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-interpolate": {
      "version": "3.0.1",
      "resolved": "https://registry.npmjs.org/d3-interpolate/-/d3-interpolate-3.0.1.tgz",
      "integrity": "sha512-3bYs1rOD33uo8aqJfKP3JWPAibgw8Zm2+L9vBKEHJ2Rg+viTR7o5Mmv5mZcieN+FRYaAOWX5SJATX6k1PWz72g==",
      "dependencies": {
        "d3-color": "1 - 3"
      },
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-path": {
      "version": "3.1.0",
      "resolved": "https://registry.npmjs.org/d3-path/-/d3-path-3.1.0.tgz",
      "integrity": "sha512-p3KP5HCf/bvjBSSKuXid6Zqijx7wIfNW+J/maPs+iwR35at5JCbLUT0LzF1cnjbCHWhqzQTIN2Jpe8pRebIEFQ==",
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-polygon": {
      "version": "3.0.1",
      "resolved": "https://registry.npmjs.org/d3-polygon/-/d3-polygon-3.0.1.tgz",
      "integrity": "sha512-3vbA7vXYwfe1SYhED++fPUQlWSYTTGmFmQiany/gdbiWgU/iEyQzyymwL9SkJjFFuCS4902BSzewVGsHHmHtXg==",
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-quadtree": {
      "version": "3.0.1",
      "resolved": "https://registry.npmjs.org/d3-quadtree/-/d3-quadtree-3.0.1.tgz",
      "integrity": "sha512-04xDrxQTDTCFwP5H6hRhsRcb9xxv2RzkcsygFzmkSIOJy3PeRJP7sNk3VRIbKXcog561P9oU0/rVH6vDROAgUw==",
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-random": {
      "version": "3.0.1",
      "resolved": "https://registry.npmjs.org/d3-random/-/d3-random-3.0.1.tgz",
      "integrity": "sha512-FXMe9GfxTxqd5D6jFsQ+DJ8BJS4E/fT5mqqdjovykEB2oFbTMDVdg1MGFxfQW+FBOGoB++k8swBrgwSHT1cUXQ==",
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-scale": {
      "version": "4.0.2",
      "resolved": "https://registry.npmjs.org/d3-scale/-/d3-scale-4.0.2.tgz",
      "integrity": "sha512-GZW464g1SH7ag3Y7hXjf8RoUuAFIqklOAq3MRl4OaWabTFJY9PN/E1YklhXLh+OQ3fM9yS2nOkCoS+WLZ6kvxQ==",
      "dependencies": {
        "d3-array": "2.10.0 - 3",
        "d3-format": "1 - 3",
        "d3-interpolate": "1.2.0 - 3",
        "d3-time": "2.1.1 - 3",
        "d3-time-format": "2 - 4"
      },
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-scale-chromatic": {
      "version": "3.1.0",
      "resolved": "https://registry.npmjs.org/d3-scale-chromatic/-/d3-scale-chromatic-3.1.0.tgz",
      "integrity": "sha512-A3s5PWiZ9YCXFye1o246KoscMWqf8BsD9eRiJ3He7C9OBaxKhAd5TFCdEx/7VbKtxxTsu//1mMJFrEt572cEyQ==",
      "dependencies": {
        "d3-color": "1 - 3",
        "d3-interpolate": "1 - 3"
      },
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-selection": {
      "version": "3.0.0",
      "resolved": "https://registry.npmjs.org/d3-selection/-/d3-selection-3.0.0.tgz",
      "integrity": "sha512-fmTRWbNMmsmWq6xJV8D19U/gw/bwrHfNXxrIN+HfZgnzqTHp9jOmKMhsTUjXOJnZOdZY9Q28y4yebKzqDKlxlQ==",
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-shape": {
      "version": "3.2.0",
      "resolved": "https://registry.npmjs.org/d3-shape/-/d3-shape-3.2.0.tgz",
      "integrity": "sha512-SaLBuwGm3MOViRq2ABk3eLoxwZELpH6zhl3FbAoJ7Vm1gofKx6El1Ib5z23NUEhF9AsGl7y+dzLe5Cw2AArGTA==",
      "dependencies": {
        "d3-path": "^3.1.0"
      },
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-time": {
      "version": "3.1.0",
      "resolved": "https://registry.npmjs.org/d3-time/-/d3-time-3.1.0.tgz",
      "integrity": "sha512-VqKjzBLejbSMT4IgbmVgDjpkYrNWUYJnbCGo874u7MMKIWsILRX+OpX/gTk8MqjpT1A/c6HY2dCA77ZN0lkQ2Q==",
      "dependencies": {
        "d3-array": "2 - 3"
      },
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-time-format": {
      "version": "4.1.0",
      "resolved": "https://registry.npmjs.org/d3-time-format/-/d3-time-format-4.1.0.tgz",
      "integrity": "sha512-dJxPBlzC7NugB2PDLwo9Q8JiTR3M3e4/XANkreKSUxF8vvXKqm1Yfq4Q5dl8budlunRVlUUaDUgFt7eA8D6NLg==",
      "dependencies": {
        "d3-time": "1 - 3"
      },
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-timer": {
      "version": "3.0.1",
      "resolved": "https://registry.npmjs.org/d3-timer/-/d3-timer-3.0.1.tgz",
      "integrity": "sha512-ndfJ/JxxMd3nw31uyKoY2naivF+r29V+Lc0svZxe1JvvIRmi8hUsrMvdOwgS1o6uBHmiz91geQ0ylPP0aj1VUA==",
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/d3-transition": {
      "version": "3.0.1",
      "resolved": "https://registry.npmjs.org/d3-transition/-/d3-transition-3.0.1.tgz",
      "integrity": "sha512-ApKvfjsSR6tg06xrL434C0WydLr7JewBB3V+/39RMHsaXTOG0zmt/OAXeng5M5LBm0ojmxJrpomQVZ1aPvBL4w==",
      "dependencies": {
        "d3-color": "1 - 3",
        "d3-dispatch": "1 - 3",
        "d3-ease": "1 - 3",
        "d3-interpolate": "1 - 3",
        "d3-timer": "1 - 3"
      },
      "engines": {
        "node": ">=12"
      },
      "peerDependencies": {
        "d3-selection": "2 - 3"
      }
    },
    "node_modules/d3-zoom": {
      "version": "3.0.0",
      "resolved": "https://registry.npmjs.org/d3-zoom/-/d3-zoom-3.0.0.tgz",
      "integrity": "sha512-b8AmV3kfQaqWAuacbPuNbL6vahnOJflOhexLzMMNLga62+/nh0JzvJ0aO/5a5MVgUFGS7Hu1P9P03o3fJkDCyw==",
      "dependencies": {
        "d3-dispatch": "1 - 3",
        "d3-drag": "2 - 3",
        "d3-interpolate": "1 - 3",
        "d3-selection": "2 - 3",
        "d3-transition": "2 - 3"
      },
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/date-fns": {
      "version": "2.30.0",
      "resolved": "https://registry.npmjs.org/date-fns/-/date-fns-2.30.0.tgz",
      "integrity": "sha512-fnULvOpxnC5/Vg3NCiWelDsLiUc9bRwAPs/+LfTLNvetFCtCTN+yQz15C/fs4AwX1R9K5GLtLfn8QW+dWisaAw==",
      "dev": true,
      "dependencies": {
        "@babel/runtime": "^7.21.0"
      },
      "engines": {
        "node": ">=0.11"
      },
      "funding": {
        "type": "opencollective",
        "url": "https://opencollective.com/date-fns"
      }
    },
    "node_modules/delaunator": {
      "version": "5.0.1",
      "resolved": "https://registry.npmjs.org/delaunator/-/delaunator-5.0.1.tgz",
      "integrity": "sha512-8nvh+XBe96aCESrGOqMp/84b13H9cdKbG5P2ejQCh4d4sK9RL4371qou9drQjMhvnPmhWl5hnmqbEE0fXr9Xnw==",
      "dependencies": {
        "robust-predicates": "^3.0.2"
      }
    },
    "node_modules/delayed-stream": {
      "version": "1.0.0",
      "resolved": "https://registry.npmjs.org/delayed-stream/-/delayed-stream-1.0.0.tgz",
      "integrity": "sha512-ZySD7Nf91aLB0RxL4KGrKHBXl7Eds1DAmEdcoVawXnLD7SDhpNgtuII2aAkg7a7QS41jxPSZ17p4VdGnMHk3MQ==",
      "engines": {
        "node": ">=0.4.0"
      }
    },
    "node_modules/emoji-regex": {
      "version": "8.0.0",
      "resolved": "https://registry.npmjs.org/emoji-regex/-/emoji-regex-8.0.0.tgz",
      "integrity": "sha512-MSjYzcWNOA0ewAHpz0MxpYFvwg6yjy1NG3xteoqz644VCo/RPgnr1/GGt+ic3iJTzQ8Eu3TdM14SawnVUmGE6A==",
      "dev": true
    },
    "node_modules/entities": {
      "version": "4.5.0",
      "resolved": "https://registry.npmjs.org/entities/-/entities-4.5.0.tgz",
      "integrity": "sha512-V0hjH4dGPh9Ao5p0MoRY6BVqtwCjhz6vI5LT8AJ55H+4g9/4vbHx1I54fS0XuclLhDHArPQCiMjDxjaL8fPxhw==",
      "engines": {
        "node": ">=0.12"
      },
      "funding": {
        "url": "https://github.com/fb55/entities?sponsor=1"
      }
    },
    "node_modules/esbuild": {
      "version": "0.18.20",
      "resolved": "https://registry.npmjs.org/esbuild/-/esbuild-0.18.20.tgz",
      "integrity": "sha512-ceqxoedUrcayh7Y7ZX6NdbbDzGROiyVBgC4PriJThBKSVPWnnFHZAkfI1lJT8QFkOwH4qOS2SJkS4wvpGl8BpA==",
      "dev": true,
      "hasInstallScript": true,
      "bin": {
        "esbuild": "bin/esbuild"
      },
      "engines": {
        "node": ">=12"
      },
      "optionalDependencies": {
        "@esbuild/android-arm": "0.18.20",
        "@esbuild/android-arm64": "0.18.20",
        "@esbuild/android-x64": "0.18.20",
        "@esbuild/darwin-arm64": "0.18.20",
        "@esbuild/darwin-x64": "0.18.20",
        "@esbuild/freebsd-arm64": "0.18.20",
        "@esbuild/freebsd-x64": "0.18.20",
        "@esbuild/linux-arm": "0.18.20",
        "@esbuild/linux-arm64": "0.18.20",
        "@esbuild/linux-ia32": "0.18.20",
        "@esbuild/linux-loong64": "0.18.20",
        "@esbuild/linux-mips64el": "0.18.20",
        "@esbuild/linux-ppc64": "0.18.20",
        "@esbuild/linux-riscv64": "0.18.20",
        "@esbuild/linux-s390x": "0.18.20",
        "@esbuild/linux-x64": "0.18.20",
        "@esbuild/netbsd-x64": "0.18.20",
        "@esbuild/openbsd-x64": "0.18.20",
        "@esbuild/sunos-x64": "0.18.20",
        "@esbuild/win32-arm64": "0.18.20",
        "@esbuild/win32-ia32": "0.18.20",
        "@esbuild/win32-x64": "0.18.20"
      }
    },
    "node_modules/escalade": {
      "version": "3.2.0",
      "resolved": "https://registry.npmjs.org/escalade/-/escalade-3.2.0.tgz",
      "integrity": "sha512-WUj2qlxaQtO4g6Pq5c29GTcWGDyd8itL8zTlipgECz3JesAiiOKotd8JU6otB3PACgG6xkJUyVhboMS+bje/jA==",
      "dev": true,
      "engines": {
        "node": ">=6"
      }
    },
    "node_modules/estree-walker": {
      "version": "2.0.2",
      "resolved": "https://registry.npmjs.org/estree-walker/-/estree-walker-2.0.2.tgz",
      "integrity": "sha512-Rfkk/Mp/DL7JVje3u18FxFujQlTNR2q6QfMSMB7AvCBx91NGj/ba3kCfza0f6dVDbw7YlRf/nDrn7pQrCCyQ/w=="
    },
    "node_modules/follow-redirects": {
      "version": "1.15.9",
      "resolved": "https://registry.npmjs.org/follow-redirects/-/follow-redirects-1.15.9.tgz",
      "integrity": "sha512-gew4GsXizNgdoRyqmyfMHyAmXsZDk6mHkSxZFCzW9gwlbtOW44CDtYavM+y+72qD/Vq2l550kMF52DT8fOLJqQ==",
      "funding": [
        {
          "type": "individual",
          "url": "https://github.com/sponsors/RubenVerborgh"
        }
      ],
      "engines": {
        "node": ">=4.0"
      },
      "peerDependenciesMeta": {
        "debug": {
          "optional": true
        }
      }
    },
    "node_modules/form-data": {
      "version": "4.0.1",
      "resolved": "https://registry.npmjs.org/form-data/-/form-data-4.0.1.tgz",
      "integrity": "sha512-tzN8e4TX8+kkxGPK8D5u0FNmjPUjw3lwC9lSLxxoB/+GtsJG91CO8bSWy73APlgAZzZbXEYZJuxjkHH2w+Ezhw==",
      "dependencies": {
        "asynckit": "^0.4.0",
        "combined-stream": "^1.0.8",
        "mime-types": "^2.1.12"
      },
      "engines": {
        "node": ">= 6"
      }
    },
    "node_modules/fsevents": {
      "version": "2.3.3",
      "resolved": "https://registry.npmjs.org/fsevents/-/fsevents-2.3.3.tgz",
      "integrity": "sha512-5xoDfX+fL7faATnagmWPpbFtwh/R77WmMMqqHGS65C3vvB0YHrgF+B1YmZ3441tMj5n63k0212XNoJwzlhffQw==",
      "dev": true,
      "hasInstallScript": true,
      "optional": true,
      "os": [
        "darwin"
      ],
      "engines": {
        "node": "^8.16.0 || ^10.6.0 || >=11.0.0"
      }
    },
    "node_modules/get-caller-file": {
      "version": "2.0.5",
      "resolved": "https://registry.npmjs.org/get-caller-file/-/get-caller-file-2.0.5.tgz",
      "integrity": "sha512-DyFP3BM/3YHTQOCUL/w0OZHR0lpKeGrxotcHWcqNEdnltqFwXVfhEBQ94eIo34AfQpo0rGki4cyIiftY06h2Fg==",
      "dev": true,
      "engines": {
        "node": "6.* || 8.* || >= 10.*"
      }
    },
    "node_modules/has-flag": {
      "version": "4.0.0",
      "resolved": "https://registry.npmjs.org/has-flag/-/has-flag-4.0.0.tgz",
      "integrity": "sha512-EykJT/Q1KjTWctppgIAgfSO0tKVuZUjhgMr17kqTumMl6Afv3EISleU7qZUzoXDFTAHTDC4NOoG/ZxU3EvlMPQ==",
      "dev": true,
      "engines": {
        "node": ">=8"
      }
    },
    "node_modules/iconv-lite": {
      "version": "0.6.3",
      "resolved": "https://registry.npmjs.org/iconv-lite/-/iconv-lite-0.6.3.tgz",
      "integrity": "sha512-4fCk79wshMdzMp2rH06qWrJE4iolqLhCUH+OiuIgU++RB0+94NlDL81atO7GX55uUKueo0txHNtvEyI6D7WdMw==",
      "dependencies": {
        "safer-buffer": ">= 2.1.2 < 3.0.0"
      },
      "engines": {
        "node": ">=0.10.0"
      }
    },
    "node_modules/internmap": {
      "version": "2.0.3",
      "resolved": "https://registry.npmjs.org/internmap/-/internmap-2.0.3.tgz",
      "integrity": "sha512-5Hh7Y1wQbvY5ooGgPbDaL5iYLAPzMTUrjMulskHLH6wnv/A+1q5rgEaiuqEjB+oxGXIVZs1FF+R/KPN3ZSQYYg==",
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/is-fullwidth-code-point": {
      "version": "3.0.0",
      "resolved": "https://registry.npmjs.org/is-fullwidth-code-point/-/is-fullwidth-code-point-3.0.0.tgz",
      "integrity": "sha512-zymm5+u+sCsSWyD9qNaejV3DFvhCKclKdizYaJUuHA83RLjb7nSuGnddCHGv0hk+KY7BMAlsWeK4Ueg6EV6XQg==",
      "dev": true,
      "engines": {
        "node": ">=8"
      }
    },
    "node_modules/lodash": {
      "version": "4.17.21",
      "resolved": "https://registry.npmjs.org/lodash/-/lodash-4.17.21.tgz",
      "integrity": "sha512-v2kDEe57lecTulaDIuNTPy3Ry4gLGJ6Z1O3vE1krgXZNrsQ+LFTGHVxVjcXPs17LhbZVGedAJv8XZ1tvj5FvSg==",
      "dev": true
    },
    "node_modules/magic-string": {
      "version": "0.30.17",
      "resolved": "https://registry.npmjs.org/magic-string/-/magic-string-0.30.17.tgz",
      "integrity": "sha512-sNPKHvyjVf7gyjwS4xGTaW/mCnF8wnjtifKBEhxfZ7E/S8tQ0rssrwGNn6q8JH/ohItJfSQp9mBtQYuTlH5QnA==",
      "dependencies": {
        "@jridgewell/sourcemap-codec": "^1.5.0"
      }
    },
    "node_modules/marked": {
      "version": "5.1.2",
      "resolved": "https://registry.npmjs.org/marked/-/marked-5.1.2.tgz",
      "integrity": "sha512-ahRPGXJpjMjwSOlBoTMZAK7ATXkli5qCPxZ21TG44rx1KEo44bii4ekgTDQPNRQ4Kh7JMb9Ub1PVk1NxRSsorg==",
      "bin": {
        "marked": "bin/marked.js"
      },
      "engines": {
        "node": ">= 16"
      }
    },
    "node_modules/mime-db": {
      "version": "1.52.0",
      "resolved": "https://registry.npmjs.org/mime-db/-/mime-db-1.52.0.tgz",
      "integrity": "sha512-sPU4uV7dYlvtWJxwwxHD0PuihVNiE7TyAbQ5SWxDCB9mUYvOgroQOwYQQOKPJ8CIbE+1ETVlOoK1UC2nU3gYvg==",
      "engines": {
        "node": ">= 0.6"
      }
    },
    "node_modules/mime-types": {
      "version": "2.1.35",
      "resolved": "https://registry.npmjs.org/mime-types/-/mime-types-2.1.35.tgz",
      "integrity": "sha512-ZDY+bPm5zTTF+YpCrAU9nK0UgICYPT0QtT1NZWFv4s++TNkcgVaT0g6+4R2uI4MjQjzysHB1zxuWL50hzaeXiw==",
      "dependencies": {
        "mime-db": "1.52.0"
      },
      "engines": {
        "node": ">= 0.6"
      }
    },
    "node_modules/nanoid": {
      "version": "3.3.8",
      "resolved": "https://registry.npmjs.org/nanoid/-/nanoid-3.3.8.tgz",
      "integrity": "sha512-WNLf5Sd8oZxOm+TzppcYk8gVOgP+l58xNy58D0nbUnOxOWRWvlcCV4kUF7ltmI6PsrLl/BgKEyS4mqsGChFN0w==",
      "funding": [
        {
          "type": "github",
          "url": "https://github.com/sponsors/ai"
        }
      ],
      "bin": {
        "nanoid": "bin/nanoid.cjs"
      },
      "engines": {
        "node": "^10 || ^12 || ^13.7 || ^14 || >=15.0.1"
      }
    },
    "node_modules/picocolors": {
      "version": "1.1.1",
      "resolved": "https://registry.npmjs.org/picocolors/-/picocolors-1.1.1.tgz",
      "integrity": "sha512-xceH2snhtb5M9liqDsmEw56le376mTZkEX/jEb/RxNFyegNul7eNslCXP9FDj/Lcu0X8KEyMceP2ntpaHrDEVA=="
    },
    "node_modules/postcss": {
      "version": "8.5.2",
      "resolved": "https://registry.npmjs.org/postcss/-/postcss-8.5.2.tgz",
      "integrity": "sha512-MjOadfU3Ys9KYoX0AdkBlFEF1Vx37uCCeN4ZHnmwm9FfpbsGWMZeBLMmmpY+6Ocqod7mkdZ0DT31OlbsFrLlkA==",
      "funding": [
        {
          "type": "opencollective",
          "url": "https://opencollective.com/postcss/"
        },
        {
          "type": "tidelift",
          "url": "https://tidelift.com/funding/github/npm/postcss"
        },
        {
          "type": "github",
          "url": "https://github.com/sponsors/ai"
        }
      ],
      "dependencies": {
        "nanoid": "^3.3.8",
        "picocolors": "^1.1.1",
        "source-map-js": "^1.2.1"
      },
      "engines": {
        "node": "^10 || ^12 || >=14"
      }
    },
    "node_modules/proxy-from-env": {
      "version": "1.1.0",
      "resolved": "https://registry.npmjs.org/proxy-from-env/-/proxy-from-env-1.1.0.tgz",
      "integrity": "sha512-D+zkORCbA9f1tdWRK0RaCR3GPv50cMxcrz4X8k5LTSUD1Dkw47mKJEZQNunItRTkWwgtaUSo1RVFRIG9ZXiFYg=="
    },
    "node_modules/regenerator-runtime": {
      "version": "0.14.1",
      "resolved": "https://registry.npmjs.org/regenerator-runtime/-/regenerator-runtime-0.14.1.tgz",
      "integrity": "sha512-dYnhHh0nJoMfnkZs6GmmhFknAGRrLznOu5nc9ML+EJxGvrx6H7teuevqVqCuPcPK//3eDrrjQhehXVx9cnkGdw==",
      "dev": true
    },
    "node_modules/require-directory": {
      "version": "2.1.1",
      "resolved": "https://registry.npmjs.org/require-directory/-/require-directory-2.1.1.tgz",
      "integrity": "sha512-fGxEI7+wsG9xrvdjsrlmL22OMTTiHRwAMroiEeMgq8gzoLC/PQr7RsRDSTLUg/bZAZtF+TVIkHc6/4RIKrui+Q==",
      "dev": true,
      "engines": {
        "node": ">=0.10.0"
      }
    },
    "node_modules/robust-predicates": {
      "version": "3.0.2",
      "resolved": "https://registry.npmjs.org/robust-predicates/-/robust-predicates-3.0.2.tgz",
      "integrity": "sha512-IXgzBWvWQwE6PrDI05OvmXUIruQTcoMDzRsOd5CDvHCVLcLHMTSYvOK5Cm46kWqlV3yAbuSpBZdJ5oP5OUoStg=="
    },
    "node_modules/rollup": {
      "version": "3.29.5",
      "resolved": "https://registry.npmjs.org/rollup/-/rollup-3.29.5.tgz",
      "integrity": "sha512-GVsDdsbJzzy4S/v3dqWPJ7EfvZJfCHiDqe80IyrF59LYuP+e6U1LJoUqeuqRbwAWoMNoXivMNeNAOf5E22VA1w==",
      "dev": true,
      "bin": {
        "rollup": "dist/bin/rollup"
      },
      "engines": {
        "node": ">=14.18.0",
        "npm": ">=8.0.0"
      },
      "optionalDependencies": {
        "fsevents": "~2.3.2"
      }
    },
    "node_modules/rw": {
      "version": "1.3.3",
      "resolved": "https://registry.npmjs.org/rw/-/rw-1.3.3.tgz",
      "integrity": "sha512-PdhdWy89SiZogBLaw42zdeqtRJ//zFd2PgQavcICDUgJT5oW10QCRKbJ6bg4r0/UY2M6BWd5tkxuGFRvCkgfHQ=="
    },
    "node_modules/rxjs": {
      "version": "7.8.1",
      "resolved": "https://registry.npmjs.org/rxjs/-/rxjs-7.8.1.tgz",
      "integrity": "sha512-AA3TVj+0A2iuIoQkWEK/tqFjBq2j+6PO6Y0zJcvzLAFhEFIO3HL0vls9hWLncZbAAbK0mar7oZ4V079I/qPMxg==",
      "dev": true,
      "dependencies": {
        "tslib": "^2.1.0"
      }
    },
    "node_modules/safer-buffer": {
      "version": "2.1.2",
      "resolved": "https://registry.npmjs.org/safer-buffer/-/safer-buffer-2.1.2.tgz",
      "integrity": "sha512-YZo3K82SD7Riyi0E1EQPojLz7kpepnSQI9IyPbHHg1XXXevb5dJI7tpyN2ADxGcQbHG7vcyRHk0cbwqcQriUtg=="
    },
    "node_modules/shell-quote": {
      "version": "1.8.2",
      "resolved": "https://registry.npmjs.org/shell-quote/-/shell-quote-1.8.2.tgz",
      "integrity": "sha512-AzqKpGKjrj7EM6rKVQEPpB288oCfnrEIuyoT9cyF4nmGa7V8Zk6f7RRqYisX8X9m+Q7bd632aZW4ky7EhbQztA==",
      "dev": true,
      "engines": {
        "node": ">= 0.4"
      },
      "funding": {
        "url": "https://github.com/sponsors/ljharb"
      }
    },
    "node_modules/source-map-js": {
      "version": "1.2.1",
      "resolved": "https://registry.npmjs.org/source-map-js/-/source-map-js-1.2.1.tgz",
      "integrity": "sha512-UXWMKhLOwVKb728IUtQPXxfYU+usdybtUrK/8uGE8CQMvrhOpwvzDBwj0QhSL7MQc7vIsISBG8VQ8+IDQxpfQA==",
      "engines": {
        "node": ">=0.10.0"
      }
    },
    "node_modules/spawn-command": {
      "version": "0.0.2",
      "resolved": "https://registry.npmjs.org/spawn-command/-/spawn-command-0.0.2.tgz",
      "integrity": "sha512-zC8zGoGkmc8J9ndvml8Xksr1Amk9qBujgbF0JAIWO7kXr43w0h/0GJNM/Vustixu+YE8N/MTrQ7N31FvHUACxQ==",
      "dev": true
    },
    "node_modules/string-width": {
      "version": "4.2.3",
      "resolved": "https://registry.npmjs.org/string-width/-/string-width-4.2.3.tgz",
      "integrity": "sha512-wKyQRQpjJ0sIp62ErSZdGsjMJWsap5oRNihHhu6G7JVO/9jIB6UyevL+tXuOqrng8j/cxKTWyWUwvSTriiZz/g==",
      "dev": true,
      "dependencies": {
        "emoji-regex": "^8.0.0",
        "is-fullwidth-code-point": "^3.0.0",
        "strip-ansi": "^6.0.1"
      },
      "engines": {
        "node": ">=8"
      }
    },
    "node_modules/strip-ansi": {
      "version": "6.0.1",
      "resolved": "https://registry.npmjs.org/strip-ansi/-/strip-ansi-6.0.1.tgz",
      "integrity": "sha512-Y38VPSHcqkFrCpFnQ9vuSXmquuv5oXOKpGeT6aGrr3o3Gc9AlVa6JBfUSOCnbxGGZF+/0ooI7KrPuUSztUdU5A==",
      "dev": true,
      "dependencies": {
        "ansi-regex": "^5.0.1"
      },
      "engines": {
        "node": ">=8"
      }
    },
    "node_modules/supports-color": {
      "version": "8.1.1",
      "resolved": "https://registry.npmjs.org/supports-color/-/supports-color-8.1.1.tgz",
      "integrity": "sha512-MpUEN2OodtUzxvKQl72cUF7RQ5EiHsGvSsVG0ia9c5RbWGL2CI4C7EpPS8UTBIplnlzZiNuV56w+FuNxy3ty2Q==",
      "dev": true,
      "dependencies": {
        "has-flag": "^4.0.0"
      },
      "engines": {
        "node": ">=10"
      },
      "funding": {
        "url": "https://github.com/chalk/supports-color?sponsor=1"
      }
    },
    "node_modules/tree-kill": {
      "version": "1.2.2",
      "resolved": "https://registry.npmjs.org/tree-kill/-/tree-kill-1.2.2.tgz",
      "integrity": "sha512-L0Orpi8qGpRG//Nd+H90vFB+3iHnue1zSSGmNOOCh1GLJ7rUKVwV2HvijphGQS2UmhUZewS9VgvxYIdgr+fG1A==",
      "dev": true,
      "bin": {
        "tree-kill": "cli.js"
      }
    },
    "node_modules/tslib": {
      "version": "2.8.1",
      "resolved": "https://registry.npmjs.org/tslib/-/tslib-2.8.1.tgz",
      "integrity": "sha512-oJFu94HQb+KVduSUQL7wnpmqnfmLsOA/nAh6b6EH0wCEoK0/mPeXU6c3wKDV83MkOuHPRHtSXKKU99IBazS/2w==",
      "dev": true
    },
    "node_modules/vite": {
      "version": "4.5.9",
      "resolved": "https://registry.npmjs.org/vite/-/vite-4.5.9.tgz",
      "integrity": "sha512-qK9W4xjgD3gXbC0NmdNFFnVFLMWSNiR3swj957yutwzzN16xF/E7nmtAyp1rT9hviDroQANjE4HK3H4WqWdFtw==",
      "dev": true,
      "dependencies": {
        "esbuild": "^0.18.10",
        "postcss": "^8.4.27",
        "rollup": "^3.27.1"
      },
      "bin": {
        "vite": "bin/vite.js"
      },
      "engines": {
        "node": "^14.18.0 || >=16.0.0"
      },
      "funding": {
        "url": "https://github.com/vitejs/vite?sponsor=1"
      },
      "optionalDependencies": {
        "fsevents": "~2.3.2"
      },
      "peerDependencies": {
        "@types/node": ">= 14",
        "less": "*",
        "lightningcss": "^1.21.0",
        "sass": "*",
        "stylus": "*",
        "sugarss": "*",
        "terser": "^5.4.0"
      },
      "peerDependenciesMeta": {
        "@types/node": {
          "optional": true
        },
        "less": {
          "optional": true
        },
        "lightningcss": {
          "optional": true
        },
        "sass": {
          "optional": true
        },
        "stylus": {
          "optional": true
        },
        "sugarss": {
          "optional": true
        },
        "terser": {
          "optional": true
        }
      }
    },
    "node_modules/vue": {
      "version": "3.5.13",
      "resolved": "https://registry.npmjs.org/vue/-/vue-3.5.13.tgz",
      "integrity": "sha512-wmeiSMxkZCSc+PM2w2VRsOYAZC8GdipNFRTsLSfodVqI9mbejKeXEGr8SckuLnrQPGe3oJN5c3K0vpoU9q/wCQ==",
      "dependencies": {
        "@vue/compiler-dom": "3.5.13",
        "@vue/compiler-sfc": "3.5.13",
        "@vue/runtime-dom": "3.5.13",
        "@vue/server-renderer": "3.5.13",
        "@vue/shared": "3.5.13"
      },
      "peerDependencies": {
        "typescript": "*"
      },
      "peerDependenciesMeta": {
        "typescript": {
          "optional": true
        }
      }
    },
    "node_modules/wrap-ansi": {
      "version": "7.0.0",
      "resolved": "https://registry.npmjs.org/wrap-ansi/-/wrap-ansi-7.0.0.tgz",
      "integrity": "sha512-YVGIj2kamLSTxw6NsZjoBxfSwsn0ycdesmc4p+Q21c5zPuZ1pl+NfxVdxPtdHvmNVOQ6XSYG4AUtyt/Fi7D16Q==",
      "dev": true,
      "dependencies": {
        "ansi-styles": "^4.0.0",
        "string-width": "^4.1.0",
        "strip-ansi": "^6.0.0"
      },
      "engines": {
        "node": ">=10"
      },
      "funding": {
        "url": "https://github.com/chalk/wrap-ansi?sponsor=1"
      }
    },
    "node_modules/y18n": {
      "version": "5.0.8",
      "resolved": "https://registry.npmjs.org/y18n/-/y18n-5.0.8.tgz",
      "integrity": "sha512-0pfFzegeDWJHJIAmTLRP2DwHjdF5s7jo9tuztdQxAhINCdvS+3nGINqPd00AphqJR/0LhANUS6/+7SCb98YOfA==",
      "dev": true,
      "engines": {
        "node": ">=10"
      }
    },
    "node_modules/yargs": {
      "version": "17.7.2",
      "resolved": "https://registry.npmjs.org/yargs/-/yargs-17.7.2.tgz",
      "integrity": "sha512-7dSzzRQ++CKnNI/krKnYRV7JKKPUXMEh61soaHKg9mrWEhzFWhFnxPxGl+69cD1Ou63C13NUPCnmIcrvqCuM6w==",
      "dev": true,
      "dependencies": {
        "cliui": "^8.0.1",
        "escalade": "^3.1.1",
        "get-caller-file": "^2.0.5",
        "require-directory": "^2.1.1",
        "string-width": "^4.2.3",
        "y18n": "^5.0.5",
        "yargs-parser": "^21.1.1"
      },
      "engines": {
        "node": ">=12"
      }
    },
    "node_modules/yargs-parser": {
      "version": "21.1.1",
      "resolved": "https://registry.npmjs.org/yargs-parser/-/yargs-parser-21.1.1.tgz",
      "integrity": "sha512-tVpsJW7DdjecAiFpbIB1e3qxIQsE6NoPc5/eTdrbbIC4h0LVsWhnoa3g+m2HclBIujHzsxZ4VJVA+GUuc2/LBw==",
      "dev": true,
      "engines": {
        "node": ">=12"
      }
    }
  }
}

</file>

<file path='src/frontend/package.json'>
{
  "name": "local-notes-app",
  "version": "0.1.0",
  "private": true,
  "scripts": {
      "dev": "concurrently \"uvicorn src.backend.main:app --host 127.0.0.1 --port 8000 --reload --app-dir ../..\" \"vite\"",
      "build": "vite build",
      "preview": "vite preview"
  },
  "dependencies": {
      "axios": "^1.3.2",
      "vue": "^3.2.47",
      "marked": "^5.1.0",
      "d3": "^7.8.2"
  },
  "devDependencies": {
      "@vitejs/plugin-vue": "^4.0.0",
      "vite": "^4.0.0",
      "concurrently": "^7.6.0"
  }
}

</file>

<file path='src/frontend/src/App.vue'>
<template>
    <div class="app-container">
        <div class="header-bar">
            <h1>Local Notes App</h1>

            <!-- The view-toggle container still has the same buttons -->
            <div class="view-toggle">
                <button @click="setViewMode('notes')" :class="{ active: viewMode === 'notes' }">
                    Notes View
                </button>
                <button @click="setViewMode('kanban')" :class="{ active: viewMode === 'kanban' }">
                    Kanban Board
                </button>
                <button @click="setViewMode('canvas')" :class="{ active: viewMode === 'canvas' }">
                    Infinite Canvas
                </button>

                <!-- NEW Daily Note button -->
                <button @click="createDailyNote">
                    Daily Note
                </button>
            </div>
        </div>

        <!-- Notes view: File explorer, editor/preview, and task panel -->
        <div class="layout" v-if="viewMode === 'notes'">
            <!-- Left Pane: Note Explorer -->
            <section class="pane side">
                <NoteExplorer 
                    :notes="notesList" 
                    @selectNote="handleNoteSelected"
                    @reloadNotes="fetchNotes"
                />
            </section>

            <!-- Center Pane: Editor + Preview -->
            <section class="pane main">
                <div class="editor-preview-container">
                    <EditorPane
                        v-if="currentNotePath"
                        :currentNoteContent="currentNoteContent"
                        @updateContent="updateNoteContent"
                    />
                    <PreviewPane
                        v-if="currentNoteContent"
                        :markdownText="currentNoteContent"
                    />
                </div>
            </section>

            <!-- Right Pane: Task Panel -->
            <section class="pane side tasks-side">
                <TaskPanel />
            </section>
        </div>

        <!-- Kanban view -->
        <div v-else-if="viewMode === 'kanban'">
            <KanbanBoard />
        </div>

        <!-- Infinite Canvas view -->
        <div v-else-if="viewMode === 'canvas'" class="canvas-view-container">
            <CanvasView />
        </div>
    </div>
</template>

<script>
import axios from 'axios'
import NoteExplorer from './components/NoteExplorer.vue'
import EditorPane from './components/EditorPane.vue'
import PreviewPane from './components/PreviewPane.vue'
import TaskPanel from './components/TaskPanel.vue'
import KanbanBoard from './components/KanbanBoard.vue'
import CanvasView from './components/CanvasView.vue'

/**
 * App.vue
 *
 * The top-level component that manages the main layout.
 * It supports multiple views: Notes view, Kanban board, and Infinite Canvas.
 *
 * NEW: Adds 'createDailyNote()' method to integrate the daily note feature.
 */
export default {
    name: 'App',

    components: {
        NoteExplorer,
        EditorPane,
        PreviewPane,
        TaskPanel,
        KanbanBoard,
        CanvasView
    },

    data() {
        return {
            notesList: [],
            currentNotePath: null,
            currentNoteContent: '',
            viewMode: 'notes'  // 'notes', 'kanban', or 'canvas'
        }
    },

    mounted() {
        this.fetchNotes()
    },

    methods: {
        /**
         * Sets the current view mode ('notes', 'kanban', or 'canvas').
         */
        setViewMode(mode) {
            this.viewMode = mode
        },

        /**
         * Fetches the list of notes from the backend.
         */
        async fetchNotes() {
            try {
                const response = await axios.get('http://localhost:8000/notes')
                this.notesList = response.data.notes || []
            } catch (err) {
                console.error('App.vue: Failed to fetch notes:', err)
            }
        },

        /**
         * Handles the event when a note is selected from the NoteExplorer.
         * @param {String} notePath - The relative path of the selected note.
         */
        handleNoteSelected(notePath) {
            this.currentNotePath = notePath
            this.fetchNoteContent(notePath)
        },

        /**
         * Fetches the content of the selected note from the backend.
         * @param {String} notePath - The relative path of the note.
         */
        async fetchNoteContent(notePath) {
            try {
                const response = await axios.get(`http://localhost:8000/notes/${notePath}`)
                this.currentNoteContent = response.data.content
            } catch (err) {
                console.error('App.vue: Failed to load note content:', err)
            }
        },

        /**
         * Updates the content of the current note by sending a PUT request to the backend.
         * @param {String} newContent - The updated markdown content.
         */
        async updateNoteContent(newContent) {
            if (!this.currentNotePath) {
                return
            }
            try {
                await axios.put(`http://localhost:8000/notes/${this.currentNotePath}`, {
                    content: newContent
                })
                this.currentNoteContent = newContent
            } catch (err) {
                console.error('App.vue: Failed to update note content:', err)
            }
        },

        /**
         * NEW: Creates (or opens) today's daily note by calling the '/notes/daily' endpoint.
         * Upon success, sets the new note path/content and refreshes the notes list.
         */
        async createDailyNote() {
            try {
                // If you want to create a daily note for a custom date, you could do:
                //   const customDateStr = '2025-02-14' // or user input
                //   const response = await axios.post('http://localhost:8000/notes/daily', { date_str: customDateStr })
                // For now, we default to "today" by sending no date_str.
                const response = await axios.post('http://localhost:8000/notes/daily')
                const { note, content } = response.data

                // e.g. note might be "daily/2025-02-14.md"
                this.currentNotePath = note
                this.currentNoteContent = content

                // Reload notes so the new daily note shows up in the explorer.
                this.fetchNotes()

                // Switch to notes view in case the user was on Kanban or Canvas.
                this.viewMode = 'notes'
            } catch (err) {
                console.error('App.vue: Failed to create or open daily note:', err)
            }
        }
    }
}
</script>

<style scoped>
.app-container {
    height: 100vh;
    display: flex;
    flex-direction: column;
    margin: 0;
    font-family: sans-serif;
    box-sizing: border-box;
}

.header-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: #f3f3f3;
    padding: 0.5rem;
    border-bottom: 1px solid #ccc;
}

.view-toggle {
    display: flex;
    gap: 0.5rem;
}

.view-toggle button {
    padding: 0.5rem 1rem;
    cursor: pointer;
}

.view-toggle button.active {
    background-color: #007acc;
    color: #fff;
    border: none;
}

.layout {
    flex: 1;
    display: flex;
    flex-direction: row;
}

.pane {
    border: 1px solid #ccc;
    box-sizing: border-box;
    padding: 0.5rem;
}

.side {
    width: 20%;
    overflow-y: auto;
}

.tasks-side {
    width: 25%;
}

.main {
    flex: 1;
    display: flex;
    flex-direction: column;
}

.editor-preview-container {
    display: flex;
    flex-direction: row;
    height: 100%;
}

.editor-preview-container > * {
    width: 50%;
    padding: 0.5rem;
    box-sizing: border-box;
    border-right: 1px dashed #ccc;
}

.editor-preview-container > *:last-child {
    border-right: none;
}

.canvas-view-container {
    flex: 1;
    padding: 1rem;
}
</style>

</file>

<file path='src/frontend/src/components/CanvasView.vue'>
<!-- src/frontend/src/components/CanvasView.vue -->
<template>
    <div class="canvas-view">
        <h2>Infinite Canvas</h2>
        <!-- Container for D3.js rendered canvas -->
        <div ref="canvasContainer" class="canvas-container"></div>
    </div>
  </template>
  
  <script>
  import * as d3 from 'd3'
  
  /**
   * CanvasView.vue
   *
   * A component that implements an infinite canvas using D3.js.
   * Users can pan and zoom to explore the canvas.
   * Nodes and edges can be added for visual note/task layout.
   */
  export default {
    name: 'CanvasView',
    data() {
        return {
            svg: null,     // D3 selection for the SVG element
            svgGroup: null // D3 group element inside SVG for panning and zooming
        }
    },
    mounted() {
        this.initCanvas()
    },
    methods: {
        /**
         * Initializes the infinite canvas using D3.js.
         * Sets up the SVG element, zoom behavior, and adds sample nodes.
         */
        initCanvas() {
            // Reference to the canvas container DOM element
            const container = this.$refs.canvasContainer
  
            // Create an SVG element that fills the container
            this.svg = d3.select(container)
                .append('svg')
                .attr('width', '100%')
                .attr('height', '100%')
  
            // Append a group element for panning and zooming
            this.svgGroup = this.svg.append('g')
  
            // Define zoom behavior with scale limits
            const zoomBehavior = d3.zoom()
                .scaleExtent([0.5, 5])
                .on('zoom', (event) => {
                    // Apply transformation to the group element
                    this.svgGroup.attr('transform', event.transform)
                })
  
            // Apply the zoom behavior to the SVG element
            this.svg.call(zoomBehavior)
  
            // Add a sample node to demonstrate functionality
            this.addSampleNode(100, 100, 'Sample Node')
        },
  
        /**
         * Adds a sample node to the canvas for demonstration.
         *
         * @param {Number} cx - X-coordinate of the node center.
         * @param {Number} cy - Y-coordinate of the node center.
         * @param {String} label - Label text for the node.
         */
        addSampleNode(cx, cy, label) {
            // Create a group element for the node
            const nodeGroup = this.svgGroup.append('g')
                .attr('class', 'canvas-node')
                .attr('transform', `translate(${cx}, ${cy})`)
  
            // Append a circle to represent the node
            nodeGroup.append('circle')
                .attr('r', 30)
                .attr('fill', 'steelblue')
  
            // Append text to label the node
            nodeGroup.append('text')
                .attr('y', 5)
                .attr('text-anchor', 'middle')
                .attr('fill', '#fff')
                .text(label)
        }
    }
  }
  </script>
  
  <style scoped>
  .canvas-view {
    display: flex;
    flex-direction: column;
    height: 100%;
  }
  
  .canvas-container {
    flex: 1;
    border: 1px solid #ccc;
    overflow: hidden;
    position: relative;
  }
  </style>
  
</file>

<file path='src/frontend/src/components/EditorPane.vue'>
<template>
    <div class="editor-pane">
      <h3>Editor</h3>
      <textarea
        v-model="editorContent"
        class="editor-textarea"
        @input="onContentChange"
      />
    </div>
  </template>
  
  <script>
  export default {
    name: 'EditorPane',
    props: {
      currentNoteContent: {
        type: String,
        default: ''
      }
    },
    data() {
      return {
        editorContent: this.currentNoteContent
      }
    },
    watch: {
      // If the prop changes externally (e.g. when selecting a different note),
      // sync it back to the local data
      currentNoteContent(newVal) {
        this.editorContent = newVal
      }
    },
    methods: {
      onContentChange() {
        // Emit event to update note content in the parent
        this.$emit('updateContent', this.editorContent)
      }
    }
  }
  </script>
  
  <style scoped>
  .editor-pane {
    display: flex;
    flex-direction: column;
    height: 100%;
  }
  
  .editor-textarea {
    flex: 1;
    resize: none;
    width: 100%;
    height: calc(100% - 2rem);
    font-family: monospace;
    font-size: 14px;
    padding: 8px;
    box-sizing: border-box;
  }
  </style>
  
</file>

<file path='src/frontend/src/components/KanbanBoard.vue'>
<template>
    <div class="kanban-container">
        <h2>Kanban Board</h2>
        <p class="kanban-instructions">
            Drag and drop tasks between columns to update their status.
        </p>

        <div class="columns">
            <!-- TODO Column -->
            <div class="column" @drop.prevent="onDrop('TODO')" @dragover.prevent>
                <h3>TODO</h3>
                <div
                    v-for="task in todoTasks"
                    :key="task.id"
                    class="task-card"
                    :draggable="true"
                    @dragstart="onDragStart(task)"
                >
                    <strong>{{ task.title }}</strong>
                    <p v-if="task.description">{{ task.description }}</p>
                    <small v-if="task.due_date">
                        Due: {{ formatDate(task.due_date) }}
                    </small>
                    <small>
                        Priority: {{ formatPriority(task.priority) }}
                    </small>
                    <small v-if="task.recurrence">
                        Recurrence: {{ task.recurrence }}
                    </small>
                    <small>Status: {{ task.status }}</small>
                </div>
            </div>

            <!-- In Progress Column -->
            <div class="column" @drop.prevent="onDrop('IN_PROGRESS')" @dragover.prevent>
                <h3>In Progress</h3>
                <div
                    v-for="task in inProgressTasks"
                    :key="task.id"
                    class="task-card"
                    :draggable="true"
                    @dragstart="onDragStart(task)"
                >
                    <strong>{{ task.title }}</strong>
                    <p v-if="task.description">{{ task.description }}</p>
                    <small v-if="task.due_date">
                        Due: {{ formatDate(task.due_date) }}
                    </small>
                    <small>
                        Priority: {{ formatPriority(task.priority) }}
                    </small>
                    <small v-if="task.recurrence">
                        Recurrence: {{ task.recurrence }}
                    </small>
                    <small>Status: {{ task.status }}</small>
                </div>
            </div>

            <!-- Completed Column -->
            <div class="column" @drop.prevent="onDrop('COMPLETED')" @dragover.prevent>
                <h3>Completed</h3>
                <div
                    v-for="task in completedTasks"
                    :key="task.id"
                    class="task-card"
                    :draggable="true"
                    @dragstart="onDragStart(task)"
                >
                    <strong>{{ task.title }}</strong>
                    <p v-if="task.description">{{ task.description }}</p>
                    <small v-if="task.due_date">
                        Due: {{ formatDate(task.due_date) }}
                    </small>
                    <small>
                        Priority: {{ formatPriority(task.priority) }}
                    </small>
                    <small v-if="task.recurrence">
                        Recurrence: {{ task.recurrence }}
                    </small>
                    <small>Status: {{ task.status }}</small>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import axios from 'axios'

/**
 * KanbanBoard.vue
 *
 * This component implements a Kanban board for task management.
 * Tasks are grouped by their status (TODO, IN_PROGRESS, COMPLETED) and can be
 * dragged between columns to update their status. Additional task metadata
 * (due date, priority, recurrence) is also displayed.
 */
export default {
    name: 'KanbanBoard',
    data() {
        return {
            tasks: [],        // Array to store all tasks from the backend
            draggedTask: null // Currently dragged task object
        }
    },
    computed: {
        /**
         * Returns tasks with status 'TODO'.
         */
        todoTasks() {
            return this.tasks.filter(task => task.status === 'TODO')
        },
        /**
         * Returns tasks with status 'IN_PROGRESS'.
         */
        inProgressTasks() {
            return this.tasks.filter(task => task.status === 'IN_PROGRESS')
        },
        /**
         * Returns tasks with status 'COMPLETED'.
         */
        completedTasks() {
            return this.tasks.filter(task => task.status === 'COMPLETED')
        }
    },
    mounted() {
        // Fetch tasks when component is mounted.
        this.fetchTasks()
    },
    methods: {
        /**
         * Fetch tasks from the backend and update local tasks array.
         */
        async fetchTasks() {
            try {
                const response = await axios.get('http://localhost:8000/tasks')
                this.tasks = response.data
            } catch (error) {
                console.error('KanbanBoard: Failed to fetch tasks:', error)
            }
        },

        /**
         * Handler for dragstart event.
         * Sets the current dragged task.
         *
         * @param {Object} task - The task object that is being dragged.
         */
        onDragStart(task) {
            this.draggedTask = task
        },

        /**
         * Handler for drop event on a column.
         * Updates the dragged task's status based on the column dropped into.
         *
         * @param {String} newStatus - The status representing the target column.
         */
        async onDrop(newStatus) {
            if (!this.draggedTask) {
                return
            }
            if (this.draggedTask.status === newStatus) {
                this.draggedTask = null
                return
            }
            try {
                // For recurring tasks, use the complete endpoint if moving to COMPLETED.
                if (this.draggedTask.recurrence && this.draggedTask.due_date) {
                    if (newStatus === 'COMPLETED') {
                        await axios.post(
                            `http://localhost:8000/tasks/${this.draggedTask.id}/complete`
                        )
                    } else {
                        await axios.put(
                            `http://localhost:8000/tasks/${this.draggedTask.id}`,
                            { status: newStatus }
                        )
                    }
                } else {
                    await axios.put(
                        `http://localhost:8000/tasks/${this.draggedTask.id}`,
                        { status: newStatus }
                    )
                }
                // Refresh tasks after updating.
                this.fetchTasks()
            } catch (error) {
                console.error('KanbanBoard: Error updating task status:', error)
            }
            this.draggedTask = null
        },

        /**
         * Formats a date string into a locale-specific date.
         *
         * @param {String} dateStr - The date string.
         * @returns {String} Formatted date.
         */
        formatDate(dateStr) {
            const date = new Date(dateStr)
            return date.toLocaleDateString()
        },

        /**
         * Converts numeric priority to a human-readable string.
         *
         * @param {Number} priority - The task priority.
         * @returns {String} The formatted priority string.
         */
        formatPriority(priority) {
            switch (priority) {
                case 1:
                    return 'High'
                case 2:
                    return 'Medium'
                case 3:
                    return 'Low'
                default:
                    return priority
            }
        }
    }
}
</script>

<style scoped>
.kanban-container {
    display: flex;
    flex-direction: column;
    padding: 1rem;
    height: 100%;
    box-sizing: border-box;
    font-family: sans-serif;
}

.kanban-instructions {
    font-size: 0.9rem;
    color: #666;
    margin-bottom: 1rem;
}

.columns {
    display: flex;
    gap: 1rem;
    flex: 1;
}

.column {
    flex: 1;
    border: 1px solid #ccc;
    min-height: 300px;
    padding: 0.5rem;
    box-sizing: border-box;
    background-color: #fafafa;
}

.task-card {
    background: #fff;
    margin-bottom: 0.5rem;
    padding: 0.5rem;
    border: 1px solid #ddd;
    cursor: grab;
}

.task-card:active {
    cursor: grabbing;
}
</style>

</file>

<file path='src/frontend/src/components/NoteExplorer.vue'>
<template>
  <div class="note-explorer">
    <h2>Notes</h2>

    <div class="notes-list">
      <ul>
        <li
          v-for="(note, idx) in notes"
          :key="idx"
          @click="select(note)"
          class="note-item"
        >
          {{ note }}
        </li>
      </ul>
    </div>
    <div class="actions">
      <input
        v-model="newNoteName"
        placeholder="New note name..."
        @keydown.enter="createNote"
      />
      <button @click="createNote">Create Note</button>
      <button @click="reloadNotes">Reload</button>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'NoteExplorer',
  props: {
    notes: {
      type: Array,
      required: true
    }
  },
  data() {
    return {
      newNoteName: ''
    }
  },
  methods: {
    select(notePath) {
      // Notify parent that a note was selected
      this.$emit('selectNote', notePath)
    },
    createNote() {
      if (!this.newNoteName) return
      axios.post('http://localhost:8000/notes', {
        note_name: this.newNoteName
      })
      .then(() => {
        this.newNoteName = ''
        // Refresh the parent’s note list
        this.$emit('reloadNotes')
      })
      .catch(err => {
        console.error('Failed to create note:', err)
      })
    },
    reloadNotes() {
      this.$emit('reloadNotes')
    }
  }
}
</script>

<style scoped>
.note-explorer {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.notes-list {
  flex: 1;
  overflow-y: auto;
}

.note-item {
  cursor: pointer;
  padding: 4px;
  border-bottom: 1px solid #eee;
}

.note-item:hover {
  background: #fafafa;
}

.actions {
  margin-top: 0.5rem;
}

.actions input {
  width: 60%;
  padding: 4px;
  margin-right: 0.5rem;
}
</style>

</file>

<file path='src/frontend/src/components/PreviewPane.vue'>
<template>
    <div class="preview-pane">
      <h3>Preview</h3>
      <div
        class="preview-content"
        v-html="renderedMarkdown"
      />
    </div>
  </template>
  
  <script>
  import { marked } from 'marked'
  
  export default {
    name: 'PreviewPane',
    props: {
      markdownText: {
        type: String,
        default: ''
      }
    },
    computed: {
      renderedMarkdown() {
        // Use 'marked' to convert the raw markdown text into HTML
        return marked(this.markdownText || '')
      }
    }
  }
  </script>
  
  <style scoped>
  .preview-pane {
    display: flex;
    flex-direction: column;
    height: 100%;
  }
  
  .preview-content {
    flex: 1;
    overflow-y: auto;
    padding: 0.5rem;
    background: #f9f9f9;
    border: 1px solid #ddd;
  }
  </style>
  
</file>

<file path='src/frontend/src/components/TaskPanel.vue'>
<template>
  <div class="task-panel">
      <h2>Tasks</h2>
      <!-- Task creation form with extended fields -->
      <div class="task-form">
          <input
              v-model="newTaskTitle"
              placeholder="New task title..."
          />
          <input
              v-model="newTaskDescription"
              placeholder="Description"
          />
          <input
              type="date"
              v-model="newTaskDueDate"
              placeholder="Due Date"
          />
          <select v-model="newTaskPriority">
              <option value="1">High</option>
              <option value="2">Medium</option>
              <option value="3">Low</option>
          </select>
          <input
              v-model="newTaskRecurrence"
              placeholder="Recurrence (daily, weekly, monthly)"
          />
          <button @click="createTask">Add Task</button>
          <button @click="fetchTasks">Reload</button>
      </div>

      <!-- Task list display -->
      <div class="task-list">
          <div
              v-for="task in tasks"
              :key="task.id"
              class="task-item"
          >
              <label>
                  <input
                      type="checkbox"
                      :checked="task.status === 'COMPLETED'"
                      @change="handleComplete(task)"
                  />
                  <strong>{{ task.title }}</strong>
              </label>
              <p v-if="task.description">{{ task.description }}</p>
              <small v-if="task.due_date">
                  Due: {{ formatDate(task.due_date) }}
              </small>
              <small>
                  Priority: {{ formatPriority(task.priority) }}
              </small>
              <small v-if="task.recurrence">
                  Recurrence: {{ task.recurrence }}
              </small>
              <small>Status: {{ task.status }}</small>
          </div>
      </div>
  </div>
</template>

<script>
import axios from 'axios'

/**
* TaskPanel.vue
*
* This component displays a panel for managing tasks.
* It allows users to create new tasks with extended fields (description,
* due date, priority, recurrence) and displays the list of tasks.
* It also handles marking tasks complete using the appropriate backend endpoint.
*/
export default {
  name: 'TaskPanel',
  data() {
      return {
          tasks: [],                // Array holding all tasks from the backend
          newTaskTitle: '',         // Title for new task
          newTaskDescription: '',   // Description for new task
          newTaskDueDate: '',       // Due date (as a string) for new task
          newTaskPriority: '2',     // Default priority (2 = Medium)
          newTaskRecurrence: ''     // Recurrence rule (if any)
      }
  },
  mounted() {
      // Fetch tasks once the component is mounted
      this.fetchTasks()
  },
  methods: {
      /**
       * Fetch all tasks from the backend.
       */
      async fetchTasks() {
          try {
              const response = await axios.get('http://localhost:8000/tasks')
              this.tasks = response.data
          } catch (error) {
              console.error('TaskPanel: Failed to fetch tasks:', error)
          }
      },

      /**
       * Create a new task with the given details.
       * Converts the due date to a Date object if provided.
       */
      async createTask() {
          if (!this.newTaskTitle) {
              return
          }
          try {
              const payload = {
                  title: this.newTaskTitle,
                  description: this.newTaskDescription,
                  due_date: this.newTaskDueDate
                      ? new Date(this.newTaskDueDate)
                      : null,
                  priority: parseInt(this.newTaskPriority),
                  recurrence: this.newTaskRecurrence || null
              }
              await axios.post('http://localhost:8000/tasks', payload)
              // Reset form fields
              this.newTaskTitle = ''
              this.newTaskDescription = ''
              this.newTaskDueDate = ''
              this.newTaskPriority = '2'
              this.newTaskRecurrence = ''
              // Refresh the task list
              this.fetchTasks()
          } catch (error) {
              console.error('TaskPanel: Failed to create task:', error)
          }
      },

      /**
       * Handle the task completion toggle.
       * If the task has a recurrence rule and a due date, call the complete endpoint.
       * Otherwise, simply update the status.
       *
       * @param {Object} task - The task object to update.
       */
      async handleComplete(task) {
          try {
              if (task.recurrence && task.due_date) {
                  // For recurring tasks, use the dedicated complete endpoint.
                  await axios.post(`http://localhost:8000/tasks/${task.id}/complete`)
              } else {
                  // Toggle the status between TODO and COMPLETED.
                  if (task.status !== 'COMPLETED') {
                      await axios.put(`http://localhost:8000/tasks/${task.id}`, {
                          status: 'COMPLETED'
                      })
                  } else {
                      await axios.put(`http://localhost:8000/tasks/${task.id}`, {
                          status: 'TODO'
                      })
                  }
              }
              // Refresh tasks after update.
              this.fetchTasks()
          } catch (error) {
              console.error('TaskPanel: Failed to update task status:', error)
          }
      },

      /**
       * Format a date string into a locale-specific date.
       *
       * @param {String} dateStr - The date string.
       * @returns {String} Formatted date.
       */
      formatDate(dateStr) {
          const date = new Date(dateStr)
          return date.toLocaleDateString()
      },

      /**
       * Format the numeric priority into a human-readable string.
       *
       * @param {Number} priority - The priority value.
       * @returns {String} Formatted priority.
       */
      formatPriority(priority) {
          switch (priority) {
              case 1:
                  return 'High'
              case 2:
                  return 'Medium'
              case 3:
                  return 'Low'
              default:
                  return priority
          }
      }
  }
}
</script>

<style scoped>
.task-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  font-family: sans-serif;
  padding: 0.5rem;
  box-sizing: border-box;
}

.task-form {
  margin-bottom: 1rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.task-form input,
.task-form select {
  padding: 4px;
  font-size: 0.9rem;
}

.task-form button {
  padding: 4px 8px;
  cursor: pointer;
}

.task-list {
  flex: 1;
  overflow-y: auto;
}

.task-item {
  border-bottom: 1px solid #eee;
  padding: 0.5rem 0;
}
</style>

</file>

<file path='src/frontend/src/main.js'>
/**
 * main.js
 *
 * The main entry point for the Vue app. Creates the Vue application,
 * mounts it to #app in index.html, and configures global dependencies.
 */

import { createApp } from 'vue'
import App from './App.vue'

// Create the app instance
const app = createApp(App)

// Mount it to <div id="app"> in index.html
app.mount('#app')
</file>

<file path='src/frontend/storage/vault/2.md'>
# hello


</file>

<file path='src/frontend/storage/vault/test note 1.md'>
# bye
## 2

</file>

<file path='src/frontend/vite.config.js'>
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    // Optional: The proxy ensures requests to "/notes", "/tasks", etc. go to http://127.0.0.1:8000
    proxy: {
      '/notes': 'http://127.0.0.1:8000',
      '/tasks': 'http://127.0.0.1:8000',
      '/backup': 'http://127.0.0.1:8000',
      '/search': 'http://127.0.0.1:8000'
    }
  }
})
</file>

<file path='storage/vault/Test note 1.md'>

# Tile
## Sub-title
Here I am testing this app I built!
</file>

"""
<goal>
IMPLEMENT TipTap Editor to replace the split editor by a single unified WUSIWYG editor

</goal>


<output instruction>
1) Explain 
2) Give me the COMPLETE UPDATED VERSION of each script that needs to be updated
</output instruction>
"""
