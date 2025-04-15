# app/tasks/reclassification_logic.py
import os # Keep the import
import asyncio
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Tuple, Optional

from core.database import SessionLocal # Assuming SessionLocal might be needed
from core.logging_config import get_logger
from core.log_context import set_log_context, clear_log_context # Assuming context might be used
from utils.log_utils import LogTimer, log_duration # Assuming logging utils might be used
from utils.taxonomy_loader import load_taxonomy, Taxonomy # Assuming taxonomy is needed
from models.job import Job, JobStatus, ProcessingStage, JobType # Assuming Job model is needed
from services.llm_service import LLMService # Assuming LLM service is needed
from schemas.review import ReclassifyRequestItem, ReviewResultItem # Assuming review schemas are needed
from schemas.job import JobResultItem # Assuming job result schema is needed for structure

# Import classification prompts if needed for reclassification
from .reclassification_prompts import generate_reclassification_prompt # Example: Assuming a specific prompt exists

logger = get_logger("vendor_classification.reclassification_logic")

async def process_reclassification(
    review_job: Job,
    db: Session,
    llm_service: LLMService
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Processes the reclassification request based on the review job details.
    Fetches original results, applies hints using LLM, and generates new results.
    """
    logger.info(f"Starting reclassification logic for review job {review_job.id}")
    set_log_context({"review_job_id": review_job.id, "parent_job_id": review_job.parent_job_id})

    start_time = datetime.now()
    # Initialize stats structure similar to classification, but focused on review
    final_stats: Dict[str, Any] = {
        "job_id": review_job.id,
        "parent_job_id": review_job.parent_job_id,
        "company_name": review_job.company_name,
        "target_level": review_job.target_level,
        "start_time": start_time.isoformat(),
        "end_time": None,
        "processing_duration_seconds": None,
        "total_items_processed": 0,
        "successful_reclassifications": 0,
        "failed_reclassifications": 0,
        "api_usage": {
            "openrouter_calls": 0,
            "openrouter_prompt_tokens": 0,
            "openrouter_completion_tokens": 0,
            "openrouter_total_tokens": 0,
            "tavily_search_calls": 0, # Should remain 0
            "cost_estimate_usd": 0.0
        }
    }
    review_results_list: List[Dict[str, Any]] = [] # Holds ReviewResultItem dicts

    try:
        # 1. Validate Input
        if not review_job or not review_job.parent_job_id or not review_job.stats or 'reclassify_input' not in review_job.stats:
            logger.error("Review job is missing parent job ID or input hints.", extra={"job_stats": review_job.stats if review_job else None})
            raise ValueError("Review job is missing parent job ID or input hints.")

        # --- FIX: Handle potential non-list or invalid items in reclassify_input ---
        input_items = review_job.stats['reclassify_input']
        items_to_reclassify: List[ReclassifyRequestItem] = []
        if isinstance(input_items, list):
            for item in input_items:
                try:
                    # Validate each item conforms to the Pydantic model
                    items_to_reclassify.append(ReclassifyRequestItem.model_validate(item))
                except Exception as item_validation_err:
                    logger.warning(f"Skipping invalid item in reclassify_input: {item}. Error: {item_validation_err}", exc_info=False)
        else:
            logger.error(f"reclassify_input in job stats is not a list: {type(input_items)}", extra={"job_id": review_job.id})
            raise ValueError("Invalid format for reclassify_input in job stats.")
        # --- END FIX ---

        final_stats["total_items_processed"] = len(items_to_reclassify)
        if not items_to_reclassify:
             logger.warning("No valid items found in reclassify_input stats.")
             # Complete the job successfully but with 0 items processed
             end_time = datetime.now()
             final_stats["end_time"] = end_time.isoformat()
             final_stats["processing_duration_seconds"] = (end_time - start_time).total_seconds()
             return [], final_stats # Return empty results and stats

        logger.info(f"Found {len(items_to_reclassify)} items to reclassify.")

        # 2. Fetch Parent Job's Detailed Results
        # Use a separate session or ensure the passed `db` session is robust
        parent_job = db.query(Job).filter(Job.id == review_job.parent_job_id).first()
        if not parent_job:
             logger.error(f"Parent job {review_job.parent_job_id} not found.")
             raise ValueError(f"Parent job {review_job.parent_job_id} not found.")
        if not parent_job.detailed_results:
             logger.error(f"Parent job {review_job.parent_job_id} has no detailed results.")
             # Decide how to handle this: fail or process items as failures?
             raise ValueError(f"Parent job {review_job.parent_job_id} has no detailed results.")

        original_results_map: Dict[str, JobResultItem] = {}
        try:
            for item_dict in parent_job.detailed_results:
                 # Validate each item conforms to JobResultItem before adding
                 validated_item = JobResultItem.model_validate(item_dict)
                 original_results_map[validated_item.vendor_name] = validated_item
        except Exception as validation_err:
             logger.error(f"Error validating original results from parent job {parent_job.id}", exc_info=True)
             raise ValueError("Failed to parse original results from parent job.")

        logger.info(f"Loaded {len(original_results_map)} original results from parent job.")

        # 3. Load Taxonomy
        taxonomy = load_taxonomy()

        # 4. Iterate and Reclassify each item
        update_interval = max(1, len(items_to_reclassify) // 10)
        processed_count = 0

        # Prepare batch for LLM if applicable (might call LLM per item or in batches)
        # For simplicity, let's assume one call per item for now
        for item_data in items_to_reclassify:
            vendor_name = item_data.vendor_name
            hint = item_data.hint
            logger.info(f"Reclassifying vendor: '{vendor_name}' with hint: '{hint}'")
            set_log_context({"current_vendor": vendor_name}) # Add vendor to context

            original_result_model = original_results_map.get(vendor_name)
            if not original_result_model:
                logger.warning(f"Vendor '{vendor_name}' from review request not found in parent job results. Skipping.")
                final_stats["failed_reclassifications"] += 1
                # Create a failure entry for this item
                failed_result_item = ReviewResultItem(
                    vendor_name=vendor_name,
                    hint=hint,
                    original_result={"error": "Original result not found in parent job"}, # Indicate error source
                    new_result=JobResultItem( # Use JobResultItem for structure consistency
                        vendor_name=vendor_name,
                        level1_id="ERROR", level1_name="ERROR",
                        level2_id=None, level2_name=None, level3_id=None, level3_name=None,
                        level4_id=None, level4_name=None, level5_id=None, level5_name=None,
                        final_confidence=0.0, final_status="Error", classification_source="Review",
                        classification_notes_or_reason="Original result not found in parent job",
                        achieved_level=0
                    ).model_dump()
                )
                review_results_list.append(failed_result_item.model_dump())
                clear_log_context(["current_vendor"])
                continue

            # --- Actual Reclassification LLM Call ---
            new_result_model = None
            try:
                # Fetch original vendor data (assuming it's stored appropriately or derivable)
                # For this example, let's assume original data might be part of the original_result_model
                # or needs fetching separately. We'll use a placeholder if not readily available.
                # A better approach would be to ensure the parent job stores original vendor input data.
                original_vendor_input_data = original_result_model.model_dump() # Use the stored result as a proxy for now
                original_vendor_input_data['vendor_name'] = vendor_name # Ensure name is correct

                # Generate the specific prompt for reclassification
                prompt = generate_reclassification_prompt(
                    original_vendor_data=original_vendor_input_data, # Pass original data
                    user_hint=hint,
                    original_classification=original_result_model.model_dump(), # Pass previous result dict
                    taxonomy=taxonomy, # Pass the whole taxonomy object
                    target_level=review_job.target_level, # Pass the target level for reclassification
                    attempt_id=f"{review_job.id}-{vendor_name}" # Create a unique ID for this attempt
                )

                logger.debug(f"Generated reclassification prompt for '{vendor_name}'") # Prompt content logged by LLM service now

                # --- UPDATED: Call the new LLM service method ---
                # Pass the nested api_usage dict directly for updates
                parsed_llm_output = await llm_service.call_llm_with_prompt(
                    prompt=prompt,
                    stats_dict=final_stats["api_usage"], # Pass the nested dict
                    job_id=review_job.id, # Pass review job ID for logging/cache key
                    max_tokens=1024 # Adjust if needed for reclassification output size
                )
                # --- END UPDATED ---

                # Remove the old parse call:
                # parsed_llm_output = llm_service.parse_json_response(llm_response_str, ...)

                logger.debug(f"Parsed LLM response dictionary for '{vendor_name}': {parsed_llm_output}")

                # Extract the classification result for this vendor
                # The prompt asks for a specific JSON output format, so parse that
                # Expecting format like: {"batch_id": "...", "level": N, "classifications": [...]}
                # Or potentially just the classification dict directly if the prompt asks for single output
                llm_output_data = None # Initialize
                if parsed_llm_output and isinstance(parsed_llm_output, dict):
                    # Check if the response has the expected 'classifications' list structure
                    if "classifications" in parsed_llm_output and isinstance(parsed_llm_output["classifications"], list) and len(parsed_llm_output["classifications"]) > 0:
                        llm_output_data = parsed_llm_output["classifications"][0]
                        logger.debug(f"Extracted classification data from 'classifications' list for '{vendor_name}': {llm_output_data}")
                    # Fallback: Check if the root object itself looks like the classification structure
                    elif "vendor_name" in parsed_llm_output and "level1" in parsed_llm_output:
                         llm_output_data = parsed_llm_output
                         logger.debug(f"Using root LLM response object as classification data for '{vendor_name}': {llm_output_data}")
                    else:
                        logger.warning(f"Parsed LLM output for '{vendor_name}' does not match expected structures ('classifications' list or direct result). Output: {parsed_llm_output}")
                else:
                     logger.warning(f"Failed to get valid dictionary from LLM response for '{vendor_name}'. Response: {parsed_llm_output}")


                # --- More robust check for L1 data from parsed output ---
                l1_data = llm_output_data.get("level1") if llm_output_data else None
                l1_category_id = l1_data.get("category_id") if l1_data else None
                l1_category_name = l1_data.get("category_name") if l1_data else None
                classification_not_possible = l1_data.get("classification_not_possible", True) if l1_data else True

                # Check if we got valid L1 classification data
                if l1_data and l1_category_id and l1_category_name and l1_category_id not in ["ERROR", "N/A"] and not classification_not_possible:
                     # --- Recursive Classification based on Hint ---
                     achieved_level = 0
                     final_confidence = 0.0
                     final_notes = None
                     final_status = "Not Possible" # Default

                     new_result_data = {
                         "vendor_name": vendor_name,
                         "level1_id": None, "level1_name": None,
                         "level2_id": None, "level2_name": None,
                         "level3_id": None, "level3_name": None,
                         "level4_id": None, "level4_name": None,
                         "level5_id": None, "level5_name": None,
                         "final_confidence": 0.0,
                         "final_status": "Not Possible",
                         "classification_source": "Review", # Mark as reviewed
                         "classification_notes_or_reason": None,
                         "achieved_level": 0
                     }

                     # Populate levels from LLM output
                     for level in range(1, review_job.target_level + 1):
                         level_key = f"level{level}"
                         level_data = llm_output_data.get(level_key)
                         if level_data and isinstance(level_data, dict):
                             cat_id = level_data.get("category_id")
                             cat_name = level_data.get("category_name")
                             level_not_possible = level_data.get("classification_not_possible", True)

                             if cat_id and cat_name and cat_id not in ["N/A", "ERROR"] and not level_not_possible:
                                 new_result_data[f"level{level}_id"] = cat_id
                                 new_result_data[f"level{level}_name"] = cat_name
                                 achieved_level = level
                                 final_confidence = level_data.get("confidence", 0.0)
                                 final_notes = level_data.get("notes") # Store notes from the deepest successful level
                                 final_status = "Classified"
                             else:
                                 # Stop populating further levels if this one failed or wasn't possible
                                 if achieved_level == 0 and level == 1: # Capture reason from L1 failure
                                     final_notes = level_data.get("classification_not_possible_reason") or level_data.get("notes")
                                 break # Stop processing levels for this vendor
                         else:
                             # Stop if expected level data is missing
                             if achieved_level == 0 and level == 1:
                                 final_notes = "LLM response missing Level 1 data."
                             break

                     # Finalize the result item
                     new_result_data["achieved_level"] = achieved_level
                     new_result_data["final_status"] = final_status
                     new_result_data["final_confidence"] = final_confidence
                     new_result_data["classification_notes_or_reason"] = final_notes or f"Reclassified based on hint: {hint}"


                     new_result_model = JobResultItem(**new_result_data)
                     final_stats["successful_reclassifications"] += 1
                     logger.info(f"Successfully reclassified '{vendor_name}' to Level {achieved_level}: '{new_result_model.level1_name}{' -> ' + new_result_model.level2_name if achieved_level > 1 else ''}...'.")

                else:
                     # Handle classification_not_possible or ERROR from LLM or missing L1 data
                     reason = "LLM response did not include valid Level 1 data." # Default reason
                     if l1_data:
                         if l1_category_id in ["ERROR", "N/A"]:
                             reason = l1_data.get("classification_not_possible_reason", f"LLM returned '{l1_category_id}' for Level 1")
                         elif classification_not_possible:
                             reason = l1_data.get("classification_not_possible_reason", "LLM indicated Level 1 classification not possible")
                         elif not l1_category_id or not l1_category_name:
                             reason = "LLM response missing Level 1 category_id or category_name."
                     elif llm_output_data is None:
                         # Reason is based on why llm_output_data became None earlier
                         if parsed_llm_output is None:
                             reason = "LLM call failed or response parsing failed."
                         else:
                             reason = "LLM response structure did not match expected format."
                     else: # llm_output_data exists but no l1_data
                         reason = "LLM response missing 'level1' field."


                     logger.warning(f"LLM could not reclassify '{vendor_name}' with hint. Reason: {reason}")
                     final_stats["failed_reclassifications"] += 1
                     new_result_model = JobResultItem(
                         vendor_name=vendor_name,
                         level1_id=None, level1_name=None, # Or ERROR if appropriate
                         level2_id=None, level2_name=None, level3_id=None, level3_name=None,
                         level4_id=None, level4_name=None, level5_id=None, level5_name=None,
                         final_confidence=0.0,
                         final_status="Not Possible", # Or "Error"
                         classification_source="Review",
                         classification_notes_or_reason=f"Reclassification failed: {reason}", # Store the specific reason
                         achieved_level=0
                     )

            except Exception as llm_err:
                logger.error(f"Error during LLM reclassification call or processing for '{vendor_name}'", exc_info=True)
                final_stats["failed_reclassifications"] += 1
                new_result_model = JobResultItem( # Create error result
                    vendor_name=vendor_name,
                    level1_id="ERROR", level1_name="ERROR",
                    level2_id=None, level2_name=None, level3_id=None, level3_name=None,
                    level4_id=None, level4_name=None, level5_id=None, level5_name=None,
                    final_confidence=0.0, final_status="Error", classification_source="Review",
                    classification_notes_or_reason=f"Error during reclassification processing: {llm_err}",
                    achieved_level=0
                )
            # --- End Actual Reclassification LLM Call ---

            # Store the result (original + new)
            review_item = ReviewResultItem(
                vendor_name=vendor_name,
                hint=hint,
                original_result=original_result_model.model_dump(), # Store as dict
                new_result=new_result_model.model_dump() # Store as dict
            )
            review_results_list.append(review_item.model_dump()) # Append the dict representation

            processed_count += 1
            if processed_count % update_interval == 0 or processed_count == len(items_to_reclassify):
                 progress = 0.1 + 0.85 * (processed_count / len(items_to_reclassify))
                 # Use try-except for update_progress as the session might become invalid
                 try:
                     review_job.update_progress(progress=min(0.95, progress), stage=ProcessingStage.RECLASSIFICATION, db_session=db)
                     logger.debug(f"Updated review job progress: {progress:.2f}")
                 except Exception as db_update_err:
                      logger.error("Failed to update job progress during reclassification loop", exc_info=db_update_err)
                      db.rollback() # Rollback potential partial commit within update_progress

            clear_log_context(["current_vendor"]) # Clear vendor from context


        # 5. Finalize Stats
        end_time = datetime.now()
        processing_duration = (end_time - start_time).total_seconds()
        final_stats["end_time"] = end_time.isoformat()
        final_stats["processing_duration_seconds"] = round(processing_duration, 2)
        # Calculate final cost based on accumulated API usage
        cost_input_per_1k = 0.0005
        cost_output_per_1k = 0.0015
        api_usage = final_stats["api_usage"]
        estimated_cost = (api_usage["openrouter_prompt_tokens"] / 1000) * cost_input_per_1k + \
                           (api_usage["openrouter_completion_tokens"] / 1000) * cost_output_per_1k
        # No Tavily cost expected here
        api_usage["cost_estimate_usd"] = round(estimated_cost, 4)

        logger.info(f"Reclassification logic finished for review job {review_job.id}. Results: {final_stats}")

    except Exception as e:
        logger.error(f"Error during reclassification logic for review job {review_job.id}", exc_info=True)
        # Ensure the job is marked as failed by the caller (_process_reclassification_async)
        final_stats["error_message"] = f"Reclassification logic failed: {type(e).__name__}: {str(e)}"
        # Attempt to add an overall error marker to results if possible
        if not review_results_list: # If no results were added yet
             review_results_list.append({"error": final_stats["error_message"]})
        # Return potentially partial results and error stats
        return review_results_list, final_stats
    finally:
        clear_log_context() # Clear job-specific context

    return review_results_list, final_stats