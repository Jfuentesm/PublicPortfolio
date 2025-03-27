# app/services/llm_service.py
import httpx
import json
from typing import List, Dict, Any, Optional
import logging
import time
from tenacity import retry, stop_after_attempt, wait_exponential

from core.config import settings
from models.taxonomy import Taxonomy, TaxonomyCategory
from core.logging_config import get_logger, LogTimer, log_function_call, set_log_context
from utils.log_utils import log_api_request, log_method

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

    @retry(stop=stop_after_attempt(settings.MAX_RETRIES), wait=wait_exponential(multiplier=1, min=settings.RETRY_DELAY, max=10))
    @log_function_call(logger, include_args=True) # Keep logging args for debugging
    @log_api_request("openrouter")
    async def classify_batch(
        self,
        batch: List[str],
        level: int,
        taxonomy: Taxonomy,
        parent_category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a batch of vendors to LLM for classification.

        Args:
            batch: List of vendor names
            level: Classification level (1-4)
            taxonomy: Taxonomy data
            parent_category: Parent category ID (required for levels 2-4)

        Returns:
            Classification results
        """
        logger.info(f"Classifying vendor batch",
                   extra={
                       "batch_size": len(batch),
                       "level": level,
                       "parent_category": parent_category
                   })
        set_log_context({"vendor_count": len(batch), "taxonomy_level": level})
        batch_id = f"batch-{level}-{len(batch)}-{time.time_ns()}" # Add timestamp for uniqueness

        # Create prompt based on level
        logger.debug(f"Creating classification prompt")
        with LogTimer(logger, "Prompt creation", include_in_stats=True):
            # --- UPDATED PROMPT CREATION CALL ---
            prompt = self._create_classification_prompt(batch, level, taxonomy, parent_category)
            # --- END UPDATED PROMPT CREATION CALL ---
            # Log prompt length but not full content for security
            prompt_length = len(prompt)
            logger.debug(f"Classification prompt created",
                        extra={"prompt_length": prompt_length})

        # Call OpenRouter API
        try:
            logger.debug(f"Sending request to OpenRouter API")
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
                    {"role": "system", "content": "You are a precise vendor classification expert using the NAICS taxonomy. Adhere strictly to the provided categories and JSON output format. Do not guess if unsure."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1, # Lower temperature for more deterministic results
                "max_tokens": 2048, # Increased slightly for potentially longer JSON
                "top_p": 0.9, # Adjusted slightly
                "frequency_penalty": 0,
                "presence_penalty": 0
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

            logger.info(f"OpenRouter API response received",
                       extra={
                           "duration": api_duration,
                           "batch_id": batch_id,
                           "prompt_tokens": prompt_tokens,
                           "completion_tokens": completion_tokens,
                           "total_tokens": total_tokens
                       })

            # Parse response
            content = response_data["choices"][0]["message"]["content"]

            # Extract JSON from response
            try:
                with LogTimer(logger, "JSON parsing", include_in_stats=True):
                    json_str = content.strip()
                    # Handle case where JSON is wrapped in markdown code blocks
                    if json_str.startswith("```json"):
                        json_str = json_str[len("```json"):].strip()
                    if json_str.endswith("```"):
                        json_str = json_str[:-len("```")].strip()

                    result = json.loads(json_str)
                    logger.debug(f"Successfully parsed JSON response")

                # Track token usage
                usage_data = {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens
                }

                # Set context with token usage for metrics
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
                "parent_category": parent_category,
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
            Classification result (Level 1 attempt)
        """
        logger.info(f"Processing search results for vendor classification",
                   extra={
                       "vendor": vendor,
                       "source_count": len(search_results.get("sources", []))
                   })
        set_log_context({"vendor": vendor})
        batch_id = f"search-{vendor}-{time.time_ns()}" # Unique ID for this attempt

        # Create prompt with search results
        with LogTimer(logger, "Search prompt creation", include_in_stats=True):
             # --- UPDATED PROMPT CREATION CALL ---
            prompt = self._create_search_results_prompt(vendor, search_results, taxonomy)
             # --- END UPDATED PROMPT CREATION CALL ---
            # Log prompt length but not content
            prompt_length = len(prompt)
            logger.debug(f"Search results prompt created",
                        extra={"prompt_length": prompt_length})

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
                    {"role": "system", "content": "You are a precise vendor classification expert using the NAICS taxonomy. Analyze the provided search results to determine the vendor's primary business activity and classify it into the given Level 1 categories. Adhere strictly to the JSON output format. If information is insufficient or contradictory, state 'classification_not_possible'."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1, # Lower temperature
                "max_tokens": 1024, # Reduced slightly, only need one classification
                "top_p": 0.9,
                "frequency_penalty": 0,
                "presence_penalty": 0
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

            logger.info(f"OpenRouter API response received for search results",
                       extra={
                           "duration": api_duration,
                           "vendor": vendor,
                           "prompt_tokens": prompt_tokens,
                           "completion_tokens": completion_tokens,
                           "total_tokens": total_tokens,
                           "batch_id": batch_id
                       })

            # Parse response
            content = response_data["choices"][0]["message"]["content"]

            # Extract JSON from response
            try:
                with LogTimer(logger, "JSON parsing", include_in_stats=True):
                    json_str = content.strip()
                    # Handle case where JSON is wrapped in markdown code blocks
                    if json_str.startswith("```json"):
                        json_str = json_str[len("```json"):].strip()
                    if json_str.endswith("```"):
                        json_str = json_str[:-len("```")].strip()

                    result = json.loads(json_str)
                    logger.debug(f"Successfully parsed JSON response for search result processing")

                # Track token usage
                usage_data = {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens
                }

                # Set context with token usage for metrics
                set_log_context({
                    "openrouter_prompt_tokens": prompt_tokens,
                    "openrouter_completion_tokens": completion_tokens,
                    "openrouter_total_tokens": total_tokens
                })

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
                                "batch_id": batch_id
                            })
                raise ValueError(f"LLM response after search was not valid JSON. Preview: {content[:200]}")

        except httpx.HTTPStatusError as e:
             logger.error(f"HTTP error during search result processing", exc_info=True,
                         extra={ "status_code": e.response.status_code, "response_text": e.response.text[:200], "vendor": vendor, "batch_id": batch_id })
             raise # Re-raise after logging
        except httpx.RequestError as e:
             logger.error(f"Network error during search result processing", exc_info=True,
                         extra={ "error_details": str(e), "vendor": vendor, "batch_id": batch_id })
             raise # Re-raise after logging
        except Exception as e:
            # Capture request parameters for error logging
            error_context = {
                "vendor": vendor,
                "error": str(e),
                "model": self.model,
                "batch_id": batch_id
            }
            logger.error(f"Unexpected error during search result processing", exc_info=True, extra=error_context)
            raise # Re-raise after logging

    @log_function_call(logger, include_args=False) # Don't log vendors list
    def _create_classification_prompt(
        self,
        vendors: List[str],
        level: int,
        taxonomy: Taxonomy,
        parent_category: Optional[str] = None
    ) -> str:
        """
        Create an appropriate prompt for the current classification level.

        Args:
            vendors: List of vendor names
            level: Classification level (1-4)
            taxonomy: Taxonomy data
            parent_category: Parent category ID (required for levels 2-4)

        Returns:
            Prompt string
        """
        logger.debug(f"Creating classification prompt for level {level}",
                    extra={
                        "vendor_count": len(vendors),
                        "level": level,
                        "parent_category": parent_category
                    })

        # --- UPDATED PROMPT ---
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
3.  If the name is generic, ambiguous, or you lack specific knowledge about the company (e.g., "Global Services", "Enterprise Solutions", "Consulting Group", "J. Smith Co."), **DO NOT GUESS**. Instead, mark `classification_not_possible` as `true` and provide a brief reason (e.g., "Ambiguous name", "Insufficient information from name", "Generic name"). Set confidence to 0.0 in this case.
4.  Provide a confidence score between 0.0 and 1.0 for each classification attempt. A score of 0.0 indicates classification was not possible.

**Vendor list:**
{', '.join(vendors)}

**Output Format:** Respond *only* with a valid JSON object matching this exact schema. Do not include any text before or after the JSON object.
{{
  "level": 1,
  "batch_id": "batch-{len(vendors)}",
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
Ensure every vendor from the list is included in the `classifications` array.
"""
        else:
            # For levels 2-4, include parent category info
            logger.debug(f"Creating prompt for level {level} with parent category {parent_category}")
            if level == 2:
                categories = taxonomy.get_level2_categories(parent_category)
            elif level == 3:
                categories = taxonomy.get_level3_categories(parent_category)
            else:  # level == 4:
                categories = taxonomy.get_level4_categories(parent_category)

            logger.debug(f"Found {len(categories)} level {level} categories for parent {parent_category}")

            if not categories:
                 logger.warning(f"No subcategories found for level {level}, parent {parent_category}. Prompt cannot be generated effectively.")
                 # Return a prompt that reflects this, forcing 'classification_not_possible'
                 prompt = f"""
You are a precise vendor classification expert. The parent category '{parent_category}' has no defined subcategories at Level {level} in the provided taxonomy.

For the following vendors, classification at Level {level} is not possible due to missing taxonomy definitions.

Vendor list:
{', '.join(vendors)}

Respond *only* with a valid JSON object matching this exact schema:
{{
  "level": {level},
  "batch_id": "batch-{len(vendors)}",
  "parent_category_id": "{parent_category}",
  "classifications": [
    {{
      "vendor_name": "Vendor Name Here",
      "category_id": "N/A",
      "category_name": "N/A",
      "confidence": 0.0,
      "classification_not_possible": true,
      "classification_not_possible_reason": "No subcategories defined for parent {parent_category} at Level {level}"
    }}
    // ... more classifications, all marked as not possible
  ]
}}
Ensure every vendor from the list is included in the `classifications` array.
"""
                 return prompt


            categories_str = "\n".join(f"- {cat.id}: {cat.name}" for cat in categories)

            prompt = f"""
You are a precise vendor classification expert using the NAICS taxonomy. Your task is to classify the vendors below, which belong to the parent category '{parent_category}'.

Classify each vendor into ONE of the following Level {level} NAICS categories, which are subcategories of '{parent_category}':
{categories_str}

**Instructions:**
1.  Consider the vendor name and the fact it belongs to the parent category '{parent_category}'.
2.  Assign the most specific and appropriate Level {level} category ID and name.
3.  If the name is too generic *within the context of the parent category* to determine the correct Level {level} subcategory, or if you lack specific knowledge, **DO NOT GUESS**. Mark `classification_not_possible` as `true` and provide a brief reason (e.g., "Insufficient information for subcategory", "Ambiguous within parent category"). Set confidence to 0.0 in this case.
4.  Provide a confidence score between 0.0 and 1.0 for each classification attempt. A score of 0.0 indicates classification was not possible.

**Vendor list:**
{', '.join(vendors)}

**Output Format:** Respond *only* with a valid JSON object matching this exact schema. Do not include any text before or after the JSON object.
{{
  "level": {level},
  "batch_id": "batch-{len(vendors)}",
  "parent_category_id": "{parent_category}",
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
Ensure every vendor from the list is included in the `classifications` array.
"""
        # --- END UPDATED PROMPT ---

        return prompt

    @log_function_call(logger, include_args=False) # Don't log full search results
    def _create_search_results_prompt(
        self,
        vendor: str,
        search_results: Dict[str, Any],
        taxonomy: Taxonomy
    ) -> str:
        """
        Create a prompt for processing search results.

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
                content_preview = source.get('content', '')[:800] # Increased preview length
                sources_str += f"\nSource {i+1}:\nTitle: {source.get('title', 'N/A')}\nURL: {source.get('url', 'N/A')}\nContent Snippet: {content_preview}...\n"
        else:
            sources_str = "No relevant search results found."

        # --- UPDATED PROMPT ---
        prompt = f"""
You are a precise vendor classification expert using the NAICS taxonomy. Your task is to classify the vendor '{vendor}' based *only* on the provided search results.

**Vendor:** {vendor}

**Search Results:**
{sources_str}

**Instructions:**
1.  Analyze the search results carefully to understand the primary business activity of '{vendor}'.
2.  Based *only* on the provided search results, classify the vendor into ONE of the following Level 1 NAICS categories:
    {categories_str}
3.  Provide a confidence score between 0.0 and 1.0.
4.  If the search results are insufficient, contradictory, irrelevant, or do not provide enough detail to confidently determine the business type, set `classification_not_possible` to `true` and provide a brief reason (e.g., "Insufficient information from search", "Conflicting sources", "Search results irrelevant"). Set confidence to 0.0 in this case.
5.  Provide brief notes explaining your reasoning, especially if confidence is not 1.0 or if classification was not possible.

**Output Format:** Respond *only* with a valid JSON object matching this exact schema. Do not include any text before or after the JSON object.
{{
  "vendor_name": "{vendor}",
  "category_id": "ID or N/A",
  "category_name": "Category Name or N/A",
  "confidence": 0.0_to_1.0,
  "classification_not_possible": true_or_false,
  "classification_not_possible_reason": "Reason text or null",
  "notes": "Brief explanation of classification decision based on search results."
}}
"""
        # --- END UPDATED PROMPT ---

        return prompt