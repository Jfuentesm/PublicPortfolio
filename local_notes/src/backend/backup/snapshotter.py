#!/usr/bin/env python3
# snapshotter.py
"""
snapshotter.py

Implements a simple snapshot mechanism for creating periodic backups of the vault.
This module can be integrated with a scheduler (or background thread) to run every
N minutes, as configured in config.py.

Example usage from another module:
    from src.backend.backup.snapshotter import create_snapshot
    create_snapshot()
"""

import shutil
from pathlib import Path
from datetime import datetime

from src.backend.config import Config

# Use the backup directory defined in the configuration and create a "snapshots" subfolder.
SNAPSHOT_DIR = Config.BACKUP_DIR / "snapshots"
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

def create_snapshot() -> None:
    """
    Create a snapshot backup of the entire vault.
    
    The snapshot is a copy of the vault directory stored with a timestamp.
    """
    vault_path = Path(Config.VAULT_DIR)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot_path = SNAPSHOT_DIR / f"vault_snapshot_{timestamp}"
    shutil.copytree(vault_path, snapshot_path)
