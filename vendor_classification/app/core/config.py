# app/core/config.py
import os
import logging
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional, List, Union, Dict, Any
import sys
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("vendor_classification.config")

# --- Defaults remain the same ---
DEFAULT_OPENROUTER_PROVISIONING_KEYS = ["REPLACE_WITH_YOUR_VALID_OPENROUTER_PROVISIONING_KEY"]
DEFAULT_TAVILY_KEYS = [
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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"
]

# --- Parsing function remains the same ---
def _parse_string_to_list(value: Optional[str]) -> List[str]:
    """Parses a comma-separated string into a list of strings."""
    if not value:
        return []
    return [k.strip() for k in value.split(',') if k.strip()]

class Settings(BaseSettings):
    """Application settings (excluding manually parsed lists)."""
    model_config = SettingsConfigDict(
        env_file='.env',
        case_sensitive=True,
        extra='ignore'
    )

    # --- REMOVED problematic List fields ---
    # OPENROUTER_PROVISIONING_KEYS: List[str] = ...
    # TAVILY_API_KEYS: List[str] = ...

    # --- Other Settings ---
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "NAICS Vendor Classification"
    FRONTEND_URL: str = "http://localhost:8080"
    SECRET_KEY: str = "supersecretkey"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 15
    DATABASE_URL: str = Field("postgresql://user:pass@host:port/db", validation_alias='DATABASE_URL')
    REDIS_URL: str = "redis://localhost:6379/0"
    INPUT_DATA_DIR: str = "/data/input"
    OUTPUT_DATA_DIR: str = "/data/output"
    TAXONOMY_DATA_DIR: str = "/data/taxonomy"
    OPENROUTER_API_BASE: str = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL: str = "deepseek/deepseek-chat-v3-0324:free"
    GENERATED_KEY_NAME_PREFIX: str = "auto-gen-vendor-classifier"
    GENERATED_KEY_LABEL: Optional[str] = None
    GENERATED_KEY_CREDIT_LIMIT: Optional[float] = None
    BATCH_SIZE: int = 5
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 1
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_TLS: bool = True
    EMAIL_FROM: Optional[str] = None
    USE_LLM_CACHE: bool = False

# === Instantiate Settings (loads from .env EXCEPT for the removed fields) ===
try:
    settings = Settings()
    logger.info("Pydantic Settings object initialized successfully (excluding manual keys).")
    logger.info(f"Loaded DATABASE_URL: {settings.DATABASE_URL}") # Example check
    logger.info(f"Loaded USE_LLM_CACHE: {settings.USE_LLM_CACHE}")
except Exception as e:
     logger.error(f"CRITICAL: Failed to initialize Pydantic Settings object: {e}", exc_info=True)
     sys.exit("Failed to initialize settings.")


# === Manual Loading Section (Now assigns to module-level variables) ===
logger.info("Manually loading and parsing API keys from environment variables...")

# OpenRouter Provisioning Keys
openrouter_prov_keys_str = os.getenv('OPENROUTER_PROVISIONING_KEYS')
parsed_prov_keys = _parse_string_to_list(openrouter_prov_keys_str)
MANUAL_OPENROUTER_PROVISIONING_KEYS = parsed_prov_keys if parsed_prov_keys else DEFAULT_OPENROUTER_PROVISIONING_KEYS
if MANUAL_OPENROUTER_PROVISIONING_KEYS == DEFAULT_OPENROUTER_PROVISIONING_KEYS:
     logger.info("Using default OpenRouter Provisioning Keys.")
else:
     logger.info(f"Using {len(MANUAL_OPENROUTER_PROVISIONING_KEYS)} OpenRouter Provisioning Keys from environment.")
# Critical check for placeholders
if any("REPLACE_WITH_YOUR_VALID" in k for k in MANUAL_OPENROUTER_PROVISIONING_KEYS):
    logger.error("CRITICAL: Manually loaded OpenRouter Provisioning Keys contain placeholders!")

# Tavily API Keys
tavily_api_keys_str = os.getenv('TAVILY_API_KEYS')
parsed_tavily_keys = _parse_string_to_list(tavily_api_keys_str)
MANUAL_TAVILY_API_KEYS = parsed_tavily_keys if parsed_tavily_keys else DEFAULT_TAVILY_KEYS
if MANUAL_TAVILY_API_KEYS == DEFAULT_TAVILY_KEYS:
     logger.info("Using default Tavily Keys.")
else:
     logger.info(f"Using {len(MANUAL_TAVILY_API_KEYS)} Tavily Keys from environment.")
# Optional placeholder check
if any("REPLACE_WITH_YOUR_VALID" in k for k in MANUAL_TAVILY_API_KEYS):
    logger.warning("Warning: Manually loaded Tavily Keys may contain placeholders.")


logger.info("Manual API key loading complete.")
logger.info(f"Final Manual Prov Keys count: {len(MANUAL_OPENROUTER_PROVISIONING_KEYS)}")
logger.info(f"Final Manual Tavily Keys count: {len(MANUAL_TAVILY_API_KEYS)}")
