# app/services/llm_service.py
import httpx
import json
import re
from typing import List, Dict, Any, Optional, Set
import logging
import time
import uuid
from tenacity import retry, stop_after_attempt, wait_exponential, RetryError

from core.config import settings
from models.taxonomy import Taxonomy
from core.logging_config import get_logger
from core.log_context import set_log_context, get_correlation_id
from utils.log_utils import LogTimer, log_function_call
from tasks.classification_prompts import generate_batch_prompt, generate_search_prompt

# Configure logger
logger = get_logger("vendor_classification.llm_service")
llm_trace_logger = logging.getLogger("llm_api_trace")

logger.debug("Successfully imported generate_batch_prompt and generate_search_prompt from tasks.classification_prompts.")

# --- Helper function for JSON parsing (Remains unchanged) ---
def _extract_json_from_response(response_content: str) -> Optional[Dict[str, Any]]:
    """
    Attempts to extract a JSON object from a string, handling common LLM response issues.
    """
    if not response_content:
        logger.warning("Attempted to parse empty response content.")
        return None

    content = response_content.strip()

    # 1. Check for markdown code fences (json ...  or  ... )
    match = re.search(r"(?:json)?\s*(\{.*\})\s*", content, re.DOTALL | re.IGNORECASE)
    if match:
        content = match.group(1).strip()
        logger.debug("Extracted JSON content from within markdown code fences.")
    else:
        # 2. If no fences, try finding the first '{' and last '}'
        start_index = content.find('{')
        end_index = content.rfind('}')
        if start_index != -1 and end_index != -1 and end_index > start_index:
            potential_json = content[start_index:end_index+1]
            # Basic brace count check
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
                     exc_info=False, # Less noise in main log, trace log has full info
                     extra={"error": str(e), "cleaned_content_preview": content[:500]})
        return None
    except Exception as e:
        logger.error("Unexpected error during JSON parsing after cleaning/extraction.",
                     exc_info=True,
                     extra={"cleaned_content_preview": content[:500]})
        return None
# --- END HELPER ---

# --- Status codes that trigger key rotation ---
OPENROUTER_ROTATION_STATUS_CODES = {401, 403, 429, 500, 502, 503, 504}

class LLMService:
    """Service for interacting with OpenRouter API, with key rotation."""

    def __init__(self):
        """Initialize the LLM service."""
        logger.info("Initializing LLM service with OpenRouter and key rotation")
        self.api_keys = settings.OPENROUTER_API_KEYS
        self.api_base = settings.OPENROUTER_API_BASE
        self.model = settings.OPENROUTER_MODEL
        self.current_key_index = 0

        if not self.api_keys:
             logger.error("OpenRouter API key list is empty! LLM calls will fail.")
             # Optionally raise an exception here if keys are absolutely required
             # raise ValueError("OpenRouter API keys are missing in configuration.")

        logger.debug("LLM service initialized",
                    extra={"api_base": self.api_base,
                           "model": self.model,
                           "key_count": len(self.api_keys)})

    def _get_current_key(self) -> Optional[str]:
        """Gets the current API key based on the index."""
        if not self.api_keys:
            return None
        # Ensure index is valid
        if self.current_key_index >= len(self.api_keys):
            logger.warning(f"OpenRouter key index {self.current_key_index} out of bounds ({len(self.api_keys)} keys). Resetting to 0.")
            self.current_key_index = 0
        return self.api_keys[self.current_key_index]

    def _rotate_key(self):
        """Rotates to the next API key in the list."""
        if not self.api_keys or len(self.api_keys) <= 1:
            logger.warning("Cannot rotate OpenRouter key: list is empty or has only one key.")
            return # No rotation possible

        old_index = self.current_key_index
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        logger.warning(f"Rotated OpenRouter API key from index {old_index} to {self.current_key_index} due to API error.")

    @retry(stop=stop_after_attempt(settings.MAX_RETRIES), wait=wait_exponential(multiplier=1, min=settings.RETRY_DELAY, max=10))
    @log_function_call(logger, include_args=False)
    async def classify_batch(
        self,
        batch_data: List[Dict[str, Any]],
        level: int,
        taxonomy: Taxonomy,
        parent_category_id: Optional[str] = None,
        search_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a batch of vendors to LLM for classification, with key rotation on failure.
        """
        batch_names = [vd.get('vendor_name', f'Unknown_{i}') for i, vd in enumerate(batch_data)]
        context_type = "Search Context" if search_context else "Initial Data"
        logger.info(f"Classifying vendor batch using {context_type}",
                   extra={
                       "batch_size": len(batch_data),
                       "level": level,
                       "parent_category_id": parent_category_id,
                       "has_search_context": bool(search_context)
                   })
        set_log_context({"vendor_count": len(batch_data), "taxonomy_level": level, "context_type": context_type})
        batch_id = str(uuid.uuid4())
        logger.debug(f"Generated batch ID", extra={"batch_id": batch_id})
        correlation_id = get_correlation_id()
        llm_trace_logger.debug(f"LLM_TRACE: Starting classify_batch (Batch ID: {batch_id}, Level: {level}, Parent: {parent_category_id}, Context: {context_type})", extra={'correlation_id': correlation_id})

        # --- Get current key ---
        current_api_key = self._get_current_key()
        if not current_api_key:
            logger.error("Cannot classify batch: No OpenRouter API key available (list empty or initialization failed).")
            llm_trace_logger.error(f"LLM_TRACE: LLM API Error (Batch ID: {batch_id}): No API key available.", extra={'correlation_id': correlation_id})
            # Return error structure consistent with other failures
            return {
                "result": {
                    "level": level, "batch_id": batch_id, "parent_category_id": parent_category_id,
                    "classifications": [
                        {
                            "vendor_name": vd.get('vendor_name', f'Unknown_{i}'), "category_id": "ERROR", "category_name": "ERROR",
                            "confidence": 0.0, "classification_not_possible": True,
                            "classification_not_possible_reason": "No API key configured", "notes": "Failed due to missing API key configuration."
                        } for i, vd in enumerate(batch_data)
                    ]
                },
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            }
        # --- End get current key ---

        logger.debug(f"Creating classification prompt with {context_type}")
        with LogTimer(logger, "Prompt creation", include_in_stats=True):
            prompt = generate_batch_prompt(
                batch_data, level, taxonomy, parent_category_id, batch_id, search_context
            )
            prompt_length = len(prompt)
            logger.debug(f"Classification prompt created", extra={"prompt_length": prompt_length, "current_key_index": self.current_key_index})
            # Log the generated prompt (already present)
            llm_trace_logger.debug(f"LLM_TRACE: Generated Prompt (Batch ID: {batch_id}):\n-------\n{prompt}\n-------", extra={'correlation_id': correlation_id})

        headers = {
            "Authorization": f"Bearer {current_api_key}", # Use current key
            "Content-Type": "application/json",
            "HTTP-Referer": "naicsvendorclassification.com", "X-Title": "NAICS Vendor Classification"
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1, "max_tokens": 2048, "top_p": 0.9,
            "frequency_penalty": 0, "presence_penalty": 0,
            "response_format": {"type": "json_object"}
        }

        # Log Request Details (Trace Log)
        try:
            # Log Headers (Redacted Key - already present)
            log_headers = {k: v for k, v in headers.items() if k.lower() != 'authorization'}
            log_headers['Authorization'] = f'Bearer [REDACTED_KEY_INDEX_{self.current_key_index}]'
            llm_trace_logger.debug(f"LLM_TRACE: LLM Request Headers (Batch ID: {batch_id}):\n{json.dumps(log_headers, indent=2)}", extra={'correlation_id': correlation_id})
            # --- ADDED: Log Full Request Payload ---
            llm_trace_logger.debug(f"LLM_TRACE: LLM Request Payload (Batch ID: {batch_id}):\n{json.dumps(payload, indent=2)}", extra={'correlation_id': correlation_id})
            # --- END ADDED ---
        except Exception as log_err:
            llm_trace_logger.warning(f"LLM_TRACE: Failed to log LLM request details (Batch ID: {batch_id}): {log_err}", extra={'correlation_id': correlation_id})

        response_data = None; raw_content = None; response = None; status_code = None; api_duration = 0.0
        try:
            logger.debug(f"Sending request to OpenRouter API using key index {self.current_key_index}")
            start_time = time.time()
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self.api_base}/chat/completions", json=payload, headers=headers, timeout=90.0)
                # --- Log Raw Response (already present) ---
                raw_content = response.text
                status_code = response.status_code
                api_duration = time.time() - start_time
                llm_trace_logger.debug(f"LLM_TRACE: LLM Raw Response (Batch ID: {batch_id}, Status: {status_code}, Duration: {api_duration:.3f}s):\n-------\n{raw_content or '[No Content Received]'}\n-------", extra={'correlation_id': correlation_id})
                # --- End Log Raw Response ---
                response.raise_for_status() # Check for HTTP errors AFTER logging raw response
                response_data = response.json()

            # ... (rest of successful response processing remains the same) ...
            if response_data and response_data.get("choices") and isinstance(response_data["choices"], list) and len(response_data["choices"]) > 0:
                 message = response_data["choices"][0].get("message")
                 if message and isinstance(message, dict):
                     content_field = message.get("content")
                     if content_field:
                         # Update raw_content if message.content exists, otherwise keep response.text
                         raw_content = content_field
                         logger.debug("Extracted 'content' field from LLM JSON response.")
                     else:
                         logger.warning("LLM response message object missing 'content' field.", extra={"message_obj": message})
                 else:
                     logger.warning("LLM response choice missing 'message' object or it's not a dict.", extra={"choice_obj": response_data["choices"][0]})

            usage = response_data.get("usage", {}) if response_data else {}
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)

            logger.info(f"OpenRouter API response received successfully",
                       extra={
                           "duration": api_duration, "batch_id": batch_id, "level": level,
                           "status_code": status_code, "key_index_used": self.current_key_index,
                           "openrouter_prompt_tokens": prompt_tokens,
                           "openrouter_completion_tokens": completion_tokens,
                           "openrouter_total_tokens": total_tokens
                       })

            logger.debug("Raw LLM response content received (after potential extraction)", extra={"content_preview": str(raw_content)[:500]})
            with LogTimer(logger, "JSON parsing and extraction", include_in_stats=True):
                result = _extract_json_from_response(raw_content)

            if result is None:
                llm_trace_logger.error(f"LLM_TRACE: LLM JSON Parse Error (Batch ID: {batch_id}). Raw content logged above.", extra={'correlation_id': correlation_id})
                raise ValueError(f"LLM response was not valid JSON or could not be extracted. Preview: {str(raw_content)[:200]}")

            try:
                 # Log Parsed Response (already present)
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
             response_text = raw_content or (e.response.text[:500] if hasattr(e.response, 'text') else "[No Response Body]")
             status_code = e.response.status_code
             logger.error(f"HTTP error during LLM batch classification", exc_info=False,
                         extra={ "status_code": status_code, "response_text": response_text, "batch_id": batch_id, "level": level, "key_index_used": self.current_key_index })
             # Log HTTP Error (already present)
             llm_trace_logger.error(f"LLM_TRACE: LLM API HTTP Error (Batch ID: {batch_id}): Status={status_code}, Response='{response_text}'", exc_info=True, extra={'correlation_id': correlation_id})

             # --- Key Rotation Logic (already present) ---
             if status_code in OPENROUTER_ROTATION_STATUS_CODES:
                 self._rotate_key()
             # --- END Key Rotation Logic ---
             raise # Re-raise for tenacity

        except httpx.RequestError as e:
             logger.error(f"Network error during LLM batch classification", exc_info=False,
                         extra={ "error_details": str(e), "batch_id": batch_id, "level": level, "key_index_used": self.current_key_index })
             # Log Network Error (already present)
             llm_trace_logger.error(f"LLM_TRACE: LLM API Network Error (Batch ID: {batch_id}): {e}", exc_info=True, extra={'correlation_id': correlation_id})
             # Optionally rotate on specific network errors too, but less common for key issues
             # self._rotate_key()
             raise # Re-raise for tenacity

        except ValueError as ve: # Catch the specific error raised on JSON parse failure
             logger.error(f"LLM response parsing error during batch classification", exc_info=False,
                          extra={"error": str(ve), "batch_id": batch_id, "level": level})
             # Don't rotate on parse errors, likely not a key issue
             raise # Re-raise for tenacity

        except Exception as e:
            error_context = { "batch_size": len(batch_data), "level": level, "parent_category_id": parent_category_id, "error": str(e), "model": self.model, "batch_id": batch_id, "key_index_used": self.current_key_index }
            logger.error(f"Unexpected error during LLM batch classification", exc_info=True, extra=error_context)
            # Log Unexpected Error (already present)
            llm_trace_logger.error(f"LLM_TRACE: LLM Unexpected Error (Batch ID: {batch_id}): {e}", exc_info=True, extra={'correlation_id': correlation_id})
            # Optionally rotate on unexpected errors, but might hide other issues
            # self._rotate_key()
            raise # Re-raise for tenacity

    @retry(stop=stop_after_attempt(settings.MAX_RETRIES), wait=wait_exponential(multiplier=1, min=settings.RETRY_DELAY, max=10))
    @log_function_call(logger, include_args=False)
    async def process_search_results(
        self,
        vendor_data: Dict[str, Any],
        search_results: Dict[str, Any],
        taxonomy: Taxonomy
    ) -> Dict[str, Any]:
        """
        Process search results for L1 classification, with key rotation on failure.
        """
        vendor_name = vendor_data.get('vendor_name', 'UnknownVendor')
        logger.info(f"Processing search results for initial L1 classification",
                   extra={ "vendor": vendor_name, "source_count": len(search_results.get("sources", [])) })
        set_log_context({"vendor": vendor_name})
        attempt_id = str(uuid.uuid4())
        logger.debug(f"Generated search processing attempt ID", extra={"attempt_id": attempt_id})
        correlation_id = get_correlation_id()
        llm_trace_logger.debug(f"LLM_TRACE: Starting process_search_results (Attempt ID: {attempt_id}, Vendor: {vendor_name})", extra={'correlation_id': correlation_id})

        # --- Get current key ---
        current_api_key = self._get_current_key()
        if not current_api_key:
            logger.error("Cannot process search results: No OpenRouter API key available.")
            llm_trace_logger.error(f"LLM_TRACE: LLM API Error (Attempt ID: {attempt_id}): No API key available.", extra={'correlation_id': correlation_id})
            return {
                "result": { "vendor_name": vendor_name, "category_id": "ERROR", "category_name": "ERROR", "confidence": 0.0, "classification_not_possible": True, "classification_not_possible_reason": "No API key configured", "notes": "" },
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            }
        # --- End get current key ---

        with LogTimer(logger, "Search prompt creation", include_in_stats=True):
            prompt = generate_search_prompt(vendor_data, search_results, taxonomy, attempt_id)
            prompt_length = len(prompt)
            logger.debug(f"Search results prompt created", extra={"prompt_length": prompt_length, "current_key_index": self.current_key_index})
            # Log Generated Prompt (already present)
            llm_trace_logger.debug(f"LLM_TRACE: Generated Search Prompt (Attempt ID: {attempt_id}):\n-------\n{prompt}\n-------", extra={'correlation_id': correlation_id})

        headers = {
            "Authorization": f"Bearer {current_api_key}", # Use current key
            "Content-Type": "application/json",
            "HTTP-Referer": "naicsvendorclassification.com", "X-Title": "NAICS Vendor Classification"
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1, "max_tokens": 1024, "top_p": 0.9,
            "frequency_penalty": 0, "presence_penalty": 0,
            "response_format": {"type": "json_object"}
        }

        # Log Request Details (Trace Log)
        try:
            # Log Headers (Redacted Key - already present)
            log_headers = {k: v for k, v in headers.items() if k.lower() != 'authorization'}
            log_headers['Authorization'] = f'Bearer [REDACTED_KEY_INDEX_{self.current_key_index}]'
            llm_trace_logger.debug(f"LLM_TRACE: LLM Request Headers (Attempt ID: {attempt_id}):\n{json.dumps(log_headers, indent=2)}", extra={'correlation_id': correlation_id})
            # --- ADDED: Log Full Request Payload ---
            llm_trace_logger.debug(f"LLM_TRACE: LLM Request Payload (Attempt ID: {attempt_id}):\n{json.dumps(payload, indent=2)}", extra={'correlation_id': correlation_id})
            # --- END ADDED ---
        except Exception as log_err:
            llm_trace_logger.warning(f"LLM_TRACE: Failed to log LLM request details (Attempt ID: {attempt_id}): {log_err}", extra={'correlation_id': correlation_id})

        response_data = None; raw_content = None; response = None; status_code = None; api_duration = 0.0
        try:
            logger.debug(f"Sending search results to OpenRouter API using key index {self.current_key_index}")
            start_time = time.time()
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self.api_base}/chat/completions", json=payload, headers=headers, timeout=60.0)
                # --- Log Raw Response (already present) ---
                raw_content = response.text
                status_code = response.status_code
                api_duration = time.time() - start_time
                llm_trace_logger.debug(f"LLM_TRACE: LLM Raw Response (Attempt ID: {attempt_id}, Status: {status_code}, Duration: {api_duration:.3f}s):\n-------\n{raw_content or '[No Content Received]'}\n-------", extra={'correlation_id': correlation_id})
                # --- End Log Raw Response ---
                response.raise_for_status()
                response_data = response.json()

            # ... (rest of successful response processing remains the same) ...
            if response_data and response_data.get("choices") and isinstance(response_data["choices"], list) and len(response_data["choices"]) > 0:
                 message = response_data["choices"][0].get("message")
                 if message and isinstance(message, dict):
                     content_field = message.get("content")
                     if content_field:
                         # Update raw_content if message.content exists, otherwise keep response.text
                         raw_content = content_field
                         logger.debug("Extracted 'content' field from LLM JSON response (search).")
                     else:
                         logger.warning("LLM response message object missing 'content' field (search).", extra={"message_obj": message})
                 else:
                     logger.warning("LLM response choice missing 'message' object or it's not a dict (search).", extra={"choice_obj": response_data["choices"][0]})

            usage = response_data.get("usage", {}) if response_data else {}
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)

            logger.info(f"OpenRouter API response received successfully for search results",
                       extra={ "duration": api_duration, "vendor": vendor_name, "status_code": status_code, "key_index_used": self.current_key_index, "openrouter_prompt_tokens": prompt_tokens, "openrouter_completion_tokens": completion_tokens, "openrouter_total_tokens": total_tokens, "attempt_id": attempt_id })

            logger.debug("Raw LLM response content received (search, after potential extraction)", extra={"content_preview": str(raw_content)[:500]})
            with LogTimer(logger, "JSON parsing and extraction (search)", include_in_stats=True):
                result = _extract_json_from_response(raw_content)

            if result is None:
                llm_trace_logger.error(f"LLM_TRACE: LLM JSON Parse Error (Attempt ID: {attempt_id}). Raw content logged above.", extra={'correlation_id': correlation_id})
                raise ValueError(f"LLM response after search was not valid JSON or could not be extracted. Preview: {str(raw_content)[:200]}")

            try:
                 # Log Parsed Response (already present)
                 llm_trace_logger.debug(f"LLM_TRACE: LLM Parsed Response (Attempt ID: {attempt_id}):\n{json.dumps(result, indent=2)}", extra={'correlation_id': correlation_id})
            except Exception as log_err:
                 llm_trace_logger.warning(f"LLM_TRACE: Failed to log LLM parsed response (Attempt ID: {attempt_id}): {log_err}", extra={'correlation_id': correlation_id})

            response_vendor = result.get("vendor_name")
            if response_vendor != vendor_name:
                logger.warning(f"LLM search response vendor name mismatch!",
                               extra={"expected_vendor": vendor_name, "received_vendor": response_vendor})
                result["vendor_name"] = vendor_name

            usage_data = { "prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens, "total_tokens": total_tokens }
            set_log_context({ "openrouter_prompt_tokens": prompt_tokens, "openrouter_completion_tokens": completion_tokens, "openrouter_total_tokens": total_tokens })

            return { "result": result, "usage": usage_data }

        except httpx.HTTPStatusError as e:
             response_text = raw_content or (e.response.text[:500] if hasattr(e.response, 'text') else "[No Response Body]")
             status_code = e.response.status_code
             logger.error(f"HTTP error during search result processing", exc_info=False,
                         extra={ "status_code": status_code, "response_text": response_text, "vendor": vendor_name, "attempt_id": attempt_id, "key_index_used": self.current_key_index })
             # Log HTTP Error (already present)
             llm_trace_logger.error(f"LLM_TRACE: LLM API HTTP Error (Attempt ID: {attempt_id}): Status={status_code}, Response='{response_text}'", exc_info=True, extra={'correlation_id': correlation_id})

             # --- Key Rotation Logic (already present) ---
             if status_code in OPENROUTER_ROTATION_STATUS_CODES:
                 self._rotate_key()
             # --- END Key Rotation Logic ---
             raise # Re-raise for tenacity

        except httpx.RequestError as e:
             logger.error(f"Network error during search result processing", exc_info=False,
                         extra={ "error_details": str(e), "vendor": vendor_name, "attempt_id": attempt_id, "key_index_used": self.current_key_index })
             # Log Network Error (already present)
             llm_trace_logger.error(f"LLM_TRACE: LLM API Network Error (Attempt ID: {attempt_id}): {e}", exc_info=True, extra={'correlation_id': correlation_id})
             # Optionally rotate on network errors
             # self._rotate_key()
             raise # Re-raise for tenacity

        except ValueError as ve: # Catch the specific error raised on JSON parse failure
             logger.error(f"LLM response parsing error during search result processing", exc_info=False,
                          extra={"error": str(ve), "vendor": vendor_name, "attempt_id": attempt_id})
             # Don't rotate on parse errors
             raise # Re-raise for tenacity

        except Exception as e:
            error_context = { "vendor": vendor_name, "error": str(e), "model": self.model, "attempt_id": attempt_id, "key_index_used": self.current_key_index }
            logger.error(f"Unexpected error during search result processing", exc_info=True, extra=error_context)
            # Log Unexpected Error (already present)
            llm_trace_logger.error(f"LLM_TRACE: LLM Unexpected Error (Attempt ID: {attempt_id}): {e}", exc_info=True, extra={'correlation_id': correlation_id})
            # Optionally rotate on unexpected errors
            # self._rotate_key()
            raise # Re-raise for tenacity