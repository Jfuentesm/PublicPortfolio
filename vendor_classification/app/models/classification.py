# <file path='app/models/classification.py'>
# --- file path='app/models/classification.py' ---
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class VendorClassification(BaseModel):
    """Vendor classification model."""
    vendor_name: str
    category_id: str
    category_name: str
    confidence: float = Field(ge=0.0, le=1.0)
    notes: Optional[str] = None
    classification_not_possible: bool = False
    classification_not_possible_reason: Optional[str] = None
    sources: Optional[List[Dict[str, str]]] = None
    classification_source: Optional[str] = None # e.g., 'Initial', 'Search'

class ClassificationBatchResponse(BaseModel):
    """Response model for classification batch (expected from LLM)."""
    # --- MODIFIED: Allow level up to 5 ---
    level: int = Field(ge=1, le=5)
    # --- END MODIFIED ---
    batch_id: str
    parent_category_id: Optional[str] = None
    classifications: List[VendorClassification] # LLM should return this structure

class ApiUsage(BaseModel):
    """API usage statistics."""
    # Field names match the keys used in the stats dictionary
    openrouter_calls: int = 0
    openrouter_prompt_tokens: int = 0
    openrouter_completion_tokens: int = 0
    openrouter_total_tokens: int = 0
    tavily_search_calls: int = 0
    cost_estimate_usd: float = 0.0

class ProcessingStats(BaseModel):
    """Processing statistics for a job (stored in Job.stats JSON)."""
    job_id: str
    company_name: str
    start_time: Any # Can be datetime or ISO string
    end_time: Optional[Any] = None
    processing_duration_seconds: Optional[float] = None
    total_vendors: int = 0
    unique_vendors: int = 0
    # --- UPDATED/ADDED Fields ---
    successfully_classified_l4: int = 0 # Keep L4 count for reference/comparison
    successfully_classified_l5: int = 0 # NEW: Total vendors reaching L5 (initial or post-search)
    classification_not_possible_initial: int = 0 # Vendors needing search initially
    invalid_category_errors: int = 0 # Count of times LLM returned invalid category ID
    search_attempts: int = 0 # How many vendors triggered the search path
    search_successful_classifications_l1: int = 0 # Vendors getting L1 via search
    search_successful_classifications_l5: int = 0 # NEW: Vendors getting L5 via search path
    # --- END UPDATED/ADDED ---
    api_usage: ApiUsage = Field(default_factory=ApiUsage)
