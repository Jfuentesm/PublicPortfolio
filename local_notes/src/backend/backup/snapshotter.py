# src/backend/backup/snapshotter.py
"""
snapshotter.py

Implements a simple snapshot mechanism for creating periodic backups of the vault.
This module can be integrated with a scheduler to run every 5 minutes.
"""

import shutil
from pathlib import Path
from datetime import datetime

# Import Config for centralized configuration values.
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
