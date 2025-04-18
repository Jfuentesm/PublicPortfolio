# core/config.py
import os
from pydantic_settings import BaseSettings
from pydantic import Field, PostgresDsn, EmailStr, AnyHttpUrl
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
import json
import logging

# Configure logging for this module
logger = logging.getLogger("vendor_classification.config")

# Load environment variables from .env file if it exists
# This is useful for local development
load_dotenv()

# --- Manual Loading for Early Access ---
# These will be loaded directly from environment variables BEFORE Pydantic Settings
# This allows their use during module import time if needed (e.g., in other modules)
MANUAL_OPENROUTER_PROVISIONING_KEYS: List[str] = []
MANUAL_TAVILY_API_KEYS: List[str] = []

def _load_manual_keys():
    """Loads specific keys manually from environment variables."""
    global MANUAL_OPENROUTER_PROVISIONING_KEYS, MANUAL_TAVILY_API_KEYS

    openrouter_keys_str = os.getenv("OPENROUTER_PROVISIONING_KEYS", "")
    if openrouter_keys_str:
        try:
            # Attempt to parse as JSON list first
            keys = json.loads(openrouter_keys_str)
            if isinstance(keys, list) and all(isinstance(k, str) for k in keys):
                MANUAL_OPENROUTER_PROVISIONING_KEYS = keys
            else:
                # Fallback to comma-separated if JSON parsing fails or type is wrong
                MANUAL_OPENROUTER_PROVISIONING_KEYS = [k.strip() for k in openrouter_keys_str.split(',') if k.strip()]
                logger.warning("OPENROUTER_PROVISIONING_KEYS was not a valid JSON list, parsed as comma-separated.")
        except json.JSONDecodeError:
            # Assume comma-separated if JSON parsing fails
            MANUAL_OPENROUTER_PROVISIONING_KEYS = [k.strip() for k in openrouter_keys_str.split(',') if k.strip()]
            logger.warning("Failed to parse OPENROUTER_PROVISIONING_KEYS as JSON, parsed as comma-separated.")
    else:
        logger.warning("OPENROUTER_PROVISIONING_KEYS environment variable not set or empty.")

    tavily_keys_str = os.getenv("TAVILY_API_KEYS", "")
    if tavily_keys_str:
        try:
            # Attempt to parse as JSON list first
            keys = json.loads(tavily_keys_str)
            if isinstance(keys, list) and all(isinstance(k, str) for k in keys):
                MANUAL_TAVILY_API_KEYS = keys
            else:
                # Fallback to comma-separated if JSON parsing fails or type is wrong
                MANUAL_TAVILY_API_KEYS = [k.strip() for k in tavily_keys_str.split(',') if k.strip()]
                logger.warning("TAVILY_API_KEYS was not a valid JSON list, parsed as comma-separated.")
        except json.JSONDecodeError:
            # Assume comma-separated if JSON parsing fails
            MANUAL_TAVILY_API_KEYS = [k.strip() for k in tavily_keys_str.split(',') if k.strip()]
            logger.warning("Failed to parse TAVILY_API_KEYS as JSON, parsed as comma-separated.")
    else:
        logger.warning("TAVILY_API_KEYS environment variable not set or empty.")

_load_manual_keys()
# --- End Manual Loading ---


class Settings(BaseSettings):
    # --- Core Settings ---
    PROJECT_NAME: str = "NAICS Vendor Classification"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = Field(..., env="SECRET_KEY") # Make secret key mandatory
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 1 day expiration
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30 # Password reset token expires in 30 mins

    # --- Database Settings ---
    DATABASE_URL: PostgresDsn = Field(..., env="DATABASE_URL")

    # --- Celery Settings ---
    CELERY_BROKER_URL: str = Field("redis://redis:6379/0", env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field("redis://redis:6379/0", env="CELERY_RESULT_BACKEND")

    # --- File Paths (relative to project root or absolute) ---
    # Assume TAXONOMY_DATA_DIR is where taxonomy, input, output, logs, cache reside
    TAXONOMY_DATA_DIR: str = "data"
    INPUT_DIR: str = Field(default_factory=lambda: os.path.join(Settings().TAXONOMY_DATA_DIR, "input"))
    OUTPUT_DIR: str = Field(default_factory=lambda: os.path.join(Settings().TAXONOMY_DATA_DIR, "output"))
    LOG_DIR: str = Field(default_factory=lambda: os.path.join(Settings().TAXONOMY_DATA_DIR, "logs"))
    CACHE_DIR: str = Field(default_factory=lambda: os.path.join(Settings().TAXONOMY_DATA_DIR, "cache"))
    TAXONOMY_FILE_PATH: str = Field(default_factory=lambda: os.path.join(Settings().TAXONOMY_DATA_DIR, "taxonomy", "2022_NAICS_Structure.xlsx"))

    # --- Frontend Settings ---
    FRONTEND_URL: str = "http://localhost:8080" # Default for local dev Vue server

    # --- LLM & Search API Settings ---
    # These are loaded via Pydantic Settings but also manually above for early access
    OPENROUTER_PROVISIONING_KEYS: List[str] = Field(default_factory=lambda: MANUAL_OPENROUTER_PROVISIONING_KEYS)
    TAVILY_API_KEYS: List[str] = Field(default_factory=lambda: MANUAL_TAVILY_API_KEYS)
    OPENROUTER_API_BASE: Optional[str] = "https://openrouter.ai/api/v1"
    # --- FIX: Add TAVILY_API_URL ---
    TAVILY_API_URL: Optional[str] = "https://api.tavily.com/search"
    # --- END FIX ---
    USE_LLM_CACHE: bool = True # Enable/disable simple file-based cache for OpenRouter calls
    LLM_CACHE_FILE: str = Field(default_factory=lambda: os.path.join(Settings().CACHE_DIR, "openrouter_dev_cache.json"))
    LLM_DEFAULT_MODEL: str = "anthropic/claude-3.5-sonnet"
    LLM_FALLBACK_MODEL: Optional[str] = "anthropic/claude-3-haiku" # Optional fallback
    LLM_MAX_RETRIES: int = 3
    LLM_RETRY_DELAY_SECONDS: int = 5
    LLM_REQUEST_TIMEOUT_SECONDS: int = 120 # Timeout for individual LLM API calls

    # --- Email Settings (Optional) ---
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_TLS: bool = True
    EMAIL_FROM: Optional[EmailStr] = None

    # --- Initial Admin User ---
    ADMIN_USERNAME: str = "admin"
    ADMIN_EMAIL: EmailStr = "admin@example.com"
    ADMIN_PASSWORD: str = "password" # Default password, CHANGE IN PRODUCTION

    class Config:
        env_file = ".env" # Load .env file if present
        env_file_encoding = 'utf-8'
        case_sensitive = True # Environment variables are case-sensitive

# Instantiate settings
try:
    settings = Settings()
    logger.info("Pydantic Settings object initialized successfully (excluding manual keys).")
    logger.info(f"Loaded DATABASE_URL: {settings.DATABASE_URL.host}:{settings.DATABASE_URL.port}/{settings.DATABASE_URL.path}") # Hide user/pass
    logger.info(f"Loaded USE_LLM_CACHE: {settings.USE_LLM_CACHE}")
except Exception as e:
    logger.error(f"Failed to initialize Pydantic Settings: {e}", exc_info=True)
    raise

# Log manually loaded keys after Pydantic init for completeness
logger.info("Manually loading and parsing API keys from environment variables...")
# The loading happens before Settings instantiation, log the result here
logger.info(f"Using {len(MANUAL_OPENROUTER_PROVISIONING_KEYS)} OpenRouter Provisioning Keys from environment.")
if not MANUAL_OPENROUTER_PROVISIONING_KEYS: logger.warning("OPENROUTER_PROVISIONING_KEYS was empty or not set.")
if any("REPLACE_WITH_YOUR_VALID" in k for k in MANUAL_OPENROUTER_PROVISIONING_KEYS): logger.warning("OpenRouter keys seem to contain placeholders.")

logger.info(f"Using {len(MANUAL_TAVILY_API_KEYS)} Tavily Keys from environment.")
if not MANUAL_TAVILY_API_KEYS: logger.warning("TAVILY_API_KEYS was empty or not set.")
if any("REPLACE_WITH_YOUR_VALID" in k for k in MANUAL_TAVILY_API_KEYS): logger.warning("Tavily keys seem to contain placeholders.")

logger.info("Manual API key loading complete.")
# Log final counts again for clarity
logger.info(f"Final Manual Prov Keys count: {len(settings.OPENROUTER_PROVISIONING_KEYS)}")
logger.info(f"Final Manual Tavily Keys count: {len(settings.TAVILY_API_KEYS)}")