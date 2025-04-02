# file path='app/services/search_service.py'
import httpx
import logging
from typing import Dict, Any, List
from tenacity import retry, stop_after_attempt, wait_exponential
import time # Added import

from core.config import settings

from core.logging_config import get_logger, LogTimer, log_function_call, set_log_context
from utils.log_utils import log_api_request

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
    @log_api_request("tavily_search")
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

        try:
            logger.debug(f"Sending request to Tavily API")

            # Set up request parameters
            payload = {
                "api_key": self.api_key,
                "query": search_query,
                "search_depth": "advanced", # Use advanced for potentially better results
                "include_answer": True, # Request a summary answer
                # "include_domains": [ # Consider if specific domains are truly helpful or too limiting
                #     "linkedin.com", "bloomberg.com", "dnb.com",
                #     "zoominfo.com", "crunchbase.com"
                # ],
                "max_results": 5 # Limit number of results to process
            }
            logger.debug(f"Request parameters prepared",
                       extra={
                           "search_depth": payload["search_depth"],
                           "max_results": payload["max_results"],
                           # "include_domains": payload.get("include_domains")
                       })

            async with httpx.AsyncClient() as client:
                with LogTimer(logger, "Tavily API request", include_in_stats=True):
                    response = await client.post(
                        f"{self.base_url}/search", # Corrected endpoint path
                        json=payload,
                        timeout=30.0
                    )
                    response.raise_for_status() # Raise HTTPStatusError for 4xx/5xx
                    search_results = response.json()

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
                    for result in search_results.get("results", []) if result.get("url") # Filter out results without URL?
                ],
                "summary": search_results.get("answer", ""), # Use the summary if provided
                "error": None # Explicitly set error to None on success
            }
            logger.info(f"Tavily search successful", extra={"vendor": vendor_name, "results_found": len(processed_results["sources"])})
            return processed_results

        except httpx.HTTPStatusError as e:
            response_text = e.response.text[:500] if hasattr(e.response, 'text') else "No response body"
            logger.error(f"Tavily API HTTP error for vendor '{vendor_name}'", exc_info=True,
                         extra={"status_code": e.response.status_code, "response": response_text})
            return {
                "vendor": vendor_name,
                "error": f"Tavily API returned status {e.response.status_code}: {response_text}",
                "search_query": search_query,
                "sources": []
            }
        except httpx.RequestError as e:
             logger.error(f"Tavily API request error for vendor '{vendor_name}'", exc_info=True)
             return {
                "vendor": vendor_name,
                "error": f"Tavily API request failed: {str(e)}",
                "search_query": search_query,
                "sources": []
             }
        except Exception as e:
            logger.error(f"Unexpected error during Tavily search for vendor '{vendor_name}'", exc_info=True)
            return {
                "vendor": vendor_name,
                "error": f"Unexpected error during search: {str(e)}",
                "search_query": search_query,
                "sources": []
            }