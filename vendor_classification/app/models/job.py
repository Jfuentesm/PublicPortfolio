# <file path='app/models/job.py'>
# --- file path='app/models/job.py' ---
from sqlalchemy import Column, String, Float, DateTime, Enum as SQLEnum, JSON, Text, Integer, ForeignKey, Index # <<< ADDED Index
from sqlalchemy.sql import func
from sqlalchemy.orm import Session # <<< ADDED IMPORT FOR TYPE HINTING
from enum import Enum as PyEnum
from datetime import datetime, timezone # <<< Added timezone
from typing import Optional, Dict, Any, List # <<< ADDED List

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
    CLASSIFICATION_L5 = "classification_level_5" # ADDED L5 Stage
    SEARCH = "search_unknown_vendors" # This stage now covers search AND recursive post-search classification
    RECLASSIFICATION = "reclassification" # <<< ADDED Reclassification Stage
    RESULT_GENERATION = "result_generation"

# --- ADDED: Job Type Enum ---
class JobType(str, PyEnum):
    """Type of job."""
    CLASSIFICATION = "CLASSIFICATION"
    REVIEW = "REVIEW"
# --- END ADDED ---


class Job(Base):
    """Job model for tracking classification jobs."""

    __tablename__ = "jobs"

    id = Column(String, primary_key=True, index=True)
    company_name = Column(String, nullable=False)
    input_file_name = Column(String, nullable=False)
    output_file_name = Column(String, nullable=True)
    status = Column(String, default=JobStatus.PENDING.value) # Consider adding index if frequently filtered by status
    current_stage = Column(String, default=ProcessingStage.INGESTION.value)
    progress = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now()) # Consider adding index if frequently sorted/filtered by creation time
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now()) # Consider index if filtered by update time (e.g., failed jobs in last X hours)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    notification_email = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    stats = Column(JSON, default={}) # Structure defined by ProcessingStats model OR used for review inputs/status
    created_by = Column(String, nullable=False) # Consider adding index if frequently filtered by user
    target_level = Column(Integer, nullable=False, default=5) # Store the desired classification depth (1-5)

    # --- ADDED: Job Type and Parent Link ---
    job_type = Column(String, default=JobType.CLASSIFICATION.value, nullable=False) # Consider adding index if frequently filtered by job type
    parent_job_id = Column(String, ForeignKey("jobs.id"), nullable=True, index=True) # Link to original job for reviews
    # --- END ADDED ---

    # Stores List[JobResultItem] for CLASSIFICATION jobs
    # Stores List[ReviewResultItem] for REVIEW jobs
    detailed_results = Column(JSON, nullable=True)


    # --- ADDED: Potential Indexes for Admin Dashboard Performance ---
    __table_args__ = (
        Index('ix_jobs_status_updated_at', 'status', 'updated_at'), # For failed jobs in last X hours query
        Index('ix_jobs_created_at_desc', created_at.desc()), # For recent jobs query
        Index('ix_jobs_created_by', 'created_by'), # If filtering by user becomes common
        Index('ix_jobs_job_type', 'job_type'), # If filtering by job type becomes common
        # parent_job_id already has an index due to index=True above
    )
    # --- END ADDED ---


    def update_progress(self, progress: float, stage: ProcessingStage, db_session: Optional[Session] = None): # Type hint now valid
        """Update job progress and stage, optionally committing."""
        self.progress = progress
        self.current_stage = stage.value
        self.updated_at = datetime.now(timezone.utc) # Use timezone aware now
        # Optionally commit immediately if session provided
        if db_session:
            try:
                db_session.commit()
            except Exception as e:
                from core.logging_config import get_logger # Local import for safety
                logger = get_logger("vendor_classification.job_model")
                logger.error(f"Failed to commit progress update for job {self.id}", exc_info=True)
                db_session.rollback()


    # --- UPDATED: complete method signature ---
    # detailed_results type hint updated to handle both list types
    def complete(self, output_file_name: Optional[str], stats: Dict[str, Any], detailed_results: Optional[List[Dict[str, Any]]] = None):
    # --- END UPDATED ---
        """Mark job as completed."""
        self.status = JobStatus.COMPLETED.value
        self.progress = 1.0
        # Ensure stage reflects completion (Result Generation for CLASSIFICATION, RECLASSIFICATION for REVIEW)
        self.current_stage = ProcessingStage.RESULT_GENERATION.value if self.job_type == JobType.CLASSIFICATION.value else ProcessingStage.RECLASSIFICATION.value
        self.output_file_name = output_file_name # Can be None for review jobs if no file is generated
        self.completed_at = datetime.now(timezone.utc) # Use timezone aware now
        self.stats = stats
        # --- UPDATED: Save detailed results ---
        self.detailed_results = detailed_results
        # --- END UPDATED ---
        self.updated_at = self.completed_at # Align updated_at with completed_at

    def fail(self, error_message: str):
        """Mark job as failed."""
        self.status = JobStatus.FAILED.value
        # Optionally set progress to 1.0 or leave as is upon failure
        # self.progress = 1.0
        self.error_message = error_message
        self.updated_at = datetime.now(timezone.utc) # Use timezone aware now
        # Ensure completed_at is Null if it failed
        self.completed_at = None
        # --- UPDATED: Ensure detailed_results is Null if it failed ---
        self.detailed_results = None
        # --- END UPDATED ---