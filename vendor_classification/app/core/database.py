import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from core.config import settings

# Configure logging
logger = logging.getLogger("vendor_classification.database")

logger.info("Initializing database connection")

# Create SQLAlchemy engine
try:
    engine = create_engine(settings.DATABASE_URL)
    logger.info(f"Database engine created successfully for {settings.DATABASE_URL.split('@')[-1]}")
except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
    raise

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
logger.info("Database session factory created")

# Create base class for models
Base = declarative_base()
logger.info("SQLAlchemy Base declarative_base initialized")

def get_db():
    """Get database session."""
    db = SessionLocal()
    logger.debug("Database session created")
    try:
        yield db
    finally:
        db.close()
        logger.debug("Database session closed")