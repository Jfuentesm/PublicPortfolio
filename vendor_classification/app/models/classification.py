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

class ClassificationBatchResponse(BaseModel):
    """Response model for classification batch."""
    level: int = Field(ge=1, le=4)
    batch_id: str
    parent_category_id: Optional[str] = None
    classifications: List[VendorClassification]

class ApiUsage(BaseModel):
    """API usage statistics."""
    azure_openai_calls: int = 0
    azure_openai_tokens_input: int = 0
    azure_openai_tokens_output: int = 0
    azure_openai_tokens_total: int = 0
    tavily_search_calls: int = 0
    cost_estimate_usd: float = 0.0

class ProcessingStats(BaseModel):
    """Processing statistics for a job."""
    job_id: str
    company_name: str
    start_time: Any
    end_time: Optional[Any] = None
    processing_duration_seconds: Optional[float] = None
    total_vendors: int = 0
    unique_vendors: int = 0
    successfully_classified: int = 0
    classification_not_possible: int = 0
    tavily_searches: int = 0
    tavily_search_successful_classifications: int = 0
    api_usage: ApiUsage = Field(default_factory=ApiUsage)
