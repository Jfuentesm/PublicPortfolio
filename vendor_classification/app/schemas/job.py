# <file path='app/schemas/job.py'>
# app/schemas/job.py
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, Any, List # <<< ADDED List
from datetime import datetime
from enum import Enum as PyEnum

from models.job import JobStatus, ProcessingStage # Import enums from model

# --- UPDATED: Schema for a single detailed result item ---
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
    # NOTE: We don't include detailed_results here by default to keep this response smaller.
    # It will be fetched via a separate endpoint if needed.

    class Config:
        from_attributes = True # Enable ORM mode for automatic mapping from Job model
        use_enum_values = True # Ensure enum values (strings) are used in the response


# Schema for the new results endpoint (redundant as endpoint returns List[JobResultItem])
# class JobResultsResponse(BaseModel):
#     job_id: str
#     results: List[JobResultItem] = []