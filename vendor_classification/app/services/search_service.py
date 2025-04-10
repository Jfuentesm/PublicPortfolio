# app/services/search_service.py

import httpx
import logging
from typing import Dict, Any, List, Optional # Added Optional
from tenacity import retry, stop_after_attempt, wait_exponential, RetryError
import time
import uuid
import json

from core.config import settings
from core.logging_config import get_logger
from core.log_context import set_log_context, get_correlation_id
from utils.log_utils import LogTimer, log_function_call

llm_trace_logger = logging.getLogger("llm_api_trace")
logger = get_logger("vendor_classification.search_service")

# --- Status codes that trigger key rotation ---
# UPDATED: Added 432 (Tavily specific usage limit code) to the set
TAVILY_ROTATION_STATUS_CODES = {400, 401, 403, 429, 432, 500, 502, 503, 504}

class SearchService:
    """Service for interacting with Tavily Search API, with key rotation."""

    def __init__(self):
        """Initialize the search service."""
        logger.info("Initializing Tavily Search service with key rotation")
        self.api_keys = settings.TAVILY_API_KEYS
        self.base_url = "https://api.tavily.com"
        self.current_key_index = 0

        if not self.api_keys:
            logger.error("Tavily API key list is empty! Search calls will fail.")
            # Optionally raise an exception
            # raise ValueError("Tavily API keys are missing in configuration.")

        logger.debug("Search service initialized",
                   extra={"api_endpoint": self.base_url,
                          "key_count": len(self.api_keys),
                          "rotation_codes": sorted(list(TAVILY_ROTATION_STATUS_CODES))}) # Log rotation codes sorted

    def _get_current_key(self) -> Optional[str]:
        """Gets the current API key based on the index."""
        if not self.api_keys:
            logger.warning("Attempted to get Tavily key, but key list is empty.")
            return None
        # Ensure index is always valid, even if list shrinks dynamically (though unlikely here)
        if self.current_key_index >= len(self.api_keys):
            logger.warning(f"Tavily key index {self.current_key_index} out of bounds ({len(self.api_keys)} keys). Resetting to 0.")
            self.current_key_index = 0
        return self.api_keys[self.current_key_index]

    def _rotate_key(self):
        """Rotates to the next API key in the list."""
        if not self.api_keys or len(self.api_keys) <= 1:
            logger.warning("Cannot rotate Tavily key: list is empty or has only one key.")
            return # No rotation possible

        old_index = self.current_key_index
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        logger.warning(f"Rotated Tavily API key from index {old_index} to {self.current_key_index} due to API error.")

    # Increased retries slightly for search as it might be less critical than LLM? Or keep same.
    @retry(stop=stop_after_attempt(settings.MAX_RETRIES), wait=wait_exponential(multiplier=1, min=1, max=10))
    @log_function_call(logger)
    async def search_vendor(self, vendor_name: str) -> Dict[str, Any]:
        """
        Search for information about a vendor, with key rotation on failure.
        """
        logger.info(f"Searching for vendor information",
                   extra={"vendor": vendor_name})
        set_log_context({"vendor": vendor_name})
        # Basic query sanitization attempt (remove potential control characters, excessive whitespace)
        sanitized_vendor_name = ' '.join(str(vendor_name).split())
        search_query = f"{sanitized_vendor_name} company business type industry"
        if vendor_name != sanitized_vendor_name:
             logger.debug(f"Sanitized vendor name for search query", extra={"original": vendor_name, "sanitized": sanitized_vendor_name})

        logger.debug(f"Generated search query",
                   extra={"search_query": search_query})

        # --- Get current key ---
        current_api_key = self._get_current_key()
        if not current_api_key:
             logger.error("Cannot perform Tavily search: No API key available.")
             # Return error structure consistent with API failures
             return {
                "vendor": vendor_name, # Return original name here
                "error": "Tavily API key not configured",
                "search_query": search_query,
                "sources": [],
                "summary": None # Ensure summary is None on error
             }
        # --- End get current key ---

        correlation_id = get_correlation_id()
        search_attempt_id = str(uuid.uuid4())
        llm_trace_logger.debug(f"LLM_TRACE: Starting Tavily Search (Attempt ID: {search_attempt_id}, Vendor: {vendor_name})", extra={'correlation_id': correlation_id})

        response = None; raw_content = None; response_data = None; status_code = None
        try:
            logger.debug(f"Sending request to Tavily API using key index {self.current_key_index}")

            payload_for_log = { # Redact key for logging
                "api_key": f"[REDACTED_KEY_INDEX_{self.current_key_index}]",
                "query": search_query,
                "search_depth": "advanced",
                "include_answer": True,
                "max_results": 5
            }
            headers = {"Content-Type": "application/json"}

            # Trace Logging for Request
            try:
                llm_trace_logger.debug(f"LLM_TRACE: Tavily Request Headers (Attempt ID: {search_attempt_id}):\n{json.dumps(headers, indent=2)}", extra={'correlation_id': correlation_id})
                llm_trace_logger.debug(f"LLM_TRACE: Tavily Request Payload (Attempt ID: {search_attempt_id}):\n{json.dumps(payload_for_log, indent=2)}", extra={'correlation_id': correlation_id})
            except Exception as log_err:
                 llm_trace_logger.warning(f"LLM_TRACE: Failed to log Tavily request details (Attempt ID: {search_attempt_id}): {log_err}", extra={'correlation_id': correlation_id})

            actual_payload = payload_for_log.copy()
            actual_payload["api_key"] = current_api_key # Use the actual key for the request

            async with httpx.AsyncClient() as client:
                with LogTimer(logger, "Tavily API request", include_in_stats=True):
                    start_time = time.time()
                    response = await client.post(
                        f"{self.base_url}/search",
                        json=actual_payload,
                        headers=headers,
                        timeout=30.0
                    )
                    api_duration = time.time() - start_time
                    raw_content = response.text
                    status_code = response.status_code
                    # Trace Logging for Response
                    llm_trace_logger.debug(f"LLM_TRACE: Tavily Raw Response (Attempt ID: {search_attempt_id}, Status: {status_code}, Duration: {api_duration:.3f}s):\n-------\n{raw_content or '[No Content Received]'}\n-------", extra={'correlation_id': correlation_id})
                    response.raise_for_status() # Raise HTTPStatusError for 4xx/5xx AFTER logging
                    response_data = response.json()

            processed_results = {
                "vendor": vendor_name, # Return original name
                "search_query": search_query,
                "sources": [
                    {
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "content": result.get("content", "")
                    }
                    for result in response_data.get("results", []) if result.get("url") and result.get("content") # Ensure content exists
                ],
                "summary": response_data.get("answer", ""),
                "error": None
            }
            logger.info(f"Tavily search successful", extra={"vendor": vendor_name, "results_found": len(processed_results["sources"]), "key_index_used": self.current_key_index})
            return processed_results

        except httpx.HTTPStatusError as e:
             response_text = raw_content or (e.response.text[:500] if hasattr(e.response, 'text') else "[No Response Body]")
             status_code = e.response.status_code
             logger.error(f"Tavily API HTTP error for vendor '{vendor_name}'", exc_info=False, # exc_info=False for less noise, trace log has it
                         extra={"status_code": status_code, "response": response_text, "key_index_used": self.current_key_index, "attempt_id": search_attempt_id})
             llm_trace_logger.error(f"LLM_TRACE: Tavily API HTTP Error (Attempt ID: {search_attempt_id}): Status={status_code}, Response='{response_text}'", exc_info=True, extra={'correlation_id': correlation_id})

             # --- Key Rotation Logic ---
             if status_code in TAVILY_ROTATION_STATUS_CODES:
                 self._rotate_key() # Rotate if the status code matches
             else:
                 logger.warning(f"HTTP Status Code {status_code} not in TAVILY_ROTATION_STATUS_CODES. Key will not be rotated for this error.", extra={"vendor": vendor_name})
             # --- END Key Rotation Logic ---

             # Re-raise *after* potential rotation for tenacity to handle retry
             raise # Re-raise for tenacity

        except httpx.RequestError as e:
             # Network errors (connection, timeout etc.)
             logger.error(f"Tavily API request error for vendor '{vendor_name}'", exc_info=False, # exc_info=False for less noise, trace log has it
                          extra={"error_details": str(e), "key_index_used": self.current_key_index, "attempt_id": search_attempt_id})
             llm_trace_logger.error(f"LLM_TRACE: Tavily API Network Error (Attempt ID: {search_attempt_id}): {e}", exc_info=True, extra={'correlation_id': correlation_id})
             # Optionally rotate on specific network errors? Less common for key issues.
             # self._rotate_key()
             raise # Re-raise for tenacity

        except json.JSONDecodeError as e:
             # Handle cases where Tavily returns non-JSON response with 200 OK (unlikely but possible)
             logger.error(f"Failed to decode JSON response from Tavily for vendor '{vendor_name}'", exc_info=False,
                          extra={"response_preview": raw_content[:500] if raw_content else "N/A", "key_index_used": self.current_key_index, "attempt_id": search_attempt_id})
             llm_trace_logger.error(f"LLM_TRACE: Tavily JSON Decode Error (Attempt ID: {search_attempt_id}): {e}. Raw Content: {raw_content or 'N/A'}", exc_info=True, extra={'correlation_id': correlation_id})
             # Don't rotate key for JSON errors. Re-raise for tenacity.
             # Treat as a failure like other exceptions.
             raise ValueError(f"Tavily response was not valid JSON: {str(e)}") from e

        except Exception as e:
            # Catch any other unexpected errors during the process
            logger.error(f"Unexpected error during Tavily search for vendor '{vendor_name}'", exc_info=True, # Include stack trace for unexpected
                         extra={"key_index_used": self.current_key_index, "attempt_id": search_attempt_id})
            llm_trace_logger.error(f"LLM_TRACE: Tavily Unexpected Error (Attempt ID: {search_attempt_id}): {e}", exc_info=True, extra={'correlation_id': correlation_id})
            # Optionally rotate on unexpected errors? Could hide other issues.
            # self._rotate_key()
            raise # Re-raise for tenacity


