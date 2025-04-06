
# app/core/logging_config.py
import logging
import os
import sys
import uuid
import queue
from logging.handlers import RotatingFileHandler, QueueHandler, QueueListener, TimedRotatingFileHandler
from typing import Optional

# Import from new/refactored modules
from .log_formatters import JsonFormatter
# Context functions are now used implicitly by the formatter or middleware

# Global variable to hold the queue listener instance
_queue_listener: Optional[QueueListener] = None

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    # This function remains simple, just returns the logger instance.
    # Configuration is handled by setup_logging.
    logger = logging.getLogger(name)
    return logger

def setup_logging(log_level: Optional[int] = None, log_to_file: bool = True, log_dir: str = "/data/logs",
                  log_format: str = "json", async_logging: bool = True,
                  llm_trace_log_file: str = "llm_api_trace.log"):
    """
    Setup application logging using the specified configuration.
    """
    # Determine log level from environment or parameter
    if log_level is None:
        env = os.getenv("ENVIRONMENT", "development").lower()
        log_level_name = os.getenv("LOG_LEVEL", "INFO" if env == "production" else "DEBUG")
        try:
            log_level = getattr(logging, log_level_name.upper())
        except AttributeError:
            print(f"WARNING: Invalid LOG_LEVEL '{log_level_name}'. Defaulting to INFO.")
            log_level = logging.INFO

    # Validate or create log directory
    effective_log_dir = None
    if log_to_file:
        if not log_dir:
            print("ERROR: log_to_file is True, but log_dir is not specified. Disabling file logging.")
            log_to_file = False
        else:
            try:
                abs_log_dir = os.path.abspath(log_dir)
                os.makedirs(abs_log_dir, exist_ok=True)
                # Test write permissions
                test_file_path = os.path.join(abs_log_dir, f"startup_test_{uuid.uuid4()}.log")
                with open(test_file_path, "w") as f:
                    f.write("Write test successful.")
                os.remove(test_file_path)
                effective_log_dir = abs_log_dir
                print(f"Logging directory verified: {effective_log_dir}")
            except OSError as e:
                print(f"ERROR: Could not create or write to logging directory {abs_log_dir}: {e}. Disabling file logging.")
                log_to_file = False
            except Exception as e:
                 print(f"ERROR: Unexpected error verifying logging directory {abs_log_dir}: {e}. Disabling file logging.")
                 log_to_file = False

    # Configure the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear any existing handlers to prevent duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        if hasattr(handler, 'close') and callable(handler.close):
             try: handler.close()
             except Exception as close_err: print(f"Error closing handler: {close_err}")

    # Select formatter based on format
    if log_format.lower() == 'json':
        formatter = JsonFormatter() # Use the imported formatter
    else:
        # Basic formatter as fallback (though JSON is recommended)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S,%f'
        )

    handlers = []

    # Create console handler (always add this one)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter) # Use selected formatter for console
    handlers.append(console_handler)

    # Create file handler if requested and directory is valid
    if log_to_file and effective_log_dir:
        try:
            main_log_path = os.path.join(effective_log_dir, "vendor_classification.log")
            print(f"Setting up main log file at: {main_log_path}")
            file_handler = RotatingFileHandler(
                main_log_path,
                maxBytes=10 * 1024 * 1024,  # 10 MB
                backupCount=10
            )
            file_handler.setFormatter(formatter)
            handlers.append(file_handler)

            # Create an error log file that only contains ERROR and higher
            error_log_path = os.path.join(effective_log_dir, "errors.log")
            print(f"Setting up error log file at: {error_log_path}")
            error_file_handler = RotatingFileHandler(
                error_log_path,
                maxBytes=10 * 1024 * 1024,  # 10 MB
                backupCount=10
            )
            error_file_handler.setFormatter(formatter)
            error_file_handler.setLevel(logging.ERROR)
            handlers.append(error_file_handler)

        except Exception as file_handler_err:
            print(f"ERROR: Failed to create file handlers in {effective_log_dir}: {file_handler_err}. File logging disabled.")
            handlers = [h for h in handlers if not isinstance(h, RotatingFileHandler)]
            log_to_file = False # Disable flag if handlers failed

    # --- Async Logging Setup ---
    global _queue_listener
    if _queue_listener:
        print("Stopping existing queue listener...")
        try:
            _queue_listener.stop()
            _queue_listener = None
        except Exception as stop_err:
             print(f"Error stopping existing listener: {stop_err}")

    if async_logging:
        log_queue = queue.Queue(-1) # Use an infinite queue size
        queue_handler = QueueHandler(log_queue)
        root_logger.addHandler(queue_handler) # Add ONLY the queue handler to root
        _queue_listener = QueueListener(log_queue, *handlers, respect_handler_level=True)
        _queue_listener.start()
        print("Async logging configured with QueueListener.")
    else:
        for handler in handlers:
            root_logger.addHandler(handler)
        print("Synchronous logging configured.")
    # --- End Async Logging Setup ---

    # --- LLM TRACE LOGGING SETUP ---
    if log_to_file and effective_log_dir and llm_trace_log_file:
        try:
            llm_trace_logger = logging.getLogger("llm_api_trace")
            llm_trace_logger.setLevel(logging.DEBUG) # Log everything for trace
            llm_trace_logger.propagate = False # Don't send to root logger

            for handler in llm_trace_logger.handlers[:]:
                llm_trace_logger.removeHandler(handler)
                if hasattr(handler, 'close') and callable(handler.close):
                    try: handler.close()
                    except Exception as close_err: print(f"Error closing existing trace handler: {close_err}")

            llm_trace_log_path = os.path.join(effective_log_dir, llm_trace_log_file)
            print(f"Setting up LLM trace log at: {llm_trace_log_path}")
            llm_trace_formatter = JsonFormatter() # Use the same JSON formatter
            llm_trace_handler = TimedRotatingFileHandler(
                 llm_trace_log_path, when='midnight', interval=1, backupCount=7
            )
            llm_trace_handler.setFormatter(llm_trace_formatter)
            llm_trace_logger.addHandler(llm_trace_handler)
            root_logger.info(f"LLM API trace logging initialized", extra={"file": llm_trace_log_path})
            llm_trace_logger.info("LLM_TRACE: Initialization successful.", extra={'correlation_id': 'startup'})
        except Exception as e:
            root_logger.error("Failed to initialize LLM API trace logging", exc_info=True)
            print(f"ERROR: Failed to initialize LLM API trace logging: {e}")
    elif log_to_file:
         root_logger.warning("LLM API trace logging disabled because file logging is disabled or trace filename is empty.")
    # --- END LLM TRACE LOGGING SETUP ---

    # Set specific log levels for noisy libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("celery").setLevel(logging.INFO)

    # Log setup completion
    root_logger.info(
        "Logging setup complete",
        extra={
            "log_level": logging.getLevelName(log_level),
            "log_dir": effective_log_dir if log_to_file else None,
            "handlers": [h.__class__.__name__ + (f' ({h.baseFilename})' if hasattr(h, 'baseFilename') else '') for h in handlers],
            "async_mode": async_logging
        }
    )

    return root_logger