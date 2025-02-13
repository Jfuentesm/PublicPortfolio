# src/backend/search/routes.py
"""
routes.py

Defines FastAPI endpoints for search functionality.
Provides an endpoint to search through Markdown notes.
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List

from .indexer import search_notes, build_index

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
    Search for notes matching the provided query.

    Args:
        query (str): The search query string.

    Returns:
        JSONResponse: A list of note paths that match the query.
    """
    try:
        results = search_notes(query)
        return JSONResponse(content={"results": results})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
