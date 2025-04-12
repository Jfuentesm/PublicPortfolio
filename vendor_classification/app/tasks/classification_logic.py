# <file path='app/tasks/classification_logic.py'>
import asyncio
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from core.config import settings
from core.logging_config import get_logger
# Import context functions if needed directly (though often used via logger)
from core.log_context import set_log_context
# Import log helpers from utils
from utils.log_utils import LogTimer, log_function_call, log_duration

from models.job import Job, JobStatus, ProcessingStage
from models.taxonomy import Taxonomy
from services.llm_service import LLMService
from services.search_service import SearchService

logger = get_logger("vendor_classification.classification_logic")

# --- Constants ---
MAX_CONCURRENT_SEARCHES = 10 # Limit concurrent search/LLM processing for unknown vendors
BATCH_PROCESSING_TIMEOUT = 300.0 # Max time (seconds) per classification batch
SEARCH_CLASSIFY_TIMEOUT = 600.0 # Max time (seconds) per vendor search + recursive classification

# --- Helper Functions (Moved from classification_tasks.py) ---

def create_batches(items: List[Any], batch_size: int) -> List[List[Any]]:
    """Create batches from a list of items."""
    if not items: return []
    if not isinstance(items, list):
        logger.warning(f"create_batches expected a list, got {type(items)}. Returning empty list.")
        return []
    if batch_size <= 0:
        logger.warning(f"Invalid batch_size {batch_size}, using default from settings.")
        batch_size = settings.BATCH_SIZE
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
        level_result = None
        if vendor_results is not None:
            level_result = vendor_results.get(parent_key)
        else:
            logger.warning(f"group_by_parent_category: Vendor '{vendor_name}' not found in results dictionary.")
            excluded_count += 1
            continue

        if level_result and isinstance(level_result, dict) and not level_result.get("classification_not_possible", True):
            category_id = level_result.get("category_id")
            if category_id and category_id not in ["N/A", "ERROR"]:
                if category_id not in grouped:
                    grouped[category_id] = []
                grouped[category_id].append(vendor_name)
                grouped_count += 1
                # Reduced verbosity: logger.debug(f"  Grouping vendor '{vendor_name}' under parent '{category_id}'.")
            else:
                logger.debug(f"  Excluding vendor '{vendor_name}': classified at '{parent_key}' but has invalid category_id '{category_id}'.")
                excluded_count += 1
        else:
            reason = "Not processed"
            if level_result and isinstance(level_result, dict):
                reason = level_result.get('classification_not_possible_reason', 'Marked not possible')
            elif not level_result:
                    reason = f"No result found for {parent_key}"
            logger.info(f"  Excluding vendor '{vendor_name}' from Level {parent_level + 1}: not successfully classified at '{parent_key}'. Reason: {reason}.")
            excluded_count += 1

    logger.info(f"group_by_parent_category: Finished grouping for Level {parent_level + 1}. Created {len(grouped)} groups, included {grouped_count} vendors, excluded {excluded_count} vendors.")
    return grouped

# --- Core Processing Logic (Moved from classification_tasks.py) ---

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
    classification_source = "Search" if search_context else "Initial" # Determine source

    logger.info(f"process_batch: Starting Level {level} batch using {context_type}.",
                extra={"batch_size": len(batch_data), "parent_category_id": parent_category_id, "first_vendor": batch_names[0] if batch_names else 'N/A'})

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
            elif level == 5:
                categories = taxonomy.get_level5_categories(parent_category_id)
            else:
                    logger.error(f"process_batch: Invalid level {level} requested.")
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
        # else: # Reduced verbosity
                # logger.debug(f"process_batch: Found {len(valid_category_ids)} valid IDs for Level {level}, Parent '{parent_category_id}'. Example: {list(valid_category_ids)[:5]}")

    except Exception as tax_err:
        logger.error(f"process_batch: Error getting valid categories from taxonomy", exc_info=True,
                        extra={"level": level, "parent_category_id": parent_category_id})
        valid_category_ids = set()
        category_id_lookup_error = True

    # --- Call LLM ---
    llm_response_data = None
    try:
        logger.info(f"process_batch: Calling LLM for Level {level}, Parent '{parent_category_id or 'None'}', Context: {context_type}")
        with LogTimer(logger, f"LLM classification - Level {level}, Parent '{parent_category_id or 'None'}' ({context_type})", include_in_stats=True):
            # Note: The actual HTTP call and retries happen inside classify_batch
            llm_response_data = await llm_service.classify_batch(
                batch_data=batch_data,
                level=level,
                taxonomy=taxonomy,
                parent_category_id=parent_category_id,
                search_context=search_context
            )
        logger.info(f"process_batch: LLM call completed for Level {level}, Parent '{parent_category_id or 'None'}'.")

        if llm_response_data and isinstance(llm_response_data.get("usage"), dict):
            usage = llm_response_data["usage"]
            stats["api_usage"]["openrouter_calls"] += 1
            stats["api_usage"]["openrouter_prompt_tokens"] += usage.get("prompt_tokens", 0)
            stats["api_usage"]["openrouter_completion_tokens"] += usage.get("completion_tokens", 0)
            stats["api_usage"]["openrouter_total_tokens"] += usage.get("total_tokens", 0)
            # logger.debug(f"process_batch: LLM API usage updated", extra=usage) # Reduced verbosity
        else:
            logger.warning("process_batch: LLM response missing or has invalid usage data.")

        if llm_response_data is None:
                logger.error("process_batch: Received None response from llm_service.classify_batch. Cannot process results.")
                raise ValueError("LLM service returned None, indicating a failure in the call.")

        llm_result = llm_response_data.get("result", {})
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
                                    extra={"valid_ids_count": len(valid_category_ids)})
                    classification_not_possible = True
                    reason = f"Invalid category ID '{category_id}' returned by LLM (Valid examples: {list(valid_category_ids)[:3]})"
                    confidence = 0.0
                    category_id = "N/A"
                    category_name = "N/A"
                    stats["invalid_category_errors"] = stats.get("invalid_category_errors", 0) + 1
                # else: # Reduced verbosity
                        # logger.debug(f"Category ID '{category_id}' for '{target_vendor_name}' is valid for Level {level}, Parent '{parent_category_id}'.")
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
                "vendor_name": target_vendor_name,
                # --- UPDATED: Use classification_source ---
                "classification_source": classification_source
                # --- END UPDATED ---
            }
            # logger.debug(f"process_batch: Processed result for '{target_vendor_name}' at Level {level}. Possible: {not classification_not_possible}, ID: {category_id}") # Reduced verbosity

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
                    "vendor_name": vendor_name,
                    # --- UPDATED: Use classification_source ---
                    "classification_source": classification_source
                    # --- END UPDATED ---
                }

    # This broad exception catch handles errors from llm_service.classify_batch (like RetryError)
    # or errors during the result processing/validation within this function.
    except Exception as e:
        logger.error(f"Failed to process batch at Level {level} ({context_type})", exc_info=True,
                        extra={"batch_names": batch_names, "error": str(e)})
        # Mark all vendors in the batch as failed
        for vendor_name in batch_names:
            results[vendor_name] = {
                "category_id": "ERROR", "category_name": "ERROR", "confidence": 0.0,
                "classification_not_possible": True,
                "classification_not_possible_reason": f"Batch processing error: {str(e)[:100]}",
                "notes": None,
                "vendor_name": vendor_name,
                # --- UPDATED: Use classification_source ---
                "classification_source": classification_source
                # --- END UPDATED ---
            }
    logger.info(f"process_batch: Finished Level {level} batch for parent '{parent_category_id or 'None'}'. Returning {len(results)} results.")
    return results


@log_function_call(logger, include_args=False)
async def search_and_classify_recursively(
    vendor_data: Dict[str, Any],
    taxonomy: Taxonomy,
    llm_service: LLMService,
    search_service: SearchService,
    stats: Dict[str, Any],
    semaphore: asyncio.Semaphore,
    target_level: int # <<< ADDED target_level
) -> Dict[str, Any]:
    """
    Performs Tavily search, attempts L1 classification, and then recursively
    attempts L2 up to target_level classification using the search context.
    Controlled by semaphore.
    Returns the search_result_data dictionary, potentially augmented with
    classification results (keyed as classification_l1, classification_l2, etc.).
    """
    vendor_name = vendor_data.get('vendor_name', 'UnknownVendor')
    logger.debug(f"search_and_classify_recursively: Waiting to acquire semaphore for vendor '{vendor_name}'.")
    async with semaphore: # Limit concurrency
        logger.info(f"search_and_classify_recursively: Acquired semaphore. Starting for vendor '{vendor_name}' up to Level {target_level}.")
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
            "classification_l5": None
            }

        # --- 1. Perform Tavily Search ---
        try:
            logger.debug(f"search_and_classify_recursively: Calling search_service.search_vendor for '{vendor_name}'.")
            with LogTimer(logger, f"Tavily search for '{vendor_name}'", include_in_stats=True):
                tavily_response = await search_service.search_vendor(vendor_name)
            logger.debug(f"search_and_classify_recursively: search_service.search_vendor returned for '{vendor_name}'.")

            stats["api_usage"]["tavily_search_calls"] += 1
            search_result_data.update(tavily_response) # Update with actual search results or error

            source_count = len(search_result_data.get("sources", []))
            if search_result_data.get("error"):
                logger.warning(f"search_and_classify_recursively: Search failed", extra={"vendor": vendor_name, "error": search_result_data["error"]})
                search_result_data["classification_l1"] = {
                        "classification_not_possible": True,
                        "classification_not_possible_reason": f"Search error: {str(search_result_data['error'])[:100]}",
                        "confidence": 0.0, "vendor_name": vendor_name, "notes": "Search Failed",
                        # --- UPDATED: Add source ---
                        "classification_source": "Search"
                        # --- END UPDATED ---
                }
                logger.debug(f"search_and_classify_recursively: Releasing semaphore early due to search error for '{vendor_name}'.")
                return search_result_data # Stop if search failed
            else:
                logger.info(f"search_and_classify_recursively: Search completed", extra={"vendor": vendor_name, "source_count": source_count, "summary_present": bool(search_result_data.get('summary'))})

        except Exception as search_exc:
            logger.error(f"search_and_classify_recursively: Unexpected error during Tavily search for {vendor_name}", exc_info=True)
            search_result_data["error"] = f"Unexpected search error: {str(search_exc)}"
            search_result_data["classification_l1"] = {
                    "classification_not_possible": True,
                    "classification_not_possible_reason": f"Search task error: {str(search_exc)[:100]}",
                    "confidence": 0.0, "vendor_name": vendor_name, "notes": "Search Failed",
                    # --- UPDATED: Add source ---
                    "classification_source": "Search"
                    # --- END UPDATED ---
                }
            logger.debug(f"search_and_classify_recursively: Releasing semaphore early due to search exception for '{vendor_name}'.")
            return search_result_data # Stop if search failed

        # --- 2. Attempt L1 Classification using Search Results ---
        search_content_available = search_result_data.get("sources") or search_result_data.get("summary")
        if not search_content_available:
            logger.warning(f"search_and_classify_recursively: No usable search results found for vendor, cannot classify", extra={"vendor": vendor_name})
            search_result_data["classification_l1"] = {
                    "classification_not_possible": True,
                    "classification_not_possible_reason": "No search results content found",
                    "confidence": 0.0, "vendor_name": vendor_name, "notes": "No Search Content",
                    # --- UPDATED: Add source ---
                    "classification_source": "Search"
                    # --- END UPDATED ---
            }
            logger.debug(f"search_and_classify_recursively: Releasing semaphore early due to no search content for '{vendor_name}'.")
            return search_result_data # Stop if no content

        valid_l1_category_ids: Set[str] = set(taxonomy.categories.keys())
        llm_response_l1 = None
        try:
            logger.debug(f"search_and_classify_recursively: Calling llm_service.process_search_results (L1) for '{vendor_name}'.")
            with LogTimer(logger, f"LLM L1 classification from search for '{vendor_name}'", include_in_stats=True):
                # This specific function is designed only for L1 from search results
                llm_response_l1 = await llm_service.process_search_results(vendor_data, search_result_data, taxonomy)
            logger.debug(f"search_and_classify_recursively: llm_service.process_search_results (L1) returned for '{vendor_name}'.")

            if llm_response_l1 is None:
                    logger.error("search_and_classify_recursively: Received None response from llm_service.process_search_results. Cannot process L1.")
                    raise ValueError("LLM service (process_search_results) returned None.")

            if isinstance(llm_response_l1.get("usage"), dict):
                usage = llm_response_l1["usage"]
                stats["api_usage"]["openrouter_calls"] += 1
                stats["api_usage"]["openrouter_prompt_tokens"] += usage.get("prompt_tokens", 0)
                stats["api_usage"]["openrouter_completion_tokens"] += usage.get("completion_tokens", 0)
                stats["api_usage"]["openrouter_total_tokens"] += usage.get("total_tokens", 0)

            l1_classification = llm_response_l1.get("result", {})
            if "vendor_name" not in l1_classification: l1_classification["vendor_name"] = vendor_name
            # --- UPDATED: Ensure source is marked ---
            l1_classification["classification_source"] = "Search"
            # --- END UPDATED ---

            # Validate L1 result
            classification_not_possible_l1 = l1_classification.get("classification_not_possible", True)
            category_id_l1 = l1_classification.get("category_id", "N/A")
            is_valid_l1 = True

            if not classification_not_possible_l1 and valid_l1_category_ids:
                if category_id_l1 not in valid_l1_category_ids:
                    is_valid_l1 = False
                    logger.warning(f"Invalid L1 category ID '{category_id_l1}' from search LLM for '{vendor_name}'.", extra={"valid_ids_count": len(valid_l1_category_ids)})
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
                    "confidence": 0.0, "vendor_name": vendor_name, "notes": "LLM L1 Error",
                    # --- UPDATED: Add source ---
                    "classification_source": "Search"
                    # --- END UPDATED ---
                }
                logger.debug(f"search_and_classify_recursively: Releasing semaphore early due to L1 LLM exception for '{vendor_name}'.")
                return search_result_data # Stop if L1 classification failed

        # --- 3. Recursive Classification L2 up to target_level using Search Context ---
        current_parent_id = search_result_data["classification_l1"].get("category_id")
        classification_possible = not search_result_data["classification_l1"].get("classification_not_possible", True)

        # --- UPDATED: Loop up to target_level ---
        if classification_possible and current_parent_id and current_parent_id != "N/A" and target_level > 1:
            logger.info(f"search_and_classify_recursively: L1 successful ({current_parent_id}), proceeding to L2-{target_level} for {vendor_name} using search context.")
            for level in range(2, target_level + 1):
        # --- END UPDATED ---
                logger.debug(f"Attempting post-search Level {level} for {vendor_name}, parent {current_parent_id}")
                try:
                    logger.debug(f"search_and_classify_recursively: Calling process_batch (Level {level}) for '{vendor_name}' with search context.")
                    # Use process_batch for consistency in validation and structure
                    # Note: process_batch itself doesn't have an external timeout,
                    # but the overall search_and_classify_recursively task does (added in process_vendors)
                    batch_result_dict = await process_batch(
                        batch_data=[vendor_data], # Batch of one
                        level=level,
                        parent_category_id=current_parent_id,
                        taxonomy=taxonomy,
                        llm_service=llm_service,
                        stats=stats,
                        search_context=search_result_data # Pass the full search results as context
                    )
                    logger.debug(f"search_and_classify_recursively: process_batch (Level {level}) returned for '{vendor_name}'.")

                    level_result = batch_result_dict.get(vendor_name)
                    if level_result:
                        # --- UPDATED: Ensure source is marked (process_batch should already do this) ---
                        level_result["classification_source"] = "Search"
                        # --- END UPDATED ---
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
                                "confidence": 0.0, "vendor_name": vendor_name, "notes": f"L{level} Error",
                                # --- UPDATED: Add source ---
                                "classification_source": "Search"
                                # --- END UPDATED ---
                        }
                        break

                except Exception as recursive_err:
                    logger.error(f"search_and_classify_recursively: Error during post-search Level {level} for {vendor_name}", exc_info=True)
                    search_result_data[f"classification_l{level}"] = {
                            "classification_not_possible": True,
                            "classification_not_possible_reason": f"L{level} processing error: {str(recursive_err)[:100]}",
                            "confidence": 0.0, "vendor_name": vendor_name, "notes": f"L{level} Error",
                            # --- UPDATED: Add source ---
                            "classification_source": "Search"
                            # --- END UPDATED ---
                    }
                    break # Stop recursion on error
        else:
            logger.info(f"search_and_classify_recursively: L1 classification failed or not possible for {vendor_name}, or target level is 1. Skipping L2-{target_level}.")

        logger.info(f"search_and_classify_recursively: Finished for vendor", extra={"vendor": vendor_name})
        logger.debug(f"search_and_classify_recursively: Releasing semaphore for vendor '{vendor_name}'.")
        return search_result_data


@log_function_call(logger, include_args=False) # Keep args=False
async def process_vendors(
    unique_vendors_map: Dict[str, Dict[str, Any]], # Pass map containing full vendor data
    taxonomy: Taxonomy,
    results: Dict[str, Dict],
    stats: Dict[str, Any],
    job: Job,
    db: Session,
    llm_service: LLMService,
    search_service: SearchService,
    target_level: int # <<< ADDED target_level
):
    """
    Main orchestration function for processing vendors through the classification workflow (up to target_level),
    including recursive search for unknowns (up to target_level). Updates results and stats dictionaries in place.
    """
    unique_vendor_names = list(unique_vendors_map.keys()) # Get names from map
    total_unique_vendors = len(unique_vendor_names)
    processed_count = 0 # Count unique vendors processed in batches

    logger.info(f"Starting classification loop for {total_unique_vendors} unique vendors up to target Level {target_level}.")

    # --- Initial Hierarchical Classification (Levels 1 to target_level) ---
    vendors_to_process_next_level_names = set(unique_vendor_names) # Start with all unique vendor names for Level 1
    initial_l4_success_count = 0 # Track L4 for stats
    initial_l5_success_count = 0 # Track L5 for stats

    # --- UPDATED: Loop up to target_level ---
    for level in range(1, target_level + 1):
    # --- END UPDATED ---
        if not vendors_to_process_next_level_names:
            logger.info(f"No vendors remaining to process for Level {level}. Skipping.")
            continue # Skip level if no vendors need processing

        current_vendors_for_this_level = list(vendors_to_process_next_level_names) # Copy names for processing this level
        vendors_successfully_classified_in_level_names = set() # Track vendors that pass this level

        stage_enum_name = f"CLASSIFICATION_L{level}"
        if hasattr(ProcessingStage, stage_enum_name):
                job.current_stage = getattr(ProcessingStage, stage_enum_name).value
        else:
                logger.error(f"ProcessingStage enum does not have member '{stage_enum_name}'. Using default.")
                job.current_stage = ProcessingStage.PROCESSING.value # Fallback

        # Adjust progress calculation based on target_level (distribute 0.7 across target_level steps)
        progress_per_level = 0.7 / target_level if target_level > 0 else 0.7
        job.progress = min(0.8, 0.1 + ((level - 1) * progress_per_level))
        logger.info(f"[process_vendors] Committing status update before Level {level}: {job.status}, {job.current_stage}, {job.progress:.3f}")
        try:
            db.commit()
        except Exception as db_err:
            logger.error("Failed to commit status update before level processing", exc_info=True)
            db.rollback() # Rollback if commit fails

        logger.info(f"===== Starting Initial Level {level} Classification =====",
                    extra={ "vendors_to_process": len(current_vendors_for_this_level), "progress": job.progress })

        if level == 1:
            grouped_vendors_names = { None: current_vendors_for_this_level }
            logger.info(f"Level 1: Processing all {len(current_vendors_for_this_level)} vendors.")
        else:
            logger.info(f"Level {level}: Grouping {len(current_vendors_for_this_level)} vendors based on Level {level-1} results.")
            grouped_vendors_names = group_by_parent_category(results, level - 1, current_vendors_for_this_level)
            logger.info(f"Level {level}: Created {len(grouped_vendors_names)} groups for processing.")
            # Reduced verbosity:
            # for parent_id, names in grouped_vendors_names.items():
            #         logger.debug(f"  Group Parent ID '{parent_id}': {len(names)} vendors")

        processed_in_level_count = 0
        batch_counter_for_level = 0
        total_batches_for_level = sum( (len(names) + settings.BATCH_SIZE - 1) // settings.BATCH_SIZE for names in grouped_vendors_names.values() )
        logger.info(f"Level {level}: Total batches to process: {total_batches_for_level}")

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
                            extra={"batch_size": len(batch_data), "first_vendor": batch_names[0] if batch_names else 'N/A', "batch_num": batch_counter_for_level, "total_batches": total_batches_for_level})
                try:
                    # --- MODIFICATION: Added asyncio.wait_for ---
                    logger.debug(f"Calling process_batch with timeout {BATCH_PROCESSING_TIMEOUT}s")
                    batch_results = await asyncio.wait_for(
                        process_batch(batch_data, level, parent_category_id, taxonomy, llm_service, stats, search_context=None),
                        timeout=BATCH_PROCESSING_TIMEOUT
                    )
                    # --- END MODIFICATION ---
                    logger.debug(f"Level {level} batch {i+1} results received. Count: {len(batch_results)}.")

                    for vendor_name, classification in batch_results.items():
                        if vendor_name in results:
                            # --- UPDATED: Ensure source is set (process_batch should do this) ---
                            classification["classification_source"] = "Initial"
                            # --- END UPDATED ---
                            results[vendor_name][f"level{level}"] = classification
                            processed_in_level_count += 1

                            if not classification.get("classification_not_possible", True):
                                vendors_successfully_classified_in_level_names.add(vendor_name)
                                # logger.debug(f"Vendor '{vendor_name}' successfully classified at Level {level} (ID: {classification.get('category_id')}). Added for L{level+1}.") # Reduced verbosity
                                # Update stats based on the actual level completed
                                if level == 4:
                                    initial_l4_success_count += 1
                                    # logger.debug(f"Incremented initial_l4_success_count for {vendor_name}. Current L4 count: {initial_l4_success_count}") # Reduced verbosity
                                if level == 5:
                                    initial_l5_success_count += 1
                                    # logger.debug(f"Incremented initial_l5_success_count for {vendor_name}. Current L5 count: {initial_l5_success_count}") # Reduced verbosity
                            # else: # Reduced verbosity
                                # logger.debug(f"Vendor '{vendor_name}' not successfully classified at Level {level}. Reason: {classification.get('classification_not_possible_reason', 'Unknown')}. Will not proceed.")
                        else:
                                logger.warning(f"Vendor '{vendor_name}' from batch result not found in main results dictionary.", extra={"level": level})

                # --- MODIFICATION: Catch asyncio.TimeoutError specifically ---
                except asyncio.TimeoutError:
                    logger.error(f"Timeout processing Level {level} batch {i+1} for parent '{parent_category_id or 'None'}' after {BATCH_PROCESSING_TIMEOUT}s.",
                                 extra={"batch_vendors": batch_names})
                    # Mark all vendors in this batch as failed due to timeout
                    for vendor_name in batch_names:
                        if vendor_name in results:
                            # Only add error if not already processed (shouldn't happen with timeout, but defensive)
                            if f"level{level}" not in results[vendor_name]:
                                results[vendor_name][f"level{level}"] = {
                                    "category_id": "ERROR", "category_name": "ERROR", "confidence": 0.0,
                                    "classification_not_possible": True,
                                    "classification_not_possible_reason": f"Batch processing timed out after {BATCH_PROCESSING_TIMEOUT}s",
                                    "vendor_name": vendor_name,
                                    # --- UPDATED: Add source ---
                                    "classification_source": "Initial"
                                    # --- END UPDATED ---
                                }
                                processed_in_level_count += 1 # Count as processed (though failed)
                        else:
                            logger.warning(f"Vendor '{vendor_name}' from timed-out batch not found in main results dictionary.", extra={"level": level})
                # --- END MODIFICATION ---

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
                                        "vendor_name": vendor_name,
                                        # --- UPDATED: Add source ---
                                        "classification_source": "Initial"
                                        # --- END UPDATED ---
                                    }
                                    processed_in_level_count += 1
                            else:
                                logger.warning(f"Vendor '{vendor_name}' from failed batch not found in main results dictionary.", extra={"level": level})


                # Update progress within the level (based on batches completed)
                level_progress_fraction = batch_counter_for_level / total_batches_for_level if total_batches_for_level > 0 else 1
                job.progress = min(0.8, 0.1 + ((level - 1) * progress_per_level) + (progress_per_level * level_progress_fraction))
                try:
                    # logger.info(f"[process_vendors] Committing progress update after batch {batch_counter_for_level}/{total_batches_for_level} (Level {level}): {job.progress:.3f}") # Reduced verbosity
                    db.commit()
                except Exception as db_err:
                        logger.error("Failed to commit progress update during batch processing", exc_info=True)
                        db.rollback()

        logger.info(f"===== Initial Level {level} Classification Completed =====")
        logger.info(f"  Processed {processed_in_level_count} vendor results at Level {level}.")
        logger.info(f"  {len(vendors_successfully_classified_in_level_names)} vendors successfully classified and validated at Level {level}, proceeding to L{level+1}.")
        # logger.debug(f"Vendors proceeding to Level {level+1}: {list(vendors_successfully_classified_in_level_names)[:10]}...") # Reduced verbosity
        vendors_to_process_next_level_names = vendors_successfully_classified_in_level_names

    # --- End of Initial Level Loop ---
    logger.info(f"===== Finished Initial Hierarchical Classification Loop (Up to Level {target_level}) =====")

    # --- Identify vendors needing search (those not successfully classified at target_level) ---
    unknown_vendors_data_to_search = []
    for vendor_name in unique_vendor_names:
        is_classified_target = False
        if vendor_name in results:
            target_level_result = results[vendor_name].get(f"level{target_level}")
            if target_level_result and isinstance(target_level_result, dict) and not target_level_result.get("classification_not_possible", True):
                    # Also check for valid ID just in case
                    if target_level_result.get("category_id") and target_level_result.get("category_id") not in ["N/A", "ERROR"]:
                        is_classified_target = True

        if not is_classified_target:
            logger.debug(f"Vendor '{vendor_name}' did not initially reach/pass target Level {target_level} classification. Adding to search list.")
            if vendor_name in unique_vendors_map:
                unknown_vendors_data_to_search.append(unique_vendors_map[vendor_name])
            else:
                logger.warning(f"Vendor '{vendor_name}' marked for search but not found in unique_vendors_map.")
                unknown_vendors_data_to_search.append({'vendor_name': vendor_name}) # Add basic entry

    stats["classification_not_possible_initial"] = len(unknown_vendors_data_to_search)
    stats["successfully_classified_l4"] = initial_l4_success_count # Store initial L4 count
    stats["successfully_classified_l5"] = initial_l5_success_count # Store initial L5 count

    logger.info(f"Initial Classification Summary (Target L{target_level}): {total_unique_vendors - stats['classification_not_possible_initial']} reached target, {stats['classification_not_possible_initial']} did not.")
    if target_level >= 4: logger.info(f"  Ref: {initial_l4_success_count} reached L4 initially.")
    if target_level >= 5: logger.info(f"  Ref: {initial_l5_success_count} reached L5 initially.")

    # --- Search and Recursive Classification for Unknown Vendors (up to target_level) ---
    if unknown_vendors_data_to_search:
        job.current_stage = ProcessingStage.SEARCH.value
        job.progress = 0.8 # Progress after initial classification attempts
        logger.info(f"[process_vendors] Committing status update before Search stage: {job.status}, {job.current_stage}, {job.progress}")
        try:
            db.commit()
        except Exception as db_err:
            logger.error("Failed to commit status update before Search stage", exc_info=True)
            db.rollback()

        logger.info(f"===== Starting Search and Recursive Classification for {stats['classification_not_possible_initial']} Unclassified Vendors (Up to Level {target_level}) =====")

        stats["search_attempts"] = len(unknown_vendors_data_to_search)

        search_tasks = []
        if MAX_CONCURRENT_SEARCHES <= 0:
            logger.error(f"MAX_CONCURRENT_SEARCHES is {MAX_CONCURRENT_SEARCHES}. Cannot proceed with search tasks.")
            raise ValueError("MAX_CONCURRENT_SEARCHES must be positive.")
        search_semaphore = asyncio.Semaphore(MAX_CONCURRENT_SEARCHES)
        logger.info(f"Created search semaphore with concurrency limit: {MAX_CONCURRENT_SEARCHES}")

        # --- MODIFICATION: Added wrapper for search task timeout ---
        for vendor_data in unknown_vendors_data_to_search:
            # Define the coroutine to run with a timeout
            async def timed_search_classify_task(vd):
                vn = vd.get('vendor_name', 'UnknownVendor') # Get name early for logging
                try:
                    logger.debug(f"Calling search_and_classify_recursively for '{vn}' with timeout {SEARCH_CLASSIFY_TIMEOUT}s")
                    return await asyncio.wait_for(
                        search_and_classify_recursively(
                            vd, taxonomy, llm_service, search_service, stats, search_semaphore, target_level
                        ),
                        timeout=SEARCH_CLASSIFY_TIMEOUT
                    )
                except asyncio.TimeoutError:
                    logger.error(f"Timeout (> {SEARCH_CLASSIFY_TIMEOUT}s) during search_and_classify_recursively for vendor: {vn}")
                    # Return an error structure consistent with other failures in search_and_classify_recursively
                    return {
                        "vendor": vn, "search_query": f"{vn} company business type industry", "sources": [], "summary": None,
                        "error": f"Task timed out after {SEARCH_CLASSIFY_TIMEOUT} seconds.",
                        "classification_l1": {
                            "classification_not_possible": True, "classification_not_possible_reason": f"Search/classify task timed out (> {SEARCH_CLASSIFY_TIMEOUT}s)",
                            "confidence": 0.0, "vendor_name": vn, "notes": "Timeout",
                            # --- UPDATED: Add source ---
                            "classification_source": "Search"
                            # --- END UPDATED ---
                        },
                        # Ensure other levels are None
                        "classification_l2": None, "classification_l3": None, "classification_l4": None, "classification_l5": None
                    }
                except Exception as task_exc:
                    # Catch other exceptions within the task execution itself
                    logger.error(f"Exception during search_and_classify_recursively task for vendor {vn}", exc_info=task_exc)
                    return {
                         "vendor": vn, "search_query": f"{vn} company business type industry", "sources": [], "summary": None,
                         "error": f"Task execution error: {str(task_exc)}",
                         "classification_l1": {
                             "classification_not_possible": True, "classification_not_possible_reason": f"Search/classify task error: {str(task_exc)[:100]}",
                             "confidence": 0.0, "vendor_name": vn, "notes": "Task Error",
                             # --- UPDATED: Add source ---
                             "classification_source": "Search"
                             # --- END UPDATED ---
                         },
                         "classification_l2": None, "classification_l3": None, "classification_l4": None, "classification_l5": None
                    }

            # Create the task using the wrapper coroutine
            task = asyncio.create_task(timed_search_classify_task(vendor_data))
            search_tasks.append(task)
        # --- END MODIFICATION ---

        logger.info(f"Gathering results for {len(search_tasks)} search & recursive classification tasks...")
        logger.debug(f"Starting asyncio.gather for {len(search_tasks)} tasks.")
        gather_start_time = time.monotonic()
        # asyncio.gather will now return the result from timed_search_classify_task or any exception raised *by asyncio.create_task itself* (rare)
        # Keep return_exceptions=True for gather errors (e.g., task cancellation)
        search_and_recursive_results = await asyncio.gather(*search_tasks, return_exceptions=True)
        gather_duration = time.monotonic() - gather_start_time
        logger.info(f"Search & recursive classification tasks completed (asyncio.gather finished). Duration: {gather_duration:.3f}s")

        job.progress = 0.95 # Indicate search phase is done, before result processing/generation
        logger.info(f"[process_vendors] Committing progress update after search gather: {job.progress:.3f}")
        try:
            db.commit()
        except Exception as db_err:
            logger.error("Failed to commit progress update after search gather", exc_info=True)
            db.rollback()

        successful_l1_searches = 0
        successful_l5_searches = 0 # Track L5 success via search
        processed_search_count = 0

        logger.info(f"Processing {len(search_and_recursive_results)} results from search/recursive tasks.")
        # --- MODIFICATION: Updated result processing loop to handle timeout/error dicts ---
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
                # This catches errors from asyncio.gather itself (e.g., cancellation)
                logger.error(f"Error returned by asyncio.gather for vendor {vendor_name}", exc_info=result_or_exc)
                results[vendor_name]["search_results"] = {"error": f"Search task gather error: {str(result_or_exc)}"}
                # Mark L1 as failed
                logger.info(f"OVERWRITE_LOG: Search task gather failed for '{vendor_name}'. Marking L1 as failed.")
                results[vendor_name]["level1"] = {
                    "classification_not_possible": True,
                    "classification_not_possible_reason": f"Search task gather error: {str(result_or_exc)[:100]}",
                    "confidence": 0.0, "vendor_name": vendor_name, "notes": "Search Gather Error",
                    # --- UPDATED: Add source ---
                    "classification_source": "Search"
                    # --- END UPDATED ---
                }
                # Clear higher levels
                for lvl in range(2, target_level + 1): results[vendor_name].pop(f"level{lvl}", None)

            elif isinstance(result_or_exc, dict):
                 # This is the normal case OR the error dict returned by timed_search_classify_task
                 search_data = result_or_exc
                 results[vendor_name]["search_results"] = search_data # Store raw search info (including potential timeout/task error)

                 # Check if the dict indicates an error (timeout or task exception captured by the wrapper)
                 if search_data.get("error"):
                     logger.warning(f"Search/classify task for {vendor_name} failed or timed out. Error: {search_data['error']}")
                     # Ensure L1 reflects the failure (using the L1 data from the error dict)
                     l1_error_classification = search_data.get("classification_l1", {
                         "classification_not_possible": True, "classification_not_possible_reason": search_data['error'],
                         "confidence": 0.0, "vendor_name": vendor_name, "notes": "Task Failed/Timeout",
                         # --- UPDATED: Add source ---
                         "classification_source": "Search"
                         # --- END UPDATED ---
                     })
                     logger.info(f"OVERWRITE_LOG: Search task failed/timed out for '{vendor_name}'. Marking L1 as failed.")
                     results[vendor_name]["level1"] = l1_error_classification
                     # Clear higher levels
                     for lvl in range(2, target_level + 1):
                         if f"level{lvl}" in results[vendor_name]:
                             logger.info(f"OVERWRITE_LOG: Clearing L{lvl} for '{vendor_name}' due to search task failure/timeout.")
                             results[vendor_name].pop(f"level{lvl}", None)
                 else:
                     # Process successful result (original logic)
                     l1_classification = search_data.get("classification_l1")
                     if l1_classification:
                         logger.info(f"OVERWRITE_LOG: Processing successful search results for '{vendor_name}'. Target Level: {target_level}.")
                         results[vendor_name]["classified_via_search"] = True # Add flag

                         # Overwrite Level 1 unconditionally with the search result
                         logger.info(f"OVERWRITE_LOG: Overwriting L1 for '{vendor_name}' with search result. Possible: {not l1_classification.get('classification_not_possible', True)}")
                         results[vendor_name]["level1"] = l1_classification # This is the L1 overwrite

                         if not l1_classification.get("classification_not_possible", True):
                             successful_l1_searches += 1
                             logger.debug(f"Vendor '{vendor_name}' successfully classified at L1 via search (ID: {l1_classification.get('category_id')}).")

                             # Overwrite or clear higher levels based on recursive search results
                             for lvl in range(2, target_level + 1):
                                 search_lvl_key = f"classification_l{lvl}"
                                 main_lvl_key = f"level{lvl}"

                                 if search_lvl_key in search_data and search_data[search_lvl_key]:
                                     # Overwrite with the result from the recursive search
                                     lvl_result_data = search_data[search_lvl_key]
                                     logger.info(f"OVERWRITE_LOG: Overwriting L{lvl} for '{vendor_name}' with search result. Possible: {not lvl_result_data.get('classification_not_possible', True)}")
                                     results[vendor_name][main_lvl_key] = lvl_result_data

                                     # Track L5 success specifically if reached via search
                                     if lvl == 5 and not lvl_result_data.get("classification_not_possible", True):
                                         successful_l5_searches += 1
                                         logger.info(f"Vendor '{vendor_name}' reached L5 classification via search.")
                                 else:
                                     # If search path didn't yield a result for this level (stopped early/failed), remove any initial result
                                     if main_lvl_key in results[vendor_name]:
                                         logger.info(f"OVERWRITE_LOG: Clearing L{lvl} for '{vendor_name}' as search path did not provide a result for this level.")
                                         results[vendor_name].pop(main_lvl_key, None)
                                     else:
                                         logger.debug(f"OVERWRITE_LOG: No initial L{lvl} result to clear for '{vendor_name}' and no search result provided.")

                         else: # L1 classification via search failed or wasn't possible
                             reason = l1_classification.get("classification_not_possible_reason", "Search did not yield L1 classification")
                             logger.info(f"Vendor '{vendor_name}' could not be classified via search at L1. Reason: {reason}. Clearing higher levels.")
                             # Clear higher levels as L1 failed post-search
                             for lvl in range(2, target_level + 1):
                                 if f"level{lvl}" in results[vendor_name]:
                                     logger.info(f"OVERWRITE_LOG: Clearing L{lvl} for '{vendor_name}' due to L1 failure post-search.")
                                     results[vendor_name].pop(f"level{lvl}", None)
                     else:
                         # This case should ideally not happen if search_and_classify returns correctly, but handle defensively
                         logger.error(f"Search task for '{vendor_name}' returned dict but missing 'classification_l1'. Marking L1 as failed.")
                         results[vendor_name]["level1"] = { "classification_not_possible": True, "classification_not_possible_reason": "Internal search error (missing L1 result)", "confidence": 0.0, "vendor_name": vendor_name, "notes": "Search Error",
                                                            # --- UPDATED: Add source ---
                                                            "classification_source": "Search"
                                                            # --- END UPDATED ---
                                                            }
                         for lvl in range(2, target_level + 1): results[vendor_name].pop(f"level{lvl}", None)
            else: # Handle unexpected return type from gather
                logger.error(f"Unexpected result type for vendor {vendor_name} search task: {type(result_or_exc)}")
                results[vendor_name]["search_results"] = {"error": f"Unexpected search result type: {type(result_or_exc)}"}
                # Mark L1 as failed
                logger.info(f"OVERWRITE_LOG: Unexpected search result type for '{vendor_name}'. Marking L1 as failed.")
                results[vendor_name]["level1"] = { "classification_not_possible": True, "classification_not_possible_reason": "Internal search error (unexpected type)", "confidence": 0.0, "vendor_name": vendor_name, "notes": "Search Error",
                                                   # --- UPDATED: Add source ---
                                                   "classification_source": "Search"
                                                   # --- END UPDATED ---
                                                   }
                # Clear higher levels
                for lvl in range(2, target_level + 1):
                    if f"level{lvl}" in results[vendor_name]:
                        logger.info(f"OVERWRITE_LOG: Clearing L{lvl} for '{vendor_name}' due to unexpected search result type.")
                        results[vendor_name].pop(f"level{lvl}", None)
        # --- END MODIFICATION ---


        stats["search_successful_classifications_l1"] = successful_l1_searches
        stats["search_successful_classifications_l5"] = successful_l5_searches # Updated stat
        # Update total L5 success count (if target was >= 5)
        # Recalculate final L5 count based on the *final* state of results dict
        final_l5_success_count = 0
        if target_level >= 5:
            for vendor_name in unique_vendor_names:
                l5_res = results.get(vendor_name, {}).get("level5")
                if l5_res and isinstance(l5_res, dict) and not l5_res.get("classification_not_possible", True):
                    final_l5_success_count += 1
            stats["successfully_classified_l5"] = final_l5_success_count
            logger.info(f"Final recalculation: Total vendors successfully classified at L5: {stats['successfully_classified_l5']}")
        else:
            stats["successfully_classified_l5"] = 0 # Ensure it's 0 if target level was lower

        logger.info(f"===== Unknown Vendor Search & Recursive Classification Completed =====")
        logger.info(f"  Attempted search for {stats['search_attempts']} vendors.")
        logger.info(f"  Successfully classified {successful_l1_searches} at L1 via search.")
        if target_level >= 5:
            logger.info(f"  Successfully classified {successful_l5_searches} at L5 via search path.") # L5 count specifically from search path
            logger.info(f"  Total vendors successfully classified at L5 (final state): {stats['successfully_classified_l5']}")
    else:
        logger.info("No unknown vendors required search.")
        job.progress = 0.95 # Set progress high if search wasn't needed
        logger.info(f"[process_vendors] Committing status update as search was skipped: {job.progress:.3f}")
        try:
            db.commit()
        except Exception as db_err:
            logger.error("Failed to commit status update when skipping search", exc_info=True)
            db.rollback()
    logger.info("process_vendors function is returning.")
