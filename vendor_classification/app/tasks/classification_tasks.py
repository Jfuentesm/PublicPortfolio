# <file path='app/tasks/classification_tasks.py'>
# app/tasks/classification_tasks.py
import os
import asyncio
import logging
from datetime import datetime, timezone # <<< Added timezone
from celery import shared_task
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, Any, List, Optional # <<< ADDED List, Optional

from core.database import SessionLocal
from core.config import settings
from core.logging_config import get_logger
# Import context functions from the new module
from core.log_context import set_correlation_id, set_job_id, set_log_context, clear_all_context
# Import log helpers from utils
from utils.log_utils import LogTimer, log_duration

from models.job import Job, JobStatus, ProcessingStage, JobType # <<< ADDED JobType
from services.file_service import read_vendor_file, normalize_vendor_data, generate_output_file
from services.llm_service import LLMService
from services.search_service import SearchService
from utils.taxonomy_loader import load_taxonomy

# Import the refactored logic
from .classification_logic import process_vendors
# Import the schema for type hinting
from schemas.job import JobResultItem
# Import review schemas/logic if needed (likely handled by separate task)
from schemas.review import ReviewResultItem


# Configure logger
logger = get_logger("vendor_classification.tasks")
# --- ADDED: Log confirmation ---
logger.debug("Successfully imported Dict and Any from typing for classification tasks.")
# --- END ADDED ---


# --- UPDATED: Helper function to process results for DB storage ---
def _prepare_detailed_results_for_storage(
    results_dict: Dict[str, Dict],
    target_level: int # Keep target_level for reference if needed, but we store all levels now
) -> List[Dict[str, Any]]:
    """
    Processes the complex results dictionary (containing level1, level2... sub-dicts)
    into a flat list of dictionaries, where each dictionary represents a vendor
    and contains fields for all L1-L5 classifications, plus final status details.
    Matches the JobResultItem schema.
    THIS IS FOR **CLASSIFICATION** JOBS. Review jobs store results differently.
    """
    processed_list = []
    logger.info(f"Preparing detailed results for CLASSIFICATION job storage. Processing {len(results_dict)} vendors.")

    for vendor_name, vendor_results in results_dict.items():
        # Initialize the flat structure for this vendor
        flat_result: Dict[str, Any] = {
            "vendor_name": vendor_name,
            "level1_id": None, "level1_name": None,
            "level2_id": None, "level2_name": None,
            "level3_id": None, "level3_name": None,
            "level4_id": None, "level4_name": None,
            "level5_id": None, "level5_name": None,
            "final_confidence": None,
            "final_status": "Not Possible", # Default status
            "classification_source": "Initial", # Default source
            "classification_notes_or_reason": None,
            "achieved_level": 0 # Default achieved level
        }

        deepest_successful_level = 0
        final_level_data = None
        final_source = "Initial" # Track the source of the final decision point
        final_notes_or_reason = None

        # Iterate through levels 1 to 5 to populate the flat structure
        for level in range(1, 6):
            level_key = f"level{level}"
            level_data = vendor_results.get(level_key)

            if level_data and isinstance(level_data, dict):
                # Populate the corresponding fields in flat_result
                flat_result[f"level{level}_id"] = level_data.get("category_id")
                flat_result[f"level{level}_name"] = level_data.get("category_name")

                # Track the deepest successful classification
                if not level_data.get("classification_not_possible", True):
                    deepest_successful_level = level
                    final_level_data = level_data # Store data of the deepest successful level
                    # Update source based on the source recorded *at that level*
                    final_source = level_data.get("classification_source", final_source)
                    final_notes_or_reason = level_data.get("notes") # Get notes from successful level
                elif deepest_successful_level == 0: # If no level succeeded yet, track potential failure reasons/notes from L1
                    if level == 1:
                        final_notes_or_reason = level_data.get("classification_not_possible_reason") or level_data.get("notes")
                        # Update source based on L1 source if it exists
                        final_source = level_data.get("classification_source", final_source)

            # If a level wasn't processed (e.g., stopped early), its fields remain None

        # Determine final status, confidence, and notes based on the deepest successful level
        if final_level_data:
            flat_result["final_status"] = "Classified"
            flat_result["final_confidence"] = final_level_data.get("confidence")
            flat_result["achieved_level"] = deepest_successful_level
            flat_result["classification_notes_or_reason"] = final_notes_or_reason # Use notes from final level
        else:
            # No level was successfully classified
            flat_result["final_status"] = "Not Possible"
            flat_result["final_confidence"] = 0.0
            flat_result["achieved_level"] = 0
            # Use the reason/notes captured from L1 failure or search failure
            flat_result["classification_notes_or_reason"] = final_notes_or_reason

        # Set the final determined source
        flat_result["classification_source"] = final_source

        # Handle potential ERROR states explicitly (e.g., if L1 failed with ERROR)
        l1_data = vendor_results.get("level1")
        if l1_data and l1_data.get("category_id") == "ERROR":
            flat_result["final_status"] = "Error"
            flat_result["classification_notes_or_reason"] = l1_data.get("classification_not_possible_reason") or "Processing error occurred"
            # Override source if error occurred
            final_source = l1_data.get("classification_source", "Initial")
            flat_result["classification_source"] = final_source


        # Validate against Pydantic model (optional, but good practice)
        try:
            JobResultItem.model_validate(flat_result)
            processed_list.append(flat_result)
        except Exception as validation_err:
            logger.error(f"Validation failed for prepared result of vendor '{vendor_name}'",
                         exc_info=True, extra={"result_data": flat_result})
            # Optionally append a placeholder error entry or skip
            # For now, let's skip invalid entries
            continue

    logger.info(f"Finished preparing {len(processed_list)} detailed result items for CLASSIFICATION job storage.")
    return processed_list
# --- END UPDATED ---


@shared_task(bind=True)
# --- UPDATED: Added target_level parameter ---
def process_vendor_file(self, job_id: str, file_path: str, target_level: int):
# --- END UPDATED ---
    """
    Celery task entry point for processing a vendor file (CLASSIFICATION job type).
    Orchestrates the overall process by calling the main async helper.

    Args:
        job_id: Job ID
        file_path: Path to vendor file
        target_level: The desired maximum classification level (1-5)
    """
    task_id = self.request.id if self.request and self.request.id else "UnknownTaskID"
    logger.info(f"***** process_vendor_file TASK RECEIVED (CLASSIFICATION) *****",
                extra={
                    "celery_task_id": task_id,
                    "job_id_arg": job_id,
                    "file_path_arg": file_path,
                    "target_level_arg": target_level # Log received target level
                })

    set_correlation_id(job_id) # Set correlation ID early
    set_job_id(job_id)
    set_log_context({"target_level": target_level, "job_type": JobType.CLASSIFICATION.value}) # Add target level and type to context
    logger.info(f"Starting vendor file processing task (inside function)",
                extra={"job_id": job_id, "file_path": file_path, "target_level": target_level})

    # Validate target_level
    if not 1 <= target_level <= 5:
        logger.error(f"Invalid target_level received: {target_level}. Must be between 1 and 5.")
        # Fail the job immediately if level is invalid
        db_fail = SessionLocal()
        try:
            job_fail = db_fail.query(Job).filter(Job.id == job_id).first()
            if job_fail:
                job_fail.fail(f"Invalid target level specified: {target_level}. Must be 1-5.")
                db_fail.commit()
        except Exception as db_err:
            logger.error("Failed to mark job as failed due to invalid target level", exc_info=db_err)
            db_fail.rollback()
        finally:
            db_fail.close()
        clear_all_context() # Clear context before returning
        return # Stop task execution

    # Initialize loop within the task context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    logger.debug(f"Created and set new asyncio event loop for job {job_id}")

    db = SessionLocal()
    job = None # Initialize job to None

    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            # Verify the target level matches the job record (optional sanity check)
            if job.target_level != target_level:
                logger.warning(f"Task received target_level {target_level} but job record has {job.target_level}. Using task value: {target_level}.")
                # Optionally update job record here if desired, or just proceed with task value

            # Ensure job type is CLASSIFICATION
            if job.job_type != JobType.CLASSIFICATION.value:
                 logger.error(f"process_vendor_file task called for a non-CLASSIFICATION job.", extra={"job_id": job_id, "job_type": job.job_type})
                 raise ValueError(f"Job {job_id} is not a CLASSIFICATION job.")


            set_log_context({
                "company_name": job.company_name,
                "creator": job.created_by,
                "file_name": job.input_file_name
                # target_level and job_type already set above
            })
            logger.info(f"Processing file for company",
                        extra={"company": job.company_name})
        else:
            logger.error("Job not found in database at start of task!", extra={"job_id": job_id})
            loop.close() # Close loop if job not found
            db.close() # Close db session
            clear_all_context() # Clear context before returning
            return # Exit task if job doesn't exist

        logger.info(f"About to run async processing for job {job_id}")
        with LogTimer(logger, "Complete file processing", level=logging.INFO, include_in_stats=True):
            # Run the async function within the loop created for this task
            # --- UPDATED: Pass target_level to async helper ---
            loop.run_until_complete(_process_vendor_file_async(job_id, file_path, db, target_level))
            # --- END UPDATED ---

        logger.info(f"Vendor file processing completed successfully (async part finished)")

    except Exception as e:
        logger.error(f"Error processing vendor file task (in main try block)", exc_info=True, extra={"job_id": job_id})
        try:
            # Re-query the job within this exception handler if it wasn't fetched initially or became None
            db_error_session = SessionLocal()
            try:
                job_in_error = db_error_session.query(Job).filter(Job.id == job_id).first()
                if job_in_error:
                    if job_in_error.status != JobStatus.COMPLETED.value:
                        err_msg = f"Task failed: {type(e).__name__}: {str(e)}"
                        job_in_error.fail(err_msg[:2000]) # Limit error message length
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
        if loop and not loop.is_closed():
            loop.close()
            logger.debug(f"Event loop closed for task.")
        clear_all_context()
        logger.info(f"***** process_vendor_file TASK FINISHED (CLASSIFICATION) *****", extra={"job_id": job_id})


# --- UPDATED: Added target_level parameter ---
async def _process_vendor_file_async(job_id: str, file_path: str, db: Session, target_level: int):
# --- END UPDATED ---
    """
    Asynchronous part of the vendor file processing (CLASSIFICATION job type).
    Sets up services, initializes stats, calls the core processing logic,
    and handles final result generation and job status updates.
    """
    logger.info(f"[_process_vendor_file_async] Starting async processing for job {job_id} to target level {target_level}")

    llm_service = LLMService()
    search_service = SearchService()

    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        logger.error(f"[_process_vendor_file_async] Job not found in database", extra={"job_id": job_id})
        return

    # --- Initialize stats (Updated for L5) ---
    start_time = datetime.now(timezone.utc) # Use timezone aware now
    # --- MODIFIED: Type hints added ---
    stats: Dict[str, Any] = {
        "job_id": job.id,
        "company_name": job.company_name,
        "target_level": target_level, # Store target level in stats
        "start_time": start_time.isoformat(),
        "end_time": None,
        "processing_duration_seconds": None,
        "total_vendors": 0,
        "unique_vendors": 0,
        "successfully_classified_l4": 0, # Keep L4 count for reference
        "successfully_classified_l5": 0, # Count successful classifications reaching L5 (if target >= 5)
        "classification_not_possible_initial": 0, # Count initially unclassifiable before search
        "invalid_category_errors": 0, # Track validation errors
        "search_attempts": 0, # Count how many vendors needed search
        "search_successful_classifications_l1": 0, # Count successful L1 classifications *after* search
        "search_successful_classifications_l5": 0, # Count successful L5 classifications *after* search (if target >= 5)
        "api_usage": {
            "openrouter_calls": 0,
            "openrouter_prompt_tokens": 0,
            "openrouter_completion_tokens": 0,
            "openrouter_total_tokens": 0,
            "tavily_search_calls": 0,
            "cost_estimate_usd": 0.0
        }
    }
    # --- END MODIFIED ---
    # --- End Initialize stats ---

    # --- Initialize results dictionary ---
    # This will be populated by process_vendors
    results_dict: Dict[str, Dict] = {}
    # --- UPDATED: This will hold the processed results for DB storage (List[JobResultItem]) ---
    detailed_results_for_db: Optional[List[Dict[str, Any]]] = None
    # --- END UPDATED ---
    # --- End Initialize results dictionary ---

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
        # --- MODIFIED: Type hints added ---
        unique_vendors_map: Dict[str, Dict[str, Any]] = {}
        # --- END MODIFIED ---
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

        # Initialize the results dict structure before passing to process_vendors
        results_dict = {vendor_name: {} for vendor_name in unique_vendors_map.keys()}

        logger.info(f"Starting vendor classification process by calling classification_logic.process_vendors up to Level {target_level}")
        # --- Call the refactored logic, passing target_level ---
        # process_vendors will populate the results_dict in place
        await process_vendors(
            unique_vendors_map=unique_vendors_map,
            taxonomy=taxonomy,
            results=results_dict, # Pass the dict to be populated
            stats=stats,
            job=job,
            db=db,
            llm_service=llm_service,
            search_service=search_service,
            target_level=target_level # Pass the target level
        )
        # --- End call to refactored logic ---
        logger.info(f"Vendor classification process completed (returned from classification_logic.process_vendors)")

        logger.info("Starting result generation phase.")

        job.current_stage = ProcessingStage.RESULT_GENERATION.value
        job.progress = 0.98 # Progress after all classification/search
        logger.info(f"[_process_vendor_file_async] Committing status update before result generation: {job.status}, {job.current_stage}, {job.progress}")
        db.commit()
        logger.info(f"Job status updated",
                    extra={"stage": job.current_stage, "progress": job.progress})

        output_file_name = None # Initialize

        # --- Process results for DB Storage ---
        try:
            logger.info("Processing detailed results for database storage.")
            with log_duration(logger, "Processing detailed results"):
                 # --- UPDATED: Call the preparation function ---
                 detailed_results_for_db = _prepare_detailed_results_for_storage(results_dict, target_level)
                 # --- END UPDATED ---
            logger.info(f"Processed {len(detailed_results_for_db)} items for detailed results storage.")
        except Exception as proc_err:
            logger.error("Failed during detailed results processing for DB", exc_info=True)
            # Continue to generate Excel, but log the error. The job won't store detailed results.
            detailed_results_for_db = None # Ensure it's None if processing failed
        # --- End Process results for DB Storage ---

        # --- Generate Excel File ---
        if detailed_results_for_db is not None: # Only generate if DB results were processed successfully
            try:
                    logger.info(f"Generating output file")
                    with log_duration(logger, "Generating output file"):
                        # --- UPDATED: Call generate_output_file with List[JobResultItem] ---
                        # Pass original vendor data as well for optional columns
                        output_file_name = generate_output_file(
                            job_id=job_id,
                            detailed_results=[JobResultItem.model_validate(item) for item in detailed_results_for_db],
                            # original_vendor_data=normalized_vendors_data # Pass original data if needed by generate_output_file
                        )
                        # --- END UPDATED ---
                    logger.info(f"Output file generated", extra={"output_file": output_file_name})
            except Exception as gen_err:
                    logger.error("Failed during output file generation", exc_info=True)
                    # Don't fail the whole job, just log and proceed without the file
                    output_file_name = None # Ensure filename is None if generation failed
                    # Optionally add a note to the job's error message or stats?
                    # For now, just log it. The job can still complete with DB results.
        else:
            logger.warning("Skipping output file generation because detailed results processing failed.")
            output_file_name = None
        # --- End Generate Excel File ---

        # --- Finalize stats ---
        end_time = datetime.now(timezone.utc) # Use timezone aware now
        processing_duration = (end_time - datetime.fromisoformat(stats["start_time"])).total_seconds()
        stats["end_time"] = end_time.isoformat()
        stats["processing_duration_seconds"] = round(processing_duration, 2)
        # Cost calculation remains the same
        cost_input_per_1k = 0.0005
        cost_output_per_1k = 0.0015
        estimated_cost = (stats["api_usage"]["openrouter_prompt_tokens"] / 1000) * cost_input_per_1k + \
                            (stats["api_usage"]["openrouter_completion_tokens"] / 1000) * cost_output_per_1k
        estimated_cost += (stats["api_usage"]["tavily_search_calls"] / 1000) * 4.0
        stats["api_usage"]["cost_estimate_usd"] = round(estimated_cost, 4)
        # --- End Finalize stats ---

        # --- Final Commit Block ---
        try:
            logger.info("Attempting final job completion update in database.")
            # --- UPDATED: Pass the processed detailed_results_for_db to the complete method ---
            job.complete(output_file_name, stats, detailed_results_for_db)
            # --- END UPDATED ---
            job.progress = 1.0 # Ensure progress is 1.0 on completion
            logger.info(f"[_process_vendor_file_async] Committing final job completion status.")
            db.commit()
            logger.info(f"Job completed successfully",
                        extra={
                            "processing_duration": processing_duration,
                            "output_file": output_file_name,
                            "target_level": target_level,
                            # --- UPDATED: Log if detailed results were stored ---
                            "detailed_results_stored": bool(detailed_results_for_db),
                            "detailed_results_count": len(detailed_results_for_db) if detailed_results_for_db else 0,
                            # --- END UPDATED ---
                            "openrouter_calls": stats["api_usage"]["openrouter_calls"],
                            "tokens_used": stats["api_usage"]["openrouter_total_tokens"],
                            "tavily_calls": stats["api_usage"]["tavily_search_calls"],
                            "estimated_cost": stats["api_usage"]["cost_estimate_usd"],
                            "invalid_category_errors": stats.get("invalid_category_errors", 0),
                            "successfully_classified_l5_total": stats.get("successfully_classified_l5", 0)
                        })
        except Exception as final_commit_err:
            logger.error("CRITICAL: Failed to commit final job completion status!", exc_info=True)
            db.rollback()
            try:
                # Re-fetch job in new session to attempt marking as failed
                db_fail_final = SessionLocal()
                job_fail_final = db_fail_final.query(Job).filter(Job.id == job_id).first()
                if job_fail_final:
                    err_msg = f"Failed during final commit: {type(final_commit_err).__name__}: {str(final_commit_err)}"
                    job_fail_final.fail(err_msg[:2000])
                    db_fail_final.commit()
                else:
                    logger.error("Job not found when trying to mark as failed after final commit error.")
                db_fail_final.close()
            except Exception as fail_err:
                logger.error("CRITICAL: Also failed to mark job as failed after final commit error.", exc_info=fail_err)
                # db.rollback() # Already rolled back original session
        # --- End Final Commit Block ---

    except (ValueError, FileNotFoundError, IOError) as file_err:
        logger.error(f"[_process_vendor_file_async] File reading or writing error", exc_info=True,
                    extra={"error": str(file_err)})
        if job:
            err_msg = f"File processing error: {type(file_err).__name__}: {str(file_err)}"
            job.fail(err_msg[:2000])
            db.commit()
        else:
            logger.error("Job object was None during file error handling.")
    except SQLAlchemyError as db_err:
        logger.error(f"[_process_vendor_file_async] Database error during processing", exc_info=True,
                    extra={"error": str(db_err)})
        db.rollback() # Rollback on DB error
        if job:
            # Re-fetch job in new session to attempt marking as failed
            db_fail_db = SessionLocal()
            job_fail_db = db_fail_db.query(Job).filter(Job.id == job_id).first()
            if job_fail_db and job_fail_db.status not in [JobStatus.FAILED.value, JobStatus.COMPLETED.value]:
                    err_msg = f"Database error: {type(db_err).__name__}: {str(db_err)}"
                    job_fail_db.fail(err_msg[:2000])
                    db_fail_db.commit()
            elif job_fail_db:
                    logger.warning(f"Database error occurred but job status was already {job_fail_db.status}. Error: {db_err}")
            else:
                logger.error("Job not found when trying to mark as failed after database error.")
            db_fail_db.close()
        else:
            logger.error("Job object was None during database error handling.")
    except Exception as async_err:
        logger.error(f"[_process_vendor_file_async] Unexpected error during async processing", exc_info=True,
                    extra={"error": str(async_err)})
        db.rollback() # Rollback on unexpected error
        if job:
            # Re-fetch job in new session to attempt marking as failed
            db_fail_unexpected = SessionLocal()
            job_fail_unexpected = db_fail_unexpected.query(Job).filter(Job.id == job_id).first()
            if job_fail_unexpected and job_fail_unexpected.status not in [JobStatus.FAILED.value, JobStatus.COMPLETED.value]:
                err_msg = f"Unexpected error: {type(async_err).__name__}: {str(async_err)}"
                job_fail_unexpected.fail(err_msg[:2000])
                db_fail_unexpected.commit()
            elif job_fail_unexpected:
                logger.warning(f"Unexpected error occurred but job status was already {job_fail_unexpected.status}. Error: {async_err}")
            else:
                logger.error("Job not found when trying to mark as failed after unexpected error.")
            db_fail_unexpected.close()
        else:
            logger.error("Job object was None during unexpected error handling.")
    finally:
        logger.info(f"[_process_vendor_file_async] Finished async processing for job {job_id}")


# --- ADDED: Reclassification Task ---
@shared_task(bind=True)
def reclassify_flagged_vendors_task(self, review_job_id: str):
    """
    Celery task entry point for re-classifying flagged vendors (REVIEW job type).
    Orchestrates the reclassification process.

    Args:
        review_job_id: The ID of the REVIEW job.
    """
    task_id = self.request.id if self.request and self.request.id else "UnknownTaskID"
    logger.info(f"***** reclassify_flagged_vendors_task TASK RECEIVED *****",
                extra={"celery_task_id": task_id, "review_job_id": review_job_id})

    set_correlation_id(review_job_id) # Use review job ID as correlation ID
    set_job_id(review_job_id)
    set_log_context({"job_type": JobType.REVIEW.value})
    logger.info(f"Starting reclassification task", extra={"review_job_id": review_job_id})

    # Initialize loop within the task context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    logger.debug(f"Created and set new asyncio event loop for review job {review_job_id}")

    db = SessionLocal()
    review_job = None

    try:
        review_job = db.query(Job).filter(Job.id == review_job_id).first()
        if not review_job:
            logger.error("Review job not found in database at start of task!", extra={"review_job_id": review_job_id})
            raise ValueError("Review job not found.")

        # Ensure job type is REVIEW
        if review_job.job_type != JobType.REVIEW.value:
            logger.error(f"reclassify_flagged_vendors_task called for a non-REVIEW job.", extra={"review_job_id": review_job_id, "job_type": review_job.job_type})
            raise ValueError(f"Job {review_job_id} is not a REVIEW job.")

        set_log_context({
            "company_name": review_job.company_name,
            "creator": review_job.created_by,
            "parent_job_id": review_job.parent_job_id
        })
        logger.info(f"Processing review for company", extra={"company": review_job.company_name})

        # --- Call the async reclassification logic ---
        logger.info(f"About to run async reclassification processing for review job {review_job_id}")
        with LogTimer(logger, "Complete reclassification processing", level=logging.INFO, include_in_stats=True):
            loop.run_until_complete(_process_reclassification_async(review_job_id, db))

        logger.info(f"Reclassification processing completed successfully (async part finished)")

    except Exception as e:
        logger.error(f"Error processing reclassification task", exc_info=True, extra={"review_job_id": review_job_id})
        try:
            # Re-query the job within this exception handler
            db_error_session = SessionLocal()
            try:
                job_in_error = db_error_session.query(Job).filter(Job.id == review_job_id).first()
                if job_in_error:
                    if job_in_error.status != JobStatus.COMPLETED.value:
                        err_msg = f"Reclassification task failed: {type(e).__name__}: {str(e)}"
                        job_in_error.fail(err_msg[:2000])
                        db_error_session.commit()
                        logger.info(f"Review job status updated to failed due to task error", extra={"error": str(e)})
                    else:
                        logger.warning(f"Task error occurred after review job was marked completed, status not changed.", extra={"error": str(e)})
                else:
                    logger.error("Review job not found when trying to mark as failed.", extra={"review_job_id": review_job_id})
            except Exception as db_error:
                logger.error(f"Error updating review job status during task failure handling", exc_info=True,
                            extra={"original_error": str(e), "db_error": str(db_error)})
                db_error_session.rollback()
            finally:
                db_error_session.close()
        except Exception as final_db_error:
            logger.critical(f"CRITICAL: Failed even to handle database update in reclassification task error handler.", exc_info=final_db_error)

    finally:
        if db:
            db.close()
            logger.debug(f"Main database session closed for reclassification task.")
        if loop and not loop.is_closed():
            loop.close()
            logger.debug(f"Event loop closed for reclassification task.")
        clear_all_context()
        logger.info(f"***** reclassify_flagged_vendors_task TASK FINISHED *****", extra={"review_job_id": review_job_id})


async def _process_reclassification_async(review_job_id: str, db: Session):
    """
    Asynchronous part of the reclassification task.
    Sets up services, calls the core reclassification logic, stores results.
    """
    logger.info(f"[_process_reclassification_async] Starting async processing for review job {review_job_id}")

    llm_service = LLMService()
    # search_service is not needed for reclassification

    review_job = db.query(Job).filter(Job.id == review_job_id).first()
    if not review_job:
        logger.error(f"[_process_reclassification_async] Review job not found in database", extra={"review_job_id": review_job_id})
        return

    # Import the core logic function here to avoid circular imports at module level
    from .reclassification_logic import process_reclassification

    review_results_list = None
    final_stats = {}
    logic_error_message = None # Variable to store error message from logic

    try:
        review_job.status = JobStatus.PROCESSING.value
        review_job.current_stage = ProcessingStage.RECLASSIFICATION.value
        review_job.progress = 0.1 # Start progress
        logger.info(f"[_process_reclassification_async] Committing initial status update: {review_job.status}, {review_job.current_stage}, {review_job.progress}")
        db.commit()
        logger.info(f"Review job status updated",
                    extra={"status": review_job.status, "stage": review_job.current_stage, "progress": review_job.progress})

        # --- Call the reclassification logic ---
        # This function will handle fetching parent data, calling LLM, etc.
        review_results_list, final_stats = await process_reclassification(
            review_job=review_job,
            db=db,
            llm_service=llm_service
        )
        # --- End call ---

        # --- Check if the logic function reported an error in stats ---
        logic_error_message = final_stats.get("error_message")
        if logic_error_message:
            logger.error(f"Reclassification logic reported an error: {logic_error_message}")
            # Raise an exception to trigger the failure handling block below
            raise Exception(logic_error_message)
        # --- End Check ---

        logger.info(f"Reclassification logic completed. Processed {final_stats.get('total_items_processed', 0)} items.")
        review_job.progress = 0.95 # Mark logic as complete

        # --- Final Commit Block (Only if no error from logic) ---
        try:
            logger.info("Attempting final review job completion update in database.")
            # Pass None for output_file_name as review jobs don't generate one
            # Pass the potentially modified final_stats (e.g., with duration)
            review_job.complete(output_file_name=None, stats=final_stats, detailed_results=review_results_list)
            review_job.progress = 1.0
            logger.info(f"[_process_reclassification_async] Committing final review job completion status.")
            db.commit()
            logger.info(f"Review job completed successfully",
                        extra={
                            "processing_duration": final_stats.get("processing_duration_seconds"),
                            "items_processed": final_stats.get("total_items_processed"),
                            "successful": final_stats.get("successful_reclassifications"),
                            "failed": final_stats.get("failed_reclassifications"),
                            "openrouter_calls": final_stats.get("api_usage", {}).get("openrouter_calls"),
                            "tokens_used": final_stats.get("api_usage", {}).get("openrouter_total_tokens"),
                            "estimated_cost": final_stats.get("api_usage", {}).get("cost_estimate_usd")
                        })
        except Exception as final_commit_err:
            logger.error("CRITICAL: Failed to commit final review job completion status!", exc_info=True)
            db.rollback()
            # Attempt to mark as failed (similar logic as in main task handler)
            try:
                db_fail_final = SessionLocal()
                job_fail_final = db_fail_final.query(Job).filter(Job.id == review_job_id).first()
                if job_fail_final:
                    err_msg = f"Failed during final commit: {type(final_commit_err).__name__}: {str(final_commit_err)}"
                    job_fail_final.fail(err_msg[:2000])
                    db_fail_final.commit()
                db_fail_final.close()
            except Exception as fail_err:
                logger.error("CRITICAL: Also failed to mark review job as failed after final commit error.", exc_info=fail_err)
        # --- End Final Commit Block ---

    # --- UPDATED: Catch specific errors and the generic Exception (including the one raised above) ---
    except (ValueError, FileNotFoundError) as logic_err:
        logger.error(f"[_process_reclassification_async] Data or File error during reclassification logic", exc_info=True,
                    extra={"error": str(logic_err)})
        if review_job:
            err_msg = f"Reclassification data error: {type(logic_err).__name__}: {str(logic_err)}"
            review_job.fail(err_msg[:2000])
            db.commit()
    except SQLAlchemyError as db_err:
         logger.error(f"[_process_reclassification_async] Database error during reclassification processing", exc_info=True,
                     extra={"error": str(db_err)})
         db.rollback()
         # Attempt to mark as failed (similar logic as in main task handler)
         try:
            db_fail_db = SessionLocal()
            job_fail_db = db_fail_db.query(Job).filter(Job.id == review_job_id).first()
            if job_fail_db and job_fail_db.status not in [JobStatus.FAILED.value, JobStatus.COMPLETED.value]:
                 err_msg = f"Database error: {type(db_err).__name__}: {str(db_err)}"
                 job_fail_db.fail(err_msg[:2000])
                 db_fail_db.commit()
            db_fail_db.close()
         except Exception as fail_err:
            logger.error("CRITICAL: Also failed to mark review job as failed after database error.", exc_info=fail_err)

    except Exception as async_err:
        # This catches errors from process_reclassification or other unexpected errors
        logger.error(f"[_process_reclassification_async] Unexpected error during async reclassification processing", exc_info=True,
                    extra={"error": str(async_err)})
        db.rollback()
        # Attempt to mark as failed
        try:
            db_fail_unexpected = SessionLocal()
            job_fail_unexpected = db_fail_unexpected.query(Job).filter(Job.id == review_job_id).first()
            if job_fail_unexpected and job_fail_unexpected.status not in [JobStatus.FAILED.value, JobStatus.COMPLETED.value]:
                # Use the error message captured from logic_error_message if available, otherwise use the current exception
                err_to_report = logic_error_message if logic_error_message else f"Unexpected error: {type(async_err).__name__}: {str(async_err)}"
                job_fail_unexpected.fail(err_to_report[:2000])
                # Add the error message to stats as well before committing failure
                if job_fail_unexpected.stats:
                     job_fail_unexpected.stats['error_message'] = err_to_report[:2000]
                else:
                     job_fail_unexpected.stats = {'error_message': err_to_report[:2000]}
                db_fail_unexpected.commit()
            db_fail_unexpected.close()
        except Exception as fail_err:
            logger.error("CRITICAL: Also failed to mark review job as failed after unexpected error.", exc_info=fail_err)
    # --- END UPDATED ---
    finally:
        logger.info(f"[_process_reclassification_async] Finished async processing for review job {review_job_id}")

# --- END ADDED ---