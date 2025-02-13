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
