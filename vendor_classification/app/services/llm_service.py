# app/services/llm_service.py
import httpx
import json
import re # <<< Added import for regex parsing
from typing import List, Dict, Any, Optional, Set # <<< Added Set
import logging # <<< Ensure logging is imported
import time
import uuid # <<< Added import
from tenacity import retry, stop_after_attempt, wait_exponential

from core.config import settings
# --- MODIFIED IMPORT ---
from models.taxonomy import Taxonomy, TaxonomyCategory # <<< Simplified import
# --- END MODIFIED IMPORT ---
from core.logging_config import get_logger, LogTimer, log_function_call, set_log_context, get_correlation_id # <-- Added get_correlation_id
from utils.log_utils import log_api_request, log_method # <<< Ensure log_method is imported if used

# Configure logger
logger = get_logger("vendor_classification.llm_service")
# --- ADDED LLM TRACE LOGGER ---
llm_trace_logger = logging.getLogger("llm_api_trace") # ENSURE NAME CONSISTENT
# --- END ADDED LLM TRACE LOGGER ---


# --- Helper function for JSON parsing (No changes needed here) ---
def _extract_json_from_response(response_content: str) -> Optional[Dict[str, Any]]:
    """
    Attempts to extract a JSON object from a string, handling common LLM response issues.

    Args:
        response_content: The raw string response from the LLM.

    Returns:
        A dictionary if JSON is successfully parsed, None otherwise.
    """
    if not response_content:
        logger.warning("Attempted to parse empty response content.")
        return None

    content = response_content.strip()

    # 1. Check for markdown code fences (```json ... ``` or ``` ... ```)
    match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", content, re.DOTALL | re.IGNORECASE)
    if match:
        content = match.group(1).strip()
        logger.debug("Extracted JSON content from within markdown code fences.")
    else:
        # 2. If no fences, try finding the first '{' and last '}'
        start_index = content.find('{')
        end_index = content.rfind('}')
        if start_index != -1 and end_index != -1 and end_index > start_index:
            potential_json = content[start_index:end_index+1]
            # Basic brace matching check
            if potential_json.count('{') == potential_json.count('}'):
                 content = potential_json
                 logger.debug("Extracted potential JSON content based on first '{' and last '}'.")
            else:
                 logger.debug("Found '{' and '}', but braces don't match. Proceeding with original stripped content.")
        else:
            logger.debug("No markdown fences found, and couldn't reliably find JSON object boundaries. Proceeding with original stripped content.")

    # 3. Attempt to parse the cleaned/extracted content
    try:
        parsed_json = json.loads(content)
        logger.debug("Successfully parsed JSON after cleaning/extraction.")
        return parsed_json
    except json.JSONDecodeError as e:
        logger.error("JSONDecodeError after cleaning/extraction attempt.",
                     exc_info=False,
                     extra={"error": str(e), "cleaned_content_preview": content[:500]})
        return None
    except Exception as e:
        logger.error("Unexpected error during JSON parsing after cleaning/extraction.",
                     exc_info=True,
                     extra={"cleaned_content_preview": content[:500]})
        return None
# --- END HELPER ---


class LLMService:
    """Service for interacting with OpenRouter API."""

    def __init__(self):
        """Initialize the LLM service."""
        logger.info("Initializing LLM service with OpenRouter")
        self.api_key = settings.OPENROUTER_API_KEY
        self.api_base = settings.OPENROUTER_API_BASE
        self.model = settings.OPENROUTER_MODEL
        logger.debug("LLM service initialized",
                    extra={"api_base": settings.OPENROUTER_API_BASE,
                          "model": settings.OPENROUTER_MODEL})
        if not self.api_key:
             logger.error("OpenRouter API key is missing!")

    @retry(stop=stop_after_attempt(settings.MAX_RETRIES), wait=wait_exponential(multiplier=1, min=settings.RETRY_DELAY, max=10))
    @log_function_call(logger, include_args=False)
    async def classify_batch(
        self,
        batch_data: List[Dict[str, Any]],
        level: int,
        taxonomy: Taxonomy,
        parent_category_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a batch of vendors to LLM for classification.
        """
        batch_names = [vd.get('vendor_name', f'Unknown_{i}') for i, vd in enumerate(batch_data)]
        logger.info(f"Classifying vendor batch",
                   extra={
                       "batch_size": len(batch_data),
                       "level": level,
                       "parent_category_id": parent_category_id
                   })
        set_log_context({"vendor_count": len(batch_data), "taxonomy_level": level})
        batch_id = str(uuid.uuid4())
        logger.debug(f"Generated batch ID", extra={"batch_id": batch_id})
        correlation_id = get_correlation_id()
        llm_trace_logger.debug(f"LLM_TRACE: Starting classify_batch (Batch ID: {batch_id}, Level: {level}, Parent: {parent_category_id})", extra={'correlation_id': correlation_id})

        if not self.api_key:
            logger.error("Cannot classify batch: OpenRouter API key is missing.")
            llm_trace_logger.error(f"LLM_TRACE: LLM API Error (Batch ID: {batch_id}): API key missing.", extra={'correlation_id': correlation_id})
            return {
                "result": {
                    "level": level, "batch_id": batch_id, "parent_category_id": parent_category_id,
                    "classifications": [
                        {
                            "vendor_name": vd.get('vendor_name', f'Unknown_{i}'), "category_id": "ERROR", "category_name": "ERROR",
                            "confidence": 0.0, "classification_not_possible": True,
                            "classification_not_possible_reason": "API key missing", "notes": "Failed due to missing API key configuration."
                        } for i, vd in enumerate(batch_data)
                    ]
                },
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            }

        logger.debug(f"Creating classification prompt")
        with LogTimer(logger, "Prompt creation", include_in_stats=True):
            prompt = self._create_classification_prompt(batch_data, level, taxonomy, parent_category_id, batch_id)
            prompt_length = len(prompt)
            logger.debug(f"Classification prompt created", extra={"prompt_length": prompt_length})
            llm_trace_logger.debug(f"LLM_TRACE: Generated Prompt (Batch ID: {batch_id}):\n-------\n{prompt}\n-------", extra={'correlation_id': correlation_id})

        headers = {
            "Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json",
            "HTTP-Referer": "naicsvendorclassification.com", "X-Title": "NAICS Vendor Classification"
        }
        payload = {
            "model": self.model,
            "messages": [
                # System message is now integrated into the user prompt structure
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1, "max_tokens": 2048, "top_p": 0.9,
            "frequency_penalty": 0, "presence_penalty": 0,
            "response_format": {"type": "json_object"} # Request JSON output mode
        }

        try:
            log_headers = {k: v for k, v in headers.items() if k.lower() != 'authorization'}
            log_headers['Authorization'] = 'Bearer [REDACTED]'
            llm_trace_logger.debug(f"LLM_TRACE: LLM Request Headers (Batch ID: {batch_id}):\n{json.dumps(log_headers, indent=2)}", extra={'correlation_id': correlation_id})
            llm_trace_logger.debug(f"LLM_TRACE: LLM Request Payload (Batch ID: {batch_id}):\n{json.dumps(payload, indent=2)}", extra={'correlation_id': correlation_id})
        except Exception as log_err:
            llm_trace_logger.warning(f"LLM_TRACE: Failed to log LLM request details (Batch ID: {batch_id}): {log_err}", extra={'correlation_id': correlation_id})

        response_data = None; raw_content = None; response = None
        try:
            logger.debug(f"Sending request to OpenRouter API")
            start_time = time.time()
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self.api_base}/chat/completions", json=payload, headers=headers, timeout=90.0)
                response.raise_for_status()
                response_data = response.json()
                if response_data and response_data.get("choices") and isinstance(response_data["choices"], list) and len(response_data["choices"]) > 0:
                     message = response_data["choices"][0].get("message")
                     if message and isinstance(message, dict): raw_content = message.get("content")
            api_duration = time.time() - start_time

            status_code = response.status_code if response else 'N/A'
            llm_trace_logger.debug(f"LLM_TRACE: LLM Raw Response (Batch ID: {batch_id}, Status: {status_code}, Duration: {api_duration:.3f}s):\n-------\n{raw_content or '[No Content Received]'}\n-------", extra={'correlation_id': correlation_id})

            usage = response_data.get("usage", {}) if response_data else {}
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)

            logger.info(f"OpenRouter API response received",
                       extra={
                           "duration": api_duration, "batch_id": batch_id, "level": level,
                           "openrouter_prompt_tokens": prompt_tokens,
                           "openrouter_completion_tokens": completion_tokens,
                           "openrouter_total_tokens": total_tokens
                       })

            logger.debug("Raw LLM response content received", extra={"content_preview": str(raw_content)[:500]})
            with LogTimer(logger, "JSON parsing and extraction", include_in_stats=True):
                result = _extract_json_from_response(raw_content)

            if result is None:
                llm_trace_logger.error(f"LLM_TRACE: LLM JSON Parse Error (Batch ID: {batch_id}). Raw content logged above.", extra={'correlation_id': correlation_id})
                raise ValueError(f"LLM response was not valid JSON or could not be extracted. Preview: {str(raw_content)[:200]}")

            try:
                 llm_trace_logger.debug(f"LLM_TRACE: LLM Parsed Response (Batch ID: {batch_id}):\n{json.dumps(result, indent=2)}", extra={'correlation_id': correlation_id})
            except Exception as log_err:
                 llm_trace_logger.warning(f"LLM_TRACE: Failed to log LLM parsed response (Batch ID: {batch_id}): {log_err}", extra={'correlation_id': correlation_id})

            response_batch_id = result.get("batch_id")
            if response_batch_id != batch_id:
                logger.warning(f"LLM response batch_id mismatch!",
                               extra={"expected_batch_id": batch_id, "received_batch_id": response_batch_id})
                result["batch_id_mismatch"] = True

            usage_data = { "prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens, "total_tokens": total_tokens }
            set_log_context({
                "openrouter_prompt_tokens": prompt_tokens, "openrouter_completion_tokens": completion_tokens, "openrouter_total_tokens": total_tokens
            })

            classification_count = len(result.get("classifications", []))
            successful_count = sum( 1 for c in result.get("classifications", []) if isinstance(c, dict) and not c.get("classification_not_possible", False) )
            logger.info(f"LLM Classification attempt completed for batch",
                       extra={
                           "level": level, "batch_id": batch_id, "total_in_batch": len(batch_data),
                           "classifications_in_response": classification_count, "successful_classifications": successful_count,
                           "failed_or_not_possible": classification_count - successful_count
                       })

            return { "result": result, "usage": usage_data }

        except httpx.HTTPStatusError as e:
             response_text = e.response.text[:500] if hasattr(e.response, 'text') else "[No Response Body]"
             status_code = e.response.status_code
             logger.error(f"HTTP error during LLM batch classification", exc_info=False,
                         extra={ "status_code": status_code, "response_text": response_text, "batch_id": batch_id, "level": level })
             llm_trace_logger.error(f"LLM_TRACE: LLM API HTTP Error (Batch ID: {batch_id}): Status={status_code}, Response='{response_text}'", exc_info=True, extra={'correlation_id': correlation_id})
             raise
        except httpx.RequestError as e:
             logger.error(f"Network error during LLM batch classification", exc_info=False,
                         extra={ "error_details": str(e), "batch_id": batch_id, "level": level })
             llm_trace_logger.error(f"LLM_TRACE: LLM API Network Error (Batch ID: {batch_id}): {e}", exc_info=True, extra={'correlation_id': correlation_id})
             raise
        except Exception as e:
            error_context = { "batch_size": len(batch_data), "level": level, "parent_category_id": parent_category_id, "error": str(e), "model": self.model, "batch_id": batch_id }
            logger.error(f"Unexpected error during LLM batch classification", exc_info=True, extra=error_context)
            llm_trace_logger.error(f"LLM_TRACE: LLM Unexpected Error (Batch ID: {batch_id}): {e}", exc_info=True, extra={'correlation_id': correlation_id})
            raise

    @retry(stop=stop_after_attempt(settings.MAX_RETRIES), wait=wait_exponential(multiplier=1, min=settings.RETRY_DELAY, max=10))
    @log_function_call(logger, include_args=False)
    async def process_search_results(
        self,
        vendor_data: Dict[str, Any],
        search_results: Dict[str, Any],
        taxonomy: Taxonomy
    ) -> Dict[str, Any]:
        """
        Process search results to determine classification.
        """
        vendor_name = vendor_data.get('vendor_name', 'UnknownVendor')
        logger.info(f"Processing search results for vendor classification",
                   extra={ "vendor": vendor_name, "source_count": len(search_results.get("sources", [])) })
        set_log_context({"vendor": vendor_name})
        attempt_id = str(uuid.uuid4())
        logger.debug(f"Generated search processing attempt ID", extra={"attempt_id": attempt_id})
        correlation_id = get_correlation_id()
        llm_trace_logger.debug(f"LLM_TRACE: Starting process_search_results (Attempt ID: {attempt_id}, Vendor: {vendor_name})", extra={'correlation_id': correlation_id})

        if not self.api_key:
            logger.error("Cannot process search results: OpenRouter API key is missing.")
            llm_trace_logger.error(f"LLM_TRACE: LLM API Error (Attempt ID: {attempt_id}): API key missing.", extra={'correlation_id': correlation_id})
            return {
                "result": { "vendor_name": vendor_name, "category_id": "ERROR", "category_name": "ERROR", "confidence": 0.0, "classification_not_possible": True, "classification_not_possible_reason": "API key missing", "notes": "" },
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            }

        with LogTimer(logger, "Search prompt creation", include_in_stats=True):
            prompt = self._create_search_results_prompt(vendor_data, search_results, taxonomy, attempt_id) # Pass attempt_id
            prompt_length = len(prompt)
            logger.debug(f"Search results prompt created", extra={"prompt_length": prompt_length})
            llm_trace_logger.debug(f"LLM_TRACE: Generated Search Prompt (Attempt ID: {attempt_id}):\n-------\n{prompt}\n-------", extra={'correlation_id': correlation_id})

        headers = {
            "Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json",
            "HTTP-Referer": "naicsvendorclassification.com", "X-Title": "NAICS Vendor Classification"
        }
        payload = {
            "model": self.model,
            "messages": [
                # System message is now integrated into the user prompt structure
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1, "max_tokens": 1024, "top_p": 0.9,
            "frequency_penalty": 0, "presence_penalty": 0,
            "response_format": {"type": "json_object"} # Request JSON output mode
        }

        try:
            log_headers = {k: v for k, v in headers.items() if k.lower() != 'authorization'}
            log_headers['Authorization'] = 'Bearer [REDACTED]'
            llm_trace_logger.debug(f"LLM_TRACE: LLM Request Headers (Attempt ID: {attempt_id}):\n{json.dumps(log_headers, indent=2)}", extra={'correlation_id': correlation_id})
            llm_trace_logger.debug(f"LLM_TRACE: LLM Request Payload (Attempt ID: {attempt_id}):\n{json.dumps(payload, indent=2)}", extra={'correlation_id': correlation_id})
        except Exception as log_err:
            llm_trace_logger.warning(f"LLM_TRACE: Failed to log LLM request details (Attempt ID: {attempt_id}): {log_err}", extra={'correlation_id': correlation_id})

        response_data = None; raw_content = None; response = None
        try:
            logger.debug(f"Sending search results to OpenRouter API")
            start_time = time.time()
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self.api_base}/chat/completions", json=payload, headers=headers, timeout=60.0)
                response.raise_for_status()
                response_data = response.json()
                if response_data and response_data.get("choices") and isinstance(response_data["choices"], list) and len(response_data["choices"]) > 0:
                     message = response_data["choices"][0].get("message")
                     if message and isinstance(message, dict): raw_content = message.get("content")
            api_duration = time.time() - start_time

            status_code = response.status_code if response else 'N/A'
            llm_trace_logger.debug(f"LLM_TRACE: LLM Raw Response (Attempt ID: {attempt_id}, Status: {status_code}, Duration: {api_duration:.3f}s):\n-------\n{raw_content or '[No Content Received]'}\n-------", extra={'correlation_id': correlation_id})

            usage = response_data.get("usage", {}) if response_data else {}
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)

            logger.info(f"OpenRouter API response received for search results",
                       extra={ "duration": api_duration, "vendor": vendor_name, "openrouter_prompt_tokens": prompt_tokens, "openrouter_completion_tokens": completion_tokens, "openrouter_total_tokens": total_tokens, "attempt_id": attempt_id })

            logger.debug("Raw LLM response content received (search)", extra={"content_preview": str(raw_content)[:500]})
            with LogTimer(logger, "JSON parsing and extraction (search)", include_in_stats=True):
                result = _extract_json_from_response(raw_content)

            if result is None:
                llm_trace_logger.error(f"LLM_TRACE: LLM JSON Parse Error (Attempt ID: {attempt_id}). Raw content logged above.", extra={'correlation_id': correlation_id})
                raise ValueError(f"LLM response after search was not valid JSON or could not be extracted. Preview: {str(raw_content)[:200]}")

            try:
                 llm_trace_logger.debug(f"LLM_TRACE: LLM Parsed Response (Attempt ID: {attempt_id}):\n{json.dumps(result, indent=2)}", extra={'correlation_id': correlation_id})
            except Exception as log_err:
                 llm_trace_logger.warning(f"LLM_TRACE: Failed to log LLM parsed response (Attempt ID: {attempt_id}): {log_err}", extra={'correlation_id': correlation_id})

            response_vendor = result.get("vendor_name")
            if response_vendor != vendor_name:
                logger.warning(f"LLM search response vendor name mismatch!",
                               extra={"expected_vendor": vendor_name, "received_vendor": response_vendor})
                result["vendor_name"] = vendor_name # Ensure the correct vendor name is in the result

            usage_data = { "prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens, "total_tokens": total_tokens }
            set_log_context({ "openrouter_prompt_tokens": prompt_tokens, "openrouter_completion_tokens": completion_tokens, "openrouter_total_tokens": total_tokens })

            return { "result": result, "usage": usage_data }

        except httpx.HTTPStatusError as e:
             response_text = e.response.text[:500] if hasattr(e.response, 'text') else "[No Response Body]"
             status_code = e.response.status_code
             logger.error(f"HTTP error during search result processing", exc_info=False,
                         extra={ "status_code": status_code, "response_text": response_text, "vendor": vendor_name, "attempt_id": attempt_id })
             llm_trace_logger.error(f"LLM_TRACE: LLM API HTTP Error (Attempt ID: {attempt_id}): Status={status_code}, Response='{response_text}'", exc_info=True, extra={'correlation_id': correlation_id})
             raise
        except httpx.RequestError as e:
             logger.error(f"Network error during search result processing", exc_info=False,
                         extra={ "error_details": str(e), "vendor": vendor_name, "attempt_id": attempt_id })
             llm_trace_logger.error(f"LLM_TRACE: LLM API Network Error (Attempt ID: {attempt_id}): {e}", exc_info=True, extra={'correlation_id': correlation_id})
             raise
        except Exception as e:
            error_context = { "vendor": vendor_name, "error": str(e), "model": self.model, "attempt_id": attempt_id }
            logger.error(f"Unexpected error during search result processing", exc_info=True, extra=error_context)
            llm_trace_logger.error(f"LLM_TRACE: LLM Unexpected Error (Attempt ID: {attempt_id}): {e}", exc_info=True, extra={'correlation_id': correlation_id})
            raise

    # --- UPDATED PROMPT GENERATION METHOD ---
    @log_function_call(logger, include_args=False)
    def _create_classification_prompt(
        self,
        vendors_data: List[Dict[str, Any]],
        level: int,
        taxonomy: Taxonomy,
        parent_category_id: Optional[str] = None, # <<< FIX: Use parent_category_id here
        batch_id: str = "unknown-batch"
    ) -> str:
        """
        Create an appropriate prompt for the current classification level,
        following the structured guidance.
        """
        logger.debug(f"_create_classification_prompt: Generating prompt for Level {level}",
                    extra={ "vendor_count": len(vendors_data), "parent_category_id": parent_category_id, "batch_id": batch_id })

        # --- Build Vendor Data Section ---
        vendor_data_xml = "<vendor_data>\n"
        for i, vendor_entry in enumerate(vendors_data):
            vendor_name = vendor_entry.get('vendor_name', f'UnknownVendor_{i}')
            example = vendor_entry.get('example')
            address = vendor_entry.get('vendor_address')
            website = vendor_entry.get('vendor_website')
            internal_cat = vendor_entry.get('internal_category')
            parent_co = vendor_entry.get('parent_company')
            spend_cat = vendor_entry.get('spend_category')

            vendor_data_xml += f"  <vendor index=\"{i+1}\">\n"
            vendor_data_xml += f"    <name>{vendor_name}</name>\n"
            if example: vendor_data_xml += f"    <example_goods_services>{str(example)[:200]}</example_goods_services>\n" # Limit length
            if address: vendor_data_xml += f"    <address>{str(address)[:200]}</address>\n"
            if website: vendor_data_xml += f"    <website>{str(website)[:100]}</website>\n"
            if internal_cat: vendor_data_xml += f"    <internal_category>{str(internal_cat)[:100]}</internal_category>\n"
            if parent_co: vendor_data_xml += f"    <parent_company>{str(parent_co)[:100]}</parent_company>\n"
            if spend_cat: vendor_data_xml += f"    <spend_category>{str(spend_cat)[:100]}</spend_category>\n"
            vendor_data_xml += f"  </vendor>\n"
        vendor_data_xml += "</vendor_data>"

        # --- Get Category Options ---
        categories: List[TaxonomyCategory] = []
        parent_category_name = "N/A"
        category_lookup_successful = True
        try:
            # --- ADDED LOGGING ---
            logger.debug(f"_create_classification_prompt: Retrieving categories via taxonomy methods for Level {level}, Parent: {parent_category_id}")
            # --- END ADDED LOGGING ---
            if level == 1:
                categories = taxonomy.get_level1_categories()
            elif parent_category_id: # <<< FIX: Use parent_category_id
                if level == 2:
                    categories = taxonomy.get_level2_categories(parent_category_id) # <<< FIX: Use parent_category_id
                    parent_obj = taxonomy.categories.get(parent_category_id) # <<< FIX: Use parent_category_id
                    if parent_obj: parent_category_name = parent_obj.name
                elif level == 3:
                    categories = taxonomy.get_level3_categories(parent_category_id) # <<< FIX: Use parent_category_id
                    # --- Adjusted logic to find parent name based on potential dotted ID ---
                    l1_id = None; l2_id = None
                    id_parts = parent_category_id.split('.') # <<< FIX: Use parent_category_id
                    if len(id_parts) >= 2:
                         l1_id, l2_id = id_parts[0], id_parts[1]
                    elif len(id_parts) == 1: # Handle case where only L2 ID might be passed (check taxonomy methods)
                         # Need to find L1 parent
                         for l1_key, l1_node in taxonomy.categories.items():
                              if parent_category_id in getattr(l1_node, 'children', {}):
                                   l1_id = l1_key
                                   l2_id = parent_category_id
                                   break
                    if l1_id and l2_id:
                        parent_obj = taxonomy.categories.get(l1_id, {}).children.get(l2_id)
                        if parent_obj: parent_category_name = parent_obj.name
                    # --- End Adjusted logic ---
                elif level == 4:
                    categories = taxonomy.get_level4_categories(parent_category_id) # <<< FIX: Use parent_category_id
                     # --- Adjusted logic to find parent name based on potential dotted ID ---
                    l1_id = None; l2_id = None; l3_id = None
                    id_parts = parent_category_id.split('.') # <<< FIX: Use parent_category_id
                    if len(id_parts) >= 3:
                         l1_id, l2_id, l3_id = id_parts[0], id_parts[1], id_parts[2]
                    elif len(id_parts) == 1: # Handle case where only L3 ID might be passed
                         # Need to find L1/L2 parents
                         found_l3_parent = False
                         for l1k, l1n in taxonomy.categories.items():
                             for l2k, l2n in getattr(l1n, 'children', {}).items():
                                 if parent_category_id in getattr(l2n, 'children', {}):
                                     l1_id = l1k
                                     l2_id = l2k
                                     l3_id = parent_category_id
                                     found_l3_parent = True
                                     break
                             if found_l3_parent: break
                    if l1_id and l2_id and l3_id:
                        parent_obj = taxonomy.categories.get(l1_id, {}).children.get(l2_id, {}).children.get(l3_id)
                        if parent_obj: parent_category_name = parent_obj.name
                    # --- End Adjusted logic ---
            else:
                logger.error(f"Parent category ID is required for level {level} prompt generation but was not provided.")
                category_lookup_successful = False

            # --- ADDED LOGGING ---
            if not categories and level > 1 and parent_category_id:
                 logger.warning(f"No subcategories found for Level {level}, Parent '{parent_category_id}'.")
                 category_lookup_successful = False # Treat as failure if no children found
            elif not categories and level == 1:
                 logger.error(f"No Level 1 categories found in taxonomy!")
                 category_lookup_successful = False
            # --- END ADDED LOGGING ---

            logger.debug(f"_create_classification_prompt: Retrieved {len(categories)} categories for Level {level}, Parent '{parent_category_id}' ('{parent_category_name}').")

        except Exception as e:
            logger.error(f"Error retrieving categories for prompt (Level {level}, Parent: {parent_category_id})", exc_info=True) # <<< FIX: Use parent_category_id
            category_lookup_successful = False

        # --- Build Category Options Section ---
        category_options_xml = "<category_options>\n"
        if category_lookup_successful:
            category_options_xml += f"  <level>{level}</level>\n"
            if level > 1 and parent_category_id: # <<< FIX: Use parent_category_id
                category_options_xml += f"  <parent_id>{parent_category_id}</parent_id>\n" # <<< FIX: Use parent_category_id
                category_options_xml += f"  <parent_name>{parent_category_name}</parent_name>\n"
            category_options_xml += "  <categories>\n"
            for cat in categories:
                category_options_xml += f"    <category id=\"{cat.id}\" name=\"{cat.name}\"/>\n" # Omit description
            category_options_xml += "  </categories>\n"
        else:
            # Indicate failure to retrieve categories
            category_options_xml += f"  <error>Could not retrieve valid categories for Level {level}, Parent '{parent_category_id}'. Classification is not possible.</error>\n" # <<< FIX: Use parent_category_id
        category_options_xml += "</category_options>"

        # --- Define Output Format Section ---
        output_format_xml = f"""<output_format>
Respond *only* with a valid JSON object matching this exact schema. Do not include any text before or after the JSON object.

```json
{{
  "level": {level},
  "batch_id": "{batch_id}",
  "parent_category_id": {json.dumps(parent_category_id)}, 
  "classifications": [
    {{
      "vendor_name": "string", // Exact vendor name from input <vendor_data>
      "category_id": "string", // ID from <category_options> or "N/A" if not possible
      "category_name": "string", // Name corresponding to category_id or "N/A"
      "confidence": "float", // 0.0 to 1.0. MUST be 0.0 if classification_not_possible is true.
      "classification_not_possible": "boolean", // true if classification cannot be confidently made from options, false otherwise.
      "classification_not_possible_reason": "string | null", // Brief reason if true (e.g., "Ambiguous", "Insufficient info"), null if false.
      "notes": "string | null" // Optional brief justification or reasoning, especially if confidence is low or not possible.
    }}
    // ... one entry for EACH vendor in <vendor_data>
  ]
}}
```

**Example for Successful Classification:**
```json
  {{
    "vendor_name": "Acme Technologies Inc.",
    "category_id": "541511",
    "category_name": "Custom Computer Programming Services",
    "confidence": 0.95,
    "classification_not_possible": false,
    "classification_not_possible_reason": null,
    "notes": "Vendor name and example services clearly indicate custom software development."
  }}
```

**Example for Unsuccessful Classification:**
```json
  {{
    "vendor_name": "General Supplies Co.",
    "category_id": "N/A",
    "category_name": "N/A",
    "confidence": 0.0,
    "classification_not_possible": true,
    "classification_not_possible_reason": "Name too generic, no specific context provided.",
    "notes": "Could be wholesale, retail, or other based on name alone."
  }}
```
</output_format>"""

        # --- Assemble Final Prompt ---
        prompt = f"""
<role>You are a precise vendor classification expert using the NAICS taxonomy.</role>

<task>Classify each vendor provided in `<vendor_data>` into **ONE** appropriate NAICS category from the `<category_options>` for Level {level}. {f"Consider that these vendors belong to the parent category '{parent_category_id}: {parent_category_name}'. " if level > 1 and parent_category_id else ""}</task> 

<instructions>
1.  Analyze each vendor's details in `<vendor_data>`, including the name and any provided context (example goods/services, address, website, internal category, parent company, spend category).
2.  Compare the vendor's likely primary business activity against the available categories in `<category_options>`.
3.  Assign the **single most specific and appropriate** category ID and name from the list.
4.  Provide a confidence score (0.0 to 1.0).
5.  **CRITICAL:** If the vendor's primary activity is genuinely ambiguous, cannot be determined from the provided information, or does not fit well into *any* of the specific categories listed in `<category_options>`, **DO NOT GUESS**. Instead:
    *   Set `classification_not_possible` to `true`.
    *   Set `confidence` to `0.0`.
    *   Provide a brief `classification_not_possible_reason` (e.g., "Ambiguous name", "Insufficient information", "Generic activity within parent").
    *   Set `category_id` and `category_name` to "N/A".
6.  If classification *is* possible (`classification_not_possible: false`), ensure `confidence` is greater than 0.0 and `category_id` / `category_name` are populated correctly from `<category_options>`.
7.  Provide brief optional `notes` for reasoning, especially if confidence is low or classification was not possible.
8.  Ensure the `batch_id` in the final JSON output matches the `batch_id` specified in `<output_format>`.
9.  Ensure the output contains an entry for **every** vendor listed in `<vendor_data>`.
10. Respond *only* with the valid JSON object as specified in `<output_format>`. Do not include any introductory text, explanations, or apologies outside the JSON structure.
</instructions>

{vendor_data_xml}

{category_options_xml}

{output_format_xml}
"""
        # Handle the case where category lookup failed explicitly
        if not category_lookup_successful:
             prompt = f"""
<role>You are a precise vendor classification expert using the NAICS taxonomy.</role>

<task>Acknowledge that classification is not possible for the vendors in `<vendor_data>` at Level {level} because the necessary subcategories could not be provided.</task>

<instructions>
1. For **every** vendor listed in `<vendor_data>`, create a classification entry in the final JSON output.
2. In each entry, set `classification_not_possible` to `true`.
3. Set `confidence` to `0.0`.
4. Set `category_id` and `category_name` to "N/A".
5. Set `classification_not_possible_reason` to "No subcategories defined or retrievable for parent {parent_category_id} at Level {level}". 
6. Ensure the `batch_id` in the final JSON output matches the `batch_id` specified in `<output_format>`.
7. Respond *only* with the valid JSON object as specified in `<output_format>`. Do not include any introductory text, explanations, or apologies outside the JSON structure.
</instructions>

{vendor_data_xml}

{category_options_xml} 

{output_format_xml} 
"""

        return prompt

    # --- UPDATED SEARCH RESULTS PROMPT GENERATION METHOD ---
    # FIX: Added the colon and corrected indentation for line 571 to address potential syntax error
    @log_function_call(logger, include_args=False)
    def _create_search_results_prompt(
        self,
        vendor_data: Dict[str, Any],
        search_results: Dict[str, Any],
        taxonomy: Taxonomy,
        attempt_id: str = "unknown-attempt" # Added attempt ID
    ) -> str:
        """
        Create a prompt for processing search results, following the structured guidance.
        """
        # --- ADDED LOGGING ---
        logger.debug(f"Entering _create_search_results_prompt for vendor: {vendor_data.get('vendor_name', 'Unknown')}")
        # --- END ADDED LOGGING ---
        vendor_name = vendor_data.get('vendor_name', 'UnknownVendor')
        example = vendor_data.get('example')
        address = vendor_data.get('vendor_address')
        website = vendor_data.get('vendor_website')
        internal_cat = vendor_data.get('internal_category')
        parent_co = vendor_data.get('parent_company')
        spend_cat = vendor_data.get('spend_category')

        logger.debug(f"Creating search results prompt for vendor",
                    extra={ "vendor": vendor_name, "source_count": len(search_results.get("sources", [])), "attempt_id": attempt_id })

        # --- Build Vendor Data Section ---
        vendor_data_xml = "<vendor_data>\n"
        vendor_data_xml += f"  <name>{vendor_name}</name>\n"
        if example: vendor_data_xml += f"  <example_goods_services>{str(example)[:300]}</example_goods_services>\n"
        if address: vendor_data_xml += f"  <address>{str(address)[:200]}</address>\n"
        if website: vendor_data_xml += f"  <website>{str(website)[:100]}</website>\n"
        if internal_cat: vendor_data_xml += f"  <internal_category>{str(internal_cat)[:100]}</internal_category>\n"
        if parent_co: vendor_data_xml += f"  <parent_company>{str(parent_co)[:100]}</parent_company>\n"
        if spend_cat: vendor_data_xml += f"  <spend_category>{str(spend_cat)[:100]}</spend_category>\n"
        vendor_data_xml += "</vendor_data>"

        # --- Build Search Results Section ---
        search_results_xml = "<search_results>\n"
        sources = search_results.get("sources")
        if sources and isinstance(sources, list):
            search_results_xml += "  <sources>\n"
            for i, source in enumerate(sources):
                content_preview = str(source.get('content', ''))[:1500] # Limit length
                search_results_xml += f"    <source index=\"{i+1}\">\n"
                search_results_xml += f"      <title>{source.get('title', 'N/A')}</title>\n"
                search_results_xml += f"      <url>{source.get('url', 'N/A')}</url>\n"
                search_results_xml += f"      <content_snippet>{content_preview}...</content_snippet>\n"
                search_results_xml += f"    </source>\n"
            search_results_xml += "  </sources>\n"
        else:
            search_results_xml += "  <message>No relevant search results sources were found.</message>\n"

        summary_str = search_results.get("summary", "")
        if summary_str:
            search_results_xml += f"  <summary>{summary_str}</summary>\n"
        search_results_xml += "</search_results>"

        # --- Get Level 1 Category Options ---
        categories = taxonomy.get_level1_categories()
        category_options_xml = "<category_options>\n"
        category_options_xml += "  <level>1</level>\n"
        category_options_xml += "  <categories>\n"
        for cat in categories:
            category_options_xml += f"    <category id=\"{cat.id}\" name=\"{cat.name}\"/>\n" # Omit description
        category_options_xml += "  </categories>\n"
        category_options_xml += "</category_options>"

        # --- Define Output Format Section ---
        # Note: Added attempt_id to the output schema description for traceability if needed
        output_format_xml = f"""<output_format>
Respond *only* with a valid JSON object matching this exact schema. Do not include any text before or after the JSON object.

```json
{{
  "attempt_id": "{attempt_id}", // ID for this specific attempt
  "vendor_name": "{vendor_name}", // Exact vendor name from input <vendor_data>
  "category_id": "string", // Level 1 ID from <category_options> or "N/A" if not possible
  "category_name": "string", // Name corresponding to category_id or "N/A"
  "confidence": "float", // 0.0 to 1.0. MUST be 0.0 if classification_not_possible is true.
  "classification_not_possible": "boolean", // true if classification cannot be confidently made from options based *only* on provided info, false otherwise.
  "classification_not_possible_reason": "string | null", // Brief reason if true (e.g., "Insufficient info", "Conflicting sources"), null if false.
  "notes": "string | null" // Brief explanation of decision based *only* on the provided context and search results. Reference specific sources if helpful.
}}
```

**Example for Successful Classification:**
```json
{{
  "attempt_id": "some-uuid-attempt-id",
  "vendor_name": "WebSearch Widgets LLC",
  "category_id": "54",
  "category_name": "Professional, Scientific, and Technical Services",
  "confidence": 0.85,
  "classification_not_possible": false,
  "classification_not_possible_reason": null,
  "notes": "Sources mention software consulting and technical services, aligning with Sector 54. Website context confirms."
}}
```

**Example for Unsuccessful Classification:**
```json
{{
  "attempt_id": "some-uuid-attempt-id",
  "vendor_name": "Ambiguous Corp",
  "category_id": "N/A",
  "category_name": "N/A",
  "confidence": 0.0,
  "classification_not_possible": true,
  "classification_not_possible_reason": "Search results conflicting (mention retail and manufacturing), insufficient detail to determine primary L1 activity.",
  "notes": "Source 1 suggests retail, Source 3 suggests manufacturing. No clear primary activity."
}}
```
</output_format>"""

        # --- Assemble Final Prompt ---
        prompt = f"""
<role>You are a precise vendor classification expert using the NAICS taxonomy.</role>

<task>Analyze the vendor details in `<vendor_data>` and the web search information in `<search_results>` to classify the vendor into **ONE** appropriate Level 1 NAICS category from `<category_options>`. Base your decision *only* on the provided information.</task>

<instructions>
1.  Carefully review the vendor details in `<vendor_data>` (name, examples, address, website, internal category, parent company, spend category).
2.  Carefully review the search results in `<search_results>` (sources and summary).
3.  Synthesize all provided information to understand the vendor's **primary business activity**. Focus on what the company *does*, not just what it might resell.
4.  Compare this primary activity against the Level 1 categories listed in `<category_options>`.
5.  Assign the **single most appropriate** Level 1 category ID and name.
6.  Provide a confidence score (0.0 to 1.0) based on the clarity, consistency, and relevance of the provided information.
7.  **CRITICAL:** If the provided information (vendor data + search results) is insufficient, contradictory, irrelevant, focuses only on products sold rather than the business activity, or does not allow for confident determination of the primary business activity *from the listed L1 categories*, **DO NOT GUESS**. Instead:
    *   Set `classification_not_possible` to `true`.
    *   Set `confidence` to `0.0`.
    *   Provide a brief `classification_not_possible_reason` (e.g., "Insufficient information", "Conflicting sources", "Unclear primary activity from sources").
    *   Set `category_id` and `category_name` to "N/A".
8.  If classification *is* possible (`classification_not_possible: false`), ensure `confidence` is greater than 0.0 and `category_id` / `category_name` are populated correctly from `<category_options>`.
9.  Provide brief optional `notes` explaining your reasoning, referencing specific details from `<vendor_data>` or `<search_results>` (e.g., "Source 2 mentions...", "Website context indicates...").
10. Ensure the `vendor_name` in the final JSON output matches the name in `<vendor_data>`.
11. Respond *only* with the valid JSON object as specified in `<output_format>`. Do not include any introductory text, explanations, or apologies outside the JSON structure.
</instructions>

{vendor_data_xml}

{search_results_xml}

{category_options_xml}

{output_format_xml}
"""
        return prompt
    # --- END UPDATED ---