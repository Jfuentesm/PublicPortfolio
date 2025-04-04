# <file path='app/tasks/classification_tasks.py'>
# --- file path='app/tasks/classification_tasks.py' ---
# app/tasks/classification_tasks.py
import os
import time
import asyncio
import logging # <<< Ensure logging is imported
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from celery import shared_task
from sqlalchemy.orm import Session

from core.database import SessionLocal
from core.config import settings
from core.logging_config import (
    get_logger, LogTimer, set_correlation_id, set_job_id,
    log_function_call, set_log_context, log_duration
)
from models.job import Job, JobStatus, ProcessingStage # Updated import
# --- MODIFIED IMPORT: Include L5 ---
from models.taxonomy import Taxonomy, TaxonomyLevel1, TaxonomyLevel2, TaxonomyLevel3, TaxonomyLevel4, TaxonomyLevel5
# --- END MODIFIED IMPORT ---
from services.file_service import read_vendor_file, normalize_vendor_data, generate_output_file
from services.llm_service import LLMService
from services.search_service import SearchService
from utils.taxonomy_loader import load_taxonomy

# Configure logger
logger = get_logger("vendor_classification.tasks")

# --- Constants ---
MAX_CONCURRENT_SEARCHES = 10 # Limit concurrent search/LLM processing for unknown vendors

@shared_task(bind=True)
def process_vendor_file(self, job_id: str, file_path: str):
    """
    Process vendor file for classification. (Celery Task Entry Point)

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
    job = None # Initialize job to None

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
            db.close() # Close db session
            return

        with LogTimer(logger, "Complete file processing", level=logging.INFO, include_in_stats=True):
             # Run the async function within the loop created for this task
            loop.run_until_complete(_process_vendor_file_async(job_id, file_path, db))

        logger.info(f"Vendor file processing completed successfully (async part finished)")
    except Exception as e:
        logger.error(f"Error processing vendor file task", exc_info=True)
        try:
            # Re-query the job within this exception handler if it wasn't fetched initially or became None
            # Use a new session for safety in exception handling
            db_error_session = SessionLocal()
            try:
                job_in_error = db_error_session.query(Job).filter(Job.id == job_id).first()
                if job_in_error:
                    # Ensure we don't overwrite a completed status if the error happens late
                    if job_in_error.status != JobStatus.COMPLETED.value:
                        job_in_error.fail(f"Task failed: {str(e)}")
                        db_error_session.commit()
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
                db_error_session.rollback()
            finally:
                 db_error_session.close()
        except Exception as final_db_error:
             logger.critical(f"CRITICAL: Failed even to handle database update in task error handler.", exc_info=final_db_error)

    finally:
        if db: # Close the main session used by the async function
            db.close()
            logger.debug(f"Main database session closed for task.")
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

    # --- Initialize stats (Updated for L5) ---
    start_time = datetime.now()
    stats = {
        "job_id": job.id,
        "company_name": job.company_name,
        "start_time": start_time.isoformat(),
        "end_time": None,
        "processing_duration_seconds": None,
        "total_vendors": 0,
        "unique_vendors": 0,
        "successfully_classified_l4": 0, # Keep L4 count for reference
        "successfully_classified_l5": 0, # NEW: Count successful classifications reaching L5
        "classification_not_possible_initial": 0, # Count initially unclassifiable before search
        "invalid_category_errors": 0, # Track validation errors
        "search_attempts": 0, # Count how many vendors needed search
        "search_successful_classifications_l1": 0, # Count successful L1 classifications *after* search
        "search_successful_classifications_l5": 0, # NEW: Count successful L5 classifications *after* search
        "api_usage": {
            "openrouter_calls": 0,
            "openrouter_prompt_tokens": 0,
            "openrouter_completion_tokens": 0,
            "openrouter_total_tokens": 0,
            "tavily_search_calls": 0,
            "cost_estimate_usd": 0.0
        }
    }
    # --- End Initialize stats ---

    try:
        job.status = JobStatus.PROCESSING.value
        job.current_stage = ProcessingStage.INGESTION.value
        job.progress = 0.05
        logger.info(f"[_process_vendor_file_async] Committing initial status update: {job.status}, {job.current_stage}, {job.progress}")
        db.commit()
        logger.info(f"Job status updated",
                   extra={"status": job.status, "stage": job.current_stage, "progress": job.progress})

        logger.info(f"Reading vendor file")
        with log_duration(logger, "Reading vendor file"):
            vendors_data = read_vendor_file(file_path)
        logger.info(f"Vendor file read successfully",
                   extra={"vendor_count": len(vendors_data)})

        job.current_stage = ProcessingStage.NORMALIZATION.value
        job.progress = 0.1
        logger.info(f"[_process_vendor_file_async] Committing status update: {job.status}, {job.current_stage}, {job.progress}")
        db.commit()
        logger.info(f"Job status updated",
                   extra={"stage": job.current_stage, "progress": job.progress})

        logger.info(f"Normalizing vendor data")
        with log_duration(logger, "Normalizing vendor data"):
            normalized_vendors_data = normalize_vendor_data(vendors_data)
        logger.info(f"Vendor data normalized",
                   extra={"normalized_count": len(normalized_vendors_data)})

        logger.info(f"Identifying unique vendors")
        unique_vendors_map: Dict[str, Dict[str, Any]] = {}
        for entry in normalized_vendors_data:
            name = entry.get('vendor_name')
            if name and name not in unique_vendors_map:
                unique_vendors_map[name] = entry
        logger.info(f"Unique vendors identified",
                   extra={"unique_count": len(unique_vendors_map)})

        stats["total_vendors"] = len(normalized_vendors_data)
        stats["unique_vendors"] = len(unique_vendors_map)

        logger.info(f"Loading taxonomy")
        with log_duration(logger, "Loading taxonomy"):
            taxonomy = load_taxonomy() # Can raise exceptions
        logger.info(f"Taxonomy loaded",
                   extra={"taxonomy_version": taxonomy.version})

        results: Dict[str, Dict] = {vendor_name: {} for vendor_name in unique_vendors_map.keys()}

        logger.info(f"Starting vendor classification process")
        await process_vendors(unique_vendors_map, taxonomy, results, stats, job, db, llm_service, search_service)
        logger.info(f"Vendor classification process completed")

        # --- UPDATE STAGE AND PROGRESS ---
        job.current_stage = ProcessingStage.RESULT_GENERATION.value
        job.progress = 0.98 # Progress after all classification/search
        logger.info(f"[_process_vendor_file_async] Committing status update: {job.status}, {job.current_stage}, {job.progress}")
        db.commit()
        logger.info(f"Job status updated",
                   extra={"stage": job.current_stage, "progress": job.progress})
        # --- END UPDATE ---

        logger.info(f"Generating output file")
        with log_duration(logger, "Generating output file"):
            output_file_name = generate_output_file(normalized_vendors_data, results, job_id) # Can raise IOError
        logger.info(f"Output file generated",
                   extra={"output_file": output_file_name})

        # --- Finalize stats ---
        end_time = datetime.now()
        processing_duration = (end_time - datetime.fromisoformat(stats["start_time"])).total_seconds()
        stats["end_time"] = end_time.isoformat()
        stats["processing_duration_seconds"] = round(processing_duration, 2)
        # Calculate estimated cost (adjust cost as needed)
        cost_input_per_1k = 0.0005
        cost_output_per_1k = 0.0015
        estimated_cost = (stats["api_usage"]["openrouter_prompt_tokens"] / 1000) * cost_input_per_1k + \
                         (stats["api_usage"]["openrouter_completion_tokens"] / 1000) * cost_output_per_1k
        estimated_cost += (stats["api_usage"]["tavily_search_calls"] / 1000) * 4.0
        stats["api_usage"]["cost_estimate_usd"] = round(estimated_cost, 4)
        # --- End Finalize stats ---

        job.complete(output_file_name, stats)
        job.progress = 1.0 # Ensure progress is 1.0 on completion
        logger.info(f"[_process_vendor_file_async] Committing final job completion status.")
        db.commit()
        logger.info(f"Job completed successfully",
                   extra={
                       "processing_duration": processing_duration,
                       "output_file": output_file_name,
                       "openrouter_calls": stats["api_usage"]["openrouter_calls"],
                       "tokens_used": stats["api_usage"]["openrouter_total_tokens"],
                       "tavily_calls": stats["api_usage"]["tavily_search_calls"],
                       "estimated_cost": stats["api_usage"]["cost_estimate_usd"],
                       "invalid_category_errors": stats.get("invalid_category_errors", 0),
                       "successfully_classified_l5_total": stats.get("successfully_classified_l5", 0) # Final L5 count
                   })

    except (ValueError, FileNotFoundError, IOError) as file_err:
        logger.error(f"[_process_vendor_file_async] File reading or writing error", exc_info=True,
                    extra={"error": str(file_err)})
        if job:
            job.fail(f"File processing error: {str(file_err)}")
            db.commit() # Commit the failure status
        else:
            logger.error("Job object was None during file error handling.")
    except Exception as async_err:
        logger.error(f"[_process_vendor_file_async] Unexpected error during async processing", exc_info=True,
                    extra={"error": str(async_err)})
        if job:
            if job.status not in [JobStatus.FAILED.value, JobStatus.COMPLETED.value]:
                job.fail(f"Unexpected error: {str(async_err)}")
                db.commit() # Commit the failure status
            else:
                logger.warning(f"Unexpected error occurred but job status was already {job.status}. Error: {async_err}")
                db.rollback() # Rollback any pending changes if job was already terminal
        else:
            logger.error("Job object was None during unexpected error handling.")
    finally:
        logger.info(f"[_process_vendor_file_async] Finished async processing for job {job_id}")


@log_function_call(logger, include_args=False) # Keep args=False
async def process_vendors(
    unique_vendors_map: Dict[str, Dict[str, Any]], # Pass map containing full vendor data
    taxonomy: Taxonomy,
    results: Dict[str, Dict],
    stats: Dict[str, Any],
    job: Job,
    db: Session,
    llm_service: LLMService,
    search_service: SearchService
):
    """
    Process vendors through the classification workflow (Levels 1-5), including recursive search for unknowns.
    Updates results and stats dictionaries in place. Passes full vendor data to batching/search.
    """
    unique_vendor_names = list(unique_vendors_map.keys()) # Get names from map
    total_unique_vendors = len(unique_vendor_names)
    processed_count = 0 # Count unique vendors processed in batches

    logger.info(f"Starting classification loop for {total_unique_vendors} unique vendors.")

    # --- Initial Hierarchical Classification (Levels 1-5) ---
    vendors_to_process_next_level_names = set(unique_vendor_names) # Start with all unique vendor names for Level 1

    # --- MODIFIED: Loop up to Level 5 ---
    for level in range(1, 6):
        if not vendors_to_process_next_level_names:
            logger.info(f"No vendors remaining to process for Level {level}. Skipping.")
            continue # Skip level if no vendors need processing

        current_vendors_for_this_level = list(vendors_to_process_next_level_names) # Copy names for processing this level
        vendors_successfully_classified_in_level_names = set() # Track vendors that pass this level

        # --- MODIFIED: Use correct stage enum ---
        stage_enum_name = f"CLASSIFICATION_L{level}"
        if hasattr(ProcessingStage, stage_enum_name):
             job.current_stage = getattr(ProcessingStage, stage_enum_name).value
        else:
             logger.error(f"ProcessingStage enum does not have member '{stage_enum_name}'. Using default.")
             job.current_stage = ProcessingStage.PROCESSING.value # Fallback

        # Adjust progress calculation: Spread 0.1 to 0.8 across 5 levels
        job.progress = min(0.8, 0.1 + ((level - 1) * 0.14)) # 0.7 / 5 = 0.14 per level
        logger.info(f"[process_vendors] Committing status update before Level {level}: {job.status}, {job.current_stage}, {job.progress}")
        db.commit()
        logger.info(f"===== Starting Initial Level {level} Classification =====",
                   extra={ "vendors_to_process": len(current_vendors_for_this_level), "progress": job.progress })

        if level == 1:
            grouped_vendors_names = { None: current_vendors_for_this_level }
            logger.info(f"Level 1: Processing all {len(current_vendors_for_this_level)} vendors.")
        else:
            logger.info(f"Level {level}: Grouping {len(current_vendors_for_this_level)} vendors based on Level {level-1} results.")
            grouped_vendors_names = group_by_parent_category(results, level - 1, current_vendors_for_this_level)
            logger.info(f"Level {level}: Created {len(grouped_vendors_names)} groups for processing.")
            for parent_id, names in grouped_vendors_names.items():
                 logger.debug(f"  Group Parent ID '{parent_id}': {len(names)} vendors")

        processed_in_level_count = 0
        batch_counter_for_level = 0
        total_batches_for_level = sum( (len(names) + settings.BATCH_SIZE - 1) // settings.BATCH_SIZE for names in grouped_vendors_names.values() )

        for parent_category_id, group_vendor_names in grouped_vendors_names.items():
            if not group_vendor_names:
                logger.debug(f"Skipping empty group for parent '{parent_category_id}' at Level {level}.")
                continue

            logger.info(f"Processing Level {level} group",
                       extra={"parent_category_id": parent_category_id, "vendor_count": len(group_vendor_names)})

            group_vendor_data = [unique_vendors_map[name] for name in group_vendor_names if name in unique_vendors_map]
            level_batches_data = create_batches(group_vendor_data, batch_size=settings.BATCH_SIZE)
            logger.debug(f"Created {len(level_batches_data)} batches for group '{parent_category_id}' at Level {level}.")

            for i, batch_data in enumerate(level_batches_data):
                batch_counter_for_level += 1
                batch_names = [vd['vendor_name'] for vd in batch_data] # Get names for logging
                logger.info(f"Processing Level {level} batch {i+1}/{len(level_batches_data)} for parent '{parent_category_id or 'None'}'",
                           extra={"batch_size": len(batch_data), "first_vendor": batch_names[0] if batch_names else 'N/A'})
                try:
                    # Process batch WITHOUT search context initially
                    batch_results = await process_batch(batch_data, level, parent_category_id, taxonomy, llm_service, stats, search_context=None)

                    for vendor_name, classification in batch_results.items():
                        if vendor_name in results:
                            results[vendor_name][f"level{level}"] = classification
                            processed_in_level_count += 1

                            if not classification.get("classification_not_possible", True):
                                vendors_successfully_classified_in_level_names.add(vendor_name)
                                logger.debug(f"Vendor '{vendor_name}' successfully classified at Level {level} (ID: {classification.get('category_id')}). Added for L{level+1}.")
                            else:
                                logger.debug(f"Vendor '{vendor_name}' not successfully classified at Level {level}. Reason: {classification.get('classification_not_possible_reason', 'Unknown')}. Will not proceed.")
                        else:
                             logger.warning(f"Vendor '{vendor_name}' from batch result not found in main results dictionary.", extra={"level": level})

                except Exception as batch_error:
                    logger.error(f"Error during initial batch processing logic (Level {level}, parent '{parent_category_id or 'None'}')", exc_info=True,
                                 extra={"batch_vendors": batch_names, "error": str(batch_error)})
                    for vendor_name in batch_names:
                         if vendor_name in results:
                            if f"level{level}" not in results[vendor_name]:
                                results[vendor_name][f"level{level}"] = {
                                    "category_id": "ERROR", "category_name": "ERROR", "confidence": 0.0,
                                    "classification_not_possible": True,
                                    "classification_not_possible_reason": f"Batch processing logic error: {str(batch_error)[:100]}",
                                    "vendor_name": vendor_name
                                }
                            processed_in_level_count += 1
                         else:
                              logger.warning(f"Vendor '{vendor_name}' from failed batch not found in main results dictionary.", extra={"level": level})

                # Update progress within the level (based on batches completed)
                level_progress_fraction = batch_counter_for_level / total_batches_for_level if total_batches_for_level > 0 else 1
                # Spread progress for this level within its 0.14 range (updated for 5 levels)
                job.progress = min(0.8, 0.1 + ((level - 1) * 0.14) + (0.14 * level_progress_fraction))
                try:
                    logger.info(f"[process_vendors] Committing progress update after batch {batch_counter_for_level}/{total_batches_for_level} (Level {level}): {job.progress:.3f}")
                    db.commit()
                except Exception as db_err:
                     logger.error("Failed to commit progress update during batch processing", exc_info=True)
                     db.rollback()

        logger.info(f"===== Initial Level {level} Classification Completed =====")
        logger.info(f"  Processed {processed_in_level_count} vendor results at Level {level}.")
        logger.info(f"  {len(vendors_successfully_classified_in_level_names)} vendors successfully classified and validated at Level {level}, proceeding to L{level+1}.")

        vendors_to_process_next_level_names = vendors_successfully_classified_in_level_names

    # --- End of Initial Level Loop ---
    logger.info("===== Finished Initial Hierarchical Classification Loop (Levels 1-5) =====")

    # --- Identify initially unclassifiable vendors (based on reaching L5) ---
    unknown_vendors_data_to_search = []
    initial_l5_success_count = 0
    initial_l4_success_count = 0 # Keep track of L4 success too
    for vendor_name in unique_vendor_names:
        is_classified_l5 = False
        is_classified_l4 = False # Track L4 separately
        if vendor_name in results:
            l4_result = results[vendor_name].get("level4")
            if l4_result and not l4_result.get("classification_not_possible", False):
                 is_classified_l4 = True
                 initial_l4_success_count += 1
            l5_result = results[vendor_name].get("level5")
            if l5_result and not l5_result.get("classification_not_possible", False):
                 is_classified_l5 = True
                 initial_l5_success_count += 1

        if not is_classified_l5: # If didn't reach L5 successfully
            logger.debug(f"Vendor '{vendor_name}' did not initially reach/pass Level 5 classification. Adding to search list.")
            if vendor_name in unique_vendors_map:
                unknown_vendors_data_to_search.append(unique_vendors_map[vendor_name])
            else:
                logger.warning(f"Vendor '{vendor_name}' marked for search but not found in unique_vendors_map.")
                unknown_vendors_data_to_search.append({'vendor_name': vendor_name})

    stats["classification_not_possible_initial"] = len(unknown_vendors_data_to_search)
    stats["successfully_classified_l4"] = initial_l4_success_count # Store initial L4 count
    stats["successfully_classified_l5"] = initial_l5_success_count # Store initial L5 count

    logger.info(f"Initial Classification Summary: {initial_l5_success_count} reached L5, {stats['classification_not_possible_initial']} did not.")

    # --- Search and Recursive Classification for Unknown Vendors ---
    if unknown_vendors_data_to_search:
        job.current_stage = ProcessingStage.SEARCH.value
        job.progress = 0.8 # Progress after initial classification attempts
        logger.info(f"[process_vendors] Committing status update before Search stage: {job.status}, {job.current_stage}, {job.progress}")
        db.commit()
        logger.info(f"===== Starting Search and Recursive Classification for {stats['classification_not_possible_initial']} Unclassified Vendors =====")

        stats["search_attempts"] = len(unknown_vendors_data_to_search)

        search_tasks = []
        search_semaphore = asyncio.Semaphore(MAX_CONCURRENT_SEARCHES)

        for vendor_data in unknown_vendors_data_to_search:
            task = asyncio.create_task(
                search_and_classify_recursively(
                    vendor_data, taxonomy, llm_service, search_service, stats, search_semaphore
                )
            )
            search_tasks.append(task)

        logger.info(f"Gathering results for {len(search_tasks)} search & recursive classification tasks...")
        search_and_recursive_results = await asyncio.gather(*search_tasks, return_exceptions=True)
        logger.info(f"Search & recursive classification tasks completed.")

        # --- ADDED: Progress update after gather ---
        job.progress = 0.95 # Indicate search phase is done, before result processing/generation
        logger.info(f"[process_vendors] Committing progress update after search gather: {job.progress:.3f}")
        db.commit()
        # --- END ADDED ---

        successful_l1_searches = 0
        successful_l5_searches = 0 # Track L5 success via search
        processed_search_count = 0

        for i, result_or_exc in enumerate(search_and_recursive_results):
            processed_search_count += 1
            if i >= len(unknown_vendors_data_to_search):
                 logger.error(f"Search result index {i} out of bounds for unknown_vendors list.")
                 continue
            vendor_data = unknown_vendors_data_to_search[i]
            vendor_name = vendor_data.get('vendor_name', f'UnknownVendor_{i}')

            if vendor_name not in results:
                 logger.warning(f"Vendor '{vendor_name}' from search task not found in main results dict. Initializing.")
                 results[vendor_name] = {}

            results[vendor_name]["search_attempted"] = True # Add flag

            if isinstance(result_or_exc, Exception):
                logger.error(f"Error during search_and_classify_recursively for vendor {vendor_name}", exc_info=result_or_exc)
                results[vendor_name]["search_results"] = {"error": f"Search/Recursive task error: {str(result_or_exc)}"}
                if "level1" not in results[vendor_name] or results[vendor_name]["level1"].get("classification_not_possible", True):
                    results[vendor_name]["level1"] = {
                        "classification_not_possible": True,
                        "classification_not_possible_reason": f"Search task error: {str(result_or_exc)[:100]}",
                        "confidence": 0.0, "vendor_name": vendor_name, "notes": "Search Failed"
                    }
            elif isinstance(result_or_exc, dict):
                search_data = result_or_exc
                results[vendor_name]["search_results"] = search_data # Store raw search info

                l1_classification = search_data.get("classification_l1")
                if l1_classification and not l1_classification.get("classification_not_possible", True):
                    successful_l1_searches += 1
                    logger.info(f"Vendor '{vendor_name}' classified via search (Level 1: {l1_classification.get('category_id')}).")
                    results[vendor_name]["classified_via_search"] = True # Add flag

                    if not results[vendor_name].get("level1") or results[vendor_name]["level1"].get("classification_not_possible", True):
                         results[vendor_name]["level1"] = l1_classification
                         if "notes" not in results[vendor_name]["level1"]: results[vendor_name]["level1"]["notes"] = ""
                         results[vendor_name]["level1"]["notes"] = f"Classified via search: {results[vendor_name]['level1']['notes']}"

                    # Store L2-L5 results obtained recursively
                    # --- MODIFIED: Loop up to Level 5 ---
                    for lvl in range(2, 6):
                        lvl_key = f"classification_l{lvl}"
                        if lvl_key in search_data:
                            results[vendor_name][f"level{lvl}"] = search_data[lvl_key]
                            # Check if L5 was successfully reached post-search
                            if lvl == 5 and not search_data[lvl_key].get("classification_not_possible", True):
                                successful_l5_searches += 1
                                logger.info(f"Vendor '{vendor_name}' reached L5 classification via search.")
                        else:
                            results[vendor_name].pop(f"level{lvl}", None)

                else: # L1 classification via search failed or wasn't possible
                    reason = "Search did not yield L1 classification"
                    if l1_classification: reason = l1_classification.get("classification_not_possible_reason", reason)
                    logger.info(f"Vendor '{vendor_name}' could not be classified via search at L1. Reason: {reason}")
                    if not results[vendor_name].get("level1") or results[vendor_name]["level1"].get("classification_not_possible", True):
                        results[vendor_name]["level1"] = {
                            "classification_not_possible": True,
                            "classification_not_possible_reason": reason,
                            "confidence": 0.0, "vendor_name": vendor_name, "notes": "Search Failed L1"
                        }
                    # --- MODIFIED: Clear L2-L5 ---
                    for lvl in range(2, 6): results[vendor_name].pop(f"level{lvl}", None)

            else: # Handle unexpected return type
                logger.error(f"Unexpected result type for vendor {vendor_name} search task: {type(result_or_exc)}")
                results[vendor_name]["search_results"] = {"error": f"Unexpected search result type: {type(result_or_exc)}"}
                if "level1" not in results[vendor_name] or results[vendor_name]["level1"].get("classification_not_possible", True):
                     results[vendor_name]["level1"] = { "classification_not_possible": True, "classification_not_possible_reason": "Internal search error", "confidence": 0.0, "vendor_name": vendor_name, "notes": "Search Error" }
                # --- MODIFIED: Clear L2-L5 ---
                for lvl in range(2, 6): results[vendor_name].pop(f"level{lvl}", None)

            # --- REMOVED: Progress update within this loop, moved after gather ---
            # search_progress_fraction = processed_search_count / len(unknown_vendors_data_to_search) if unknown_vendors_data_to_search else 1
            # job.progress = min(0.98, 0.8 + (0.18 * search_progress_fraction))
            # try:
            #     logger.info(f"[process_vendors] Committing progress update after search task {processed_search_count}/{len(unknown_vendors_data_to_search)}: {job.progress:.3f}")
            #     db.commit()
            # except Exception as db_err:
            #      logger.error("Failed to commit progress update during search processing", exc_info=True)
            #      db.rollback()
            # --- END REMOVED ---

        stats["search_successful_classifications_l1"] = successful_l1_searches
        stats["search_successful_classifications_l5"] = successful_l5_searches # Updated stat
        # Update total L5 success count
        stats["successfully_classified_l5"] = initial_l5_success_count + successful_l5_searches

        logger.info(f"===== Unknown Vendor Search & Recursive Classification Completed =====")
        logger.info(f"  Attempted search for {stats['search_attempts']} vendors.")
        logger.info(f"  Successfully classified {successful_l1_searches} at L1 via search.")
        logger.info(f"  Successfully classified {successful_l5_searches} at L5 via search.") # Updated stat
        logger.info(f"  Total vendors successfully classified at L5: {stats['successfully_classified_l5']}") # Updated stat
    else:
        logger.info("No unknown vendors required search.")
        job.progress = 0.98 # Set progress high if search wasn't needed
        logger.info(f"[process_vendors] Committing status update as search was skipped: {job.status}, {job.current_stage}, {job.progress}")
        db.commit()


@log_function_call(logger, include_args=False) # Keep args=False
async def process_batch(
    batch_data: List[Dict[str, Any]], # Pass list of dicts including optional fields
    level: int,
    parent_category_id: Optional[str],
    taxonomy: Taxonomy,
    llm_service: LLMService,
    stats: Dict[str, Any],
    search_context: Optional[Dict[str, Any]] = None # ADDED: Optional search context
) -> Dict[str, Dict]:
    """
    Process a batch of vendors for a specific classification level (1-5), including taxonomy validation.
    Optionally uses search context for post-search classification attempts.
    Updates stats dictionary in place. Passes full vendor data and context to LLM.
    Returns results for the batch.
    """
    results = {}
    if not batch_data:
        logger.warning(f"process_batch called with empty batch_data for Level {level}, Parent '{parent_category_id}'.")
        return results

    batch_names = [vd.get('vendor_name', f'Unknown_{i}') for i, vd in enumerate(batch_data)] # For logging
    context_type = "Search Context" if search_context else "Initial Data"

    logger.debug(f"process_batch: Preparing Level {level} batch using {context_type}.",
               extra={"batch_size": len(batch_data), "parent_category_id": parent_category_id})

    # --- Get valid category IDs for this level/parent (Updated for L5) ---
    valid_category_ids: Set[str] = set()
    category_id_lookup_error = False
    try:
        logger.debug(f"process_batch: Retrieving valid category IDs for Level {level}, Parent '{parent_category_id}'.")
        categories = []
        if level == 1:
            categories = taxonomy.get_level1_categories()
        elif parent_category_id:
            if level == 2:
                categories = taxonomy.get_level2_categories(parent_category_id)
            elif level == 3:
                categories = taxonomy.get_level3_categories(parent_category_id)
            elif level == 4:
                categories = taxonomy.get_level4_categories(parent_category_id)
            # --- ADDED LEVEL 5 ---
            elif level == 5:
                categories = taxonomy.get_level5_categories(parent_category_id)
            # --- END ADDED ---
            else:
                 categories = [] # Should not happen
        else: # level > 1 and no parent_category_id
             logger.error(f"process_batch: Parent category ID is required for Level {level} but was not provided.")
             categories = []

        valid_category_ids = {cat.id for cat in categories}

        if not valid_category_ids:
             if level > 1 and parent_category_id:
                 logger.warning(f"process_batch: No valid child categories found or retrieved for Level {level}, Parent '{parent_category_id}'. LLM cannot classify.")
             elif level == 1:
                 logger.error("process_batch: No Level 1 categories found in taxonomy!")
                 category_id_lookup_error = True
        else:
             logger.debug(f"process_batch: Found {len(valid_category_ids)} valid IDs for Level {level}, Parent '{parent_category_id}'. Example: {list(valid_category_ids)[:5]}")

    except Exception as tax_err:
        logger.error(f"process_batch: Error getting valid categories from taxonomy", exc_info=True,
                     extra={"level": level, "parent_category_id": parent_category_id})
        valid_category_ids = set()
        category_id_lookup_error = True

    # --- Call LLM ---
    llm_response_data = None
    try:
        with LogTimer(logger, f"LLM classification - Level {level}, Parent '{parent_category_id or 'None'}' ({context_type})", include_in_stats=True):
            llm_response_data = await llm_service.classify_batch(
                batch_data=batch_data,
                level=level,
                taxonomy=taxonomy,
                parent_category_id=parent_category_id,
                search_context=search_context
            )

        if llm_response_data and isinstance(llm_response_data.get("usage"), dict):
            usage = llm_response_data["usage"]
            stats["api_usage"]["openrouter_calls"] += 1
            stats["api_usage"]["openrouter_prompt_tokens"] += usage.get("prompt_tokens", 0)
            stats["api_usage"]["openrouter_completion_tokens"] += usage.get("completion_tokens", 0)
            stats["api_usage"]["openrouter_total_tokens"] += usage.get("total_tokens", 0)
            logger.debug(f"process_batch: LLM API usage updated", extra=usage)
        else:
            logger.warning("process_batch: LLM response missing or has invalid usage data.")

        llm_result = llm_response_data.get("result", {}) if llm_response_data else {}
        classifications = llm_result.get("classifications", [])
        if not isinstance(classifications, list):
             logger.warning("LLM response 'classifications' is not a list.", extra={"response_preview": str(llm_result)[:500]})
             classifications = []

        logger.debug(f"process_batch: Received {len(classifications)} classifications from LLM for batch size {len(batch_data)} at Level {level}.")
        if llm_result.get("batch_id_mismatch"):
             logger.warning(f"process_batch: Processing batch despite batch_id mismatch warning from LLM service.")

        # --- Validate and process results ---
        processed_vendors_in_response = set()
        for classification in classifications:
            if not isinstance(classification, dict):
                logger.warning("Invalid classification item format received from LLM (not a dict)", extra={"item": classification})
                continue

            vendor_name = classification.get("vendor_name")
            if not vendor_name:
                logger.warning("Classification received without vendor_name", extra={"classification": classification})
                continue

            target_vendor_name = vendor_name
            processed_vendors_in_response.add(target_vendor_name)

            category_id = classification.get("category_id", "N/A")
            category_name = classification.get("category_name", "N/A")
            confidence = classification.get("confidence", 0.0)
            classification_not_possible = classification.get("classification_not_possible", False)
            reason = classification.get("classification_not_possible_reason")
            notes = classification.get("notes")
            is_valid_category = True

            # --- TAXONOMY VALIDATION ---
            if not classification_not_possible and not category_id_lookup_error and valid_category_ids:
                if category_id not in valid_category_ids:
                    is_valid_category = False
                    logger.warning(f"Invalid category ID '{category_id}' returned by LLM for vendor '{target_vendor_name}' at level {level}, parent '{parent_category_id}'.",
                                   extra={"valid_ids": list(valid_category_ids)[:10]})
                    classification_not_possible = True
                    reason = f"Invalid category ID '{category_id}' returned by LLM (Valid examples: {list(valid_category_ids)[:3]})"
                    confidence = 0.0
                    category_id = "N/A"
                    category_name = "N/A"
                    stats["invalid_category_errors"] = stats.get("invalid_category_errors", 0) + 1
                else:
                     logger.debug(f"Category ID '{category_id}' for '{target_vendor_name}' is valid for Level {level}, Parent '{parent_category_id}'.")
            elif not classification_not_possible and category_id_lookup_error:
                 logger.warning(f"Cannot validate category ID '{category_id}' for '{target_vendor_name}' due to earlier taxonomy lookup error.")
            elif not classification_not_possible and not valid_category_ids and level > 1:
                 logger.warning(f"Cannot validate category ID '{category_id}' for '{target_vendor_name}' because no valid child categories were found for parent '{parent_category_id}'.")
                 is_valid_category = False
                 classification_not_possible = True
                 reason = f"LLM returned category '{category_id}' but no valid children found for parent '{parent_category_id}'."
                 confidence = 0.0
                 category_id = "N/A"; category_name = "N/A"
                 stats["invalid_category_errors"] = stats.get("invalid_category_errors", 0) + 1
            # --- End TAXONOMY VALIDATION ---

            # --- Consistency Checks ---
            if classification_not_possible and confidence > 0.0:
                logger.warning("Correcting confidence to 0.0 for classification_not_possible=true", extra={"vendor": target_vendor_name})
                confidence = 0.0
            if not classification_not_possible and is_valid_category and (category_id == "N/A" or not category_id):
                 logger.warning("Classification marked possible by LLM but category ID is 'N/A' or empty", extra={"vendor": target_vendor_name, "classification": classification})
                 classification_not_possible = True
                 reason = reason or "Missing category ID despite LLM success claim"
                 confidence = 0.0
                 category_id = "N/A"
                 category_name = "N/A"
            # --- End Consistency Checks ---

            results[target_vendor_name] = {
                "category_id": category_id,
                "category_name": category_name,
                "confidence": confidence,
                "classification_not_possible": classification_not_possible,
                "classification_not_possible_reason": reason,
                "notes": notes,
                "vendor_name": target_vendor_name
            }

        # Handle missing vendors from batch
        missing_vendors = set(batch_names) - processed_vendors_in_response
        if missing_vendors:
            logger.warning(f"LLM response did not include results for all vendors in the batch.", extra={"missing_vendors": list(missing_vendors), "level": level})
            for vendor_name in missing_vendors:
                results[vendor_name] = {
                    "category_id": "N/A", "category_name": "N/A", "confidence": 0.0,
                    "classification_not_possible": True,
                    "classification_not_possible_reason": "Vendor missing from LLM response batch",
                    "notes": None,
                    "vendor_name": vendor_name
                }

    except Exception as e:
        logger.error(f"Failed to process batch at Level {level} ({context_type})", exc_info=True,
                     extra={"batch_names": batch_names, "error": str(e)})
        for vendor_name in batch_names:
            results[vendor_name] = {
                "category_id": "ERROR", "category_name": "ERROR", "confidence": 0.0,
                "classification_not_possible": True,
                "classification_not_possible_reason": f"Batch processing error: {str(e)[:100]}",
                "notes": None,
                "vendor_name": vendor_name
            }
    return results


@log_function_call(logger, include_args=False)
async def search_and_classify_recursively(
    vendor_data: Dict[str, Any],
    taxonomy: Taxonomy,
    llm_service: LLMService,
    search_service: SearchService,
    stats: Dict[str, Any],
    semaphore: asyncio.Semaphore
) -> Dict[str, Any]:
    """
    Performs Tavily search, attempts L1 classification, and then recursively
    attempts L2-L5 classification using the search context. Controlled by semaphore.
    Returns the search_result_data dictionary, potentially augmented with
    classification results for L1-L5 (keyed as classification_l1, classification_l2, etc.).
    """
    vendor_name = vendor_data.get('vendor_name', 'UnknownVendor')
    async with semaphore: # Limit concurrency
        logger.info(f"search_and_classify_recursively: Starting for vendor", extra={"vendor": vendor_name})
        search_result_data = {
            "vendor": vendor_name,
            "search_query": f"{vendor_name} company business type industry",
            "sources": [],
            "summary": None,
            "error": None,
            # Keys for storing classification results obtained via search
            "classification_l1": None,
            "classification_l2": None,
            "classification_l3": None,
            "classification_l4": None,
            # --- ADDED L5 ---
            "classification_l5": None
            # --- END ADDED ---
         }

        # --- 1. Perform Tavily Search ---
        try:
            with LogTimer(logger, f"Tavily search for '{vendor_name}'", include_in_stats=True):
                tavily_response = await search_service.search_vendor(vendor_name)

            stats["api_usage"]["tavily_search_calls"] += 1
            search_result_data.update(tavily_response) # Update with actual search results or error

            source_count = len(search_result_data.get("sources", []))
            if search_result_data.get("error"):
                logger.warning(f"search_and_classify_recursively: Search failed", extra={"vendor": vendor_name, "error": search_result_data["error"]})
                search_result_data["classification_l1"] = {
                     "classification_not_possible": True,
                     "classification_not_possible_reason": f"Search error: {str(search_result_data['error'])[:100]}",
                     "confidence": 0.0, "vendor_name": vendor_name, "notes": "Search Failed"
                }
                return search_result_data # Stop if search failed
            else:
                logger.info(f"search_and_classify_recursively: Search completed", extra={"vendor": vendor_name, "source_count": source_count, "summary_present": bool(search_result_data.get('summary'))})

        except Exception as search_exc:
            logger.error(f"search_and_classify_recursively: Unexpected error during Tavily search for {vendor_name}", exc_info=True)
            search_result_data["error"] = f"Unexpected search error: {str(search_exc)}"
            search_result_data["classification_l1"] = {
                 "classification_not_possible": True,
                 "classification_not_possible_reason": f"Search task error: {str(search_exc)[:100]}",
                 "confidence": 0.0, "vendor_name": vendor_name, "notes": "Search Failed"
            }
            return search_result_data # Stop if search failed

        # --- 2. Attempt L1 Classification using Search Results ---
        search_content_available = search_result_data.get("sources") or search_result_data.get("summary")
        if not search_content_available:
            logger.warning(f"search_and_classify_recursively: No usable search results found for vendor, cannot classify", extra={"vendor": vendor_name})
            search_result_data["classification_l1"] = {
                 "classification_not_possible": True,
                 "classification_not_possible_reason": "No search results content found",
                 "confidence": 0.0, "vendor_name": vendor_name, "notes": "No Search Content"
            }
            return search_result_data # Stop if no content

        valid_l1_category_ids: Set[str] = set(taxonomy.categories.keys())
        llm_response_l1 = None
        try:
            with LogTimer(logger, f"LLM L1 classification from search for '{vendor_name}'", include_in_stats=True):
                llm_response_l1 = await llm_service.process_search_results(vendor_data, search_result_data, taxonomy)

            if llm_response_l1 and isinstance(llm_response_l1.get("usage"), dict):
                usage = llm_response_l1["usage"]
                stats["api_usage"]["openrouter_calls"] += 1
                stats["api_usage"]["openrouter_prompt_tokens"] += usage.get("prompt_tokens", 0)
                stats["api_usage"]["openrouter_completion_tokens"] += usage.get("completion_tokens", 0)
                stats["api_usage"]["openrouter_total_tokens"] += usage.get("total_tokens", 0)

            l1_classification = llm_response_l1.get("result", {}) if llm_response_l1 else {}
            if "vendor_name" not in l1_classification: l1_classification["vendor_name"] = vendor_name

            # Validate L1 result
            classification_not_possible_l1 = l1_classification.get("classification_not_possible", True)
            category_id_l1 = l1_classification.get("category_id", "N/A")
            is_valid_l1 = True

            if not classification_not_possible_l1 and valid_l1_category_ids:
                if category_id_l1 not in valid_l1_category_ids:
                    is_valid_l1 = False
                    logger.warning(f"Invalid L1 category ID '{category_id_l1}' from search LLM for '{vendor_name}'.", extra={"valid_ids": list(valid_l1_category_ids)[:10]})
                    l1_classification["classification_not_possible"] = True
                    l1_classification["classification_not_possible_reason"] = f"Invalid L1 category ID '{category_id_l1}' from search."
                    l1_classification["confidence"] = 0.0
                    l1_classification["category_id"] = "N/A"
                    l1_classification["category_name"] = "N/A"
                    stats["invalid_category_errors"] = stats.get("invalid_category_errors", 0) + 1

            if l1_classification.get("classification_not_possible") and l1_classification.get("confidence", 0.0) > 0.0: l1_classification["confidence"] = 0.0
            if not l1_classification.get("classification_not_possible") and not l1_classification.get("category_id", "N/A"):
                 l1_classification["classification_not_possible"] = True
                 l1_classification["classification_not_possible_reason"] = "Missing L1 category ID despite LLM success claim"
                 l1_classification["confidence"] = 0.0
                 l1_classification["category_id"] = "N/A"; l1_classification["category_name"] = "N/A"

            search_result_data["classification_l1"] = l1_classification # Store validated L1 result

        except Exception as llm_err:
             logger.error(f"search_and_classify_recursively: Error during LLM L1 processing for {vendor_name}", exc_info=True)
             search_result_data["error"] = search_result_data.get("error") or f"LLM L1 processing error: {str(llm_err)}"
             search_result_data["classification_l1"] = {
                 "classification_not_possible": True,
                 "classification_not_possible_reason": f"LLM L1 processing error: {str(llm_err)[:100]}",
                 "confidence": 0.0, "vendor_name": vendor_name, "notes": "LLM L1 Error"
             }
             return search_result_data # Stop if L1 classification failed

        # --- 3. Recursive Classification L2-L5 using Search Context ---
        current_parent_id = search_result_data["classification_l1"].get("category_id")
        classification_possible = not search_result_data["classification_l1"].get("classification_not_possible", True)

        if classification_possible and current_parent_id and current_parent_id != "N/A":
            logger.info(f"search_and_classify_recursively: L1 successful ({current_parent_id}), proceeding to L2-L5 for {vendor_name} using search context.")
            # --- MODIFIED: Loop up to Level 5 ---
            for level in range(2, 6):
                logger.debug(f"Attempting post-search Level {level} for {vendor_name}, parent {current_parent_id}")
                try:
                    batch_result_dict = await process_batch(
                        batch_data=[vendor_data], # Batch of one
                        level=level,
                        parent_category_id=current_parent_id,
                        taxonomy=taxonomy,
                        llm_service=llm_service,
                        stats=stats,
                        search_context=search_result_data # Pass the full search results as context
                    )

                    level_result = batch_result_dict.get(vendor_name)
                    if level_result:
                        search_result_data[f"classification_l{level}"] = level_result # Store result
                        if level_result.get("classification_not_possible", True):
                            logger.info(f"Post-search classification stopped at Level {level} for {vendor_name}. Reason: {level_result.get('classification_not_possible_reason')}")
                            break # Stop recursion if classification fails
                        else:
                            current_parent_id = level_result.get("category_id") # Update parent for next level
                            if not current_parent_id or current_parent_id == "N/A":
                                logger.warning(f"Post-search Level {level} successful but returned invalid parent_id '{current_parent_id}' for {vendor_name}. Stopping recursion.")
                                break
                    else:
                        logger.error(f"Post-search Level {level} batch processing did not return result for {vendor_name}. Stopping recursion.")
                        search_result_data[f"classification_l{level}"] = {
                             "classification_not_possible": True,
                             "classification_not_possible_reason": f"Missing result from L{level} post-search batch",
                             "confidence": 0.0, "vendor_name": vendor_name, "notes": f"L{level} Error"
                        }
                        break

                except Exception as recursive_err:
                    logger.error(f"search_and_classify_recursively: Error during post-search Level {level} for {vendor_name}", exc_info=True)
                    search_result_data[f"classification_l{level}"] = {
                         "classification_not_possible": True,
                         "classification_not_possible_reason": f"L{level} processing error: {str(recursive_err)[:100]}",
                         "confidence": 0.0, "vendor_name": vendor_name, "notes": f"L{level} Error"
                    }
                    break # Stop recursion on error
        else:
            logger.info(f"search_and_classify_recursively: L1 classification failed or not possible for {vendor_name}, skipping L2-L5.")

        logger.info(f"search_and_classify_recursively: Finished for vendor", extra={"vendor": vendor_name})
        return search_result_data


def create_batches(items: List[Any], batch_size: int) -> List[List[Any]]:
    """Create batches from a list of items."""
    if not items: return []
    if not isinstance(items, list):
        logger.warning(f"create_batches expected a list, got {type(items)}. Returning empty list.")
        return []
    if batch_size <= 0:
        logger.warning(f"Invalid batch_size {batch_size}, using default 5.")
        batch_size = settings.BATCH_SIZE # Use setting or a fixed default
    return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]


def group_by_parent_category(
    results: Dict[str, Dict],
    parent_level: int,
    vendors_to_group_names: List[str]
) -> Dict[Optional[str], List[str]]:
    """
    Group a specific list of vendor names based on their classification result at the parent_level.
    Only includes vendors that were successfully classified with a valid ID at the parent level.
    Returns a dictionary mapping parent category ID to a list of vendor *names*.
    """
    grouped: Dict[Optional[str], List[str]] = {}
    parent_key = f"level{parent_level}"
    logger.debug(f"group_by_parent_category: Grouping {len(vendors_to_group_names)} vendors based on results from '{parent_key}'.")

    grouped_count = 0
    excluded_count = 0

    for vendor_name in vendors_to_group_names:
        vendor_results = results.get(vendor_name)
        level_result = vendor_results.get(parent_key) if vendor_results else None

        if level_result and isinstance(level_result, dict) and not level_result.get("classification_not_possible", True):
            category_id = level_result.get("category_id")
            if category_id and category_id not in ["N/A", "ERROR"]:
                if category_id not in grouped:
                    grouped[category_id] = []
                grouped[category_id].append(vendor_name)
                grouped_count += 1
            else:
                logger.debug(f"  Excluding vendor '{vendor_name}': classified at '{parent_key}' but has invalid category_id '{category_id}'.")
                excluded_count += 1
        else:
            reason = "Not processed"
            if level_result and isinstance(level_result, dict):
                reason = level_result.get('classification_not_possible_reason', 'Marked not possible')
            elif not level_result:
                 reason = f"No result found for {parent_key}"
            logger.debug(f"  Excluding vendor '{vendor_name}': not successfully classified at '{parent_key}'. Reason: {reason}.")
            excluded_count += 1

    logger.info(f"group_by_parent_category: Finished grouping. Created {len(grouped)} groups, included {grouped_count} vendors, excluded {excluded_count} vendors.")
    return grouped