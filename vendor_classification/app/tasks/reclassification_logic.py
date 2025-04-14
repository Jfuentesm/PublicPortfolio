# app/tasks/reclassification_logic.py
import asyncio
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from core.config import settings
from core.logging_config import get_logger
from core.log_context import set_log_context
from utils.log_utils import LogTimer, log_function_call, log_duration

from models.job import Job, JobStatus, ProcessingStage, JobType
from models.taxonomy import Taxonomy
from services.llm_service import LLMService
from services.file_service import read_vendor_file # To read original data
from utils.taxonomy_loader import load_taxonomy
from schemas.job import JobResultItem # For validation/structure reference
from schemas.review import ReviewResultItem

# Import the specific prompt generator
from .reclassification_prompts import generate_reclassification_prompt

logger = get_logger("vendor_classification.reclassification_logic")

# Timeout for a single vendor reclassification LLM call
RECLASSIFY_VENDOR_TIMEOUT = 120.0 # 2 minutes per vendor

async def _reclassify_single_vendor(
    vendor_name: str,
    hint: str,
    original_vendor_data: Dict[str, Any],
    original_classification_result: Optional[Dict[str, Any]],
    taxonomy: Taxonomy,
    llm_service: LLMService,
    target_level: int,
    stats: Dict[str, Any], # Pass stats dict to update API usage
    attempt_id: str
) -> Dict[str, Any]:
    """
    Handles the LLM call and result processing for re-classifying a single vendor.
    Returns a dictionary matching the JobResultItem structure for the *new* classification.
    """
    logger.info(f"Re-classifying vendor '{vendor_name}' using hint.", extra={"target_level": target_level, "attempt_id": attempt_id})
    new_result_structure: Dict[str, Any] = {
        "vendor_name": vendor_name,
        "level1_id": None, "level1_name": None,
        "level2_id": None, "level2_name": None,
        "level3_id": None, "level3_name": None,
        "level4_id": None, "level4_name": None,
        "level5_id": None, "level5_name": None,
        "final_confidence": 0.0,
        "final_status": "Error", # Default to Error
        "classification_source": "Review", # Source is Review
        "classification_notes_or_reason": "Reclassification not completed.",
        "achieved_level": 0
    }

    try:
        # 1. Generate Prompt
        logger.debug(f"Generating reclassification prompt for '{vendor_name}'")
        prompt = generate_reclassification_prompt(
            original_vendor_data=original_vendor_data,
            user_hint=hint,
            original_classification=original_classification_result,
            taxonomy=taxonomy,
            target_level=target_level,
            attempt_id=attempt_id
        )

        # 2. Call LLM (using classify_batch for one item, adapting prompt/payload)
        #    We expect the LLM to perform the hierarchy internally based on the prompt.
        logger.debug(f"Calling LLM for reclassification of '{vendor_name}'")
        with LogTimer(logger, f"LLM reclassification - Vendor '{vendor_name}'", include_in_stats=True):
            # Use classify_batch with a single item list and the custom prompt
            # Note: classify_batch expects a list of vendor dicts, level, taxonomy etc.
            # We need to adjust how we call it or create a wrapper/new method.
            # Let's assume classify_batch can handle a custom prompt via messages for now.
            # OR, more likely, we need a new method in LLMService or adapt the prompt generation
            # to fit the existing classify_batch structure (less ideal).

            # --- Alternative Approach: Direct LLM Call (if LLMService allows) ---
            # This bypasses the batching logic but gives more control over the prompt.
            # Requires adding a method like `call_llm_raw` or similar to LLMService.
            # For now, let's *simulate* the expected output structure as if classify_batch worked.
            # In a real implementation, this LLM call needs refinement.

            # --- Placeholder LLM Call ---
            # This simulates the structure returned by classify_batch
            # Replace this with the actual LLM call logic
            llm_response_data = await llm_service.classify_batch(
                 batch_data=[original_vendor_data], # Pass original data for context if needed by classify_batch internals
                 level=target_level, # Signal target level
                 taxonomy=taxonomy,
                 parent_category_id=None, # Not applicable directly here, hierarchy driven by prompt
                 # We need a way to pass the custom prompt - maybe a new parameter?
                 # custom_prompt=prompt # Hypothetical parameter
                 # Or modify classify_batch to accept raw messages
            )
            # --- End Placeholder ---

        logger.debug(f"LLM reclassification call completed for '{vendor_name}'")

        if llm_response_data and isinstance(llm_response_data.get("usage"), dict):
            usage = llm_response_data["usage"]
            stats["api_usage"]["openrouter_calls"] += 1
            stats["api_usage"]["openrouter_prompt_tokens"] += usage.get("prompt_tokens", 0)
            stats["api_usage"]["openrouter_completion_tokens"] += usage.get("completion_tokens", 0)
            stats["api_usage"]["openrouter_total_tokens"] += usage.get("total_tokens", 0)
        else:
            logger.warning("Reclassification LLM response missing or has invalid usage data.")

        if llm_response_data is None or "result" not in llm_response_data:
            raise ValueError("LLM service returned None or invalid response structure.")

        llm_result_payload = llm_response_data["result"]
        classifications = llm_result_payload.get("classifications", [])

        if not classifications or not isinstance(classifications, list) or len(classifications) == 0:
             raise ValueError("LLM response missing 'classifications' array or it's empty.")

        # The prompt asks for the full hierarchy in the response under 'classifications'[0]
        new_classification_data = classifications[0] # Get the single vendor result

        # 3. Process and Validate the LLM's Hierarchical Result
        deepest_successful_level = 0
        final_level_data = None
        final_notes_or_reason = None

        # Iterate through levels 1 to target_level from the LLM response
        for level in range(1, target_level + 1):
            level_key = f"level{level}"
            level_data = new_classification_data.get(level_key)

            if level_data and isinstance(level_data, dict):
                # --- Basic Validation (similar to process_batch) ---
                category_id = level_data.get("category_id")
                is_possible = not level_data.get("classification_not_possible", True)

                if is_possible and (not category_id or category_id == "N/A"):
                    logger.warning(f"Reclassification L{level} for '{vendor_name}' marked possible but ID missing/NA. Marking failed.")
                    level_data["classification_not_possible"] = True
                    level_data["classification_not_possible_reason"] = f"LLM marked L{level} possible but ID was missing/NA"
                    level_data["confidence"] = 0.0
                    is_possible = False

                # TODO: Add taxonomy validation against valid IDs for the parent if needed,
                # similar to process_batch. This requires getting the parent ID from the previous level's result.

                # Populate the flat structure
                new_result_structure[f"level{level}_id"] = level_data.get("category_id")
                new_result_structure[f"level{level}_name"] = level_data.get("category_name")

                if is_possible:
                    deepest_successful_level = level
                    final_level_data = level_data
                    final_notes_or_reason = level_data.get("notes")
                elif deepest_successful_level == 0 and level == 1: # Capture L1 failure reason
                    final_notes_or_reason = level_data.get("classification_not_possible_reason") or level_data.get("notes")

                # If classification not possible at this level, stop processing further levels
                if not is_possible:
                    logger.info(f"Reclassification for '{vendor_name}' stopped at Level {level}. Reason: {level_data.get('classification_not_possible_reason')}")
                    break
            else:
                # Stop if a level is missing in the response (shouldn't happen if LLM follows prompt)
                logger.warning(f"Reclassification response for '{vendor_name}' missing expected Level {level} data. Stopping hierarchy processing.")
                if deepest_successful_level == 0 and level == 1: # If L1 is missing entirely
                    final_notes_or_reason = f"LLM response did not include Level {level} data."
                break

        # Determine final status based on results
        if final_level_data:
            new_result_structure["final_status"] = "Classified"
            new_result_structure["final_confidence"] = final_level_data.get("confidence")
            new_result_structure["achieved_level"] = deepest_successful_level
            new_result_structure["classification_notes_or_reason"] = final_notes_or_reason
        else:
            new_result_structure["final_status"] = "Not Possible"
            new_result_structure["final_confidence"] = 0.0
            new_result_structure["achieved_level"] = 0
            new_result_structure["classification_notes_or_reason"] = final_notes_or_reason or "Reclassification failed or yielded no result."

        # Validate the final structure (optional but recommended)
        try:
            JobResultItem.model_validate(new_result_structure)
        except Exception as validation_err:
            logger.error(f"Validation failed for reclassified result of vendor '{vendor_name}'",
                         exc_info=True, extra={"result_data": new_result_structure})
            # Fallback to error state
            new_result_structure["final_status"] = "Error"
            new_result_structure["classification_notes_or_reason"] = f"Internal validation error after reclassification: {str(validation_err)}"
            new_result_structure["achieved_level"] = 0
            new_result_structure["final_confidence"] = 0.0
            # Clear level data on validation error
            for i in range(1, 6):
                new_result_structure[f"level{i}_id"] = None
                new_result_structure[f"level{i}_name"] = None

    except Exception as e:
        logger.error(f"Error during single vendor reclassification for '{vendor_name}'", exc_info=True)
        new_result_structure["final_status"] = "Error"
        new_result_structure["classification_notes_or_reason"] = f"Reclassification task error: {str(e)[:150]}"
        new_result_structure["achieved_level"] = 0
        new_result_structure["final_confidence"] = 0.0
         # Clear level data on error
        for i in range(1, 6):
            new_result_structure[f"level{i}_id"] = None
            new_result_structure[f"level{i}_name"] = None

    return new_result_structure


@log_function_call(logger, include_args=False)
async def process_reclassification(
    review_job: Job,
    db: Session,
    llm_service: LLMService
):
    """
    Main orchestration function for the reclassification task.
    Fetches original data/results, iterates through hints, calls LLM, stores results.
    """
    parent_job_id = review_job.parent_job_id
    review_job_id = review_job.id
    target_level = review_job.target_level
    reclassify_input = review_job.stats.get("reclassify_input", [])

    logger.info(f"Starting reclassification process for review job {review_job_id}",
                extra={"parent_job_id": parent_job_id, "item_count": len(reclassify_input)})

    if not parent_job_id:
        raise ValueError("Review job is missing parent_job_id.")
    if not reclassify_input:
        logger.warning(f"Review job {review_job_id} has no items to reclassify in stats.")
        return [], {} # Return empty results and stats

    # --- Initialize stats for the review job ---
    start_time = datetime.now()
    stats: Dict[str, Any] = {
        "job_id": review_job_id,
        "parent_job_id": parent_job_id,
        "start_time": start_time.isoformat(),
        "end_time": None,
        "processing_duration_seconds": None,
        "total_items_processed": 0,
        "successful_reclassifications": 0,
        "failed_reclassifications": 0,
        "api_usage": { # Initialize API usage tracking
            "openrouter_calls": 0,
            "openrouter_prompt_tokens": 0,
            "openrouter_completion_tokens": 0,
            "openrouter_total_tokens": 0,
            "tavily_search_calls": 0, # Should be 0 for reclassification
            "cost_estimate_usd": 0.0
        }
    }
    # --- End Initialize stats ---

    # 1. Fetch Parent Job and Taxonomy
    parent_job = db.query(Job).filter(Job.id == parent_job_id).first()
    if not parent_job:
        raise ValueError(f"Parent job {parent_job_id} not found.")
    if not parent_job.detailed_results:
        raise ValueError(f"Parent job {parent_job_id} does not have detailed results stored.")

    taxonomy = load_taxonomy()

    # 2. Load Original Input Data (Requires access to the parent job's input file)
    # Construct the path relative to the parent job ID
    parent_input_dir = os.path.join(settings.INPUT_DATA_DIR, parent_job_id)
    parent_file_path = os.path.join(parent_input_dir, parent_job.input_file_name)
    if not os.path.exists(parent_file_path):
         raise FileNotFoundError(f"Original input file not found for parent job {parent_job_id} at {parent_file_path}")

    original_vendors_data_list = read_vendor_file(parent_file_path)
    # Create a map for easy lookup: vendor_name -> full original data dict
    original_data_map = {
        str(vendor.get('vendor_name')).strip().title(): vendor # Assuming names were normalized
        for vendor in original_vendors_data_list if vendor.get('vendor_name')
    }
    logger.info(f"Loaded original input data from {parent_file_path}. Found {len(original_data_map)} vendors.")

    # 3. Create Map of Original Results
    original_results_map: Dict[str, Dict[str, Any]] = {
        str(result.get('vendor_name')).strip().title(): result # Assuming names match normalized names
        for result in parent_job.detailed_results if result.get('vendor_name')
    }
    logger.info(f"Created map of original results from parent job {parent_job_id}. Found {len(original_results_map)} results.")


    # 4. Process each item with hint concurrently
    review_results_list: List[Dict[str, Any]] = []
    tasks = []
    processed_count = 0

    for item in reclassify_input:
        processed_count += 1
        vendor_name_raw = item.get("vendor_name")
        hint = item.get("hint")

        if not vendor_name_raw or not hint:
            logger.warning("Skipping item due to missing vendor name or hint", extra={"item": item})
            stats["failed_reclassifications"] += 1
            continue

        # Normalize vendor name for lookup consistency
        vendor_name = str(vendor_name_raw).strip().title()

        original_data = original_data_map.get(vendor_name)
        original_result = original_results_map.get(vendor_name)

        if not original_data:
            logger.warning(f"Original data not found for vendor '{vendor_name}'. Skipping reclassification.", extra={"vendor_name_raw": vendor_name_raw})
            stats["failed_reclassifications"] += 1
            # Store a failure record?
            review_results_list.append({
                "vendor_name": vendor_name_raw,
                "hint": hint,
                "original_result": original_result or {"error": "Original result lookup failed"},
                "new_result": {"final_status": "Error", "classification_notes_or_reason": "Original input data not found"}
            })
            continue
        if not original_result:
             logger.warning(f"Original classification result not found for vendor '{vendor_name}'. Proceeding without it as context.", extra={"vendor_name_raw": vendor_name_raw})
             # Proceed, but the prompt won't have the original classification context

        attempt_id = f"{review_job_id}_{processed_count}"
        set_log_context({"vendor_name": vendor_name, "attempt_id": attempt_id})

        # Create task for concurrent execution
        task = asyncio.create_task(
            _reclassify_single_vendor(
                vendor_name=vendor_name, # Use normalized name for processing
                hint=hint,
                original_vendor_data=original_data,
                original_classification_result=original_result,
                taxonomy=taxonomy,
                llm_service=llm_service,
                target_level=target_level,
                stats=stats, # Pass stats dict
                attempt_id=attempt_id
            )
        )
        tasks.append((vendor_name_raw, hint, original_result, task)) # Store raw name, hint, original result with task

    # 5. Gather results
    logger.info(f"Gathering results for {len(tasks)} reclassification tasks.")
    task_results = await asyncio.gather(*(task for _, _, _, task in tasks))
    logger.info("Reclassification tasks completed.")

    # 6. Combine results
    for i, new_result in enumerate(task_results):
        vendor_name_raw, hint, original_result, _ = tasks[i]
        review_item = {
            "vendor_name": vendor_name_raw, # Store the name as provided in the input
            "hint": hint,
            "original_result": original_result or {"message": "Original result not found during processing"},
            "new_result": new_result # This is the dict returned by _reclassify_single_vendor
        }
        review_results_list.append(review_item)

        # Update stats based on the new result status
        if new_result and new_result.get("final_status") == "Classified":
            stats["successful_reclassifications"] += 1
        else:
            stats["failed_reclassifications"] += 1

    stats["total_items_processed"] = len(reclassify_input)

    # 7. Finalize stats
    end_time = datetime.now()
    processing_duration = (end_time - start_time).total_seconds()
    stats["end_time"] = end_time.isoformat()
    stats["processing_duration_seconds"] = round(processing_duration, 2)
    # Calculate cost
    cost_input_per_1k = 0.0005
    cost_output_per_1k = 0.0015
    estimated_cost = (stats["api_usage"]["openrouter_prompt_tokens"] / 1000) * cost_input_per_1k + \
                        (stats["api_usage"]["openrouter_completion_tokens"] / 1000) * cost_output_per_1k
    # Tavily cost should be 0 here
    stats["api_usage"]["cost_estimate_usd"] = round(estimated_cost, 4)

    logger.info("Reclassification processing finished.", extra={
        "successful": stats["successful_reclassifications"],
        "failed": stats["failed_reclassifications"],
        "duration_sec": stats["processing_duration_seconds"]
    })

    # Return the list of review results and the final stats dict
    return review_results_list, stats