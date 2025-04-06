# <file path='app/services/llm_service.py'>
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
# --- MODIFIED IMPORT: Include L5 ---
from models.taxonomy import Taxonomy, TaxonomyCategory, TaxonomyLevel1, TaxonomyLevel2, TaxonomyLevel3, TaxonomyLevel4, TaxonomyLevel5
# --- END MODIFIED IMPORT ---
from core.logging_config import get_logger, LogTimer, log_function_call, set_log_context, get_correlation_id # <-- Added get_correlation_id
from utils.log_utils import log_api_request, log_method # <<< Ensure log_method is imported if used

# Configure logger
logger = get_logger("vendor_classification.llm_service")
llm_trace_logger = logging.getLogger("llm_api_trace") # ENSURE NAME CONSISTENT


# --- Helper function for JSON parsing (No changes needed here) ---
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
        parent_category_id: Optional[str] = None,
        search_context: Optional[Dict[str, Any]] = None # ADDED: Optional search context
    ) -> Dict[str, Any]:
        """
        Send a batch of vendors to LLM for classification.
        Can optionally include search context for post-search classification attempts.
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
        correlation_id = get_correlation_id() # Get correlation ID for tracing
        llm_trace_logger.debug(f"LLM_TRACE: Starting classify_batch (Batch ID: {batch_id}, Level: {level}, Parent: {parent_category_id}, Context: {context_type})", extra={'correlation_id': correlation_id})

        if not self.api_key:
            logger.error("Cannot classify batch: OpenRouter API key is missing.")
            llm_trace_logger.error(f"LLM_TRACE: LLM API Error (Batch ID: {batch_id}): API key missing.", extra={'correlation_id': correlation_id})
            # Return a structured error response
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

        logger.debug(f"Creating classification prompt with {context_type}")
        with LogTimer(logger, "Prompt creation", include_in_stats=True):
            prompt = self._create_classification_prompt(
                batch_data, level, taxonomy, parent_category_id, batch_id, search_context
            )
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
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1, "max_tokens": 2048, "top_p": 0.9,
            "frequency_penalty": 0, "presence_penalty": 0,
            "response_format": {"type": "json_object"} # Request JSON output mode
        }

        # --- Log Request Details (Trace Log) ---
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
                response = await client.post(f"{self.api_base}/chat/completions", json=payload, headers=headers, timeout=90.0) # Increased timeout
                # --- ADDED: Log raw response immediately ---
                raw_content = response.text # Get raw text
                status_code = response.status_code
                api_duration = time.time() - start_time
                llm_trace_logger.debug(f"LLM_TRACE: LLM Raw Response (Batch ID: {batch_id}, Status: {status_code}, Duration: {api_duration:.3f}s):\n-------\n{raw_content or '[No Content Received]'}\n-------", extra={'correlation_id': correlation_id})
                # --- END ADDED ---
                response.raise_for_status() # Check for HTTP errors AFTER logging raw response
                response_data = response.json() # Parse JSON only if status is OK
                # Extract raw content from JSON if structure is as expected
                if response_data and response_data.get("choices") and isinstance(response_data["choices"], list) and len(response_data["choices"]) > 0:
                     message = response_data["choices"][0].get("message")
                     if message and isinstance(message, dict): raw_content = message.get("content") # Overwrite with content field if possible

            usage = response_data.get("usage", {}) if response_data else {}
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)

            logger.info(f"OpenRouter API response received",
                       extra={
                           "duration": api_duration, "batch_id": batch_id, "level": level,
                           "status_code": status_code, # Log status code
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
                result["batch_id_mismatch"] = True # Add flag but continue processing

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
             # Log the raw content we captured earlier
             response_text = raw_content or (e.response.text[:500] if hasattr(e.response, 'text') else "[No Response Body]")
             status_code = e.response.status_code
             logger.error(f"HTTP error during LLM batch classification", exc_info=False, # Don't need full stack trace here
                         extra={ "status_code": status_code, "response_text": response_text, "batch_id": batch_id, "level": level })
             llm_trace_logger.error(f"LLM_TRACE: LLM API HTTP Error (Batch ID: {batch_id}): Status={status_code}, Response='{response_text}'", exc_info=True, extra={'correlation_id': correlation_id}) # Include stack trace in trace log
             raise # Re-raise for tenacity
        except httpx.RequestError as e:
             logger.error(f"Network error during LLM batch classification", exc_info=False, # Don't need full stack trace here
                         extra={ "error_details": str(e), "batch_id": batch_id, "level": level })
             llm_trace_logger.error(f"LLM_TRACE: LLM API Network Error (Batch ID: {batch_id}): {e}", exc_info=True, extra={'correlation_id': correlation_id}) # Include stack trace in trace log
             raise # Re-raise for tenacity
        except Exception as e:
            error_context = { "batch_size": len(batch_data), "level": level, "parent_category_id": parent_category_id, "error": str(e), "model": self.model, "batch_id": batch_id }
            logger.error(f"Unexpected error during LLM batch classification", exc_info=True, extra=error_context)
            llm_trace_logger.error(f"LLM_TRACE: LLM Unexpected Error (Batch ID: {batch_id}): {e}", exc_info=True, extra={'correlation_id': correlation_id}) # Include stack trace in trace log
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
        Process search results to determine **Level 1** classification only.
        This function is intended for the *initial* classification attempt after search.
        Recursive L2-L5 calls should use classify_batch with the search context.
        """
        vendor_name = vendor_data.get('vendor_name', 'UnknownVendor')
        logger.info(f"Processing search results for initial L1 classification",
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
            prompt = self._create_search_results_prompt(vendor_data, search_results, taxonomy, attempt_id)
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
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1, "max_tokens": 1024, "top_p": 0.9,
            "frequency_penalty": 0, "presence_penalty": 0,
            "response_format": {"type": "json_object"} # Request JSON output mode
        }

        # --- Log Request Details (Trace Log) ---
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
                # --- ADDED: Log raw response immediately ---
                raw_content = response.text # Get raw text
                status_code = response.status_code
                api_duration = time.time() - start_time
                llm_trace_logger.debug(f"LLM_TRACE: LLM Raw Response (Attempt ID: {attempt_id}, Status: {status_code}, Duration: {api_duration:.3f}s):\n-------\n{raw_content or '[No Content Received]'}\n-------", extra={'correlation_id': correlation_id})
                # --- END ADDED ---
                response.raise_for_status() # Check for HTTP errors AFTER logging raw response
                response_data = response.json() # Parse JSON only if status is OK
                # Extract raw content from JSON if structure is as expected
                if response_data and response_data.get("choices") and isinstance(response_data["choices"], list) and len(response_data["choices"]) > 0:
                     message = response_data["choices"][0].get("message")
                     if message and isinstance(message, dict): raw_content = message.get("content") # Overwrite with content field if possible

            usage = response_data.get("usage", {}) if response_data else {}
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)

            logger.info(f"OpenRouter API response received for search results",
                       extra={ "duration": api_duration, "vendor": vendor_name, "status_code": status_code, "openrouter_prompt_tokens": prompt_tokens, "openrouter_completion_tokens": completion_tokens, "openrouter_total_tokens": total_tokens, "attempt_id": attempt_id })

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

            # This function returns the direct result from the LLM for the L1 search attempt
            return { "result": result, "usage": usage_data }

        except httpx.HTTPStatusError as e:
             # Log the raw content we captured earlier
             response_text = raw_content or (e.response.text[:500] if hasattr(e.response, 'text') else "[No Response Body]")
             status_code = e.response.status_code
             logger.error(f"HTTP error during search result processing", exc_info=False, # Don't need full stack trace here
                         extra={ "status_code": status_code, "response_text": response_text, "vendor": vendor_name, "attempt_id": attempt_id })
             llm_trace_logger.error(f"LLM_TRACE: LLM API HTTP Error (Attempt ID: {attempt_id}): Status={status_code}, Response='{response_text}'", exc_info=True, extra={'correlation_id': correlation_id}) # Include stack trace in trace log
             raise # Re-raise for tenacity
        except httpx.RequestError as e:
             logger.error(f"Network error during search result processing", exc_info=False, # Don't need full stack trace here
                         extra={ "error_details": str(e), "vendor": vendor_name, "attempt_id": attempt_id })
             llm_trace_logger.error(f"LLM_TRACE: LLM API Network Error (Attempt ID: {attempt_id}): {e}", exc_info=True, extra={'correlation_id': correlation_id}) # Include stack trace in trace log
             raise # Re-raise for tenacity
        except Exception as e:
            error_context = { "vendor": vendor_name, "error": str(e), "model": self.model, "attempt_id": attempt_id }
            logger.error(f"Unexpected error during search result processing", exc_info=True, extra=error_context)
            llm_trace_logger.error(f"LLM_TRACE: LLM Unexpected Error (Attempt ID: {attempt_id}): {e}", exc_info=True, extra={'correlation_id': correlation_id}) # Include stack trace in trace log
            raise # Re-raise for tenacity


    # --- UPDATED PROMPT GENERATION METHOD ---
    @log_function_call(logger, include_args=False)
    def _create_classification_prompt(
        self,
        vendors_data: List[Dict[str, Any]],
        level: int,
        taxonomy: Taxonomy,
        parent_category_id: Optional[str] = None,
        batch_id: str = "unknown-batch",
        search_context: Optional[Dict[str, Any]] = None # ADDED: Optional search context
    ) -> str:
        """
        Create an appropriate prompt for the current classification level (1-5),
        optionally including search context for post-search classification.
        """
        context_type = "Search Context" if search_context else "Initial Data"
        logger.debug(f"_create_classification_prompt: Generating prompt for Level {level} using {context_type}",
                    extra={ "vendor_count": len(vendors_data), "parent_category_id": parent_category_id, "batch_id": batch_id, "has_search_context": bool(search_context) })

        # --- Build Vendor Data Section (Remains the same) ---
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
            if example: vendor_data_xml += f"    <example_goods_services>{str(example)[:200]}</example_goods_services>\n"
            if address: vendor_data_xml += f"    <address>{str(address)[:200]}</address>\n"
            if website: vendor_data_xml += f"    <website>{str(website)[:100]}</website>\n"
            if internal_cat: vendor_data_xml += f"    <internal_category>{str(internal_cat)[:100]}</internal_category>\n"
            if parent_co: vendor_data_xml += f"    <parent_company>{str(parent_co)[:100]}</parent_company>\n"
            if spend_cat: vendor_data_xml += f"    <spend_category>{str(spend_cat)[:100]}</spend_category>\n"
            vendor_data_xml += f"  </vendor>\n"
        vendor_data_xml += "</vendor_data>"

        # --- Build Search Context Section (NEW) ---
        search_context_xml = ""
        # Include search context only for L2-L5 post-search attempts
        if search_context and level > 1:
            logger.debug(f"Including search context in prompt for Level {level}", extra={"batch_id": batch_id})
            search_context_xml += "<search_context>\n"
            summary = search_context.get("summary")
            sources = search_context.get("sources")
            if summary:
                search_context_xml += f"  <summary>{str(summary)[:1000]}</summary>\n" # Limit length
            if sources and isinstance(sources, list):
                search_context_xml += "  <sources>\n"
                for j, source in enumerate(sources[:3]): # Limit to top 3 sources for brevity
                    title = source.get('title', 'N/A')
                    url = source.get('url', 'N/A')
                    content_preview = str(source.get('content', ''))[:500] # Limit length
                    search_context_xml += f"    <source index=\"{j+1}\">\n"
                    search_context_xml += f"      <title>{title}</title>\n"
                    search_context_xml += f"      <url>{url}</url>\n"
                    search_context_xml += f"      <content_snippet>{content_preview}...</content_snippet>\n"
                    search_context_xml += f"    </source>\n"
                search_context_xml += "  </sources>\n"
            else:
                 search_context_xml += "  <message>No relevant search results sources were provided.</message>\n"
            search_context_xml += "</search_context>\n"
        # --- END Build Search Context Section ---

        # --- Get Category Options (Updated for Level 5) ---
        categories: List[TaxonomyCategory] = []
        parent_category_name = "N/A"
        category_lookup_successful = True
        try:
            logger.debug(f"_create_classification_prompt: Retrieving categories via taxonomy methods for Level {level}, Parent: {parent_category_id}")
            if level == 1:
                categories = taxonomy.get_level1_categories()
            elif parent_category_id:
                parent_obj = None
                if level == 2:
                    categories = taxonomy.get_level2_categories(parent_category_id)
                    parent_obj = taxonomy.categories.get(parent_category_id)
                elif level == 3:
                    categories = taxonomy.get_level3_categories(parent_category_id)
                    l1_id, l2_id = parent_category_id.split('.') if '.' in parent_category_id else (None, parent_category_id)
                    if not l1_id: # Find L1 if only L2 was given
                        for l1_key, l1_node in taxonomy.categories.items():
                            if l2_id in getattr(l1_node, 'children', {}): l1_id = l1_key; break
                    if l1_id: parent_obj = taxonomy.categories.get(l1_id, {}).children.get(l2_id)
                elif level == 4:
                    categories = taxonomy.get_level4_categories(parent_category_id)
                    l1_id, l2_id, l3_id = parent_category_id.split('.') if parent_category_id.count('.') == 2 else (None, None, parent_category_id)
                    if not l1_id: # Find parents if only L3 was given
                         found = False
                         for l1k, l1n in taxonomy.categories.items():
                             for l2k, l2n in getattr(l1n, 'children', {}).items():
                                 if l3_id in getattr(l2n, 'children', {}): l1_id = l1k; l2_id = l2k; found = True; break
                             if found: break
                    if l1_id and l2_id: parent_obj = taxonomy.categories.get(l1_id, {}).children.get(l2_id, {}).children.get(l3_id)
                # --- ADDED LEVEL 5 CASE ---
                elif level == 5:
                    categories = taxonomy.get_level5_categories(parent_category_id)
                    l1_id, l2_id, l3_id, l4_id = parent_category_id.split('.') if parent_category_id.count('.') == 3 else (None, None, None, parent_category_id)
                    if not l1_id: # Find parents if only L4 was given
                        found = False
                        for l1k, l1n in taxonomy.categories.items():
                            for l2k, l2n in getattr(l1n, 'children', {}).items():
                                for l3k, l3n in getattr(l2n, 'children', {}).items():
                                    if l4_id in getattr(l3n, 'children', {}): l1_id = l1k; l2_id = l2k; l3_id = l3k; found = True; break
                                if found: break
                            if found: break
                    if l1_id and l2_id and l3_id:
                        parent_obj = taxonomy.categories.get(l1_id, {}).children.get(l2_id, {}).children.get(l3_id, {}).children.get(l4_id)
                # --- END ADDED LEVEL 5 CASE ---

                if parent_obj: parent_category_name = parent_obj.name

            else: # level > 1 and no parent_category_id
                logger.error(f"Parent category ID is required for level {level} prompt generation but was not provided.")
                category_lookup_successful = False

            if not categories and level > 1 and parent_category_id:
                 logger.warning(f"No subcategories found for Level {level}, Parent '{parent_category_id}'.")
                 # This might be valid if a parent has no children, don't mark as error unless L1 failed
                 if level == 1: category_lookup_successful = False
            elif not categories and level == 1:
                 logger.error(f"No Level 1 categories found in taxonomy!")
                 category_lookup_successful = False

            logger.debug(f"_create_classification_prompt: Retrieved {len(categories)} categories for Level {level}, Parent '{parent_category_id}' ('{parent_category_name}').")

        except Exception as e:
            logger.error(f"Error retrieving categories for prompt (Level {level}, Parent: {parent_category_id})", exc_info=True)
            category_lookup_successful = False

        # --- Build Category Options Section (Remains the same) ---
        category_options_xml = "<category_options>\n"
        if category_lookup_successful:
            category_options_xml += f"  <level>{level}</level>\n"
            if level > 1 and parent_category_id:
                category_options_xml += f"  <parent_id>{parent_category_id}</parent_id>\n"
                category_options_xml += f"  <parent_name>{parent_category_name}</parent_name>\n"
            category_options_xml += "  <categories>\n"
            if categories: # Check if categories list is not empty
                for cat in categories:
                    category_options_xml += f"    <category id=\"{cat.id}\" name=\"{cat.name}\"/>\n"
            else:
                 category_options_xml += f"    <message>No subcategories available for this level and parent.</message>\n"
            category_options_xml += "  </categories>\n"
        else:
            category_options_xml += f"  <error>Could not retrieve valid categories for Level {level}, Parent '{parent_category_id}'. Classification is not possible.</error>\n"
        category_options_xml += "</category_options>"

        # --- Define Output Format Section (Updated for Level 5) ---
        output_format_xml = f"""<output_format>
Respond *only* with a valid JSON object matching this exact schema. Do not include any text before or after the JSON object.

json
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

</output_format>"""

        # --- Assemble Final Prompt ---
        prompt_base = f"""
<role>You are a precise vendor classification expert using the NAICS taxonomy.</role>

<task>Classify each vendor provided in `<vendor_data>` into **ONE** appropriate NAICS category from the `<category_options>` for Level {level}. {f"Consider that these vendors belong to the parent category '{parent_category_id}: {parent_category_name}'. " if level > 1 and parent_category_id else ""}</task>"""

        if search_context_xml:
            prompt_base += f"""
<search_context_instruction>You have been provided with additional context from a web search in `<search_context>`. Use this information, along with the original `<vendor_data>`, to make the most accurate classification decision for Level {level}.</search_context_instruction>"""

        prompt_base += f"""
<instructions>
1.  Analyze each vendor's details in `<vendor_data>` {f"and the supplementary information in `<search_context>`" if search_context_xml else ""}.
2.  Compare the vendor's likely primary business activity against the available categories in `<category_options>`.
3.  Assign the **single most specific and appropriate** category ID and name from the list.
4.  Provide a confidence score (0.0 to 1.0).
5.  **CRITICAL:** If the vendor's primary activity is genuinely ambiguous, cannot be determined from the provided information, or does not fit well into *any* of the specific categories listed in `<category_options>`, **DO NOT GUESS**. Instead: Set `classification_not_possible` to `true`, `confidence` to `0.0`, provide a brief `classification_not_possible_reason`, and set `category_id`/`category_name` to "N/A".
6.  If classification *is* possible (`classification_not_possible: false`), ensure `confidence` > 0.0 and `category_id`/`category_name` are populated correctly from `<category_options>`.
7.  Provide brief optional `notes` for reasoning, especially if confidence is low or classification was not possible.
8.  Ensure the `batch_id` in the final JSON output matches the `batch_id` specified in `<output_format>`.
9.  Ensure the output contains an entry for **every** vendor listed in `<vendor_data>`.
10. Respond *only* with the valid JSON object as specified in `<output_format>`.
</instructions>

{vendor_data_xml}
{search_context_xml if search_context_xml else ""}
{category_options_xml}
{output_format_xml}
"""
        prompt = prompt_base

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
7. Respond *only* with the valid JSON object as specified in `<output_format>`.
</instructions>
{vendor_data_xml}
{category_options_xml}
{output_format_xml}
"""

        return prompt

    # --- UPDATED SEARCH RESULTS PROMPT GENERATION METHOD ---
    # This prompt remains focused on getting ONLY Level 1 classification after search.
    @log_function_call(logger, include_args=False)
    def _create_search_results_prompt(
        self,
        vendor_data: Dict[str, Any],
        search_results: Dict[str, Any],
        taxonomy: Taxonomy,
        attempt_id: str = "unknown-attempt" # Added attempt ID
    ) -> str:
        """
        Create a prompt for processing search results, aiming for Level 1 classification.
        """
        logger.debug(f"Entering _create_search_results_prompt for vendor: {vendor_data.get('vendor_name', 'Unknown')}")
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
        category_options_xml += "  <level>1</level>\n" # Explicitly state Level 1
        category_options_xml += "  <categories>\n"
        for cat in categories:
            category_options_xml += f"    <category id=\"{cat.id}\" name=\"{cat.name}\"/>\n" # Omit description
        category_options_xml += "  </categories>\n"
        category_options_xml += "</category_options>"

        # --- Define Output Format Section ---
        output_format_xml = f"""<output_format>
Respond *only* with a valid JSON object matching this exact schema. Do not include any text before or after the JSON object.

json
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

</output_format>"""

        # --- Assemble Final Prompt ---
        prompt = f"""
<role>You are a precise vendor classification expert using the NAICS taxonomy.</role>

<task>Analyze the vendor details in `<vendor_data>` and the web search information in `<search_results>` to classify the vendor into **ONE** appropriate **Level 1** NAICS category from `<category_options>`. Base your decision *only* on the provided information.</task>

<instructions>
1.  Carefully review the vendor details in `<vendor_data>` (name, examples, address, website, internal category, parent company, spend category).
2.  Carefully review the search results in `<search_results>` (sources and summary).
3.  Synthesize all provided information to understand the vendor's **primary business activity**. Focus on what the company *does*, not just what it might resell.
4.  Compare this primary activity against the **Level 1** categories listed in `<category_options>`.
5.  Assign the **single most appropriate** Level 1 category ID and name.
6.  Provide a confidence score (0.0 to 1.0) based on the clarity, consistency, and relevance of the provided information.
7.  **CRITICAL:** If the provided information (vendor data + search results) is insufficient, contradictory, irrelevant, focuses only on products sold rather than the business activity, or does not allow for confident determination of the primary business activity *from the listed L1 categories*, **DO NOT GUESS**. Instead: Set `classification_not_possible` to `true`, `confidence` to `0.0`, provide a brief `classification_not_possible_reason`, and set `category_id`/`category_name` to "N/A".
8.  If classification *is* possible (`classification_not_possible: false`), ensure `confidence` > 0.0 and `category_id`/`category_name` are populated correctly from `<category_options>`.
9.  Provide brief optional `notes` explaining your reasoning, referencing specific details from `<vendor_data>` or `<search_results>`.
10. Ensure the `vendor_name` in the final JSON output matches the name in `<vendor_data>`.
11. Respond *only* with the valid JSON object as specified in `<output_format>`.
</instructions>

{vendor_data_xml}

{search_results_xml}

{category_options_xml}

{output_format_xml}
"""
        return prompt
    # --- END UPDATED ---