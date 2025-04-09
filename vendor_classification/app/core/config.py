# app/core/config.py
import os
import logging
from pydantic_settings import BaseSettings
from typing import Optional, List # Added List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("vendor_classification")

logger.info("Initializing application settings")

# --- Define Key Lists ---
# It's better to load these from environment variables in production
# Example ENV format: TAVILY_API_KEYS="key1,key2,key3"
# For this exercise, we'll define them directly as defaults.
DEFAULT_OPENROUTER_KEYS = [
    "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",
    "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"
]

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

def _parse_comma_separated_list(env_var_name: str, default_list: List[str]) -> List[str]:
    """Parses a comma-separated string from env var or returns default."""
    value = os.getenv(env_var_name)
    if value:
        keys = [k.strip() for k in value.split(',') if k.strip()]
        if keys:
            logger.info(f"Loaded {len(keys)} keys from environment variable {env_var_name}")
            return keys
        else:
            logger.warning(f"Environment variable {env_var_name} found but contained no valid keys after splitting. Using defaults.")
    logger.info(f"Environment variable {env_var_name} not found or empty. Using {len(default_list)} default keys.")
    return default_list


class Settings(BaseSettings):
    """Application settings."""

    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "NAICS Vendor Classification"

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey")  # Change in production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/vendor_classification")

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # File Storage
    INPUT_DATA_DIR: str = "/data/input"
    OUTPUT_DATA_DIR: str = "/data/output"
    TAXONOMY_DATA_DIR: str = "/data/taxonomy"

    # --- UPDATED: Use lists for API Keys ---
    OPENROUTER_API_KEYS: List[str] = _parse_comma_separated_list("OPENROUTER_API_KEYS", DEFAULT_OPENROUTER_KEYS)
    TAVILY_API_KEYS: List[str] = _parse_comma_separated_list("TAVILY_API_KEYS", DEFAULT_TAVILY_KEYS)
    # --- END UPDATED ---

    OPENROUTER_API_BASE: str = os.getenv("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat-v3-0324:free")

    # Processing Configuration
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", 5))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", 3))
    RETRY_DELAY: int = int(os.getenv("RETRY_DELAY", 1))  # seconds

    class Config:
        env_file = ".env"
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logger.info(f"Settings initialized with DATABASE_URL: {self.DATABASE_URL}")
        logger.info(f"OPENROUTER_MODEL: {self.OPENROUTER_MODEL}")
        # Log counts instead of keys
        logger.info(f"Number of OpenRouter API keys loaded: {len(self.OPENROUTER_API_KEYS)}")
        logger.info(f"OPENROUTER_API_BASE present: {bool(self.OPENROUTER_API_BASE)}")
        logger.info(f"Number of Tavily API keys loaded: {len(self.TAVILY_API_KEYS)}")

        if not self.OPENROUTER_API_KEYS:
            logger.error("CRITICAL: No OpenRouter API keys loaded. LLM functionality will fail.")
        if not self.TAVILY_API_KEYS:
            logger.error("CRITICAL: No Tavily API keys loaded. Search functionality will fail.")


settings = Settings()
logger.info("Application settings loaded successfully")