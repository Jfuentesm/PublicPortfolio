# src/backend/main.py
"""
main.py

The entry point for the local note-taking and task management application backend.
This module sets up the FastAPI application, integrates note operations, task endpoints,
canvas operations, search functionality, and backup/versioning endpoints, and starts
the local development server.
"""

from fastapi import FastAPI, HTTPException, Path, Body
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config import Config
from file_handler import NoteManager

# Import task routes (Wave 2)
from tasks.routes import router as tasks_router
# Import canvas routes (Wave 3)
from canvas.routes import router as canvas_router
# Import search routes (Wave 3)
from search.routes import router as search_router
# Import backup routes (Wave 3)
from backup.routes import router as backup_router

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

# Include routers for tasks, canvas, search, and backup
app.include_router(tasks_router)
app.include_router(canvas_router)
app.include_router(search_router)
app.include_router(backup_router)


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


if __name__ == "__main__":
    uvicorn.run("main:app", host=Config.HOST, port=Config.PORT, reload=True)
