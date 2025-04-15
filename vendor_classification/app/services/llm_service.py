# app/services/llm_service.py
import httpx
import json
import re
import os
import hashlib
from typing import List, Dict, Any, Optional, Set
import logging
import time
import uuid
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential, RetryError, TryAgain
from core import config
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

# --- Cache Configuration ---
CACHE_DIR = "data/cache"
CACHE_FILE_PATH = os.path.join(CACHE_DIR, "openrouter_dev_cache.json")
logger.info(f"Checking for cache file existence at: {CACHE_FILE_PATH} (Absolute: {os.path.abspath(CACHE_FILE_PATH)})")
CACHE_ENABLED = settings.USE_LLM_CACHE and os.path.exists(CACHE_FILE_PATH) # Enable only if setting is true AND file exists

if CACHE_ENABLED:
    logger.warning(f"--- OpenRouter DEV CACHE ACTIVE --- API calls will be cached in {CACHE_FILE_PATH}")
elif settings.USE_LLM_CACHE and not os.path.exists(CACHE_FILE_PATH):
     logger.warning(f"--- OpenRouter DEV CACHE INACTIVE --- USE_LLM_CACHE is true, but cache file not found at {CACHE_FILE_PATH}. Live API calls will be made. Cache file will be created on first save.")
     # Ensure directory exists if we intend to create the file later
     try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        logger.info(f"Ensured cache directory '{CACHE_DIR}' exists.")
     except Exception as e:
        logger.error(f"Failed to create cache directory '{CACHE_DIR}': {e}")
        # Decide if this is fatal or just disable caching
        # settings.USE_LLM_CACHE = False # Disable caching if dir creation fails
        # logger.warning("Disabling cache due to directory creation failure.")
else:
    logger.info(f"--- OpenRouter DEV CACHE INACTIVE --- USE_LLM_CACHE is false. Live API calls will be made.")


# --- Cache Helper Functions (Unchanged from previous version) ---
def _load_cache() -> Dict[str, Any]:
    """Loads the cache from the JSON file."""
    if not settings.USE_LLM_CACHE: # Check setting first
        return {}
    if not os.path.exists(CACHE_FILE_PATH):
         logger.info(f"Cache file {CACHE_FILE_PATH} not found. Starting with empty cache.")
         return {}
    try:
        with open(CACHE_FILE_PATH, 'r') as f:
            cache_data = json.load(f)
            logger.debug(f"Loaded cache with {len(cache_data)} entries from {CACHE_FILE_PATH}")
            return cache_data
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from cache file {CACHE_FILE_PATH}. Returning empty cache.", exc_info=True)
        return {}
    except Exception as e:
        logger.error(f"Error loading cache file {CACHE_FILE_PATH}: {e}", exc_info=True)
        return {}

def _save_cache(cache_data: Dict[str, Any]):
    """Saves the cache data to the JSON file."""
    if not settings.USE_LLM_CACHE: # Only save if cache is enabled
        return
    try:
        # Ensure the cache directory exists
        os.makedirs(os.path.dirname(CACHE_FILE_PATH), exist_ok=True)
        with open(CACHE_FILE_PATH, 'w') as f:
            json.dump(cache_data, f, indent=2)
        logger.debug(f"Saved cache with {len(cache_data)} entries to {CACHE_FILE_PATH}")
    except IOError as e:
        logger.error(f"Error writing cache file {CACHE_FILE_PATH}: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Unexpected error saving cache file {CACHE_FILE_PATH}: {e}", exc_info=True)

def _generate_cache_key(payload: Dict[str, Any]) -> str:
    """Generates a consistent cache key based on the request payload."""
    key_data = {
        "model": payload.get("model"),
        "messages": [msg.get("content", "") for msg in payload.get("messages", [])],
        "temperature": payload.get("temperature"),
        "max_tokens": payload.get("max_tokens"),
        "top_p": payload.get("top_p"),
        "response_format": payload.get("response_format")
    }
    stable_string = json.dumps(key_data, sort_keys=True)
    return hashlib.sha256(stable_string.encode('utf-8')).hexdigest()

# --- Helper function for JSON parsing (Unchanged) ---
def _extract_json_from_response(response_content: str) -> Optional[Dict[str, Any]]:
    """Attempts to extract a JSON object from a string, handling common LLM response issues."""
    # ... (implementation remains the same as provided previously) ...
    if not response_content:
        logger.warning("Attempted to parse empty response content.")
        return None

    content = response_content.strip()
    match = re.search(r"(?:```)?(?:json)?\s*(\{.*\})\s*(?:```)?", content, re.DOTALL | re.IGNORECASE)
    if match:
        content = match.group(1).strip()
        logger.debug("Extracted JSON content from within markdown code fences.")
    else:
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

# --- Status codes remain the same ---
GENERATED_KEY_INVALID_STATUS_CODES = {401, 403, 429}
PROVISIONING_RELATED_ERROR_CODES = {500, 502, 503, 504}

class LLMService:
    """Service for interacting with OpenRouter API, using Provisioning Keys."""

    def __init__(self):
        """Initialize the LLM service."""
        logger.info("Initializing LLM service with OpenRouter Provisioning Keys")
        # --- UPDATED: Access manually loaded keys from config module ---
        self.provisioning_keys = config.MANUAL_OPENROUTER_PROVISIONING_KEYS
        # --- Use settings object for other values ---
        self.api_base = settings.OPENROUTER_API_BASE
        self.model = settings.OPENROUTER_MODEL
        # --- END UPDATED ---
        self.current_provisioning_key_index = 0
        self.active_generated_key: Optional[str] = None
        self.active_generated_key_hash: Optional[str] = None
        self.cache = _load_cache()

        if not self.provisioning_keys:
            logger.critical("OpenRouter Provisioning Key list is empty! LLM calls WILL fail.")

        logger.debug("LLM service initialized",
                    extra={"api_base": self.api_base,
                        "model": self.model,
                        "provisioning_key_count": len(self.provisioning_keys),
                        "cache_enabled": settings.USE_LLM_CACHE,
                        "initial_cache_size": len(self.cache)})

    def _get_current_provisioning_key(self) -> Optional[str]:
        """Gets the current provisioning key based on the index."""
        if not self.provisioning_keys:
            return None
        if self.current_provisioning_key_index >= len(self.provisioning_keys):
            logger.warning(f"Provisioning key index {self.current_provisioning_key_index} out of bounds ({len(self.provisioning_keys)} keys). Resetting to 0.")
            self.current_provisioning_key_index = 0
        return self.provisioning_keys[self.current_provisioning_key_index]

    def _rotate_provisioning_key(self):
        """Rotates to the next provisioning key in the list."""
        if not self.provisioning_keys or len(self.provisioning_keys) <= 1:
            logger.warning("Cannot rotate Provisioning key: list is empty or has only one key.")
            return False # Indicate rotation didn't happen

        old_index = self.current_provisioning_key_index
        self.current_provisioning_key_index = (self.current_provisioning_key_index + 1) % len(self.provisioning_keys)
        logger.warning(f"Rotated OpenRouter Provisioning Key from index {old_index} to {self.current_provisioning_key_index} due to key generation failure.")
        return True # Indicate rotation happened

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5)) # Retry generation few times
    async def _generate_api_key(self) -> bool:
        """
        Generates a new API key using the current provisioning key.
        Rotates provisioning key on failure.
        Returns True if successful, False otherwise.
        """
        provisioning_key = self._get_current_provisioning_key()
        if not provisioning_key:
            logger.error("Cannot generate API key: No provisioning key available.")
            return False

        generation_url = f"{self.api_base}/keys" # Use the correct endpoint from docs
        headers = {
            "Authorization": f"Bearer {provisioning_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "naicsvendorclassification.com", # Optional but good practice
            "X-Title": "NAICS Vendor Classification" # Optional
        }
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        payload = {
            "name": f"{settings.GENERATED_KEY_NAME_PREFIX}-{timestamp}",
        }
        if settings.GENERATED_KEY_LABEL:
            payload["label"] = settings.GENERATED_KEY_LABEL
        if settings.GENERATED_KEY_CREDIT_LIMIT is not None:
             # Ensure limit is treated as float/number by API if needed
             try:
                 payload["limit"] = float(settings.GENERATED_KEY_CREDIT_LIMIT)
             except ValueError:
                 logger.warning(f"Invalid GENERATED_KEY_CREDIT_LIMIT format: '{settings.GENERATED_KEY_CREDIT_LIMIT}'. Ignoring limit.")


        logger.info(f"Attempting to generate new OpenRouter API key using provisioning key index {self.current_provisioning_key_index}")
        llm_trace_logger.info(f"LLM_TRACE: Generating new API key. URL: {generation_url}, ProvKeyIndex: {self.current_provisioning_key_index}", extra={'correlation_id': get_correlation_id()})
        llm_trace_logger.debug(f"LLM_TRACE: Key Generation Payload: {json.dumps(payload)}", extra={'correlation_id': get_correlation_id()})

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(generation_url, json=payload, headers=headers, timeout=30.0)
                llm_trace_logger.debug(f"LLM_TRACE: Key Generation Raw Response (Status: {response.status_code}):\n{response.text}", extra={'correlation_id': get_correlation_id()})
                response.raise_for_status() # Raises HTTPStatusError for 4xx/5xx

                response_data = response.json()
                new_key = response_data.get("key")
                # --- FIX START: Access hash correctly from nested 'data' object ---
                response_data_inner = response_data.get("data", {}) # Get inner dict, default {}
                key_hash = response_data_inner.get("hash") if isinstance(response_data_inner, dict) else None
                # --- FIX END ---

                if not new_key:
                    logger.error("Key generation response did not contain a 'key' field.", extra={"response": response_data})
                    raise ValueError("Invalid response format from key generation API")
                # --- FIX START: Check key_hash before slicing for logging ---
                if not key_hash:
                    logger.warning("Key generation response did not contain a 'hash' field within 'data'.", extra={"response": response_data})
                    # Decide if this is critical. For now, proceed without hash.
                    # raise ValueError("Invalid response format from key generation API (missing hash)") # Or raise error

                self.active_generated_key = new_key
                self.active_generated_key_hash = key_hash # Store the hash (could be None)

                key_hash_prefix = f"{key_hash[:8]}..." if key_hash else "N/A" # Use N/A if hash is None
                logger.info(f"Successfully generated new OpenRouter API key (hash: {key_hash_prefix}) using provisioning key index {self.current_provisioning_key_index}")
                llm_trace_logger.info(f"LLM_TRACE: Successfully generated key {key_hash_prefix}", extra={'correlation_id': get_correlation_id()})
                # --- FIX END ---
                return True # Success

        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            response_text = e.response.text[:500]
            logger.error(f"HTTP error during API key generation", exc_info=False,
                        extra={ "status_code": status_code, "response_text": response_text, "provisioning_key_index": self.current_provisioning_key_index })
            llm_trace_logger.error(f"LLM_TRACE: Key Generation HTTP Error: Status={status_code}, Response='{response_text}'", exc_info=True, extra={'correlation_id': get_correlation_id()})
            # If it's an auth error (401/403) or server error, likely the provisioning key is bad or service issue
            if status_code in {401, 403} or status_code in PROVISIONING_RELATED_ERROR_CODES:
                rotated = self._rotate_provisioning_key()
                if not rotated and len(self.provisioning_keys) <= 1:
                     logger.critical("Single provisioning key failed, cannot rotate. Key generation will likely keep failing.")
                     return False # Stop retrying if rotation isn't possible/doesn't help
                raise TryAgain # Tell tenacity to retry after rotating
            else: # Other client errors (e.g., 400 Bad Request) might not be helped by rotation
                 logger.error("Key generation failed with unrecoverable client error.")
                 return False # Don't retry for e.g. bad request format

        except (httpx.RequestError, json.JSONDecodeError, ValueError, Exception) as e:
            # --- FIX START: Log hash prefix safely in exception ---
            key_hash_prefix = f"{self.active_generated_key_hash[:8]}..." if self.active_generated_key_hash else "N/A"
            logger.error(f"Error during API key generation: {e}", exc_info=True,
                         extra={"provisioning_key_index": self.current_provisioning_key_index, "key_hash_used": key_hash_prefix})
            llm_trace_logger.error(f"LLM_TRACE: Key Generation Error: {e}", exc_info=True, extra={'correlation_id': get_correlation_id(), "key_hash_used": key_hash_prefix})
            # --- FIX END ---
            # Rotate on general errors too, might be transient network issue or bad key
            rotated = self._rotate_provisioning_key()
            if not rotated and len(self.provisioning_keys) <= 1:
                 logger.critical("Single provisioning key failed on error, cannot rotate.")
                 return False
            raise TryAgain # Retry after rotation

        return False # Should not be reached if retry logic works, but acts as default failure

    async def _get_active_key_or_generate(self) -> Optional[str]:
        """Gets the currently active generated key, or generates a new one if needed."""
        if self.active_generated_key:
            return self.active_generated_key

        logger.info("No active generated key found. Attempting to generate a new one.")
        success = await self._generate_api_key()
        if success:
            return self.active_generated_key
        else:
            logger.error("Failed to generate a new API key after multiple attempts.")
            return None

    # --- Main API Call Methods ---

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
        Send a batch of vendors to LLM for classification, using generated keys.
        """
        # ... (logging and setup remains similar) ...
        batch_names = [vd.get('vendor_name', f'Unknown_{i}') for i, vd in enumerate(batch_data)]
        context_type = "Search Context" if search_context else "Initial Data"
        logger.info(f"Classifying vendor batch using {context_type}",
                extra={ "batch_size": len(batch_data), "level": level, "parent_category_id": parent_category_id, "has_search_context": bool(search_context) })
        set_log_context({"vendor_count": len(batch_data), "taxonomy_level": level, "context_type": context_type})
        batch_id = str(uuid.uuid4())
        correlation_id = get_correlation_id()
        llm_trace_logger.debug(f"LLM_TRACE: Starting classify_batch (Batch ID: {batch_id}, Level: {level})", extra={'correlation_id': correlation_id})

        # --- Prompt Generation (remains the same) ---
        with LogTimer(logger, "Prompt creation", include_in_stats=True):
            prompt = generate_batch_prompt(batch_data, level, taxonomy, parent_category_id, batch_id, search_context)
            prompt_length = len(prompt)
            logger.debug(f"Classification prompt created", extra={"prompt_length": prompt_length})
            llm_trace_logger.debug(f"LLM_TRACE: Generated Prompt (Batch ID: {batch_id}):\n-------\n{prompt}\n-------", extra={'correlation_id': correlation_id})

        # --- Payload (remains the same) ---
        payload = {
            "model": self.model, "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1, "max_tokens": 2048, "top_p": 0.9,
            "frequency_penalty": 0, "presence_penalty": 0,
            "response_format": {"type": "json_object"}
        }

        # --- CACHE CHECK ---
        cache_key = _generate_cache_key(payload)
        if settings.USE_LLM_CACHE and cache_key in self.cache:
            logger.warning(f"--- CACHE HIT --- Returning cached response for Level {level} batch {batch_id[:8]}...")
            llm_trace_logger.info(f"LLM_TRACE: Cache Hit (Batch ID: {batch_id}, Key: {cache_key[:8]}...)", extra={'correlation_id': correlation_id})
            cached_response = self.cache[cache_key]
            cached_response.setdefault("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
            return cached_response
        # --- END CACHE CHECK ---

        logger.info(f"--- CACHE MISS --- Preparing LIVE API call for Level {level} batch {batch_id[:8]}...")

        # --- Get or Generate API Key ---
        current_api_key = await self._get_active_key_or_generate()
        if not current_api_key:
            logger.error("Cannot make live API call: Failed to obtain a generated API key.")
            llm_trace_logger.error(f"LLM_TRACE: LLM API Error (Batch ID: {batch_id}): Failed to obtain generated key.", extra={'correlation_id': correlation_id})
            # Return error structure
            return {
                "result": { "level": level, "batch_id": batch_id, "parent_category_id": parent_category_id, "classifications": [ { "vendor_name": vd.get('vendor_name', f'Unknown_{i}'), "category_id": "ERROR", "category_name": "ERROR", "confidence": 0.0, "classification_not_possible": True, "classification_not_possible_reason": "Failed to generate API key", "notes": "Failed due to internal key generation error." } for i, vd in enumerate(batch_data) ] },
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            }

        headers = {
            "Authorization": f"Bearer {current_api_key}", # Use the generated key
            "Content-Type": "application/json",
            "HTTP-Referer": "naicsvendorclassification.com", "X-Title": "NAICS Vendor Classification"
        }

        # Log Request Details (Trace Log)
        try:
            log_headers = {k: v for k, v in headers.items() if k.lower() != 'authorization'}
            # --- FIX START: Safely log key hash prefix ---
            key_hash_prefix = self.active_generated_key_hash[:8] if self.active_generated_key_hash else "UNKNOWN"
            log_headers['Authorization'] = f'Bearer [REDACTED_GENERATED_KEY_{key_hash_prefix}]'
            # --- FIX END ---
            llm_trace_logger.debug(f"LLM_TRACE: LLM Request Headers (Batch ID: {batch_id}):\n{json.dumps(log_headers, indent=2)}", extra={'correlation_id': correlation_id})
            llm_trace_logger.debug(f"LLM_TRACE: LLM Request Payload (Batch ID: {batch_id}):\n{json.dumps(payload, indent=2)}", extra={'correlation_id': correlation_id})
        except Exception as log_err:
            llm_trace_logger.warning(f"LLM_TRACE: Failed to log LLM request details (Batch ID: {batch_id}): {log_err}", extra={'correlation_id': correlation_id})

        response_data = None; raw_content = None; response = None; status_code = None; api_duration = 0.0
        try:
            # --- FIX START: Safely log key hash prefix ---
            key_hash_prefix = self.active_generated_key_hash[:8] if self.active_generated_key_hash else 'N/A'
            logger.debug(f"Sending request to OpenRouter API using generated key (hash: {key_hash_prefix})")
            # --- FIX END ---
            start_time = time.time()
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self.api_base}/chat/completions", json=payload, headers=headers, timeout=90.0)
                raw_content = response.text
                status_code = response.status_code
                api_duration = time.time() - start_time
                llm_trace_logger.debug(f"LLM_TRACE: LLM Raw Response (Batch ID: {batch_id}, Status: {status_code}, Duration: {api_duration:.3f}s):\n-------\n{raw_content or '[No Content Received]'}\n-------", extra={'correlation_id': correlation_id})
                response.raise_for_status()
                response_data = response.json()

            # --- Successful response processing (remains largely the same) ---
            # ... (extract content, usage, parse JSON) ...
            if response_data and response_data.get("choices") and isinstance(response_data["choices"], list) and len(response_data["choices"]) > 0:
                message = response_data["choices"][0].get("message")
                if message and isinstance(message, dict): content_field = message.get("content")
                else: content_field = None
                if content_field: raw_content = content_field
                else: logger.warning("LLM response message object missing 'content' field.", extra={"message_obj": message})
            else: logger.warning("LLM response choice missing 'message' object or structure invalid.", extra={"choice_obj": response_data.get("choices", [{}])[0]})

            usage = response_data.get("usage", {}) if response_data else {}
            prompt_tokens = usage.get("prompt_tokens", 0); completion_tokens = usage.get("completion_tokens", 0); total_tokens = usage.get("total_tokens", 0)

            # --- FIX START: Safely log key hash prefix ---
            key_hash_prefix = self.active_generated_key_hash[:8] if self.active_generated_key_hash else 'N/A'
            logger.info(f"OpenRouter API response received successfully",
                    extra={ "duration": api_duration, "batch_id": batch_id, "level": level, "status_code": status_code, "key_hash_used": key_hash_prefix, "openrouter_prompt_tokens": prompt_tokens, "openrouter_completion_tokens": completion_tokens, "openrouter_total_tokens": total_tokens })
            # --- FIX END ---

            with LogTimer(logger, "JSON parsing and extraction", include_in_stats=True):
                result = _extract_json_from_response(raw_content)

            if result is None:
                llm_trace_logger.error(f"LLM_TRACE: LLM JSON Parse Error (Batch ID: {batch_id}). Raw content logged above.", extra={'correlation_id': correlation_id})
                raise ValueError(f"LLM response was not valid JSON or could not be extracted. Preview: {str(raw_content)[:200]}")

            # ... (log parsed response, check batch_id mismatch, etc.) ...
            try: llm_trace_logger.debug(f"LLM_TRACE: LLM Parsed Response (Batch ID: {batch_id}):\n{json.dumps(result, indent=2)}", extra={'correlation_id': correlation_id})
            except Exception as log_err: llm_trace_logger.warning(f"LLM_TRACE: Failed to log LLM parsed response (Batch ID: {batch_id}): {log_err}", extra={'correlation_id': correlation_id})

            usage_data = { "prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens, "total_tokens": total_tokens }
            api_result = { "result": result, "usage": usage_data }

            # --- SAVE TO CACHE ---
            if settings.USE_LLM_CACHE:
                logger.info(f"--- SAVING TO CACHE --- Storing successful response for batch {batch_id[:8]} (Key: {cache_key[:8]}...)")
                self.cache[cache_key] = api_result
                _save_cache(self.cache)
            # --- END SAVE TO CACHE ---

            return api_result

        except httpx.HTTPStatusError as e:
            response_text = raw_content or (e.response.text[:500] if hasattr(e.response, 'text') else "[No Response Body]")
            status_code = e.response.status_code
            # --- FIX START: Safely log key hash prefix ---
            key_hash_used_prefix = self.active_generated_key_hash[:8] if self.active_generated_key_hash else 'N/A'
            logger.error(f"HTTP error during LLM batch classification", exc_info=False,
                        extra={ "status_code": status_code, "response_text": response_text, "batch_id": batch_id, "level": level, "key_hash_used": key_hash_used_prefix })
            llm_trace_logger.error(f"LLM_TRACE: LLM API HTTP Error (Batch ID: {batch_id}): Status={status_code}, Response='{response_text}', KeyHash={key_hash_used_prefix}", exc_info=True, extra={'correlation_id': correlation_id})
            # --- FIX END ---

            # --- Key Invalidation Logic ---
            if status_code in GENERATED_KEY_INVALID_STATUS_CODES:
                logger.warning(f"Generated key (hash: {key_hash_used_prefix}) may be invalid due to status {status_code}. Discarding and forcing regeneration on retry.")
                self.active_generated_key = None # Discard the key
                self.active_generated_key_hash = None
                # Let tenacity handle the retry, _get_active_key_or_generate will run again
            elif status_code in PROVISIONING_RELATED_ERROR_CODES:
                 logger.warning(f"Server error {status_code} encountered. This might indicate an OpenRouter issue or potentially a problem with the provisioning key used.")
                 # Optionally, could try rotating provisioning key here too, but might just be OpenRouter outage
                 # self._rotate_provisioning_key() # Be cautious with this, might mask persistent OR issues

            raise # Re-raise for tenacity to handle retry based on status code or general failure

        except httpx.RequestError as e:
             # --- FIX START: Safely log key hash prefix ---
            key_hash_used_prefix = self.active_generated_key_hash[:8] if self.active_generated_key_hash else 'N/A'
            logger.error(f"Network error during LLM batch classification", exc_info=False,
                        extra={ "error_details": str(e), "batch_id": batch_id, "level": level, "key_hash_used": key_hash_used_prefix })
            llm_trace_logger.error(f"LLM_TRACE: LLM API Network Error (Batch ID: {batch_id}): {e}, KeyHash={key_hash_used_prefix}", exc_info=True, extra={'correlation_id': correlation_id})
             # --- FIX END ---
            # Network errors might warrant discarding the key too, as its state is unknown
            # self.active_generated_key = None
            # self.active_generated_key_hash = None
            raise # Re-raise for tenacity

        except ValueError as ve: # Catch the specific error raised on JSON parse failure
            logger.error(f"LLM response parsing error during batch classification", exc_info=False,
                        extra={"error": str(ve), "batch_id": batch_id, "level": level})
            # Don't discard key for parsing error, key is likely fine.
            raise # Re-raise for tenacity

        except Exception as e:
            # --- FIX START: Safely log key hash prefix ---
            key_hash_used_prefix = self.active_generated_key_hash[:8] if self.active_generated_key_hash else 'N/A'
            error_context = { "batch_size": len(batch_data), "level": level, "parent_category_id": parent_category_id, "error": str(e), "model": self.model, "batch_id": batch_id, "key_hash_used": key_hash_used_prefix }
            logger.error(f"Unexpected error during LLM batch classification", exc_info=True, extra=error_context)
            llm_trace_logger.error(f"LLM_TRACE: LLM Unexpected Error (Batch ID: {batch_id}): {e}, KeyHash={key_hash_used_prefix}", exc_info=True, extra={'correlation_id': correlation_id})
            # --- FIX END ---
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
        Process search results for L1 classification, using generated keys.
        """
        # ... (logging and setup remains similar) ...
        vendor_name = vendor_data.get('vendor_name', 'UnknownVendor')
        logger.info(f"Processing search results for initial L1 classification",
                extra={ "vendor": vendor_name, "source_count": len(search_results.get("sources", [])) })
        set_log_context({"vendor": vendor_name})
        attempt_id = str(uuid.uuid4())
        correlation_id = get_correlation_id()
        llm_trace_logger.debug(f"LLM_TRACE: Starting process_search_results (Attempt ID: {attempt_id}, Vendor: {vendor_name})", extra={'correlation_id': correlation_id})

        # --- Prompt Generation (remains the same) ---
        with LogTimer(logger, "Search prompt creation", include_in_stats=True):
            prompt = generate_search_prompt(vendor_data, search_results, taxonomy, attempt_id)
            prompt_length = len(prompt)
            logger.debug(f"Search results prompt created", extra={"prompt_length": prompt_length})
            llm_trace_logger.debug(f"LLM_TRACE: Generated Search Prompt (Attempt ID: {attempt_id}):\n-------\n{prompt}\n-------", extra={'correlation_id': correlation_id})

        # --- Payload (remains the same) ---
        payload = {
            "model": self.model, "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1, "max_tokens": 1024, "top_p": 0.9,
            "frequency_penalty": 0, "presence_penalty": 0,
            "response_format": {"type": "json_object"}
        }

        # --- CACHE CHECK ---
        cache_key = _generate_cache_key(payload)
        if settings.USE_LLM_CACHE and cache_key in self.cache:
            logger.warning(f"--- CACHE HIT --- Returning cached response for search results processing {attempt_id[:8]}...")
            llm_trace_logger.info(f"LLM_TRACE: Cache Hit (Attempt ID: {attempt_id}, Key: {cache_key[:8]}...)", extra={'correlation_id': correlation_id})
            cached_response = self.cache[cache_key]
            cached_response.setdefault("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
            return cached_response
        # --- END CACHE CHECK ---

        logger.info(f"--- CACHE MISS --- Preparing LIVE API call for search results processing {attempt_id[:8]}...")

        # --- Get or Generate API Key ---
        current_api_key = await self._get_active_key_or_generate()
        if not current_api_key:
            logger.error("Cannot make live API call for search results: Failed to obtain a generated API key.")
            llm_trace_logger.error(f"LLM_TRACE: LLM API Error (Attempt ID: {attempt_id}): Failed to obtain generated key.", extra={'correlation_id': correlation_id})
            return {
                "result": { "vendor_name": vendor_name, "category_id": "ERROR", "category_name": "ERROR", "confidence": 0.0, "classification_not_possible": True, "classification_not_possible_reason": "Failed to generate API key", "notes": "" },
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            }

        headers = {
            "Authorization": f"Bearer {current_api_key}", # Use the generated key
            "Content-Type": "application/json",
            "HTTP-Referer": "naicsvendorclassification.com", "X-Title": "NAICS Vendor Classification"
        }

        # Log Request Details (Trace Log)
        try:
            log_headers = {k: v for k, v in headers.items() if k.lower() != 'authorization'}
            # --- FIX START: Safely log key hash prefix ---
            key_hash_prefix = self.active_generated_key_hash[:8] if self.active_generated_key_hash else "UNKNOWN"
            log_headers['Authorization'] = f'Bearer [REDACTED_GENERATED_KEY_{key_hash_prefix}]'
            # --- FIX END ---
            llm_trace_logger.debug(f"LLM_TRACE: LLM Request Headers (Attempt ID: {attempt_id}):\n{json.dumps(log_headers, indent=2)}", extra={'correlation_id': correlation_id})
            llm_trace_logger.debug(f"LLM_TRACE: LLM Request Payload (Attempt ID: {attempt_id}):\n{json.dumps(payload, indent=2)}", extra={'correlation_id': correlation_id})
        except Exception as log_err:
            llm_trace_logger.warning(f"LLM_TRACE: Failed to log LLM request details (Attempt ID: {attempt_id}): {log_err}", extra={'correlation_id': correlation_id})

        response_data = None; raw_content = None; response = None; status_code = None; api_duration = 0.0
        try:
            # --- FIX START: Safely log key hash prefix ---
            key_hash_prefix = self.active_generated_key_hash[:8] if self.active_generated_key_hash else 'N/A'
            logger.debug(f"Sending search results to OpenRouter API using generated key (hash: {key_hash_prefix})")
            # --- FIX END ---
            start_time = time.time()
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self.api_base}/chat/completions", json=payload, headers=headers, timeout=60.0)
                raw_content = response.text
                status_code = response.status_code
                api_duration = time.time() - start_time
                llm_trace_logger.debug(f"LLM_TRACE: LLM Raw Response (Attempt ID: {attempt_id}, Status: {status_code}, Duration: {api_duration:.3f}s):\n-------\n{raw_content or '[No Content Received]'}\n-------", extra={'correlation_id': correlation_id})
                response.raise_for_status()
                response_data = response.json()

            # --- Successful response processing (remains largely the same) ---
            # ... (extract content, usage, parse JSON) ...
            if response_data and response_data.get("choices") and isinstance(response_data["choices"], list) and len(response_data["choices"]) > 0:
                message = response_data["choices"][0].get("message")
                if message and isinstance(message, dict): content_field = message.get("content")
                else: content_field = None
                if content_field: raw_content = content_field
                else: logger.warning("LLM response message object missing 'content' field (search).", extra={"message_obj": message})
            else: logger.warning("LLM response choice missing 'message' object or structure invalid (search).", extra={"choice_obj": response_data.get("choices", [{}])[0]})

            usage = response_data.get("usage", {}) if response_data else {}
            prompt_tokens = usage.get("prompt_tokens", 0); completion_tokens = usage.get("completion_tokens", 0); total_tokens = usage.get("total_tokens", 0)

            # --- FIX START: Safely log key hash prefix ---
            key_hash_prefix = self.active_generated_key_hash[:8] if self.active_generated_key_hash else 'N/A'
            logger.info(f"OpenRouter API response received successfully for search results",
                    extra={ "duration": api_duration, "vendor": vendor_name, "status_code": status_code, "key_hash_used": key_hash_prefix, "openrouter_prompt_tokens": prompt_tokens, "openrouter_completion_tokens": completion_tokens, "openrouter_total_tokens": total_tokens, "attempt_id": attempt_id })
            # --- FIX END ---

            with LogTimer(logger, "JSON parsing and extraction (search)", include_in_stats=True):
                result = _extract_json_from_response(raw_content)

            if result is None:
                llm_trace_logger.error(f"LLM_TRACE: LLM JSON Parse Error (Attempt ID: {attempt_id}). Raw content logged above.", extra={'correlation_id': correlation_id})
                raise ValueError(f"LLM response after search was not valid JSON or could not be extracted. Preview: {str(raw_content)[:200]}")

            # ... (log parsed response, check vendor name mismatch, etc.) ...
            try: llm_trace_logger.debug(f"LLM_TRACE: LLM Parsed Response (Attempt ID: {attempt_id}):\n{json.dumps(result, indent=2)}", extra={'correlation_id': correlation_id})
            except Exception as log_err: llm_trace_logger.warning(f"LLM_TRACE: Failed to log LLM parsed response (Attempt ID: {attempt_id}): {log_err}", extra={'correlation_id': correlation_id})

            usage_data = { "prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens, "total_tokens": total_tokens }
            api_result = { "result": result, "usage": usage_data }

            # --- SAVE TO CACHE ---
            if settings.USE_LLM_CACHE:
                logger.info(f"--- SAVING TO CACHE --- Storing successful response for search results {attempt_id[:8]} (Key: {cache_key[:8]}...)")
                self.cache[cache_key] = api_result
                _save_cache(self.cache)
            # --- END SAVE TO CACHE ---

            return api_result

        except httpx.HTTPStatusError as e:
            response_text = raw_content or (e.response.text[:500] if hasattr(e.response, 'text') else "[No Response Body]")
            status_code = e.response.status_code
            # --- FIX START: Safely log key hash prefix ---
            key_hash_used_prefix = self.active_generated_key_hash[:8] if self.active_generated_key_hash else 'N/A'
            logger.error(f"HTTP error during search result processing", exc_info=False,
                        extra={ "status_code": status_code, "response_text": response_text, "vendor": vendor_name, "attempt_id": attempt_id, "key_hash_used": key_hash_used_prefix })
            llm_trace_logger.error(f"LLM_TRACE: LLM API HTTP Error (Attempt ID: {attempt_id}): Status={status_code}, Response='{response_text}', KeyHash={key_hash_used_prefix}", exc_info=True, extra={'correlation_id': correlation_id})
            # --- FIX END ---

            # --- Key Invalidation Logic ---
            if status_code in GENERATED_KEY_INVALID_STATUS_CODES:
                logger.warning(f"Generated key (hash: {key_hash_used_prefix}) may be invalid due to status {status_code}. Discarding and forcing regeneration on retry.")
                self.active_generated_key = None
                self.active_generated_key_hash = None
            elif status_code in PROVISIONING_RELATED_ERROR_CODES:
                 logger.warning(f"Server error {status_code} encountered during search processing.")
                 # Optionally rotate provisioning key here too

            raise # Re-raise for tenacity

        except httpx.RequestError as e:
            # --- FIX START: Safely log key hash prefix ---
            key_hash_used_prefix = self.active_generated_key_hash[:8] if self.active_generated_key_hash else 'N/A'
            logger.error(f"Network error during search result processing", exc_info=False,
                        extra={ "error_details": str(e), "vendor": vendor_name, "attempt_id": attempt_id, "key_hash_used": key_hash_used_prefix })
            llm_trace_logger.error(f"LLM_TRACE: LLM API Network Error (Attempt ID: {attempt_id}): {e}, KeyHash={key_hash_used_prefix}", exc_info=True, extra={'correlation_id': correlation_id})
            # --- FIX END ---
            # self.active_generated_key = None # Optional: discard key on network error
            # self.active_generated_key_hash = None
            raise # Re-raise for tenacity

        except ValueError as ve: # Catch the specific error raised on JSON parse failure
            logger.error(f"LLM response parsing error during search result processing", exc_info=False,
                        extra={"error": str(ve), "vendor": vendor_name, "attempt_id": attempt_id})
            raise # Re-raise for tenacity

        except Exception as e:
            # --- FIX START: Safely log key hash prefix ---
            key_hash_used_prefix = self.active_generated_key_hash[:8] if self.active_generated_key_hash else 'N/A'
            error_context = { "vendor": vendor_name, "error": str(e), "model": self.model, "attempt_id": attempt_id, "key_hash_used": key_hash_used_prefix }
            logger.error(f"Unexpected error during search result processing", exc_info=True, extra=error_context)
            llm_trace_logger.error(f"LLM_TRACE: LLM Unexpected Error (Attempt ID: {attempt_id}): {e}, KeyHash={key_hash_used_prefix}", exc_info=True, extra={'correlation_id': correlation_id})
            # --- FIX END ---
            raise # Re-raise for tenacity