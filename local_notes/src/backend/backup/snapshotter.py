# src/backend/backup/snapshotter.py
"""
snapshotter.py

Implements a simple snapshot mechanism for creating periodic backups of the vault.
This can be integrated with a scheduler to run every 5 minutes.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

# Directory for storing snapshots
SNAPSHOT_DIR = Path(os.getcwd(), "storage", "backups", "snapshots")
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)


def create_snapshot() -> None:
    """
    Create a snapshot backup of the entire vault.
    The snapshot is a copy of the vault directory stored with a timestamp.
    """
    from config import Config
    vault_path = Path(Config.VAULT_DIR)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot_path = SNAPSHOT_DIR / f"vault_snapshot_{timestamp}"
    shutil.copytree(vault_path, snapshot_path)
