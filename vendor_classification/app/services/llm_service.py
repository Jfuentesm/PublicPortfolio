# file path='app/services/llm_service.py'
# app/services/llm_service.py
import httpx
import json
from typing import List, Dict, Any, Optional
import logging # <<< Ensure logging is imported
import time
import uuid # <<< Added import
from tenacity import retry, stop_after_attempt, wait_exponential

from core.config import settings
from models.taxonomy import Taxonomy, TaxonomyCategory # <<< Added TaxonomyCategory
from core.logging_config import get_logger, LogTimer, log_function_call, set_log_context
from utils.log_utils import log_api_request, log_method # <<< Ensure log_method is imported if used

# Configure logger
logger = get_logger("vendor_classification.llm_service")

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
    @log_api_request("openrouter")
    async def classify_batch(
        self,
        batch: List[str],
        level: int,
        taxonomy: Taxonomy,
        parent_category_id: Optional[str] = None # Renamed for clarity
    ) -> Dict[str, Any]:
        """
        Send a batch of vendors to LLM for classification.

        Args:
            batch: List of vendor names
            level: Classification level (1-4)
            taxonomy: Taxonomy data
            parent_category_id: Parent category ID (required for levels 2-4)

        Returns:
            Classification results and API usage data.
        """
        logger.info(f"Classifying vendor batch",
                   extra={
                       "batch_size": len(batch),
                       "level": level,
                       "parent_category_id": parent_category_id
                   })
        set_log_context({"vendor_count": len(batch), "taxonomy_level": level})
        batch_id = str(uuid.uuid4()) # Use UUID for uniqueness
        logger.debug(f"Generated batch ID", extra={"batch_id": batch_id})

        if not self.api_key:
            logger.error("Cannot classify batch: OpenRouter API key is missing.")
            # Return an error structure consistent with expected output but indicating failure
            return {
                "result": {
                    "level": level,
                    "batch_id": batch_id,
                    "parent_category_id": parent_category_id,
                    "classifications": [
                        {
                            "vendor_name": vendor, "category_id": "ERROR", "category_name": "ERROR",
                            "confidence": 0.0, "classification_not_possible": True,
                            "classification_not_possible_reason": "API key missing"
                        } for vendor in batch
                    ]
                },
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            }

        # --- UPDATED PROMPT CREATION ---
        logger.debug(f"Creating classification prompt")
        with LogTimer(logger, "Prompt creation", include_in_stats=True):
            # Pass parent_category_id instead of parent_category string
            prompt = self._create_classification_prompt(batch, level, taxonomy, parent_category_id, batch_id)
            # Log prompt length but not full content for security/verbosity
            prompt_length = len(prompt)
            logger.debug(f"Classification prompt created",
                        extra={"prompt_length": prompt_length})
        # --- END UPDATED PROMPT CREATION ---

        # Call OpenRouter API
        try:
            logger.debug(f"Sending request to OpenRouter API")
            start_time = time.time()

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "naicsvendorclassification.com",  # Replace with your actual domain
                "X-Title": "NAICS Vendor Classification" # Optional: Helps OpenRouter identify your app
            }

            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a precise vendor classification expert using the NAICS taxonomy. Adhere strictly to the provided categories and JSON output format. Do not guess if unsure. Ensure the `batch_id` in the output matches the one provided in the prompt."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1, # Lower temperature for more deterministic results
                "max_tokens": 2048, # Adjusted based on typical JSON size needs
                "top_p": 0.9, # Adjusted slightly
                "frequency_penalty": 0,
                "presence_penalty": 0,
                "response_format": {"type": "json_object"} # Request JSON output directly if model supports it
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=90.0 # Increased timeout
                )
                response.raise_for_status()
                response_data = response.json()

            api_duration = time.time() - start_time

            # Extract usage information
            usage = response_data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)

            # --- USE CORRECT KEYS FOR LOGGING ---
            logger.info(f"OpenRouter API response received",
                       extra={
                           "duration": api_duration,
                           "batch_id": batch_id,
                           "openrouter_prompt_tokens": prompt_tokens,
                           "openrouter_completion_tokens": completion_tokens,
                           "openrouter_total_tokens": total_tokens
                       })
            # --- END USE CORRECT KEYS FOR LOGGING ---

            # Parse response
            content = response_data["choices"][0]["message"]["content"]

            # Extract JSON from response
            try:
                with LogTimer(logger, "JSON parsing", include_in_stats=True):
                    # If response_format was used, content should already be JSON string
                    result = json.loads(content)
                    logger.debug(f"Successfully parsed JSON response")

                # --- Validate Batch ID ---
                response_batch_id = result.get("batch_id")
                if response_batch_id != batch_id:
                    logger.warning(f"LLM response batch_id mismatch!",
                                   extra={"expected_batch_id": batch_id, "received_batch_id": response_batch_id})
                    # Decide how to handle: raise error, proceed with caution, etc.
                    # For now, log warning and proceed, but ensure the calling function knows.
                    result["batch_id_mismatch"] = True # Add a flag
                # --- End Validate Batch ID ---

                # Track token usage
                usage_data = {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens
                }

                # --- USE CORRECT KEYS FOR CONTEXT ---
                set_log_context({
                    "openrouter_prompt_tokens": prompt_tokens,
                    "openrouter_completion_tokens": completion_tokens,
                    "openrouter_total_tokens": total_tokens
                })
                # --- END USE CORRECT KEYS FOR CONTEXT ---

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

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response from LLM",
                            exc_info=False, # Don't need full traceback usually
                            extra={
                                "error": str(e),
                                "content_preview": content[:500] if content else None, # Increased preview
                                "batch_id": batch_id,
                                "level": level
                            })
                # Raise a specific error that the task can potentially handle or log appropriately
                raise ValueError(f"LLM response was not valid JSON. Preview: {content[:200]}")

        except httpx.HTTPStatusError as e:
             logger.error(f"HTTP error during LLM batch classification", exc_info=True,
                         extra={ "status_code": e.response.status_code, "response_text": e.response.text[:200], "batch_id": batch_id, "level": level })
             raise # Re-raise after logging
        except httpx.RequestError as e:
             logger.error(f"Network error during LLM batch classification", exc_info=True,
                         extra={ "error_details": str(e), "batch_id": batch_id, "level": level })
             raise # Re-raise after logging
        except Exception as e:
            # Capture request parameters for error logging
            error_context = {
                "batch_size": len(batch),
                "level": level,
                "parent_category_id": parent_category_id,
                "error": str(e),
                "model": self.model,
                "batch_id": batch_id
            }
            logger.error(f"Unexpected error during LLM batch classification", exc_info=True, extra=error_context)
            raise # Re-raise after logging

    @retry(stop=stop_after_attempt(settings.MAX_RETRIES), wait=wait_exponential(multiplier=1, min=settings.RETRY_DELAY, max=10))
    @log_function_call(logger, include_args=False) # Don't log full search results here
    @log_api_request("openrouter")
    async def process_search_results(
        self,
        vendor: str,
        search_results: Dict[str, Any],
        taxonomy: Taxonomy
    ) -> Dict[str, Any]:
        """
        Process search results to determine classification.

        Args:
            vendor: Vendor name
            search_results: Search results from Tavily
            taxonomy: Taxonomy data

        Returns:
            Classification result (Level 1 attempt) and API usage data.
        """
        logger.info(f"Processing search results for vendor classification",
                   extra={
                       "vendor": vendor,
                       "source_count": len(search_results.get("sources", []))
                   })
        set_log_context({"vendor": vendor})
        attempt_id = str(uuid.uuid4()) # Unique ID for this attempt
        logger.debug(f"Generated search processing attempt ID", extra={"attempt_id": attempt_id})

        if not self.api_key:
            logger.error("Cannot process search results: OpenRouter API key is missing.")
            return {
                "result": {
                    "vendor_name": vendor, "category_id": "ERROR", "category_name": "ERROR",
                    "confidence": 0.0, "classification_not_possible": True,
                    "classification_not_possible_reason": "API key missing", "notes": ""
                },
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            }

        # --- UPDATED PROMPT CREATION ---
        with LogTimer(logger, "Search prompt creation", include_in_stats=True):
            prompt = self._create_search_results_prompt(vendor, search_results, taxonomy)
            # Log prompt length but not content
            prompt_length = len(prompt)
            logger.debug(f"Search results prompt created",
                        extra={"prompt_length": prompt_length})
        # --- END UPDATED PROMPT CREATION ---

        # Call OpenRouter API
        try:
            logger.debug(f"Sending search results to OpenRouter API")
            start_time = time.time()

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "naicsvendorclassification.com",  # Replace with your actual domain
                "X-Title": "NAICS Vendor Classification"
            }

            payload = {
                "model": self.model,
                "messages": [
                    # --- SYSTEM PROMPT SLIGHTLY REFINED ---
                    {"role": "system", "content": "You are a precise vendor classification expert using the NAICS taxonomy. Analyze the provided search results *only* to determine the vendor's primary business activity and classify it into the given Level 1 categories. Adhere strictly to the JSON output format. If information is insufficient or contradictory, state 'classification_not_possible'."},
                    # --- END SYSTEM PROMPT REFINEMENT ---
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1, # Lower temperature
                "max_tokens": 1024, # Reduced slightly, only need one classification
                "top_p": 0.9,
                "frequency_penalty": 0,
                "presence_penalty": 0,
                "response_format": {"type": "json_object"} # Request JSON output directly
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=60.0
                )
                response.raise_for_status()
                response_data = response.json()

            api_duration = time.time() - start_time

            # Extract usage information
            usage = response_data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)

            # --- USE CORRECT KEYS FOR LOGGING ---
            logger.info(f"OpenRouter API response received for search results",
                       extra={
                           "duration": api_duration,
                           "vendor": vendor,
                           "openrouter_prompt_tokens": prompt_tokens,
                           "openrouter_completion_tokens": completion_tokens,
                           "openrouter_total_tokens": total_tokens,
                           "attempt_id": attempt_id
                       })
            # --- END USE CORRECT KEYS FOR LOGGING ---

            # Parse response
            content = response_data["choices"][0]["message"]["content"]

            # Extract JSON from response
            try:
                with LogTimer(logger, "JSON parsing", include_in_stats=True):
                    result = json.loads(content)
                    logger.debug(f"Successfully parsed JSON response for search result processing")

                # --- Validate Vendor Name ---
                response_vendor = result.get("vendor_name")
                if response_vendor != vendor:
                    logger.warning(f"LLM search response vendor name mismatch!",
                                   extra={"expected_vendor": vendor, "received_vendor": response_vendor})
                    # Overwrite with expected vendor name for consistency downstream
                    result["vendor_name"] = vendor
                # --- End Validate Vendor Name ---

                # Track token usage
                usage_data = {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens
                }

                # --- USE CORRECT KEYS FOR CONTEXT ---
                set_log_context({
                    "openrouter_prompt_tokens": prompt_tokens,
                    "openrouter_completion_tokens": completion_tokens,
                    "openrouter_total_tokens": total_tokens
                })
                # --- END USE CORRECT KEYS FOR CONTEXT ---

                return {
                    "result": result,
                    "usage": usage_data
                }

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response from LLM after search",
                            exc_info=False,
                            extra={
                                "error": str(e),
                                "content_preview": content[:500] if content else None,
                                "vendor": vendor,
                                "attempt_id": attempt_id
                            })
                raise ValueError(f"LLM response after search was not valid JSON. Preview: {content[:200]}")

        except httpx.HTTPStatusError as e:
             logger.error(f"HTTP error during search result processing", exc_info=True,
                         extra={ "status_code": e.response.status_code, "response_text": e.response.text[:200], "vendor": vendor, "attempt_id": attempt_id })
             raise # Re-raise after logging
        except httpx.RequestError as e:
             logger.error(f"Network error during search result processing", exc_info=True,
                         extra={ "error_details": str(e), "vendor": vendor, "attempt_id": attempt_id })
             raise # Re-raise after logging
        except Exception as e:
            # Capture request parameters for error logging
            error_context = {
                "vendor": vendor,
                "error": str(e),
                "model": self.model,
                "attempt_id": attempt_id
            }
            logger.error(f"Unexpected error during search result processing", exc_info=True, extra=error_context)
            raise # Re-raise after logging

    # --- UPDATED PROMPT GENERATION LOGIC ---
    @log_function_call(logger, include_args=False) # Don't log vendors list
    def _create_classification_prompt(
        self,
        vendors: List[str],
        level: int,
        taxonomy: Taxonomy,
        parent_category_id: Optional[str] = None, # Changed parameter name
        batch_id: str = "unknown-batch"
    ) -> str:
        """
        Create an appropriate prompt for the current classification level,
        emphasizing how to handle ambiguity for less-known vendors.

        Args:
            vendors: List of vendor names
            level: Classification level (1-4)
            taxonomy: Taxonomy data
            parent_category_id: Parent category ID (required for levels 2-4)
            batch_id: Unique ID for this batch

        Returns:
            Prompt string
        """
        logger.debug(f"Creating classification prompt for level {level}",
                    extra={
                        "vendor_count": len(vendors),
                        "level": level,
                        "parent_category_id": parent_category_id,
                        "batch_id": batch_id
                    })

        # --- LEVEL 1 PROMPT ---
        if level == 1:
            logger.debug(f"Fetching level 1 categories from taxonomy")
            categories = taxonomy.get_level1_categories()
            logger.debug(f"Found {len(categories)} level 1 categories")
            categories_str = "\n".join(f"- {cat.id}: {cat.name}" for cat in categories)

            prompt = f"""
You are a precise vendor classification expert using the NAICS taxonomy. Your task is to classify the vendors below based *only* on their names.

Classify each vendor into ONE of the following Level 1 NAICS categories:
{categories_str}

**Instructions:**
1.  Analyze each vendor name carefully.
2.  If the name clearly indicates the industry (e.g., "Acme Construction", "Beta Software Inc."), assign the most appropriate category ID and name with a high confidence (0.8-1.0).
3.  **CRITICAL:** If the name is generic, ambiguous, or you lack specific knowledge about the company (e.g., "Global Services", "Enterprise Solutions", "Consulting Group", "J. Smith Co.", "Anytown Supplies"), **DO NOT GUESS**. Instead, mark `classification_not_possible` as `true` and provide a brief reason (e.g., "Ambiguous name", "Insufficient information from name", "Generic name", "Name does not indicate industry"). Set confidence to 0.0 in this case.
4.  Provide a confidence score between 0.0 and 1.0 for each classification attempt. A score of 0.0 *must* correspond to `classification_not_possible: true`.

**Vendor list:**
{', '.join(vendors)}

**Output Format:** Respond *only* with a valid JSON object matching this exact schema. Do not include any text before or after the JSON object.
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
Ensure every vendor from the list is included in the `classifications` array. Ensure the `batch_id` in the response matches "{batch_id}".
"""
        # --- LEVELS 2-4 PROMPT ---
        else:
            logger.debug(f"Creating prompt for level {level} with parent category {parent_category_id}")
            parent_category_name = "Unknown" # Default
            parent_category_obj = None

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
                    else: categories = []
                elif level == 4:
                    parts = parent_category_id.split('.')
                    if len(parts) == 3 and parts[0] in taxonomy.categories and \
                       parts[1] in taxonomy.categories[parts[0]].children and \
                       parts[2] in taxonomy.categories[parts[0]].children[parts[1]].children:
                         parent_category_obj = taxonomy.categories[parts[0]].children[parts[1]].children[parts[2]]
                         categories = taxonomy.get_level4_categories(parent_category_id)
                    else: categories = []
                else:
                    categories = []

                if parent_category_obj:
                    parent_category_name = parent_category_obj.name
                else:
                     logger.warning(f"Could not find parent category object for ID: {parent_category_id}")

            except Exception as e:
                logger.error(f"Error retrieving categories for level {level}, parent {parent_category_id}", exc_info=True)
                categories = []
            # --- End Get Parent Category Name ---

            logger.debug(f"Found {len(categories)} level {level} categories for parent {parent_category_id}")

            # --- HANDLE MISSING SUBCATEGORIES ---
            if not categories:
                 logger.warning(f"No subcategories found for level {level}, parent {parent_category_id}. Prompt cannot be generated effectively.")
                 # Return a prompt that reflects this, forcing 'classification_not_possible'
                 prompt = f"""
You are a precise vendor classification expert. The parent category ID '{parent_category_id}' (Name: '{parent_category_name}') has no defined subcategories at Level {level} in the provided taxonomy.

For the following vendors, classification at Level {level} is not possible due to missing taxonomy definitions.

Vendor list:
{', '.join(vendors)}

Respond *only* with a valid JSON object matching this exact schema:
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
Ensure every vendor from the list is included in the `classifications` array. Ensure the `batch_id` in the response matches "{batch_id}".
"""
                 return prompt
            # --- END HANDLE MISSING SUBCATEGORIES ---

            categories_str = "\n".join(f"- {cat.id}: {cat.name}" for cat in categories)

            # --- ADDED PARENT NAME TO PROMPT ---
            prompt = f"""
You are a precise vendor classification expert using the NAICS taxonomy. Your task is to classify the vendors below, which belong to the parent category '{parent_category_id}: {parent_category_name}'.

Classify each vendor into ONE of the following Level {level} NAICS categories, which are subcategories of '{parent_category_name}':
{categories_str}

**Instructions:**
1.  Consider the vendor name and the fact it belongs to the parent category '{parent_category_name}'.
2.  Assign the most specific and appropriate Level {level} category ID and name. Use context from the parent category to help disambiguate if possible.
3.  **CRITICAL:** If the name is too generic *even within the context of the parent category* to determine the correct Level {level} subcategory (e.g., "General Supply" under "Wholesale Trade"), or if you lack specific knowledge, **DO NOT GUESS**. Mark `classification_not_possible` as `true` and provide a brief reason (e.g., "Insufficient information for subcategory", "Ambiguous within parent category"). Set confidence to 0.0 in this case.
4.  Provide a confidence score between 0.0 and 1.0 for each classification attempt. A score of 0.0 *must* correspond to `classification_not_possible: true`.

**Vendor list:**
{', '.join(vendors)}

**Output Format:** Respond *only* with a valid JSON object matching this exact schema. Do not include any text before or after the JSON object.
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
Ensure every vendor from the list is included in the `classifications` array. Ensure the `batch_id` in the response matches "{batch_id}".
"""
        # --- END LEVELS 2-4 PROMPT ---

        return prompt
    # --- END UPDATED PROMPT GENERATION LOGIC ---

    # --- UPDATED SEARCH RESULTS PROMPT ---
    @log_function_call(logger, include_args=False) # Don't log full search results
    def _create_search_results_prompt(
        self,
        vendor: str,
        search_results: Dict[str, Any],
        taxonomy: Taxonomy
    ) -> str:
        """
        Create a prompt for processing search results, emphasizing grounding and handling uncertainty.

        Args:
            vendor: Vendor name
            search_results: Search results from Tavily
            taxonomy: Taxonomy data

        Returns:
            Prompt string
        """
        logger.debug(f"Creating search results prompt for vendor",
                    extra={
                        "vendor": vendor,
                        "source_count": len(search_results.get("sources", []))
                    })
        # Get level 1 categories
        categories = taxonomy.get_level1_categories()
        categories_str = "\n".join(f"- {cat.id}: {cat.name}" for cat in categories)

        # Format search results
        sources_str = ""
        if search_results.get("sources"):
            for i, source in enumerate(search_results["sources"]):
                # Truncate content here for the prompt if necessary, but provide substantial context
                content_preview = source.get('content', '')[:1500] # Provide more content to LLM
                sources_str += f"\nSource {i+1}:\nTitle: {source.get('title', 'N/A')}\nURL: {source.get('url', 'N/A')}\nContent Snippet: {content_preview}...\n"
        else:
            sources_str = "No relevant search results were found."

        # Add summary if available
        summary_str = search_results.get("summary", "")
        if summary_str:
            sources_str += f"\nOverall Summary from Search:\n{summary_str}\n"


        prompt = f"""
You are a precise vendor classification expert using the NAICS taxonomy. Your task is to classify the vendor '{vendor}' based *only* on the provided search results. **Do not use any prior knowledge you have about this vendor unless it is confirmed in the search results provided.**

**Vendor:** {vendor}

**Search Results:**
{sources_str}

**Instructions:**
1.  Analyze the search results carefully to understand the primary business activity of '{vendor}'. Focus on what the company *does*, not just what it sells if it's a reseller. Synthesize information across sources if possible.
2.  Based *only* on the provided search results, classify the vendor into ONE of the following Level 1 NAICS categories:
    {categories_str}
3.  Provide a confidence score between 0.0 and 1.0. Base confidence on the clarity, consistency, and relevance of the information in the search results. Higher confidence requires clear evidence of the primary business activity.
4.  **CRITICAL:** If the search results are insufficient, contradictory, irrelevant, focus only on products sold rather than the business activity, or do not provide enough detail to confidently determine the business type, set `classification_not_possible` to `true` and provide a brief reason (e.g., "Insufficient information from search", "Conflicting sources", "Search results irrelevant", "Results unclear about primary business activity"). Set confidence to 0.0 in this case.
5.  Provide brief notes explaining your reasoning, referencing specific details or sources from the search results, especially if confidence is not 1.0 or if classification was not possible.

**Output Format:** Respond *only* with a valid JSON object matching this exact schema. Do not include any text before or after the JSON object.
{{
  "vendor_name": "{vendor}",
  "category_id": "ID or N/A",
  "category_name": "Category Name or N/A",
  "confidence": 0.0_to_1.0,
  "classification_not_possible": true_or_false,
  "classification_not_possible_reason": "Reason text or null",
  "notes": "Brief explanation of classification decision based *only* on the provided search results."
}}
Ensure the `vendor_name` in the response matches "{vendor}".
"""
        return prompt
    # --- END UPDATED SEARCH RESULTS PROMPT ---