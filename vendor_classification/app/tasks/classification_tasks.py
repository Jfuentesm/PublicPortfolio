import os
import time
import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from celery import shared_task
from sqlalchemy.orm import Session

from core.database import SessionLocal
from models.job import Job, JobStatus, ProcessingStage
from models.taxonomy import Taxonomy
from services.file_service import read_vendor_file, normalize_vendor_names, generate_output_file
from services.llm_service import LLMService
from services.search_service import SearchService
from utils.taxonomy_loader import load_taxonomy

@shared_task
def process_vendor_file(job_id: str, file_path: str):
    """
    Process vendor file for classification.
    
    Args:
        job_id: Job ID
        file_path: Path to vendor file
    """
    # Create a new event loop for this task
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Run the async processing function
        loop.run_until_complete(_process_vendor_file_async(job_id, file_path, db))
    except Exception as e:
        # Log error
        logging.error(f"Error processing job {job_id}: {e}")
        
        try:
            # Get job from database
            job = db.query(Job).filter(Job.id == job_id).first()
            
            if job:
                # Update job status
                job.fail(str(e))
                db.commit()
        except Exception as db_error:
            logging.error(f"Error updating job status: {db_error}")
    finally:
        # Close database session
        db.close()
        loop.close()

async def _process_vendor_file_async(job_id: str, file_path: str, db: Session):
    """
    Async implementation of vendor file processing.
    
    Args:
        job_id: Job ID
        file_path: Path to vendor file
        db: Database session
    """
    # Initialize services
    llm_service = LLMService()
    search_service = SearchService()
    
    # Get job from database
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        logging.error(f"Job with ID {job_id} not found")
        return
    
    # Update job status
    job.status = JobStatus.PROCESSING.value
    job.current_stage = ProcessingStage.INGESTION.value
    job.progress = 0.1
    db.commit()
    
    # Initialize processing stats
    start_time = datetime.now()
    stats = {
        "job_id": job_id,
        "company_name": job.company_name,
        "start_time": start_time,
        "api_usage": {
            "azure_openai_calls": 0,
            "azure_openai_tokens_input": 0,
            "azure_openai_tokens_output": 0,
            "azure_openai_tokens_total": 0,
            "tavily_search_calls": 0,
            "cost_estimate_usd": 0.0
        }
    }
    
    # Read vendor file
    vendors = read_vendor_file(file_path)
    
    # Update job progress
    job.current_stage = ProcessingStage.NORMALIZATION.value
    job.progress = 0.2
    db.commit()
    
    # Normalize vendor names
    normalized_vendors = normalize_vendor_names(vendors)
    
    # Remove duplicates while preserving order
    unique_vendors = []
    seen = set()
    for vendor in normalized_vendors:
        if vendor not in seen:
            unique_vendors.append(vendor)
            seen.add(vendor)
    
    # Update stats
    stats["total_vendors"] = len(normalized_vendors)
    stats["unique_vendors"] = len(unique_vendors)
    
    # Load taxonomy
    taxonomy = load_taxonomy()
    
    # Initialize results
    results = {vendor: {} for vendor in unique_vendors}
    
    # Process vendors
    await process_vendors(unique_vendors, taxonomy, results, stats, job, db, llm_service, search_service)
    
    # Update job progress
    job.current_stage = ProcessingStage.RESULT_GENERATION.value
    job.progress = 0.9
    db.commit()
    
    # Generate output file
    output_file_name = generate_output_file(normalized_vendors, results, job_id)
    
    # Update stats
    end_time = datetime.now()
    stats["end_time"] = end_time
    stats["processing_duration_seconds"] = (end_time - start_time).total_seconds()
    
    # Complete job
    job.complete(output_file_name, stats)
    db.commit()
    
    # Log completion
    logging.info(f"Job {job_id} completed successfully")

async def process_vendors(
    vendors: List[str],
    taxonomy: Taxonomy,
    results: Dict[str, Dict],
    stats: Dict[str, Any],
    job: Job,
    db: Session,
    llm_service: LLMService,
    search_service: SearchService
):
    """
    Process vendors through the classification workflow.
    
    Args:
        vendors: List of vendor names
        taxonomy: Taxonomy data
        results: Results dictionary
        stats: Statistics dictionary
        job: Job object
        db: Database session
        llm_service: LLM service
        search_service: Search service
    """
    # Level 1 classification for all vendors
    job.current_stage = ProcessingStage.CLASSIFICATION_L1.value
    job.progress = 0.3
    db.commit()
    
    level1_batches = create_batches(vendors, batch_size=10)
    level1_results = {}
    
    for batch in level1_batches:
        batch_results = await process_batch(batch, 1, None, taxonomy, llm_service, stats)
        level1_results.update(batch_results)
    
    # Update results with Level 1 classifications
    for vendor, classification in level1_results.items():
        results[vendor]["level1"] = classification
    
    # Update job progress
    job.progress = 0.4
    db.commit()
    
    # Process subsequent levels (2-4) based on Level 1 groupings
    for level in range(2, 5):
        # Update job stage
        if level == 2:
            job.current_stage = ProcessingStage.CLASSIFICATION_L2.value
            job.progress = 0.5
        elif level == 3:
            job.current_stage = ProcessingStage.CLASSIFICATION_L3.value
            job.progress = 0.6
        else:  # level == 4
            job.current_stage = ProcessingStage.CLASSIFICATION_L4.value
            job.progress = 0.7
        db.commit()
        
        # Group vendors by previous level classification
        grouped_vendors = group_by_parent_category(results, level-1)
        
        # Process each group separately
        for parent_category, group_vendors in grouped_vendors.items():
            level_batches = create_batches(group_vendors, batch_size=10)
            level_results = {}
            
            for batch in level_batches:
                batch_results = await process_batch(batch, level, parent_category, taxonomy, llm_service, stats)
                level_results.update(batch_results)
            
            # Update results with this level's classifications
            for vendor, classification in level_results.items():
                results[vendor][f"level{level}"] = classification
    
    # Handle unknown vendors that couldn't be classified
    job.current_stage = ProcessingStage.SEARCH.value
    job.progress = 0.8
    db.commit()
    
    unknown_vendors = identify_unknown_vendors(results)
    if unknown_vendors:
        unknown_results = {}
        for vendor in unknown_vendors:
            search_result = await search_vendor(vendor, taxonomy, llm_service, search_service, stats)
            unknown_results[vendor] = search_result
        
        # Update results with findings from Tavily searches
        for vendor, search_result in unknown_results.items():
            results[vendor]["search_results"] = search_result

async def process_batch(
    batch: List[str],
    level: int,
    parent_category: Optional[str],
    taxonomy: Taxonomy,
    llm_service: LLMService,
    stats: Dict[str, Any]
) -> Dict[str, Dict]:
    """
    Process a batch of vendors for a specific classification level.
    
    Args:
        batch: List of vendors
        level: Classification level
        parent_category: Parent category ID
        taxonomy: Taxonomy data
        llm_service: LLM service
        stats: Statistics dictionary
        
    Returns:
        Classification results
    """
    results = {}
    
    response = await llm_service.classify_batch(batch, level, taxonomy, parent_category)
    
    # Update API usage stats
    stats["api_usage"]["azure_openai_calls"] += 1
    stats["api_usage"]["azure_openai_tokens_input"] += response["usage"]["prompt_tokens"]
    stats["api_usage"]["azure_openai_tokens_output"] += response["usage"]["completion_tokens"]
    stats["api_usage"]["azure_openai_tokens_total"] += response["usage"]["total_tokens"]
    
    # Process results
    classifications = response["result"]["classifications"]
    for classification in classifications:
        vendor_name = classification["vendor_name"]
        results[vendor_name] = {
            "category_id": classification["category_id"],
            "category_name": classification["category_name"],
            "confidence": classification["confidence"],
            "classification_not_possible": classification.get("classification_not_possible", False),
            "classification_not_possible_reason": classification.get("classification_not_possible_reason", None)
        }
    
    return results

async def search_vendor(
    vendor: str,
    taxonomy: Taxonomy,
    llm_service: LLMService,
    search_service: SearchService,
    stats: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Search for vendor information and attempt classification.
    
    Args:
        vendor: Vendor name
        taxonomy: Taxonomy data
        llm_service: LLM service
        search_service: Search service
        stats: Statistics dictionary
        
    Returns:
        Search and classification results
    """
    # Search for vendor information
    search_result = await search_service.search_vendor(vendor)
    
    # Update API usage stats
    stats["api_usage"]["tavily_search_calls"] += 1
    
    # Process search results with LLM
    if search_result.get("sources"):
        classification = await llm_service.process_search_results(vendor, search_result, taxonomy)
        
        # Update API usage stats
        stats["api_usage"]["azure_openai_calls"] += 1
        stats["api_usage"]["azure_openai_tokens_input"] += classification["usage"]["prompt_tokens"]
        stats["api_usage"]["azure_openai_tokens_output"] += classification["usage"]["completion_tokens"]
        stats["api_usage"]["azure_openai_tokens_total"] += classification["usage"]["total_tokens"]
        
        # Add classification to search result
        search_result["classification"] = classification["result"]
        
        # Check if classification was successful
        if not classification["result"].get("classification_not_possible", True):
            stats["tavily_search_successful_classifications"] = stats.get("tavily_search_successful_classifications", 0) + 1
    
    return search_result

def create_batches(items: List[Any], batch_size: int) -> List[List[Any]]:
    """Create batches from a list of items."""
    return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]

def group_by_parent_category(results: Dict[str, Dict], level: int) -> Dict[str, List[str]]:
    """Group vendors by parent category."""
    grouped = {}
    
    for vendor, vendor_results in results.items():
        level_result = vendor_results.get(f"level{level}")
        
        if level_result and not level_result.get("classification_not_possible", False):
            category_id = level_result["category_id"]
            
            if category_id not in grouped:
                grouped[category_id] = []
            
            grouped[category_id].append(vendor)
    
    return grouped

def identify_unknown_vendors(results: Dict[str, Dict]) -> List[str]:
    """Identify vendors that couldn't be classified."""
    unknown_vendors = []
    
    for vendor, vendor_results in results.items():
        # Check if any level has classification_not_possible=True
        if any(
            level_result.get("classification_not_possible", False)
            for level_key, level_result in vendor_results.items()
            if level_key.startswith("level")
        ):
            unknown_vendors.append(vendor)
    
    return unknown_vendors