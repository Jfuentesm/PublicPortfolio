# <file path='app/api/jobs.py'>
# app/api/jobs.py
from fastapi import APIRouter, Depends, HTTPException, Query, status, Path # Added Path
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import datetime
import logging # Import logging

from core.database import get_db
from api.auth import get_current_user
from models.user import User
from models.job import Job, JobStatus
# --- UPDATED: Import JobResultItem ---
from schemas.job import JobResponse, JobResultItem
# --- END UPDATED ---
from core.logging_config import get_logger
from core.log_context import set_log_context
from core.config import settings # Need settings for file path construction


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
    skip: int = Query(0, ge=0, description="Number of jobs to skip for pagination"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of jobs to return"),
):
    """
    List jobs for the current user. Admins can see all jobs (optional enhancement).
    Supports filtering by status and date range, and pagination.
    """
    set_log_context({"username": current_user.username})
    logger.info("Fetching job history", extra={
        "status_filter": status_filter,
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

    # LOGGING: Log the job details being returned, especially target_level
    logger.info(f"Returning details for job ID: {job_id}", extra={"job_status": job.status, "target_level": job.target_level})
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
    logger.info(f"Returning statistics for job ID: {job_id}")
    logger.debug(f"Raw stats from DB for job {job_id}: {job.stats}") # Log the actual stats dict

    # The stats are stored as JSON in the Job model
    return job.stats if job.stats else {}


# --- ADDED: Endpoint for Detailed Results ---
@router.get("/{job_id}/results", response_model=List[JobResultItem])
async def read_job_results(
    job_id: str = Path(..., title="The ID of the job to get detailed results for"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve the detailed classification results for a specific completed job.
    Returns a list of items conforming to the JobResultItem schema.
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
                       extra={"job_id": job_id, "status": job.status})
        # Return empty list instead of 400, as the job exists but results aren't ready
        return []
        # Alternatively, raise HTTPException:
        # raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job is not completed yet.")

    if not job.detailed_results:
        logger.warning(f"Job {job_id} is completed but has no detailed results stored.", extra={"job_id": job_id})
        return []

    # The detailed_results field should already contain a list of dicts
    # matching the JobResultItem schema, prepared by the background task.
    # Pydantic will validate this structure upon return.
    logger.info(f"Returning {len(job.detailed_results)} detailed result items for job ID: {job_id}")
    # Pydantic should automatically validate the list of dicts against List[JobResultItem]
    return job.detailed_results
# --- END ADDED ---


@router.get("/{job_id}/download")
async def download_job_results(
    job_id: str = Path(..., title="The ID of the job to download results for"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Downloads the output Excel file for a completed job.
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

    if job.status != JobStatus.COMPLETED.value or not job.output_file_name:
        logger.warning(f"Download requested but job not completed or output file missing",
                       extra={"job_id": job_id, "status": job.status, "output_file": job.output_file_name})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job not completed or output file not available.")

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