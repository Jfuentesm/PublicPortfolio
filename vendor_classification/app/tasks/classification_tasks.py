# app/tasks/classification_tasks.py
import os
import time
import asyncio
import logging # <<< Ensure logging is imported
from typing import List, Dict, Any, Optional
from datetime import datetime
from celery import shared_task
from sqlalchemy.orm import Session

from core.database import SessionLocal
from core.config import settings
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

    # Initialize loop within the task context
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
            loop.close() # Close loop if job not found
            return

        with LogTimer(logger, "Complete file processing", level=logging.INFO, include_in_stats=True):
             # Run the async function within the loop created for this task
            loop.run_until_complete(_process_vendor_file_async(job_id, file_path, db))

        logger.info(f"Vendor file processing completed successfully (async part finished)")
    except Exception as e:
        logger.error(f"Error processing vendor file task", exc_info=True)
        try:
            # Re-query the job within this exception handler
            job_in_error = db.query(Job).filter(Job.id == job_id).first()
            if job_in_error:
                # Ensure we don't overwrite a completed status if the error happens late
                if job_in_error.status != JobStatus.COMPLETED.value:
                    job_in_error.fail(f"Task failed: {str(e)}")
                    db.commit()
                    logger.info(f"Job status updated to failed due to task error",
                               extra={"error": str(e)})
                else:
                    logger.warning(f"Task error occurred after job was marked completed, status not changed.",
                                   extra={"error": str(e)})
            else:
                logger.error("Job not found when trying to mark as failed.", extra={"job_id": job_id})
        except Exception as db_error:
            logger.error(f"Error updating job status during task failure handling", exc_info=True,
                        extra={"original_error": str(e), "db_error": str(db_error)})
            db.rollback()
    finally:
        if db:
            db.close()
            logger.debug(f"Database session closed for task.")
        # Ensure loop is closed after run_until_complete finishes or if an error occurs
        if loop and not loop.is_closed():
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

    # --- Initialize stats ---
    start_time = datetime.now()
    stats = {
        "job_id": job.id,
        "company_name": job.company_name,
        "start_time": start_time.isoformat(),
        "end_time": None,
        "processing_duration_seconds": None,
        "total_vendors": 0,
        "unique_vendors": 0,
        "successfully_classified_initial": 0, # Count successful classifications before search
        "classification_not_possible_initial": 0, # Count initially unclassifiable
        "search_attempts": 0, # Count how many vendors needed search
        "search_successful_classifications": 0, # Count successful classifications *after* search
        "api_usage": {
            # --- USE CORRECT KEYS ---
            "openrouter_calls": 0,
            "openrouter_prompt_tokens": 0,
            "openrouter_completion_tokens": 0,
            "openrouter_total_tokens": 0,
            "tavily_search_calls": 0,
            # --- END USE CORRECT KEYS ---
            "cost_estimate_usd": 0.0 # Will calculate later if needed
        }
    }
    # --- End Initialize stats ---

    try:
        job.status = JobStatus.PROCESSING.value
        job.current_stage = ProcessingStage.INGESTION.value
        job.progress = 0.1
        db.commit()
        logger.info(f"Job status updated",
                   extra={"status": job.status, "stage": job.current_stage, "progress": job.progress})


        logger.info(f"Reading vendor file")
        with log_duration(logger, "Reading vendor file"):
            vendors = read_vendor_file(file_path) # Can raise ValueError or FileNotFoundError
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
        unique_vendors = list(dict.fromkeys(normalized_vendors)) # Efficient way to get unique while preserving order

        logger.info(f"Duplicates removed",
                   extra={"unique_count": len(unique_vendors)})

        stats["total_vendors"] = len(normalized_vendors) # Count includes duplicates
        stats["unique_vendors"] = len(unique_vendors)

        logger.info(f"Loading taxonomy")
        with log_duration(logger, "Loading taxonomy"):
            taxonomy = load_taxonomy() # Can raise exceptions
        logger.info(f"Taxonomy loaded",
                   extra={"taxonomy_version": taxonomy.version})

        results = {vendor: {} for vendor in unique_vendors}

        logger.info(f"Starting vendor classification process")
        # Process vendors through the multi-level classification
        await process_vendors(unique_vendors, taxonomy, results, stats, job, db, llm_service, search_service)
        logger.info(f"Vendor classification process completed")

        # --- UPDATE STAGE AND PROGRESS ---
        job.current_stage = ProcessingStage.RESULT_GENERATION.value
        job.progress = 0.95 # Increased progress after search/classification
        db.commit()
        logger.info(f"Job status updated",
                   extra={"stage": job.current_stage, "progress": job.progress})
        # --- END UPDATE ---

        logger.info(f"Generating output file")
        with log_duration(logger, "Generating output file"):
            # Pass the original list with duplicates for the output file
            output_file_name = generate_output_file(normalized_vendors, results, job_id) # Can raise IOError
        logger.info(f"Output file generated",
                   extra={"output_file": output_file_name})

        # --- Finalize stats ---
        end_time = datetime.now()
        processing_duration = (end_time - datetime.fromisoformat(stats["start_time"])).total_seconds()
        stats["end_time"] = end_time.isoformat()
        stats["processing_duration_seconds"] = processing_duration
        # Calculate estimated cost (adjust cost as needed)
        # Example cost: $0.0005 per 1k input, $0.0015 per 1k output for a blended model
        cost_input_per_1k = 0.0005
        cost_output_per_1k = 0.0015
        estimated_cost = (stats["api_usage"]["openrouter_prompt_tokens"] / 1000) * cost_input_per_1k + \
                         (stats["api_usage"]["openrouter_completion_tokens"] / 1000) * cost_output_per_1k
        # Add Tavily cost if applicable (e.g., $4 per 1000 searches)
        estimated_cost += (stats["api_usage"]["tavily_search_calls"] / 1000) * 4.0
        stats["api_usage"]["cost_estimate_usd"] = round(estimated_cost, 4)
        # --- End Finalize stats ---

        job.complete(output_file_name, stats)
        db.commit()
        logger.info(f"Job completed successfully",
                   extra={
                       "processing_duration": processing_duration,
                       "output_file": output_file_name,
                       "openrouter_calls": stats["api_usage"]["openrouter_calls"],
                       "tokens_used": stats["api_usage"]["openrouter_total_tokens"],
                       "tavily_calls": stats["api_usage"]["tavily_search_calls"],
                       "estimated_cost": stats["api_usage"]["cost_estimate_usd"]
                   })

    except (ValueError, FileNotFoundError, IOError) as file_err:
        logger.error(f"[_process_vendor_file_async] File reading or writing error", exc_info=True,
                    extra={"error": str(file_err)})
        job.fail(f"File processing error: {str(file_err)}")
        db.commit()
    except Exception as async_err:
        logger.error(f"[_process_vendor_file_async] Unexpected error during async processing", exc_info=True,
                    extra={"error": str(async_err)})
        # --- MODIFICATION: Ensure job status is updated even with unexpected errors ---
        # Check if job status is already failed or completed to avoid overwriting
        if job.status not in [JobStatus.FAILED.value, JobStatus.COMPLETED.value]:
            job.fail(f"Unexpected error: {str(async_err)}")
            db.commit()
        else:
            logger.warning(f"Unexpected error occurred but job status was already {job.status}. Error: {async_err}")
            db.rollback() # Rollback potential partial changes if any happened before error
        # --- END MODIFICATION ---
        # Don't re-raise here, let the outer handler manage final logging/cleanup
    finally:
        logger.info(f"[_process_vendor_file_async] Finished async processing for job {job_id}")


@log_function_call(logger, include_args=False) # Keep args=False
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
    Process vendors through the classification workflow, including search for unknowns.
    Updates results and stats dictionaries in place.
    """
    total_unique_vendors = len(vendors)
    processed_count = 0

    # Classification Levels 1-4
    vendors_to_process_next = vendors # Start with all unique vendors for Level 1
    for level in range(1, 5):
        job.current_stage = getattr(ProcessingStage, f"CLASSIFICATION_L{level}").value
        job.progress = 0.2 + (level * 0.15) # Approximate progress
        db.commit()
        logger.info(f"Starting Level {level} classification for {len(vendors_to_process_next)} vendors")

        # Group vendors for the current level
        if level == 1:
            grouped_vendors = { None: vendors_to_process_next } # No parent for level 1
        else:
            grouped_vendors = group_by_parent_category(results, level - 1, vendors_to_process_next)

        logger.info(f"Grouped vendors for Level {level}",
                   extra={"group_count": len(grouped_vendors)})

        processed_in_level = set()
        vendors_classified_in_level = []

        for parent_category, group_vendors in grouped_vendors.items():
            if not group_vendors: continue

            logger.info(f"Processing Level {level} group",
                       extra={"parent_category": parent_category, "vendor_count": len(group_vendors)})
            level_batches = create_batches(group_vendors, batch_size=settings.BATCH_SIZE)

            for i, batch in enumerate(level_batches):
                logger.info(f"Processing Level {level} batch {i+1}/{len(level_batches)} for parent '{parent_category or 'None'}'",
                           extra={"batch_size": len(batch)})
                try:
                    batch_results = await process_batch(batch, level, parent_category, taxonomy, llm_service, stats)
                    for vendor, classification in batch_results.items():
                        if vendor in results:
                            results[vendor][f"level{level}"] = classification
                            processed_in_level.add(vendor)
                            if not classification.get("classification_not_possible", False):
                                vendors_classified_in_level.append(vendor)
                except Exception as batch_error:
                    logger.error(f"Error processing Level {level} batch for parent '{parent_category or 'None'}'", exc_info=True,
                                 extra={"batch_vendors": batch, "error": str(batch_error)})
                    # Mark vendors in failed batch as unclassified for this level
                    for vendor in batch:
                         if vendor in results:
                            results[vendor][f"level{level}"] = {
                                "category_id": "ERROR",
                                "category_name": "ERROR",
                                "confidence": 0.0,
                                "classification_not_possible": True,
                                "classification_not_possible_reason": f"Batch processing error: {str(batch_error)[:100]}"
                            }
                            processed_in_level.add(vendor)

                # Update overall progress slightly after each batch
                processed_count += len(batch)
                job.progress = 0.2 + (level * 0.15) + (0.15 * (processed_count / total_unique_vendors))
                db.commit()

        logger.info(f"Level {level} classification completed. Processed {len(processed_in_level)} vendors.")

        # Prepare list of vendors successfully classified at this level for the *next* level
        vendors_to_process_next = vendors_classified_in_level

        if not vendors_to_process_next:
            logger.info(f"No vendors successfully classified at Level {level} to proceed to Level {level+1}.")
            break # Stop if no vendors can proceed

    # Identify initially unclassifiable vendors after all levels
    stats["classification_not_possible_initial"] = sum(
        1 for vendor in vendors
        if any(res.get("classification_not_possible", False) for key, res in results[vendor].items() if key.startswith("level"))
    )
    stats["successfully_classified_initial"] = total_unique_vendors - stats["classification_not_possible_initial"]

    # Search for Unknown Vendors
    job.current_stage = ProcessingStage.SEARCH.value
    job.progress = 0.85 # Progress after initial classification attempts
    db.commit()
    logger.info(f"Starting search for {stats['classification_not_possible_initial']} initially unknown vendors")

    unknown_vendors_to_search = [
        vendor for vendor in vendors
        if any(res.get("classification_not_possible", False) for key, res in results[vendor].items() if key.startswith("level"))
    ]
    stats["search_attempts"] = len(unknown_vendors_to_search)

    if unknown_vendors_to_search:
        search_tasks = [
            search_vendor(vendor, taxonomy, llm_service, search_service, stats)
            for vendor in unknown_vendors_to_search
        ]
        search_results_list = await asyncio.gather(*search_tasks, return_exceptions=True)

        successful_searches = 0
        for i, search_result_or_exc in enumerate(search_results_list):
             vendor = unknown_vendors_to_search[i]
             if isinstance(search_result_or_exc, Exception):
                 logger.error(f"Error searching for vendor {vendor}", exc_info=search_result_or_exc)
                 results[vendor]["search_results"] = {"error": str(search_result_or_exc)}
             else:
                 search_result = search_result_or_exc
                 results[vendor]["search_results"] = search_result

                 # --- MODIFICATION: Safely access classification data ---
                 classification_data = search_result.get("classification") # Safely get classification dict

                 if classification_data and not classification_data.get("classification_not_possible", True):
                     # Classification was successful via search
                     results[vendor]["level1"] = classification_data # Overwrite L1
                     results[vendor]["level1"]["notes"] = f"Classified via search: {classification_data.get('notes', '')}"
                     successful_searches += 1
                     # Clear potentially failed L2-L4 classifications if L1 changed
                     for lvl in range(2, 5):
                         results[vendor].pop(f'level{lvl}', None)
                     logger.info(f"Vendor search processed", extra={"vendor": vendor, "classified_after_search": True})
                 else:
                     # Classification via search was not possible or classification data was missing
                     reason = "Classification data missing from search result"
                     if classification_data: # Check if the dict exists even if classification failed
                         reason = classification_data.get("classification_not_possible_reason", "Search did not yield classification")
                     logger.info(f"Vendor search processed", extra={"vendor": vendor, "classified_after_search": False, "reason": reason})
                 # --- END MODIFICATION ---

        stats["search_successful_classifications"] = successful_searches
        logger.info(f"Unknown vendor search completed. Successfully classified {successful_searches} via search.")
    else:
        logger.info("No unknown vendors identified for search.")


@log_function_call(logger, include_args=False) # Keep args=False
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
    Updates stats dictionary in place.
    Returns results for the batch.
    """
    results = {}
    if not batch:
        return results

    logger.debug(f"Sending batch to LLM for classification",
               extra={"level": level, "batch_size": len(batch), "parent_category": parent_category})

    # --- MODIFIED: Wrap LLM call in try/except ---
    try:
        with LogTimer(logger, f"LLM classification - Level {level}", include_in_stats=True):
            response = await llm_service.classify_batch(batch, level, taxonomy, parent_category)

        # --- USE CORRECT KEYS ---
        stats["api_usage"]["openrouter_calls"] += 1
        stats["api_usage"]["openrouter_prompt_tokens"] += response["usage"]["prompt_tokens"]
        stats["api_usage"]["openrouter_completion_tokens"] += response["usage"]["completion_tokens"]
        stats["api_usage"]["openrouter_total_tokens"] += response["usage"]["total_tokens"]
        # --- END USE CORRECT KEYS ---

        logger.debug(f"LLM API usage updated",
                   extra={
                       "level": level,
                       "prompt_tokens": response["usage"]["prompt_tokens"],
                       "completion_tokens": response["usage"]["completion_tokens"],
                       "total_tokens": response["usage"]["total_tokens"]
                   })

        classifications = response.get("result", {}).get("classifications", [])
        if not classifications:
             logger.warning("LLM response missing 'classifications' array.", extra={"response_preview": str(response)[:200]})
             raise ValueError("LLM response structure invalid: missing 'classifications'.")

        logger.debug(f"Received {len(classifications)} classifications from LLM for batch size {len(batch)}")

        # Validate and process results, ensuring all vendors in batch are covered
        processed_vendors_in_response = set()
        for classification in classifications:
            vendor_name = classification.get("vendor_name")
            if not vendor_name:
                logger.warning("Classification received without vendor_name", extra={"classification": classification})
                continue
            processed_vendors_in_response.add(vendor_name)

            # Handle potential missing fields gracefully
            category_id = classification.get("category_id", "N/A")
            category_name = classification.get("category_name", "N/A")
            confidence = classification.get("confidence", 0.0)
            classification_not_possible = classification.get("classification_not_possible", False)
            reason = classification.get("classification_not_possible_reason", None)

            # Ensure consistency: if not possible, confidence must be 0
            if classification_not_possible and confidence > 0.0:
                logger.warning("Correcting confidence to 0.0 for classification_not_possible=true", extra={"vendor": vendor_name})
                confidence = 0.0
            # Ensure consistency: if possible, category should not be N/A (unless LLM explicitly provides it)
            if not classification_not_possible and (category_id == "N/A" or category_name == "N/A"):
                 logger.warning("Classification possible but category ID/Name is 'N/A'", extra={"vendor": vendor_name})
                 # Optionally mark as not possible if category is truly missing
                 # classification_not_possible = True
                 # reason = reason or "Missing category ID/Name despite classification success"

            results[vendor_name] = {
                "category_id": category_id,
                "category_name": category_name,
                "confidence": confidence,
                "classification_not_possible": classification_not_possible,
                "classification_not_possible_reason": reason
            }
            logger.debug(f"Vendor classified",
                       extra={
                           "vendor": vendor_name,
                           "level": level,
                           "category_id": category_id,
                           "confidence": confidence,
                           "classification_possible": not classification_not_possible
                       })

        # Check if any vendors from the input batch are missing in the response
        missing_vendors = set(batch) - processed_vendors_in_response
        if missing_vendors:
            logger.warning(f"LLM response did not include results for all vendors in the batch.", extra={"missing_vendors": list(missing_vendors), "level": level})
            for vendor in missing_vendors:
                results[vendor] = {
                    "category_id": "N/A",
                    "category_name": "N/A",
                    "confidence": 0.0,
                    "classification_not_possible": True,
                    "classification_not_possible_reason": "Vendor missing from LLM response batch"
                }

    # --- END MODIFIED: Wrap LLM call in try/except ---
    except Exception as e:
        logger.error(f"Failed to process batch at Level {level}", exc_info=True,
                     extra={"batch": batch, "error": str(e)})
        # Mark all vendors in this batch as failed for this level
        for vendor in batch:
            results[vendor] = {
                "category_id": "ERROR",
                "category_name": "ERROR",
                "confidence": 0.0,
                "classification_not_possible": True,
                "classification_not_possible_reason": f"Batch processing error: {str(e)[:100]}"
            }
    return results


@log_function_call(logger, include_args=False) # Keep args=False
async def search_vendor(
    vendor: str,
    taxonomy: Taxonomy,
    llm_service: LLMService,
    search_service: SearchService,
    stats: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Search for vendor information and attempt classification using LLM.
    Updates stats dictionary in place.
    Returns search results possibly augmented with classification.
    """
    logger.info(f"Searching for vendor information", extra={"vendor": vendor})
    # --- MODIFICATION: Initialize classification to None ---
    search_result_data = {"vendor": vendor, "search_query": f"{vendor} company business type industry", "sources": [], "error": None, "classification": None}
    # --- END MODIFICATION ---
    try:
        with LogTimer(logger, "Tavily search", include_in_stats=True):
            tavily_response = await search_service.search_vendor(vendor)

        stats["api_usage"]["tavily_search_calls"] += 1
        search_result_data.update(tavily_response) # Update with actual search results or error from service

        source_count = len(search_result_data.get("sources", []))
        if search_result_data.get("error"):
            logger.warning(f"Search failed for vendor", extra={"vendor": vendor, "error": search_result_data["error"]})
            # --- MODIFICATION: Ensure classification is set to failure on search error ---
            search_result_data["classification"] = {
                 "classification_not_possible": True,
                 "classification_not_possible_reason": f"Search error: {search_result_data['error'][:100]}",
                 "confidence": 0.0
            }
            # --- END MODIFICATION ---
        else:
            logger.info(f"Search completed", extra={"vendor": vendor, "source_count": source_count})

        # Proceed to classification only if search was successful and yielded sources
        if not search_result_data.get("error") and search_result_data.get("sources"):
            logger.info(f"Classifying vendor based on search results", extra={"vendor": vendor})
            with LogTimer(logger, "LLM classification from search", include_in_stats=True):
                llm_response = await llm_service.process_search_results(vendor, search_result_data, taxonomy)

            # --- USE CORRECT KEYS ---
            stats["api_usage"]["openrouter_calls"] += 1
            stats["api_usage"]["openrouter_prompt_tokens"] += llm_response["usage"]["prompt_tokens"]
            stats["api_usage"]["openrouter_completion_tokens"] += llm_response["usage"]["completion_tokens"]
            stats["api_usage"]["openrouter_total_tokens"] += llm_response["usage"]["total_tokens"]
            # --- END USE CORRECT KEYS ---

            logger.debug(f"LLM API usage for search processing updated",
                       extra={
                           "vendor": vendor,
                           "prompt_tokens": llm_response["usage"]["prompt_tokens"],
                           "completion_tokens": llm_response["usage"]["completion_tokens"],
                           "total_tokens": llm_response["usage"]["total_tokens"]
                       })

            search_result_data["classification"] = llm_response.get("result") # Store the classification part

            classification_possible = search_result_data["classification"] and not search_result_data["classification"].get("classification_not_possible", True)

            if classification_possible:
                # stats["search_successful_classifications"] += 1 # Moved calculation to process_vendors
                logger.info(f"Successful classification from search",
                           extra={
                               "vendor": vendor,
                               "category_id": search_result_data["classification"].get("category_id", "unknown"),
                               "confidence": search_result_data["classification"].get("confidence", 0)
                           })
            else:
                logger.info(f"Classification from search not possible",
                           extra={
                               "vendor": vendor,
                               "reason": search_result_data.get("classification", {}).get("classification_not_possible_reason", "unknown reason")
                           })
        elif not search_result_data.get("error"): # Case: Search succeeded but found no sources
            logger.warning(f"No search results sources found for vendor, skipping classification attempt", extra={"vendor": vendor})
            search_result_data["classification"] = {
                 "classification_not_possible": True,
                 "classification_not_possible_reason": "No search results found",
                 "confidence": 0.0
            }

    except Exception as e:
        logger.error(f"Unexpected error during search_vendor for {vendor}", exc_info=True)
        search_result_data["error"] = f"Unexpected error in search task: {str(e)}"
        # --- MODIFICATION: Ensure classification is set on unexpected error ---
        search_result_data["classification"] = {
             "classification_not_possible": True,
             "classification_not_possible_reason": f"Search task error: {str(e)[:100]}",
             "confidence": 0.0
        }
        # --- END MODIFICATION ---

    return search_result_data


def create_batches(items: List[Any], batch_size: int) -> List[List[Any]]:
    """Create batches from a list of items."""
    if batch_size <= 0: batch_size = 10 # Default safeguard
    return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]


def group_by_parent_category(results: Dict[str, Dict], parent_level: int, vendors_to_group: List[str]) -> Dict[Optional[str], List[str]]:
    """
    Group a specific list of vendors based on their classification at the parent_level.
    Handles vendors that might not have a result for the parent level yet or were unclassifiable.
    """
    grouped: Dict[Optional[str], List[str]] = {}
    parent_key = f"level{parent_level}"

    for vendor in vendors_to_group:
        vendor_results = results.get(vendor, {})
        level_result = vendor_results.get(parent_key)

        # Only group vendors that were successfully classified at the parent level
        if level_result and not level_result.get("classification_not_possible", False):
            category_id = level_result.get("category_id")
            if category_id and category_id != "N/A":
                if category_id not in grouped:
                    grouped[category_id] = []
                grouped[category_id].append(vendor)
            else:
                # Treat vendors classified without a valid category ID at parent level as unclassifiable for next level grouping
                logger.debug(f"Vendor '{vendor}' had successful parent level ({parent_key}) but invalid category_id '{category_id}', excluding from next level grouping.")
        else:
            # Vendors not processed or not classifiable at parent level won't be grouped for the next level
             logger.debug(f"Vendor '{vendor}' not successfully classified at parent level ({parent_key}), excluding from next level grouping.")


    return grouped

# --- NO CHANGE NEEDED for identify_unknown_vendors ---
def identify_unknown_vendors(results: Dict[str, Dict]) -> List[str]:
    """Identify vendors that couldn't be classified even at Level 1 initially."""
    unknown_vendors = []
    for vendor, vendor_results in results.items():
        # Check specifically if Level 1 classification failed or wasn't possible
        level1_result = vendor_results.get("level1")
        if not level1_result or level1_result.get("classification_not_possible", False):
            unknown_vendors.append(vendor)
    return unknown_vendors