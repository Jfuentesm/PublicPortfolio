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
