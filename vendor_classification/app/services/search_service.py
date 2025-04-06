# file path='app/services/search_service.py'
import httpx
import logging
from typing import Dict, Any, List
from tenacity import retry, stop_after_attempt, wait_exponential
import time # Added import
import uuid # Added import
import json # Added import

from core.config import settings

# --- ADDED: Import trace logger and correlation ID getter ---
from core.logging_config import get_logger, LogTimer, log_function_call, set_log_context, get_correlation_id
from utils.log_utils import log_api_request # Keep for potential other uses
llm_trace_logger = logging.getLogger("llm_api_trace") # Get the trace logger
# --- END ADDED ---

# Configure logger
logger = get_logger("vendor_classification.search_service")

class SearchService:
    """Service for interacting with Tavily Search API."""

    def __init__(self):
        """Initialize the search service."""
        logger.info("Initializing Tavily Search service")
        self.api_key = settings.TAVILY_API_KEY
        self.base_url = "https://api.tavily.com" # Removed /v1 from base_url
        if not self.api_key:
            logger.error("Tavily API key is missing!")
            # Depending on requirements, you might want to raise an error here
            # raise ValueError("Tavily API key not configured")
        logger.debug("Search service initialized",
                   extra={"api_endpoint": self.base_url})

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    @log_function_call(logger)
    # @log_api_request("tavily_search") # Keep decorator if desired, but add explicit trace logging below
    async def search_vendor(self, vendor_name: str) -> Dict[str, Any]:
        """
        Search for information about a vendor.

        Args:
            vendor_name: Vendor name

        Returns:
            Search results including sources, summary, or error.
        """
        logger.info(f"Searching for vendor information",
                   extra={"vendor": vendor_name})
        set_log_context({"vendor": vendor_name})
        search_query = f"{vendor_name} company business type industry"
        logger.debug(f"Generated search query",
                   extra={"search_query": search_query})

        if not self.api_key:
             logger.error("Cannot perform Tavily search: API key is missing.")
             return {
                "vendor": vendor_name,
                "error": "Tavily API key not configured",
                "search_query": search_query,
                "sources": []
             }

        correlation_id = get_correlation_id() # Get correlation ID
        search_attempt_id = str(uuid.uuid4()) # Unique ID for this specific search attempt
        llm_trace_logger.debug(f"LLM_TRACE: Starting Tavily Search (Attempt ID: {search_attempt_id}, Vendor: {vendor_name})", extra={'correlation_id': correlation_id})

        response = None; raw_content = None; response_data = None; status_code = None
        try:
            logger.debug(f"Sending request to Tavily API")

            # Set up request parameters
            payload = {
                "api_key": "[REDACTED]", # Redact for logging payload
                "query": search_query,
                "search_depth": "advanced", # Use advanced for potentially better results
                "include_answer": True, # Request a summary answer
                "max_results": 5 # Limit number of results to process
            }
            headers = {"Content-Type": "application/json"}

            # --- ADDED: Trace Logging for Request ---
            try:
                llm_trace_logger.debug(f"LLM_TRACE: Tavily Request Headers (Attempt ID: {search_attempt_id}):\n{json.dumps(headers, indent=2)}", extra={'correlation_id': correlation_id})
                llm_trace_logger.debug(f"LLM_TRACE: Tavily Request Payload (Attempt ID: {search_attempt_id}):\n{json.dumps(payload, indent=2)}", extra={'correlation_id': correlation_id})
            except Exception as log_err:
                 llm_trace_logger.warning(f"LLM_TRACE: Failed to log Tavily request details (Attempt ID: {search_attempt_id}): {log_err}", extra={'correlation_id': correlation_id})
            # --- END ADDED ---

            # Prepare actual payload with key
            actual_payload = payload.copy()
            actual_payload["api_key"] = self.api_key

            async with httpx.AsyncClient() as client:
                with LogTimer(logger, "Tavily API request", include_in_stats=True):
                    start_time = time.time() # Manual timing for trace log
                    response = await client.post(
                        f"{self.base_url}/search",
                        json=actual_payload, # Use payload with actual key
                        headers=headers,
                        timeout=30.0
                    )
                    api_duration = time.time() - start_time
                    raw_content = response.text # Get raw text immediately
                    status_code = response.status_code
                    # --- ADDED: Trace Logging for Response ---
                    llm_trace_logger.debug(f"LLM_TRACE: Tavily Raw Response (Attempt ID: {search_attempt_id}, Status: {status_code}, Duration: {api_duration:.3f}s):\n-------\n{raw_content or '[No Content Received]'}\n-------", extra={'correlation_id': correlation_id})
                    # --- END ADDED ---
                    response.raise_for_status() # Check for HTTP errors AFTER logging raw response
                    response_data = response.json() # Parse JSON only if status is OK

            # Extract relevant information from search results
            processed_results = {
                "vendor": vendor_name,
                "search_query": search_query,
                "sources": [
                    {
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "content": result.get("content", "") # Keep full content for LLM, truncate later if needed
                    }
                    for result in response_data.get("results", []) if result.get("url") # Filter out results without URL?
                ],
                "summary": response_data.get("answer", ""), # Use the summary if provided
                "error": None # Explicitly set error to None on success
            }
            logger.info(f"Tavily search successful", extra={"vendor": vendor_name, "results_found": len(processed_results["sources"])})
            return processed_results

        except httpx.HTTPStatusError as e:
             response_text = raw_content or (e.response.text[:500] if hasattr(e.response, 'text') else "[No Response Body]")
             status_code = e.response.status_code
             logger.error(f"Tavily API HTTP error for vendor '{vendor_name}'", exc_info=False,
                         extra={"status_code": status_code, "response": response_text})
             # --- ADDED: Trace Logging for HTTP Error ---
             llm_trace_logger.error(f"LLM_TRACE: Tavily API HTTP Error (Attempt ID: {search_attempt_id}): Status={status_code}, Response='{response_text}'", exc_info=True, extra={'correlation_id': correlation_id})
             # --- END ADDED ---
             return {
                "vendor": vendor_name,
                "error": f"Tavily API returned status {status_code}: {response_text}",
                "search_query": search_query,
                "sources": []
             }
        except httpx.RequestError as e:
             logger.error(f"Tavily API request error for vendor '{vendor_name}'", exc_info=False, extra={"error_details": str(e)})
             # --- ADDED: Trace Logging for Request Error ---
             llm_trace_logger.error(f"LLM_TRACE: Tavily API Network Error (Attempt ID: {search_attempt_id}): {e}", exc_info=True, extra={'correlation_id': correlation_id})
             # --- END ADDED ---
             return {
                "vendor": vendor_name,
                "error": f"Tavily API request failed: {str(e)}",
                "search_query": search_query,
                "sources": []
             }
        except Exception as e:
            logger.error(f"Unexpected error during Tavily search for vendor '{vendor_name}'", exc_info=True)
            # --- ADDED: Trace Logging for Unexpected Error ---
            llm_trace_logger.error(f"LLM_TRACE: Tavily Unexpected Error (Attempt ID: {search_attempt_id}): {e}", exc_info=True, extra={'correlation_id': correlation_id})
            # --- END ADDED ---
            return {
                "vendor": vendor_name,
                "error": f"Unexpected error during search: {str(e)}",
                "search_query": search_query,
                "sources": []
            }

# </file>