# app/tasks/celery_app.py
from celery import Celery
import logging
import sys
import os

# Attempt initial logging setup
try:
    from core.logging_config import setup_logging
    log_dir_worker = "/data/logs" if os.path.exists("/data") else "./logs_worker"
    os.makedirs(log_dir_worker, exist_ok=True)
    print(f"WORKER: Attempting initial logging setup to {log_dir_worker}")
    setup_logging(log_to_file=True, log_dir=log_dir_worker, async_logging=False, llm_trace_log_file="llm_api_trace_worker.log")
    print("WORKER: Initial logging setup attempted.")
except Exception as setup_err:
    print(f"WORKER: CRITICAL ERROR during initial logging setup: {setup_err}")
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Import logger *after* setup attempt
from core.logging_config import get_logger
# Import context functions from the new module
from core.log_context import set_correlation_id, set_job_id, clear_all_context

# Use direct signal imports from celery.signals
from celery.signals import task_prerun, task_postrun, task_failure

logger = get_logger("vendor_classification.celery")

# Log diagnostic information
logger.info(
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
    logger.info("Successfully imported settings")
except Exception as e:
    logger.error("Error importing settings", exc_info=True)
    raise

# Create Celery app
logger.info("Creating Celery app")
try:
    celery_app = Celery(
        "vendor_classification",
        broker=settings.REDIS_URL,
        backend=settings.REDIS_URL
    )
    logger.info("Celery app created", extra={"broker": settings.REDIS_URL})

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
    logger.info("Celery configuration updated")

    # Signal Handlers
    logger.info("Connecting Celery signal handlers...")

    @task_prerun.connect
    def handle_task_prerun(task_id, task, args, kwargs, **extra_options):
        """Signal handler before task runs."""
        clear_all_context() # Clear any lingering context
        # Determine job_id based on common kwargs patterns
        job_id = kwargs.get('job_id') or kwargs.get('review_job_id') or (args[0] if args else None) or task_id
        set_correlation_id(job_id) # Use job_id as correlation_id
        set_job_id(job_id)
        logger.info(
            "Task about to run",
            extra={
                "signal": "task_prerun",
                "task_id": task_id,
                "task_name": task.name,
                "args": args,
                "kwargs": kwargs
            }
        )

    @task_postrun.connect
    def handle_task_postrun(task_id, task, args, kwargs, retval, state, **extra_options):
        """Signal handler after task completes."""
        logger.info(
            "Task finished running",
            extra={
                "signal": "task_postrun",
                "task_id": task_id,
                "task_name": task.name,
                "retval": repr(retval)[:200],
                "final_state": state
            }
        )
        clear_all_context() # Clean up context

    @task_failure.connect
    def handle_task_failure(task_id, exception, args, kwargs, traceback, einfo, **extra_options):
        """Signal handler if task fails."""
        task_name = getattr(kwargs.get('task'), 'name', None) or getattr(einfo, 'task', {}).get('name', 'UnknownTask')
        logger.error(
            "Task failed",
            exc_info=(type(exception), exception, traceback),
            extra={
                "signal": "task_failure",
                "task_id": task_id,
                "task_name": task_name,
                "args": args,
                "kwargs": kwargs,
                "exception_type": type(exception).__name__,
                "error": str(exception),
                "einfo": str(einfo)[:1000] if einfo else None
            }
        )
        clear_all_context() # Clean up context

    logger.info("Celery signal handlers connected.")

except Exception as e:
    logger.error("Error creating or configuring Celery app", exc_info=True)
    raise

# Import tasks to register them
logger.info("Attempting to import tasks for registration...")
try:
    # Import original classification task
    from tasks.classification_tasks import process_vendor_file
    logger.info("Successfully imported 'tasks.classification_tasks.process_vendor_file'")
    # --- CORRECTED: Import reclassification task from classification_tasks ---
    from tasks.classification_tasks import reclassify_flagged_vendors_task
    logger.info("Successfully imported 'tasks.classification_tasks.reclassify_flagged_vendors_task'")
    # --- END CORRECTED ---
except ImportError as e:
    logger.error("ImportError when importing tasks", exc_info=True)
    logger.error(f"sys.path during task import: {sys.path}")
    raise
except Exception as e:
    logger.error("Unexpected error importing tasks", exc_info=True)
    raise

# Log discovered tasks
logger.info(f"Tasks registered in Celery app: {list(celery_app.tasks.keys())}")

logger.info("Celery app initialization finished.")

if __name__ == "__main__":
    logger.warning("celery_app.py run directly (likely for testing/debugging)")