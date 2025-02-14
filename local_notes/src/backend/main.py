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
