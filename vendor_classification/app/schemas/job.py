# <file path='app/schemas/job.py'>
# app/schemas/job.py
from pydantic import BaseModel, Field # <<< ADDED Field
from datetime import datetime
from typing import Optional, Dict, Any

from models.job import JobStatus, ProcessingStage # Import enums from model

class JobResponse(BaseModel):
    """Schema for returning job information."""
    id: str
    company_name: str
    status: JobStatus # Use the enum
    progress: float
    current_stage: ProcessingStage # Use the enum
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    output_file_name: Optional[str] = None
    input_file_name: str
    created_by: str
    error_message: Optional[str] = None
    # --- ADDED: Target Level ---
    target_level: int = Field(..., ge=1, le=5) # Include target level in response
    # --- END ADDED ---
    # stats: Optional[Dict[str, Any]] = None # Optionally include stats summary

    class Config:
        from_attributes = True # Pydantic v2 way to enable ORM mode
        # orm_mode = True # Pydantic v1 way