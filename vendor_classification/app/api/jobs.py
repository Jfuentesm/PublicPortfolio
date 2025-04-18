# <file path='app/api/jobs.py'>
# app/api/jobs.py
from fastapi import APIRouter, Depends, HTTPException, Query, status, Path # Added Path
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Union, Any # <<< ADDED Union, Any
from datetime import datetime, timezone # <<< ADDED timezone
import logging # Import logging
import uuid # <<< ADDED for generating review job IDs
import os # <<< ADDED for path joining

from core.database import get_db
from api.auth import get_current_user
from models.user import User
# --- CORRECTED IMPORT: Add ProcessingStage ---
from models.job import Job, JobStatus, JobType, ProcessingStage
# --- END CORRECTED IMPORT ---
# --- UPDATED: Import specific schemas ---
from schemas.job import JobResponse, JobResultItem, JobResultsResponse
from schemas.review import ReclassifyPayload, ReclassifyResponse, ReviewResultItem # <<< ADDED Review Schemas
# --- END UPDATED ---
from core.logging_config import get_logger
from core.log_context import set_log_context
from core.config import settings # Need settings for file path construction
# --- CORRECTED IMPORT PATH ---
from tasks.classification_tasks import reclassify_flagged_vendors_task
# --- END CORRECTED IMPORT PATH ---
# --- ADDED: Import file service for merge ---
from services.file_service import generate_output_file
# --- END ADDED ---


logger = get_logger("vendor_classification.api.jobs")
logger.debug("Successfully imported Dict from typing for jobs API.")

router = APIRouter()

@router.get("/", response_model=List[JobResponse])
async def list_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status_filter: Optional[JobStatus] = Query(None, alias="status", description="Filter jobs by status"),
    start_date: Optional[datetime] = Query(None, description="Filter jobs created on or after this date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="Filter jobs created on or before this date (ISO format)"),
    job_type_filter: Optional[JobType] = Query(None, alias="type", description="Filter jobs by type (CLASSIFICATION or REVIEW)"), # <<< ADDED Filter
    skip: int = Query(0, ge=0, description="Number of jobs to skip for pagination"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of jobs to return"),
):
    """
    List jobs. Superusers see all jobs, regular users see only their own.
    Supports filtering by status, date range, type, and pagination.
    """
    set_log_context({"username": current_user.username, "is_superuser": current_user.is_superuser}) # Log superuser status
    logger.info("Fetching job history", extra={
        "status_filter": status_filter,
        "job_type_filter": job_type_filter, # <<< ADDED Log
        "start_date": start_date.isoformat() if start_date else None,
        "end_date": end_date.isoformat() if end_date else None,
        "skip": skip,
        "limit": limit,
    })

    query = db.query(Job)

    # --- MODIFIED: Filter by user ONLY if not superuser ---
    if not current_user.is_superuser:
        logger.debug("Applying user filter for non-superuser.")
        query = query.filter(Job.created_by == current_user.username)
    else:
        logger.debug("Skipping user filter for superuser.")
    # --- END MODIFIED ---

    # Apply filters
    if status_filter:
        query = query.filter(Job.status == status_filter.value)
    if job_type_filter: # <<< ADDED Filter
        query = query.filter(Job.job_type == job_type_filter.value)
    if start_date:
        query = query.filter(Job.created_at >= start_date)
    if end_date:
        # Add a day to end_date to make it inclusive of the whole day if time is not specified
        # Or adjust based on desired behavior (e.g., end_date < end_date + timedelta(days=1))
        query = query.filter(Job.created_at <= end_date)

    # Order by creation date (newest first)
    query = query.order_by(Job.created_at.desc())

    # Apply pagination
    jobs = query.offset(skip).limit(limit).all()

    logger.info(f"Retrieved {len(jobs)} jobs from history.")

    # Convert Job models to JobResponse schemas
    # Pydantic v2 handles this automatically with from_attributes=True
    return jobs

@router.get("/{job_id}", response_model=JobResponse)
async def read_job(
    # Use Path to ensure job_id is correctly extracted from the URL path
    job_id: str = Path(..., title="The ID of the job to get"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve details for a specific job by its ID.
    Ensures the current user owns the job or is an admin.
    """
    set_log_context({"username": current_user.username, "target_job_id": job_id, "is_superuser": current_user.is_superuser})
    logger.info(f"Fetching details for job ID: {job_id}")

    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        logger.warning(f"Job not found", extra={"job_id": job_id})
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    # --- MODIFIED: Authorization Check (Allow Superusers) ---
    if not current_user.is_superuser and job.created_by != current_user.username:
        logger.warning(f"Authorization failed: User '{current_user.username}' attempted to access job '{job_id}' owned by '{job.created_by}'")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this job")
    # --- END MODIFIED ---

    # LOGGING: Log the job details being returned, especially target_level and job_type
    logger.info(f"Returning details for job ID: {job_id}", extra={"job_status": job.status, "target_level": job.target_level, "job_type": job.job_type})
    return job # Pydantic will validate against JobResponse

# Use Dict for flexibility, or create a specific StatsResponse schema later if needed
@router.get("/{job_id}/stats", response_model=Dict)
async def read_job_stats(
    job_id: str = Path(..., title="The ID of the job to get stats for"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve processing statistics for a specific job.
    Ensures the current user owns the job or is an admin.
    For REVIEW jobs, this might contain the input hints and merge status.
    """
    set_log_context({"username": current_user.username, "target_job_id": job_id, "is_superuser": current_user.is_superuser})
    logger.info(f"Fetching statistics for job ID: {job_id}")

    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        logger.warning(f"Job not found for stats", extra={"job_id": job_id})
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    # --- MODIFIED: Authorization Check (Allow Superusers) ---
    if not current_user.is_superuser and job.created_by != current_user.username:
        logger.warning(f"Authorization failed: User '{current_user.username}' attempted to access stats for job '{job_id}' owned by '{job.created_by}'")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access stats for this job")
    # --- END MODIFIED ---

    # LOGGING: Log the raw stats being returned from the database
    logger.info(f"Returning statistics for job ID: {job_id}", extra={"job_type": job.job_type})
    logger.debug(f"Raw stats from DB for job {job_id}: {job.stats}") # Log the actual stats dict

    # The stats are stored as JSON in the Job model
    return job.stats if job.stats else {}


# --- UPDATED: Endpoint for Detailed Results ---
# Now returns JobResultsResponse which includes job_type and Union of result types
@router.get("/{job_id}/results", response_model=JobResultsResponse)
async def read_job_results(
    job_id: str = Path(..., title="The ID of the job to get detailed results for"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve the detailed classification results for a specific completed job.
    Ensures the current user owns the job or is an admin.
    Returns a structure containing the job_id, job_type, and a list of results
    (either JobResultItem or ReviewResultItem depending on the job_type).
    """
    set_log_context({"username": current_user.username, "target_job_id": job_id, "is_superuser": current_user.is_superuser})
    logger.info(f"Fetching detailed results for job ID: {job_id}")

    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        logger.warning(f"Job not found for results", extra={"job_id": job_id})
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    # --- MODIFIED: Authorization Check (Allow Superusers) ---
    if not current_user.is_superuser and job.created_by != current_user.username:
        logger.warning(f"Authorization failed: User '{current_user.username}' attempted to access results for job '{job_id}' owned by '{job.created_by}'")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access results for this job")
    # --- END MODIFIED ---

    # Check if job is completed and has results
    if job.status != JobStatus.COMPLETED.value:
        logger.warning(f"Detailed results requested but job not completed",
                       extra={"job_id": job_id, "status": job.status, "job_type": job.job_type})
        # Return empty list in the correct response structure
        return JobResultsResponse(job_id=job_id, job_type=JobType(job.job_type), results=[]) # Cast job_type to enum

    if not job.detailed_results:
        logger.warning(f"Job {job_id} is completed but has no detailed results stored.", extra={"job_id": job_id, "job_type": job.job_type})
        return JobResultsResponse(job_id=job_id, job_type=JobType(job.job_type), results=[]) # Cast job_type to enum

    # The detailed_results field should contain a list of dicts matching the expected schema.
    # Pydantic will validate this structure upon return based on the response_model.
    # We trust the background task stored the correct structure based on job_type.
    results_count = len(job.detailed_results)
    logger.info(f"Returning {results_count} detailed result items for job ID: {job_id}", extra={"job_type": job.job_type})

    # Pydantic should automatically validate based on the Union in JobResultsResponse
    return JobResultsResponse(job_id=job_id, job_type=JobType(job.job_type), results=job.detailed_results) # Cast job_type to enum
# --- END UPDATED ---


@router.get("/{job_id}/download")
async def download_job_results(
    job_id: str = Path(..., title="The ID of the job to download results for"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Downloads the output Excel file for a completed job.
    Ensures the current user owns the job or is an admin.
    Note: Only generates Excel for CLASSIFICATION jobs.
    The file reflects the latest state, including merged review results.
    """
    from fastapi.responses import FileResponse # Import here
    # import os # Already imported above

    set_log_context({"username": current_user.username, "target_job_id": job_id, "is_superuser": current_user.is_superuser})
    logger.info(f"Request to download results for job ID: {job_id}")

    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        logger.warning(f"Job not found for download", extra={"job_id": job_id})
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    # --- MODIFIED: Authorization Check (Allow Superusers) ---
    if not current_user.is_superuser and job.created_by != current_user.username:
        logger.warning(f"Authorization failed: User '{current_user.username}' attempted download for job '{job_id}' owned by '{job.created_by}'")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to download results for this job")
    # --- END MODIFIED ---

    # --- Check if download is applicable ---
    if job.job_type == JobType.REVIEW.value:
         logger.warning(f"Download requested for a REVIEW job ({job_id}), which doesn't generate an Excel file.", extra={"job_type": job.job_type})
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Download is not available for review jobs.")

    if job.status != JobStatus.COMPLETED.value or not job.output_file_name:
        logger.warning(f"Download requested but job not completed or output file missing",
                       extra={"job_id": job_id, "status": job.status, "output_file": job.output_file_name})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job not completed or output file not available.")
    # --- End Check ---

    # Construct the full path to the output file
    output_dir = os.path.join(settings.OUTPUT_DATA_DIR, job_id)
    file_path = os.path.join(output_dir, job.output_file_name)

    if not os.path.exists(file_path):
         logger.error(f"Output file record exists in DB but file not found on disk",
                      extra={"job_id": job_id, "expected_path": file_path})
         # Consider regenerating the file here if it's missing? Or just fail.
         # For now, fail. Regeneration should happen on completion/merge.
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Output file not found.")

    logger.info(f"Streaming output file for download",
                extra={"job_id": job_id, "file_path": file_path})
    return FileResponse(
        path=file_path,
        filename=job.output_file_name, # Suggest filename to browser
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# --- ADDED: Reclassify Endpoint ---
@router.post("/{original_job_id}/reclassify", response_model=ReclassifyResponse, status_code=status.HTTP_202_ACCEPTED)
async def reclassify_job_items(
    original_job_id: str = Path(..., description="The ID of the original classification job"),
    payload: ReclassifyPayload = ..., # Use the Pydantic model for the request body
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Initiates a re-classification task for specific vendors from an original job,
    using user-provided hints. Creates a new REVIEW job.
    Ensures the current user owns the original job or is an admin.
    """
    set_log_context({"username": current_user.username, "original_job_id": original_job_id, "is_superuser": current_user.is_superuser})
    logger.info(f"Received reclassification request for job {original_job_id}", extra={"item_count": len(payload.items)})

    # 1. Find the original job
    original_job = db.query(Job).filter(Job.id == original_job_id).first()
    if not original_job:
        logger.warning(f"Original job {original_job_id} not found for reclassification.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Original job not found")

    # --- MODIFIED: Authorization Check (Allow Superusers) ---
    if not current_user.is_superuser and original_job.created_by != current_user.username:
        logger.warning(f"Authorization failed: User '{current_user.username}' attempted reclassification for job '{original_job_id}' owned by '{original_job.created_by}'")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to reclassify items for this job")
    # --- END MODIFIED ---

    # 3. Basic validation (ensure original job was classification, maybe check status?)
    if original_job.job_type != JobType.CLASSIFICATION.value:
         logger.warning(f"Attempted to reclassify based on a non-CLASSIFICATION job.", extra={"original_job_type": original_job.job_type})
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reclassification can only be initiated from an original CLASSIFICATION job.")
    if original_job.status != JobStatus.COMPLETED.value:
         logger.warning(f"Attempted to reclassify based on a non-completed job.", extra={"original_job_status": original_job.status})
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reclassification can only be initiated from a COMPLETED job.")

    if not payload.items:
        logger.warning("Reclassification request received with no items to process.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No items provided for reclassification.")

    # 4. Create the new Review Job record
    review_job_id = f"review_{uuid.uuid4().hex[:12]}"
    review_job = Job(
        id=review_job_id,
        company_name=original_job.company_name, # Inherit company name
        input_file_name=f"Review of {original_job.input_file_name}", # Indicate source
        output_file_name=None, # Review jobs don't produce downloads
        status=JobStatus.PENDING.value,
        # --- FIX: Use a valid ProcessingStage ---
        current_stage=ProcessingStage.RECLASSIFICATION.value, # Set initial stage to RECLASSIFICATION
        # --- END FIX ---
        progress=0.0,
        created_by=current_user.username, # The user initiating the review owns the review job
        target_level=original_job.target_level, # Inherit target level
        job_type=JobType.REVIEW.value, # Mark as REVIEW type
        parent_job_id=original_job_id, # Link back to the original job
        stats={"reclassify_input": [item.model_dump() for item in payload.items]}, # Store input hints/vendors
        detailed_results=None, # Will be populated by the task
        notification_email=original_job.notification_email # Optionally inherit email
    )

    try:
        db.add(review_job)
        db.commit()
        db.refresh(review_job)
        logger.info(f"Created new REVIEW job record", extra={"review_job_id": review_job_id, "parent_job_id": original_job_id})
    except Exception as e:
        db.rollback()
        logger.error("Failed to create REVIEW job record in database", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to initiate reclassification job.")

    # 5. Queue the Celery task
    try:
        logger.info(f"Queuing reclassification task for review job {review_job_id}")
        reclassify_flagged_vendors_task.delay(review_job_id=review_job_id)
        logger.info(f"Reclassification task successfully queued.")
    except Exception as e:
        logger.error(f"Failed to queue Celery reclassification task for review job {review_job_id}", exc_info=True)
        # Attempt to mark the created review job as failed
        # Use the fail method on the Job instance
        review_job.fail(f"Failed to queue background task: {str(e)}")
        db.add(review_job) # Need to add the updated job back to the session
        db.commit()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to queue reclassification task.")

    # 6. Return the review job ID
    return ReclassifyResponse(review_job_id=review_job_id)
# --- END ADDED ---

# --- ADDED: Merge Endpoint ---
@router.post("/{review_job_id}/merge", status_code=status.HTTP_200_OK)
async def merge_review_results(
    review_job_id: str = Path(..., description="The ID of the completed REVIEW job to merge"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Merges the results from a completed REVIEW job back into its parent CLASSIFICATION job.
    Ensures the current user owns the review job or is an admin.
    Updates the parent job's detailed_results and triggers regeneration of its downloadable Excel file.
    """
    set_log_context({"username": current_user.username, "review_job_id": review_job_id, "is_superuser": current_user.is_superuser})
    logger.info(f"Received request to merge results for review job {review_job_id}")

    # 1. Fetch the REVIEW job
    review_job = db.query(Job).filter(Job.id == review_job_id).first()
    if not review_job:
        logger.warning(f"Review job {review_job_id} not found for merging.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review job not found")

    # --- MODIFIED: Authorization Check (Allow Superusers) ---
    if not current_user.is_superuser and review_job.created_by != current_user.username:
        logger.warning(f"Authorization failed: User '{current_user.username}' attempted merge for job '{review_job_id}' owned by '{review_job.created_by}'")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to merge this review job")
    # --- END MODIFIED ---

    # 3. Validation
    if review_job.job_type != JobType.REVIEW.value:
        logger.warning(f"Attempted to merge a non-REVIEW job.", extra={"job_id": review_job_id, "job_type": review_job.job_type})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only REVIEW jobs can be merged.")
    if review_job.status != JobStatus.COMPLETED.value:
        logger.warning(f"Attempted to merge a non-completed REVIEW job.", extra={"job_id": review_job_id, "status": review_job.status})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Review job must be COMPLETED to merge.")
    if not review_job.parent_job_id:
        logger.error(f"Review job {review_job_id} is missing a parent_job_id.", extra={"job_id": review_job_id})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Review job has no associated parent job.")
    if not review_job.detailed_results:
        logger.warning(f"Review job {review_job_id} has no detailed results to merge.", extra={"job_id": review_job_id})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Review job has no results to merge.")

    # Check if already merged
    if review_job.stats and review_job.stats.get("merged_at"):
        logger.warning(f"Review job {review_job_id} has already been merged.", extra={"job_id": review_job_id, "merged_at": review_job.stats["merged_at"]})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This review job has already been merged.")

    # 4. Fetch the Parent (Original) CLASSIFICATION job
    parent_job = db.query(Job).filter(Job.id == review_job.parent_job_id).first()
    if not parent_job:
        logger.error(f"Parent job {review_job.parent_job_id} not found for merging (referenced by review job {review_job_id}).")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent classification job not found.")
    if parent_job.job_type != JobType.CLASSIFICATION.value:
        logger.error(f"Parent job {parent_job.id} is not a CLASSIFICATION job.", extra={"parent_job_type": parent_job.job_type})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Parent job is not a classification job.")
    if not parent_job.detailed_results:
        logger.warning(f"Parent job {parent_job.id} has no detailed results to update. Initializing as empty list.", extra={"parent_job_id": parent_job.id})
        # Initialize as empty list if missing
        parent_job.detailed_results = []

    set_log_context({"parent_job_id": parent_job.id}) # Add parent job ID to context
    logger.info(f"Found parent job {parent_job.id} for merging.")

    # 5. Load results and perform the merge
    try:
        # Load review results (List[ReviewResultItem])
        review_results_data: List[ReviewResultItem] = [ReviewResultItem.model_validate(item) for item in review_job.detailed_results]
        logger.info(f"Loaded {len(review_results_data)} items from review job {review_job_id}.")

        # Load original results (List[JobResultItem])
        original_results_data: List[JobResultItem] = [JobResultItem.model_validate(item) for item in parent_job.detailed_results]
        logger.info(f"Loaded {len(original_results_data)} items from parent job {parent_job.id}.")

        # Create a map of original results keyed by vendor_name for efficient updates
        original_results_map: Dict[str, JobResultItem] = {item.vendor_name: item for item in original_results_data}

        # Iterate through review results and update the map
        updated_count = 0
        for review_item in review_results_data:
            vendor_name = review_item.vendor_name
            # The 'new_result' field in ReviewResultItem is already a dict matching JobResultItem structure
            new_result_dict = review_item.new_result
            if vendor_name in original_results_map:
                # Ensure the source is marked correctly in the merged result
                new_result_dict['classification_source'] = 'Review'
                # Validate the new result dict against the schema before replacing
                validated_new_result = JobResultItem.model_validate(new_result_dict)
                original_results_map[vendor_name] = validated_new_result
                updated_count += 1
                logger.debug(f"Updated result for vendor '{vendor_name}' in parent job map.")
            else:
                logger.warning(f"Vendor '{vendor_name}' from review job {review_job_id} not found in parent job {parent_job.id} results. Skipping update for this vendor.")

        logger.info(f"Updated {updated_count} vendor results in the parent job map.")

        # Convert the updated map back into a List[JobResultItem]
        updated_detailed_results_list: List[Dict[str, Any]] = [item.model_dump() for item in original_results_map.values()]

        # 6. Update the parent job's detailed_results
        parent_job.detailed_results = updated_detailed_results_list
        parent_job.updated_at = datetime.now(timezone.utc) # Mark parent job as updated
        logger.info(f"Updated detailed_results field on parent job {parent_job.id}.")

        # 7. Regenerate the Excel file for the parent job
        try:
            logger.info(f"Triggering Excel regeneration for parent job {parent_job.id}...")
            # Call generate_output_file with the updated results list
            # Ensure generate_output_file accepts List[JobResultItem] or adapt here
            new_output_filename = generate_output_file(
                job_id=parent_job.id,
                detailed_results=[JobResultItem.model_validate(item) for item in updated_detailed_results_list] # Pass validated models
            )
            parent_job.output_file_name = new_output_filename
            logger.info(f"Successfully regenerated Excel file for parent job {parent_job.id}: {new_output_filename}")
        except Exception as excel_err:
            logger.error(f"Failed to regenerate Excel file for parent job {parent_job.id} during merge.", exc_info=True)
            # Log the error prominently but continue with DB commit.
            # The results are still merged in the DB.

        # 8. Mark the REVIEW job as merged in its stats
        if not review_job.stats:
            review_job.stats = {}
        review_job.stats["merged_at"] = datetime.now(timezone.utc).isoformat()
        logger.info(f"Marked review job {review_job_id} as merged in stats.")

        # 9. Commit changes to both jobs
        db.add(parent_job) # Ensure parent job changes are staged
        db.add(review_job) # Ensure review job changes are staged
        db.commit()
        logger.info(f"Successfully committed changes for merge operation (Review Job: {review_job_id}, Parent Job: {parent_job.id}).")

        # 10. Return success response
        return {
            "message": f"Successfully merged results from review job {review_job_id} into parent job {parent_job.id}.",
            "updated_parent_job_id": parent_job.id
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error during merge operation for review job {review_job_id}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to merge results: {str(e)}")
# --- END ADDED ---