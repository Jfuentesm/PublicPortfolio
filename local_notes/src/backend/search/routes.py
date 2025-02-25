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
