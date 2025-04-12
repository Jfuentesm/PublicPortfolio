# <file path='app/core/config.py'>


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



# For development, we'll define them directly as defaults.
# NOTE FOR LLMS: DO NOT REPLACE THE DEFAULTS WITH PLACEHOLDER KEYS, these are safe dev-only keys


DEFAULT_OPENROUTER_KEYS = [
    "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", # Juan
    "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", # John
    "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", # lesley
    "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", # Jima
    "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" #lila
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
            # Basic check to warn if default placeholders might still be in use via ENV VAR
            if any("REPLACE_WITH_YOUR_VALID" in k for k in keys):
                 logger.warning(f"Environment variable {env_var_name} seems to contain placeholder keys. Ensure actual keys are set.")
            return keys
        else:
            logger.warning(f"Environment variable {env_var_name} found but contained no valid keys after splitting. Using defaults.")
    # Check if default list contains placeholders before using it
    if any("REPLACE_WITH_YOUR_VALID" in k for k in default_list):
         # This is the critical error path if defaults are placeholders and ENV is not set
         logger.error(f"CRITICAL: Environment variable {env_var_name} not found or empty, AND default keys are placeholders. API calls WILL fail. Please provide valid keys either via the environment variable or by editing the defaults in config.py.")
    else:
        logger.info(f"Environment variable {env_var_name} not found or empty. Using {len(default_list)} default keys.")
    return default_list


class Settings(BaseSettings):
    """Application settings."""

    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "NAICS Vendor Classification"
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:8080") # Added for password reset links

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey")  # Change in production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    # --- ADDED: Password Reset Token Expiry ---
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("PASSWORD_RESET_TOKEN_EXPIRE_MINUTES", 15)) # e.g., 15 minutes

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/vendor_classification")

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # File Storage
    INPUT_DATA_DIR: str = "/data/input"
    OUTPUT_DATA_DIR: str = "/data/output"
    TAXONOMY_DATA_DIR: str = "/data/taxonomy"

    # --- UPDATED: Use lists for API Keys ---
    # Load keys, potentially logging errors if defaults are placeholders
    OPENROUTER_API_KEYS: List[str] = _parse_comma_separated_list("OPENROUTER_API_KEYS", DEFAULT_OPENROUTER_KEYS)
    TAVILY_API_KEYS: List[str] = _parse_comma_separated_list("TAVILY_API_KEYS", DEFAULT_TAVILY_KEYS)
    # --- END UPDATED ---

    OPENROUTER_API_BASE: str = os.getenv("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1")
    # Consider making the model configurable or checking its availability
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat-v3-0324:free") # Check if this model is still valid/available

    # Processing Configuration
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", 5))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", 3))
    RETRY_DELAY: int = int(os.getenv("RETRY_DELAY", 1))  # seconds

    # --- ADDED: Email Configuration (Optional) ---
    # Set these in your .env file for actual email sending
    SMTP_HOST: Optional[str] = os.getenv("SMTP_HOST", None)
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER: Optional[str] = os.getenv("SMTP_USER", None)
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD", None)
    SMTP_TLS: bool = os.getenv("SMTP_TLS", "true").lower() == "true"
    EMAIL_FROM: Optional[str] = os.getenv("EMAIL_FROM", None) # Sender email

    # --- ADDED: LLM Cache Configuration ---
    USE_LLM_CACHE: bool = os.getenv("USE_LLM_CACHE", "false").lower() == "true"

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
        logger.info(f"Password reset token expiry: {self.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} minutes")
        logger.info(f"Frontend URL for links: {self.FRONTEND_URL}")
        logger.info(f"SMTP Configured: Host={self.SMTP_HOST is not None}, User={self.SMTP_USER is not None}, From={self.EMAIL_FROM is not None}")
        # --- ADDED: Log cache setting ---
        logger.info(f"LLM Cache Enabled: {self.USE_LLM_CACHE}")


        # Enhanced check for placeholder keys after initialization
        # This provides a second layer of warning/error if the parsing function didn't catch it
        # or if placeholders were somehow loaded via environment variables.
        if not self.OPENROUTER_API_KEYS or any("REPLACE_WITH_YOUR_VALID" in k for k in self.OPENROUTER_API_KEYS):
            logger.error("CRITICAL: No valid OpenRouter API keys loaded (either empty list or placeholders detected after initialization). LLM functionality WILL fail. Please provide valid keys via OPENROUTER_API_KEYS environment variable or update defaults in config.py.")
        if not self.TAVILY_API_KEYS or any("REPLACE_WITH_YOUR_VALID" in k for k in self.TAVILY_API_KEYS):
            logger.error("CRITICAL: No valid Tavily API keys loaded (either empty list or placeholders detected after initialization). Search functionality WILL fail. Please provide valid keys via TAVILY_API_KEYS environment variable or update defaults in config.py.")


settings = Settings()
logger.info("Application settings loaded successfully")

# </file>