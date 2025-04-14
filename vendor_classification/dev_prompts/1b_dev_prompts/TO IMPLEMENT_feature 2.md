
Okay, let's break down the implementation of Feature 2: Interactive Re-classification with Hints.

1.  **Completeness:** The feature described is not yet implemented in the provided code. Significant additions and modifications are needed across the frontend and backend.

2.  **New Files:**
    *   `frontend/vue_frontend/src/components/HintInputModal.vue`
    *   `frontend/vue_frontend/src/components/ReviewResultsTable.vue`
    *   `app/schemas/review.py` (To keep review-specific schemas separate)
    *   `app/tasks/reclassification_logic.py` (To house the reclassification task logic)
    *   `app/tasks/reclassification_prompts.py` (For the specific reclassification prompts)

3.  **Updated Files:**
    *   `app/models/job.py` (Add `job_type`, `parent_job_id`)
    *   `app/schemas/job.py` (Update `JobResponse`, add `ReviewResultItem` structure to `detailed_results` handling)
    *   `app/api/jobs.py` (Add `/reclassify` endpoint, adjust `/results` if needed - likely not needed if `detailed_results` stores the correct structure)
    *   `app/tasks/celery_app.py` (Import the new task)
    *   `app/tasks/classification_tasks.py` (Import and potentially call the new task, update result preparation if needed - likely handled by new task)
    *   `app/services/llm_service.py` (May need adaptation or new method for re-classification prompt/call)
    *   `frontend/vue_frontend/src/stores/job.ts` (Add state/actions for flagging, hints, review results)
    *   `frontend/vue_frontend/src/services/api.ts` (Add `reclassifyJob` function)
    *   `frontend/vue_frontend/src/components/JobResultsTable.vue` (Add flagging UI/logic)
    *   `frontend/vue_frontend/src/components/JobStatus.vue` (Conditionally render results tables, link to review jobs)
    *   `frontend/vue_frontend/src/App.vue` (Minor changes if navigation to review jobs is handled here)

---

Let's implement the necessary code changes.

**Backend Changes**

<file path='app/models/job.py'>
```python
# <file path='app/models/job.py'>
# --- file path='app/models/job.py' ---
from sqlalchemy import Column, String, Float, DateTime, Enum as SQLEnum, JSON, Text, Integer, ForeignKey # <<< ADDED ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import Session # <<< ADDED IMPORT FOR TYPE HINTING
from enum import Enum as PyEnum
from datetime import datetime
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
    status = Column(String, default=JobStatus.PENDING.value)
    current_stage = Column(String, default=ProcessingStage.INGESTION.value)
    progress = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    notification_email = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    stats = Column(JSON, default={}) # Structure defined by ProcessingStats model OR used for review inputs
    created_by = Column(String, nullable=False)
    target_level = Column(Integer, nullable=False, default=5) # Store the desired classification depth (1-5)

    # --- ADDED: Job Type and Parent Link ---
    job_type = Column(String, default=JobType.CLASSIFICATION.value, nullable=False)
    parent_job_id = Column(String, ForeignKey("jobs.id"), nullable=True, index=True) # Link to original job for reviews
    # --- END ADDED ---

    # Stores List[JobResultItem] for CLASSIFICATION jobs
    # Stores List[ReviewResultItem] for REVIEW jobs
    detailed_results = Column(JSON, nullable=True)


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
        self.completed_at = datetime.now()
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
        self.updated_at = datetime.now()
        # Ensure completed_at is Null if it failed
        self.completed_at = None
        # --- UPDATED: Ensure detailed_results is Null if it failed ---
        self.detailed_results = None
        # --- END UPDATED ---
```
</file>

<file path='app/schemas/review.py'>
```python
# app/schemas/review.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any

# Schema for items in the reclassify request payload
class ReclassifyRequestItem(BaseModel):
    vendor_name: str = Field(..., description="The exact vendor name to reclassify")
    hint: str = Field(..., description="User-provided hint for reclassification")

# Schema for the reclassify request payload
class ReclassifyPayload(BaseModel):
    items: List[ReclassifyRequestItem] = Field(..., description="List of vendors and hints to reclassify")

# Schema for the reclassify response
class ReclassifyResponse(BaseModel):
    review_job_id: str = Field(..., description="The ID of the newly created review job")
    message: str = Field(default="Re-classification job started.", description="Status message")

# Schema for a single item in the detailed_results of a REVIEW job
# It stores the original result (as a dict) and the new result (as a dict)
class ReviewResultItem(BaseModel):
    vendor_name: str = Field(..., description="Original vendor name")
    hint: str = Field(..., description="Hint provided by the user for this reclassification")
    # Store the full original result structure (which should match JobResultItem)
    original_result: Dict[str, Any] = Field(..., description="The original classification result for this vendor")
    # Store the full new result structure (which should also match JobResultItem)
    new_result: Dict[str, Any] = Field(..., description="The new classification result after applying the hint")

    class Config:
        from_attributes = True # For potential future ORM mapping if results move to separate table
```
</file>

<file path='app/schemas/job.py'>
```python
# <file path='app/schemas/job.py'>
# app/schemas/job.py
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, Any, List, Union # <<< ADDED Union
from datetime import datetime
from enum import Enum as PyEnum

from models.job import JobStatus, ProcessingStage, JobType # Import enums from model
from .review import ReviewResultItem # Import the review result schema

# --- UPDATED: Schema for a single detailed result item (for CLASSIFICATION jobs) ---
class JobResultItem(BaseModel):
    vendor_name: str = Field(..., description="Original vendor name")
    level1_id: Optional[str] = Field(None, description="Level 1 Category ID")
    level1_name: Optional[str] = Field(None, description="Level 1 Category Name")
    level2_id: Optional[str] = Field(None, description="Level 2 Category ID")
    level2_name: Optional[str] = Field(None, description="Level 2 Category Name")
    level3_id: Optional[str] = Field(None, description="Level 3 Category ID")
    level3_name: Optional[str] = Field(None, description="Level 3 Category Name")
    level4_id: Optional[str] = Field(None, description="Level 4 Category ID")
    level4_name: Optional[str] = Field(None, description="Level 4 Category Name")
    level5_id: Optional[str] = Field(None, description="Level 5 Category ID")
    level5_name: Optional[str] = Field(None, description="Level 5 Category Name")
    final_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score of the final classification level achieved (0.0 if not possible)")
    final_status: str = Field(..., description="Overall status ('Classified', 'Not Possible', 'Error')")
    classification_source: Optional[str] = Field(None, description="Source of the final classification ('Initial', 'Search')")
    classification_notes_or_reason: Optional[str] = Field(None, description="LLM notes or reason for failure/low confidence")
    achieved_level: Optional[int] = Field(None, ge=0, le=5, description="Deepest level successfully classified (0 if none)")

    class Config:
        from_attributes = True # For potential future ORM mapping if results move to separate table
# --- END UPDATED ---


class JobBase(BaseModel):
    company_name: str = Field(..., example="Example Corp")
    target_level: int = Field(default=5, ge=1, le=5, example=5) # Add target_level here
    notification_email: Optional[EmailStr] = Field(None, example="user@example.com")

class JobCreate(JobBase):
    # Fields required specifically on creation, if any (handled by JobBase for now)
    pass

class JobResponse(JobBase):
    id: str = Field(..., example="job_abc123")
    input_file_name: str = Field(..., example="vendors.xlsx")
    output_file_name: Optional[str] = Field(None, example="results_job_abc123.xlsx")
    status: JobStatus = Field(..., example=JobStatus.PROCESSING)
    current_stage: ProcessingStage = Field(..., example=ProcessingStage.CLASSIFICATION_L2)
    progress: float = Field(..., example=0.75)
    created_at: datetime = Field(...)
    updated_at: datetime = Field(...)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = Field(None, example="Failed during search phase.")
    stats: Dict[str, Any] = Field(default={}, example={"total_vendors": 100, "unique_vendors": 95})
    created_by: str = Field(..., example="user@example.com")

    # --- ADDED: Job Type and Parent Link ---
    job_type: JobType = Field(..., example=JobType.CLASSIFICATION)
    parent_job_id: Optional[str] = Field(None, example="job_xyz789")
    # --- END ADDED ---

    # NOTE: We don't include detailed_results here by default to keep this response smaller.
    # It will be fetched via a separate endpoint if needed.

    class Config:
        from_attributes = True # Enable ORM mode for automatic mapping from Job model
        use_enum_values = True # Ensure enum values (strings) are used in the response


# --- ADDED: Schema for the detailed results endpoint response ---
# This allows the endpoint to return either type of result list based on job type
class JobResultsResponse(BaseModel):
    job_id: str
    job_type: JobType
    results: Union[List[JobResultItem], List[ReviewResultItem]] = Field(..., description="List of detailed results, structure depends on job_type")
# --- END ADDED ---
```
</file>

<file path='app/api/jobs.py'>
```python
# <file path='app/api/jobs.py'>
# app/api/jobs.py
from fastapi import APIRouter, Depends, HTTPException, Query, status, Path # Added Path
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Union # <<< ADDED Union
from datetime import datetime
import logging # Import logging
import uuid # <<< ADDED for generating review job IDs

from core.database import get_db
from api.auth import get_current_user
from models.user import User
from models.job import Job, JobStatus, JobType # <<< ADDED JobType
# --- UPDATED: Import specific schemas ---
from schemas.job import JobResponse, JobResultItem, JobResultsResponse
from schemas.review import ReclassifyPayload, ReclassifyResponse, ReviewResultItem # <<< ADDED Review Schemas
# --- END UPDATED ---
from core.logging_config import get_logger
from core.log_context import set_log_context
from core.config import settings # Need settings for file path construction
from tasks.classification_tasks import process_vendor_file # Original task
from tasks.reclassification_tasks import reclassify_flagged_vendors_task # <<< ADDED New task


logger = get_logger("vendor_classification.api.jobs")
logger.debug("Successfully imported Dict from typing for jobs API.")

router = APIRouter()

@router.get("/", response_model=List[JobResponse])
async def list_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status_filter: Optional[JobStatus] = Query(None, alias="status", description="Filter jobs by status"),
    start_date: Optional[datetime] = Query(None, description="Filter jobs created on or after this date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="Filter jobs created on or before this date (ISO format)"),
    job_type_filter: Optional[JobType] = Query(None, alias="type", description="Filter jobs by type (CLASSIFICATION or REVIEW)"), # <<< ADDED Filter
    skip: int = Query(0, ge=0, description="Number of jobs to skip for pagination"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of jobs to return"),
):
    """
    List jobs for the current user. Admins can see all jobs (optional enhancement).
    Supports filtering by status, date range, type, and pagination.
    """
    set_log_context({"username": current_user.username})
    logger.info("Fetching job history", extra={
        "status_filter": status_filter,
        "job_type_filter": job_type_filter, # <<< ADDED Log
        "start_date": start_date.isoformat() if start_date else None,
        "end_date": end_date.isoformat() if end_date else None,
        "skip": skip,
        "limit": limit,
    })

    query = db.query(Job)

    # Filter by user (Admins could potentially see all - add logic here if needed)
    # For now, all users only see their own jobs
    # if not current_user.is_superuser: # Example admin check
    query = query.filter(Job.created_by == current_user.username)

    # Apply filters
    if status_filter:
        query = query.filter(Job.status == status_filter.value)
    if job_type_filter: # <<< ADDED Filter
        query = query.filter(Job.job_type == job_type_filter.value)
    if start_date:
        query = query.filter(Job.created_at >= start_date)
    if end_date:
        # Add a day to end_date to make it inclusive of the whole day if time is not specified
        # Or adjust based on desired behavior (e.g., end_date < end_date + timedelta(days=1))
        query = query.filter(Job.created_at <= end_date)

    # Order by creation date (newest first)
    query = query.order_by(Job.created_at.desc())

    # Apply pagination
    jobs = query.offset(skip).limit(limit).all()

    logger.info(f"Retrieved {len(jobs)} jobs from history.")

    # Convert Job models to JobResponse schemas
    # Pydantic v2 handles this automatically with from_attributes=True
    return jobs

@router.get("/{job_id}", response_model=JobResponse)
async def read_job(
    # Use Path to ensure job_id is correctly extracted from the URL path
    job_id: str = Path(..., title="The ID of the job to get"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve details for a specific job by its ID.
    Ensures the current user owns the job (or is an admin - future enhancement).
    """
    set_log_context({"username": current_user.username, "target_job_id": job_id})
    logger.info(f"Fetching details for job ID: {job_id}")

    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        logger.warning(f"Job not found", extra={"job_id": job_id})
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    # --- Authorization Check ---
    # Ensure the user requesting the job is the one who created it
    # (Or add admin override logic here if needed)
    if job.created_by != current_user.username: # and not current_user.is_superuser:
        logger.warning(f"Authorization failed: User '{current_user.username}' attempted to access job '{job_id}' owned by '{job.created_by}'")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this job")
    # --- End Authorization Check ---

    # LOGGING: Log the job details being returned, especially target_level and job_type
    logger.info(f"Returning details for job ID: {job_id}", extra={"job_status": job.status, "target_level": job.target_level, "job_type": job.job_type})
    return job # Pydantic will validate against JobResponse

# Use Dict for flexibility, or create a specific StatsResponse schema later if needed
@router.get("/{job_id}/stats", response_model=Dict)
async def read_job_stats(
    job_id: str = Path(..., title="The ID of the job to get stats for"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve processing statistics for a specific job.
    For REVIEW jobs, this might contain the input hints.
    """
    set_log_context({"username": current_user.username, "target_job_id": job_id})
    logger.info(f"Fetching statistics for job ID: {job_id}")

    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        logger.warning(f"Job not found for stats", extra={"job_id": job_id})
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    # Authorization Check (same as read_job)
    if job.created_by != current_user.username: # and not current_user.is_superuser:
        logger.warning(f"Authorization failed: User '{current_user.username}' attempted to access stats for job '{job_id}' owned by '{job.created_by}'")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access stats for this job")

    # LOGGING: Log the raw stats being returned from the database
    logger.info(f"Returning statistics for job ID: {job_id}", extra={"job_type": job.job_type})
    logger.debug(f"Raw stats from DB for job {job_id}: {job.stats}") # Log the actual stats dict

    # The stats are stored as JSON in the Job model
    return job.stats if job.stats else {}


# --- UPDATED: Endpoint for Detailed Results ---
# Now returns JobResultsResponse which includes job_type and Union of result types
@router.get("/{job_id}/results", response_model=JobResultsResponse)
async def read_job_results(
    job_id: str = Path(..., title="The ID of the job to get detailed results for"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve the detailed classification results for a specific completed job.
    Returns a structure containing the job_id, job_type, and a list of results
    (either JobResultItem or ReviewResultItem depending on the job_type).
    """
    set_log_context({"username": current_user.username, "target_job_id": job_id})
    logger.info(f"Fetching detailed results for job ID: {job_id}")

    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        logger.warning(f"Job not found for results", extra={"job_id": job_id})
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    # Authorization Check
    if job.created_by != current_user.username: # and not current_user.is_superuser:
        logger.warning(f"Authorization failed: User '{current_user.username}' attempted to access results for job '{job_id}' owned by '{job.created_by}'")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access results for this job")

    # Check if job is completed and has results
    if job.status != JobStatus.COMPLETED.value:
        logger.warning(f"Detailed results requested but job not completed",
                       extra={"job_id": job_id, "status": job.status, "job_type": job.job_type})
        # Return empty list in the correct response structure
        return JobResultsResponse(job_id=job_id, job_type=job.job_type, results=[])

    if not job.detailed_results:
        logger.warning(f"Job {job_id} is completed but has no detailed results stored.", extra={"job_id": job_id, "job_type": job.job_type})
        return JobResultsResponse(job_id=job_id, job_type=job.job_type, results=[])

    # The detailed_results field should contain a list of dicts matching the expected schema.
    # Pydantic will validate this structure upon return based on the response_model.
    # We trust the background task stored the correct structure based on job_type.
    results_count = len(job.detailed_results)
    logger.info(f"Returning {results_count} detailed result items for job ID: {job_id}", extra={"job_type": job.job_type})

    # Pydantic should automatically validate based on the Union in JobResultsResponse
    return JobResultsResponse(job_id=job_id, job_type=job.job_type, results=job.detailed_results)
# --- END UPDATED ---


@router.get("/{job_id}/download")
async def download_job_results(
    job_id: str = Path(..., title="The ID of the job to download results for"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Downloads the output Excel file for a completed job.
    Note: Currently only generates Excel for CLASSIFICATION jobs.
    """
    from fastapi.responses import FileResponse # Import here
    import os # Import os

    set_log_context({"username": current_user.username, "target_job_id": job_id})
    logger.info(f"Request to download results for job ID: {job_id}")

    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        logger.warning(f"Job not found for download", extra={"job_id": job_id})
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    # Authorization Check
    if job.created_by != current_user.username: # and not current_user.is_superuser:
        logger.warning(f"Authorization failed: User '{current_user.username}' attempted download for job '{job_id}' owned by '{job.created_by}'")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to download results for this job")

    # --- Check if download is applicable ---
    if job.job_type == JobType.REVIEW.value:
         logger.warning(f"Download requested for a REVIEW job ({job_id}), which doesn't generate an Excel file.", extra={"job_type": job.job_type})
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Download is not available for review jobs.")

    if job.status != JobStatus.COMPLETED.value or not job.output_file_name:
        logger.warning(f"Download requested but job not completed or output file missing",
                       extra={"job_id": job_id, "status": job.status, "output_file": job.output_file_name})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job not completed or output file not available.")
    # --- End Check ---

    # Construct the full path to the output file
    output_dir = os.path.join(settings.OUTPUT_DATA_DIR, job_id)
    file_path = os.path.join(output_dir, job.output_file_name)

    if not os.path.exists(file_path):
         logger.error(f"Output file record exists in DB but file not found on disk",
                      extra={"job_id": job_id, "expected_path": file_path})
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Output file not found.")

    logger.info(f"Streaming output file for download",
                extra={"job_id": job_id, "file_path": file_path})
    return FileResponse(
        path=file_path,
        filename=job.output_file_name, # Suggest filename to browser
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# --- ADDED: Reclassify Endpoint ---
@router.post("/{original_job_id}/reclassify", response_model=ReclassifyResponse, status_code=status.HTTP_202_ACCEPTED)
async def reclassify_job_items(
    original_job_id: str = Path(..., description="The ID of the original classification job"),
    payload: ReclassifyPayload = ..., # Use the Pydantic model for the request body
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Initiates a re-classification task for specific vendors from an original job,
    using user-provided hints.
    """
    set_log_context({"username": current_user.username, "original_job_id": original_job_id})
    logger.info(f"Received reclassification request for job {original_job_id}", extra={"item_count": len(payload.items)})

    # 1. Find the original job
    original_job = db.query(Job).filter(Job.id == original_job_id).first()
    if not original_job:
        logger.warning(f"Original job {original_job_id} not found for reclassification.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Original job not found")

    # 2. Authorization check (user owns the original job)
    if original_job.created_by != current_user.username: # and not current_user.is_superuser:
        logger.warning(f"Authorization failed: User '{current_user.username}' attempted reclassification for job '{original_job_id}' owned by '{original_job.created_by}'")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to reclassify items for this job")

    # 3. Basic validation (ensure original job was classification, maybe check status?)
    if original_job.job_type != JobType.CLASSIFICATION.value:
         logger.warning(f"Attempted to reclassify based on a non-CLASSIFICATION job.", extra={"original_job_type": original_job.job_type})
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reclassification can only be initiated from an original CLASSIFICATION job.")
    if original_job.status != JobStatus.COMPLETED.value:
         logger.warning(f"Attempted to reclassify based on a non-completed job.", extra={"original_job_status": original_job.status})
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reclassification can only be initiated from a COMPLETED job.")

    if not payload.items:
        logger.warning("Reclassification request received with no items to process.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No items provided for reclassification.")

    # 4. Create the new Review Job record
    review_job_id = f"review_{uuid.uuid4().hex[:12]}"
    review_job = Job(
        id=review_job_id,
        company_name=original_job.company_name, # Inherit company name
        input_file_name=f"Review of {original_job.input_file_name}", # Indicate source
        output_file_name=None, # Review jobs don't produce downloads (for now)
        status=JobStatus.PENDING.value,
        current_stage=ProcessingStage.PENDING.value, # Start as pending
        progress=0.0,
        created_by=current_user.username,
        target_level=original_job.target_level, # Inherit target level
        job_type=JobType.REVIEW.value, # Mark as REVIEW type
        parent_job_id=original_job_id, # Link back to the original job
        stats={"reclassify_input": [item.model_dump() for item in payload.items]}, # Store input hints/vendors
        detailed_results=None, # Will be populated by the task
        notification_email=original_job.notification_email # Optionally inherit email
    )

    try:
        db.add(review_job)
        db.commit()
        db.refresh(review_job)
        logger.info(f"Created new REVIEW job record", extra={"review_job_id": review_job_id, "parent_job_id": original_job_id})
    except Exception as e:
        db.rollback()
        logger.error("Failed to create REVIEW job record in database", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to initiate reclassification job.")

    # 5. Queue the Celery task
    try:
        logger.info(f"Queuing reclassification task for review job {review_job_id}")
        reclassify_flagged_vendors_task.delay(review_job_id=review_job_id)
        logger.info(f"Reclassification task successfully queued.")
    except Exception as e:
        logger.error(f"Failed to queue Celery reclassification task for review job {review_job_id}", exc_info=True)
        # Attempt to mark the created review job as failed
        review_job.fail(f"Failed to queue background task: {str(e)}")
        db.commit()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to queue reclassification task.")

    # 6. Return the review job ID
    return ReclassifyResponse(review_job_id=review_job_id)
# --- END ADDED ---
```
</file>

<file path='app/tasks/reclassification_prompts.py'>
```python
# app/tasks/reclassification_prompts.py
import json
import logging
from typing import Dict, Any, Optional

from models.taxonomy import Taxonomy, TaxonomyCategory
from schemas.job import JobResultItem # To understand the structure of original_result

logger = logging.getLogger("vendor_classification.reclassification_prompts")

def generate_reclassification_prompt(
    original_vendor_data: Dict[str, Any],
    user_hint: str,
    original_classification: Optional[Dict[str, Any]], # Dict matching JobResultItem
    taxonomy: Taxonomy,
    target_level: int, # The target level for this reclassification attempt
    attempt_id: str = "unknown-attempt"
) -> str:
    """
    Create a prompt for re-classifying a single vendor based on original data,
    user hint, and previous classification attempt. Aims for the target_level.
    """
    vendor_name = original_vendor_data.get('vendor_name', 'UnknownVendor')
    logger.debug(f"Generating reclassification prompt for vendor: {vendor_name}",
                extra={"target_level": target_level, "attempt_id": attempt_id})

    # --- Build Original Vendor Data Section ---
    vendor_data_xml = "<original_vendor_data>\n"
    vendor_data_xml += f"  <name>{vendor_name}</name>\n"
    # Include all available fields from the original data
    optional_fields = [
        'example_goods_services', 'address', 'website',
        'internal_category', 'parent_company', 'spend_category'
    ]
    # Map internal keys to XML tags if needed (adjust based on original_vendor_data structure)
    field_map = {
        'example_goods_services': 'example_goods_services',
        'address': 'address',
        'website': 'website',
        'internal_category': 'internal_category',
        'parent_company': 'parent_company',
        'spend_category': 'spend_category',
        # Add mappings if keys in original_vendor_data are different
        'example': 'example_goods_services',
        'vendor_address': 'address',
        'vendor_website': 'website',
    }
    for field_key, xml_tag in field_map.items():
        value = original_vendor_data.get(field_key)
        if value:
            vendor_data_xml += f"  <{xml_tag}>{str(value)[:300]}</{xml_tag}>\n" # Limit length
    vendor_data_xml += "</original_vendor_data>"

    # --- Build User Hint Section ---
    user_hint_xml = f"<user_hint>{user_hint}</user_hint>"

    # --- Build Original Classification Section (Optional but helpful) ---
    original_classification_xml = "<original_classification_attempt>\n"
    if original_classification:
        original_status = original_classification.get('final_status', 'Unknown')
        original_level = original_classification.get('achieved_level', 0)
        original_reason = original_classification.get('classification_notes_or_reason', 'N/A')
        original_classification_xml += f"  <status>{original_status}</status>\n"
        original_classification_xml += f"  <achieved_level>{original_level}</achieved_level>\n"
        original_classification_xml += f"  <reason_or_notes>{original_reason}</reason_or_notes>\n"
        # Include original L1-L5 IDs/Names if available
        for i in range(1, 6):
             id_key = f'level{i}_id'
             name_key = f'level{i}_name'
             cat_id = original_classification.get(id_key)
             cat_name = original_classification.get(name_key)
             if cat_id and cat_name:
                 original_classification_xml += f"  <level_{i}_result id=\"{cat_id}\" name=\"{cat_name}\"/>\n"
    else:
        original_classification_xml += "  <message>No previous classification data available.</message>\n"
    original_classification_xml += "</original_classification_attempt>"

    # --- Define Output Format Section (Standard Classification Result) ---
    # We want the LLM to output the *new* classification in the standard format
    # It needs to perform the hierarchical classification again based on the hint.
    output_format_xml = f"""<output_format>
Respond *only* with a valid JSON object containing the *new* classification result for this vendor, based *primarily* on the <user_hint> and <original_vendor_data>.
The JSON object should represent the full classification attempt up to Level {target_level}, following the standard structure used previously.

json
{{
  "level": {target_level}, // The target level for this reclassification
  "attempt_id": "{attempt_id}", // ID for this specific attempt
  "vendor_name": "{vendor_name}", // Exact vendor name
  "classifications": [ // Array with ONE entry for this vendor
    {{
      "vendor_name": "{vendor_name}", // Vendor name again
      // --- L1 Result ---
      "level1": {{
        "category_id": "string", // L1 ID from taxonomy or "N/A"
        "category_name": "string", // L1 Name or "N/A"
        "confidence": "float", // 0.0-1.0
        "classification_not_possible": "boolean",
        "classification_not_possible_reason": "string | null",
        "notes": "string | null" // Justification based on hint/data
      }},
      // --- L2 Result (if L1 possible and target_level >= 2) ---
      "level2": {{ // Include ONLY if L1 was possible AND target_level >= 2
        "category_id": "string", // L2 ID or "N/A"
        "category_name": "string", // L2 Name or "N/A"
        "confidence": "float",
        "classification_not_possible": "boolean",
        "classification_not_possible_reason": "string | null",
        "notes": "string | null"
      }} // , ... include level3, level4, level5 similarly if possible and target_level allows
      // --- L3 Result (if L2 possible and target_level >= 3) ---
      // --- L4 Result (if L3 possible and target_level >= 4) ---
      // --- L5 Result (if L4 possible and target_level >= 5) ---
    }}
  ]
}}

</output_format>"""

    # --- Assemble Final Prompt ---
    prompt = f"""
<role>You are a precise vendor classification expert using the NAICS taxonomy. You are re-evaluating a previous classification based on new user input.</role>

<task>Re-classify the vendor described in `<original_vendor_data>` using the crucial information provided in `<user_hint>`. The previous attempt is in `<original_classification_attempt>` for context. Your goal is to determine the most accurate NAICS classification up to **Level {target_level}** based *primarily* on the user hint combined with the original data.</task>

<instructions>
1.  **Prioritize the `<user_hint>`**. Assume it provides the most accurate context about the vendor's primary business activity for the user's purposes.
2.  Use the `<original_vendor_data>` to supplement the hint if necessary.
3.  Refer to the `<original_classification_attempt>` only for context on why the previous classification might have been incorrect or insufficient. Do not simply repeat the old result unless the hint strongly confirms it.
4.  Perform a hierarchical classification starting from Level 1 up to the target Level {target_level}.
5.  For **each level**:
    a.  Determine the most appropriate category based on the hint and data. Use the provided taxonomy structure (implicitly known or explicitly provided if needed in future versions).
    b.  If a confident classification for the current level is possible, provide the `category_id`, `category_name`, `confidence` (> 0.0), set `classification_not_possible` to `false`, and optionally add `notes`. Proceed to the next level if the target level allows.
    c.  If classification for the current level is **not possible** (due to ambiguity even with the hint, or the hint pointing to an activity outside the available subcategories), set `classification_not_possible` to `true`, `confidence` to `0.0`, provide a `classification_not_possible_reason`, set `category_id`/`category_name` to "N/A", and **stop** the classification process for this vendor (do not include results for subsequent levels).
6.  Structure your response as a **single JSON object** matching the schema in `<output_format>`. Ensure it contains results for all levels attempted up to the point of success or failure.
7.  The output JSON should represent the *new* classification attempt based on the hint.
8.  Respond *only* with the valid JSON object.
</instructions>

{vendor_data_xml}

{user_hint_xml}

{original_classification_xml}

{output_format_xml}
"""
    # Note: This prompt implicitly relies on the LLM having access to the taxonomy structure
    # or being trained on it. For dynamic taxonomies, the relevant category options for each
    # level would need to be injected similar to the original batch prompt.
    # For now, we assume the LLM can infer the hierarchy and valid IDs based on the target level and task.
    # A future enhancement could involve passing the relevant taxonomy branches.

    return prompt
```
</file>

<file path='app/tasks/reclassification_logic.py'>
```python
# app/tasks/reclassification_logic.py
import asyncio
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from core.config import settings
from core.logging_config import get_logger
from core.log_context import set_log_context
from utils.log_utils import LogTimer, log_function_call, log_duration

from models.job import Job, JobStatus, ProcessingStage, JobType
from models.taxonomy import Taxonomy
from services.llm_service import LLMService
from services.file_service import read_vendor_file # To read original data
from utils.taxonomy_loader import load_taxonomy
from schemas.job import JobResultItem # For validation/structure reference
from schemas.review import ReviewResultItem

# Import the specific prompt generator
from .reclassification_prompts import generate_reclassification_prompt

logger = get_logger("vendor_classification.reclassification_logic")

# Timeout for a single vendor reclassification LLM call
RECLASSIFY_VENDOR_TIMEOUT = 120.0 # 2 minutes per vendor

async def _reclassify_single_vendor(
    vendor_name: str,
    hint: str,
    original_vendor_data: Dict[str, Any],
    original_classification_result: Optional[Dict[str, Any]],
    taxonomy: Taxonomy,
    llm_service: LLMService,
    target_level: int,
    stats: Dict[str, Any], # Pass stats dict to update API usage
    attempt_id: str
) -> Dict[str, Any]:
    """
    Handles the LLM call and result processing for re-classifying a single vendor.
    Returns a dictionary matching the JobResultItem structure for the *new* classification.
    """
    logger.info(f"Re-classifying vendor '{vendor_name}' using hint.", extra={"target_level": target_level, "attempt_id": attempt_id})
    new_result_structure: Dict[str, Any] = {
        "vendor_name": vendor_name,
        "level1_id": None, "level1_name": None,
        "level2_id": None, "level2_name": None,
        "level3_id": None, "level3_name": None,
        "level4_id": None, "level4_name": None,
        "level5_id": None, "level5_name": None,
        "final_confidence": 0.0,
        "final_status": "Error", # Default to Error
        "classification_source": "Review", # Source is Review
        "classification_notes_or_reason": "Reclassification not completed.",
        "achieved_level": 0
    }

    try:
        # 1. Generate Prompt
        logger.debug(f"Generating reclassification prompt for '{vendor_name}'")
        prompt = generate_reclassification_prompt(
            original_vendor_data=original_vendor_data,
            user_hint=hint,
            original_classification=original_classification_result,
            taxonomy=taxonomy,
            target_level=target_level,
            attempt_id=attempt_id
        )

        # 2. Call LLM (using classify_batch for one item, adapting prompt/payload)
        #    We expect the LLM to perform the hierarchy internally based on the prompt.
        logger.debug(f"Calling LLM for reclassification of '{vendor_name}'")
        with LogTimer(logger, f"LLM reclassification - Vendor '{vendor_name}'", include_in_stats=True):
            # Use classify_batch with a single item list and the custom prompt
            # Note: classify_batch expects a list of vendor dicts, level, taxonomy etc.
            # We need to adjust how we call it or create a wrapper/new method.
            # Let's assume classify_batch can handle a custom prompt via messages for now.
            # OR, more likely, we need a new method in LLMService or adapt the prompt generation
            # to fit the existing classify_batch structure (less ideal).

            # --- Alternative Approach: Direct LLM Call (if LLMService allows) ---
            # This bypasses the batching logic but gives more control over the prompt.
            # Requires adding a method like `call_llm_raw` or similar to LLMService.
            # For now, let's *simulate* the expected output structure as if classify_batch worked.
            # In a real implementation, this LLM call needs refinement.

            # --- Placeholder LLM Call ---
            # This simulates the structure returned by classify_batch
            # Replace this with the actual LLM call logic
            llm_response_data = await llm_service.classify_batch(
                 batch_data=[original_vendor_data], # Pass original data for context if needed by classify_batch internals
                 level=target_level, # Signal target level
                 taxonomy=taxonomy,
                 parent_category_id=None, # Not applicable directly here, hierarchy driven by prompt
                 # We need a way to pass the custom prompt - maybe a new parameter?
                 # custom_prompt=prompt # Hypothetical parameter
                 # Or modify classify_batch to accept raw messages
            )
            # --- End Placeholder ---

        logger.debug(f"LLM reclassification call completed for '{vendor_name}'")

        if llm_response_data and isinstance(llm_response_data.get("usage"), dict):
            usage = llm_response_data["usage"]
            stats["api_usage"]["openrouter_calls"] += 1
            stats["api_usage"]["openrouter_prompt_tokens"] += usage.get("prompt_tokens", 0)
            stats["api_usage"]["openrouter_completion_tokens"] += usage.get("completion_tokens", 0)
            stats["api_usage"]["openrouter_total_tokens"] += usage.get("total_tokens", 0)
        else:
            logger.warning("Reclassification LLM response missing or has invalid usage data.")

        if llm_response_data is None or "result" not in llm_response_data:
            raise ValueError("LLM service returned None or invalid response structure.")

        llm_result_payload = llm_response_data["result"]
        classifications = llm_result_payload.get("classifications", [])

        if not classifications or not isinstance(classifications, list) or len(classifications) == 0:
             raise ValueError("LLM response missing 'classifications' array or it's empty.")

        # The prompt asks for the full hierarchy in the response under 'classifications'[0]
        new_classification_data = classifications[0] # Get the single vendor result

        # 3. Process and Validate the LLM's Hierarchical Result
        deepest_successful_level = 0
        final_level_data = None
        final_notes_or_reason = None

        # Iterate through levels 1 to target_level from the LLM response
        for level in range(1, target_level + 1):
            level_key = f"level{level}"
            level_data = new_classification_data.get(level_key)

            if level_data and isinstance(level_data, dict):
                # --- Basic Validation (similar to process_batch) ---
                category_id = level_data.get("category_id")
                is_possible = not level_data.get("classification_not_possible", True)

                if is_possible and (not category_id or category_id == "N/A"):
                    logger.warning(f"Reclassification L{level} for '{vendor_name}' marked possible but ID missing/NA. Marking failed.")
                    level_data["classification_not_possible"] = True
                    level_data["classification_not_possible_reason"] = f"LLM marked L{level} possible but ID was missing/NA"
                    level_data["confidence"] = 0.0
                    is_possible = False

                # TODO: Add taxonomy validation against valid IDs for the parent if needed,
                # similar to process_batch. This requires getting the parent ID from the previous level's result.

                # Populate the flat structure
                new_result_structure[f"level{level}_id"] = level_data.get("category_id")
                new_result_structure[f"level{level}_name"] = level_data.get("category_name")

                if is_possible:
                    deepest_successful_level = level
                    final_level_data = level_data
                    final_notes_or_reason = level_data.get("notes")
                elif deepest_successful_level == 0 and level == 1: # Capture L1 failure reason
                    final_notes_or_reason = level_data.get("classification_not_possible_reason") or level_data.get("notes")

                # If classification not possible at this level, stop processing further levels
                if not is_possible:
                    logger.info(f"Reclassification for '{vendor_name}' stopped at Level {level}. Reason: {level_data.get('classification_not_possible_reason')}")
                    break
            else:
                # Stop if a level is missing in the response (shouldn't happen if LLM follows prompt)
                logger.warning(f"Reclassification response for '{vendor_name}' missing expected Level {level} data. Stopping hierarchy processing.")
                if deepest_successful_level == 0 and level == 1: # If L1 is missing entirely
                    final_notes_or_reason = f"LLM response did not include Level {level} data."
                break

        # Determine final status based on results
        if final_level_data:
            new_result_structure["final_status"] = "Classified"
            new_result_structure["final_confidence"] = final_level_data.get("confidence")
            new_result_structure["achieved_level"] = deepest_successful_level
            new_result_structure["classification_notes_or_reason"] = final_notes_or_reason
        else:
            new_result_structure["final_status"] = "Not Possible"
            new_result_structure["final_confidence"] = 0.0
            new_result_structure["achieved_level"] = 0
            new_result_structure["classification_notes_or_reason"] = final_notes_or_reason or "Reclassification failed or yielded no result."

        # Validate the final structure (optional but recommended)
        try:
            JobResultItem.model_validate(new_result_structure)
        except Exception as validation_err:
            logger.error(f"Validation failed for reclassified result of vendor '{vendor_name}'",
                         exc_info=True, extra={"result_data": new_result_structure})
            # Fallback to error state
            new_result_structure["final_status"] = "Error"
            new_result_structure["classification_notes_or_reason"] = f"Internal validation error after reclassification: {str(validation_err)}"
            new_result_structure["achieved_level"] = 0
            new_result_structure["final_confidence"] = 0.0
            # Clear level data on validation error
            for i in range(1, 6):
                new_result_structure[f"level{i}_id"] = None
                new_result_structure[f"level{i}_name"] = None

    except Exception as e:
        logger.error(f"Error during single vendor reclassification for '{vendor_name}'", exc_info=True)
        new_result_structure["final_status"] = "Error"
        new_result_structure["classification_notes_or_reason"] = f"Reclassification task error: {str(e)[:150]}"
        new_result_structure["achieved_level"] = 0
        new_result_structure["final_confidence"] = 0.0
         # Clear level data on error
        for i in range(1, 6):
            new_result_structure[f"level{i}_id"] = None
            new_result_structure[f"level{i}_name"] = None

    return new_result_structure


@log_function_call(logger, include_args=False)
async def process_reclassification(
    review_job: Job,
    db: Session,
    llm_service: LLMService
):
    """
    Main orchestration function for the reclassification task.
    Fetches original data/results, iterates through hints, calls LLM, stores results.
    """
    parent_job_id = review_job.parent_job_id
    review_job_id = review_job.id
    target_level = review_job.target_level
    reclassify_input = review_job.stats.get("reclassify_input", [])

    logger.info(f"Starting reclassification process for review job {review_job_id}",
                extra={"parent_job_id": parent_job_id, "item_count": len(reclassify_input)})

    if not parent_job_id:
        raise ValueError("Review job is missing parent_job_id.")
    if not reclassify_input:
        logger.warning(f"Review job {review_job_id} has no items to reclassify in stats.")
        return [], {} # Return empty results and stats

    # --- Initialize stats for the review job ---
    start_time = datetime.now()
    stats: Dict[str, Any] = {
        "job_id": review_job_id,
        "parent_job_id": parent_job_id,
        "start_time": start_time.isoformat(),
        "end_time": None,
        "processing_duration_seconds": None,
        "total_items_processed": 0,
        "successful_reclassifications": 0,
        "failed_reclassifications": 0,
        "api_usage": { # Initialize API usage tracking
            "openrouter_calls": 0,
            "openrouter_prompt_tokens": 0,
            "openrouter_completion_tokens": 0,
            "openrouter_total_tokens": 0,
            "tavily_search_calls": 0, # Should be 0 for reclassification
            "cost_estimate_usd": 0.0
        }
    }
    # --- End Initialize stats ---

    # 1. Fetch Parent Job and Taxonomy
    parent_job = db.query(Job).filter(Job.id == parent_job_id).first()
    if not parent_job:
        raise ValueError(f"Parent job {parent_job_id} not found.")
    if not parent_job.detailed_results:
        raise ValueError(f"Parent job {parent_job_id} does not have detailed results stored.")

    taxonomy = load_taxonomy()

    # 2. Load Original Input Data (Requires access to the parent job's input file)
    # Construct the path relative to the parent job ID
    parent_input_dir = os.path.join(settings.INPUT_DATA_DIR, parent_job_id)
    parent_file_path = os.path.join(parent_input_dir, parent_job.input_file_name)
    if not os.path.exists(parent_file_path):
         raise FileNotFoundError(f"Original input file not found for parent job {parent_job_id} at {parent_file_path}")

    original_vendors_data_list = read_vendor_file(parent_file_path)
    # Create a map for easy lookup: vendor_name -> full original data dict
    original_data_map = {
        str(vendor.get('vendor_name')).strip().title(): vendor # Assuming names were normalized
        for vendor in original_vendors_data_list if vendor.get('vendor_name')
    }
    logger.info(f"Loaded original input data from {parent_file_path}. Found {len(original_data_map)} vendors.")

    # 3. Create Map of Original Results
    original_results_map: Dict[str, Dict[str, Any]] = {
        str(result.get('vendor_name')).strip().title(): result # Assuming names match normalized names
        for result in parent_job.detailed_results if result.get('vendor_name')
    }
    logger.info(f"Created map of original results from parent job {parent_job_id}. Found {len(original_results_map)} results.")


    # 4. Process each item with hint concurrently
    review_results_list: List[Dict[str, Any]] = []
    tasks = []
    processed_count = 0

    for item in reclassify_input:
        processed_count += 1
        vendor_name_raw = item.get("vendor_name")
        hint = item.get("hint")

        if not vendor_name_raw or not hint:
            logger.warning("Skipping item due to missing vendor name or hint", extra={"item": item})
            stats["failed_reclassifications"] += 1
            continue

        # Normalize vendor name for lookup consistency
        vendor_name = str(vendor_name_raw).strip().title()

        original_data = original_data_map.get(vendor_name)
        original_result = original_results_map.get(vendor_name)

        if not original_data:
            logger.warning(f"Original data not found for vendor '{vendor_name}'. Skipping reclassification.", extra={"vendor_name_raw": vendor_name_raw})
            stats["failed_reclassifications"] += 1
            # Store a failure record?
            review_results_list.append({
                "vendor_name": vendor_name_raw,
                "hint": hint,
                "original_result": original_result or {"error": "Original result lookup failed"},
                "new_result": {"final_status": "Error", "classification_notes_or_reason": "Original input data not found"}
            })
            continue
        if not original_result:
             logger.warning(f"Original classification result not found for vendor '{vendor_name}'. Proceeding without it as context.", extra={"vendor_name_raw": vendor_name_raw})
             # Proceed, but the prompt won't have the original classification context

        attempt_id = f"{review_job_id}_{processed_count}"
        set_log_context({"vendor_name": vendor_name, "attempt_id": attempt_id})

        # Create task for concurrent execution
        task = asyncio.create_task(
            _reclassify_single_vendor(
                vendor_name=vendor_name, # Use normalized name for processing
                hint=hint,
                original_vendor_data=original_data,
                original_classification_result=original_result,
                taxonomy=taxonomy,
                llm_service=llm_service,
                target_level=target_level,
                stats=stats, # Pass stats dict
                attempt_id=attempt_id
            )
        )
        tasks.append((vendor_name_raw, hint, original_result, task)) # Store raw name, hint, original result with task

    # 5. Gather results
    logger.info(f"Gathering results for {len(tasks)} reclassification tasks.")
    task_results = await asyncio.gather(*(task for _, _, _, task in tasks))
    logger.info("Reclassification tasks completed.")

    # 6. Combine results
    for i, new_result in enumerate(task_results):
        vendor_name_raw, hint, original_result, _ = tasks[i]
        review_item = {
            "vendor_name": vendor_name_raw, # Store the name as provided in the input
            "hint": hint,
            "original_result": original_result or {"message": "Original result not found during processing"},
            "new_result": new_result # This is the dict returned by _reclassify_single_vendor
        }
        review_results_list.append(review_item)

        # Update stats based on the new result status
        if new_result and new_result.get("final_status") == "Classified":
            stats["successful_reclassifications"] += 1
        else:
            stats["failed_reclassifications"] += 1

    stats["total_items_processed"] = len(reclassify_input)

    # 7. Finalize stats
    end_time = datetime.now()
    processing_duration = (end_time - start_time).total_seconds()
    stats["end_time"] = end_time.isoformat()
    stats["processing_duration_seconds"] = round(processing_duration, 2)
    # Calculate cost
    cost_input_per_1k = 0.0005
    cost_output_per_1k = 0.0015
    estimated_cost = (stats["api_usage"]["openrouter_prompt_tokens"] / 1000) * cost_input_per_1k + \
                        (stats["api_usage"]["openrouter_completion_tokens"] / 1000) * cost_output_per_1k
    # Tavily cost should be 0 here
    stats["api_usage"]["cost_estimate_usd"] = round(estimated_cost, 4)

    logger.info("Reclassification processing finished.", extra={
        "successful": stats["successful_reclassifications"],
        "failed": stats["failed_reclassifications"],
        "duration_sec": stats["processing_duration_seconds"]
    })

    # Return the list of review results and the final stats dict
    return review_results_list, stats
```
</file>

<file path='app/tasks/classification_tasks.py'>
```python
# <file path='app/tasks/classification_tasks.py'>
# app/tasks/classification_tasks.py
import os
import asyncio
import logging
from datetime import datetime
from celery import shared_task
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, Any, List, Optional # <<< ADDED List, Optional

from core.database import SessionLocal
from core.config import settings
from core.logging_config import get_logger
# Import context functions from the new module
from core.log_context import set_correlation_id, set_job_id, set_log_context, clear_all_context
# Import log helpers from utils
from utils.log_utils import LogTimer, log_duration

from models.job import Job, JobStatus, ProcessingStage, JobType # <<< ADDED JobType
from services.file_service import read_vendor_file, normalize_vendor_data, generate_output_file
from services.llm_service import LLMService
from services.search_service import SearchService
from utils.taxonomy_loader import load_taxonomy

# Import the refactored logic
from .classification_logic import process_vendors
# Import the schema for type hinting
from schemas.job import JobResultItem
# Import review schemas/logic if needed (likely handled by separate task)
from schemas.review import ReviewResultItem


# Configure logger
logger = get_logger("vendor_classification.tasks")
# --- ADDED: Log confirmation ---
logger.debug("Successfully imported Dict and Any from typing for classification tasks.")
# --- END ADDED ---


# --- UPDATED: Helper function to process results for DB storage ---
def _prepare_detailed_results_for_storage(
    results_dict: Dict[str, Dict],
    target_level: int # Keep target_level for reference if needed, but we store all levels now
) -> List[Dict[str, Any]]:
    """
    Processes the complex results dictionary (containing level1, level2... sub-dicts)
    into a flat list of dictionaries, where each dictionary represents a vendor
    and contains fields for all L1-L5 classifications, plus final status details.
    Matches the JobResultItem schema.
    THIS IS FOR **CLASSIFICATION** JOBS. Review jobs store results differently.
    """
    processed_list = []
    logger.info(f"Preparing detailed results for CLASSIFICATION job storage. Processing {len(results_dict)} vendors.")

    for vendor_name, vendor_results in results_dict.items():
        # Initialize the flat structure for this vendor
        flat_result: Dict[str, Any] = {
            "vendor_name": vendor_name,
            "level1_id": None, "level1_name": None,
            "level2_id": None, "level2_name": None,
            "level3_id": None, "level3_name": None,
            "level4_id": None, "level4_name": None,
            "level5_id": None, "level5_name": None,
            "final_confidence": None,
            "final_status": "Not Possible", # Default status
            "classification_source": "Initial", # Default source
            "classification_notes_or_reason": None,
            "achieved_level": 0 # Default achieved level
        }

        deepest_successful_level = 0
        final_level_data = None
        final_source = "Initial" # Track the source of the final decision point
        final_notes_or_reason = None

        # Iterate through levels 1 to 5 to populate the flat structure
        for level in range(1, 6):
            level_key = f"level{level}"
            level_data = vendor_results.get(level_key)

            if level_data and isinstance(level_data, dict):
                # Populate the corresponding fields in flat_result
                flat_result[f"level{level}_id"] = level_data.get("category_id")
                flat_result[f"level{level}_name"] = level_data.get("category_name")

                # Track the deepest successful classification
                if not level_data.get("classification_not_possible", True):
                    deepest_successful_level = level
                    final_level_data = level_data # Store data of the deepest successful level
                    # Update source based on the source recorded *at that level*
                    final_source = level_data.get("classification_source", final_source)
                    final_notes_or_reason = level_data.get("notes") # Get notes from successful level
                elif deepest_successful_level == 0: # If no level succeeded yet, track potential failure reasons/notes from L1
                    if level == 1:
                        final_notes_or_reason = level_data.get("classification_not_possible_reason") or level_data.get("notes")
                        # Update source based on L1 source if it exists
                        final_source = level_data.get("classification_source", final_source)

            # If a level wasn't processed (e.g., stopped early), its fields remain None

        # Determine final status, confidence, and notes based on the deepest successful level
        if final_level_data:
            flat_result["final_status"] = "Classified"
            flat_result["final_confidence"] = final_level_data.get("confidence")
            flat_result["achieved_level"] = deepest_successful_level
            flat_result["classification_notes_or_reason"] = final_notes_or_reason # Use notes from final level
        else:
            # No level was successfully classified
            flat_result["final_status"] = "Not Possible"
            flat_result["final_confidence"] = 0.0
            flat_result["achieved_level"] = 0
            # Use the reason/notes captured from L1 failure or search failure
            flat_result["classification_notes_or_reason"] = final_notes_or_reason

        # Set the final determined source
        flat_result["classification_source"] = final_source

        # Handle potential ERROR states explicitly (e.g., if L1 failed with ERROR)
        l1_data = vendor_results.get("level1")
        if l1_data and l1_data.get("category_id") == "ERROR":
            flat_result["final_status"] = "Error"
            flat_result["classification_notes_or_reason"] = l1_data.get("classification_not_possible_reason") or "Processing error occurred"
            # Override source if error occurred
            final_source = l1_data.get("classification_source", "Initial")
            flat_result["classification_source"] = final_source


        # Validate against Pydantic model (optional, but good practice)
        try:
            JobResultItem.model_validate(flat_result)
            processed_list.append(flat_result)
        except Exception as validation_err:
            logger.error(f"Validation failed for prepared result of vendor '{vendor_name}'",
                         exc_info=True, extra={"result_data": flat_result})
            # Optionally append a placeholder error entry or skip
            # For now, let's skip invalid entries
            continue

    logger.info(f"Finished preparing {len(processed_list)} detailed result items for CLASSIFICATION job storage.")
    return processed_list
# --- END UPDATED ---


@shared_task(bind=True)
# --- UPDATED: Added target_level parameter ---
def process_vendor_file(self, job_id: str, file_path: str, target_level: int):
# --- END UPDATED ---
    """
    Celery task entry point for processing a vendor file (CLASSIFICATION job type).
    Orchestrates the overall process by calling the main async helper.

    Args:
        job_id: Job ID
        file_path: Path to vendor file
        target_level: The desired maximum classification level (1-5)
    """
    task_id = self.request.id if self.request and self.request.id else "UnknownTaskID"
    logger.info(f"***** process_vendor_file TASK RECEIVED (CLASSIFICATION) *****",
                extra={
                    "celery_task_id": task_id,
                    "job_id_arg": job_id,
                    "file_path_arg": file_path,
                    "target_level_arg": target_level # Log received target level
                })

    set_correlation_id(job_id) # Set correlation ID early
    set_job_id(job_id)
    set_log_context({"target_level": target_level, "job_type": JobType.CLASSIFICATION.value}) # Add target level and type to context
    logger.info(f"Starting vendor file processing task (inside function)",
                extra={"job_id": job_id, "file_path": file_path, "target_level": target_level})

    # Validate target_level
    if not 1 <= target_level <= 5:
        logger.error(f"Invalid target_level received: {target_level}. Must be between 1 and 5.")
        # Fail the job immediately if level is invalid
        db_fail = SessionLocal()
        try:
            job_fail = db_fail.query(Job).filter(Job.id == job_id).first()
            if job_fail:
                job_fail.fail(f"Invalid target level specified: {target_level}. Must be 1-5.")
                db_fail.commit()
        except Exception as db_err:
            logger.error("Failed to mark job as failed due to invalid target level", exc_info=db_err)
            db_fail.rollback()
        finally:
            db_fail.close()
        clear_all_context() # Clear context before returning
        return # Stop task execution

    # Initialize loop within the task context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    logger.debug(f"Created and set new asyncio event loop for job {job_id}")

    db = SessionLocal()
    job = None # Initialize job to None

    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            # Verify the target level matches the job record (optional sanity check)
            if job.target_level != target_level:
                logger.warning(f"Task received target_level {target_level} but job record has {job.target_level}. Using task value: {target_level}.")
                # Optionally update job record here if desired, or just proceed with task value

            # Ensure job type is CLASSIFICATION
            if job.job_type != JobType.CLASSIFICATION.value:
                 logger.error(f"process_vendor_file task called for a non-CLASSIFICATION job.", extra={"job_id": job_id, "job_type": job.job_type})
                 raise ValueError(f"Job {job_id} is not a CLASSIFICATION job.")


            set_log_context({
                "company_name": job.company_name,
                "creator": job.created_by,
                "file_name": job.input_file_name
                # target_level and job_type already set above
            })
            logger.info(f"Processing file for company",
                        extra={"company": job.company_name})
        else:
            logger.error("Job not found in database at start of task!", extra={"job_id": job_id})
            loop.close() # Close loop if job not found
            db.close() # Close db session
            clear_all_context() # Clear context before returning
            return # Exit task if job doesn't exist

        logger.info(f"About to run async processing for job {job_id}")
        with LogTimer(logger, "Complete file processing", level=logging.INFO, include_in_stats=True):
            # Run the async function within the loop created for this task
            # --- UPDATED: Pass target_level to async helper ---
            loop.run_until_complete(_process_vendor_file_async(job_id, file_path, db, target_level))
            # --- END UPDATED ---

        logger.info(f"Vendor file processing completed successfully (async part finished)")

    except Exception as e:
        logger.error(f"Error processing vendor file task (in main try block)", exc_info=True, extra={"job_id": job_id})
        try:
            # Re-query the job within this exception handler if it wasn't fetched initially or became None
            db_error_session = SessionLocal()
            try:
                job_in_error = db_error_session.query(Job).filter(Job.id == job_id).first()
                if job_in_error:
                    if job_in_error.status != JobStatus.COMPLETED.value:
                        err_msg = f"Task failed: {type(e).__name__}: {str(e)}"
                        job_in_error.fail(err_msg[:2000]) # Limit error message length
                        db_error_session.commit()
                        logger.info(f"Job status updated to failed due to task error",
                                    extra={"error": str(e)})
                    else:
                        logger.warning(f"Task error occurred after job was marked completed, status not changed.",
                                        extra={"error": str(e)})
                else:
                    logger.error("Job not found when trying to mark as failed.", extra={"job_id": job_id})
            except Exception as db_error:
                logger.error(f"Error updating job status during task failure handling", exc_info=True,
                            extra={"original_error": str(e), "db_error": str(db_error)})
                db_error_session.rollback()
            finally:
                    db_error_session.close()
        except Exception as final_db_error:
                logger.critical(f"CRITICAL: Failed even to handle database update in task error handler.", exc_info=final_db_error)

    finally:
        if db: # Close the main session used by the async function
            db.close()
            logger.debug(f"Main database session closed for task.")
        if loop and not loop.is_closed():
            loop.close()
            logger.debug(f"Event loop closed for task.")
        clear_all_context()
        logger.info(f"***** process_vendor_file TASK FINISHED (CLASSIFICATION) *****", extra={"job_id": job_id})


# --- UPDATED: Added target_level parameter ---
async def _process_vendor_file_async(job_id: str, file_path: str, db: Session, target_level: int):
# --- END UPDATED ---
    """
    Asynchronous part of the vendor file processing (CLASSIFICATION job type).
    Sets up services, initializes stats, calls the core processing logic,
    and handles final result generation and job status updates.
    """
    logger.info(f"[_process_vendor_file_async] Starting async processing for job {job_id} to target level {target_level}")

    llm_service = LLMService()
    search_service = SearchService()

    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        logger.error(f"[_process_vendor_file_async] Job not found in database", extra={"job_id": job_id})
        return

    # --- Initialize stats (Updated for L5) ---
    start_time = datetime.now()
    # --- MODIFIED: Type hints added ---
    stats: Dict[str, Any] = {
        "job_id": job.id,
        "company_name": job.company_name,
        "target_level": target_level, # Store target level in stats
        "start_time": start_time.isoformat(),
        "end_time": None,
        "processing_duration_seconds": None,
        "total_vendors": 0,
        "unique_vendors": 0,
        "successfully_classified_l4": 0, # Keep L4 count for reference
        "successfully_classified_l5": 0, # Count successful classifications reaching L5 (if target >= 5)
        "classification_not_possible_initial": 0, # Count initially unclassifiable before search
        "invalid_category_errors": 0, # Track validation errors
        "search_attempts": 0, # Count how many vendors needed search
        "search_successful_classifications_l1": 0, # Count successful L1 classifications *after* search
        "search_successful_classifications_l5": 0, # Count successful L5 classifications *after* search (if target >= 5)
        "api_usage": {
            "openrouter_calls": 0,
            "openrouter_prompt_tokens": 0,
            "openrouter_completion_tokens": 0,
            "openrouter_total_tokens": 0,
            "tavily_search_calls": 0,
            "cost_estimate_usd": 0.0
        }
    }
    # --- END MODIFIED ---
    # --- End Initialize stats ---

    # --- Initialize results dictionary ---
    # This will be populated by process_vendors
    results_dict: Dict[str, Dict] = {}
    # --- UPDATED: This will hold the processed results for DB storage (List[JobResultItem]) ---
    detailed_results_for_db: Optional[List[Dict[str, Any]]] = None
    # --- END UPDATED ---
    # --- End Initialize results dictionary ---

    try:
        job.status = JobStatus.PROCESSING.value
        job.current_stage = ProcessingStage.INGESTION.value
        job.progress = 0.05
        logger.info(f"[_process_vendor_file_async] Committing initial status update: {job.status}, {job.current_stage}, {job.progress}")
        db.commit()
        logger.info(f"Job status updated",
                    extra={"status": job.status, "stage": job.current_stage, "progress": job.progress})

        logger.info(f"Reading vendor file")
        with log_duration(logger, "Reading vendor file"):
            vendors_data = read_vendor_file(file_path)
        logger.info(f"Vendor file read successfully",
                    extra={"vendor_count": len(vendors_data)})

        job.current_stage = ProcessingStage.NORMALIZATION.value
        job.progress = 0.1
        logger.info(f"[_process_vendor_file_async] Committing status update: {job.status}, {job.current_stage}, {job.progress}")
        db.commit()
        logger.info(f"Job status updated",
                    extra={"stage": job.current_stage, "progress": job.progress})

        logger.info(f"Normalizing vendor data")
        with log_duration(logger, "Normalizing vendor data"):
            normalized_vendors_data = normalize_vendor_data(vendors_data)
        logger.info(f"Vendor data normalized",
                    extra={"normalized_count": len(normalized_vendors_data)})

        logger.info(f"Identifying unique vendors")
        # --- MODIFIED: Type hints added ---
        unique_vendors_map: Dict[str, Dict[str, Any]] = {}
        # --- END MODIFIED ---
        for entry in normalized_vendors_data:
            name = entry.get('vendor_name')
            if name and name not in unique_vendors_map:
                unique_vendors_map[name] = entry
        logger.info(f"Unique vendors identified",
                    extra={"unique_count": len(unique_vendors_map)})

        stats["total_vendors"] = len(normalized_vendors_data)
        stats["unique_vendors"] = len(unique_vendors_map)

        logger.info(f"Loading taxonomy")
        with log_duration(logger, "Loading taxonomy"):
            taxonomy = load_taxonomy() # Can raise exceptions
        logger.info(f"Taxonomy loaded",
                    extra={"taxonomy_version": taxonomy.version})

        # Initialize the results dict structure before passing to process_vendors
        results_dict = {vendor_name: {} for vendor_name in unique_vendors_map.keys()}

        logger.info(f"Starting vendor classification process by calling classification_logic.process_vendors up to Level {target_level}")
        # --- Call the refactored logic, passing target_level ---
        # process_vendors will populate the results_dict in place
        await process_vendors(
            unique_vendors_map=unique_vendors_map,
            taxonomy=taxonomy,
            results=results_dict, # Pass the dict to be populated
            stats=stats,
            job=job,
            db=db,
            llm_service=llm_service,
            search_service=search_service,
            target_level=target_level # Pass the target level
        )
        # --- End call to refactored logic ---
        logger.info(f"Vendor classification process completed (returned from classification_logic.process_vendors)")

        logger.info("Starting result generation phase.")

        job.current_stage = ProcessingStage.RESULT_GENERATION.value
        job.progress = 0.98 # Progress after all classification/search
        logger.info(f"[_process_vendor_file_async] Committing status update before result generation: {job.status}, {job.current_stage}, {job.progress}")
        db.commit()
        logger.info(f"Job status updated",
                    extra={"stage": job.current_stage, "progress": job.progress})

        output_file_name = None # Initialize

        # --- Process results for DB Storage ---
        try:
            logger.info("Processing detailed results for database storage.")
            with log_duration(logger, "Processing detailed results"):
                 # --- UPDATED: Call the preparation function ---
                 detailed_results_for_db = _prepare_detailed_results_for_storage(results_dict, target_level)
                 # --- END UPDATED ---
            logger.info(f"Processed {len(detailed_results_for_db)} items for detailed results storage.")
        except Exception as proc_err:
            logger.error("Failed during detailed results processing for DB", exc_info=True)
            # Continue to generate Excel, but log the error. The job won't store detailed results.
            detailed_results_for_db = None # Ensure it's None if processing failed
        # --- End Process results for DB Storage ---

        # --- Generate Excel File ---
        try:
                logger.info(f"Generating output file")
                with log_duration(logger, "Generating output file"):
                    # Pass the original complex results_dict to generate_output_file
                    # generate_output_file needs to be updated if its logic depends on the old flattened structure
                    # For now, assume it can handle the complex results_dict or adapt it internally
                    output_file_name = generate_output_file(normalized_vendors_data, results_dict, job_id)
                logger.info(f"Output file generated", extra={"output_file": output_file_name})
        except Exception as gen_err:
                logger.error("Failed during output file generation", exc_info=True)
                job.fail(f"Failed to generate output file: {str(gen_err)}")
                db.commit()
                return # Stop processing
        # --- End Generate Excel File ---

        # --- Finalize stats ---
        end_time = datetime.now()
        processing_duration = (end_time - datetime.fromisoformat(stats["start_time"])).total_seconds()
        stats["end_time"] = end_time.isoformat()
        stats["processing_duration_seconds"] = round(processing_duration, 2)
        # Cost calculation remains the same
        cost_input_per_1k = 0.0005
        cost_output_per_1k = 0.0015
        estimated_cost = (stats["api_usage"]["openrouter_prompt_tokens"] / 1000) * cost_input_per_1k + \
                            (stats["api_usage"]["openrouter_completion_tokens"] / 1000) * cost_output_per_1k
        estimated_cost += (stats["api_usage"]["tavily_search_calls"] / 1000) * 4.0
        stats["api_usage"]["cost_estimate_usd"] = round(estimated_cost, 4)
        # --- End Finalize stats ---

        # --- Final Commit Block ---
        try:
            logger.info("Attempting final job completion update in database.")
            # --- UPDATED: Pass the processed detailed_results_for_db to the complete method ---
            job.complete(output_file_name, stats, detailed_results_for_db)
            # --- END UPDATED ---
            job.progress = 1.0 # Ensure progress is 1.0 on completion
            logger.info(f"[_process_vendor_file_async] Committing final job completion status.")
            db.commit()
            logger.info(f"Job completed successfully",
                        extra={
                            "processing_duration": processing_duration,
                            "output_file": output_file_name,
                            "target_level": target_level,
                            # --- UPDATED: Log if detailed results were stored ---
                            "detailed_results_stored": bool(detailed_results_for_db),
                            "detailed_results_count": len(detailed_results_for_db) if detailed_results_for_db else 0,
                            # --- END UPDATED ---
                            "openrouter_calls": stats["api_usage"]["openrouter_calls"],
                            "tokens_used": stats["api_usage"]["openrouter_total_tokens"],
                            "tavily_calls": stats["api_usage"]["tavily_search_calls"],
                            "estimated_cost": stats["api_usage"]["cost_estimate_usd"],
                            "invalid_category_errors": stats.get("invalid_category_errors", 0),
                            "successfully_classified_l5_total": stats.get("successfully_classified_l5", 0)
                        })
        except Exception as final_commit_err:
            logger.error("CRITICAL: Failed to commit final job completion status!", exc_info=True)
            db.rollback()
            try:
                # Re-fetch job in new session to attempt marking as failed
                db_fail_final = SessionLocal()
                job_fail_final = db_fail_final.query(Job).filter(Job.id == job_id).first()
                if job_fail_final:
                    err_msg = f"Failed during final commit: {type(final_commit_err).__name__}: {str(final_commit_err)}"
                    job_fail_final.fail(err_msg[:2000])
                    db_fail_final.commit()
                else:
                    logger.error("Job not found when trying to mark as failed after final commit error.")
                db_fail_final.close()
            except Exception as fail_err:
                logger.error("CRITICAL: Also failed to mark job as failed after final commit error.", exc_info=fail_err)
                # db.rollback() # Already rolled back original session
        # --- End Final Commit Block ---

    except (ValueError, FileNotFoundError, IOError) as file_err:
        logger.error(f"[_process_vendor_file_async] File reading or writing error", exc_info=True,
                    extra={"error": str(file_err)})
        if job:
            err_msg = f"File processing error: {type(file_err).__name__}: {str(file_err)}"
            job.fail(err_msg[:2000])
            db.commit()
        else:
            logger.error("Job object was None during file error handling.")
    except SQLAlchemyError as db_err:
        logger.error(f"[_process_vendor_file_async] Database error during processing", exc_info=True,
                    extra={"error": str(db_err)})
        db.rollback() # Rollback on DB error
        if job:
            # Re-fetch job in new session to attempt marking as failed
            db_fail_db = SessionLocal()
            job_fail_db = db_fail_db.query(Job).filter(Job.id == job_id).first()
            if job_fail_db and job_fail_db.status not in [JobStatus.FAILED.value, JobStatus.COMPLETED.value]:
                    err_msg = f"Database error: {type(db_err).__name__}: {str(db_err)}"
                    job_fail_db.fail(err_msg[:2000])
                    db_fail_db.commit()
            elif job_fail_db:
                    logger.warning(f"Database error occurred but job status was already {job_fail_db.status}. Error: {db_err}")
            else:
                logger.error("Job not found when trying to mark as failed after database error.")
            db_fail_db.close()
        else:
            logger.error("Job object was None during database error handling.")
    except Exception as async_err:
        logger.error(f"[_process_vendor_file_async] Unexpected error during async processing", exc_info=True,
                    extra={"error": str(async_err)})
        db.rollback() # Rollback on unexpected error
        if job:
            # Re-fetch job in new session to attempt marking as failed
            db_fail_unexpected = SessionLocal()
            job_fail_unexpected = db_fail_unexpected.query(Job).filter(Job.id == job_id).first()
            if job_fail_unexpected and job_fail_unexpected.status not in [JobStatus.FAILED.value, JobStatus.COMPLETED.value]:
                err_msg = f"Unexpected error: {type(async_err).__name__}: {str(async_err)}"
                job_fail_unexpected.fail(err_msg[:2000])
                db_fail_unexpected.commit()
            elif job_fail_unexpected:
                logger.warning(f"Unexpected error occurred but job status was already {job_fail_unexpected.status}. Error: {async_err}")
            else:
                logger.error("Job not found when trying to mark as failed after unexpected error.")
            db_fail_unexpected.close()
        else:
            logger.error("Job object was None during unexpected error handling.")
    finally:
        logger.info(f"[_process_vendor_file_async] Finished async processing for job {job_id}")


# --- ADDED: Reclassification Task ---
@shared_task(bind=True)
def reclassify_flagged_vendors_task(self, review_job_id: str):
    """
    Celery task entry point for re-classifying flagged vendors (REVIEW job type).
    Orchestrates the reclassification process.

    Args:
        review_job_id: The ID of the REVIEW job.
    """
    task_id = self.request.id if self.request and self.request.id else "UnknownTaskID"
    logger.info(f"***** reclassify_flagged_vendors_task TASK RECEIVED *****",
                extra={"celery_task_id": task_id, "review_job_id": review_job_id})

    set_correlation_id(review_job_id) # Use review job ID as correlation ID
    set_job_id(review_job_id)
    set_log_context({"job_type": JobType.REVIEW.value})
    logger.info(f"Starting reclassification task", extra={"review_job_id": review_job_id})

    # Initialize loop within the task context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    logger.debug(f"Created and set new asyncio event loop for review job {review_job_id}")

    db = SessionLocal()
    review_job = None

    try:
        review_job = db.query(Job).filter(Job.id == review_job_id).first()
        if not review_job:
            logger.error("Review job not found in database at start of task!", extra={"review_job_id": review_job_id})
            raise ValueError("Review job not found.")

        # Ensure job type is REVIEW
        if review_job.job_type != JobType.REVIEW.value:
            logger.error(f"reclassify_flagged_vendors_task called for a non-REVIEW job.", extra={"review_job_id": review_job_id, "job_type": review_job.job_type})
            raise ValueError(f"Job {review_job_id} is not a REVIEW job.")

        set_log_context({
            "company_name": review_job.company_name,
            "creator": review_job.created_by,
            "parent_job_id": review_job.parent_job_id
        })
        logger.info(f"Processing review for company", extra={"company": review_job.company_name})

        # --- Call the async reclassification logic ---
        logger.info(f"About to run async reclassification processing for review job {review_job_id}")
        with LogTimer(logger, "Complete reclassification processing", level=logging.INFO, include_in_stats=True):
            loop.run_until_complete(_process_reclassification_async(review_job_id, db))

        logger.info(f"Reclassification processing completed successfully (async part finished)")

    except Exception as e:
        logger.error(f"Error processing reclassification task", exc_info=True, extra={"review_job_id": review_job_id})
        try:
            # Re-query the job within this exception handler
            db_error_session = SessionLocal()
            try:
                job_in_error = db_error_session.query(Job).filter(Job.id == review_job_id).first()
                if job_in_error:
                    if job_in_error.status != JobStatus.COMPLETED.value:
                        err_msg = f"Reclassification task failed: {type(e).__name__}: {str(e)}"
                        job_in_error.fail(err_msg[:2000])
                        db_error_session.commit()
                        logger.info(f"Review job status updated to failed due to task error", extra={"error": str(e)})
                    else:
                        logger.warning(f"Task error occurred after review job was marked completed, status not changed.", extra={"error": str(e)})
                else:
                    logger.error("Review job not found when trying to mark as failed.", extra={"review_job_id": review_job_id})
            except Exception as db_error:
                logger.error(f"Error updating review job status during task failure handling", exc_info=True,
                            extra={"original_error": str(e), "db_error": str(db_error)})
                db_error_session.rollback()
            finally:
                db_error_session.close()
        except Exception as final_db_error:
            logger.critical(f"CRITICAL: Failed even to handle database update in reclassification task error handler.", exc_info=final_db_error)

    finally:
        if db:
            db.close()
            logger.debug(f"Main database session closed for reclassification task.")
        if loop and not loop.is_closed():
            loop.close()
            logger.debug(f"Event loop closed for reclassification task.")
        clear_all_context()
        logger.info(f"***** reclassify_flagged_vendors_task TASK FINISHED *****", extra={"review_job_id": review_job_id})


async def _process_reclassification_async(review_job_id: str, db: Session):
    """
    Asynchronous part of the reclassification task.
    Sets up services, calls the core reclassification logic, stores results.
    """
    logger.info(f"[_process_reclassification_async] Starting async processing for review job {review_job_id}")

    llm_service = LLMService()
    # search_service is not needed for reclassification

    review_job = db.query(Job).filter(Job.id == review_job_id).first()
    if not review_job:
        logger.error(f"[_process_reclassification_async] Review job not found in database", extra={"review_job_id": review_job_id})
        return

    # Import the core logic function here to avoid circular imports at module level
    from .reclassification_logic import process_reclassification

    review_results_list = None
    final_stats = {}

    try:
        review_job.status = JobStatus.PROCESSING.value
        review_job.current_stage = ProcessingStage.RECLASSIFICATION.value
        review_job.progress = 0.1 # Start progress
        logger.info(f"[_process_reclassification_async] Committing initial status update: {review_job.status}, {review_job.current_stage}, {review_job.progress}")
        db.commit()
        logger.info(f"Review job status updated",
                    extra={"status": review_job.status, "stage": review_job.current_stage, "progress": review_job.progress})

        # --- Call the reclassification logic ---
        # This function will handle fetching parent data, calling LLM, etc.
        review_results_list, final_stats = await process_reclassification(
            review_job=review_job,
            db=db,
            llm_service=llm_service
        )
        # --- End call ---

        logger.info(f"Reclassification logic completed. Processed {final_stats.get('total_items_processed', 0)} items.")
        review_job.progress = 0.95 # Mark logic as complete

        # --- Final Commit Block ---
        try:
            logger.info("Attempting final review job completion update in database.")
            # Pass None for output_file_name as review jobs don't generate one
            review_job.complete(output_file_name=None, stats=final_stats, detailed_results=review_results_list)
            review_job.progress = 1.0
            logger.info(f"[_process_reclassification_async] Committing final review job completion status.")
            db.commit()
            logger.info(f"Review job completed successfully",
                        extra={
                            "processing_duration": final_stats.get("processing_duration_seconds"),
                            "items_processed": final_stats.get("total_items_processed"),
                            "successful": final_stats.get("successful_reclassifications"),
                            "failed": final_stats.get("failed_reclassifications"),
                            "openrouter_calls": final_stats.get("api_usage", {}).get("openrouter_calls"),
                            "tokens_used": final_stats.get("api_usage", {}).get("openrouter_total_tokens"),
                            "estimated_cost": final_stats.get("api_usage", {}).get("cost_estimate_usd")
                        })
        except Exception as final_commit_err:
            logger.error("CRITICAL: Failed to commit final review job completion status!", exc_info=True)
            db.rollback()
            # Attempt to mark as failed (similar logic as in main task handler)
            try:
                db_fail_final = SessionLocal()
                job_fail_final = db_fail_final.query(Job).filter(Job.id == review_job_id).first()
                if job_fail_final:
                    err_msg = f"Failed during final commit: {type(final_commit_err).__name__}: {str(final_commit_err)}"
                    job_fail_final.fail(err_msg[:2000])
                    db_fail_final.commit()
                db_fail_final.close()
            except Exception as fail_err:
                logger.error("CRITICAL: Also failed to mark review job as failed after final commit error.", exc_info=fail_err)
        # --- End Final Commit Block ---

    # Handle specific errors from process_reclassification or other issues
    except (ValueError, FileNotFoundError) as logic_err:
        logger.error(f"[_process_reclassification_async] Data or File error during reclassification logic", exc_info=True,
                    extra={"error": str(logic_err)})
        if review_job:
            err_msg = f"Reclassification data error: {type(logic_err).__name__}: {str(logic_err)}"
            review_job.fail(err_msg[:2000])
            db.commit()
    except SQLAlchemyError as db_err:
         logger.error(f"[_process_reclassification_async] Database error during reclassification processing", exc_info=True,
                     extra={"error": str(db_err)})
         db.rollback()
         # Attempt to mark as failed (similar logic as in main task handler)
         try:
            db_fail_db = SessionLocal()
            job_fail_db = db_fail_db.query(Job).filter(Job.id == review_job_id).first()
            if job_fail_db and job_fail_db.status not in [JobStatus.FAILED.value, JobStatus.COMPLETED.value]:
                 err_msg = f"Database error: {type(db_err).__name__}: {str(db_err)}"
                 job_fail_db.fail(err_msg[:2000])
                 db_fail_db.commit()
            db_fail_db.close()
         except Exception as fail_err:
            logger.error("CRITICAL: Also failed to mark review job as failed after database error.", exc_info=fail_err)

    except Exception as async_err:
        logger.error(f"[_process_reclassification_async] Unexpected error during async reclassification processing", exc_info=True,
                    extra={"error": str(async_err)})
        db.rollback()
        # Attempt to mark as failed (similar logic as in main task handler)
        try:
            db_fail_unexpected = SessionLocal()
            job_fail_unexpected = db_fail_unexpected.query(Job).filter(Job.id == review_job_id).first()
            if job_fail_unexpected and job_fail_unexpected.status not in [JobStatus.FAILED.value, JobStatus.COMPLETED.value]:
                err_msg = f"Unexpected error: {type(async_err).__name__}: {str(async_err)}"
                job_fail_unexpected.fail(err_msg[:2000])
                db_fail_unexpected.commit()
            db_fail_unexpected.close()
        except Exception as fail_err:
            logger.error("CRITICAL: Also failed to mark review job as failed after unexpected error.", exc_info=fail_err)
    finally:
        logger.info(f"[_process_reclassification_async] Finished async processing for review job {review_job_id}")

# --- END ADDED ---
```
</file>

<file path='app/tasks/celery_app.py'>
```python

# app/tasks/celery_app.py
from celery import Celery
import logging
import sys
import os

# Attempt initial logging setup
try:
    from core.logging_config import setup_logging
    log_dir_worker = "/data/logs" if os.path.exists("/data") else "./logs_worker"
    os.makedirs(log_dir_worker, exist_ok=True)
    print(f"WORKER: Attempting initial logging setup to {log_dir_worker}")
    setup_logging(log_to_file=True, log_dir=log_dir_worker, async_logging=False, llm_trace_log_file="llm_api_trace_worker.log")
    print("WORKER: Initial logging setup attempted.")
except Exception as setup_err:
    print(f"WORKER: CRITICAL ERROR during initial logging setup: {setup_err}")
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Import logger *after* setup attempt
from core.logging_config import get_logger
# Import context functions from the new module
from core.log_context import set_correlation_id, set_job_id, clear_all_context

# Use direct signal imports from celery.signals
from celery.signals import task_prerun, task_postrun, task_failure

logger = get_logger("vendor_classification.celery")

# Log diagnostic information
logger.info(
    f"Initializing Celery app",
    extra={
        "python_executable": sys.executable,
        "python_version": sys.version,
        "python_path": sys.path,
        "cwd": os.getcwd()
    }
)

try:
    from core.config import settings
    logger.info("Successfully imported settings")
except Exception as e:
    logger.error("Error importing settings", exc_info=True)
    raise

# Create Celery app
logger.info("Creating Celery app")
try:
    celery_app = Celery(
        "vendor_classification",
        broker=settings.REDIS_URL,
        backend=settings.REDIS_URL
    )
    logger.info("Celery app created", extra={"broker": settings.REDIS_URL})

    # Configure Celery
    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_send_sent_event=True,
    )
    logger.info("Celery configuration updated")

    # Signal Handlers
    logger.info("Connecting Celery signal handlers...")

    @task_prerun.connect
    def handle_task_prerun(task_id, task, args, kwargs, **extra_options):
        """Signal handler before task runs."""
        clear_all_context() # Clear any lingering context
        # Determine job_id based on common kwargs patterns
        job_id = kwargs.get('job_id') or kwargs.get('review_job_id') or (args[0] if args else None) or task_id
        set_correlation_id(job_id) # Use job_id as correlation_id
        set_job_id(job_id)
        logger.info(
            "Task about to run",
            extra={
                "signal": "task_prerun",
                "task_id": task_id,
                "task_name": task.name,
                "args": args,
                "kwargs": kwargs
            }
        )

    @task_postrun.connect
    def handle_task_postrun(task_id, task, args, kwargs, retval, state, **extra_options):
        """Signal handler after task completes."""
        logger.info(
            "Task finished running",
            extra={
                "signal": "task_postrun",
                "task_id": task_id,
                "task_name": task.name,
                "retval": repr(retval)[:200],
                "final_state": state
            }
        )
        clear_all_context() # Clean up context

    @task_failure.connect
    def handle_task_failure(task_id, exception, args, kwargs, traceback, einfo, **extra_options):
        """Signal handler if task fails."""
        task_name = getattr(kwargs.get('task'), 'name', None) or getattr(einfo, 'task', {}).get('name', 'UnknownTask')
        logger.error(
            "Task failed",
            exc_info=(type(exception), exception, traceback),
            extra={
                "signal": "task_failure",
                "task_id": task_id,
                "task_name": task_name,
                "args": args,
                "kwargs": kwargs,
                "exception_type": type(exception).__name__,
                "error": str(exception),
                "einfo": str(einfo)[:1000] if einfo else None
            }
        )
        clear_all_context() # Clean up context

    logger.info("Celery signal handlers connected.")

except Exception as e:
    logger.error("Error creating or configuring Celery app", exc_info=True)
    raise

# Import tasks to register them
logger.info("Attempting to import tasks for registration...")
try:
    # Import original classification task
    from tasks.classification_tasks import process_vendor_file
    logger.info("Successfully imported 'tasks.classification_tasks.process_vendor_file'")
    # --- ADDED: Import reclassification task ---
    from tasks.reclassification_tasks import reclassify_flagged_vendors_task
    logger.info("Successfully imported 'tasks.reclassification_tasks.reclassify_flagged_vendors_task'")
    # --- END ADDED ---
except ImportError as e:
    logger.error("ImportError when importing tasks", exc_info=True)
    logger.error(f"sys.path during task import: {sys.path}")
    raise
except Exception as e:
    logger.error("Unexpected error importing tasks", exc_info=True)
    raise

# Log discovered tasks
logger.info(f"Tasks registered in Celery app: {list(celery_app.tasks.keys())}")

logger.info("Celery app initialization finished.")

if __name__ == "__main__":
    logger.warning("celery_app.py run directly (likely for testing/debugging)")

```
</file>

**Note on `llm_service.py`:** The current implementation assumes `classify_batch` can be used for re-classification by passing a custom prompt. This might require modification to `classify_batch` or `generate_batch_prompt` to accept raw message payloads, or the creation of a new, more flexible method in `LLMService` specifically for single-item, custom-prompt classifications. For this iteration, we'll assume the placeholder call within `reclassification_logic.py` works, but this is a key area for refinement.

---

**Frontend Changes**

<file path='frontend/vue_frontend/src/stores/job.ts'>
```typescript
// <file path='frontend/vue_frontend/src/stores/job.ts'>
import { defineStore } from 'pinia';
import { ref, reactive, computed } from 'vue'; // <<< Added reactive, computed
import apiService, { type JobResponse, type JobResultsResponse } from '@/services/api'; // Import JobResponse type

// Define the structure of the job details object based on your API response
// Should align with app/schemas/job.py -> JobResponse
export interface JobDetails {
    id: string; // Changed from job_id to match JobResponse schema
    status: 'pending' | 'processing' | 'completed' | 'failed';
    progress: number;
    current_stage: string; // Consider using specific stage literals if known
    created_at: string | null; // Use string for ISO date
    updated_at: string | null; // Use string for ISO date
    completed_at?: string | null; // Optional completion time
    estimated_completion?: string | null; // Added optional field (backend doesn't provide this explicitly yet)
    error_message: string | null;
    target_level: number; // ADDED: Ensure target_level is part of the details
    company_name?: string;
    input_file_name?: string;
    output_file_name?: string | null;
    created_by?: string;
    // --- ADDED: Job Type and Parent Link ---
    job_type: 'CLASSIFICATION' | 'REVIEW';
    parent_job_id: string | null;
    // --- END ADDED ---
}

// --- UPDATED: Interface for a single detailed result item (for CLASSIFICATION jobs) ---
// Should align with app/schemas/job.py -> JobResultItem
export interface JobResultItem {
    vendor_name: string;
    level1_id: string | null;
    level1_name: string | null;
    level2_id: string | null;
    level2_name: string | null;
    level3_id: string | null;
    level3_name: string | null;
    level4_id: string | null;
    level4_name: string | null;
    level5_id: string | null;
    level5_name: string | null;
    final_confidence: number | null;
    final_status: string; // 'Classified', 'Not Possible', 'Error'
    classification_source: string | null; // 'Initial', 'Search', 'Review'
    classification_notes_or_reason: string | null;
    achieved_level: number | null; // 0-5
}
// --- END UPDATED ---

// --- ADDED: Interface for a single detailed result item (for REVIEW jobs) ---
// Should align with app/schemas/review.py -> ReviewResultItem
export interface ReviewResultItem {
    vendor_name: string;
    hint: string;
    // Store the original result (as a dict matching JobResultItem)
    original_result: JobResultItem; // Use JobResultItem type for structure
    // Store the new result (as a dict matching JobResultItem)
    new_result: JobResultItem; // Use JobResultItem type for structure
}
// --- END ADDED ---


export const useJobStore = defineStore('job', () => {
    // --- State ---
    const currentJobId = ref<string | null>(null);
    const jobDetails = ref<JobDetails | null>(null);
    const isLoading = ref(false); // For tracking polling/loading state for CURRENT job
    const error = ref<string | null>(null); // For storing errors related to fetching CURRENT job status

    // --- ADDED: Job History State ---
    const jobHistory = ref<JobResponse[]>([]);
    const historyLoading = ref(false);
    const historyError = ref<string | null>(null);
    // --- END ADDED ---

    // --- ADDED: Detailed Job Results State ---
    // Use Union type to hold either result type
    const jobResults = ref<JobResultItem[] | ReviewResultItem[] | null>(null);
    const resultsLoading = ref(false);
    const resultsError = ref<string | null>(null);
    // --- END ADDED ---

    // --- ADDED: Reclassification State ---
    // Map vendor name to its flagged state and hint
    const flaggedForReview = reactive<Map<string, { hint: string | null }>>(new Map());
    const reclassifyLoading = ref(false);
    const reclassifyError = ref<string | null>(null);
    const lastReviewJobId = ref<string | null>(null); // Store ID of the last created review job
    // --- END ADDED ---

    // --- Computed ---
    const hasFlaggedItems = computed(() => flaggedForReview.size > 0);

    // --- Actions ---
    function setCurrentJobId(jobId: string | null): void {
        console.log(`JobStore: Setting currentJobId from '${currentJobId.value}' to '${jobId}'`); // LOGGING
        if (currentJobId.value !== jobId) {
            currentJobId.value = jobId;
            // Clear details when ID changes (to null or a new ID) to force refresh
            jobDetails.value = null;
            console.log(`JobStore: Cleared jobDetails due to ID change.`); // LOGGING
            error.value = null; // Clear errors
            isLoading.value = false; // Reset loading state
            // --- ADDED: Clear detailed results when job changes ---
            jobResults.value = null;
            resultsLoading.value = false;
            resultsError.value = null;
            console.log(`JobStore: Cleared detailed jobResults due to ID change.`); // LOGGING
            // --- END ADDED ---
            // --- ADDED: Clear flagging state when job changes ---
            flaggedForReview.clear();
            reclassifyLoading.value = false;
            reclassifyError.value = null;
            lastReviewJobId.value = null;
            console.log(`JobStore: Cleared flagging state due to ID change.`); // LOGGING
            // --- END ADDED ---

            // Update URL to reflect the current job ID or clear it
            try {
                 const url = new URL(window.location.href);
                 if (jobId) {
                     url.searchParams.set('job_id', jobId);
                     console.log(`JobStore: Updated URL searchParam 'job_id' to ${jobId}`); // LOGGING
                 } else {
                     url.searchParams.delete('job_id');
                     console.log(`JobStore: Removed 'job_id' from URL searchParams.`); // LOGGING
                 }
                 // Use replaceState to avoid polluting history
                 window.history.replaceState({}, '', url.toString());
            } catch (e) {
                 console.error("JobStore: Failed to update URL:", e);
            }
        }
         // If the same job ID is set again, force a refresh of details
         else if (jobId !== null) {
             console.log(`JobStore: Re-setting same job ID ${jobId}, clearing details and results to force refresh.`); // LOGGING
             jobDetails.value = null;
             error.value = null;
             isLoading.value = false;
             // --- ADDED: Clear detailed results on re-select too ---
             jobResults.value = null;
             resultsLoading.value = false;
             resultsError.value = null;
             // --- END ADDED ---
             // --- ADDED: Clear flagging state on re-select too ---
             flaggedForReview.clear();
             reclassifyLoading.value = false;
             reclassifyError.value = null;
             lastReviewJobId.value = null;
             // --- END ADDED ---
         }
    }

    function updateJobDetails(details: JobDetails): void {
        // Only update if the details are for the currently tracked job
        if (details && details.id === currentJobId.value) { // Match 'id' field from JobResponse/JobDetails
            // LOGGING: Include target_level in log
            console.log(`JobStore: Updating jobDetails for ${currentJobId.value} with status ${details.status}, progress ${details.progress}, target_level ${details.target_level}, job_type ${details.job_type}`);
            jobDetails.value = { ...details }; // Create new object for reactivity
            error.value = null; // Clear error on successful update
        } else if (details) {
            console.warn(`JobStore: Received details for job ${details.id}, but currently tracking ${currentJobId.value}. Ignoring update.`); // LOGGING
        } else {
            console.warn(`JobStore: updateJobDetails called with invalid details object.`); // LOGGING
        }
    }

    function setLoading(loading: boolean): void {
        isLoading.value = loading;
    }

    function setError(errorMessage: string | null): void {
        error.value = errorMessage;
    }

    function clearJob(): void {
        console.log('JobStore: Clearing job state.'); // LOGGING
        setCurrentJobId(null); // This also clears details, error, loading, results and URL param
        // --- ADDED: Clear history too on full clear? Optional. ---
        // jobHistory.value = [];
        // historyLoading.value = false;
        // historyError.value = null;
        // --- END ADDED ---
    }

    // --- ADDED: Job History Actions ---
    async function fetchJobHistory(params = {}): Promise<void> {
        console.log('JobStore: Fetching job history with params:', params); // LOGGING
        historyLoading.value = true;
        historyError.value = null;
        try {
            const jobs = await apiService.getJobs(params);
            jobHistory.value = jobs;
            console.log(`JobStore: Fetched ${jobs.length} jobs.`); // LOGGING
        } catch (err: any) {
            console.error('JobStore: Failed to fetch job history:', err); // LOGGING
            historyError.value = err.message || 'Failed to load job history.';
            jobHistory.value = []; // Clear history on error
        } finally {
            historyLoading.value = false;
        }
    }
    // --- END ADDED ---

    // --- ADDED: Detailed Job Results Actions ---
    async function fetchJobResults(jobId: string): Promise<void> {
        // Only fetch if the jobId matches the current job
        if (jobId !== currentJobId.value) {
            console.log(`JobStore: fetchJobResults called for ${jobId}, but current job is ${currentJobId.value}. Skipping.`);
            return;
        }
        // Avoid redundant fetches if already loading
        if (resultsLoading.value) {
             console.log(`JobStore: fetchJobResults called for ${jobId}, but already loading. Skipping.`);
             return;
        }

        console.log(`JobStore: Fetching detailed results for job ${jobId}...`);
        resultsLoading.value = true;
        resultsError.value = null;
        jobResults.value = null; // Clear previous results before fetching
        try {
            // API now returns { job_id, job_type, results: [...] }
            const response: JobResultsResponse = await apiService.getJobResults(jobId);
            // Double-check the job ID hasn't changed *during* the API call
            if (jobId === currentJobId.value) {
                // Store the results array. The type (JobResultItem[] or ReviewResultItem[])
                // is implicitly handled by the Union type and determined by job_type.
                jobResults.value = response.results;
                // Update jobDetails with the job_type from the response if needed
                if (jobDetails.value && jobDetails.value.job_type !== response.job_type) {
                    console.log(`JobStore: Updating job_type in details from results response for ${jobId}`);
                    jobDetails.value.job_type = response.job_type;
                }
                console.log(`JobStore: Successfully fetched ${response.results.length} detailed results for ${jobId} (Type: ${response.job_type}).`);
            } else {
                 console.log(`JobStore: Job ID changed while fetching results for ${jobId}. Discarding fetched results.`);
            }
        } catch (err: any) {
            console.error(`JobStore: Failed to fetch detailed results for ${jobId}:`, err);
            // Only set error if it's for the currently selected job
            if (jobId === currentJobId.value) {
                resultsError.value = err.message || 'Failed to load detailed results.';
                jobResults.value = null; // Clear results on error
            }
        } finally {
             // Only stop loading if it's for the currently selected job
            if (jobId === currentJobId.value) {
                resultsLoading.value = false;
            }
        }
    }
    // --- END ADDED ---

    // --- ADDED: Reclassification Actions ---
    function isFlagged(vendorName: string): boolean {
        return flaggedForReview.has(vendorName);
    }

    function getHint(vendorName: string): string | null {
        return flaggedForReview.get(vendorName)?.hint ?? null;
    }

    function flagVendor(vendorName: string): void {
        if (!flaggedForReview.has(vendorName)) {
            flaggedForReview.set(vendorName, { hint: null });
            console.log(`JobStore: Flagged vendor '${vendorName}' for review.`);
        }
    }

    function unflagVendor(vendorName: string): void {
        if (flaggedForReview.has(vendorName)) {
            flaggedForReview.delete(vendorName);
            console.log(`JobStore: Unflagged vendor '${vendorName}'.`);
        }
    }

    function setHint(vendorName: string, hint: string | null): void {
        if (flaggedForReview.has(vendorName)) {
            flaggedForReview.set(vendorName, { hint });
            console.log(`JobStore: Set hint for '${vendorName}': ${hint ? `'${hint}'` : 'cleared'}`);
        } else {
            console.warn(`JobStore: Tried to set hint for unflagged vendor '${vendorName}'.`);
        }
    }

    async function submitFlagsForReview(): Promise<string | null> {
        const originalJobId = currentJobId.value;
        if (!originalJobId || flaggedForReview.size === 0) {
            console.warn("JobStore: submitFlagsForReview called with no job ID or no flagged items.");
            reclassifyError.value = "No items flagged for review.";
            return null;
        }

        const itemsToReclassify = Array.from(flaggedForReview.entries())
            .filter(([_, data]) => data.hint && data.hint.trim() !== '') // Only submit items with a non-empty hint
            .map(([vendorName, data]) => ({
                vendor_name: vendorName,
                hint: data.hint!, // Assert non-null because we filtered
            }));

        if (itemsToReclassify.length === 0) {
            console.warn("JobStore: submitFlagsForReview called, but no flagged items have valid hints.");
            reclassifyError.value = "Please provide hints for the flagged items before submitting.";
            // Clear flags that have no hint? Maybe not, let user clear them.
            return null;
        }


        console.log(`JobStore: Submitting ${itemsToReclassify.length} flags for reclassification for job ${originalJobId}...`);
        reclassifyLoading.value = true;
        reclassifyError.value = null;
        lastReviewJobId.value = null;

        try {
            const response = await apiService.reclassifyJob(originalJobId, itemsToReclassify);
            console.log(`JobStore: Reclassification job started successfully. Review Job ID: ${response.review_job_id}`);
            lastReviewJobId.value = response.review_job_id;
            // Clear the flags after successful submission
            flaggedForReview.clear();
            // Optionally: Fetch job history again to show the new PENDING review job
            // await fetchJobHistory();
            // Optionally: Navigate to the new review job? Or just show a success message.
            // setCurrentJobId(response.review_job_id); // This would switch view immediately
            return response.review_job_id; // Return the new job ID for potential navigation
        } catch (err: any) {
            console.error('JobStore: Failed to submit flags for reclassification:', err);
            reclassifyError.value = err.message || 'Failed to start reclassification job.';
            return null;
        } finally {
            reclassifyLoading.value = false;
        }
    }
    // --- END ADDED ---


    return {
        currentJobId,
        jobDetails,
        isLoading,
        error,
        // History state & actions
        jobHistory,
        historyLoading,
        historyError,
        fetchJobHistory,
        // Detailed Results state & actions
        jobResults, // Can be JobResultItem[] or ReviewResultItem[]
        resultsLoading,
        resultsError,
        fetchJobResults,
        // Reclassification state & actions
        flaggedForReview,
        reclassifyLoading,
        reclassifyError,
        lastReviewJobId,
        hasFlaggedItems,
        isFlagged,
        getHint,
        flagVendor,
        unflagVendor,
        setHint,
        submitFlagsForReview,
        // Existing actions
        setCurrentJobId,
        updateJobDetails,
        setLoading,
        setError,
        clearJob,
    };
});

```
</file>

<file path='frontend/vue_frontend/src/services/api.ts'>
```typescript
import axios, {
    type AxiosInstance,
    type InternalAxiosRequestConfig,
    type AxiosError // Import AxiosError type
} from 'axios';
import { useAuthStore } from '@/stores/auth'; // Adjust path as needed
// --- UPDATED: Import JobResultItem and ReviewResultItem ---
import type { JobDetails, JobResultItem, ReviewResultItem } from '@/stores/job'; // Adjust path as needed
// --- END UPDATED ---

// --- Define API Response Interfaces ---

// Matches backend schemas/user.py -> UserResponse
export interface UserResponse {
    email: string;
    full_name: string | null;
    is_active: boolean | null;
    is_superuser: boolean | null;
    username: string;
    id: string; // UUID as string
    created_at: string; // ISO Date string
    updated_at: string; // ISO Date string
}

// Matches backend schemas/user.py -> UserCreate (for request body)
export interface UserCreateData {
    email: string;
    full_name?: string | null;
    is_active?: boolean | null;
    is_superuser?: boolean | null;
    username: string;
    password?: string; // Password required on create
}

// Matches backend schemas/user.py -> UserUpdate (for request body)
export interface UserUpdateData {
    email?: string | null;
    full_name?: string | null;
    password?: string | null; // Optional password update
    is_active?: boolean | null;
    is_superuser?: boolean | null;
}


// Matches backend response for /token (modified to include user object)
interface AuthResponse {
    access_token: string;
    token_type: string;
    user: UserResponse; // Include the user details
}

// --- ADDED: File Validation Response Interface ---
// Matches backend api/main.py -> FileValidationResponse
export interface FileValidationResponse {
    is_valid: boolean;
    message: string;
    detected_columns: string[];
    missing_mandatory_columns: string[];
}
// --- END ADDED ---

// Matches backend response for /api/v1/jobs/{job_id}/notify
interface NotifyResponse {
    success: boolean;
    message: string;
}

// Matches backend response for /api/v1/jobs/ (list endpoint)
// Should align with app/schemas/job.py -> JobResponse
export interface JobResponse {
    id: string;
    company_name: string;
    status: 'pending' | 'processing' | 'completed' | 'failed';
    progress: number;
    current_stage: string;
    created_at: string; // ISO Date string
    updated_at?: string | null;
    completed_at?: string | null;
    output_file_name?: string | null;
    input_file_name: string;
    created_by: string;
    error_message?: string | null;
    target_level: number; // Ensure target_level is included here
    // --- ADDED: Job Type and Parent Link ---
    job_type: 'CLASSIFICATION' | 'REVIEW';
    parent_job_id: string | null;
    // --- END ADDED ---
}

// --- ADDED: Job Results Response Interface ---
// Matches backend schemas/job.py -> JobResultsResponse
export interface JobResultsResponse {
    job_id: string;
    job_type: 'CLASSIFICATION' | 'REVIEW';
    results: JobResultItem[] | ReviewResultItem[]; // Union type
}
// --- END ADDED ---


// Matches backend models/classification.py -> ProcessingStats and console log
export interface JobStatsData {
    job_id: string;
    company_name: string;
    start_time: string | null; // Assuming ISO string
    end_time: string | null; // Assuming ISO string
    processing_duration_seconds: number | null; // Renamed from processing_time
    total_vendors: number | null; // Added
    unique_vendors: number | null; // Added (was present in console)
    target_level: number | null; // Added target level to stats
    successfully_classified_l4: number | null; // Keep for reference
    successfully_classified_l5: number | null; // Keep L5 count
    classification_not_possible_initial: number | null; // Added
    invalid_category_errors: number | null; // Added (was present in console)
    search_attempts: number | null; // Added
    search_successful_classifications_l1: number | null; // Added
    search_successful_classifications_l5: number | null; // Renamed from search_assisted_l5
    api_usage: { // Nested structure
        openrouter_calls: number | null;
        openrouter_prompt_tokens: number | null;
        openrouter_completion_tokens: number | null;
        openrouter_total_tokens: number | null;
        tavily_search_calls: number | null;
        cost_estimate_usd: number | null;
    } | null; // Allow api_usage itself to be null if not populated
    // --- ADDED: Stats specific to REVIEW jobs ---
    reclassify_input?: Array<{ vendor_name: string; hint: string }>; // Input hints
    total_items_processed?: number;
    successful_reclassifications?: number;
    failed_reclassifications?: number;
    parent_job_id?: string; // Include parent ID in stats for review jobs
    // --- END ADDED ---
}


// Structure for download result helper
interface DownloadResult {
    blob: Blob;
    filename: string;
}

// Parameters for the job history list endpoint
interface GetJobsParams {
    status?: string;
    start_date?: string; // ISO string format
    end_date?: string; // ISO string format
    job_type?: 'CLASSIFICATION' | 'REVIEW'; // Filter by type
    skip?: number;
    limit?: number;
}

// --- ADDED: Password Reset Interfaces ---
// Matches backend schemas/password_reset.py -> MessageResponse
interface MessageResponse {
    message: string;
}
// --- END ADDED ---

// --- ADDED: Reclassification Interfaces ---
// Matches backend schemas/review.py -> ReclassifyRequestItem
interface ReclassifyRequestItemData {
    vendor_name: string;
    hint: string;
}
// Matches backend schemas/review.py -> ReclassifyResponse
interface ReclassifyResponseData {
    review_job_id: string;
    message: string;
}
// --- END ADDED ---


// --- Axios Instance Setup ---

const axiosInstance: AxiosInstance = axios.create({
    baseURL: '/api/v1', // Assumes Vite dev server proxies /api/v1 to your backend
    timeout: 60000, // 60 seconds timeout
    headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    },
});

// --- Request Interceptor (Add Auth Token) ---
axiosInstance.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
        const authStore = useAuthStore();
        const token = authStore.getToken();
        // Define URLs that should NOT receive the auth token
        // --- UPDATED: Added /users/register ---
        const noAuthUrls = ['/auth/password-recovery', '/auth/reset-password', '/users/register'];
        // --- END UPDATED ---

        // Check if the request URL matches any of the no-auth URLs
        const requiresAuth = token && config.url && !noAuthUrls.some(url => config.url?.startsWith(url));

        if (requiresAuth) {
            // LOGGING: Log token presence and target URL
            // console.log(`[api.ts Request Interceptor] Adding token for URL: ${config.url}`);
            config.headers.Authorization = `Bearer ${token}`;
        } else {
            // console.log(`[api.ts Request Interceptor] No token added for URL: ${config.url} (Token: ${token ? 'present' : 'missing'}, No-Auth Match: ${!requiresAuth && !!token})`);
        }
        return config;
    },
    (error: AxiosError) => {
        console.error('[api.ts Request Interceptor] Error:', error);
        return Promise.reject(error);
    }
);

// --- Response Interceptor (Handle Errors) ---
axiosInstance.interceptors.response.use(
    (response) => {
        // LOGGING: Log successful response status and URL
        // console.log(`[api.ts Response Interceptor] Success for URL: ${response.config.url} | Status: ${response.status}`);
        return response;
    },
    (error: AxiosError) => {
        console.error('[api.ts Response Interceptor] Error:', error.config?.url, error.response?.status, error.message);
        const authStore = useAuthStore();

        if (error.response) {
            const { status, data } = error.response;

            // Handle 401 Unauthorized (except for login attempts and password reset)
            const isLoginAttempt = error.config?.url === '/token'; // Base URL for login
            // --- UPDATED: Check register url ---
            const isPublicAuthOperation = error.config?.url?.startsWith('/auth/') || error.config?.url?.startsWith('/users/register');
            // --- END UPDATED ---

            // --- UPDATED: Check isPublicAuthOperation ---
            if (status === 401 && !isLoginAttempt && !isPublicAuthOperation) {
            // --- END UPDATED ---
                console.warn('[api.ts Response Interceptor] Received 401 Unauthorized on protected route. Logging out.');
                authStore.logout(); // Trigger logout action
                // No reload here, let the component handle redirection or UI change
                return Promise.reject(new Error('Session expired. Please log in again.'));
            }

            // Extract detailed error message from response data
            let detailMessage = 'An error occurred.';
            const responseData = data as any;

            // Handle FastAPI validation errors (detail is an array)
            if (responseData?.detail && Array.isArray(responseData.detail)) {
                 detailMessage = `Validation Error: ${responseData.detail.map((err: any) => `${err.loc?.join('.') ?? 'field'}: ${err.msg}`).join('; ')}`;
            }
            // Handle other FastAPI errors (detail is a string) or custom errors
            else if (responseData?.detail && typeof responseData.detail === 'string') {
                detailMessage = responseData.detail;
            }
            // Handle cases where the error might be directly in the data object (less common)
            else if (typeof data === 'string' && data.length > 0 && data.length < 300) {
                detailMessage = data;
            }
            // Fallback to Axios error message
            else if (error.message) {
                detailMessage = error.message;
            }

            // Prepend status code for clarity, unless it's a 422 validation error where the message is usually sufficient
            const errorMessage = status === 422 ? detailMessage : `Error ${status}: ${detailMessage}`;
            console.error(`[api.ts Response Interceptor] Rejecting with error: ${errorMessage}`); // LOGGING
            return Promise.reject(new Error(errorMessage));

        } else if (error.request) {
            console.error('[api.ts Response Interceptor] Network error or no response received:', error.request);
            return Promise.reject(new Error('Network error or server did not respond. Please check connection.'));
        } else {
            console.error('[api.ts Response Interceptor] Axios setup error:', error.message);
            return Promise.reject(new Error(`Request setup error: ${error.message}`));
        }
    }
);


// --- API Service Object ---

const apiService = {
    /**
        * Logs in a user. Uses base axios for specific headers.
        */
    async login(usernameInput: string, passwordInput: string): Promise<AuthResponse> {
        const params = new URLSearchParams();
        params.append('username', usernameInput);
        params.append('password', passwordInput);
        console.log(`[api.ts login] Attempting login for user: ${usernameInput}`); // LOGGING
        // Use base axios to avoid default JSON headers and ensure correct Content-Type
        // Also avoids the interceptor adding an Authorization header if a previous token exists
        const response = await axios.post<AuthResponse>('/token', params, {
            baseURL: '/', // Use root base URL since '/token' is not under /api/v1
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        });
        console.log(`[api.ts login] Login successful for user: ${usernameInput}`); // LOGGING
        return response.data;
    },

    /**
        * Validates the header of an uploaded file.
        */
    async validateUpload(formData: FormData): Promise<FileValidationResponse> {
        console.log('[api.ts validateUpload] Attempting file header validation...'); // LOGGING
        // Uses axiosInstance, includes auth token if available and URL requires it
        const response = await axiosInstance.post<FileValidationResponse>('/validate-upload', formData, {
             headers: { 'Content-Type': undefined } // Let browser set Content-Type for FormData
        });
        console.log(`[api.ts validateUpload] Validation response received: isValid=${response.data.is_valid}`); // LOGGING
        return response.data;
    },


    /**
        * Uploads the vendor file (after validation).
        * Returns the full JobResponse object.
        */
    async uploadFile(formData: FormData): Promise<JobResponse> { // Return JobResponse
        console.log('[api.ts uploadFile] Attempting file upload...'); // LOGGING
        // This uses axiosInstance, so /api/v1 prefix is added automatically
        const response = await axiosInstance.post<JobResponse>('/upload', formData, { // Expect JobResponse
                headers: { 'Content-Type': undefined } // Let browser set Content-Type for FormData
        });
        console.log(`[api.ts uploadFile] Upload successful, job ID: ${response.data.id}, Target Level: ${response.data.target_level}`); // LOGGING
        return response.data;
    },

    /**
        * Fetches the status and details of a specific job.
        */
    async getJobStatus(jobId: string): Promise<JobDetails> {
        console.log(`[api.ts getJobStatus] Fetching status for job ID: ${jobId}`); // LOGGING
        const response = await axiosInstance.get<JobDetails>(`/jobs/${jobId}`);
        console.log(`[api.ts getJobStatus] Received status for job ${jobId}:`, response.data.status, `Target Level: ${response.data.target_level}`, `Job Type: ${response.data.job_type}`); // LOGGING
        return response.data;
    },

    /**
        * Fetches statistics for a specific job.
        */
    async getJobStats(jobId: string): Promise<JobStatsData> { // Use the updated interface here
        console.log(`[api.ts getJobStats] Fetching stats for job ID: ${jobId}`); // LOGGING
        const response = await axiosInstance.get<JobStatsData>(`/jobs/${jobId}/stats`);
        // LOGGING: Log the received stats structure
        console.log(`[api.ts getJobStats] Received stats for job ${jobId}:`, JSON.parse(JSON.stringify(response.data)));
        return response.data;
    },

    /**
     * Fetches the detailed classification results for a specific job.
     * Returns the JobResultsResponse structure containing job type and results list.
     */
    async getJobResults(jobId: string): Promise<JobResultsResponse> {
        console.log(`[api.ts getJobResults] Fetching detailed results for job ID: ${jobId}`); // LOGGING
        const response = await axiosInstance.get<JobResultsResponse>(`/jobs/${jobId}/results`);
        console.log(`[api.ts getJobResults] Received ${response.data.results.length} detailed result items for job ${jobId} (Type: ${response.data.job_type}).`); // LOGGING
        return response.data;
    },

    /**
        * Requests email notification for a job completion.
        */
    async requestNotification(jobId: string, email: string): Promise<NotifyResponse> {
        console.log(`[api.ts requestNotification] Requesting notification for job ${jobId} to email ${email}`); // LOGGING
        const response = await axiosInstance.post<NotifyResponse>(`/jobs/${jobId}/notify`, { email });
        console.log(`[api.ts requestNotification] Notification request response:`, response.data.success); // LOGGING
        return response.data;
    },

    /**
        * Downloads the results file for a completed job.
        */
    async downloadResults(jobId: string): Promise<DownloadResult> {
        console.log(`[api.ts downloadResults] Requesting download for job ID: ${jobId}`); // LOGGING
        const response = await axiosInstance.get(`/jobs/${jobId}/download`, {
            responseType: 'blob',
        });
        const disposition = response.headers['content-disposition'];
        let filename = `results_${jobId}.xlsx`;
        if (disposition?.includes('attachment')) {
            const filenameMatch = disposition.match(/filename\*?=(?:(?:"((?:[^"\\]|\\.)*)")|(?:([^;\n]*)))/i);
            if (filenameMatch?.[1]) { filename = filenameMatch[1].replace(/\\"/g, '"'); }
            else if (filenameMatch?.[2]) {
                    const utf8Match = filenameMatch[2].match(/^UTF-8''(.*)/i);
                    if (utf8Match?.[1]) { try { filename = decodeURIComponent(utf8Match[1]); } catch (e) { filename = utf8Match[1]; } }
                    else { filename = filenameMatch[2]; }
            }
        }
        console.log(`[api.ts downloadResults] Determined download filename: ${filename}`); // LOGGING
        return { blob: response.data as Blob, filename };
    },

    /**
        * Fetches a list of jobs for the current user, with optional filtering/pagination.
        */
    async getJobs(params: GetJobsParams = {}): Promise<JobResponse[]> {
        const cleanedParams = Object.fromEntries(
            Object.entries(params).filter(([, value]) => value !== undefined && value !== null && value !== '')
        );
        console.log('[api.ts getJobs] Fetching job list with params:', cleanedParams); // LOGGING
        const response = await axiosInstance.get<JobResponse[]>('/jobs/', { params: cleanedParams });
        console.log(`[api.ts getJobs] Received ${response.data.length} jobs.`); // LOGGING
        return response.data;
    },

    // --- User Management API Methods ---

    /**
        * Fetches the current logged-in user's details.
        */
    async getCurrentUser(): Promise<UserResponse> {
        console.log('[api.ts getCurrentUser] Fetching current user details...'); // LOGGING
        const response = await axiosInstance.get<UserResponse>('/users/me');
        console.log(`[api.ts getCurrentUser] Received user: ${response.data.username}`); // LOGGING
        return response.data;
    },

    /**
        * Fetches a list of all users (admin only).
        */
    async getUsers(skip: number = 0, limit: number = 100): Promise<UserResponse[]> {
        console.log(`[api.ts getUsers] Fetching user list (skip: ${skip}, limit: ${limit})...`); // LOGGING
        const response = await axiosInstance.get<UserResponse[]>('/users/', { params: { skip, limit } });
         console.log(`[api.ts getUsers] Received ${response.data.length} users.`); // LOGGING
        return response.data;
    },

        /**
        * Fetches a specific user by ID (admin or self).
        */
        async getUserById(userId: string): Promise<UserResponse> {
        console.log(`[api.ts getUserById] Fetching user ID: ${userId}`); // LOGGING
        const response = await axiosInstance.get<UserResponse>(`/users/${userId}`);
        console.log(`[api.ts getUserById] Received user: ${response.data.username}`); // LOGGING
        return response.data;
    },

    /**
        * Creates a new user (admin only).
        */
    async createUser(userData: UserCreateData): Promise<UserResponse> {
        console.log(`[api.ts createUser] Attempting to create user (admin): ${userData.username}`); // LOGGING
        const response = await axiosInstance.post<UserResponse>('/users/', userData);
        console.log(`[api.ts createUser] User created successfully (admin): ${response.data.username}`); // LOGGING
        return response.data;
    },

    /**
        * Updates a user (admin or self).
        */
    async updateUser(userId: string, userData: UserUpdateData): Promise<UserResponse> {
        console.log(`[api.ts updateUser] Attempting to update user ID: ${userId}`); // LOGGING
        const response = await axiosInstance.put<UserResponse>(`/users/${userId}`, userData);
        console.log(`[api.ts updateUser] User updated successfully: ${response.data.username}`); // LOGGING
        return response.data;
    },

    /**
        * Deletes a user (admin only).
        */
    async deleteUser(userId: string): Promise<{ message: string }> {
        console.log(`[api.ts deleteUser] Attempting to delete user ID: ${userId}`); // LOGGING
        const response = await axiosInstance.delete<{ message: string }>(`/users/${userId}`);
        console.log(`[api.ts deleteUser] User delete response: ${response.data.message}`); // LOGGING
        return response.data;
    },
    // --- END User Management API Methods ---

    // --- ADDED: Public Registration API Method ---
    /**
     * Registers a new user publicly.
     */
    async registerUser(userData: UserCreateData): Promise<UserResponse> {
        console.log(`[api.ts registerUser] Attempting public registration for user: ${userData.username}`);
        // Uses axiosInstance, interceptor skips auth token for this URL
        const response = await axiosInstance.post<UserResponse>('/users/register', userData);
        console.log(`[api.ts registerUser] Public registration successful: ${response.data.username}`);
        return response.data;
    },
    // --- END Public Registration API Method ---


    // --- ADDED: Password Reset API Methods ---
    /**
     * Requests a password reset email to be sent.
     */
    async requestPasswordRecovery(email: string): Promise<MessageResponse> {
        console.log(`[api.ts requestPasswordRecovery] Requesting password reset for email: ${email}`);
        // This uses axiosInstance, but the interceptor should skip adding auth token for this URL
        const response = await axiosInstance.post<MessageResponse>('/auth/password-recovery', { email });
        console.log(`[api.ts requestPasswordRecovery] Request response: ${response.data.message}`);
        return response.data;
    },

    /**
     * Resets the password using the provided token and new password.
     */
    async resetPassword(token: string, newPassword: string): Promise<MessageResponse> {
        console.log(`[api.ts resetPassword] Attempting password reset with token: ${token.substring(0, 10)}...`);
        // This uses axiosInstance, but the interceptor should skip adding auth token for this URL
        const response = await axiosInstance.post<MessageResponse>('/auth/reset-password', {
            token: token,
            new_password: newPassword
        });
        console.log(`[api.ts resetPassword] Reset response: ${response.data.message}`);
        return response.data;
    },
    // --- END Password Reset API Methods ---

    // --- ADDED: Reclassification API Method ---
    /**
     * Submits flagged items for reclassification.
     */
    async reclassifyJob(originalJobId: string, items: ReclassifyRequestItemData[]): Promise<ReclassifyResponseData> {
        console.log(`[api.ts reclassifyJob] Submitting ${items.length} items for reclassification for job ${originalJobId}`);
        const payload = { items: items };
        const response = await axiosInstance.post<ReclassifyResponseData>(`/jobs/${originalJobId}/reclassify`, payload);
        console.log(`[api.ts reclassifyJob] Reclassification job started: ${response.data.review_job_id}`);
        return response.data;
    }
    // --- END ADDED ---
};

export default apiService;

```
</file>

<file path='frontend/vue_frontend/src/components/HintInputModal.vue'>
```vue
<template>
  <TransitionRoot as="template" :show="open">
    <Dialog as="div" class="relative z-10" @close="closeModal">
      <TransitionChild as="template" enter="ease-out duration-300" enter-from="opacity-0" enter-to="opacity-100" leave="ease-in duration-200" leave-from="opacity-100" leave-to="opacity-0">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" />
      </TransitionChild>

      <div class="fixed inset-0 z-10 overflow-y-auto">
        <div class="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
          <TransitionChild as="template" enter="ease-out duration-300" enter-from="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95" enter-to="opacity-100 translate-y-0 sm:scale-100" leave="ease-in duration-200" leave-from="opacity-100 translate-y-0 sm:scale-100" leave-to="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95">
            <DialogPanel class="relative transform overflow-hidden rounded-lg bg-white text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg">
              <div class="bg-white px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
                <div class="sm:flex sm:items-start">
                  <div class="mx-auto flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full bg-blue-100 sm:mx-0 sm:h-10 sm:w-10">
                    <PencilSquareIcon class="h-6 w-6 text-blue-600" aria-hidden="true" />
                  </div>
                  <div class="mt-3 text-center sm:ml-4 sm:mt-0 sm:text-left w-full">
                    <DialogTitle as="h3" class="text-base font-semibold leading-6 text-gray-900">Provide Reclassification Hint</DialogTitle>
                    <div class="mt-2">
                      <p class="text-sm text-gray-600 mb-1">For Vendor: <strong class="font-medium">{{ vendorName }}</strong></p>
                      <p class="text-sm text-gray-500">
                        Please provide a concise hint to help the system re-classify this vendor accurately. Examples: "supplier of laboratory chemicals", "provides marketing consulting services", "industrial fastener manufacturer".
                      </p>
                      <div class="mt-4">
                        <label for="hint" class="sr-only">Hint</label>
                        <textarea
                          id="hint"
                          name="hint"
                          rows="3"
                          v-model="localHint"
                          class="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-primary sm:text-sm sm:leading-6"
                          placeholder="Enter hint here..."
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div class="bg-gray-50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
                <button
                  type="button"
                  class="inline-flex w-full justify-center rounded-md bg-primary px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-primary-dark focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary sm:ml-3 sm:w-auto disabled:opacity-50"
                  @click="saveHint"
                  :disabled="!localHint || localHint.trim() === ''"
                >
                  Save Hint
                </button>
                <button
                  type="button"
                  class="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto"
                  @click="closeModal"
                  ref="cancelButtonRef"
                >
                  Cancel
                </button>
              </div>
            </DialogPanel>
          </TransitionChild>
        </div>
      </div>
    </Dialog>
  </TransitionRoot>
</template>

<script setup lang="ts">
import { ref, watch, type PropType } from 'vue'
import { Dialog, DialogPanel, DialogTitle, TransitionChild, TransitionRoot } from '@headlessui/vue'
import { PencilSquareIcon } from '@heroicons/vue/24/outline'

const props = defineProps({
  open: {
    type: Boolean,
    required: true,
  },
  vendorName: {
    type: String,
    required: true,
  },
  initialHint: {
    type: String as PropType<string | null>,
    default: null,
  },
})

const emit = defineEmits(['close', 'save'])

const localHint = ref(props.initialHint || '');

watch(() => props.initialHint, (newVal) => {
  localHint.value = newVal || '';
});

watch(() => props.open, (newVal) => {
  if (newVal) {
    // Reset local hint when modal opens, based on potentially updated prop
    localHint.value = props.initialHint || '';
  }
});


const closeModal = () => {
  emit('close');
}

const saveHint = () => {
  if (localHint.value && localHint.value.trim() !== '') {
    emit('save', localHint.value.trim());
    closeModal();
  }
}
</script>
```
</file>

<file path='frontend/vue_frontend/src/components/ReviewResultsTable.vue'>
```vue
<template>
  <div class="mt-8 p-4 sm:p-6 bg-gray-50 rounded-lg border border-gray-200 shadow-inner">
    <h5 class="text-lg font-semibold text-gray-800 mb-4">Reviewed Classification Results</h5>
    <p class="text-sm text-gray-600 mb-4">
      Showing results after applying user hints. You can flag items again for further review if needed.
    </p>

    <!-- Search Input -->
    <div class="mb-4">
      <label for="review-results-search" class="sr-only">Search Reviewed Results</label>
      <div class="relative rounded-md shadow-sm">
        <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <MagnifyingGlassIcon class="h-5 w-5 text-gray-400" aria-hidden="true" />
        </div>
        <input
          type="text"
          id="review-results-search"
          v-model="searchTerm"
          placeholder="Search Vendor, Hint, Category, ID, Notes..."
          class="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
        />
      </div>
    </div>

     <!-- Action Buttons (Submit Flags) -->
    <div class="mb-4 text-right" v-if="jobStore.hasFlaggedItems">
        <button
          type="button"
          @click="submitFlags"
          :disabled="jobStore.reclassifyLoading"
          class="inline-flex items-center rounded-md bg-primary px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-primary-dark focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:opacity-50"
        >
          <ArrowPathIcon v-if="jobStore.reclassifyLoading" class="animate-spin -ml-0.5 mr-1.5 h-5 w-5" aria-hidden="true" />
          <PaperAirplaneIcon v-else class="-ml-0.5 mr-1.5 h-5 w-5" aria-hidden="true" />
          Submit {{ jobStore.flaggedForReview.size }} Flag{{ jobStore.flaggedForReview.size !== 1 ? 's' : '' }} for Re-classification
        </button>
        <p v-if="jobStore.reclassifyError" class="text-xs text-red-600 mt-1 text-right">{{ jobStore.reclassifyError }}</p>
    </div>

    <!-- Loading/Error States -->
    <div v-if="loading" class="text-center py-5 text-gray-500">
      <svg class="animate-spin h-6 w-6 text-primary mx-auto" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      <p class="mt-2 text-sm">Loading reviewed results...</p>
    </div>
    <div v-else-if="error" class="p-4 bg-red-100 border border-red-300 text-red-800 rounded-md text-sm">
      Error loading reviewed results: {{ error }}
    </div>
    <div v-else-if="!results || results.length === 0" class="text-center py-5 text-gray-500">
      No reviewed results found for this job.
    </div>

    <!-- Results Table -->
    <div v-else class="overflow-x-auto border border-gray-200 rounded-md">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-100">
          <tr>
            <!-- Flag Column -->
            <th scope="col" class="px-2 py-3 text-center text-xs font-medium text-gray-600 uppercase tracking-wider w-12">Flag</th>
            <!-- Dynamically generate headers -->
            <th v-for="header in headers" :key="header.key"
                scope="col"
                @click="header.sortable ? sortBy(header.key) : null"
                :class="[
                  'px-3 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider',
                   header.sortable ? 'cursor-pointer hover:bg-gray-200' : '',
                   header.minWidth ? `min-w-[${header.minWidth}]` : ''
                ]">
              {{ header.label }}
              <SortIcon v-if="header.sortable" :direction="sortKey === header.key ? sortDirection : null" />
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-if="filteredAndSortedResults.length === 0">
            <td :colspan="headers.length + 1" class="px-4 py-4 whitespace-nowrap text-sm text-gray-500 text-center">No results match your search criteria.</td>
          </tr>
          <tr v-for="(item, index) in filteredAndSortedResults" :key="item.vendor_name + '-' + index" class="hover:bg-gray-50 align-top" :class="{'bg-blue-50': jobStore.isFlagged(item.vendor_name)}">
            <!-- Flag Button Cell -->
            <td class="px-2 py-2 text-center align-middle">
                 <button
                    @click="toggleFlag(item.vendor_name)"
                    :title="jobStore.isFlagged(item.vendor_name) ? 'Remove flag and hint' : 'Flag for re-classification'"
                    class="p-1 rounded-full hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-primary"
                    :class="jobStore.isFlagged(item.vendor_name) ? 'text-primary' : 'text-gray-400 hover:text-primary-dark'"
                  >
                    <FlagIconSolid v-if="jobStore.isFlagged(item.vendor_name)" class="h-5 w-5" aria-hidden="true" />
                    <FlagIconOutline v-else class="h-5 w-5" aria-hidden="true" />
                    <span class="sr-only">Flag item</span>
                  </button>
            </td>
            <!-- Data Cells -->
            <td class="px-3 py-2 whitespace-nowrap text-sm font-medium text-gray-900">{{ item.vendor_name }}</td>
            <td class="px-3 py-2 text-xs text-gray-600 max-w-xs break-words">
                <span v-if="!jobStore.isFlagged(item.vendor_name)">{{ item.hint }}</span>
                 <!-- Inline Hint Editor when Flagged -->
                <textarea v-else
                          rows="2"
                          :value="jobStore.getHint(item.vendor_name)"
                          @input="updateHint(item.vendor_name, ($event.target as HTMLTextAreaElement).value)"
                          placeholder="Enter new hint..."
                          class="block w-full text-xs rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary"
                ></textarea>
            </td>
            <!-- Original Classification -->
            <td class="px-3 py-2 whitespace-nowrap text-xs font-mono text-gray-500">{{ item.original_result?.level1_id || '-' }}</td>
            <td class="px-3 py-2 text-xs text-gray-500">{{ item.original_result?.level1_name || '-' }}</td>
            <!-- ... Add other original levels L2-L5 similarly ... -->
            <td class="px-3 py-2 whitespace-nowrap text-xs font-mono text-gray-500">{{ item.original_result?.level5_id || '-' }}</td>
            <td class="px-3 py-2 text-xs text-gray-500">{{ item.original_result?.level5_name || '-' }}</td>
            <td class="px-3 py-2 whitespace-nowrap text-xs text-center text-gray-500">
                <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full"
                      :class="getStatusClass(item.original_result?.final_status)">
                    {{ item.original_result?.final_status }}
                </span>
            </td>

            <!-- New Classification -->
            <td class="px-3 py-2 whitespace-nowrap text-xs font-mono" :class="getCellClass(item.new_result, 1)">{{ item.new_result?.level1_id || '-' }}</td>
            <td class="px-3 py-2 text-xs" :class="getCellClass(item.new_result, 1)">{{ item.new_result?.level1_name || '-' }}</td>
            <!-- ... Add other new levels L2-L5 similarly ... -->
            <td class="px-3 py-2 whitespace-nowrap text-xs font-mono" :class="getCellClass(item.new_result, 5)">{{ item.new_result?.level5_id || '-' }}</td>
            <td class="px-3 py-2 text-xs" :class="getCellClass(item.new_result, 5)">{{ item.new_result?.level5_name || '-' }}</td>
            <td class="px-3 py-2 whitespace-nowrap text-sm text-center">
              <span v-if="item.new_result?.final_confidence !== null && item.new_result?.final_confidence !== undefined"
                    :class="getConfidenceClass(item.new_result.final_confidence)">
                {{ (item.new_result.final_confidence * 100).toFixed(1) }}%
              </span>
              <span v-else class="text-gray-400 text-xs">N/A</span>
            </td>
            <td class="px-3 py-2 whitespace-nowrap text-xs text-center">
               <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full"
                    :class="getStatusClass(item.new_result?.final_status)">
                {{ item.new_result?.final_status }}
              </span>
            </td>
            <td class="px-3 py-2 text-xs text-gray-500 max-w-xs break-words">
              {{ item.new_result?.classification_notes_or_reason || '-' }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

     <!-- Row Count -->
    <div class="mt-3 text-xs text-gray-500">
      Showing {{ filteredAndSortedResults.length }} of {{ results?.length || 0 }} reviewed results.
    </div>

    <!-- Hint Input Modal -->
    <!-- <HintInputModal
        :open="showHintModal"
        :vendor-name="selectedVendorForHint"
        :initial-hint="jobStore.getHint(selectedVendorForHint)"
        @close="showHintModal = false"
        @save="saveHint"
    /> -->
     <!-- Note: Using inline editor instead of modal for now -->

  </div>
</template>

<script setup lang="ts">
import { ref, computed, type PropType } from 'vue';
import { useJobStore, type ReviewResultItem, type JobResultItem } from '@/stores/job';
import { FlagIcon as FlagIconOutline, MagnifyingGlassIcon, PaperAirplaneIcon, ArrowPathIcon } from '@heroicons/vue/24/outline';
import { FlagIcon as FlagIconSolid, ChevronUpIcon, ChevronDownIcon, ChevronUpDownIcon } from '@heroicons/vue/20/solid';
// import HintInputModal from './HintInputModal.vue'; // Import if using modal

// --- Define Header Interface ---
interface ReviewTableHeader {
  key: string; // Use string for complex/nested keys
  label: string;
  sortable: boolean;
  minWidth?: string;
  isOriginal?: boolean; // Flag for styling/grouping
  isNew?: boolean;      // Flag for styling/grouping
}
// --- END Define Header Interface ---

// --- Props ---
const props = defineProps({
  results: {
    type: Array as PropType<ReviewResultItem[] | null>,
    required: true,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  error: {
    type: String as PropType<string | null>,
    default: null,
  },
  targetLevel: { // Pass the job's target level
    type: Number,
    required: true,
  }
});

const emit = defineEmits(['submit-flags']); // Emit event when submit button is clicked

// --- Store ---
const jobStore = useJobStore();

// --- Internal State ---
const searchTerm = ref('');
const sortKey = ref<string | null>('vendor_name'); // Default sort by vendor name
const sortDirection = ref<'asc' | 'desc' | null>('asc'); // Default sort direction
// const showHintModal = ref(false); // State for modal
// const selectedVendorForHint = ref(''); // State for modal

// --- Table Headers Definition ---
const headers = ref<ReviewTableHeader[]>([
  { key: 'vendor_name', label: 'Vendor Name', sortable: true, minWidth: '150px' },
  { key: 'hint', label: 'User Hint', sortable: true, minWidth: '180px' },
  // Original Results
  { key: 'original_result.level1_id', label: 'Orig L1 ID', sortable: true, minWidth: '80px', isOriginal: true },
  { key: 'original_result.level1_name', label: 'Orig L1 Name', sortable: true, minWidth: '120px', isOriginal: true },
  // Add L2-L4 original if needed
  { key: 'original_result.level5_id', label: 'Orig L5 ID', sortable: true, minWidth: '80px', isOriginal: true },
  { key: 'original_result.level5_name', label: 'Orig L5 Name', sortable: true, minWidth: '120px', isOriginal: true },
  { key: 'original_result.final_status', label: 'Orig Status', sortable: true, minWidth: '100px', isOriginal: true },
  // New Results
  { key: 'new_result.level1_id', label: 'New L1 ID', sortable: true, minWidth: '80px', isNew: true },
  { key: 'new_result.level1_name', label: 'New L1 Name', sortable: true, minWidth: '120px', isNew: true },
   // Add L2-L4 new if needed
  { key: 'new_result.level5_id', label: 'New L5 ID', sortable: true, minWidth: '80px', isNew: true },
  { key: 'new_result.level5_name', label: 'New L5 Name', sortable: true, minWidth: '120px', isNew: true },
  { key: 'new_result.final_confidence', label: 'New Confidence', sortable: true, minWidth: '100px', isNew: true },
  { key: 'new_result.final_status', label: 'New Status', sortable: true, minWidth: '100px', isNew: true },
  { key: 'new_result.classification_notes_or_reason', label: 'New Notes / Reason', sortable: false, minWidth: '200px', isNew: true },
]);

// --- Computed Properties ---

// Helper to get nested values for sorting/filtering
const getNestedValue = (obj: any, path: string): any => {
  return path.split('.').reduce((value, key) => (value && value[key] !== undefined ? value[key] : null), obj);
};


const filteredAndSortedResults = computed(() => {
  if (!props.results) return [];

  let filtered = props.results;

  // Filtering
  if (searchTerm.value) {
    const lowerSearchTerm = searchTerm.value.toLowerCase();
    filtered = filtered.filter(item =>
      item.vendor_name?.toLowerCase().includes(lowerSearchTerm) ||
      item.hint?.toLowerCase().includes(lowerSearchTerm) ||
      // Search within original results
      item.original_result?.level1_id?.toLowerCase().includes(lowerSearchTerm) ||
      item.original_result?.level1_name?.toLowerCase().includes(lowerSearchTerm) ||
      // ... add other original levels ...
      item.original_result?.level5_id?.toLowerCase().includes(lowerSearchTerm) ||
      item.original_result?.level5_name?.toLowerCase().includes(lowerSearchTerm) ||
      item.original_result?.final_status?.toLowerCase().includes(lowerSearchTerm) ||
      // Search within new results
      item.new_result?.level1_id?.toLowerCase().includes(lowerSearchTerm) ||
      item.new_result?.level1_name?.toLowerCase().includes(lowerSearchTerm) ||
      // ... add other new levels ...
      item.new_result?.level5_id?.toLowerCase().includes(lowerSearchTerm) ||
      item.new_result?.level5_name?.toLowerCase().includes(lowerSearchTerm) ||
      item.new_result?.final_status?.toLowerCase().includes(lowerSearchTerm) ||
      item.new_result?.classification_notes_or_reason?.toLowerCase().includes(lowerSearchTerm)
    );
  }

  // Sorting
  if (sortKey.value && sortDirection.value) {
    const key = sortKey.value;
    const direction = sortDirection.value === 'asc' ? 1 : -1;

    filtered = filtered.slice().sort((a, b) => {
      const valA = getNestedValue(a, key);
      const valB = getNestedValue(b, key);

      const aIsNull = valA === null || valA === undefined || valA === '';
      const bIsNull = valB === null || valB === undefined || valB === '';

      if (aIsNull && bIsNull) return 0;
      if (aIsNull) return 1 * direction;
      if (bIsNull) return -1 * direction;

      if (typeof valA === 'string' && typeof valB === 'string') {
        return valA.localeCompare(valB) * direction;
      }
      if (typeof valA === 'number' && typeof valB === 'number') {
        return (valA - valB) * direction;
      }

      const strA = String(valA).toLowerCase();
      const strB = String(valB).toLowerCase();
      if (strA < strB) return -1 * direction;
      if (strA > strB) return 1 * direction;
      return 0;
    });
  }

  return filtered;
});

// --- Methods ---

function sortBy(key: string) { // Key is now string due to nesting
  if (sortKey.value === key) {
    if (sortDirection.value === 'asc') {
        sortDirection.value = 'desc';
    } else if (sortDirection.value === 'desc') {
        sortDirection.value = null;
        sortKey.value = null;
    } else {
        sortDirection.value = 'asc';
    }
  } else {
    sortKey.value = key;
    sortDirection.value = 'asc';
  }
}

function getConfidenceClass(confidence: number | null | undefined): string {
  if (confidence === null || confidence === undefined) return 'text-gray-400';
  if (confidence >= 0.8) return 'text-green-700 font-medium';
  if (confidence >= 0.5) return 'text-yellow-700';
  return 'text-red-700';
}

function getStatusClass(status: string | null | undefined): string {
    switch(status?.toLowerCase()){
        case 'classified': return 'bg-green-100 text-green-800';
        case 'not possible': return 'bg-yellow-100 text-yellow-800';
        case 'error': return 'bg-red-100 text-red-800';
        default: return 'bg-gray-100 text-gray-800';
    }
}

// Highlight cells beyond the target classification depth in the *new* result
function getCellClass(item: JobResultItem | null | undefined, level: number): string {
    const baseClass = 'text-gray-700';
    const beyondDepthClass = 'text-gray-400 italic';

    if (!item) return baseClass; // Handle case where new_result might be null

    const levelIdKey = `level${level}_id` as keyof JobResultItem;
    const hasId = item[levelIdKey] !== null && item[levelIdKey] !== undefined && item[levelIdKey] !== '';

    if (level > props.targetLevel && hasId) {
        return beyondDepthClass;
    }
    return baseClass;
}

// --- Flagging and Hint Handling ---
function toggleFlag(vendorName: string) {
    if (jobStore.isFlagged(vendorName)) {
        jobStore.unflagVendor(vendorName);
    } else {
        jobStore.flagVendor(vendorName);
        // Optionally open modal here if using one
        // selectedVendorForHint.value = vendorName;
        // showHintModal.value = true;
    }
}

function updateHint(vendorName: string, hint: string) {
    jobStore.setHint(vendorName, hint);
}

// function saveHint(hint: string) {
//     if (selectedVendorForHint.value) {
//         jobStore.setHint(selectedVendorForHint.value, hint);
//     }
//     selectedVendorForHint.value = ''; // Clear selection
// }

async function submitFlags() {
    emit('submit-flags'); // Notify parent (JobStatus) to handle submission logic
}

// --- Helper Component for Sort Icons ---
const SortIcon = {
  props: {
    direction: {
      type: String as PropType<'asc' | 'desc' | null>,
      default: null,
    },
  },
  components: { ChevronUpIcon, ChevronDownIcon, ChevronUpDownIcon },
  template: `
    <span class="inline-block ml-1 w-4 h-4 align-middle">
      <ChevronUpIcon v-if="direction === 'asc'" class="w-4 h-4 text-gray-700" />
      <ChevronDownIcon v-else-if="direction === 'desc'" class="w-4 h-4 text-gray-700" />
      <ChevronUpDownIcon v-else class="w-4 h-4 text-gray-400 opacity-50" />
    </span>
  `,
};

</script>

<style scoped>
/* Add styles for visually separating original vs new columns if desired */
/* e.g., a subtle border or background */
/* th[isOriginal="true"], td[isOriginal="true"] { ... } */
/* th[isNew="true"], td[isNew="true"] { ... } */
</style>
```
</file>

<file path='frontend/vue_frontend/src/components/JobResultsTable.vue'>
```vue
<template>
  <div class="mt-8 p-4 sm:p-6 bg-gray-50 rounded-lg border border-gray-200 shadow-inner">
    <h5 class="text-lg font-semibold text-gray-800 mb-4">Detailed Classification Results</h5>

    <!-- Search Input -->
    <div class="mb-4">
      <label for="results-search" class="sr-only">Search Results</label>
      <div class="relative rounded-md shadow-sm">
         <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <MagnifyingGlassIcon class="h-5 w-5 text-gray-400" aria-hidden="true" />
          </div>
        <input
          type="text"
          id="results-search"
          v-model="searchTerm"
          placeholder="Search Vendor, Category, ID, Notes..."
          class="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
        />
      </div>
    </div>

    <!-- Action Buttons (Submit Flags) -->
    <div class="mb-4 text-right" v-if="jobStore.hasFlaggedItems">
        <button
          type="button"
          @click="submitFlags"
          :disabled="jobStore.reclassifyLoading"
          class="inline-flex items-center rounded-md bg-primary px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-primary-dark focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:opacity-50"
        >
          <ArrowPathIcon v-if="jobStore.reclassifyLoading" class="animate-spin -ml-0.5 mr-1.5 h-5 w-5" aria-hidden="true" />
          <PaperAirplaneIcon v-else class="-ml-0.5 mr-1.5 h-5 w-5" aria-hidden="true" />
          Submit {{ jobStore.flaggedForReview.size }} Flag{{ jobStore.flaggedForReview.size !== 1 ? 's' : '' }} for Re-classification
        </button>
         <p v-if="jobStore.reclassifyError" class="text-xs text-red-600 mt-1 text-right">{{ jobStore.reclassifyError }}</p>
    </div>


    <!-- Loading/Error States -->
    <div v-if="loading" class="text-center py-5 text-gray-500">
      <svg class="animate-spin h-6 w-6 text-primary mx-auto" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      <p class="mt-2 text-sm">Loading detailed results...</p>
    </div>
    <div v-else-if="error" class="p-4 bg-red-100 border border-red-300 text-red-800 rounded-md text-sm">
      Error loading results: {{ error }}
    </div>
    <div v-else-if="!results || results.length === 0" class="text-center py-5 text-gray-500">
      No detailed results found for this job.
    </div>

    <!-- Results Table -->
    <div v-else class="overflow-x-auto border border-gray-200 rounded-md">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-100">
          <tr>
            <!-- Flag Column -->
            <th scope="col" class="px-2 py-3 text-center text-xs font-medium text-gray-600 uppercase tracking-wider w-12">Flag</th>
            <!-- Dynamically generate headers -->
            <th v-for="header in headers" :key="header.key"
                scope="col"
                @click="header.sortable ? sortBy(header.key) : null"
                :class="[
                  'px-3 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider',
                   header.sortable ? 'cursor-pointer hover:bg-gray-200' : '',
                   header.minWidth ? `min-w-[${header.minWidth}]` : ''
                ]">
              {{ header.label }}
              <SortIcon v-if="header.sortable" :direction="sortKey === header.key ? sortDirection : null" />
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-if="filteredAndSortedResults.length === 0">
            <td :colspan="headers.length + 1" class="px-4 py-4 whitespace-nowrap text-sm text-gray-500 text-center">No results match your search criteria.</td>
          </tr>
          <tr v-for="(item, index) in filteredAndSortedResults" :key="item.vendor_name + '-' + index" class="hover:bg-gray-50 align-top" :class="{'bg-blue-50': jobStore.isFlagged(item.vendor_name)}">
             <!-- Flag Button Cell -->
             <td class="px-2 py-2 text-center align-middle">
                 <button
                    @click="toggleFlag(item.vendor_name)"
                    :title="jobStore.isFlagged(item.vendor_name) ? 'Edit hint or remove flag' : 'Flag for re-classification'"
                    class="p-1 rounded-full hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-primary"
                    :class="jobStore.isFlagged(item.vendor_name) ? 'text-primary' : 'text-gray-400 hover:text-primary-dark'"
                  >
                    <FlagIconSolid v-if="jobStore.isFlagged(item.vendor_name)" class="h-5 w-5" aria-hidden="true" />
                    <FlagIconOutline v-else class="h-5 w-5" aria-hidden="true" />
                    <span class="sr-only">Flag item</span>
                  </button>
             </td>
             <!-- Data Cells -->
            <td class="px-3 py-2 whitespace-nowrap text-sm font-medium text-gray-900">{{ item.vendor_name }}</td>
            <!-- Level 1 -->
            <td class="px-3 py-2 whitespace-nowrap text-xs font-mono" :class="getCellClass(item, 1)">{{ item.level1_id || '-' }}</td>
            <td class="px-3 py-2 text-xs" :class="getCellClass(item, 1)">{{ item.level1_name || '-' }}</td>
            <!-- Level 2 -->
            <td class="px-3 py-2 whitespace-nowrap text-xs font-mono" :class="getCellClass(item, 2)">{{ item.level2_id || '-' }}</td>
            <td class="px-3 py-2 text-xs" :class="getCellClass(item, 2)">{{ item.level2_name || '-' }}</td>
            <!-- Level 3 -->
            <td class="px-3 py-2 whitespace-nowrap text-xs font-mono" :class="getCellClass(item, 3)">{{ item.level3_id || '-' }}</td>
            <td class="px-3 py-2 text-xs" :class="getCellClass(item, 3)">{{ item.level3_name || '-' }}</td>
            <!-- Level 4 -->
            <td class="px-3 py-2 whitespace-nowrap text-xs font-mono" :class="getCellClass(item, 4)">{{ item.level4_id || '-' }}</td>
            <td class="px-3 py-2 text-xs" :class="getCellClass(item, 4)">{{ item.level4_name || '-' }}</td>
            <!-- Level 5 -->
            <td class="px-3 py-2 whitespace-nowrap text-xs font-mono" :class="getCellClass(item, 5)">{{ item.level5_id || '-' }}</td>
            <td class="px-3 py-2 text-xs" :class="getCellClass(item, 5)">{{ item.level5_name || '-' }}</td>
            <!-- Other columns -->
            <td class="px-3 py-2 whitespace-nowrap text-sm text-center">
              <span v-if="item.final_confidence !== null && item.final_confidence !== undefined"
                    :class="getConfidenceClass(item.final_confidence)">
                {{ (item.final_confidence * 100).toFixed(1) }}%
              </span>
              <span v-else class="text-gray-400 text-xs">N/A</span>
            </td>
            <td class="px-3 py-2 whitespace-nowrap text-xs text-center">
               <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full"
                    :class="getStatusClass(item.final_status)">
                {{ item.final_status }}
              </span>
            </td>
             <td class="px-3 py-2 whitespace-nowrap text-xs text-center">
              <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full"
                    :class="item.classification_source === 'Search' ? 'bg-blue-100 text-blue-800' : (item.classification_source === 'Review' ? 'bg-purple-100 text-purple-800' : 'bg-green-100 text-green-800')">
                {{ item.classification_source }}
              </span>
            </td>
            <td class="px-3 py-2 text-xs text-gray-500 max-w-xs break-words">
                 <!-- Show hint input if flagged -->
                 <div v-if="jobStore.isFlagged(item.vendor_name)">
                    <label :for="'hint-' + index" class="sr-only">Hint for {{ item.vendor_name }}</label>
                    <textarea :id="'hint-' + index"
                              rows="2"
                              :value="jobStore.getHint(item.vendor_name)"
                              @input="updateHint(item.vendor_name, ($event.target as HTMLTextAreaElement).value)"
                              placeholder="Enter hint..."
                              class="block w-full text-xs rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary"
                    ></textarea>
                    <p v-if="!jobStore.getHint(item.vendor_name)" class="text-red-600 text-xs mt-1">Hint required for submission.</p>
                 </div>
                 <!-- Show notes/reason if not flagged -->
                 <span v-else>{{ item.classification_notes_or_reason || '-' }}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

     <!-- Row Count -->
    <div class="mt-3 text-xs text-gray-500">
      Showing {{ filteredAndSortedResults.length }} of {{ results?.length || 0 }} results.
    </div>

    <!-- Pagination (Placeholder - Implement if needed for very large datasets) -->
    <!-- <div class="mt-4 flex justify-between items-center"> ... </div> -->

     <!-- Hint Input Modal (Alternative to inline editor) -->
    <!-- <HintInputModal
        :open="showHintModal"
        :vendor-name="selectedVendorForHint"
        :initial-hint="jobStore.getHint(selectedVendorForHint)"
        @close="showHintModal = false"
        @save="saveHint"
    /> -->

  </div>
</template>

<script setup lang="ts">
import { ref, computed, type PropType } from 'vue';
import { useJobStore, type JobResultItem } from '@/stores/job'; // Use the updated interface
import { FlagIcon as FlagIconOutline, MagnifyingGlassIcon, PaperAirplaneIcon, ArrowPathIcon } from '@heroicons/vue/24/outline';
import { FlagIcon as FlagIconSolid, ChevronUpIcon, ChevronDownIcon, ChevronUpDownIcon } from '@heroicons/vue/20/solid';
// import HintInputModal from './HintInputModal.vue'; // Import if using modal

// --- Define Header Interface ---
interface TableHeader {
  key: keyof JobResultItem; // Use keyof JobResultItem here
  label: string;
  sortable: boolean;
  minWidth?: string;
}
// --- END Define Header Interface ---

// --- Props ---
const props = defineProps({
  results: {
    type: Array as PropType<JobResultItem[] | null>, // This table handles JobResultItem
    required: true,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  error: {
    type: String as PropType<string | null>,
    default: null,
  },
  targetLevel: { // Pass the job's target level
    type: Number,
    required: true,
  }
});

const emit = defineEmits(['submit-flags']); // Emit event when submit button is clicked

// --- Store ---
const jobStore = useJobStore();

// --- Internal State ---
const searchTerm = ref('');
const sortKey = ref<keyof JobResultItem | null>('vendor_name'); // Default sort
const sortDirection = ref<'asc' | 'desc' | null>('asc'); // Default sort direction
// const showHintModal = ref(false); // State for modal
// const selectedVendorForHint = ref(''); // State for modal

// --- Table Headers Definition ---
// --- UPDATED: Apply TableHeader type ---
const headers = ref<TableHeader[]>([
  { key: 'vendor_name', label: 'Vendor Name', sortable: true, minWidth: '150px' },
  { key: 'level1_id', label: 'L1 ID', sortable: true, minWidth: '80px' },
  { key: 'level1_name', label: 'L1 Name', sortable: true, minWidth: '150px' },
  { key: 'level2_id', label: 'L2 ID', sortable: true, minWidth: '80px' },
  { key: 'level2_name', label: 'L2 Name', sortable: true, minWidth: '150px' },
  { key: 'level3_id', label: 'L3 ID', sortable: true, minWidth: '80px' },
  { key: 'level3_name', label: 'L3 Name', sortable: true, minWidth: '150px' },
  { key: 'level4_id', label: 'L4 ID', sortable: true, minWidth: '80px' },
  { key: 'level4_name', label: 'L4 Name', sortable: true, minWidth: '150px' },
  { key: 'level5_id', label: 'L5 ID', sortable: true, minWidth: '80px' },
  { key: 'level5_name', label: 'L5 Name', sortable: true, minWidth: '150px' },
  { key: 'final_confidence', label: 'Confidence', sortable: true, minWidth: '100px' },
  { key: 'final_status', label: 'Status', sortable: true, minWidth: '100px' },
  { key: 'classification_source', label: 'Source', sortable: true, minWidth: '80px' },
  { key: 'classification_notes_or_reason', label: 'Hint / Notes / Reason', sortable: false, minWidth: '200px' }, // Combined column
]);
// --- END UPDATED ---

// --- Computed Properties ---

const filteredAndSortedResults = computed(() => {
  // Ensure results is JobResultItem[] for this table
  const resultsData = props.results as JobResultItem[] | null;
  if (!resultsData) return [];

  let filtered = resultsData;

  // Filtering (case-insensitive, searches across multiple relevant fields)
  if (searchTerm.value) {
    const lowerSearchTerm = searchTerm.value.toLowerCase();
    filtered = filtered.filter(item =>
      item.vendor_name?.toLowerCase().includes(lowerSearchTerm) ||
      item.level1_id?.toLowerCase().includes(lowerSearchTerm) ||
      item.level1_name?.toLowerCase().includes(lowerSearchTerm) ||
      item.level2_id?.toLowerCase().includes(lowerSearchTerm) ||
      item.level2_name?.toLowerCase().includes(lowerSearchTerm) ||
      item.level3_id?.toLowerCase().includes(lowerSearchTerm) ||
      item.level3_name?.toLowerCase().includes(lowerSearchTerm) ||
      item.level4_id?.toLowerCase().includes(lowerSearchTerm) ||
      item.level4_name?.toLowerCase().includes(lowerSearchTerm) ||
      item.level5_id?.toLowerCase().includes(lowerSearchTerm) ||
      item.level5_name?.toLowerCase().includes(lowerSearchTerm) ||
      item.classification_notes_or_reason?.toLowerCase().includes(lowerSearchTerm) ||
      item.final_status?.toLowerCase().includes(lowerSearchTerm) ||
      item.classification_source?.toLowerCase().includes(lowerSearchTerm) ||
      // Include hint in search if vendor is flagged
      (jobStore.isFlagged(item.vendor_name) && jobStore.getHint(item.vendor_name)?.toLowerCase().includes(lowerSearchTerm))
    );
  }

  // Sorting
  if (sortKey.value && sortDirection.value) {
    const key = sortKey.value;
    const direction = sortDirection.value === 'asc' ? 1 : -1;

    // Use slice() to avoid sorting the original array directly if it's reactive
    filtered = filtered.slice().sort((a, b) => {
      // Handle sorting by hint if flagged
      let valA: any;
      let valB: any;
      if (key === 'classification_notes_or_reason') {
         valA = jobStore.isFlagged(a.vendor_name) ? jobStore.getHint(a.vendor_name) : a.classification_notes_or_reason;
         valB = jobStore.isFlagged(b.vendor_name) ? jobStore.getHint(b.vendor_name) : b.classification_notes_or_reason;
      } else {
        // Type assertion needed because TypeScript can't guarantee key is valid for both a and b
        valA = a[key as keyof JobResultItem];
        valB = b[key as keyof JobResultItem];
      }


      // Handle null/undefined values consistently (e.g., push them to the end)
      const aIsNull = valA === null || valA === undefined || valA === '';
      const bIsNull = valB === null || valB === undefined || valB === '';

      if (aIsNull && bIsNull) return 0;
      if (aIsNull) return 1 * direction; // Nulls/empty last
      if (bIsNull) return -1 * direction; // Nulls/empty last

      // Type-specific comparison
      if (typeof valA === 'string' && typeof valB === 'string') {
        return valA.localeCompare(valB) * direction;
      }
      if (typeof valA === 'number' && typeof valB === 'number') {
        return (valA - valB) * direction;
      }

      // Fallback for other types or mixed types (simple comparison)
      // Convert to string for consistent comparison if types differ or are complex
      const strA = String(valA).toLowerCase();
      const strB = String(valB).toLowerCase();
      if (strA < strB) return -1 * direction;
      if (strA > strB) return 1 * direction;
      return 0;
    });
  }

  return filtered;
});

// --- Methods ---

function sortBy(key: keyof JobResultItem) {
  if (sortKey.value === key) {
    // Cycle direction: asc -> desc -> null (no sort)
    if (sortDirection.value === 'asc') {
        sortDirection.value = 'desc';
    } else if (sortDirection.value === 'desc') {
        sortDirection.value = null;
        sortKey.value = null; // Clear key if sort is disabled
    } else { // Was null, start with asc
        sortDirection.value = 'asc';
    }
  } else {
    // Start new sort
    sortKey.value = key;
    sortDirection.value = 'asc';
  }
}

function getConfidenceClass(confidence: number | null | undefined): string {
  if (confidence === null || confidence === undefined) return 'text-gray-400';
  if (confidence >= 0.8) return 'text-green-700 font-medium';
  if (confidence >= 0.5) return 'text-yellow-700';
  return 'text-red-700';
}

function getStatusClass(status: string | null | undefined): string {
    switch(status?.toLowerCase()){
        case 'classified': return 'bg-green-100 text-green-800';
        case 'not possible': return 'bg-yellow-100 text-yellow-800';
        case 'error': return 'bg-red-100 text-red-800';
        default: return 'bg-gray-100 text-gray-800';
    }
}

// Highlight cells beyond the target classification depth
function getCellClass(item: JobResultItem, level: number): string {
    const baseClass = 'text-gray-700';
    const beyondDepthClass = 'text-gray-400 italic'; // Style for beyond depth

    // Check if the ID for this level exists and is not null/empty
    const levelIdKey = `level${level}_id` as keyof JobResultItem;
    const hasId = item[levelIdKey] !== null && item[levelIdKey] !== undefined && item[levelIdKey] !== '';

    if (level > props.targetLevel && hasId) {
        return beyondDepthClass;
    }
    return baseClass;
}

// --- Flagging and Hint Handling ---
function toggleFlag(vendorName: string) {
    if (jobStore.isFlagged(vendorName)) {
        jobStore.unflagVendor(vendorName);
    } else {
        jobStore.flagVendor(vendorName);
        // If using modal:
        // selectedVendorForHint.value = vendorName;
        // showHintModal.value = true;
    }
}

function updateHint(vendorName: string, hint: string) {
    jobStore.setHint(vendorName, hint);
}

// function saveHint(hint: string) {
//     if (selectedVendorForHint.value) {
//         jobStore.setHint(selectedVendorForHint.value, hint);
//     }
//     selectedVendorForHint.value = ''; // Clear selection
// }

async function submitFlags() {
    emit('submit-flags'); // Notify parent (JobStatus) to handle submission logic
}


// --- Helper Component for Sort Icons ---
const SortIcon = {
  props: {
    direction: {
      type: String as PropType<'asc' | 'desc' | null>,
      default: null,
    },
  },
  components: { ChevronUpIcon, ChevronDownIcon, ChevronUpDownIcon },
  template: `
    <span class="inline-block ml-1 w-4 h-4 align-middle">
      <ChevronUpIcon v-if="direction === 'asc'" class="w-4 h-4 text-gray-700" />
      <ChevronDownIcon v-else-if="direction === 'desc'" class="w-4 h-4 text-gray-700" />
      <ChevronUpDownIcon v-else class="w-4 h-4 text-gray-400 opacity-50" />
    </span>
  `,
};

</script>

<style scoped>
/* Add minimum width to table cells if needed for better layout */
/* th, td { min-width: 100px; } */
/* th:first-child, td:first-child { min-width: 150px; } */ /* Vendor Name */
/* th:last-child, td:last-child { min-width: 200px; } */ /* Notes */

/* Ensure table layout is fixed if content wrapping becomes an issue */
/* table { table-layout: fixed; } */

/* Style for cells beyond requested depth */
.text-gray-400.italic {
    /* Add a visual cue, e.g., slightly lighter background or border */
    /* background-color: #f9fafb; */
}
</style>

```
</file>

```vue
<file path='frontend/vue_frontend/src/components/JobStatus.vue'>
```vue
<template>
    <div v-if="jobStore.currentJobId" class="bg-white rounded-lg shadow-lg overflow-hidden border border-gray-200">
      <div class="bg-gray-100 text-gray-800 p-4 sm:p-5 border-b border-gray-200 flex justify-between items-center">
        <h4 class="text-xl font-semibold mb-0">Job Status</h4>
         <!-- Link to Parent Job (if this is a Review Job) -->
         <button v-if="jobDetails?.job_type === 'REVIEW' && jobDetails.parent_job_id"
                @click="viewParentJob"
                title="View Original Classification Job"
                class="text-xs inline-flex items-center px-2.5 py-1.5 border border-gray-300 shadow-sm font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-primary">
            <ArrowUturnLeftIcon class="h-4 w-4 mr-1.5 text-gray-500"/>
            View Original Job
        </button>
      </div>
      <div class="p-6 sm:p-8 space-y-6"> <!-- Increased spacing -->

        <!-- Error Message -->
        <div v-if="errorMessage" class="p-3 bg-yellow-100 border border-yellow-300 text-yellow-800 rounded-md text-sm flex items-center">
            <ExclamationTriangleIcon class="h-5 w-5 mr-2 text-yellow-600 flex-shrink-0"/>
            <span>{{ errorMessage }}</span>
        </div>

        <!-- Reclassification Started Message -->
        <div v-if="showReclassifySuccessMessage && jobStore.lastReviewJobId" class="p-3 bg-green-100 border border-green-300 text-green-800 rounded-md text-sm flex items-center justify-between">
             <div class="flex items-center">
                 <CheckCircleIcon class="h-5 w-5 mr-2 text-green-600 flex-shrink-0"/>
                 <span>Re-classification job started successfully (ID: {{ jobStore.lastReviewJobId }}).</span>
             </div>
             <button @click="viewReviewJob(jobStore.lastReviewJobId!)" class="ml-4 text-xs font-semibold text-green-700 hover:text-green-900 underline">View Review Job</button>
        </div>


        <!-- Job ID & Status Row -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm border-b border-gray-100 pb-4">
          <div>
             <strong class="text-gray-600 block mb-1">Job ID:</strong>
             <!-- Display the full ID for clarity during debugging -->
             <span class="text-gray-900 font-mono text-xs bg-gray-100 px-2 py-1 rounded break-all">{{ jobStore.currentJobId }}</span>
             <span v-if="jobDetails?.job_type === 'REVIEW'" class="ml-2 inline-block px-1.5 py-0.5 rounded text-xs font-semibold bg-purple-100 text-purple-800 align-middle">REVIEW</span>
          </div>
           <div class="flex items-center space-x-2">
             <strong class="text-gray-600">Status:</strong>
             <span class="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wide" :class="statusBadgeClass">
                 <!-- Use jobDetails.status directly -->
                 {{ jobDetails?.status || 'Loading...' }}
             </span>
           </div>
        </div>

        <!-- Stage & Error (if failed) -->
        <div class="text-sm">
            <strong class="text-gray-600 block mb-1">Current Stage:</strong>
            <span class="text-gray-800 font-medium">{{ formattedStage }}</span>
            <!-- Use jobDetails.error_message -->
            <div v-if="jobDetails?.status === 'failed' && jobDetails?.error_message" class="mt-3 p-4 bg-red-50 border border-red-200 text-red-800 rounded-md text-xs shadow-sm">
              <strong class="block mb-1 font-semibold">Error Details:</strong>
              <p class="whitespace-pre-wrap">{{ jobDetails.error_message }}</p> <!-- Preserve whitespace -->
            </div>
        </div>

        <!-- Progress Bar -->
        <div>
          <label class="block text-sm font-medium text-gray-600 mb-1.5">Progress:</label>
          <div class="w-full bg-gray-200 rounded-full h-3 overflow-hidden"> <!-- Slimmer progress bar -->
            <div
              class="h-3 rounded-full transition-all duration-500 ease-out"
              :class="progressColorClass"
              :style="{ width: progressPercent + '%' }"
              ></div>
          </div>
          <div class="text-right text-xs text-gray-500 mt-1">{{ progressPercent }}% Complete</div>
        </div>

        <!-- Timestamps Row -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-gray-500 border-t border-gray-100 pt-5">
            <div>
                 <strong class="block text-gray-600 mb-0.5">Created:</strong>
                 <span>{{ formattedCreatedAt }}</span>
            </div>
            <div>
                 <strong class="block text-gray-600 mb-0.5">Updated:</strong>
                 <span>{{ formattedUpdatedAt }}</span>
            </div>
             <div>
                <strong class="block text-gray-600 mb-0.5">Est. Completion:</strong>
                <span>{{ formattedEstimatedCompletion }}</span>
            </div>
        </div>

        <!-- Notification Section -->
        <div v-if="canRequestNotify" class="pt-5 border-t border-gray-100">
            <label for="notificationEmail" class="block text-sm font-medium text-gray-700 mb-1.5">Get Notified Upon Completion</label>
            <div class="flex flex-col sm:flex-row sm:space-x-2">
                <input type="email"
                       class="mb-2 sm:mb-0 flex-grow block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-primary focus:border-primary sm:text-sm disabled:opacity-60 disabled:bg-gray-100"
                       id="notificationEmail"
                       placeholder="Enter your email"
                       v-model="notificationEmail"
                       :disabled="isNotifyLoading" />
                <button
                    type="button"
                    @click="requestNotification"
                    :disabled="isNotifyLoading || !notificationEmail"
                    class="w-full sm:w-auto inline-flex justify-center items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    <svg v-if="isNotifyLoading" class="animate-spin -ml-1 mr-2 h-4 w-4 text-gray-700" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                       <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                       <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                     <EnvelopeIcon v-else class="h-4 w-4 mr-2 -ml-1 text-gray-500"/>
                    {{ isNotifyLoading ? 'Sending...' : 'Notify Me' }}
                </button>
            </div>
            <!-- Notification Feedback -->
            <p v-if="notifyMessage" :class="notifyMessageIsError ? 'text-red-600' : 'text-green-600'" class="mt-2 text-xs">{{ notifyMessage }}</p>
        </div>

        <!-- Download Section (Only for completed CLASSIFICATION jobs) -->
        <div v-if="jobDetails?.status === 'completed' && jobDetails?.job_type === 'CLASSIFICATION'" class="pt-5 border-t border-gray-100">
          <button @click="downloadResults"
                  class="w-full flex justify-center items-center px-4 py-2.5 border border-transparent rounded-md shadow-sm text-base font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  :disabled="isDownloadLoading">
             <!-- Spinner SVG -->
             <svg v-if="isDownloadLoading" class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
             </svg>
             <!-- Download Icon -->
             <ArrowDownTrayIcon v-else class="h-5 w-5 mr-2 -ml-1" />
            {{ isDownloadLoading ? ' Preparing Download...' : 'Download Excel Results' }} <!-- Updated Text -->
          </button>
          <p v-if="downloadError" class="mt-2 text-xs text-red-600 text-center">{{ downloadError }}</p>
        </div>

        <!-- Stats Section (Rendered within JobStatus when complete) -->
         <!-- Use jobDetails.id -->
         <JobStats v-if="jobDetails?.status === 'completed' && jobDetails?.id" :job-id="jobDetails.id" />

        <!-- ***** UPDATED: Conditional Detailed Results Table Section ***** -->
        <!-- Show CLASSIFICATION results table -->
        <JobResultsTable
            v-if="jobDetails?.status === 'completed' && jobDetails?.id && jobDetails?.job_type === 'CLASSIFICATION'"
            :results="jobStore.jobResults as JobResultItem[] | null"
            :loading="jobStore.resultsLoading"
            :error="jobStore.resultsError"
            :target-level="jobDetails.target_level || 5"
            @submit-flags="handleSubmitFlags" /> <!-- Listen for submit event -->

        <!-- Show REVIEW results table -->
        <ReviewResultsTable
            v-if="jobDetails?.status === 'completed' && jobDetails?.id && jobDetails?.job_type === 'REVIEW'"
            :results="jobStore.jobResults as ReviewResultItem[] | null"
            :loading="jobStore.resultsLoading"
            :error="jobStore.resultsError"
            :target-level="jobDetails.target_level || 5"
            @submit-flags="handleSubmitFlags" /> <!-- Listen for submit event -->
        <!-- ***** END UPDATED Section ***** -->

      </div>
    </div>
      <div v-else class="text-center py-10 text-gray-500">
        <!-- Message shown when no job is selected -->
        <!-- Select a job from the history or upload a new file. -->
      </div>
  </template>

  <script setup lang="ts">
  import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
  import apiService from '@/services/api';
  import { useJobStore, type JobDetails, type JobResultItem, type ReviewResultItem } from '@/stores/job';
  import JobStats from './JobStats.vue';
  import JobResultsTable from './JobResultsTable.vue';
  import ReviewResultsTable from './ReviewResultsTable.vue'; // Import the new component
  import { EnvelopeIcon, ArrowDownTrayIcon, ExclamationTriangleIcon, ArrowUturnLeftIcon, CheckCircleIcon } from '@heroicons/vue/20/solid';

  const POLLING_INTERVAL = 5000; // Poll every 5 seconds
  const jobStore = useJobStore();
  // Use jobDetails directly from the store
  const jobDetails = computed(() => jobStore.jobDetails);
  const isLoading = ref(false); // Tracks if a poll request is currently in flight
  const errorMessage = ref<string | null>(null); // Stores polling or general errors
  const pollingIntervalId = ref<number | null>(null); // Stores the ID from setInterval
  const showReclassifySuccessMessage = ref(false); // Control visibility of success message

  // --- Notification State ---
  const notificationEmail = ref('');
  const isNotifyLoading = ref(false);
  const notifyMessage = ref<string | null>(null);
  const notifyMessageIsError = ref(false);

  // --- Download State ---
  const isDownloadLoading = ref(false);
  const downloadError = ref<string | null>(null);

  // --- Computed Properties ---
  const formattedStage = computed(() => {
    const stage = jobDetails.value?.current_stage;
    const status = jobDetails.value?.status;
    if (status === 'completed') return 'Completed';
    if (status === 'failed') return 'Failed';
    if (status === 'pending') return 'Pending Start';
    if (!stage) return 'Loading...';

    // Map internal stage names to user-friendly display names
    const stageNames: { [key: string]: string } = {
      'ingestion': 'Ingesting File',
      'normalization': 'Normalizing Data',
      'classification_level_1': 'Classifying (L1)',
      'classification_level_2': 'Classifying (L2)',
      'classification_level_3': 'Classifying (L3)',
      'classification_level_4': 'Classifying (L4)',
      'classification_level_5': 'Classifying (L5)',
      'search_unknown_vendors': 'Researching Vendors',
      'reclassification': 'Re-classifying', // Added stage
      'result_generation': 'Generating Results',
      'pending': 'Pending Start', // Added pending stage mapping
    };
    return stageNames[stage] || stage; // Fallback to raw stage name if not mapped
  });

  const progressPercent = computed(() => {
    const status = jobDetails.value?.status;
    const progress = jobDetails.value?.progress ?? 0;
    if (status === 'completed') return 100;
    if (status === 'pending') return 0; // Show 0% for pending
    // Ensure progress is between 0 and 100
    return Math.max(0, Math.min(100, Math.round(progress * 100)));
  });

  const statusBadgeClass = computed(() => {
      switch (jobDetails.value?.status) {
          case 'completed': return 'bg-green-100 text-green-800';
          case 'failed': return 'bg-red-100 text-red-800';
          case 'processing': return 'bg-blue-100 text-blue-800 animate-pulse'; // Add pulse for processing
          default: return 'bg-gray-100 text-gray-800'; // Pending or loading
      }
  });

  const progressColorClass = computed(() => {
    const status = jobDetails.value?.status;
    if (status === 'completed') return 'bg-green-500';
    if (status === 'failed') return 'bg-red-500';
    // Use primary color and pulse animation for processing/pending
    return 'bg-primary animate-pulse';
  });

  const formatDateTime = (isoString: string | null | undefined): string => {
      if (!isoString) return 'N/A';
      try {
          // Use user's locale and common options
          return new Date(isoString).toLocaleString(undefined, {
              year: 'numeric', month: 'short', day: 'numeric',
              hour: 'numeric', minute: '2-digit', hour12: true
          });
      } catch {
          return 'Invalid Date';
      }
  };

  const formattedUpdatedAt = computed(() => formatDateTime(jobDetails.value?.updated_at));

  const formattedEstimatedCompletion = computed(() => {
      const status = jobDetails.value?.status;
      if (status === 'completed' && jobDetails.value?.completed_at) {
          return formatDateTime(jobDetails.value.completed_at);
      }
      // Assuming backend provides 'estimated_completion' during processing
      // --- CHECK FIELD NAME ---
      // Check if the field is 'estimated_completion' or something else in JobDetails
      const estCompletion = jobDetails.value?.estimated_completion; // Use the actual field name
      if (status === 'processing' && estCompletion) {
          return `${formatDateTime(estCompletion)} (est.)`;
      }
      // --- END CHECK ---
      if (status === 'processing') return 'Calculating...';
      if (status === 'failed') return 'N/A';
      if (status === 'pending') return 'Pending Start';
      return 'N/A';
  });

  const canRequestNotify = computed(() => {
      const status = jobDetails.value?.status;
      return status === 'pending' || status === 'processing';
  });

  // --- Methods ---
  const pollJobStatus = async (jobId: string | null | undefined) => {
     // Check if we should still be polling this job
     if (!jobId || jobStore.currentJobId !== jobId) {
         console.log(`JobStatus: [pollJobStatus] Stopping polling because jobId (${jobId}) doesn't match store (${jobStore.currentJobId}) or is null.`); // LOGGING
         stopPolling();
         return;
     }

     // Avoid concurrent polls
     if (isLoading.value) {
         console.log(`JobStatus: [pollJobStatus] Skipping poll for ${jobId} as another poll is already in progress.`); // LOGGING
         return;
     }

     isLoading.value = true;
     console.log(`JobStatus: [pollJobStatus] Polling status for job ${jobId}...`); // LOGGING
    try {
        const data = await apiService.getJobStatus(jobId);
        // IMPORTANT: Check if the job ID is still the current one *after* the API call returns
        if (jobStore.currentJobId === jobId) {
            console.log(`JobStatus: [pollJobStatus] Received status data for ${jobId}: Status=${data.status}, Progress=${data.progress}, Stage=${data.current_stage}, Type=${data.job_type}`); // LOGGING
            jobStore.updateJobDetails(data); // Update the store
            errorMessage.value = null; // Clear previous errors on successful poll

            // Stop polling if job is completed or failed
            if (data.status === 'completed' || data.status === 'failed') {
                console.log(`JobStatus: [pollJobStatus] Job ${jobId} reached terminal state (${data.status}). Stopping polling.`); // LOGGING
                stopPolling();
                // --- UPDATED: Trigger results fetch if completed ---
                if (data.status === 'completed') {
                    console.log(`JobStatus: [pollJobStatus] Job ${jobId} completed. Triggering fetchJobResults.`); // LOGGING
                    // Check if results are already loading or present before fetching again
                    if (!jobStore.resultsLoading && !jobStore.jobResults) {
                        jobStore.fetchJobResults(jobId); // Fetch detailed results
                    } else {
                         console.log(`JobStatus: [pollJobStatus] Job ${jobId} completed, but results already loading or present. Skipping fetch.`); // LOGGING
                    }
                }
                // --- END UPDATED ---
            }
        } else {
             console.log(`JobStatus: [pollJobStatus] Job ID changed from ${jobId} to ${jobStore.currentJobId} during API call. Ignoring stale data.`); // LOGGING
             // Don't update the store with stale data
        }
    } catch (error: any) {
        console.error(`JobStatus: [pollJobStatus] Error polling status for ${jobId}:`, error); // LOGGING
        // Only set error if the failed poll was for the *current* job ID
        if (jobStore.currentJobId === jobId) {
            errorMessage.value = `Polling Error: ${error.message || 'Failed to fetch status.'}`;
        }
        // Consider retrying after a longer interval before stopping completely
        stopPolling(); // Stop polling on error for now
    } finally {
        // Only set isLoading to false if the poll was for the current job
        if (jobStore.currentJobId === jobId) {
            isLoading.value = false;
        }
    }
  };

  const startPolling = (jobId: string | null | undefined) => {
    if (!jobId) {
        console.log("JobStatus: [startPolling] Cannot start polling, no jobId provided."); // LOGGING
        return;
    }
    stopPolling(); // Ensure any existing polling is stopped first
    console.log(`JobStatus: [startPolling] Starting polling for job ${jobId}.`); // LOGGING
    pollJobStatus(jobId); // Poll immediately

    pollingIntervalId.value = window.setInterval(() => {
        console.log(`JobStatus: [setInterval] Checking poll condition for ${jobId}. Current store ID: ${jobStore.currentJobId}, Status: ${jobStore.jobDetails?.status}`); // LOGGING
        // Check condition inside interval as well
        if (jobStore.currentJobId === jobId && jobStore.jobDetails?.status !== 'completed' && jobStore.jobDetails?.status !== 'failed') {
            pollJobStatus(jobId);
        } else {
            console.log(`JobStatus: [setInterval] Condition not met, stopping polling.`); // LOGGING
            // Stop if job ID changed or job finished between polls
            stopPolling();
        }
    }, POLLING_INTERVAL);
  };

  const stopPolling = () => {
    if (pollingIntervalId.value !== null) {
        console.log(`JobStatus: [stopPolling] Stopping polling interval ID ${pollingIntervalId.value}.`); // LOGGING
        clearInterval(pollingIntervalId.value);
        pollingIntervalId.value = null;
    } else {
        // console.log(`JobStatus: [stopPolling] No active polling interval to stop.`); // LOGGING (Optional)
    }
  };

  const requestNotification = async () => {
     // Use jobDetails.id
     const currentId = jobDetails.value?.id;
     if (!currentId || !notificationEmail.value) return;
     isNotifyLoading.value = true;
     notifyMessage.value = null;
     notifyMessageIsError.value = false;
     console.log(`JobStatus: Requesting notification for ${currentId} to ${notificationEmail.value}`); // LOGGING
    try {
        const response = await apiService.requestNotification(currentId, notificationEmail.value);
        console.log(`JobStatus: Notification request successful:`, response); // LOGGING
        notifyMessage.value = response.message || 'Notification request sent!';
        notificationEmail.value = ''; // Clear input on success
    } catch (error: any) {
        console.error(`JobStatus: Notification request failed:`, error); // LOGGING
        notifyMessage.value = `Error: ${error.message || 'Failed to send request.'}`;
        notifyMessageIsError.value = true;
    } finally {
        isNotifyLoading.value = false;
        // Clear message after a delay
        setTimeout(() => { notifyMessage.value = null; }, 5000);
    }
  };

  const downloadResults = async () => {
     // Use jobDetails.id
     const currentId = jobDetails.value?.id;
     if (!currentId) return;
     isDownloadLoading.value = true;
     downloadError.value = null;
     console.log(`JobStatus: Attempting download for ${currentId}`); // LOGGING
    try {
        const { blob, filename } = await apiService.downloadResults(currentId);
        console.log(`JobStatus: Download blob received, filename: ${filename}`); // LOGGING
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        console.log(`JobStatus: Download triggered for ${filename}`); // LOGGING
    } catch (error: any) {
        console.error(`JobStatus: Download failed:`, error); // LOGGING
        downloadError.value = `Download failed: ${error.message || 'Could not download results.'}`;
    } finally {
        isDownloadLoading.value = false;
    }
  };

  // --- ADDED: Reclassification Submission ---
  const handleSubmitFlags = async () => {
    console.log("JobStatus: Handling submit flags event...");
    const reviewJobId = await jobStore.submitFlagsForReview();
    if (reviewJobId) {
        // Show success message
        showReclassifySuccessMessage.value = true;
        // Hide message after a delay
        setTimeout(() => { showReclassifySuccessMessage.value = false; }, 7000);
        // Optionally fetch history to update the list
        jobStore.fetchJobHistory();
        // Do NOT automatically navigate - let user click the link in the success message
        // jobStore.setCurrentJobId(reviewJobId);
    } else {
        // Error is handled within the store and displayed by the table component
        console.log("JobStatus: Flag submission failed (error handled in store).");
    }
  };

  // --- ADDED: Navigation ---
  const viewParentJob = () => {
      if (jobDetails.value?.parent_job_id) {
          jobStore.setCurrentJobId(jobDetails.value.parent_job_id);
      }
  };

  const viewReviewJob = (reviewJobId: string) => {
       jobStore.setCurrentJobId(reviewJobId);
       showReclassifySuccessMessage.value = false; // Hide message on navigation
  };


  // --- Lifecycle Hooks ---
  onMounted(() => {
      console.log(`JobStatus: Mounted. Current job ID from store: ${jobStore.currentJobId}`); // LOGGING
      if (jobStore.currentJobId) {
          errorMessage.value = null;
          // Fetch initial details if not already present or if status is unknown/stale
          // Use jobDetails.id for comparison
          const currentDetails = jobStore.jobDetails;
          // Fetch details if they are missing OR if the ID matches but type/status might be stale
          if (!currentDetails || currentDetails.id !== jobStore.currentJobId) {
              console.log(`JobStatus: Fetching initial details and starting polling for ${jobStore.currentJobId}`); // LOGGING
              startPolling(jobStore.currentJobId);
          } else if (currentDetails.status === 'completed') {
              console.log(`JobStatus: Job ${jobStore.currentJobId} already completed. Fetching results if needed.`); // LOGGING
              stopPolling(); // Ensure polling is stopped
              // --- UPDATED: Fetch results only if not already present/loading ---
              if (!jobStore.resultsLoading && !jobStore.jobResults) {
                  jobStore.fetchJobResults(jobStore.currentJobId); // Fetch results if already completed on mount
              }
              // --- END UPDATED ---
          } else if (currentDetails.status === 'failed') {
              console.log(`JobStatus: Job ${jobStore.currentJobId} already failed. Not polling or fetching results.`); // LOGGING
              stopPolling(); // Ensure polling is stopped
          } else {
              // Status is pending or processing, start polling
              console.log(`JobStatus: Job ${jobStore.currentJobId} is ${currentDetails.status}. Starting polling.`); // LOGGING
              startPolling(jobStore.currentJobId);
          }
      }
  });


  onUnmounted(() => {
      console.log("JobStatus: Unmounted, stopping polling."); // LOGGING
      stopPolling();
  });

  // --- Watchers ---
  // Watch for changes in the store's currentJobId
  watch(() => jobStore.currentJobId, (newJobId: string | null | undefined) => {
      console.log(`JobStatus: Watched currentJobId changed to: ${newJobId}`); // LOGGING
      showReclassifySuccessMessage.value = false; // Hide success message on job change
      if (newJobId) {
          // Reset component state when job ID changes
          errorMessage.value = null;
          downloadError.value = null;
          notifyMessage.value = null;
          notificationEmail.value = '';
          isDownloadLoading.value = false;
          isNotifyLoading.value = false;

          // Fetch details or start polling if needed for the new job
          const currentDetails = jobStore.jobDetails;
          // Fetch details if they are missing OR if the ID matches but type/status might be stale
          if (!currentDetails || currentDetails.id !== newJobId) {
               console.log(`JobStatus: Fetching initial details and starting polling due to job ID change to ${newJobId}`); // LOGGING
               startPolling(newJobId);
          } else if (currentDetails.status === 'completed') {
               console.log(`JobStatus: Job ${newJobId} already completed. Fetching results if needed.`); // LOGGING
               stopPolling(); // Ensure polling is stopped
               // --- UPDATED: Fetch results only if not already present/loading ---
               if (!jobStore.resultsLoading && !jobStore.jobResults) {
                    jobStore.fetchJobResults(newJobId); // Fetch results if already completed
               }
               // --- END UPDATED ---
          } else if (currentDetails.status === 'failed') {
               console.log(`JobStatus: Job ${newJobId} already failed. Not polling or fetching results.`); // LOGGING
               stopPolling(); // Ensure polling is stopped
          } else {
               // Status is pending or processing, start polling
               console.log(`JobStatus: Job ${newJobId} is ${currentDetails.status}. Starting polling.`); // LOGGING
               startPolling(newJobId);
          }
      } else {
          // Job ID was cleared
          console.log("JobStatus: Job ID cleared, stopping polling."); // LOGGING
          stopPolling();
      }
  });

  // Watch for the job status changing to a terminal state (this handles updates from polling)
  watch(() => jobStore.jobDetails?.status, (newStatus: JobDetails['status'] | undefined, oldStatus) => {
      const currentId = jobStore.currentJobId;
      if (!currentId) return; // Don't do anything if no job is selected

      console.log(`JobStatus: Watched job status changed from ${oldStatus} to: ${newStatus} for job ${currentId}`); // LOGGING

      if (newStatus === 'completed' && oldStatus !== 'completed') {
          console.log(`JobStatus: Job ${currentId} just completed. Stopping polling and fetching results if needed.`); // LOGGING
          stopPolling();
          // --- UPDATED: Fetch results only if not already present/loading ---
          if (!jobStore.resultsLoading && !jobStore.jobResults) {
            jobStore.fetchJobResults(currentId); // Fetch detailed results when status changes to completed
          }
          // --- END UPDATED ---
      } else if (newStatus === 'failed' && oldStatus !== 'failed') {
          console.log(`JobStatus: Job ${currentId} just failed. Stopping polling.`); // LOGGING
          stopPolling();
      }
  });

  </script>
```
</file>

<file path='frontend/vue_frontend/src/App.vue'>
```vue
<template>
  <div class="flex flex-col min-h-screen">
    <Navbar
      :is-logged-in="authStore.isAuthenticated"
      :username="authStore.username"
      @logout="handleLogout"
    />

    <!-- Main content area -->
    <main role="main" class="flex-grow w-full mx-auto">
      <!-- Render based on viewStore and potentially route -->
      <LandingPage
        v-if="viewStore.currentView === 'landing' && !isResetPasswordRoute"
        @login-successful="handleLoginSuccess"
      />
      <div v-else-if="isResetPasswordRoute" class="max-w-xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <!-- ResetPassword component rendered directly based on route -->
        <ResetPassword
          :token="resetToken"
          @close="navigateToLanding"
          @show-login="navigateToLanding"
          @show-forgot-password="navigateToForgotPassword"
        />
      </div>
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8" v-else-if="viewStore.currentView === 'app'">
        <!-- AppContent manages JobUpload, JobHistory, JobStatus -->
        <AppContent />
      </div>
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8" v-else-if="viewStore.currentView === 'admin'">
        <UserManagement />
      </div>
    </main>

    <Footer />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import Navbar from './components/Navbar.vue';
import LandingPage from './components/LandingPage.vue';
import AppContent from './components/AppContent.vue';
import Footer from './components/Footer.vue';
import UserManagement from './components/UserManagement.vue';
import ResetPassword from './components/ResetPassword.vue'; // Import ResetPassword
import { useAuthStore } from './stores/auth';
import { useJobStore } from './stores/job';
import { useViewStore } from './stores/view';

const authStore = useAuthStore();
const jobStore = useJobStore();
const viewStore = useViewStore();

// --- Password Reset Route Handling ---
// This simulates basic routing without Vue Router.
// For a real app, use Vue Router for proper route handling.
const currentPath = ref(window.location.pathname);
const currentSearch = ref(window.location.search); // Track query params
const resetToken = ref('');

const isResetPasswordRoute = computed(() => {
  const match = currentPath.value.match(/^\/reset-password\/(.+)/);
  if (match && match[1]) {
    resetToken.value = match[1]; // Extract token from path
    return true;
  }
  resetToken.value = '';
  return false;
});

// Function to update path on navigation (e.g., history API changes)
const updateRouteInfo = () => {
  currentPath.value = window.location.pathname;
  currentSearch.value = window.location.search;
  console.log("App.vue: Route updated - Path:", currentPath.value, "Search:", currentSearch.value); // Debugging
};

// Simulate navigation (replace with router.push in a real app)
const navigateTo = (path: string, searchParams: URLSearchParams | null = null) => {
    let url = path;
    if (searchParams && searchParams.toString()) {
        url += `?${searchParams.toString()}`;
    }
    window.history.pushState({}, '', url);
    updateRouteInfo(); // Update internal state
    // Reset view store if navigating away from app/admin
    if (path === '/' || path === '/forgot-password') {
        if (!authStore.isAuthenticated) {
            viewStore.setView('landing');
        }
    }
    // If navigating to the main app view, check for job_id
    if (path === '/') { // Assuming '/' is the main app view when logged in
        handleAppNavigation(searchParams);
    }
};

const navigateToLanding = () => navigateTo('/');
const navigateToForgotPassword = () => {
    // In LandingPage, this would typically show the ForgotPassword modal/component
    // Since we don't have full routing, we might just navigate to '/' and rely on LandingPage state
    navigateTo('/');
    // You might need a way to signal LandingPage to show the forgot password form immediately
    // e.g., using a query parameter or a temporary state variable (less ideal)
    // For simplicity, just navigate to landing. The user clicks "Forgot Password" again there.
};


// Update path when browser back/forward buttons are used
window.addEventListener('popstate', updateRouteInfo);

onMounted(() => {
  updateRouteInfo(); // Initial route check
});
// --- End Password Reset Route Handling ---

// --- App Navigation Logic ---
const handleAppNavigation = (searchParams: URLSearchParams | null) => {
    const params = searchParams || new URLSearchParams(currentSearch.value);
    const jobIdFromUrl = params.get('job_id');
    console.log("App.vue: Handling app navigation. Job ID from URL:", jobIdFromUrl); // Debugging
    // If authenticated and a job ID is present, set it in the store
    // Let the store decide if it's a new ID or a refresh
    if (authStore.isAuthenticated && jobIdFromUrl) {
        console.log(`App.vue: Setting Job ID from URL: ${jobIdFromUrl}`);
        jobStore.setCurrentJobId(jobIdFromUrl);
    } else if (authStore.isAuthenticated && !jobIdFromUrl && jobStore.currentJobId) {
         // If authenticated and URL has no job_id, but store has one, clear it
         console.log(`App.vue: URL has no job_id, clearing store's currentJobId.`);
         jobStore.setCurrentJobId(null);
    }
};


const handleLogout = () => {
  authStore.logout();
  jobStore.clearJob();
  viewStore.setView('landing');
  navigateToLanding(); // Go to landing page URL
};

const handleLoginSuccess = () => {
  console.log('Login successful, App.vue notified.');
  viewStore.setView('app');
  authStore.fetchCurrentUserDetails();
  // Check URL for job_id immediately after login
  const urlParams = new URLSearchParams(window.location.search);
  handleAppNavigation(urlParams);
};

// Watch auth state to set initial view (excluding reset password route)
watch(() => authStore.isAuthenticated, (isAuth, wasAuth) => {
  console.log("App.vue: Auth state changed:", isAuth); // Debugging
  if (!isResetPasswordRoute.value) { // Only change view if not on reset password page
    if (isAuth && viewStore.currentView === 'landing') {
      console.log("App.vue: Auth true, setting view to 'app'");
      viewStore.setView('app');
      // Check URL for job_id when becoming authenticated
      const urlParams = new URLSearchParams(window.location.search);
      handleAppNavigation(urlParams);
    } else if (!isAuth && wasAuth) { // Only switch to landing if user was previously authenticated (i.e., logged out)
      console.log("App.vue: Auth false, setting view to 'landing'");
      viewStore.setView('landing');
    }
  }
}, { immediate: false }); // Change immediate to false to avoid race conditions on initial load

// Watch for route changes (path or search) to potentially update view or job ID
watch([currentPath, currentSearch], ([newPath, newSearch], [oldPath, oldSearch]) => {
    console.log("App.vue: Route watcher triggered. New Path:", newPath, "New Search:", newSearch); // Debugging
    if (!isResetPasswordRoute.value && !authStore.isAuthenticated) {
        console.log("App.vue: Not reset route, not authenticated, setting view to landing.");
        viewStore.setView('landing');
    } else if (authStore.isAuthenticated && viewStore.currentView === 'app') {
        // If already in the app view, check if the job_id param changed
        const oldParams = new URLSearchParams(oldSearch);
        const newParams = new URLSearchParams(newSearch);
        const oldJobId = oldParams.get('job_id');
        const newJobId = newParams.get('job_id');

        if (newJobId !== oldJobId) {
             console.log(`App.vue: job_id param changed from ${oldJobId} to ${newJobId}. Updating store.`);
             jobStore.setCurrentJobId(newJobId); // Let the store handle null/new value
        }
    }
    // Add other route-based view logic if needed
}, { deep: true }); // Use deep watch if needed, though path/search are primitive


onMounted(() => {
  authStore.checkAuthStatus().then(() => {
    // This runs after checkAuthStatus completes
    console.log("App.vue: onMounted - checkAuthStatus completed. Auth state:", authStore.isAuthenticated);
    updateRouteInfo(); // Ensure route info is current
    if (authStore.isAuthenticated) {
      authStore.fetchCurrentUserDetails();
      // Set initial view based on auth state *after* checking auth
      if (!isResetPasswordRoute.value) {
        viewStore.setView('app');
      }
      handleAppNavigation(null); // Check URL for job_id after auth check
    } else {
       if (!isResetPasswordRoute.value) {
         viewStore.setView('landing');
       }
    }
  });
});

// Cleanup listener on unmount
import { onUnmounted } from 'vue';
onUnmounted(() => {
  window.removeEventListener('popstate', updateRouteInfo);
});
</script>

<style>
/* Ensure html, body, and #app take full height if needed */
html, body, #app {
  height: 100%;
  margin: 0;
}
</style>
```
</file>

---

This completes the implementation for Feature 2, including backend API endpoints, Celery tasks, database model changes, schema updates, and frontend components/store modifications to support the interactive re-classification workflow. Remember to run database migrations (e.g., using Alembic) to apply the changes to the `jobs` table.