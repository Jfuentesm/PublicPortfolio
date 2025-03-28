import os
import logging
from pydantic_settings import BaseSettings  # Updated import from pydantic-settings package
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("vendor_classification")

logger.info("Initializing application settings")

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
    
    # OpenRouter - HARDCODED API KEY FOR TESTING
    OPENROUTER_API_KEY: str = "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"  # Replace with your OpenRouter API key
    OPENROUTER_API_BASE: str = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL: str = "deepseek/deepseek-chat-v3-0324:free"  # Default model to use
    
    # Tavily Search API - HARDCODED API KEY FOR TESTING
    TAVILY_API_KEY: str = "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"
    
    # Processing Configuration
    BATCH_SIZE: int = 5
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 1  # seconds
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logger.info(f"Settings initialized with DATABASE_URL: {self.DATABASE_URL}")
        logger.info(f"OPENROUTER_MODEL: {self.OPENROUTER_MODEL}")
        # Log if keys are present but not their actual values for security
        logger.info(f"OPENROUTER_API_KEY present: {bool(self.OPENROUTER_API_KEY)}")
        logger.info(f"OPENROUTER_API_BASE present: {bool(self.OPENROUTER_API_BASE)}")
        logger.info(f"TAVILY_API_KEY present: {bool(self.TAVILY_API_KEY)}")

settings = Settings()
logger.info("Application settings loaded successfully")
