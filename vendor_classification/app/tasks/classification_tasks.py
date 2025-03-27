# app/tasks/classification_tasks.py
import os
import time
import asyncio
import logging # <<< ADD logging import
from typing import List, Dict, Any, Optional
from datetime import datetime
from celery import shared_task
from sqlalchemy.orm import Session

from core.database import SessionLocal
from core.logging_config import (
    get_logger, LogTimer, set_correlation_id, set_job_id,
    log_function_call, set_log_context, log_duration
)
from models.job import Job, JobStatus, ProcessingStage
from models.taxonomy import Taxonomy
from services.file_service import read_vendor_file, normalize_vendor_names, generate_output_file
from services.llm_service import LLMService
from services.search_service import SearchService
from utils.taxonomy_loader import load_taxonomy

# Configure logger
logger = get_logger("vendor_classification.tasks")

@shared_task(bind=True)
def process_vendor_file(self, job_id: str, file_path: str):
    """
    Process vendor file for classification.

    Args:
        job_id: Job ID
        file_path: Path to vendor file
    """
    task_id = self.request.id if self.request and self.request.id else "UnknownTaskID"
    logger.info(f"***** process_vendor_file TASK STARTED *****",
               extra={
                   "celery_task_id": task_id,
                   "job_id_arg": job_id,
                   "file_path_arg": file_path
               })

    set_correlation_id(job_id)
    set_job_id(job_id)
    logger.info(f"Starting vendor file processing task (inside function)",
               extra={"job_id": job_id, "file_path": file_path})

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    db = SessionLocal()

    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            set_log_context({
                "company_name": job.company_name,
                "creator": job.created_by,
                "file_name": job.input_file_name
            })
            logger.info(f"Processing file for company",
                       extra={"company": job.company_name})
        else:
            logger.error("Job not found in database at start of task!", extra={"job_id": job_id})
            return

        # --- MODIFIED LogTimer level ---
        with LogTimer(logger, "Complete file processing", level=logging.INFO, include_in_stats=True): # Use logging.INFO constant
        # --- END MODIFICATION ---
            if not loop.is_running():
                 loop.run_until_complete(_process_vendor_file_async(job_id, file_path, db))
            else:
                 asyncio.ensure_future(_process_vendor_file_async(job_id, file_path, db))

        logger.info(f"Vendor file processing completed successfully (async part finished)")
    except Exception as e:
        logger.error(f"Error processing vendor file task", exc_info=True)
        try:
            job_in_error = db.query(Job).filter(Job.id == job_id).first()
            if job_in_error:
                job_in_error.fail(f"Task failed: {str(e)}")
                db.commit()
                logger.info(f"Job status updated to failed due to task error",
                           extra={"error": str(e)})
        except Exception as db_error:
            logger.error(f"Error updating job status during task failure handling", exc_info=True,
                        extra={"original_error": str(e), "db_error": str(db_error)})
            db.rollback()
    finally:
        if db:
            db.close()
            logger.debug(f"Database session closed for task.")
        if not asyncio.get_event_loop().is_running() and not loop.is_closed():
             loop.close()
             logger.debug(f"Event loop closed for task.")


async def _process_vendor_file_async(job_id: str, file_path: str, db: Session):
    """Asynchronous part of the vendor file processing."""
    logger.info(f"[_process_vendor_file_async] Starting async processing for job {job_id}")

    llm_service = LLMService()
    search_service = SearchService()

    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        logger.error(f"[_process_vendor_file_async] Job not found in database", extra={"job_id": job_id})
        return

    job.status = JobStatus.PROCESSING.value
    job.current_stage = ProcessingStage.INGESTION.value
    job.progress = 0.1
    db.commit()
    logger.info(f"Job status updated",
               extra={"status": job.status, "stage": job.current_stage, "progress": job.progress})

    start_time = datetime.now()
    stats = {
        "job_id": job_id,
        "company_name": job.company_name,
        "start_time": start_time.isoformat(),
        "api_usage": {
            "azure_openai_calls": 0,
            "azure_openai_tokens_input": 0,
            "azure_openai_tokens_output": 0,
            "azure_openai_tokens_total": 0,
            "tavily_search_calls": 0,
            "cost_estimate_usd": 0.0
        }
    }

    try:
        logger.info(f"Reading vendor file")
        with log_duration(logger, "Reading vendor file"):
            vendors = read_vendor_file(file_path)
        logger.info(f"Vendor file read successfully",
                   extra={"vendor_count": len(vendors)})

        job.current_stage = ProcessingStage.NORMALIZATION.value
        job.progress = 0.2
        db.commit()
        logger.info(f"Job status updated",
                   extra={"stage": job.current_stage, "progress": job.progress})

        logger.info(f"Normalizing vendor names")
        with log_duration(logger, "Normalizing vendor names"):
            normalized_vendors = normalize_vendor_names(vendors)
        logger.info(f"Vendor names normalized",
                   extra={"normalized_count": len(normalized_vendors)})

        logger.info(f"Removing duplicate vendors")
        unique_vendors = []
        seen = set()
        for vendor in normalized_vendors:
            if vendor not in seen:
                unique_vendors.append(vendor)
                seen.add(vendor)

        logger.info(f"Duplicates removed",
                   extra={"unique_count": len(unique_vendors)})

        stats["total_vendors"] = len(normalized_vendors)
        stats["unique_vendors"] = len(unique_vendors)

        logger.info(f"Loading taxonomy")
        with log_duration(logger, "Loading taxonomy"):
            taxonomy = load_taxonomy()
        logger.info(f"Taxonomy loaded",
                   extra={"taxonomy_version": taxonomy.version})

        results = {vendor: {} for vendor in unique_vendors}

        logger.info(f"Starting vendor classification")
        # --- MODIFIED LogTimer level ---
        with log_duration(logger, "Complete vendor classification", level=logging.INFO): # Use logging.INFO constant
        # --- END MODIFICATION ---
            await process_vendors(unique_vendors, taxonomy, results, stats, job, db, llm_service, search_service)
        logger.info(f"Vendor classification completed")

        job.current_stage = ProcessingStage.RESULT_GENERATION.value
        job.progress = 0.9
        db.commit()
        logger.info(f"Job status updated",
                   extra={"stage": job.current_stage, "progress": job.progress})

        logger.info(f"Generating output file")
        with log_duration(logger, "Generating output file"):
            output_file_name = generate_output_file(normalized_vendors, results, job_id)
        logger.info(f"Output file generated",
                   extra={"output_file": output_file_name})

        end_time = datetime.now()
        processing_duration = (end_time - datetime.fromisoformat(stats["start_time"])).total_seconds()
        stats["end_time"] = end_time.isoformat()
        stats["processing_duration_seconds"] = processing_duration

        token_cost_per_1k = 0.002
        estimated_cost = (stats["api_usage"]["azure_openai_tokens_total"] / 1000) * token_cost_per_1k
        stats["api_usage"]["cost_estimate_usd"] = estimated_cost

        job.complete(output_file_name, stats)
        db.commit()
        logger.info(f"Job completed successfully",
                   extra={
                       "processing_duration": processing_duration,
                       "output_file": output_file_name,
                       "api_calls": stats["api_usage"]["azure_openai_calls"],
                       "tokens_used": stats["api_usage"]["azure_openai_tokens_total"],
                       "estimated_cost": estimated_cost
                   })

    except Exception as async_err:
        logger.error(f"[_process_vendor_file_async] Error during async processing", exc_info=True,
                    extra={"error": str(async_err)})
        raise # Re-raise for outer handler
    finally:
        logger.info(f"[_process_vendor_file_async] Finished async processing for job {job_id}")


# --- Helper functions (process_vendors, process_batch, etc.) remain the same ---
# --- Ensure they have adequate logging as well ---

@log_function_call(logger)
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
    """
    job.current_stage = ProcessingStage.CLASSIFICATION_L1.value
    job.progress = 0.3
    db.commit()
    logger.info(f"Starting Level 1 classification",
               extra={"vendor_count": len(vendors)})

    level1_batches = create_batches(vendors, batch_size=10)
    level1_results = {}

    for i, batch in enumerate(level1_batches):
        logger.info(f"Processing Level 1 batch {i+1}/{len(level1_batches)}",
                   extra={"batch_size": len(batch)})
        batch_results = await process_batch(batch, 1, None, taxonomy, llm_service, stats)
        level1_results.update(batch_results)

    for vendor, classification in level1_results.items():
        results[vendor]["level1"] = classification

    job.progress = 0.4
    db.commit()
    logger.info(f"Level 1 classification completed")

    for level in range(2, 5):
        if level == 2:
            job.current_stage = ProcessingStage.CLASSIFICATION_L2.value
            job.progress = 0.5
        elif level == 3:
            job.current_stage = ProcessingStage.CLASSIFICATION_L3.value
            job.progress = 0.6
        else:
            job.current_stage = ProcessingStage.CLASSIFICATION_L4.value
            job.progress = 0.7
        db.commit()

        logger.info(f"Starting Level {level} classification")
        grouped_vendors = group_by_parent_category(results, level-1)
        logger.info(f"Grouped vendors by parent category",
                   extra={"level": level, "group_count": len(grouped_vendors)})

        for parent_category, group_vendors in grouped_vendors.items():
            logger.info(f"Processing Level {level} group",
                       extra={"parent_category": parent_category, "vendor_count": len(group_vendors)})
            level_batches = create_batches(group_vendors, batch_size=10)
            level_results = {}
            for i, batch in enumerate(level_batches):
                logger.info(f"Processing Level {level} batch {i+1}/{len(level_batches)} for parent {parent_category}",
                           extra={"batch_size": len(batch)})
                batch_results = await process_batch(batch, level, parent_category, taxonomy, llm_service, stats)
                level_results.update(batch_results)
            for vendor, classification in level_results.items():
                results[vendor][f"level{level}"] = classification
        logger.info(f"Level {level} classification completed")

    job.current_stage = ProcessingStage.SEARCH.value
    job.progress = 0.8
    db.commit()
    logger.info(f"Starting search for unknown vendors")
    unknown_vendors = identify_unknown_vendors(results)
    logger.info(f"Identified unknown vendors",
               extra={"unknown_count": len(unknown_vendors)})

    if unknown_vendors:
        unknown_results = {}
        for i, vendor in enumerate(unknown_vendors):
            logger.info(f"Searching for vendor information {i+1}/{len(unknown_vendors)}",
                       extra={"vendor": vendor})
            search_result = await search_vendor(vendor, taxonomy, llm_service, search_service, stats)
            unknown_results[vendor] = search_result
        for vendor, search_result in unknown_results.items():
            results[vendor]["search_results"] = search_result
        logger.info(f"Unknown vendor search completed",
                   extra={"searched_count": len(unknown_vendors)})

@log_function_call(logger)
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
    """
    results = {}
    logger.debug(f"Sending batch to LLM for classification",
               extra={"level": level, "batch_size": len(batch), "parent_category": parent_category})

    with LogTimer(logger, f"LLM classification - Level {level}", include_in_stats=True):
        response = await llm_service.classify_batch(batch, level, taxonomy, parent_category)

    stats["api_usage"]["azure_openai_calls"] += 1
    stats["api_usage"]["azure_openai_tokens_input"] += response["usage"]["prompt_tokens"]
    stats["api_usage"]["azure_openai_tokens_output"] += response["usage"]["completion_tokens"]
    stats["api_usage"]["azure_openai_tokens_total"] += response["usage"]["total_tokens"]

    logger.debug(f"LLM API usage",
               extra={
                   "level": level,
                   "prompt_tokens": response["usage"]["prompt_tokens"],
                   "completion_tokens": response["usage"]["completion_tokens"],
                   "total_tokens": response["usage"]["total_tokens"]
               })

    classifications = response["result"]["classifications"]
    logger.debug(f"Received classifications from LLM",
               extra={"classification_count": len(classifications)})

    for classification in classifications:
        vendor_name = classification["vendor_name"]
        classification_possible = not classification.get("classification_not_possible", False)
        results[vendor_name] = {
            "category_id": classification["category_id"],
            "category_name": classification["category_name"],
            "confidence": classification["confidence"],
            "classification_not_possible": classification.get("classification_not_possible", False),
            "classification_not_possible_reason": classification.get("classification_not_possible_reason", None)
        }
        logger.debug(f"Vendor classified",
                   extra={
                       "vendor": vendor_name,
                       "level": level,
                       "category_id": classification["category_id"] if classification_possible else "N/A",
                       "confidence": classification["confidence"] if classification_possible else 0,
                       "classification_possible": classification_possible
                   })
    return results

@log_function_call(logger)
async def search_vendor(
    vendor: str,
    taxonomy: Taxonomy,
    llm_service: LLMService,
    search_service: SearchService,
    stats: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Search for vendor information and attempt classification.
    """
    logger.info(f"Searching for vendor information", extra={"vendor": vendor})
    with LogTimer(logger, "Tavily search", include_in_stats=True):
        search_result = await search_service.search_vendor(vendor)

    stats["api_usage"]["tavily_search_calls"] += 1
    source_count = len(search_result.get("sources", []))
    logger.info(f"Search completed", extra={"vendor": vendor, "source_count": source_count})

    if search_result.get("sources"):
        logger.info(f"Classifying vendor based on search results", extra={"vendor": vendor})
        with LogTimer(logger, "LLM classification from search", include_in_stats=True):
            classification = await llm_service.process_search_results(vendor, search_result, taxonomy)

        stats["api_usage"]["azure_openai_calls"] += 1
        stats["api_usage"]["azure_openai_tokens_input"] += classification["usage"]["prompt_tokens"]
        stats["api_usage"]["azure_openai_tokens_output"] += classification["usage"]["completion_tokens"]
        stats["api_usage"]["azure_openai_tokens_total"] += classification["usage"]["total_tokens"]

        logger.debug(f"LLM API usage for search processing",
                   extra={
                       "vendor": vendor,
                       "prompt_tokens": classification["usage"]["prompt_tokens"],
                       "completion_tokens": classification["usage"]["completion_tokens"],
                       "total_tokens": classification["usage"]["total_tokens"]
                   })

        search_result["classification"] = classification["result"]
        classification_possible = not classification["result"].get("classification_not_possible", True)

        if classification_possible:
            stats["tavily_search_successful_classifications"] = stats.get("tavily_search_successful_classifications", 0) + 1
            logger.info(f"Successful classification from search",
                       extra={
                           "vendor": vendor,
                           "category_id": classification["result"].get("category_id", "unknown"),
                           "confidence": classification["result"].get("confidence", 0)
                       })
        else:
            logger.info(f"Classification from search not possible",
                       extra={
                           "vendor": vendor,
                           "reason": classification["result"].get("classification_not_possible_reason", "unknown")
                       })
    else:
        logger.warning(f"No search results found for vendor", extra={"vendor": vendor})
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
        if any(level_result.get("classification_not_possible", False) for level_key, level_result in vendor_results.items() if level_key.startswith("level")):
            unknown_vendors.append(vendor)
    return unknown_vendors