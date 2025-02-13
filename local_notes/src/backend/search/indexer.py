# src/backend/search/indexer.py
"""
indexer.py

Provides full-text indexing functionality for Markdown notes using Whoosh.
Builds and maintains a search index for fast querying of note content.
"""

import os
from pathlib import Path
from whoosh import index
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import QueryParser

from config import Config
from file_handler import NoteManager

# Define index directory
INDEX_DIR = Path(os.getcwd(), "storage", "search_index")
INDEX_DIR.mkdir(parents=True, exist_ok=True)


def get_schema():
    """
    Define and return the Whoosh schema for indexing notes.
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
    # Iterate through all notes and add them to the index
    for note_path in note_manager.list_notes():
        try:
            content = note_manager.read_note(note_path)
            writer.update_document(path=note_path, content=content)
        except Exception as e:
            # Log error if needed
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
