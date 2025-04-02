
# file path='app/tasks/celery_app.py'
# app/tasks/celery_app.py

from celery import Celery
import logging
import sys
import os

# --- MODIFIED: Call setup_logging early ---
# Attempt to setup logging as soon as possible, although task-specific might be better
# Note: This might run *before* settings are fully loaded depending on import order,
# but it ensures *some* logging is configured for the worker process itself.
# A more robust approach is within the task or using worker_process_init signal.
try:
    from core.logging_config import setup_logging
    # Use defaults suitable for worker, force synchronous for debugging
    log_dir_worker = "/data/logs" if os.path.exists("/data") else "./logs_worker" # Use different dir to isolate
    os.makedirs(log_dir_worker, exist_ok=True) # Ensure it exists
    print(f"WORKER: Attempting initial logging setup to {log_dir_worker}")
    setup_logging(log_to_file=True, log_dir=log_dir_worker, async_logging=False, llm_trace_log_file="llm_api_trace_worker.log") # Force sync, maybe separate file
    print("WORKER: Initial logging setup attempted.")
except Exception as setup_err:
    print(f"WORKER: CRITICAL ERROR during initial logging setup: {setup_err}")
    # Fallback to basic config if setup fails
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

from core.logging_config import get_logger # Now get logger *after* potential setup

# Use direct signal imports from celery.signals
from celery.signals import task_prerun, task_postrun, task_failure

# --- Ensure get_logger is called *after* setup_logging attempt ---
logger = get_logger("vendor_classification.celery")
# --- END MODIFICATION ---


# Log diagnostic information to help debug import issues
logger.info( # Changed to info for visibility
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
    logger.info("Successfully imported settings") # Changed to info
except Exception as e:
    logger.error("Error importing settings", exc_info=True)
    raise

# Create Celery app with detailed logging
logger.info("Creating Celery app") # Changed to info
try:
    celery_app = Celery(
        "vendor_classification",
        broker=settings.REDIS_URL,
        backend=settings.REDIS_URL
    )
    logger.info("Celery app created", extra={"broker": settings.REDIS_URL}) # Changed to info

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
    logger.info("Celery configuration updated") # Changed to info

    # -----------------------------------------------------------------------
    # Signal Handlers (using direct imports)
    # -----------------------------------------------------------------------
    logger.info("Connecting Celery signal handlers...") # Added log

    @task_prerun.connect
    def handle_task_prerun(task_id, task, args, kwargs, **extra_options): # Added args/kwargs
        """Signal handler before task runs."""
        from core.logging_config import set_correlation_id, set_job_id
        # Assume job_id is the first argument for process_vendor_file
        job_id_from_args = args[0] if args else task_id
        set_correlation_id(job_id_from_args)
        set_job_id(job_id_from_args)
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
    def handle_task_postrun(task_id, task, args, kwargs, retval, state, **extra_options): # Added args/kwargs/retval/state
        """Signal handler after task completes."""
        from core.logging_config import clear_all_context
        logger.info(
            "Task finished running",
            extra={
                "signal": "task_postrun",
                "task_id": task_id,
                "task_name": task.name,
                "retval": repr(retval)[:200], # Log return value snippet
                "final_state": state
            }
        )
        clear_all_context() # Clean up context

    @task_failure.connect
    def handle_task_failure(task_id, exception, args, kwargs, traceback, einfo, **extra_options): # Added args/kwargs/etc.
        """Signal handler if task fails."""
        from core.logging_config import clear_all_context
        logger.error(
            "Task failed",
            exc_info=(type(exception), exception, traceback),
            extra={
                "signal": "task_failure",
                "task_id": task_id,
                "task_name": kwargs.get('task').name if 'task' in kwargs else 'UnknownTask', # Get task name safely
                "args": args,
                "kwargs": kwargs,
                "exception_type": type(exception).__name__,
                "error": str(exception),
            }
        )
        clear_all_context() # Clean up context

    logger.info("Celery signal handlers connected.") # Added log
    # -----------------------------------------------------------------------

except Exception as e:
    logger.error("Error creating or configuring Celery app", exc_info=True)
    raise

# Import tasks to register them - with error handling
logger.info("Attempting to import tasks for registration...") # Changed to info
try:
    # Import relative to the /app directory which is in PYTHONPATH
    from tasks.classification_tasks import process_vendor_file
    logger.info("Successfully imported 'tasks.classification_tasks.process_vendor_file'") # Changed to info
except ImportError as e:
    logger.error("ImportError when importing tasks", exc_info=True)
    # Log sys.path again specifically here if import fails
    logger.error(f"sys.path during task import: {sys.path}")
    raise
except Exception as e:
    logger.error("Unexpected error importing tasks", exc_info=True)
    raise

# Autodiscover tasks from installed apps (if using Django structure, otherwise less relevant)
# celery_app.autodiscover_tasks()
# logger.info("Celery autodiscover_tasks called (may not find tasks unless using specific structure)")

# Log discovered tasks explicitly
logger.info(f"Tasks registered in Celery app: {list(celery_app.tasks.keys())}")

logger.info("Celery app initialization finished.") # Changed to info

# Ensure the logger works even if run standalone
if __name__ == "__main__":
    # setup_logging() # Call the potentially modified setup
    logger.warning("celery_app.py run directly (likely for testing/debugging)")