# docs/1_response_solution design.md
# NAICS Vendor Classification System Design Document

## 1. Executive Summary

#### Problem Statement
Organizations struggle to efficiently classify their vendors according to industry standards like NAICS (North American Industry Classification System). Manual classification is time-consuming, inconsistent, and prone to errors, making it difficult to maintain accurate vendor databases for analytics, reporting, and compliance purposes.

#### Proposed Solution Overview
Naicsvendorclassification.com is a specialized web application that automates the vendor classification process using advanced AI. The system ingests vendor lists from spreadsheets, normalizes the data, and leverages large language models to accurately categorize vendors according to a four-level hierarchical taxonomy. For vendors that cannot be immediately classified, the system conducts automated web searches to gather additional information before making a determination.

#### Key Benefits and Success Metrics
**Benefits:**
- Reduces vendor classification time from days/weeks to hours
- Provides consistent, standardized categorization
- Enhances data quality for procurement analytics and reporting
- Minimizes manual effort through intelligent automation
- Securely processes vendor information

**Success Metrics:**
- Classification accuracy (>95% target)
- Processing throughput (1,000+ vendors per hour)
- Reduction in manual classification effort (>80%)
- System reliability and uptime (99.9%)
- User satisfaction ratings (>4.5/5)

## 2. System Architecture

#### High-level Architecture Diagram

```
┌────────────────┐     ┌────────────────────┐     ┌──────────────────────┐
│                │     │                    │     │                      │
│  Web Interface │────▶│  Application Core  │────▶│  Processing Engine   │
│                │     │                    │     │                      │
└────────────────┘     └────────────────────┘     └──────────────────────┘
                              │      ▲                   │        ▲
                              │      │                   │        │
                              ▼      │                   ▼        │
┌────────────────┐     ┌────────────────────┐     ┌──────────────────────┐
│                │     │                    │     │                      │
│  File Storage  │◀───▶│  Security Layer    │     │  External APIs       │
│                │     │                    │     │  - OpenRouter        │
└────────────────┘     └────────────────────┘     │  - Tavily Search     │
                                                  └──────────────────────┘
```

#### Key Components and Their Interactions

1. **Web Interface**
   - Simple, intuitive UI for file upload and download
   - Progress monitoring dashboard
   - Authentication system
   - Email notification integration

2. **Application Core**
   - Job management and orchestration
   - File handling and validation
   - User session management
   - Email notification service

3. **Processing Engine**
   - Data ingestion and normalization
   - Vendor batching logic
   - Classification workflow orchestration
   - LLM prompt engineering and response handling
   - Result generation and validation

4. **File Storage**
   - Secure storage for input files
   - Temporary processing data
   - Output files and logs
   - Usage statistics

5. **Security Layer**
   - Authentication and authorization
   - Data sanitization
   - PII/sensitive data filtering
   - Encryption management

6. **External APIs**
   - OpenRouter for vendor classification
   - Tavily Search API for unknown vendor research

#### Technology Stack Recommendations

**Backend:**
- Python 3.11+ for core processing
- FastAPI for RESTful API endpoints
- Pydantic for data validation and modeling
- Celery for asynchronous task processing
- Redis for job queue and caching
- Docker and Docker Compose for containerization

**Frontend:**
- HTML, CSS, JavaScript (Vanilla JS used in current implementation)
- Bootstrap for responsive styling

**Cloud Infrastructure (Example - AWS):**
- EC2 for application hosting
- S3 for file storage
- SES for email delivery
- CloudWatch for monitoring
- IAM for access control

**External Services:**
- OpenRouter for language model processing
- Tavily API for web searches

#### Data Flow Diagram

**Main Processing Flow:**
```
┌───────────┐    ┌───────────────┐    ┌──────────────┐    ┌────────────┐    ┌────────────┐
│           │    │               │    │              │    │            │    │            │
│  Upload   │───▶│  Validation & │───▶│  Normalize & │───▶│  Process   │───▶│  Generate  │
│  Excel    │    │  Sanitization │    │  Deduplicate │    │  Batches   │    │  Output    │
│           │    │               │    │              │    │            │    │            │
└───────────┘    └───────────────┘    └──────────────┘    └────────────┘    └────────────┘
                                                               │
                                                               ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                          │
│                               Classification Processing                                  │
│                                                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐           │
│  │              │    │              │    │              │    │              │           │
│  │   Level 1    │───▶│   Level 2    │───▶│   Level 3    │───▶│   Level 4    │           │
│  │ Classification│    │ Classification│    │ Classification│    │ Classification│           │
│  │              │    │              │    │              │    │              │           │
│  └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘           │
│           │                 │                  │                   │                     │
│           ▼                 ▼                  ▼                   ▼                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐           │
│  │  Validate &  │    │  Validate &  │    │  Validate &  │    │  Validate &  │           │
│  │   Process    │    │   Process    │    │   Process    │    │   Process    │           │
│  │  Responses   │    │  Responses   │    │  Responses   │    │  Responses   │           │
│  └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘           │
│                                                                                          │
└──────────────────────────────────────────────────────────────────────────────────────────┘
                                               │
                                               ▼
                                       ┌─────────────────┐
                                       │                 │
                                       │  Handle Unknown │
                                       │  Vendors with   │
                                       │  Tavily Search  │
                                       │                 │
                                       └─────────────────┘
```

## 3. Detailed Technical Specifications

#### Component Specifications

**1. File Ingestion and Preprocessing Component**

This component handles the initial file upload, validation, and data extraction:

- **Functionality:**
  - Accept Excel files (.xlsx, .xls) containing vendor data
  - Validate file format and required columns (primarily `vendor_name`)
  - Extract vendor names and specified optional context fields (e.g., `vendor_address`, `vendor_website`, `internal_category`, `parent_company`, `spend_category`, `optional_example_good_serviced_purchased`)
  - Normalize vendor names (standardize case, remove duplicates, etc.)
  - Store sanitized data for further processing

- **Input Handling:**
  ```python
  def process_input_file(file_path: str) -> Dict[str, Any]:
      """Process the input Excel file and extract sanitized vendor data."""
      try:
          # Read Excel file
          df = pd.read_excel(file_path)

          # Check required columns
          if 'vendor_name' not in df.columns: # Case-insensitive check done in implementation
              raise ValueError("Required column 'vendor_name' not found")

          # Extract vendor name and optional context fields
          vendors_data = []
          # ... logic to extract based on file_service.py ...

          # Normalize vendor names (title case, remove duplicates)
          normalized_vendors_data = normalize_vendor_data(vendors_data) # Preserves other fields
          unique_vendors_map = {entry['vendor_name']: entry for entry in normalized_vendors_data}
          unique_vendors_list = list(unique_vendors_map.values())

          return {
              "total_records": len(df),
              "unique_vendors": len(unique_vendors_list),
              "vendors_data": unique_vendors_list # List of dicts with unique names and context
          }
      except Exception as e:
          logging.error(f"Error processing input file: {e}")
          raise
  ```

**2. Vendor Classification Component**

This component manages the hierarchical classification process:

- **Functionality:**
  - Create batches of vendors (including context data) for processing
  - Generate appropriate prompts for the LLM using vendor name and optional context
  - Send batches to OpenRouter API
  - Validate responses using Pydantic models and clean/parse JSON
  - Handle the 4-level hierarchical classification process
  - Manage unknown vendor resolution via Tavily Search

- **Classification Workflow:**
  ```python
  async def classify_vendors(vendors_data: List[Dict[str, Any]], taxonomy: Taxonomy) -> Dict[str, Any]:
      """Execute the full vendor classification workflow."""
      # Initialize results storage based on unique vendors
      unique_vendors_map = {vd['vendor_name']: vd for vd in vendors_data}
      results = {vendor_name: {} for vendor_name in unique_vendors_map.keys()}
      stats = {"api_calls": 0, "tokens": 0, "tavily_searches": 0} # Simplified stats example

      # Level 1 classification for all unique vendors
      # Batches contain full vendor dicts
      level1_batches_data = create_batches(list(unique_vendors_map.values()), batch_size=settings.BATCH_SIZE)
      level1_results = await process_level(level1_batches_data, 1, None, taxonomy, llm_service, stats) # Pass services/stats

      # Update results with Level 1 classifications
      for vendor_name, classification in level1_results.items():
          results[vendor_name]["level1"] = classification

      # Process subsequent levels (2-4) based on previous level groupings
      vendors_to_process_next_names = list(unique_vendors_map.keys())
      for level in range(2, 5):
          # Group vendor *names* by previous level classification
          grouped_vendors_names = group_by_parent_category(results, level-1, vendors_to_process_next_names)
          vendors_classified_in_level_names = []

          # Process each group separately
          for parent_category_id, group_vendor_names in grouped_vendors_names.items():
              if not group_vendor_names: continue
              # Get full data for vendors in this group
              group_vendor_data = [unique_vendors_map[name] for name in group_vendor_names if name in unique_vendors_map]
              level_batches_data = create_batches(group_vendor_data, batch_size=settings.BATCH_SIZE)
              level_results = await process_level(
                  level_batches_data, level, parent_category_id, taxonomy, llm_service, stats # Pass services/stats
              )

              # Update results with this level's classifications
              for vendor_name, classification in level_results.items():
                  results[vendor_name][f"level{level}"] = classification
                  if not classification.get("classification_not_possible", False):
                      vendors_classified_in_level_names.append(vendor_name)

          vendors_to_process_next_names = vendors_classified_in_level_names # Update list for next iteration

      # Handle unknown vendors that couldn't be classified
      unknown_vendors_data_to_search = identify_unknown_vendors(results, unique_vendors_map)
      if unknown_vendors_data_to_search:
          unknown_results = await process_unknown_vendors(unknown_vendors_data_to_search, taxonomy, llm_service, search_service, stats) # Pass services/stats
          # Update results with findings from Tavily searches
          for vendor_name, search_result in unknown_results.items():
              results[vendor_name]["search_results"] = search_result

      return {"classifications": results, "stats": stats}
  ```

**3. LLM Integration Component**

This component handles all interactions with OpenRouter:

- **Functionality:**
  - Format appropriate prompts based on taxonomy level and vendor data (name + optional context)
  - Send requests to OpenRouter API
  - Parse and validate JSON responses, handling potential LLM formatting issues (e.g., markdown fences, extra text)
  - Handle errors and retries
  - Track token usage and performance

- **Sample Prompt Generation (Level 1 - Updated):**
  ```python
  def create_classification_prompt(
      vendors_data: List[Dict[str, Any]], # List of vendor dicts
      level: int,
      parent_category: Optional[str] = None,
      taxonomy: Taxonomy,
      batch_id: str = "unique-id"
  ) -> str:
      """Create an appropriate prompt for the current classification level."""
      vendor_list_str = ""
      for i, vendor_entry in enumerate(vendors_data):
          vendor_name = vendor_entry.get('vendor_name', f'UnknownVendor_{i}')
          # Add optional fields (address, website, example, internal_cat, parent_co, spend_cat) if present
          # ... logic from llm_service.py ...
          vendor_list_str += f"\n{i+1}. Vendor Name: {vendor_name}"
          # ... add context lines ...

      if level == 1:
          categories = get_level1_categories(taxonomy)
          categories_str = "\n".join(f"- {cat.id}: {cat.name}" for cat in categories)

          prompt = f"""
          You are a vendor classification expert. Below is a list of vendors with optional context.
          Please classify each vendor according to the following Level 1 categories:

          {categories_str}

          For each vendor, provide:
          1. The most appropriate category ID and name
          2. A confidence level (0.0-1.0)
          Use the provided context (Examples, Address, Website, etc.) if available.

          If you cannot determine a category with reasonable confidence, mark it as "classification_not_possible".

          Vendor list:
          {vendor_list_str}

          **Output Format:** Respond *only* with a valid JSON object matching this exact schema. Do not include any text before or after the JSON object.
          ```json
          {{
            "level": 1,
            "batch_id": "{batch_id}",
            "parent_category_id": null,
            "classifications": [
              {{
                "vendor_name": "Vendor Name",
                "category_id": "ID or N/A",
                "category_name": "Category Name or N/A",
                "confidence": 0.95,
                "classification_not_possible": false,
                "classification_not_possible_reason": null
              }}
              // ... more classifications
            ]
          }}
          ```
          Ensure every vendor from the list is included in the `classifications` array with the exact vendor name provided. Ensure the `batch_id` in the response matches "{batch_id}".
          """
      else:
          # Similar logic for levels 2-4, including the explicit JSON output instruction
          # ...

      return prompt
  ```

**4. Tavily Search Integration Component**

This component handles research for unknown vendors:

- **Functionality:**
  - Format appropriate search queries for unknown vendors
  - Send requests to Tavily API
  - Process search results
  - Feed relevant information back to LLM for classification attempts
  - Track search usage and effectiveness

- **Tavily Integration:**
  ```python
  async def search_vendor_information(vendor_name: str) -> Dict[str, Any]:
      """Search for information about an unknown vendor using Tavily API."""
      search_query = f"{vendor_name} company business type industry"

      try:
          # Use httpx directly as in search_service.py
          payload = {
              "api_key": settings.TAVILY_API_KEY,
              "query": search_query,
              # ... other parameters ...
          }
          async with httpx.AsyncClient() as client:
              response = await client.post(f"{settings.TAVILY_API_BASE}/search", json=payload, timeout=30.0) # Assuming TAVILY_API_BASE is set
              response.raise_for_status()
              search_results = response.json()

          # Extract relevant information from search results
          processed_results = {
              "vendor": vendor_name,
              "search_query": search_query,
              "sources": [
                  {
                      "title": result.get("title", ""),
                      "url": result.get("url", ""),
                      "content": result.get("content", "")[:1500] # Increased limit for LLM
                  }
                  for result in search_results.get("results", []) if result.get("url")
              ],
              "summary": search_results.get("answer", ""),
              "error": None
          }

          return processed_results

      except Exception as e:
          logging.error(f"Tavily API error for vendor '{vendor_name}': {e}")
          return {
              "vendor": vendor_name,
              "error": str(e),
              "search_query": search_query,
              "sources": []
          }
  ```

**5. Result Generation Component**

This component compiles and formats the final output:

- **Functionality:**
  - Aggregate classification results from all levels
  - Format data according to output specifications, including original optional fields provided in input
  - Generate the output Excel file
  - Create logs and usage statistics

- **Result Compilation:**
  ```python
  def generate_output_file(
      original_vendor_data: List[Dict[str, Any]], # Original list of dicts from input
      classification_results: Dict[str, Dict], # Results keyed by unique, normalized name
      output_path: str
  ) -> None:
      """Generate the final output Excel file with classification results."""
      # Prepare data for Excel
      output_data = []

      for original_entry in original_vendor_data:
          vendor_name = original_entry.get('vendor_name') # Use the normalized name
          result = classification_results.get(vendor_name, {})

          # Combine original context with classification results
          row = {
              "vendor_name": vendor_name,
              # Include original optional fields (address, website, example, etc.) from original_entry
              "vendor_address": original_entry.get("vendor_address", ""),
              "vendor_website": original_entry.get("vendor_website", ""),
              "internal_category": original_entry.get("internal_category", ""),
              "parent_company": original_entry.get("parent_company", ""),
              "spend_category": original_entry.get("spend_category", ""),
              "Optional_example_good_serviced_purchased": original_entry.get("example", ""),
              # Classification results
              "level1_category_id": result.get("level1", {}).get("category_id", ""),
              "level1_category_name": result.get("level1", {}).get("category_name", ""),
              "level2_category_id": result.get("level2", {}).get("category_id", ""),
              "level2_category_name": result.get("level2", {}).get("category_name", ""),
              "level3_category_id": result.get("level3", {}).get("category_id", ""),
              "level3_category_name": result.get("level3", {}).get("category_name", ""),
              "level4_category_id": result.get("level4", {}).get("category_id", ""),
              "level4_category_name": result.get("level4", {}).get("category_name", ""),
              # Determine final confidence/status based on logic in file_service.py
              # ... final confidence, classification_not_possible, notes/reason ...
              "sources": ", ".join(
                  source.get("url", "") for source in result.get("search_results", {}).get("sources", []) if isinstance(source, dict) and source.get("url")
              ) if isinstance(result.get("search_results", {}).get("sources"), list) else ""
          }
          output_data.append(row)

      # Create DataFrame and write to Excel using explicit column order
      output_columns = [
          "vendor_name", "vendor_address", "vendor_website", "internal_category",
          "parent_company", "spend_category", "Optional_example_good_serviced_purchased",
          "level1_category_id", "level1_category_name", "level2_category_id", "level2_category_name",
          "level3_category_id", "level3_category_name", "level4_category_id", "level4_category_name",
          "final_confidence", "classification_not_possible", "classification_notes_or_reason", "sources"
      ]
      df = pd.DataFrame(output_data, columns=output_columns)
      df.to_excel(output_path, index=False)
  ```

#### API Definitions and Interfaces

**1. REST API Endpoints**

```
POST /api/v1/upload
- Purpose: Upload vendor Excel file for processing
- Request: multipart/form-data with file and company_name
- Response: {job_id: str, status: str, message: str, created_at: datetime, progress: float, current_stage: str}

GET /api/v1/jobs/{job_id}
- Purpose: Check job status
- Response: {
    job_id: str,
    status: str,
    progress: float,
    current_stage: str,
    created_at: datetime,
    updated_at: datetime,
    estimated_completion: Optional[datetime],
    error_message: Optional[str]
  }

GET /api/v1/jobs/{job_id}/download
- Purpose: Download job results
- Response: Excel file stream

POST /api/v1/jobs/{job_id}/notify
- Purpose: Request email notification when job completes
- Request: {email: str}
- Response: {success: bool, message: str}

GET /api/v1/jobs/{job_id}/stats
- Purpose: Get job processing statistics
- Response: {
    vendors_processed: int,
    unique_vendors: int,
    api_calls: int,
    tokens_used: int,
    tavily_searches: int,
    processing_time: float
  }

POST /token
- Purpose: Authenticate user and get JWT token
- Request: OAuth2PasswordRequestForm (username, password)
- Response: {access_token: str, token_type: str, username: str}

GET /health
- Purpose: Health check endpoint
- Response: {status: str, ...}
```

**2. Internal Component Interfaces**

```python
# TaskQueue Interface (Simplified via Celery)
# LLM Service Interface
class LLMService:
    async def classify_batch(
        self,
        batch_data: List[Dict[str, Any]], # List of vendor dicts
        level: int,
        taxonomy: Taxonomy,
        parent_category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send a batch of vendors (with context) to LLM for classification."""
        pass

    async def process_search_results(
        self,
        vendor_data: Dict[str, Any], # Vendor dict with context
        search_results: Dict[str, Any],
        taxonomy: Taxonomy
    ) -> Dict[str, Any]:
        """Process search results to determine classification."""
        pass

# Search Service Interface
class SearchService:
    async def search_vendor(self, vendor_name: str) -> Dict[str, Any]:
        """Search for information about a vendor."""
        pass
```

#### Data Models and Schema

**1. Taxonomy Model**

```python
from pydantic import BaseModel, Field
from typing import Dict, List, Optional

class TaxonomyCategory(BaseModel):
    id: str
    name: str
    description: Optional[str] = None

class TaxonomyLevel4(TaxonomyCategory):
    pass

class TaxonomyLevel3(TaxonomyCategory):
    children: Dict[str, TaxonomyLevel4]

class TaxonomyLevel2(TaxonomyCategory):
    children: Dict[str, TaxonomyLevel3]

class TaxonomyLevel1(TaxonomyCategory):
    children: Dict[str, TaxonomyLevel2]

class Taxonomy(BaseModel):
    name: str
    version: str
    description: Optional[str] = None
    categories: Dict[str, TaxonomyLevel1]
```

**2. Classification Models**

```python
class VendorClassification(BaseModel):
    vendor_name: str
    category_id: str
    category_name: str
    confidence: float = Field(ge=0.0, le=1.0)
    notes: Optional[str] = None
    classification_not_possible: bool = False
    classification_not_possible_reason: Optional[str] = None
    sources: Optional[List[Dict[str, str]]] = None

class ClassificationBatchResponse(BaseModel):
    level: int = Field(ge=1, le=4)
    batch_id: str
    parent_category_id: Optional[str] = None
    classifications: List[VendorClassification]
```

**3. Job Models**

```python
from enum import Enum
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Enum as SQLEnum, JSON, Text
from sqlalchemy.sql import func
from core.database import Base # Assuming Base is defined in database.py

class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ProcessingStage(str, Enum):
    INGESTION = "ingestion"
    NORMALIZATION = "normalization"
    CLASSIFICATION_L1 = "classification_level_1"
    CLASSIFICATION_L2 = "classification_level_2"
    CLASSIFICATION_L3 = "classification_level_3"
    CLASSIFICATION_L4 = "classification_level_4"
    SEARCH = "search_unknown_vendors"
    RESULT_GENERATION = "result_generation"

class Job(Base): # SQLAlchemy model
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, index=True)
    company_name = Column(String, nullable=False)
    input_file_name = Column(String, nullable=False)
    output_file_name = Column(String, nullable=True)
    status = Column(String, default=JobStatus.PENDING.value)
    current_stage = Column(String, default=ProcessingStage.INGESTION.value)
    progress = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    notification_email = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    stats = Column(JSON, default={})
    created_by = Column(String, nullable=False) # Store username of creator

    # Methods to update status/progress/completion/failure
```

**4. Usage Statistics Model**

```python
from typing import Any # For start/end time flexibility

class ApiUsage(BaseModel):
    openrouter_calls: int = 0 # Renamed from azure_openai_calls
    openrouter_prompt_tokens: int = 0 # Renamed
    openrouter_completion_tokens: int = 0 # Renamed
    openrouter_total_tokens: int = 0 # Renamed
    tavily_search_calls: int = 0
    cost_estimate_usd: float = 0.0

class ProcessingStats(BaseModel): # Used within the Job model's JSON field
    job_id: str
    company_name: str
    start_time: Any # Can be datetime or ISO string
    end_time: Optional[Any] = None
    processing_duration_seconds: Optional[float] = None
    total_vendors: int = 0
    unique_vendors: int = 0
    successfully_classified: int = 0 # This may need refinement (e.g., initially vs after search)
    classification_not_possible: int = 0 # See above
    tavily_searches: int = 0
    tavily_search_successful_classifications: int = 0
    api_usage: ApiUsage = Field(default_factory=ApiUsage)
```

#### Security Considerations

**1. Data Protection**

- **Input Data Sanitization:**
  - Automated scanning for PII (SSNs, credit cards, etc.) - *Future Enhancement*
  - Field validation to ensure only necessary data is retained (e.g., vendor name, optional context)
  - Input scrubbing to remove potential injection attacks

- **Storage Security:**
  - All data stored with AES-256 encryption at rest (S3 default or equivalent)
  - Storage bucket policies restricting access
  - Temporary file management with secure deletion

- **Access Controls:**
  - Strict IAM roles and permissions (if using cloud provider)
  - Least privilege access principles
  - Regular access audits

**2. API Security**

- **Authentication:**
  - JWT-based authentication for all API endpoints
  - Token expiration and rotation
  - Rate limiting to prevent abuse

- **External API Protection:**
  - Secure storage of API keys (currently hardcoded, move to environment variables or secrets manager)
  - Regular rotation of API credentials
  - API access monitoring and alerting

**3. Compliance and Privacy**

- **Data Retention:**
  - Automated purging of data after processing (configurable retention period) - *Future Enhancement*
  - Clear data handling policies
  - Audit logs for all data access and operations

- **Transmission Security:**
  - TLS 1.3 for all data in transit
  - Secure headers configuration
  - CORS policy implementation

#### Performance Requirements

**1. Scalability**
- Support for processing files with up to 10,000 vendor entries
- Ability to handle multiple concurrent jobs via Celery workers
- Dynamic batch sizing based on system load (currently fixed)

**2. Processing Speed**
- Average processing time target: <5 seconds per vendor
- Complete job turnaround target: < 1 hour for files with up to 1,000 vendors

**3. API Usage Efficiency**
- Optimal batch sizing to minimize API calls (currently fixed at 5)
- Caching of common vendors to reduce duplicate searches - *Future Enhancement*
- Intelligent retry mechanisms for failed API calls (using Tenacity)

**4. Resource Requirements**
- Minimum EC2 instance (or equivalent): t3.medium for web service and worker (separate or combined depends on load)
- Recommended: t3.large for production workloads
- Memory: Minimum 4GB RAM per service
- Storage: 20GB base + ~1MB per job (input/output/logs)

## 4. Implementation Plan

#### Development Phases

**Phase 1: Core Infrastructure (2 weeks)** - Done
**Phase 2: Data Processing Pipeline (3 weeks)** - Done
**Phase 3: LLM Integration (2 weeks)** - Done (using OpenRouter)
**Phase 4: Unknown Vendor Resolution (2 weeks)** - Done (using Tavily)
**Phase 5: Web Interface and Job Management (2 weeks)** - Done (basic UI/Job tracking)
**Phase 6: Testing and Optimization (2 weeks)** - Ongoing
**Phase 7: Deployment and Monitoring (1 week)** - Done (basic Docker deployment)

#### Dependencies and Prerequisites

**1. Technical Dependencies** - Met
**2. Data Dependencies** - Met (using provided NAICS JSON)
**3. Knowledge Requirements** - Met by current team
**4. External Services Setup** - Met (OpenRouter/Tavily keys hardcoded for now)

## 5. Risks and Mitigation Strategies

#### Technical Risks

| Risk | Impact | Likelihood | Mitigation Strategy |
|------|--------|------------|---------------------|
| LLM response inconsistency/invalid category/format | High | Medium | Implement structured prompts with explicit JSON-only instruction, JSON response format request, robust JSON parsing (handling fences/extra text), post-validation against taxonomy, error handling for invalid JSON/structure, review workflows for low-confidence classifications. |
| API rate limiting or downtime | High | Medium | Use Tenacity for robust retries with exponential backoff, implement API call monitoring, consider fallback mechanisms if critical. |
| Performance bottlenecks with large files | Medium | Medium | Use Celery for asynchronous processing, optimize Pandas operations, monitor resource usage, consider database indexing. |
| Data format inconsistencies in input | Medium | High | Implement robust input validation (e.g., checking for `vendor_name`), flexible parsing (case-insensitive columns), clear error messages to user. |

#### Security Risks

| Risk | Impact | Likelihood | Mitigation Strategy |
|------|--------|------------|---------------------|
| Sensitive data exposure in input/output | Critical | Medium | Remove unnecessary columns during ingestion (`file_service.py`), implement data sanitization checks (*Future*), strict access controls, encryption at rest/transit. |
| API credential compromise | High | Low | Move API keys from config to environment variables/secrets manager, implement credential rotation, add access logging. |
| Unauthorized system access | High | Low | Implement strong authentication (JWT), role-based access (*Future*), security monitoring, regular dependency scanning. |
| Data retention compliance issues | Medium | Medium | Create clear data retention policies with automated enforcement (*Future*), ensure secure deletion of job files. |

#### Operational Risks

| Risk | Impact | Likelihood | Mitigation Strategy |
|------|--------|------------|---------------------|
| Cost overruns from API usage | Medium | Medium | Implement detailed usage tracking per job (stats), monitor API costs, optimize batch sizes/prompts, set budget alerts. |
| Classification accuracy below expectations | High | Medium | Develop feedback mechanisms (*Future*), continuous prompt improvement based on errors/low confidence results, allow manual override (*Future*). |
| User adoption challenges | Medium | Medium | Create intuitive UI, provide clear instructions, add error handling feedback, offer user support channel. |
| Dependency on external APIs | High | Medium | Add caching mechanisms (*Future*), monitor API status, have contingency plans if APIs become unavailable. |

#### Mitigation Approaches

**For LLM Classification Accuracy:**
- Validate LLM category IDs against the loaded taxonomy at each level.
- Set confidence thresholds for flagging uncertain results.
- Log failed/low-confidence classifications for prompt tuning.
- *Future:* Implement user feedback loop or manual review queue.

**For API Dependency Issues:**
- Use Tenacity for retries on network/server errors.
- Implement health checks for external services (*Future*).
- Log detailed API request/response metrics for troubleshooting.

**For Security and Compliance:**
- Regularly update dependencies (e.g., `pip-audit`).
- Move secrets out of code into environment variables or a secrets manager.
- Implement data lifecycle management (*Future*).

**For Cost Management:**
- Track token usage per job in the `Job.stats` field.
- Analyze usage patterns to potentially optimize prompts or batching.
- Set up billing alerts for cloud provider and API services.
