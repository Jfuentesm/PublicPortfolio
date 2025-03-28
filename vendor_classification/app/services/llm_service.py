# app/services/llm_service.py
import httpx
import json
import re # <<< Added import for regex parsing
from typing import List, Dict, Any, Optional
import logging # <<< Ensure logging is imported
import time
import uuid # <<< Added import
from tenacity import retry, stop_after_attempt, wait_exponential

from core.config import settings
from models.taxonomy import Taxonomy, TaxonomyCategory # <<< Added TaxonomyCategory
from core.logging_config import get_logger, LogTimer, log_function_call, set_log_context, get_correlation_id # <-- Added get_correlation_id
from utils.log_utils import log_api_request, log_method # <<< Ensure log_method is imported if used

# Configure logger
logger = get_logger("vendor_classification.llm_service")
# --- ADDED LLM TRACE LOGGER ---
llm_trace_logger = get_logger("llm_api_trace")
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
             # Consider raising an error if the key is essential for operation
             # raise ValueError("OpenRouter API key not configured")


    @retry(stop=stop_after_attempt(settings.MAX_RETRIES), wait=wait_exponential(multiplier=1, min=settings.RETRY_DELAY, max=10))
    @log_function_call(logger, include_args=False) # Keep False to avoid logging potentially large batches
    # @log_api_request("openrouter") # <-- REMOVED decorator to use manual trace logging below
    async def classify_batch(
        self,
        batch_data: List[Dict[str, Any]], # Pass list of dicts including optional fields
        level: int,
        taxonomy: Taxonomy,
        parent_category_id: Optional[str] = None # Renamed for clarity
    ) -> Dict[str, Any]:
        """
        Send a batch of vendors to LLM for classification.

        Args:
            batch_data: List of vendor dictionaries, each potentially containing
                        'vendor_name', 'example', 'vendor_address',
                        'vendor_website', 'internal_category', 'parent_company', 'spend_category'.
            level: Classification level (1-4)
            taxonomy: Taxonomy data
            parent_category_id: Parent category ID (required for levels 2-4)

        Returns:
            Classification results and API usage data.
        """
        batch_names = [vd.get('vendor_name', f'Unknown_{i}') for i, vd in enumerate(batch_data)] # For logging
        logger.info(f"Classifying vendor batch",
                   extra={
                       "batch_size": len(batch_data),
                       "level": level,
                       "parent_category_id": parent_category_id
                   })
        set_log_context({"vendor_count": len(batch_data), "taxonomy_level": level})
        batch_id = str(uuid.uuid4()) # Use UUID for uniqueness
        logger.debug(f"Generated batch ID", extra={"batch_id": batch_id})
        # --- ADDED LLM TRACE LOGGING ---
        correlation_id = get_correlation_id() # Get current correlation ID for logging
        llm_trace_logger.debug(f"Starting classify_batch (Batch ID: {batch_id}, Level: {level})", extra={'correlation_id': correlation_id})
        # --- END ADDED LLM TRACE LOGGING ---

        if not self.api_key:
            logger.error("Cannot classify batch: OpenRouter API key is missing.")
            # --- ADDED LLM TRACE LOGGING ---
            llm_trace_logger.error(f"LLM API Error (Batch ID: {batch_id}): API key missing.", extra={'correlation_id': correlation_id})
            # --- END ADDED LLM TRACE LOGGING ---
            # Return an error structure consistent with expected output but indicating failure
            return {
                "result": {
                    "level": level,
                    "batch_id": batch_id,
                    "parent_category_id": parent_category_id,
                    "classifications": [
                        {
                            "vendor_name": vd.get('vendor_name', f'Unknown_{i}'),
                            "category_id": "ERROR", "category_name": "ERROR",
                            "confidence": 0.0, "classification_not_possible": True,
                            "classification_not_possible_reason": "API key missing"
                        } for i, vd in enumerate(batch_data)
                    ]
                },
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            }

        # --- UPDATED PROMPT CREATION ---
        logger.debug(f"Creating classification prompt")
        with LogTimer(logger, "Prompt creation", include_in_stats=True):
            prompt = self._create_classification_prompt(batch_data, level, taxonomy, parent_category_id, batch_id)
            prompt_length = len(prompt)
            logger.debug(f"Classification prompt created",
                        extra={"prompt_length": prompt_length})
        # --- END UPDATED PROMPT CREATION ---

        # --- Prepare API Call ---
        headers = {
            "Authorization": f"Bearer {self.api_key}", # Key will be sent, but not logged in trace
            "Content-Type": "application/json",
            "HTTP-Referer": "naicsvendorclassification.com",
            "X-Title": "NAICS Vendor Classification"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a precise vendor classification expert using the NAICS taxonomy. Adhere strictly to the provided categories and JSON output format. Use the optional example goods/services purchased, address, website, internal category, parent company, and spend category for context if provided. Do not guess if unsure. Ensure the `batch_id` in the output matches the one provided in the prompt."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 2048,
            "top_p": 0.9,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "response_format": {"type": "json_object"}
        }

        # --- ADDED LLM TRACE LOGGING: Request ---
        try:
            # Log headers without API key
            log_headers = {k: v for k, v in headers.items() if k.lower() != 'authorization'}
            log_headers['Authorization'] = 'Bearer [REDACTED]'
            llm_trace_logger.debug(f"LLM Request Headers (Batch ID: {batch_id}):\n{json.dumps(log_headers, indent=2)}", extra={'correlation_id': correlation_id})
            llm_trace_logger.debug(f"LLM Request Payload (Batch ID: {batch_id}):\n{json.dumps(payload, indent=2)}", extra={'correlation_id': correlation_id})
        except Exception as log_err:
            llm_trace_logger.warning(f"Failed to log LLM request details (Batch ID: {batch_id}): {log_err}", extra={'correlation_id': correlation_id})
        # --- END ADDED LLM TRACE LOGGING: Request ---

        # Call OpenRouter API
        try:
            logger.debug(f"Sending request to OpenRouter API")
            start_time = time.time()

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=90.0 # Increased timeout
                )
                response.raise_for_status() # Raise HTTPStatusError for bad responses (4xx or 5xx)
                response_data = response.json()
                raw_content = response_data["choices"][0]["message"]["content"] # Get raw content string

            api_duration = time.time() - start_time

            # --- ADDED LLM TRACE LOGGING: Raw Response ---
            llm_trace_logger.debug(f"LLM Raw Response (Batch ID: {batch_id}, Status: {response.status_code}, Duration: {api_duration:.3f}s):\n{raw_content}", extra={'correlation_id': correlation_id})
            # --- END ADDED LLM TRACE LOGGING: Raw Response ---

            # Extract usage information
            usage = response_data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)

            logger.info(f"OpenRouter API response received",
                       extra={
                           "duration": api_duration,
                           "batch_id": batch_id,
                           "openrouter_prompt_tokens": prompt_tokens,
                           "openrouter_completion_tokens": completion_tokens,
                           "openrouter_total_tokens": total_tokens
                       })

            # Parse response
            logger.debug("Raw LLM response content received", extra={"content_preview": raw_content[:500]}) # Log preview to main log

            with LogTimer(logger, "JSON parsing and extraction", include_in_stats=True):
                result = _extract_json_from_response(raw_content) # Use helper

            if result is None:
                # --- ADDED LLM TRACE LOGGING: Parse Error ---
                llm_trace_logger.error(f"LLM JSON Parse Error (Batch ID: {batch_id}). Raw content logged above.", extra={'correlation_id': correlation_id})
                # --- END ADDED LLM TRACE LOGGING: Parse Error ---
                raise ValueError(f"LLM response was not valid JSON or could not be extracted. Preview: {raw_content[:200]}")

            # --- ADDED LLM TRACE LOGGING: Parsed Response ---
            try:
                 llm_trace_logger.debug(f"LLM Parsed Response (Batch ID: {batch_id}):\n{json.dumps(result, indent=2)}", extra={'correlation_id': correlation_id})
            except Exception as log_err:
                 llm_trace_logger.warning(f"Failed to log LLM parsed response (Batch ID: {batch_id}): {log_err}", extra={'correlation_id': correlation_id})
            # --- END ADDED LLM TRACE LOGGING: Parsed Response ---

            # --- Validate Batch ID ---
            response_batch_id = result.get("batch_id")
            if response_batch_id != batch_id:
                logger.warning(f"LLM response batch_id mismatch!",
                               extra={"expected_batch_id": batch_id, "received_batch_id": response_batch_id})
                result["batch_id_mismatch"] = True # Add a flag
            # --- End Validate Batch ID ---

            # Track token usage
            usage_data = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens
            }
            set_log_context({
                "openrouter_prompt_tokens": prompt_tokens,
                "openrouter_completion_tokens": completion_tokens,
                "openrouter_total_tokens": total_tokens
            })

            # Log classification results summary
            classification_count = len(result.get("classifications", []))
            successful_count = sum(
                1 for c in result.get("classifications", [])
                if not c.get("classification_not_possible", False)
            )
            logger.info(f"Classification completed for {successful_count}/{classification_count} vendors",
                       extra={
                           "level": level,
                           "batch_id": batch_id,
                           "total_classifications": classification_count,
                           "successful_classifications": successful_count,
                           "failed_classifications": classification_count - successful_count
                       })

            return {
                "result": result,
                "usage": usage_data
            }

        except httpx.HTTPStatusError as e:
             response_text = e.response.text[:200] if hasattr(e.response, 'text') else "[No Response Body]"
             logger.error(f"HTTP error during LLM batch classification", exc_info=True,
                         extra={ "status_code": e.response.status_code, "response_text": response_text, "batch_id": batch_id, "level": level })
             # --- ADDED LLM TRACE LOGGING: HTTP Error ---
             llm_trace_logger.error(f"LLM API HTTP Error (Batch ID: {batch_id}): Status={e.response.status_code}, Response='{response_text}'", exc_info=True, extra={'correlation_id': correlation_id})
             # --- END ADDED LLM TRACE LOGGING: HTTP Error ---
             raise # Re-raise after logging
        except httpx.RequestError as e:
             logger.error(f"Network error during LLM batch classification", exc_info=True,
                         extra={ "error_details": str(e), "batch_id": batch_id, "level": level })
             # --- ADDED LLM TRACE LOGGING: Network Error ---
             llm_trace_logger.error(f"LLM API Network Error (Batch ID: {batch_id}): {e}", exc_info=True, extra={'correlation_id': correlation_id})
             # --- END ADDED LLM TRACE LOGGING: Network Error ---
             raise # Re-raise after logging
        except Exception as e:
            error_context = {
                "batch_size": len(batch_data), "level": level, "parent_category_id": parent_category_id,
                "error": str(e), "model": self.model, "batch_id": batch_id
            }
            logger.error(f"Unexpected error during LLM batch classification", exc_info=True, extra=error_context)
            # --- ADDED LLM TRACE LOGGING: Unexpected Error ---
            llm_trace_logger.error(f"LLM Unexpected Error (Batch ID: {batch_id}): {e}", exc_info=True, extra={'correlation_id': correlation_id})
            # --- END ADDED LLM TRACE LOGGING: Unexpected Error ---
            raise # Re-raise after logging

    @retry(stop=stop_after_attempt(settings.MAX_RETRIES), wait=wait_exponential(multiplier=1, min=settings.RETRY_DELAY, max=10))
    @log_function_call(logger, include_args=False) # Don't log full search results here
    # @log_api_request("openrouter") # <-- REMOVED decorator to use manual trace logging below
    async def process_search_results(
        self,
        vendor_data: Dict[str, Any], # Pass full vendor dict including optional fields
        search_results: Dict[str, Any],
        taxonomy: Taxonomy
    ) -> Dict[str, Any]:
        """
        Process search results to determine classification.

        Args:
            vendor_data: Dictionary containing vendor name and optional fields (excluding description).
            search_results: Search results from Tavily
            taxonomy: Taxonomy data

        Returns:
            Classification result (Level 1 attempt) and API usage data.
        """
        vendor_name = vendor_data.get('vendor_name', 'UnknownVendor') # Extract name
        logger.info(f"Processing search results for vendor classification",
                   extra={
                       "vendor": vendor_name,
                       "source_count": len(search_results.get("sources", []))
                   })
        set_log_context({"vendor": vendor_name})
        attempt_id = str(uuid.uuid4()) # Unique ID for this attempt
        logger.debug(f"Generated search processing attempt ID", extra={"attempt_id": attempt_id})
        # --- ADDED LLM TRACE LOGGING ---
        correlation_id = get_correlation_id() # Get current correlation ID for logging
        llm_trace_logger.debug(f"Starting process_search_results (Attempt ID: {attempt_id}, Vendor: {vendor_name})", extra={'correlation_id': correlation_id})
        # --- END ADDED LLM TRACE LOGGING ---

        if not self.api_key:
            logger.error("Cannot process search results: OpenRouter API key is missing.")
            # --- ADDED LLM TRACE LOGGING ---
            llm_trace_logger.error(f"LLM API Error (Attempt ID: {attempt_id}): API key missing.", extra={'correlation_id': correlation_id})
            # --- END ADDED LLM TRACE LOGGING ---
            return {
                "result": {
                    "vendor_name": vendor_name, "category_id": "ERROR", "category_name": "ERROR",
                    "confidence": 0.0, "classification_not_possible": True,
                    "classification_not_possible_reason": "API key missing", "notes": ""
                },
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            }

        # --- UPDATED PROMPT CREATION ---
        with LogTimer(logger, "Search prompt creation", include_in_stats=True):
            prompt = self._create_search_results_prompt(vendor_data, search_results, taxonomy)
            prompt_length = len(prompt)
            logger.debug(f"Search results prompt created",
                        extra={"prompt_length": prompt_length})
        # --- END UPDATED PROMPT CREATION ---

        # --- Prepare API Call ---
        headers = {
            "Authorization": f"Bearer {self.api_key}", # Key will be sent, but not logged in trace
            "Content-Type": "application/json",
            "HTTP-Referer": "naicsvendorclassification.com",
            "X-Title": "NAICS Vendor Classification"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a precise vendor classification expert using the NAICS taxonomy. Analyze the provided search results *and* any provided vendor examples, address, website, internal category, parent company, or spend category to determine the vendor's primary business activity and classify it into the given Level 1 categories. Adhere strictly to the JSON output format. If information is insufficient or contradictory, state 'classification_not_possible'."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 1024,
            "top_p": 0.9,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "response_format": {"type": "json_object"}
        }

        # --- ADDED LLM TRACE LOGGING: Request ---
        try:
            log_headers = {k: v for k, v in headers.items() if k.lower() != 'authorization'}
            log_headers['Authorization'] = 'Bearer [REDACTED]'
            llm_trace_logger.debug(f"LLM Request Headers (Attempt ID: {attempt_id}):\n{json.dumps(log_headers, indent=2)}", extra={'correlation_id': correlation_id})
            llm_trace_logger.debug(f"LLM Request Payload (Attempt ID: {attempt_id}):\n{json.dumps(payload, indent=2)}", extra={'correlation_id': correlation_id})
        except Exception as log_err:
            llm_trace_logger.warning(f"Failed to log LLM request details (Attempt ID: {attempt_id}): {log_err}", extra={'correlation_id': correlation_id})
        # --- END ADDED LLM TRACE LOGGING: Request ---

        # Call OpenRouter API
        try:
            logger.debug(f"Sending search results to OpenRouter API")
            start_time = time.time()

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=60.0
                )
                response.raise_for_status()
                response_data = response.json()
                raw_content = response_data["choices"][0]["message"]["content"] # Get raw content string

            api_duration = time.time() - start_time

            # --- ADDED LLM TRACE LOGGING: Raw Response ---
            llm_trace_logger.debug(f"LLM Raw Response (Attempt ID: {attempt_id}, Status: {response.status_code}, Duration: {api_duration:.3f}s):\n{raw_content}", extra={'correlation_id': correlation_id})
            # --- END ADDED LLM TRACE LOGGING: Raw Response ---

            # Extract usage information
            usage = response_data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)

            logger.info(f"OpenRouter API response received for search results",
                       extra={
                           "duration": api_duration,
                           "vendor": vendor_name,
                           "openrouter_prompt_tokens": prompt_tokens,
                           "openrouter_completion_tokens": completion_tokens,
                           "openrouter_total_tokens": total_tokens,
                           "attempt_id": attempt_id
                       })

            # Parse response
            logger.debug("Raw LLM response content received (search)", extra={"content_preview": raw_content[:500]}) # Log preview to main log

            with LogTimer(logger, "JSON parsing and extraction (search)", include_in_stats=True):
                result = _extract_json_from_response(raw_content) # Use helper

            if result is None:
                # --- ADDED LLM TRACE LOGGING: Parse Error ---
                llm_trace_logger.error(f"LLM JSON Parse Error (Attempt ID: {attempt_id}). Raw content logged above.", extra={'correlation_id': correlation_id})
                # --- END ADDED LLM TRACE LOGGING: Parse Error ---
                raise ValueError(f"LLM response after search was not valid JSON or could not be extracted. Preview: {raw_content[:200]}")

            # --- ADDED LLM TRACE LOGGING: Parsed Response ---
            try:
                 llm_trace_logger.debug(f"LLM Parsed Response (Attempt ID: {attempt_id}):\n{json.dumps(result, indent=2)}", extra={'correlation_id': correlation_id})
            except Exception as log_err:
                 llm_trace_logger.warning(f"Failed to log LLM parsed response (Attempt ID: {attempt_id}): {log_err}", extra={'correlation_id': correlation_id})
            # --- END ADDED LLM TRACE LOGGING: Parsed Response ---

            # --- Validate Vendor Name ---
            response_vendor = result.get("vendor_name")
            if response_vendor != vendor_name:
                logger.warning(f"LLM search response vendor name mismatch!",
                               extra={"expected_vendor": vendor_name, "received_vendor": response_vendor})
                result["vendor_name"] = vendor_name # Overwrite
            # --- End Validate Vendor Name ---

            # Track token usage
            usage_data = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens
            }
            set_log_context({
                "openrouter_prompt_tokens": prompt_tokens,
                "openrouter_completion_tokens": completion_tokens,
                "openrouter_total_tokens": total_tokens
            })

            return {
                "result": result,
                "usage": usage_data
            }

        except httpx.HTTPStatusError as e:
             response_text = e.response.text[:200] if hasattr(e.response, 'text') else "[No Response Body]"
             logger.error(f"HTTP error during search result processing", exc_info=True,
                         extra={ "status_code": e.response.status_code, "response_text": response_text, "vendor": vendor_name, "attempt_id": attempt_id })
             # --- ADDED LLM TRACE LOGGING: HTTP Error ---
             llm_trace_logger.error(f"LLM API HTTP Error (Attempt ID: {attempt_id}): Status={e.response.status_code}, Response='{response_text}'", exc_info=True, extra={'correlation_id': correlation_id})
             # --- END ADDED LLM TRACE LOGGING: HTTP Error ---
             raise # Re-raise after logging
        except httpx.RequestError as e:
             logger.error(f"Network error during search result processing", exc_info=True,
                         extra={ "error_details": str(e), "vendor": vendor_name, "attempt_id": attempt_id })
             # --- ADDED LLM TRACE LOGGING: Network Error ---
             llm_trace_logger.error(f"LLM API Network Error (Attempt ID: {attempt_id}): {e}", exc_info=True, extra={'correlation_id': correlation_id})
             # --- END ADDED LLM TRACE LOGGING: Network Error ---
             raise # Re-raise after logging
        except Exception as e:
            error_context = {
                "vendor": vendor_name, "error": str(e), "model": self.model, "attempt_id": attempt_id
            }
            logger.error(f"Unexpected error during search result processing", exc_info=True, extra=error_context)
            # --- ADDED LLM TRACE LOGGING: Unexpected Error ---
            llm_trace_logger.error(f"LLM Unexpected Error (Attempt ID: {attempt_id}): {e}", exc_info=True, extra={'correlation_id': correlation_id})
            # --- END ADDED LLM TRACE LOGGING: Unexpected Error ---
            raise # Re-raise after logging

    # --- Prompt generation methods (_create_classification_prompt, _create_search_results_prompt) ---
    # --- No changes needed in the prompt generation logic itself for this logging task ---
    @log_function_call(logger, include_args=False) # Don't log vendors list
    def _create_classification_prompt(
        self,
        vendors_data: List[Dict[str, Any]], # Pass list of dicts including optional fields
        level: int,
        taxonomy: Taxonomy,
        parent_category_id: Optional[str] = None, # Changed parameter name
        batch_id: str = "unknown-batch"
    ) -> str:
        """
        Create an appropriate prompt for the current classification level,
        including optional vendor context (excluding description) and emphasizing ambiguity handling.

        Args:
            vendors_data: List of vendor dictionaries.
            level: Classification level (1-4)
            taxonomy: Taxonomy data
            parent_category_id: Parent category ID (required for levels 2-4)
            batch_id: Unique ID for this batch

        Returns:
            Prompt string
        """
        logger.debug(f"Creating classification prompt for level {level}",
                    extra={
                        "vendor_count": len(vendors_data),
                        "level": level,
                        "parent_category_id": parent_category_id,
                        "batch_id": batch_id
                    })

        # --- Generate Vendor List String with ALL Optional Context (excluding description) ---
        vendor_list_str = ""
        for i, vendor_entry in enumerate(vendors_data):
            vendor_name = vendor_entry.get('vendor_name', f'UnknownVendor_{i}')
            example = vendor_entry.get('example')
            address = vendor_entry.get('vendor_address')
            website = vendor_entry.get('vendor_website')
            internal_cat = vendor_entry.get('internal_category')
            parent_co = vendor_entry.get('parent_company')
            spend_cat = vendor_entry.get('spend_category')

            vendor_list_str += f"\n{i+1}. Vendor Name: {vendor_name}"
            if example:
                vendor_list_str += f"\n   Example Goods/Services: {example[:200]}" # Truncate for prompt length
            if address:
                vendor_list_str += f"\n   Address: {address[:200]}" # Truncate
            if website:
                vendor_list_str += f"\n   Website: {website[:100]}" # Truncate
            if internal_cat:
                vendor_list_str += f"\n   Internal Category: {internal_cat[:100]}" # Truncate
            if parent_co:
                vendor_list_str += f"\n   Parent Company: {parent_co[:100]}" # Truncate
            if spend_cat:
                vendor_list_str += f"\n   Spend Category: {spend_cat[:100]}" # Truncate
        # --- END MODIFIED ---

        # --- LEVEL 1 PROMPT ---
        if level == 1:
            logger.debug(f"Fetching level 1 categories from taxonomy")
            categories = taxonomy.get_level1_categories()
            logger.debug(f"Found {len(categories)} level 1 categories")
            categories_str = "\n".join(f"- {cat.id}: {cat.name}" for cat in categories)

            prompt = f"""
You are a precise vendor classification expert using the NAICS taxonomy. Your task is to classify the vendors below based on their names and any provided context (examples, address, website, internal category, parent company, spend category).

Classify each vendor into ONE of the following Level 1 NAICS categories:
{categories_str}

**Instructions:**
1.  Analyze each vendor name carefully. Use the provided Example Goods/Services, Address, Website, Internal Category, Parent Company, and Spend Category for additional context if available. Location (Address) and Website can be strong indicators. Internal/Spend categories provide hints about the client's view.
2.  If the name and context clearly indicate the industry (e.g., "Acme Construction", "Beta Software Inc.", website points to manufacturing), assign the most appropriate category ID and name with a high confidence (0.8-1.0).
3.  **CRITICAL:** If the name is generic, ambiguous, or you lack specific knowledge about the company even with all the context (e.g., "Global Services", "Enterprise Solutions", "Consulting Group", "J. Smith Co.", "Anytown Supplies"), **DO NOT GUESS**. Instead, mark `classification_not_possible` as `true` and provide a brief reason (e.g., "Ambiguous name", "Insufficient information", "Generic name", "Name does not indicate industry"). Set confidence to 0.0 in this case.
4.  Provide a confidence score between 0.0 and 1.0 for each classification attempt. A score of 0.0 *must* correspond to `classification_not_possible: true`.

**Vendor list:**
{vendor_list_str}

**Output Format:** Respond *only* with a valid JSON object matching this exact schema. Do not include any text before or after the JSON object.
```json
{{
  "level": 1,
  "batch_id": "{batch_id}",
  "parent_category_id": null,
  "classifications": [
    {{
      "vendor_name": "Vendor Name Here",
      "category_id": "ID or N/A",
      "category_name": "Category Name or N/A",
      "confidence": 0.0_to_1.0,
      "classification_not_possible": true_or_false,
      "classification_not_possible_reason": "Reason text or null"
    }}
    // ... more classifications
  ]
}}
```
Ensure every vendor from the list is included in the `classifications` array with the exact vendor name provided. Ensure the `batch_id` in the response matches "{batch_id}".
"""
        # --- LEVELS 2-4 PROMPT ---
        else:
            logger.debug(f"Creating prompt for level {level} with parent category {parent_category_id}")
            parent_category_name = "Unknown" # Default
            parent_category_obj = None
            categories = [] # Initialize categories list

            # --- Get Parent Category Name and Subcategories ---
            try:
                if level == 2 and parent_category_id in taxonomy.categories:
                    parent_category_obj = taxonomy.categories[parent_category_id]
                    categories = taxonomy.get_level2_categories(parent_category_id)
                elif level == 3:
                    parts = parent_category_id.split('.')
                    if len(parts) == 2 and parts[0] in taxonomy.categories and parts[1] in taxonomy.categories[parts[0]].children:
                         parent_category_obj = taxonomy.categories[parts[0]].children[parts[1]]
                         categories = taxonomy.get_level3_categories(parent_category_id)
                elif level == 4:
                    parts = parent_category_id.split('.')
                    if len(parts) == 3 and parts[0] in taxonomy.categories and \
                       parts[1] in taxonomy.categories[parts[0]].children and \
                       parts[2] in taxonomy.categories[parts[0]].children[parts[1]].children:
                         parent_category_obj = taxonomy.categories[parts[0]].children[parts[1]].children[parts[2]]
                         categories = taxonomy.get_level4_categories(parent_category_id)

                if parent_category_obj:
                    parent_category_name = parent_category_obj.name
                else:
                     logger.warning(f"Could not find parent category object for ID: {parent_category_id}")

            except Exception as e:
                logger.error(f"Error retrieving categories for level {level}, parent {parent_category_id}", exc_info=True)
            # --- End Get Parent Category Name ---

            logger.debug(f"Found {len(categories)} level {level} categories for parent {parent_category_id}")

            # --- HANDLE MISSING SUBCATEGORIES ---
            if not categories:
                 logger.warning(f"No subcategories found for level {level}, parent {parent_category_id}. Prompt cannot be generated effectively.")
                 prompt = f"""
You are a precise vendor classification expert. The parent category ID '{parent_category_id}' (Name: '{parent_category_name}') has no defined subcategories at Level {level} in the provided taxonomy.

For the following vendors, classification at Level {level} is not possible due to missing taxonomy definitions.

Vendor list:
{vendor_list_str}

Respond *only* with a valid JSON object matching this exact schema:
```json
{{
  "level": {level},
  "batch_id": "{batch_id}",
  "parent_category_id": "{parent_category_id}",
  "classifications": [
    {{
      "vendor_name": "Vendor Name Here",
      "category_id": "N/A",
      "category_name": "N/A",
      "confidence": 0.0,
      "classification_not_possible": true,
      "classification_not_possible_reason": "No subcategories defined for parent {parent_category_id} at Level {level}"
    }}
    // ... repeat for all vendors in the list
  ]
}}
```
Ensure every vendor from the list is included in the `classifications` array with the exact vendor name provided. Ensure the `batch_id` in the response matches "{batch_id}".
"""
                 return prompt
            # --- END HANDLE MISSING SUBCATEGORIES ---

            categories_str = "\n".join(f"- {cat.id}: {cat.name}" for cat in categories)

            prompt = f"""
You are a precise vendor classification expert using the NAICS taxonomy. Your task is to classify the vendors below, which belong to the parent category '{parent_category_id}: {parent_category_name}'. Use the vendor name and any provided context (examples, address, website, internal category, parent company, spend category).

Classify each vendor into ONE of the following Level {level} NAICS categories, which are subcategories of '{parent_category_name}':
{categories_str}

**Instructions:**
1.  Consider the vendor name, the fact it belongs to the parent category '{parent_category_name}', and any provided Example Goods/Services, Address, Website, Internal Category, Parent Company, or Spend Category.
2.  Assign the most specific and appropriate Level {level} category ID and name. Use context from the parent category and all vendor details to help disambiguate if possible.
3.  **CRITICAL:** If the name and context are too generic *even within the context of the parent category* to determine the correct Level {level} subcategory (e.g., "General Supply" under "Wholesale Trade"), or if you lack specific knowledge, **DO NOT GUESS**. Mark `classification_not_possible` as `true` and provide a brief reason (e.g., "Insufficient information for subcategory", "Ambiguous within parent category"). Set confidence to 0.0 in this case.
4.  Provide a confidence score between 0.0 and 1.0 for each classification attempt. A score of 0.0 *must* correspond to `classification_not_possible: true`.

**Vendor list:**
{vendor_list_str}

**Output Format:** Respond *only* with a valid JSON object matching this exact schema. Do not include any text before or after the JSON object.
```json
{{
  "level": {level},
  "batch_id": "{batch_id}",
  "parent_category_id": "{parent_category_id}",
  "classifications": [
    {{
      "vendor_name": "Vendor Name Here",
      "category_id": "ID or N/A",
      "category_name": "Category Name or N/A",
      "confidence": 0.0_to_1.0,
      "classification_not_possible": true_or_false,
      "classification_not_possible_reason": "Reason text or null"
    }}
    // ... more classifications
  ]
}}
```
Ensure every vendor from the list is included in the `classifications` array with the exact vendor name provided. Ensure the `batch_id` in the response matches "{batch_id}".
"""
        # --- END LEVELS 2-4 PROMPT ---

        return prompt


    @log_function_call(logger, include_args=False) # Don't log full search results
    def _create_search_results_prompt(
        self,
        vendor_data: Dict[str, Any], # Pass full vendor dict including optional fields
        search_results: Dict[str, Any],
        taxonomy: Taxonomy
    ) -> str:
        """
        Create a prompt for processing search results, including optional vendor context (excluding description)
        and emphasizing grounding and handling uncertainty.

        Args:
            vendor_data: Dictionary containing vendor name and optional fields (excluding description).
            search_results: Search results from Tavily
            taxonomy: Taxonomy data

        Returns:
            Prompt string
        """
        vendor_name = vendor_data.get('vendor_name', 'UnknownVendor') # Extract name
        example = vendor_data.get('example')
        address = vendor_data.get('vendor_address')
        website = vendor_data.get('vendor_website')
        internal_cat = vendor_data.get('internal_category')
        parent_co = vendor_data.get('parent_company')
        spend_cat = vendor_data.get('spend_category')

        logger.debug(f"Creating search results prompt for vendor",
                    extra={
                        "vendor": vendor_name,
                        "source_count": len(search_results.get("sources", []))
                    })
        # Get level 1 categories
        categories = taxonomy.get_level1_categories()
        categories_str = "\n".join(f"- {cat.id}: {cat.name}" for cat in categories)

        # Format search results
        sources_str = ""
        if search_results.get("sources"):
            for i, source in enumerate(search_results["sources"]):
                content_preview = source.get('content', '')[:1500] # Provide more content to LLM
                sources_str += f"\nSource {i+1}:\nTitle: {source.get('title', 'N/A')}\nURL: {source.get('url', 'N/A')}\nContent Snippet: {content_preview}...\n"
        else:
            sources_str = "No relevant search results were found."

        summary_str = search_results.get("summary", "")
        if summary_str:
            sources_str += f"\nOverall Summary from Search:\n{summary_str}\n"

        # --- Add ALL Optional Vendor Context (excluding description) ---
        context_str = ""
        if example:
            context_str += f"\nProvided Example Goods/Services: {example[:300]}" # Truncate
        if address:
            context_str += f"\nProvided Address: {address[:200]}" # Truncate
        if website:
            context_str += f"\nProvided Website: {website[:100]}" # Truncate
        if internal_cat:
            context_str += f"\nProvided Internal Category: {internal_cat[:100]}" # Truncate
        if parent_co:
            context_str += f"\nProvided Parent Company: {parent_co[:100]}" # Truncate
        if spend_cat:
            context_str += f"\nProvided Spend Category: {spend_cat[:100]}" # Truncate

        if not context_str:
            context_str = "\nNo additional context provided by user."
        # --- END MODIFIED ---

        prompt = f"""
You are a precise vendor classification expert using the NAICS taxonomy. Your task is to classify the vendor '{vendor_name}' based *only* on the provided context and search results. **Do not use any prior knowledge you have about this vendor unless it is confirmed in the provided information.**

**Vendor:** {vendor_name}

**Provided Context:**
{context_str}

**Search Results:**
{sources_str}

**Instructions:**
1.  Analyze the provided context (Examples, Address, Website, Internal Category, Parent Company, Spend Category) and search results carefully to understand the primary business activity of '{vendor_name}'. Focus on what the company *does*, not just what it sells if it's a reseller. Synthesize information across all available sources. Website and Address can be particularly useful. Internal/Spend categories provide hints.
2.  Based *only* on the provided information, classify the vendor into ONE of the following Level 1 NAICS categories:
    {categories_str}
3.  Provide a confidence score between 0.0 and 1.0. Base confidence on the clarity, consistency, and relevance of the information provided. Higher confidence requires clear evidence of the primary business activity.
4.  **CRITICAL:** If the provided information is insufficient, contradictory, irrelevant, focuses only on products sold rather than the business activity, or does not provide enough detail to confidently determine the business type, set `classification_not_possible` to `true` and provide a brief reason (e.g., "Insufficient information", "Conflicting sources", "Information irrelevant", "Unclear primary business activity"). Set confidence to 0.0 in this case.
5.  Provide brief notes explaining your reasoning, referencing specific details or sources from the context or search results, especially if confidence is not 1.0 or if classification was not possible.

**Output Format:** Respond *only* with a valid JSON object matching this exact schema. Do not include any text before or after the JSON object.
```json
{{
  "vendor_name": "{vendor_name}",
  "category_id": "ID or N/A",
  "category_name": "Category Name or N/A",
  "confidence": 0.0_to_1.0,
  "classification_not_possible": true_or_false,
  "classification_not_possible_reason": "Reason text or null",
  "notes": "Brief explanation of classification decision based *only* on the provided context and search results."
}}
```
Ensure the `vendor_name` in the response matches "{vendor_name}".
"""
        return prompt