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
