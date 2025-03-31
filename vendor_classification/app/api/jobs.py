# app/api/jobs.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from core.database import get_db
from api.auth import get_current_user
from models.user import User
from models.job import Job, JobStatus
from schemas.job import JobResponse # Import the new schema
from core.logging_config import get_logger, set_log_context

logger = get_logger("vendor_classification.api.jobs")

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