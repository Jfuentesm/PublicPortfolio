
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
from models.job import Job, JobStatus, ProcessingStage
# --- MODIFIED IMPORT ---
# Import the specific level classes along with the main Taxonomy class
from models.taxonomy import Taxonomy, TaxonomyLevel1, TaxonomyLevel2, TaxonomyLevel3
# --- END MODIFIED IMPORT ---
from services.file_service import read_vendor_file, normalize_vendor_data, generate_output_file
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
        "invalid_category_errors": 0, # Track validation errors
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
            # --- MODIFIED: read_vendor_file now returns List[Dict] including optional fields ---
            vendors_data = read_vendor_file(file_path)
            # --- END MODIFIED ---
        logger.info(f"Vendor file read successfully",
                   extra={"vendor_count": len(vendors_data)})

        job.current_stage = ProcessingStage.NORMALIZATION.value
        job.progress = 0.2
        db.commit()
        logger.info(f"Job status updated",
                   extra={"stage": job.current_stage, "progress": job.progress})

        logger.info(f"Normalizing vendor data")
        with log_duration(logger, "Normalizing vendor data"):
            # --- MODIFIED: normalize_vendor_data now preserves optional fields ---
            normalized_vendors_data = normalize_vendor_data(vendors_data)
            # --- END MODIFIED ---
        logger.info(f"Vendor data normalized",
                   extra={"normalized_count": len(normalized_vendors_data)})

        logger.info(f"Identifying unique vendors")
        # --- MODIFIED: Create unique vendor mapping storing the full dictionary ---
        unique_vendors_map: Dict[str, Dict[str, Any]] = {}
        for entry in normalized_vendors_data:
            name = entry.get('vendor_name')
            # Store the first occurrence's full data (including optional fields)
            if name and name not in unique_vendors_map:
                unique_vendors_map[name] = entry
        # --- END MODIFIED ---

        logger.info(f"Unique vendors identified",
                   extra={"unique_count": len(unique_vendors_map)})

        stats["total_vendors"] = len(normalized_vendors_data) # Count includes duplicates
        stats["unique_vendors"] = len(unique_vendors_map)

        logger.info(f"Loading taxonomy")
        with log_duration(logger, "Loading taxonomy"):
            taxonomy = load_taxonomy() # Can raise exceptions
        logger.info(f"Taxonomy loaded",
                   extra={"taxonomy_version": taxonomy.version})

        # --- MODIFIED: Initialize results based on unique map ---
        results: Dict[str, Dict] = {vendor_name: {} for vendor_name in unique_vendors_map.keys()}
        # --- END MODIFIED ---

        logger.info(f"Starting vendor classification process")
        # --- MODIFIED: Pass unique_vendors_map ---
        await process_vendors(unique_vendors_map, taxonomy, results, stats, job, db, llm_service, search_service)
        # --- END MODIFIED ---
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
            # --- MODIFIED: Pass the original (normalized) list of dicts ---
            # This list contains the optional fields needed for the output file
            output_file_name = generate_output_file(normalized_vendors_data, results, job_id) # Can raise IOError
            # --- END MODIFIED ---
        logger.info(f"Output file generated",
                   extra={"output_file": output_file_name})

        # --- Finalize stats ---
        end_time = datetime.now()
        processing_duration = (end_time - datetime.fromisoformat(stats["start_time"])).total_seconds()
        stats["end_time"] = end_time.isoformat()
        stats["processing_duration_seconds"] = round(processing_duration, 2)
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
                       "estimated_cost": stats["api_usage"]["cost_estimate_usd"],
                       "invalid_category_errors": stats.get("invalid_category_errors", 0)
                   })

    except (ValueError, FileNotFoundError, IOError) as file_err:
        logger.error(f"[_process_vendor_file_async] File reading or writing error", exc_info=True,
                    extra={"error": str(file_err)})
        # Ensure job object exists before trying to fail it
        if job:
            job.fail(f"File processing error: {str(file_err)}")
            db.commit()
        else:
            logger.error("Job object was None during file error handling.")
    except Exception as async_err:
        logger.error(f"[_process_vendor_file_async] Unexpected error during async processing", exc_info=True,
                    extra={"error": str(async_err)})
        # --- MODIFICATION: Ensure job status is updated even with unexpected errors ---
        # Ensure job object exists before trying to fail it
        if job:
            # Check if job status is already failed or completed to avoid overwriting
            if job.status not in [JobStatus.FAILED.value, JobStatus.COMPLETED.value]:
                job.fail(f"Unexpected error: {str(async_err)}")
                db.commit()
            else:
                logger.warning(f"Unexpected error occurred but job status was already {job.status}. Error: {async_err}")
                db.rollback() # Rollback potential partial changes if any happened before error
        else:
            logger.error("Job object was None during unexpected error handling.")
        # --- END MODIFICATION ---
        # Don't re-raise here, let the outer handler manage final logging/cleanup
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
    Process vendors through the classification workflow, including search for unknowns.
    Updates results and stats dictionaries in place. Passes full vendor data to batching/search.
    """
    unique_vendor_names = list(unique_vendors_map.keys()) # Get names from map
    total_unique_vendors = len(unique_vendor_names)
    processed_count = 0 # Count unique vendors processed in batches

    logger.info(f"Starting classification loop for {total_unique_vendors} unique vendors.")

    # Classification Levels 1-4
    vendors_to_process_next_level_names = set(unique_vendor_names) # Start with all unique vendor names for Level 1

    for level in range(1, 5):
        if not vendors_to_process_next_level_names:
            logger.info(f"No vendors remaining to process for Level {level}. Skipping.")
            continue # Skip level if no vendors need processing

        current_vendors_for_this_level = list(vendors_to_process_next_level_names) # Copy names for processing this level
        vendors_successfully_classified_in_level_names = set() # Track vendors that pass this level

        job.current_stage = getattr(ProcessingStage, f"CLASSIFICATION_L{level}").value
        job.progress = min(0.85, 0.2 + (level * 0.15)) # Approximate progress start for this level
        db.commit()
        logger.info(f"===== Starting Level {level} Classification =====",
                   extra={ "vendors_to_process": len(current_vendors_for_this_level) })

        # Group vendors for the current level
        if level == 1:
            # For Level 1, all vendors are processed without a parent
            grouped_vendors_names = { None: current_vendors_for_this_level }
            logger.info(f"Level 1: Processing all {len(current_vendors_for_this_level)} vendors.")
        else:
            # Group names based on VALID results from the *previous* level
            logger.info(f"Level {level}: Grouping {len(current_vendors_for_this_level)} vendors based on Level {level-1} results.")
            grouped_vendors_names = group_by_parent_category(results, level - 1, current_vendors_for_this_level)
            logger.info(f"Level {level}: Created {len(grouped_vendors_names)} groups for processing.")
            # Log group sizes for debugging
            for parent_id, names in grouped_vendors_names.items():
                 logger.debug(f"  Group Parent ID '{parent_id}': {len(names)} vendors")


        processed_in_level_count = 0
        # --- Process batches for each group (or the single L1 group) ---
        for parent_category_id, group_vendor_names in grouped_vendors_names.items():
            if not group_vendor_names:
                logger.debug(f"Skipping empty group for parent '{parent_category_id}' at Level {level}.")
                continue

            logger.info(f"Processing Level {level} group",
                       extra={"parent_category_id": parent_category_id, "vendor_count": len(group_vendor_names)})

            # --- MODIFIED: Create batches of vendor *data* using the map ---
            # Ensure we only get data for vendors relevant to this group and level
            group_vendor_data = [unique_vendors_map[name] for name in group_vendor_names if name in unique_vendors_map]
            level_batches_data = create_batches(group_vendor_data, batch_size=settings.BATCH_SIZE)
            logger.debug(f"Created {len(level_batches_data)} batches for group '{parent_category_id}' at Level {level}.")
            # --- END MODIFIED ---

            for i, batch_data in enumerate(level_batches_data):
                batch_names = [vd['vendor_name'] for vd in batch_data] # Get names for logging
                logger.info(f"Processing Level {level} batch {i+1}/{len(level_batches_data)} for parent '{parent_category_id or 'None'}'",
                           extra={"batch_size": len(batch_data), "first_vendor": batch_names[0] if batch_names else 'N/A'})
                try:
                    # --- MODIFIED: Pass batch_data (list of dicts) ---
                    batch_results = await process_batch(batch_data, level, parent_category_id, taxonomy, llm_service, stats)
                    # --- END MODIFIED ---

                    for vendor_name, classification in batch_results.items():
                        if vendor_name in results:
                            # Store the result for this level
                            results[vendor_name][f"level{level}"] = classification
                            processed_in_level_count += 1

                            # If classification was successful *and* valid, add to set for next level
                            if not classification.get("classification_not_possible", True):
                                vendors_successfully_classified_in_level_names.add(vendor_name)
                                logger.debug(f"Vendor '{vendor_name}' successfully classified at Level {level} (ID: {classification.get('category_id')}). Added for L{level+1}.")
                            else:
                                logger.debug(f"Vendor '{vendor_name}' not successfully classified at Level {level}. Reason: {classification.get('classification_not_possible_reason', 'Unknown')}. Will not proceed.")
                        else:
                             logger.warning(f"Vendor '{vendor_name}' from batch result not found in main results dictionary.", extra={"level": level})

                except Exception as batch_error:
                    logger.error(f"Error during batch processing logic (Level {level}, parent '{parent_category_id or 'None'}')", exc_info=True,
                                 extra={"batch_vendors": batch_names, "error": str(batch_error)})
                    # Mark vendors in failed batch as unclassified for this level (if error happened outside LLM call)
                    for vendor_name in batch_names:
                         if vendor_name in results:
                            # Avoid overwriting if already processed successfully by LLM before the error
                            if f"level{level}" not in results[vendor_name]:
                                results[vendor_name][f"level{level}"] = {
                                    "category_id": "ERROR", "category_name": "ERROR", "confidence": 0.0,
                                    "classification_not_possible": True,
                                    "classification_not_possible_reason": f"Batch processing logic error: {str(batch_error)[:100]}",
                                    "vendor_name": vendor_name
                                }
                            processed_in_level_count += 1 # Count as processed even if error occurred here
                         else:
                              logger.warning(f"Vendor '{vendor_name}' from failed batch not found in main results dictionary.", extra={"level": level})


                # Update overall progress slightly after each batch
                # Note: This progress calculation uses total unique vendors
                processed_count += len(batch_data) # This counts attempts, not just successes
                current_progress_fraction = processed_count / total_unique_vendors
                # Spread progress across levels 1-4 (approx 0.2 to 0.85 range)
                job.progress = min(0.85, 0.2 + (level * 0.15) + (0.15 * current_progress_fraction * (1/4) ) )
                # logger.debug(f"Updating progress after batch: {job.progress:.3f}") # Log progress updates
                try:
                    db.commit()
                except Exception as db_err:
                     logger.error("Failed to commit progress update during batch processing", exc_info=True)
                     db.rollback() # Rollback if commit fails

        logger.info(f"===== Level {level} Classification Completed =====")
        logger.info(f"  Processed {processed_in_level_count} vendor results at Level {level}.")
        logger.info(f"  {len(vendors_successfully_classified_in_level_names)} vendors successfully classified and validated at Level {level}, proceeding to L{level+1}.")

        # Prepare the set of vendor names for the *next* level's processing
        vendors_to_process_next_level_names = vendors_successfully_classified_in_level_names

    # --- End of Level Loop ---
    logger.info("===== Finished Hierarchical Classification Loop =====")

    # --- Identify initially unclassifiable vendors after all levels ---
    # A vendor is unclassifiable if L4 failed OR L4 was never reached due to failure at a higher level
    unknown_vendors_data_to_search = [] # Store full data dict
    successfully_classified_l4_count = 0
    for vendor_name in unique_vendor_names:
        is_classified_l4 = False
        if vendor_name in results:
            l4_result = results[vendor_name].get("level4")
            if l4_result and not l4_result.get("classification_not_possible", False):
                 is_classified_l4 = True # Successfully classified at L4
                 successfully_classified_l4_count += 1

        if not is_classified_l4:
            logger.debug(f"Vendor '{vendor_name}' did not reach/pass Level 4 classification. Adding to search list.")
            if vendor_name in unique_vendors_map:
                unknown_vendors_data_to_search.append(unique_vendors_map[vendor_name])
            else:
                logger.warning(f"Vendor '{vendor_name}' marked for search but not found in unique_vendors_map.")
                unknown_vendors_data_to_search.append({'vendor_name': vendor_name}) # Include at least the name

    stats["classification_not_possible_initial"] = len(unknown_vendors_data_to_search)
    # This initial stat is slightly misleading now, better calc post-search
    # stats["successfully_classified_initial"] = successfully_classified_l4_count
    stats["successfully_classified_l4"] = successfully_classified_l4_count # Add specific L4 stat

    logger.info(f"Initial Classification Summary: {successfully_classified_l4_count} reached L4, {stats['classification_not_possible_initial']} did not.")

    # --- Search for Unknown Vendors ---
    if unknown_vendors_data_to_search:
        job.current_stage = ProcessingStage.SEARCH.value
        job.progress = 0.85 # Progress after initial classification attempts
        db.commit()
        logger.info(f"===== Starting Search for {stats['classification_not_possible_initial']} Unclassified Vendors =====")

        stats["search_attempts"] = len(unknown_vendors_data_to_search)

        search_tasks = [
            search_vendor(vendor_data, taxonomy, llm_service, search_service, stats)
            for vendor_data in unknown_vendors_data_to_search
        ]
        logger.info(f"Gathering results for {len(search_tasks)} search tasks...")
        search_results_list = await asyncio.gather(*search_tasks, return_exceptions=True)
        logger.info(f"Search tasks completed.")

        successful_searches = 0
        for i, search_result_or_exc in enumerate(search_results_list):
             # Defensive: Ensure index is valid
             if i >= len(unknown_vendors_data_to_search):
                 logger.error(f"Search result index {i} out of bounds for unknown_vendors list.")
                 continue
             vendor_data = unknown_vendors_data_to_search[i] # Get the original data dict
             vendor_name = vendor_data.get('vendor_name', f'UnknownVendor_{i}') # Get name

             if vendor_name not in results: # Ensure vendor key exists
                 logger.warning(f"Vendor '{vendor_name}' from search task not found in main results dict. Initializing.")
                 results[vendor_name] = {}

             if isinstance(search_result_or_exc, Exception):
                 logger.error(f"Error searching for vendor {vendor_name}", exc_info=search_result_or_exc)
                 results[vendor_name]["search_results"] = {"error": str(search_result_or_exc)}
                 # Ensure classification reflects search failure
                 results[vendor_name]["search_results"]["classification"] = {
                     "classification_not_possible": True,
                     "classification_not_possible_reason": f"Search task error: {str(search_result_or_exc)[:100]}",
                     "confidence": 0.0,
                     "vendor_name": vendor_name # Add vendor name for consistency
                 }
             elif isinstance(search_result_or_exc, dict): # Check if it's a valid result dict
                 search_result = search_result_or_exc
                 results[vendor_name]["search_results"] = search_result

                 # Safely access classification data
                 classification_data = search_result.get("classification") # Safely get classification dict

                 if classification_data and isinstance(classification_data, dict) and not classification_data.get("classification_not_possible", True):
                     # Classification was successful via search
                     if classification_data.get("vendor_name") == vendor_name:
                         # Use search result as L1 only if hierarchical classification didn't provide a valid L1
                         if not results[vendor_name].get("level1") or results[vendor_name]["level1"].get("classification_not_possible", True):
                             results[vendor_name]["level1"] = classification_data # Overwrite/set L1
                             if "notes" not in results[vendor_name]["level1"]: results[vendor_name]["level1"]["notes"] = ""
                             results[vendor_name]["level1"]["notes"] = f"Classified via search: {results[vendor_name]['level1']['notes']}"
                             # Clear potentially failed L2-L4 classifications if L1 changed/set here
                             for lvl in range(2, 5):
                                 results[vendor_name].pop(f'level{lvl}', None)
                             successful_searches += 1
                             logger.info(f"Vendor '{vendor_name}' classified via search (Level 1).")
                         else:
                              logger.info(f"Vendor '{vendor_name}' already had valid L1 classification, search result not used to overwrite.")

                     else:
                         logger.warning(f"Search classification vendor mismatch for '{vendor_name}'. Classification: {classification_data.get('vendor_name')}")
                         # Handle mismatch - mark as failed search
                         if "classification" not in results[vendor_name]["search_results"]: results[vendor_name]["search_results"]["classification"] = {}
                         results[vendor_name]["search_results"]["classification"]["classification_not_possible"] = True
                         results[vendor_name]["search_results"]["classification"]["classification_not_possible_reason"] = "Search result vendor mismatch"
                         results[vendor_name]["search_results"]["classification"]["vendor_name"] = vendor_name # Ensure vendor name is present

                 else:
                     # Classification via search was not possible or classification data was missing/invalid
                     reason = "Search result invalid or missing classification data"
                     if classification_data and isinstance(classification_data, dict): # Check if the dict exists
                         reason = classification_data.get("classification_not_possible_reason", "Search did not yield classification")
                     logger.info(f"Vendor '{vendor_name}' could not be classified via search. Reason: {reason}")
                     # Ensure classification structure exists even if search failed
                     if "classification" not in results[vendor_name]["search_results"]: results[vendor_name]["search_results"]["classification"] = {}
                     results[vendor_name]["search_results"]["classification"]["classification_not_possible"] = True
                     results[vendor_name]["search_results"]["classification"]["classification_not_possible_reason"] = reason
                     results[vendor_name]["search_results"]["classification"]["confidence"] = 0.0
                     results[vendor_name]["search_results"]["classification"]["vendor_name"] = vendor_name

             else: # Handle unexpected return type from gather
                  logger.error(f"Unexpected result type for vendor {vendor_name} search task: {type(search_result_or_exc)}")
                  results[vendor_name]["search_results"] = {"error": f"Unexpected search result type: {type(search_result_or_exc)}"}
                  results[vendor_name]["search_results"]["classification"] = { "classification_not_possible": True, "classification_not_possible_reason": "Internal search error", "confidence": 0.0, "vendor_name": vendor_name }


        stats["search_successful_classifications"] = successful_searches
        logger.info(f"===== Unknown Vendor Search Completed =====")
        logger.info(f"  Attempted search for {stats['search_attempts']} vendors.")
        logger.info(f"  Successfully classified {successful_searches} additional vendors via search (Level 1).")
    else:
        logger.info("No unknown vendors required search.")


@log_function_call(logger, include_args=False) # Keep args=False
async def process_batch(
    batch_data: List[Dict[str, Any]], # Pass list of dicts including optional fields
    level: int,
    parent_category_id: Optional[str],
    taxonomy: Taxonomy,
    llm_service: LLMService,
    stats: Dict[str, Any]
) -> Dict[str, Dict]:
    """
    Process a batch of vendors for a specific classification level, including taxonomy validation.
    Updates stats dictionary in place. Passes full vendor data to LLM.
    Returns results for the batch.
    """
    results = {}
    if not batch_data:
        logger.warning(f"process_batch called with empty batch_data for Level {level}, Parent '{parent_category_id}'.")
        return results

    batch_names = [vd.get('vendor_name', f'Unknown_{i}') for i, vd in enumerate(batch_data)] # For logging

    logger.debug(f"process_batch: Preparing Level {level} batch.",
               extra={"batch_size": len(batch_data), "parent_category_id": parent_category_id})

    # --- Get valid category IDs for this level/parent ---
    valid_category_ids: Set[str] = set()
    category_id_lookup_error = False
    try:
        logger.debug(f"process_batch: Retrieving valid category IDs for Level {level}, Parent '{parent_category_id}'.")
        if level == 1:
            categories = taxonomy.get_level1_categories()
        elif parent_category_id:
            if level == 2:
                categories = taxonomy.get_level2_categories(parent_category_id)
            elif level == 3:
                categories = taxonomy.get_level3_categories(parent_category_id)
            elif level == 4:
                categories = taxonomy.get_level4_categories(parent_category_id)
            else:
                 categories = [] # Should not happen
        else:
             logger.error(f"process_batch: Parent category ID is required for Level {level} but was not provided.")
             categories = []

        valid_category_ids = {cat.id for cat in categories}

        if not valid_category_ids:
             # Distinguish between truly no children vs. error retrieving them
             if level > 1 and parent_category_id:
                 logger.warning(f"process_batch: No valid child categories found or retrieved for Level {level}, Parent '{parent_category_id}'. LLM cannot classify.")
                 # This case is handled by the prompt generation now, but log anyway.
             elif level == 1:
                 logger.error("process_batch: No Level 1 categories found in taxonomy!")
                 category_id_lookup_error = True # Major issue

        else:
             logger.debug(f"process_batch: Found {len(valid_category_ids)} valid IDs for Level {level}, Parent '{parent_category_id}'. Example: {list(valid_category_ids)[:5]}")

    except Exception as tax_err:
        logger.error(f"process_batch: Error getting valid categories from taxonomy", exc_info=True,
                     extra={"level": level, "parent_category_id": parent_category_id})
        valid_category_ids = set() # Disable validation if lookup fails
        category_id_lookup_error = True # Flag that we couldn't get categories


    # --- Call LLM ---
    llm_response_data = None
    try:
        with LogTimer(logger, f"LLM classification - Level {level}, Parent '{parent_category_id or 'None'}'", include_in_stats=True):
            # --- MODIFIED: Pass full batch_data dictionary list ---
            llm_response_data = await llm_service.classify_batch(batch_data, level, taxonomy, parent_category_id)
            # --- END MODIFIED ---

        # Update usage stats safely
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
             classifications = [] # Treat as empty if not a list

        logger.debug(f"process_batch: Received {len(classifications)} classifications from LLM for batch size {len(batch_data)} at Level {level}.")
        if llm_result.get("batch_id_mismatch"):
             logger.warning(f"process_batch: Processing batch despite batch_id mismatch warning from LLM service.")


        # --- Validate and process results, ensuring all vendors in batch are covered ---
        processed_vendors_in_response = set()
        for classification in classifications:
            # Basic validation of the classification structure itself
            if not isinstance(classification, dict):
                logger.warning("Invalid classification item format received from LLM (not a dict)", extra={"item": classification})
                continue

            vendor_name = classification.get("vendor_name")
            if not vendor_name:
                logger.warning("Classification received without vendor_name", extra={"classification": classification})
                continue

            target_vendor_name = vendor_name # Assuming LLM returns names exactly as sent for now
            processed_vendors_in_response.add(target_vendor_name)

            # Default values
            category_id = classification.get("category_id", "N/A")
            category_name = classification.get("category_name", "N/A")
            confidence = classification.get("confidence", 0.0)
            classification_not_possible = classification.get("classification_not_possible", False)
            reason = classification.get("classification_not_possible_reason") # Can be None
            notes = classification.get("notes") # Optional notes from LLM
            is_valid_category = True # Assume valid initially

            # --- TAXONOMY VALIDATION ---
            # Only validate if:
            # 1. Classification was attempted (not_possible is False)
            # 2. We successfully retrieved valid IDs for this level/parent (no lookup error)
            # 3. We actually have a list of valid IDs (not empty set)
            if not classification_not_possible and not category_id_lookup_error and valid_category_ids:
                if category_id not in valid_category_ids:
                    is_valid_category = False
                    logger.warning(f"Invalid category ID '{category_id}' returned by LLM for vendor '{target_vendor_name}' at level {level}, parent '{parent_category_id}'.",
                                   extra={"valid_ids": list(valid_category_ids)[:10]}) # Log sample IDs
                    # Invalidate the result
                    classification_not_possible = True
                    reason = f"Invalid category ID '{category_id}' returned by LLM (Valid examples: {list(valid_category_ids)[:3]})"
                    confidence = 0.0
                    category_id = "N/A" # Ensure ID is N/A if invalid
                    category_name = "N/A"
                    stats["invalid_category_errors"] = stats.get("invalid_category_errors", 0) + 1
                else:
                     logger.debug(f"Category ID '{category_id}' for '{target_vendor_name}' is valid for Level {level}, Parent '{parent_category_id}'.")
            elif not classification_not_possible and category_id_lookup_error:
                 logger.warning(f"Cannot validate category ID '{category_id}' for '{target_vendor_name}' due to earlier taxonomy lookup error.")
                 # Proceed cautiously - accept LLM result but maybe flag it? For now, accept.
            elif not classification_not_possible and not valid_category_ids and level > 1:
                 logger.warning(f"Cannot validate category ID '{category_id}' for '{target_vendor_name}' because no valid child categories were found for parent '{parent_category_id}'.")
                 # This implies the prompt might have been generated incorrectly, but LLM still returned something. Invalidate.
                 is_valid_category = False
                 classification_not_possible = True
                 reason = f"LLM returned category '{category_id}' but no valid children found for parent '{parent_category_id}'."
                 confidence = 0.0
                 category_id = "N/A"; category_name = "N/A"
                 stats["invalid_category_errors"] = stats.get("invalid_category_errors", 0) + 1


            # --- End TAXONOMY VALIDATION ---

            # Ensure consistency: if not possible, confidence must be 0
            if classification_not_possible and confidence > 0.0:
                logger.warning("Correcting confidence to 0.0 for classification_not_possible=true", extra={"vendor": target_vendor_name})
                confidence = 0.0
            # Ensure consistency: if possible (and category was valid), category should not be N/A
            if not classification_not_possible and is_valid_category and (category_id == "N/A" or not category_id):
                 logger.warning("Classification marked possible by LLM but category ID is 'N/A' or empty", extra={"vendor": target_vendor_name, "classification": classification})
                 classification_not_possible = True # Override LLM
                 reason = reason or "Missing category ID despite LLM success claim"
                 confidence = 0.0
                 category_id = "N/A"
                 category_name = "N/A" # Ensure name is also N/A


            results[target_vendor_name] = {
                "category_id": category_id,
                "category_name": category_name,
                "confidence": confidence,
                "classification_not_possible": classification_not_possible,
                "classification_not_possible_reason": reason,
                "notes": notes, # Include notes from LLM
                "vendor_name": target_vendor_name # Ensure vendor name is in the result dict
            }
            # logger.debug(f"Vendor classified (post-validation)", # Less verbose logging now
            #            extra={
            #                "vendor": target_vendor_name, "level": level,
            #                "category_id": category_id, "confidence": confidence,
            #                "classification_possible": not classification_not_possible,
            #                "is_valid_category": is_valid_category
            #            })

        # Check if any vendors from the input batch are missing in the response
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
        logger.error(f"Failed to process batch at Level {level}", exc_info=True,
                     extra={"batch_names": batch_names, "error": str(e)})
        # Mark all vendors in this batch as failed for this level
        for vendor_name in batch_names:
            results[vendor_name] = {
                "category_id": "ERROR", "category_name": "ERROR", "confidence": 0.0,
                "classification_not_possible": True,
                "classification_not_possible_reason": f"Batch processing error: {str(e)[:100]}",
                "notes": None,
                "vendor_name": vendor_name
            }
    return results


@log_function_call(logger, include_args=False) # Keep args=False
async def search_vendor(
    vendor_data: Dict[str, Any], # Pass full vendor dict including optional fields
    taxonomy: Taxonomy,
    llm_service: LLMService,
    search_service: SearchService,
    stats: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Search for vendor information and attempt classification using LLM.
    Updates stats dictionary in place. Includes L1 category validation.
    Returns search results possibly augmented with classification.
    """
    vendor_name = vendor_data.get('vendor_name', 'UnknownVendor') # Extract name
    logger.info(f"search_vendor: Starting search for vendor", extra={"vendor": vendor_name})
    search_result_data = {
        "vendor": vendor_name,
        "search_query": f"{vendor_name} company business type industry",
        "sources": [],
        "summary": None,
        "error": None,
        "classification": None
     }

    # --- Get valid L1 category IDs for validation ---
    valid_l1_category_ids: Set[str] = set(taxonomy.categories.keys())
    if not valid_l1_category_ids:
        logger.error("search_vendor: No L1 categories found in taxonomy for validation!")
    # ---

    try:
        with LogTimer(logger, f"Tavily search for '{vendor_name}'", include_in_stats=True):
            tavily_response = await search_service.search_vendor(vendor_name) # Search using name

        stats["api_usage"]["tavily_search_calls"] += 1
        search_result_data.update(tavily_response) # Update with actual search results or error from service

        source_count = len(search_result_data.get("sources", []))
        if search_result_data.get("error"):
            logger.warning(f"search_vendor: Search failed", extra={"vendor": vendor_name, "error": search_result_data["error"]})
            search_result_data["classification"] = {
                 "classification_not_possible": True,
                 "classification_not_possible_reason": f"Search error: {str(search_result_data['error'])[:100]}",
                 "confidence": 0.0, "vendor_name": vendor_name, "notes": None
            }
        else:
            logger.info(f"search_vendor: Search completed", extra={"vendor": vendor_name, "source_count": source_count, "summary_present": bool(search_result_data.get('summary'))})

        # Proceed to classification only if search was successful AND yielded sources or a summary
        search_content_available = search_result_data.get("sources") or search_result_data.get("summary")
        if not search_result_data.get("error") and search_content_available:
            logger.info(f"search_vendor: Classifying based on search results", extra={"vendor": vendor_name})
            llm_response = None
            try:
                with LogTimer(logger, f"LLM classification from search for '{vendor_name}'", include_in_stats=True):
                    # --- Pass full vendor_data dictionary ---
                    llm_response = await llm_service.process_search_results(vendor_data, search_result_data, taxonomy)

                # Update usage stats safely
                if llm_response and isinstance(llm_response.get("usage"), dict):
                    usage = llm_response["usage"]
                    stats["api_usage"]["openrouter_calls"] += 1
                    stats["api_usage"]["openrouter_prompt_tokens"] += usage.get("prompt_tokens", 0)
                    stats["api_usage"]["openrouter_completion_tokens"] += usage.get("completion_tokens", 0)
                    stats["api_usage"]["openrouter_total_tokens"] += usage.get("total_tokens", 0)
                    logger.debug(f"search_vendor: LLM API usage updated", extra=usage)
                else:
                     logger.warning("search_vendor: LLM response missing or has invalid usage data.")

                llm_result_classification = llm_response.get("result", {}) if llm_response else {}

                # Ensure vendor name is present
                if "vendor_name" not in llm_result_classification:
                    llm_result_classification["vendor_name"] = vendor_name

                # --- L1 Taxonomy Validation for Search Result ---
                classification_not_possible = llm_result_classification.get("classification_not_possible", True)
                category_id = llm_result_classification.get("category_id", "N/A")
                is_valid_category = True

                if not classification_not_possible and valid_l1_category_ids:
                    if category_id not in valid_l1_category_ids:
                        is_valid_category = False
                        logger.warning(f"Invalid L1 category ID '{category_id}' returned by LLM for searched vendor '{vendor_name}'.",
                                       extra={"valid_ids": list(valid_l1_category_ids)[:10]})
                        # Invalidate result
                        llm_result_classification["classification_not_possible"] = True
                        llm_result_classification["classification_not_possible_reason"] = f"Invalid L1 category ID '{category_id}' from search."
                        llm_result_classification["confidence"] = 0.0
                        llm_result_classification["category_id"] = "N/A"
                        llm_result_classification["category_name"] = "N/A"
                        stats["invalid_category_errors"] = stats.get("invalid_category_errors", 0) + 1
                    else:
                         logger.debug(f"Search Result Validation: Category ID '{category_id}' for '{vendor_name}' is valid L1.")

                # Final consistency check after potential validation change
                if llm_result_classification.get("classification_not_possible") and llm_result_classification.get("confidence", 0.0) > 0.0:
                     llm_result_classification["confidence"] = 0.0
                if not llm_result_classification.get("classification_not_possible") and not llm_result_classification.get("category_id", "N/A"):
                     llm_result_classification["classification_not_possible"] = True
                     llm_result_classification["classification_not_possible_reason"] = "Missing category ID despite LLM success claim"
                     llm_result_classification["confidence"] = 0.0
                     llm_result_classification["category_id"] = "N/A"
                     llm_result_classification["category_name"] = "N/A"


                search_result_data["classification"] = llm_result_classification # Store the potentially validated classification

                classification_possible_final = not search_result_data["classification"].get("classification_not_possible", True)

                if classification_possible_final:
                    logger.info(f"search_vendor: Successful classification from search",
                               extra={ "vendor": vendor_name, "category_id": category_id, "confidence": llm_result_classification.get("confidence", 0)})
                else:
                    logger.info(f"search_vendor: Classification from search not possible",
                               extra={ "vendor": vendor_name, "reason": search_result_data.get("classification", {}).get("classification_not_possible_reason", "unknown reason") })

            except Exception as llm_err:
                 logger.error(f"search_vendor: Error during LLM processing of search results for {vendor_name}", exc_info=True)
                 search_result_data["error"] = search_result_data.get("error") or f"LLM processing error after search: {str(llm_err)}"
                 search_result_data["classification"] = {
                     "classification_not_possible": True,
                     "classification_not_possible_reason": f"LLM processing error: {str(llm_err)[:100]}",
                     "confidence": 0.0, "vendor_name": vendor_name, "notes": None
                 }

        elif not search_result_data.get("error"): # Case: Search succeeded but found no usable content
            logger.warning(f"search_vendor: No usable search results (sources or summary) found for vendor, skipping classification attempt", extra={"vendor": vendor_name})
            search_result_data["classification"] = {
                 "classification_not_possible": True,
                 "classification_not_possible_reason": "No search results content found",
                 "confidence": 0.0, "vendor_name": vendor_name, "notes": None
            }

    except Exception as e:
        logger.error(f"search_vendor: Unexpected error during search_vendor for {vendor_name}", exc_info=True)
        search_result_data["error"] = f"Unexpected error in search task: {str(e)}"
        search_result_data["classification"] = {
             "classification_not_possible": True,
             "classification_not_possible_reason": f"Search task error: {str(e)[:100]}",
             "confidence": 0.0, "vendor_name": vendor_name, "notes": None
        }

    return search_result_data


def create_batches(items: List[Any], batch_size: int) -> List[List[Any]]:
    """Create batches from a list of items."""
    if not items: return [] # Handle empty list
    if not isinstance(items, list):
        logger.warning(f"create_batches expected a list, got {type(items)}. Returning empty list.")
        return []
    if batch_size <= 0:
        logger.warning(f"Invalid batch_size {batch_size}, using default 5.")
        batch_size = 5 # Default safeguard
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

        # Check if the result exists, is valid, and classification was possible
        if level_result and isinstance(level_result, dict) and not level_result.get("classification_not_possible", True):
            category_id = level_result.get("category_id")
            # Ensure category_id is valid (not None, not "N/A", not "ERROR")
            if category_id and category_id not in ["N/A", "ERROR"]:
                if category_id not in grouped:
                    grouped[category_id] = []
                grouped[category_id].append(vendor_name) # Store name
                grouped_count += 1
                # logger.debug(f"  Vendor '{vendor_name}' added to group '{category_id}'.") # Verbose
            else:
                # Vendor was 'successfully' classified by LLM but got an invalid ID
                logger.debug(f"  Excluding vendor '{vendor_name}': classified at '{parent_key}' but has invalid category_id '{category_id}'.")
                excluded_count += 1
        else:
            # Vendor not processed, not classifiable, or had error at parent level
            reason = "Not processed"
            if level_result and isinstance(level_result, dict):
                reason = level_result.get('classification_not_possible_reason', 'Marked not possible')
            elif not level_result:
                 reason = f"No result found for {parent_key}"

            logger.debug(f"  Excluding vendor '{vendor_name}': not successfully classified at '{parent_key}'. Reason: {reason}.")
            excluded_count += 1

    logger.info(f"group_by_parent_category: Finished grouping. Created {len(grouped)} groups, included {grouped_count} vendors, excluded {excluded_count} vendors.")
    return grouped