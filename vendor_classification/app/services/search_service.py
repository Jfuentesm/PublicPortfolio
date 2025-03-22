import httpx
import logging
from typing import Dict, Any, List
from tenacity import retry, stop_after_attempt, wait_exponential

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
        self.base_url = "https://api.tavily.com/v1"
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
            Search results
        """
        logger.info(f"Searching for vendor information", 
                   extra={"vendor": vendor_name})
        set_log_context({"vendor": vendor_name})
        search_query = f"{vendor_name} company business type industry"
        logger.debug(f"Generated search query", 
                   extra={"search_query": search_query})
        
        try:
            logger.debug(f"Sending request to Tavily API")
            
            # Set up request parameters
            request_params = {
                "api_key": self.api_key,
                "query": search_query,
                "search_depth": "advanced",
                "include_domains": [
                    "linkedin.com", "bloomberg.com", "dnb.com", 
                    "zoominfo.com", "crunchbase.com"
                ],
                "max_results": 5
            }
            logger.debug(f"Request parameters prepared", 
                       extra={
                           "search_depth": request_params["search_depth"],
                           "max_results": request_params["max_results"],
                           "include_domains": request_params["include_domains"]
                       })
            async with httpx.AsyncClient() as client:
                with LogTimer(logger, "Tavily API request", include_in_stats=True):
                    response = await client.post(
                    f"{self.base_url}/search",
                    json={
                        "api_key": self.api_key,
                        "query": search_query,
                        "search_depth": "advanced",
                        "include_domains": [
                            "linkedin.com", "bloomberg.com", "dnb.com", 
                            "zoominfo.com", "crunchbase.com"
                        ],
                        "max_results": 5
                    },
                    timeout=30.0
                )
                
                response.raise_for_status()
                search_results = response.json()
                
                # Extract relevant information from search results
                processed_results = {
                    "vendor": vendor_name,
                    "search_query": search_query,
                    "sources": [
                        {
                            "title": result.get("title", ""),
                            "url": result.get("url", ""),
                            "content": result.get("content", "")[:500]  # Limit content size
                        }
                        for result in search_results.get("results", [])
                    ],
                    "summary": search_results.get("answer", "")
                }
                
                return processed_results
        
        except Exception as e:
            logging.error(f"Tavily API error for vendor '{vendor_name}': {e}")
            return {
                "vendor": vendor_name,
                "error": str(e),
                "search_query": search_query,
                "sources": []
            }
