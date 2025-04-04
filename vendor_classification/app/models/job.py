# <file path='app/models/job.py'>
# --- file path='app/models/job.py' ---
from sqlalchemy import Column, String, Float, DateTime, Enum as SQLEnum, JSON, Text # Renamed Enum import
from sqlalchemy.sql import func
from sqlalchemy.orm import Session # <<< ADDED IMPORT FOR TYPE HINTING
from enum import Enum as PyEnum
from datetime import datetime
from typing import Optional, Dict, Any

from core.database import Base

class JobStatus(str, PyEnum):
    """Job status enum."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ProcessingStage(str, PyEnum):
    """Processing stage enum."""
    INGESTION = "ingestion"
    NORMALIZATION = "normalization"
    CLASSIFICATION_L1 = "classification_level_1"
    CLASSIFICATION_L2 = "classification_level_2"
    CLASSIFICATION_L3 = "classification_level_3"
    CLASSIFICATION_L4 = "classification_level_4"
    # --- ADDED: Level 5 ---
    CLASSIFICATION_L5 = "classification_level_5"
    # --- END ADDED ---
    SEARCH = "search_unknown_vendors" # This stage now covers search AND recursive post-search classification
    RESULT_GENERATION = "result_generation"

class Job(Base):
    """Job model for tracking classification jobs."""

    __tablename__ = "jobs"

    id = Column(String, primary_key=True, index=True)
    company_name = Column(String, nullable=False)
    input_file_name = Column(String, nullable=False)
    output_file_name = Column(String, nullable=True)
    status = Column(String, default=JobStatus.PENDING.value)
    current_stage = Column(String, default=ProcessingStage.INGESTION.value)
    progress = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    notification_email = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    stats = Column(JSON, default={}) # Structure defined by ProcessingStats model
    created_by = Column(String, nullable=False)

    def update_progress(self, progress: float, stage: ProcessingStage, db_session: Optional[Session] = None): # Type hint now valid
        """Update job progress and stage, optionally committing."""
        self.progress = progress
        self.current_stage = stage.value
        self.updated_at = datetime.now()
        # Optionally commit immediately if session provided
        if db_session:
            try:
                db_session.commit()
            except Exception as e:
                from core.logging_config import get_logger # Local import for safety
                logger = get_logger("vendor_classification.job_model")
                logger.error(f"Failed to commit progress update for job {self.id}", exc_info=True)
                db_session.rollback()


    def complete(self, output_file_name: str, stats: Dict[str, Any]):
        """Mark job as completed."""
        self.status = JobStatus.COMPLETED.value
        self.progress = 1.0
        self.current_stage = ProcessingStage.RESULT_GENERATION.value # Ensure stage reflects completion
        self.output_file_name = output_file_name
        self.completed_at = datetime.now()
        self.stats = stats
        self.updated_at = self.completed_at # Align updated_at with completed_at

    def fail(self, error_message: str):
        """Mark job as failed."""
        self.status = JobStatus.FAILED.value
        # Optionally set progress to 1.0 or leave as is upon failure
        # self.progress = 1.0
        self.error_message = error_message
        self.updated_at = datetime.now()
        # Ensure completed_at is Null if it failed
        self.completed_at = None