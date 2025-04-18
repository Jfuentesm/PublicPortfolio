# app/schemas/admin.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

from models.job import JobStatus, JobType # Import enums

# --- Response for /api/v1/admin/stats ---
class SystemStatsResponse(BaseModel):
    total_users: int = Field(..., description="Total number of registered users.")
    total_jobs: int = Field(..., description="Total number of jobs created.")
    pending_jobs: int = Field(..., description="Number of jobs currently in pending state.")
    processing_jobs: int = Field(..., description="Number of jobs currently in processing state.")
    completed_jobs: int = Field(..., description="Total number of completed jobs.")
    failed_jobs_last_24h: int = Field(..., description="Number of jobs that failed in the last 24 hours.")
    estimated_recent_cost: Optional[float] = Field(None, description="Estimated API costs for a recent period (e.g., last 24h). Placeholder.")
    health_status: Dict[str, Any] = Field(..., description="Summary of system health checks (mirrors /health endpoint).")

# --- Response Item for /api/v1/admin/recent-jobs ---
class RecentJobItem(BaseModel):
    id: str = Field(..., description="Job ID.")
    created_by: str = Field(..., description="Username of the user who created the job.")
    company_name: str = Field(..., description="Company name associated with the job.")
    status: JobStatus = Field(..., description="Current status of the job.")
    created_at: datetime = Field(..., description="Timestamp when the job was created.")
    job_type: JobType = Field(..., description="Type of the job (CLASSIFICATION or REVIEW).")

    class Config:
        from_attributes = True # Enable ORM mode
        use_enum_values = True # Use string values for enums

# --- Response for /api/v1/admin/recent-jobs ---
class RecentJobsResponse(BaseModel):
    jobs: List[RecentJobItem] = Field(..., description="List of recent jobs.")