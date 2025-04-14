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