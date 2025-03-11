from celery import Celery
import logging
import sys
import os

# Setup logging to help debug import issues
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("celery_app")

# Log diagnostic information to help debug import issues
logger.debug(f"Python executable: {sys.executable}")
logger.debug(f"Python version: {sys.version}")
logger.debug(f"Python path: {sys.path}")
logger.debug(f"Current working directory: {os.getcwd()}")
logger.debug(f"Directory contents: {os.listdir('.')}")

try:
    from core.config import settings
    logger.debug("Successfully imported settings")
except Exception as e:
    logger.error(f"Error importing settings: {e}")
    raise

# Create Celery app with detailed logging
logger.debug("Creating Celery app")
try:
    celery_app = Celery(
        "vendor_classification",
        broker=settings.REDIS_URL,
        backend=settings.REDIS_URL
    )
    logger.debug(f"Celery app created with broker: {settings.REDIS_URL}")

    # Configure Celery
    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
    )
    logger.debug("Celery configuration updated")
except Exception as e:
    logger.error(f"Error creating Celery app: {e}")
    raise

# Import tasks to register them - with error handling
logger.debug("Importing tasks")
try:
    # Explicitly use absolute imports
    from app.tasks.classification_tasks import process_vendor_file
    logger.debug("Successfully imported tasks")
except Exception as e:
    logger.error(f"Error importing tasks: {e}")
    # Try relative import if absolute import fails
    try:
        from .classification_tasks import process_vendor_file
        logger.debug("Successfully imported tasks using relative import")
    except Exception as e2:
        logger.error(f"Error using relative import for tasks: {e2}")
        raise

logger.debug("celery_app.py initialization complete")