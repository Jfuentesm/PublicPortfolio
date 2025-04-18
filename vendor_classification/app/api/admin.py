# app/api/admin.py
from fastapi import APIRouter, Depends, HTTPException, status, Path # <<< ADDED Path
from sqlalchemy.orm import Session
from sqlalchemy import func, select, case
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

from core.database import get_db
from models.user import User
from models.job import Job, JobStatus # <<< ADDED JobStatus
from schemas.admin import SystemStatsResponse, RecentJobsResponse, RecentJobItem
from api.auth import get_current_active_superuser
from core.logging_config import get_logger
from core.log_context import set_log_context # <<< ADDED
# --- UPDATED IMPORT ---
from api.health_utils import health_check # Import health check function from new location
# --- END UPDATED IMPORT ---

logger = get_logger("vendor_classification.admin_api")

router = APIRouter()

@router.get("/stats", response_model=SystemStatsResponse)
async def get_admin_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser) # Ensures only superusers can access
):
    """
    Provides aggregated system statistics for the admin dashboard.
    Requires superuser privileges.
    """
    set_log_context({"admin_user": current_user.username}) # Set context for admin actions
    logger.info(f"Admin stats request by superuser: {current_user.username}")
    try:
        # User Counts
        total_users = db.query(func.count(User.id)).scalar()

        # Job Counts
        total_jobs = db.query(func.count(Job.id)).scalar()
        pending_jobs = db.query(func.count(Job.id)).filter(Job.status == JobStatus.PENDING.value).scalar()
        processing_jobs = db.query(func.count(Job.id)).filter(Job.status == JobStatus.PROCESSING.value).scalar()
        completed_jobs = db.query(func.count(Job.id)).filter(Job.status == JobStatus.COMPLETED.value).scalar()

        # Failed Jobs in the last 24 hours
        time_24h_ago = datetime.now(timezone.utc) - timedelta(hours=24)
        failed_jobs_last_24h = db.query(func.count(Job.id)).filter(
            Job.status == JobStatus.FAILED.value,
            Job.updated_at >= time_24h_ago # Use updated_at as completion/failure time indicator
        ).scalar()

        # Health Check Status (reuse existing logic from health_utils)
        health_status_data = await health_check()

        # TODO: Implement Estimated API Costs (requires cost tracking per job/API call)
        estimated_recent_cost = None # Placeholder

        stats = SystemStatsResponse(
            total_users=total_users or 0,
            total_jobs=total_jobs or 0,
            pending_jobs=pending_jobs or 0,
            processing_jobs=processing_jobs or 0,
            completed_jobs=completed_jobs or 0,
            failed_jobs_last_24h=failed_jobs_last_24h or 0,
            estimated_recent_cost=estimated_recent_cost,
            health_status=health_status_data # Include the full health check response
        )
        logger.debug("Admin stats calculated successfully.", extra={"stats": stats.model_dump(exclude={'health_status'})}) # Exclude verbose health status from log
        return stats

    except Exception as e:
        logger.error("Error fetching admin statistics", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not fetch system statistics."
        )

@router.get("/recent-jobs", response_model=RecentJobsResponse)
async def get_recent_jobs(
    limit: int = 15,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser) # Ensures only superusers can access
):
    """
    Provides a list of the most recent jobs across all users.
    Requires superuser privileges.
    """
    set_log_context({"admin_user": current_user.username}) # Set context
    logger.info(f"Recent jobs request by superuser: {current_user.username} (limit={limit})")
    try:
        recent_jobs_query = (
            select(
                Job.id,
                Job.created_by,
                Job.status,
                Job.created_at,
                Job.job_type,
                Job.company_name # Added company name for context
            )
            .order_by(Job.created_at.desc())
            .limit(limit)
        )
        results = db.execute(recent_jobs_query).all()

        # Map results to Pydantic model
        recent_jobs_list = [
            RecentJobItem(
                id=row.id,
                created_by=row.created_by,
                status=row.status,
                created_at=row.created_at,
                job_type=row.job_type,
                company_name=row.company_name
            ) for row in results
        ]

        logger.debug(f"Fetched {len(recent_jobs_list)} recent jobs.")
        return RecentJobsResponse(jobs=recent_jobs_list)

    except Exception as e:
        logger.error("Error fetching recent jobs", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not fetch recent jobs."
        )

# --- ADDED: Cancel Job Endpoint ---
@router.post("/jobs/{job_id}/cancel", status_code=status.HTTP_200_OK, response_model=Dict[str, str])
async def cancel_job(
    job_id: str = Path(..., title="The ID of the job to cancel"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser) # Ensures only superusers can access
):
    """
    Cancels a PENDING or PROCESSING job. Requires superuser privileges.
    Sets the job status to FAILED with an appropriate message.
    Does not attempt to kill the underlying Celery task (for now).
    """
    set_log_context({"admin_user": current_user.username, "target_job_id": job_id})
    logger.info(f"Admin '{current_user.username}' attempting to cancel job ID: {job_id}")

    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        logger.warning(f"Job cancellation failed: Job ID '{job_id}' not found.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    # Check if job is in a cancellable state
    if job.status not in [JobStatus.PENDING.value, JobStatus.PROCESSING.value]:
        logger.warning(f"Job cancellation failed: Job ID '{job_id}' has status '{job.status}', which cannot be cancelled.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job cannot be cancelled. Current status: {job.status}"
        )

    try:
        # Update job status and error message
        # Use the existing fail method for consistency
        error_msg = f"Cancelled by admin ({current_user.username})"
        job.fail(error_msg) # fail() method sets status, error_message, updated_at

        # Commit the changes
        db.add(job) # Stage the changes
        db.commit()
        logger.info(f"Job ID '{job_id}' successfully cancelled by admin '{current_user.username}'.")

        # TODO (Optional - Advanced): Implement Celery task cancellation logic here
        # Requires storing task_id on the Job model and using Celery's revoke/terminate
        # Example (pseudo-code):
        # if job.celery_task_id:
        #     try:
        #         from celery.result import AsyncResult
        #         task = AsyncResult(job.celery_task_id)
        #         task.revoke(terminate=True, signal='SIGKILL') # Force kill
        #         logger.info(f"Sent termination signal to Celery task {job.celery_task_id} for job {job_id}")
        #     except Exception as celery_err:
        #         logger.error(f"Failed to send termination signal to Celery task {job.celery_task_id} for job {job_id}", exc_info=True)

        return {"message": f"Job {job_id} cancelled successfully."}

    except Exception as e:
        db.rollback()
        logger.error(f"Error occurred while cancelling job ID '{job_id}'", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while cancelling the job."
        )
# --- END ADDED ---