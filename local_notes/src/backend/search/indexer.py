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
