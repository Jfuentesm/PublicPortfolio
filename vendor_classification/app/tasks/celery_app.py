from celery import Celery
import logging
import sys
import os

from core.logging_config import setup_logging, get_logger

# New: Import Celery signals directly from celery.signals
from celery.signals import task_prerun, task_postrun, task_failure

logger = get_logger("vendor_classification.celery")

# Log diagnostic information to help debug import issues
logger.debug(
    f"Initializing Celery app",
    extra={
        "python_executable": sys.executable,
        "python_version": sys.version,
        "python_path": sys.path,
        "cwd": os.getcwd()
    }
)

try:
    from core.config import settings
    logger.debug("Successfully imported settings")
except Exception as e:
    logger.error("Error importing settings", exc_info=True)
    raise

# Create Celery app with detailed logging
logger.debug("Creating Celery app")
try:
    celery_app = Celery(
        "vendor_classification",
        broker=settings.REDIS_URL,
        backend=settings.REDIS_URL
    )
    logger.debug("Celery app created", extra={"broker": settings.REDIS_URL})

    # Configure Celery
    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_send_sent_event=True,
    )
    logger.debug("Celery configuration updated")

    # -----------------------------------------------------------------------
    # Updated signal definitions: Use @task_prerun.connect instead of
    # @celery_app.task_prerun.connect, same for postrun and failure.
    # -----------------------------------------------------------------------
    @task_prerun.connect
    def handle_task_prerun(task_id, task, *args, **kwargs):
        """
        Signal handler that fires before a task runs.
        We attach correlation/job IDs for logging, etc.
        """
        from core.logging_config import set_correlation_id, set_job_id
        # Decide how to parse job_id from arguments:
        # Often your first positional arg is job_id, or fallback to the task_id
        if args and len(args) > 0:
            possible_job_id = args[0]
        else:
            possible_job_id = task_id

        set_correlation_id(possible_job_id)
        set_job_id(possible_job_id)
        logger.info(
            "task_prerun signal fired",
            extra={
                "signal": "task_prerun",
                "task_id": task_id,
                "task_name": task.name,
                "raw_args": str(args),
                "parsed_job_id": possible_job_id
            }
        )

    @task_postrun.connect
    def handle_task_postrun(task_id, task, retval, state, *args, **kwargs):
        """
        Signal handler that fires after a task completes (success or fail).
        """
        logger.info(
            "task_postrun signal fired",
            extra={
                "signal": "task_postrun",
                "task_id": task_id,
                "task_name": task.name,
                "final_state": state
            }
        )

    @task_failure.connect
    def handle_task_failure(task_id, exception, traceback, einfo, *args, **kwargs):
        """
        Signal handler that fires if a task raises an exception.
        """
        logger.error(
            "task_failure signal fired",
            exc_info=(type(exception), exception, traceback),
            extra={
                "signal": "task_failure",
                "task_id": task_id,
                "error": str(exception),
            }
        )
    # -----------------------------------------------------------------------

except Exception as e:
    logger.error("Error creating Celery app", exc_info=True)
    raise

# Import tasks to register them - with error handling
logger.debug("Importing tasks")
try:
    # Explicitly use absolute imports
    from app.tasks.classification_tasks import process_vendor_file
    logger.debug("Successfully imported tasks")
except Exception as e:
    logger.error("Error importing tasks with absolute import", exc_info=True)
    # Try relative import if absolute import fails
    try:
        from .classification_tasks import process_vendor_file
        logger.debug("Successfully imported tasks using relative import")
    except Exception as e2:
        logger.error("Error importing tasks with relative import", exc_info=True)
        raise

logger.debug("Celery app initialization complete")