
# app/tasks/classification_tasks.py
import os
import asyncio
import logging
from datetime import datetime
from celery import shared_task
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, Any # <<< ADDED IMPORTS

from core.database import SessionLocal
from core.config import settings
from core.logging_config import get_logger
# Import context functions from the new module
from core.log_context import set_correlation_id, set_job_id, set_log_context, clear_all_context
# Import log helpers from utils
from utils.log_utils import LogTimer, log_duration

from models.job import Job, JobStatus, ProcessingStage
from services.file_service import read_vendor_file, normalize_vendor_data, generate_output_file
from services.llm_service import LLMService
from services.search_service import SearchService
from utils.taxonomy_loader import load_taxonomy

# Import the refactored logic
from .classification_logic import process_vendors

# Configure logger
logger = get_logger("vendor_classification.tasks")
# --- ADDED: Log confirmation ---
logger.debug("Successfully imported Dict and Any from typing for classification tasks.")
# --- END ADDED ---

@shared_task(bind=True)
def process_vendor_file(self, job_id: str, file_path: str):
    """
    Celery task entry point for processing a vendor file.
    Orchestrates the overall process by calling the main async helper.

    Args:
        job_id: Job ID
        file_path: Path to vendor file
    """
    task_id = self.request.id if self.request and self.request.id else "UnknownTaskID"
    logger.info(f"***** process_vendor_file TASK RECEIVED *****",
                extra={
                    "celery_task_id": task_id,
                    "job_id_arg": job_id,
                    "file_path_arg": file_path
                })

    set_correlation_id(job_id) # Set correlation ID early
    set_job_id(job_id)
    logger.info(f"Starting vendor file processing task (inside function)",
                extra={"job_id": job_id, "file_path": file_path})

    # Initialize loop within the task context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    logger.debug(f"Created and set new asyncio event loop for job {job_id}")

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
            return # Exit task if job doesn't exist

        logger.info(f"About to run async processing for job {job_id}")
        with LogTimer(logger, "Complete file processing", level=logging.INFO, include_in_stats=True):
            # Run the async function within the loop created for this task
            loop.run_until_complete(_process_vendor_file_async(job_id, file_path, db))

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
        logger.info(f"***** process_vendor_file TASK FINISHED *****", extra={"job_id": job_id})


async def _process_vendor_file_async(job_id: str, file_path: str, db: Session):
    """
    Asynchronous part of the vendor file processing.
    Sets up services, initializes stats, calls the core processing logic,
    and handles final result generation and job status updates.
    """
    logger.info(f"[_process_vendor_file_async] Starting async processing for job {job_id}")

    llm_service = LLMService()
    search_service = SearchService()

    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        logger.error(f"[_process_vendor_file_async] Job not found in database", extra={"job_id": job_id})
        return

    # --- Initialize stats (Updated for L5) ---
    start_time = datetime.now()
    # --- MODIFIED: Type hints added ---
    stats: Dict[str, Any] = {
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
    # --- END MODIFIED ---
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

        # --- MODIFIED: Type hints added ---
        results: Dict[str, Dict] = {vendor_name: {} for vendor_name in unique_vendors_map.keys()}
        # --- END MODIFIED ---

        logger.info(f"Starting vendor classification process by calling classification_logic.process_vendors")
        # --- Call the refactored logic ---
        await process_vendors(unique_vendors_map, taxonomy, results, stats, job, db, llm_service, search_service)
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
        try:
             logger.info(f"Generating output file")
             with log_duration(logger, "Generating output file"):
                 output_file_name = generate_output_file(normalized_vendors_data, results, job_id) # Can raise IOError
             logger.info(f"Output file generated", extra={"output_file": output_file_name})
        except Exception as gen_err:
             logger.error("Failed during output file generation", exc_info=True)
             job.fail(f"Failed to generate output file: {str(gen_err)}")
             db.commit()
             return # Stop processing

        # --- Finalize stats ---
        end_time = datetime.now()
        processing_duration = (end_time - datetime.fromisoformat(stats["start_time"])).total_seconds()
        stats["end_time"] = end_time.isoformat()
        stats["processing_duration_seconds"] = round(processing_duration, 2)
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
                           "successfully_classified_l5_total": stats.get("successfully_classified_l5", 0)
                       })
        except Exception as final_commit_err:
            logger.error("CRITICAL: Failed to commit final job completion status!", exc_info=True)
            db.rollback()
            try:
                err_msg = f"Failed during final commit: {type(final_commit_err).__name__}: {str(final_commit_err)}"
                job.fail(err_msg[:2000])
                db.commit()
            except Exception as fail_err:
                logger.error("CRITICAL: Also failed to mark job as failed after final commit error.", exc_info=fail_err)
                db.rollback()
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
        if job:
            if job.status not in [JobStatus.FAILED.value, JobStatus.COMPLETED.value]:
                 err_msg = f"Database error: {type(db_err).__name__}: {str(db_err)}"
                 job.fail(err_msg[:2000])
                 db.commit()
            else:
                 logger.warning(f"Database error occurred but job status was already {job.status}. Error: {db_err}")
                 db.rollback()
        else:
            logger.error("Job object was None during database error handling.")
    except Exception as async_err:
        logger.error(f"[_process_vendor_file_async] Unexpected error during async processing", exc_info=True,
                    extra={"error": str(async_err)})
        if job:
            if job.status not in [JobStatus.FAILED.value, JobStatus.COMPLETED.value]:
                err_msg = f"Unexpected error: {type(async_err).__name__}: {str(async_err)}"
                job.fail(err_msg[:2000])
                db.commit()
            else:
                logger.warning(f"Unexpected error occurred but job status was already {job.status}. Error: {async_err}")
                db.rollback()
        else:
            logger.error("Job object was None during unexpected error handling.")
    finally:
        logger.info(f"[_process_vendor_file_async] Finished async processing for job {job_id}")