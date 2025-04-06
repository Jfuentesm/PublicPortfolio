
# app/services/search_service.py
import httpx
import logging
from typing import Dict, Any, List
from tenacity import retry, stop_after_attempt, wait_exponential
import time
import uuid
import json

from core.config import settings
# Import logger and context functions from refactored modules
from core.logging_config import get_logger
from core.log_context import set_log_context, get_correlation_id
# Import log helpers from utils
from utils.log_utils import LogTimer, log_function_call

llm_trace_logger = logging.getLogger("llm_api_trace") # Get the trace logger
logger = get_logger("vendor_classification.search_service")

class SearchService:
    """Service for interacting with Tavily Search API."""

    def __init__(self):
        """Initialize the search service."""
        logger.info("Initializing Tavily Search service")
        self.api_key = settings.TAVILY_API_KEY
        self.base_url = "https://api.tavily.com"
        if not self.api_key:
            logger.error("Tavily API key is missing!")
        logger.debug("Search service initialized",
                   extra={"api_endpoint": self.base_url})

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    @log_function_call(logger)
    async def search_vendor(self, vendor_name: str) -> Dict[str, Any]:
        """
        Search for information about a vendor.
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

            payload = {
                "api_key": "[REDACTED]", # Redact for logging payload
                "query": search_query,
                "search_depth": "advanced",
                "include_answer": True,
                "max_results": 5
            }
            headers = {"Content-Type": "application/json"}

            # Trace Logging for Request
            try:
                llm_trace_logger.debug(f"LLM_TRACE: Tavily Request Headers (Attempt ID: {search_attempt_id}):\n{json.dumps(headers, indent=2)}", extra={'correlation_id': correlation_id})
                llm_trace_logger.debug(f"LLM_TRACE: Tavily Request Payload (Attempt ID: {search_attempt_id}):\n{json.dumps(payload, indent=2)}", extra={'correlation_id': correlation_id})
            except Exception as log_err:
                 llm_trace_logger.warning(f"LLM_TRACE: Failed to log Tavily request details (Attempt ID: {search_attempt_id}): {log_err}", extra={'correlation_id': correlation_id})

            actual_payload = payload.copy()
            actual_payload["api_key"] = self.api_key

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
                    response.raise_for_status()
                    response_data = response.json()

            processed_results = {
                "vendor": vendor_name,
                "search_query": search_query,
                "sources": [
                    {
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "content": result.get("content", "")
                    }
                    for result in response_data.get("results", []) if result.get("url")
                ],
                "summary": response_data.get("answer", ""),
                "error": None
            }
            logger.info(f"Tavily search successful", extra={"vendor": vendor_name, "results_found": len(processed_results["sources"])})
            return processed_results

        except httpx.HTTPStatusError as e:
             response_text = raw_content or (e.response.text[:500] if hasattr(e.response, 'text') else "[No Response Body]")
             status_code = e.response.status_code
             logger.error(f"Tavily API HTTP error for vendor '{vendor_name}'", exc_info=False,
                         extra={"status_code": status_code, "response": response_text})
             llm_trace_logger.error(f"LLM_TRACE: Tavily API HTTP Error (Attempt ID: {search_attempt_id}): Status={status_code}, Response='{response_text}'", exc_info=True, extra={'correlation_id': correlation_id})
             return { "vendor": vendor_name, "error": f"Tavily API returned status {status_code}: {response_text}", "search_query": search_query, "sources": [] }
        except httpx.RequestError as e:
             logger.error(f"Tavily API request error for vendor '{vendor_name}'", exc_info=False, extra={"error_details": str(e)})
             llm_trace_logger.error(f"LLM_TRACE: Tavily API Network Error (Attempt ID: {search_attempt_id}): {e}", exc_info=True, extra={'correlation_id': correlation_id})
             return { "vendor": vendor_name, "error": f"Tavily API request failed: {str(e)}", "search_query": search_query, "sources": [] }
        except Exception as e:
            logger.error(f"Unexpected error during Tavily search for vendor '{vendor_name}'", exc_info=True)
            llm_trace_logger.error(f"LLM_TRACE: Tavily Unexpected Error (Attempt ID: {search_attempt_id}): {e}", exc_info=True, extra={'correlation_id': correlation_id})
            return { "vendor": vendor_name, "error": f"Unexpected error during search: {str(e)}", "search_query": search_query, "sources": [] }