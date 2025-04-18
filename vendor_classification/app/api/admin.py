# app/api/admin.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, select, case
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

from core.database import get_db
from models.user import User
from models.job import Job, JobStatus
from schemas.admin import SystemStatsResponse, RecentJobsResponse, RecentJobItem
from api.auth import get_current_active_superuser
from core.logging_config import get_logger
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
