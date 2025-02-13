'''
Included Files:
- requirements.txt
- script_concatenator.py
- src/backend/config.py
- src/backend/database/base.py
- src/backend/database/init_db.py
- src/backend/database/sessions.py
- src/backend/file_handler.py
- src/backend/main.py
- src/backend/tasks/models.py
- src/backend/tasks/recurrence.py
- src/backend/tasks/routes.py

'''

# Concatenated Source Code

<file path='requirements.txt'>
SQLAlchemy
fastapi
pydantic
uvicorn
</file>

<file path='script_concatenator.py'>
"""Generate a single file containing the concatenated files from backlog_generation folder."""

import os
from pathlib import Path
from datetime import datetime

def read_file_content(file_path):
    """Read and return the content of a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading {file_path}: {str(e)}"

def get_files_recursively(directory):
    """Recursively get all files in directory, excluding .venv folder and directories."""
    files = []
    for item in sorted(directory.iterdir()):
        # Skip .venv folder and hidden files
        if item.name == '.venv' or item.name.startswith('.'):
            continue
        
        if item.is_file():
            # Only include python files and text files
            if item.suffix in ['.py', '.txt', '.md']:
                files.append(item)
        elif item.is_dir():
            # Recursively get files from subdirectories
            files.extend(get_files_recursively(item))
    return files

def main():
    # Define paths
    root_dir = Path(__file__).parent
    backlog_generation_dir = root_dir 

    # Gather all files recursively, excluding .venv
    files_to_include = get_files_recursively(backlog_generation_dir)

    # Create a timestamp string in the format YYYYMMDD_HHMMSS
    timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Construct the output file name (foldersincluded_datetimestamp.py)
    output_file_name = f"{backlog_generation_dir.name}_{timestamp_str}.py"
    output_file = root_dir / output_file_name

    with open(output_file, 'w', encoding='utf-8') as f:
        # Write file tree section
        f.write("'''\nIncluded Files:\n")
        for file_path in files_to_include:
            rel_path = file_path.relative_to(root_dir)
            f.write(f"- {rel_path}\n")
        f.write("\n'''\n\n")

        # Write concatenated source code section
        f.write("# Concatenated Source Code\n\n")

        # Process files
        for file_path in files_to_include:
            rel_path = file_path.relative_to(root_dir)

            # Skip the output file itself if it exists
            if file_path.name == output_file_name:
                continue

            # Write file header
            f.write(f"<file path='{rel_path}'>\n")

            # Write file content
            content = read_file_content(file_path)
            f.write(content)

            # Write file footer
            f.write("\n</file>\n\n")

        # Add error and output instruction template
        f.write('"""\n')
        f.write('<goal>\n\n\n')
        f.write('</goal>\n\n\n')
        f.write('<output instruction>\n')
        f.write('1) Explain \n')
        f.write('2) Give me the COMPLETE UPDATED VERSION of each script that needs to be updated\n')
        f.write('</output instruction>\n')
        f.write('"""\n')

if __name__ == "__main__":
    main()
</file>

<file path='src/backend/config.py'>
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
</file>

<file path='src/backend/database/sessions.py'>
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
from config import Config  # Import configuration constants

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

from config import Config  # Import centralized configuration settings


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
# src/backend/main.py
"""
main.py

The entry point for the local note-taking and task management application backend.
This module sets up the FastAPI application, integrates note operations and task endpoints,
and starts the local development server.
"""

from fastapi import FastAPI, HTTPException, Path, Body
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config import Config  # Import configuration constants
from file_handler import NoteManager  # For Markdown note operations

# Import the tasks router (Wave 2 integration)
from tasks.routes import router as tasks_router

# Initialize the FastAPI application.
app = FastAPI(
    title="Local Note-Taking & Task Management App",
    version="0.2.0",
    description="A local, file-based note-taking and task management application inspired by Obsidian."
)

# Configure CORS to allow requests from all origins during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Initialize the NoteManager for note file operations.
note_manager = NoteManager()

# Include the tasks router to add task management endpoints.
app.include_router(tasks_router)

# --- Note Endpoints (Wave 1 functionality) ---


@app.get("/notes", summary="List all notes")
async def list_notes() -> JSONResponse:
    """
    Retrieve a list of all Markdown notes in the vault.

    Returns:
        JSONResponse: A JSON response containing a list of note file paths.
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

    Args:
        note_path (str): The relative path to the note file.

    Returns:
        JSONResponse: A JSON response containing the note's name and content.

    Raises:
        HTTPException: If the note is not found.
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

    Args:
        note_name (str): The desired name for the note.
        content (str): Optional initial content for the note.

    Returns:
        JSONResponse: A JSON response confirming note creation and providing the note path.

    Raises:
        HTTPException: If a note with the same name already exists.
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

    Args:
        note_path (str): The relative path to the note file.
        content (str): The new content to be written to the note.

    Returns:
        JSONResponse: A JSON response confirming the note update.

    Raises:
        HTTPException: If the note is not found.
    """
    try:
        # Verify that the note exists before updating.
        _ = note_manager.read_note(note_path)
        note_manager.write_note(note_path, content)
        return JSONResponse(content={"message": "Note updated", "note": note_path})
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Note not found")
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


# --- End Note Endpoints ---

if __name__ == "__main__":
    uvicorn.run("main:app", host=Config.HOST, port=Config.PORT, reload=True)

</file>

<file path='src/backend/tasks/models.py'>
"""
models.py

Defines the SQLAlchemy model for task management.
This module includes the Task model and the TaskStatus enumeration.
"""

import datetime
import enum
from sqlalchemy import Column, Integer, String, DateTime, Enum
from database.base import Base  # Shared SQLAlchemy declarative base


class TaskStatus(enum.Enum):
    """
    Enumeration for task status values.
    """
    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"


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
Provides endpoints to create, read, update, and delete tasks.
Utilizes Pydantic models for request validation.
"""

import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.sessions import SessionLocal  # Updated import: use "sessions" (plural)
from tasks.models import Task, TaskStatus
from tasks.recurrence import get_next_due_date

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    responses={404: {"description": "Not found"}}
)


def get_db() -> Session:
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
        orm_mode = True


@router.post("/", response_model=TaskResponse, summary="Create a new task")
def create_task(task: TaskCreate, db: Session = Depends(get_db)) -> Task:
    """
    Create a new task with the provided details.
    
    Args:
        task (TaskCreate): Task data from the request body.
        db (Session): Database session dependency.
    
    Returns:
        Task: The created task.
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
    Retrieve a list of all tasks.
    
    Args:
        db (Session): Database session dependency.
    
    Returns:
        List[Task]: List of tasks.
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
        task_id (int): The ID of the task.
        db (Session): Database session dependency.
    
    Returns:
        Task: The requested task.
    
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
    Update an existing task.
    
    Args:
        task_id (int): The ID of the task to update.
        task_update (TaskUpdate): Updated task data.
        db (Session): Database session dependency.
    
    Returns:
        Task: The updated task.
    
    Raises:
        HTTPException: If the task is not found.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    update_data = task_update.dict(exclude_unset=True)
    
    # If a new due date is provided along with an existing recurrence rule,
    # compute the next due date based on the recurrence rule.
    if "due_date" in update_data and task.recurrence and update_data.get("due_date"):
        update_data["due_date"] = get_next_due_date(update_data["due_date"], task.recurrence)
    
    for key, value in update_data.items():
        setattr(task, key, value)
    
    db.commit()
    db.refresh(task)
    return task


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
        dict: A message confirming deletion.
    
    Raises:
        HTTPException: If the task is not found.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return {"message": "Task deleted successfully"}
</file>

"""
<goal>


</goal>


<output instruction>
1) Explain 
2) Give me the COMPLETE UPDATED VERSION of each script that needs to be updated
</output instruction>
"""
