# app/core/logging_config.py
import logging
import os
import sys
import json
import time
import threading
import uuid
import socket
import inspect
import traceback
from datetime import datetime
from logging.handlers import RotatingFileHandler, QueueHandler, QueueListener
from typing import Dict, Any, Optional, List, Callable
import queue
from contextlib import contextmanager

# Create a thread-local storage for correlation IDs and context
local_storage = threading.local()

class JsonFormatter(logging.Formatter):
    """Format logs as JSON for better parsing and analysis."""

    def format(self, record):
        timestamp = datetime.utcfromtimestamp(record.created).isoformat() + "Z"

        log_data = {
            "timestamp": timestamp,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process_id": record.process,
            "thread_id": record.thread,
            "host": socket.gethostname(),
        }

        # Add correlation ID if available
        if hasattr(local_storage, 'correlation_id'):
            log_data["correlation_id"] = local_storage.correlation_id

        # Add request ID if available
        if hasattr(local_storage, 'request_id'):
            log_data["request_id"] = local_storage.request_id

        # Add job ID if available
        if hasattr(local_storage, 'job_id'):
            log_data["job_id"] = local_storage.job_id

        # Add user info if available
        if hasattr(local_storage, 'user'):
            log_data["user"] = local_storage.user

        # Add any additional context if available
        if hasattr(local_storage, 'context') and local_storage.context:
            log_data["context"] = local_storage.context

        # Add exception info if available
        if record.exc_info:
            exception_type = record.exc_info[0].__name__ if record.exc_info[0] else "Unknown"
            exception_msg = str(record.exc_info[1]) if record.exc_info[1] else ""
            log_data["exception"] = {
                "type": exception_type,
                "message": exception_msg,
                "traceback": self.formatException(record.exc_info)
            }

        # Add stack info if available
        if record.stack_info:
            log_data["stack_info"] = record.stack_info

        # Add any extra attributes from the record
        # --- MODIFIED: Added check for 'extra' attribute before iterating ---
        extra_data = getattr(record, 'extra', {})
        if isinstance(extra_data, dict):
            for key, value in extra_data.items():
                 # Avoid duplicating standard fields or context already added
                 if key not in log_data and key not in ['correlation_id', 'request_id', 'job_id', 'user', 'context']:
                    log_data[key] = value
        # --- END MODIFIED ---

        # Add standard fields not already included explicitly
        for key, value in record.__dict__.items():
            if key not in log_data and key not in [
                'args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
                'funcName', 'id', 'levelname', 'levelno', 'lineno', 'module',
                'msecs', 'message', 'msg', 'name', 'pathname', 'process',
                'processName', 'relativeCreated', 'stack_info', 'thread', 'threadName',
                'extra' # Also exclude 'extra' itself
            ]:
                log_data[key] = value


        return json.dumps(log_data)


class ContextAdapter(logging.LoggerAdapter):
    """Adapter that adds context to log records."""

    def process(self, msg, kwargs):
        # Ensure 'extra' exists
        kwargs.setdefault('extra', {})

        # Add correlation_id from thread-local storage if available
        if hasattr(local_storage, 'correlation_id'):
            kwargs['extra']['correlation_id'] = local_storage.correlation_id

        # Add request_id from thread-local storage if available
        if hasattr(local_storage, 'request_id'):
            kwargs['extra']['request_id'] = local_storage.request_id

        # Add job_id from thread-local storage if available
        if hasattr(local_storage, 'job_id'):
            kwargs['extra']['job_id'] = local_storage.job_id

        # Add user from thread-local storage if available
        if hasattr(local_storage, 'user'):
            kwargs['extra']['user'] = local_storage.user

        # Add context from thread-local storage if available
        if hasattr(local_storage, 'context') and local_storage.context:
            for key, value in local_storage.context.items():
                kwargs['extra'][key] = value

        # Add caller information
        if not kwargs.get('stacklevel'):
            kwargs['stacklevel'] = 2  # Default to the caller of this adapter

        return msg, kwargs


def set_correlation_id(correlation_id=None):
    """Set a correlation ID for the current thread."""
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())
    local_storage.correlation_id = correlation_id
    return correlation_id


def get_correlation_id():
    """Get the current correlation ID."""
    if not hasattr(local_storage, 'correlation_id'):
        return None
    return local_storage.correlation_id


def set_request_id(request_id=None):
    """Set a request ID for the current thread."""
    if request_id is None:
        request_id = str(uuid.uuid4())
    local_storage.request_id = request_id
    return request_id


def get_request_id():
    """Get the current request ID."""
    if not hasattr(local_storage, 'request_id'):
        return None
    return local_storage.request_id


def set_job_id(job_id):
    """Set a job ID for the current thread."""
    local_storage.job_id = job_id
    return job_id


def get_job_id():
    """Get the current job ID."""
    if not hasattr(local_storage, 'job_id'):
        return None
    return local_storage.job_id


def set_user(user):
    """Set user information for the current thread."""
    if isinstance(user, dict):
        local_storage.user = user
    elif hasattr(user, 'username'):
        local_storage.user = {'username': user.username, 'id': getattr(user, 'id', None)}
    else:
        local_storage.user = {'username': str(user)}
    return local_storage.user


def get_user():
    """Get the current user information."""
    if not hasattr(local_storage, 'user'):
        return None
    return local_storage.user


def set_log_context(context_dict):
    """Add context data to logs for the current thread."""
    if not hasattr(local_storage, 'context'):
        local_storage.context = {}

    local_storage.context.update(context_dict)


def clear_log_context():
    """Clear the log context for the current thread."""
    if hasattr(local_storage, 'context'):
        local_storage.context = {}


def get_log_context():
    """Get the current log context."""
    if not hasattr(local_storage, 'context'):
        return {}
    return local_storage.context.copy()


def clear_all_context():
    """Clear all context data for the current thread."""
    if hasattr(local_storage, 'correlation_id'):
        delattr(local_storage, 'correlation_id')
    if hasattr(local_storage, 'request_id'):
        delattr(local_storage, 'request_id')
    if hasattr(local_storage, 'job_id'):
        delattr(local_storage, 'job_id')
    if hasattr(local_storage, 'user'):
        delattr(local_storage, 'user')
    if hasattr(local_storage, 'context'):
        delattr(local_storage, 'context')


def get_logger(name):
    """Get a logger with the specified name."""
    logger = logging.getLogger(name)
    # Apply the ContextAdapter only if it's not the LLM trace logger
    # to avoid double context injection if used directly
    if name != "llm_api_trace":
        return ContextAdapter(logger, {})
    return logger # Return the raw logger for the trace logger


def setup_logging(log_level=None, log_to_file=True, log_dir="/data/logs",
                  log_format="json", async_logging=True,
                  llm_trace_log_file="llm_api_trace.log"): # <-- ADDED PARAMETER
    """
    Setup application logging.

    Args:
        log_level: Logging level (DEBUG, INFO, etc.)
        log_to_file: Whether to log to file
        log_dir: Directory to store log files
        log_format: Format of logs ('json' or 'text')
        async_logging: Whether to use async logging (recommended for production)
        llm_trace_log_file: Filename for the separate LLM API trace log.

    Returns:
        Logger instance (root logger)
    """
    # Determine log level from environment or parameter
    if log_level is None:
        env = os.getenv("ENVIRONMENT", "development").lower()
        log_level_name = os.getenv("LOG_LEVEL", "INFO" if env == "production" else "DEBUG")
        log_level = getattr(logging, log_level_name.upper())

    # Create logs directory if it doesn't exist
    if log_to_file and log_dir:
        try:
            os.makedirs(log_dir, exist_ok=True)
            print(f"Logging directory created: {log_dir}") # Basic print for early confirmation
        except OSError as e:
            print(f"ERROR: Could not create logging directory {log_dir}: {e}")
            # Consider exiting here if logging essential or using a default local dir
            log_to_file = False # Disable file logging if can't create dir
            log_dir = None
        os.makedirs(log_dir, exist_ok=True)

    # Configure the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Select formatter based on format
    if log_format.lower() == 'json':
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    handlers = []

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)

    # Create file handler if requested
    if log_to_file and log_dir:
        # Use rotating file handler to manage log size
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, "vendor_classification.log"),
            maxBytes=10485760,  # 10 MB
            backupCount=10
        )
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

        # Create an error log file that only contains ERROR and higher
        error_file_handler = RotatingFileHandler(
            os.path.join(log_dir, "errors.log"),
            maxBytes=10485760,  # 10 MB
            backupCount=10
        )
        error_file_handler.setFormatter(formatter)
        error_file_handler.setLevel(logging.ERROR)
        handlers.append(error_file_handler)

    if async_logging:
        # Set up async logging using QueueHandler and QueueListener
        log_queue = queue.Queue()
        queue_handler = QueueHandler(log_queue)
        root_logger.addHandler(queue_handler)

        # Start queue listener with all handlers
        listener = QueueListener(log_queue, *handlers)
        listener.start()

        # Store the listener in a global variable to prevent it from being garbage collected
        global _queue_listener
        _queue_listener = listener
    else:
        # Add handlers directly to the root logger
        for handler in handlers:
            root_logger.addHandler(handler)

    # --- ADDED LLM TRACE LOGGING SETUP ---
    if log_to_file and log_dir and llm_trace_log_file:
        try:
            llm_trace_logger = logging.getLogger("llm_api_trace")
            llm_trace_logger.setLevel(logging.DEBUG) # Log everything for trace
            llm_trace_logger.propagate = False # Don't send to root logger

            llm_trace_log_path = os.path.join(log_dir, llm_trace_log_file)
            # --- ADDED: Check if file already exists before creating handler to prevent errors ---
            llm_trace_logger.info(f"Checking existence of LLM trace log file: {llm_trace_log_path}")
            if not os.path.exists(llm_trace_log_path):
                llm_trace_logger.info("LLM trace log file does not exist, creating...")
                # Use a rotating file handler to manage log size
                llm_trace_handler = RotatingFileHandler(
                    llm_trace_log_path,
                    maxBytes=20971520, # 20 MB for potentially large payloads
                    backupCount=5
                )

                # Use a simple text formatter for readability
                llm_trace_formatter = logging.Formatter(
                    '%(asctime)s - %(levelname)s - [%(correlation_id)s] %(message)s',
                     datefmt='%Y-%m-%d %H:%M:%S,%f' # Added milliseconds
                )
                llm_trace_handler.setFormatter(llm_trace_formatter)
                llm_trace_logger.addHandler(llm_trace_handler)
                root_logger.info(f"LLM API trace logging initialized", extra={"file": llm_trace_log_path})
            else:
                llm_trace_logger.warning(f"LLM trace log file already exists at {llm_trace_log_path}, not creating new handler.")
        except Exception as e:
            root_logger.error("Failed to initialize LLM API trace logging", exc_info=True)
    # --- END ADDED LLM TRACE LOGGING SETUP ---


    # Set specific log levels for noisy libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    # Log setup completion
    root_logger.info(
        "Logging initialized",
        extra={
            "log_level": logging.getLevelName(log_level),
            "log_dir": log_dir if log_to_file else None,
            "handlers": ["console"] + ([h.baseFilename for h in handlers if isinstance(h, RotatingFileHandler)]),
            "async_mode": async_logging
        }
    )

    return root_logger


# Timer utility for performance logging
class LogTimer:
    def __init__(self, logger, description="Operation", level=logging.DEBUG,
                 include_in_stats=False, stats_name=None):
        """
        Initialize a timer for logging operation duration.

        Args:
            logger: Logger instance
            description: Description of the operation being timed
            level: Log level for the timer messages
            include_in_stats: Whether to add this timing to thread-local performance stats
            stats_name: Name to use for this timing in performance stats
        """
        self.logger = logger
        self.description = description
        self.level = level
        self.start_time = None
        self.include_in_stats = include_in_stats
        self.stats_name = stats_name or description

    def __enter__(self):
        self.start_time = time.time()
        self.logger.log(self.level, f"Starting: {self.description}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.time() - self.start_time

        # Store stats if requested
        if self.include_in_stats:
            if not hasattr(local_storage, 'performance_stats'):
                local_storage.performance_stats = {}

            if self.stats_name not in local_storage.performance_stats:
                local_storage.performance_stats[self.stats_name] = {
                    'count': 0,
                    'total_time': 0,
                    'min_time': float('inf'),
                    'max_time': 0
                }

            stats = local_storage.performance_stats[self.stats_name]
            stats['count'] += 1
            stats['total_time'] += elapsed
            stats['min_time'] = min(stats['min_time'], elapsed)
            stats['max_time'] = max(stats['max_time'], elapsed)

        if exc_type:
            self.logger.error(
                f"Failed: {self.description} in {elapsed:.3f}s",
                exc_info=(exc_type, exc_val, exc_tb),
                extra={
                    "duration": elapsed,
                    "error": str(exc_val) if exc_val else None
                }
            )
        else:
            self.logger.log(
                self.level,
                f"Completed: {self.description} in {elapsed:.3f}s",
                extra={"duration": elapsed}
            )


def get_performance_stats():
    """Get the current performance statistics."""
    if not hasattr(local_storage, 'performance_stats'):
        return {}
    return local_storage.performance_stats.copy()


def clear_performance_stats():
    """Clear the performance statistics."""
    if hasattr(local_storage, 'performance_stats'):
        delattr(local_storage, 'performance_stats')


@contextmanager
def log_duration(logger, description="Operation", level=logging.DEBUG, include_in_stats=False):
    """
    Context manager for logging the duration of a code block.

    Args:
        logger: Logger instance
        description: Description of the operation being timed
        level: Log level for the timer messages
        include_in_stats: Whether to add this timing to thread-local performance stats

    Usage:
        with log_duration(logger, "My operation"):
            # code to time
    """
    try:
        timer = LogTimer(logger, description, level, include_in_stats)
        timer.__enter__()
        yield
    except Exception as e:
        timer.__exit__(type(e), e, traceback.format_exc())
        raise
    else:
        timer.__exit__(None, None, None)


def log_function_call(logger, level=logging.DEBUG, include_args=True,
                      include_result=False, include_in_stats=False):
    """
    Decorator to log function calls with parameters and return value.

    Args:
        logger: Logger instance
        level: Log level for the log messages
        include_args: Whether to include function arguments in log
        include_result: Whether to include function result in log
        include_in_stats: Whether to add timing to performance stats

    Usage:
        @log_function_call(logger)
        def my_function(x, y):
            return x + y
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Get function name and module
            func_name = func.__name__
            module_name = func.__module__

            # Format arguments if requested
            args_str = ""
            if include_args:
                # Get argument names from function signature
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()

                # Format arguments as string, handling self/cls for methods
                arg_items = []
                for name, value in bound_args.arguments.items():
                    if name in ('self', 'cls') and hasattr(value, '__class__'):
                        arg_items.append(f"{name}={value.__class__.__name__}")
                    else:
                        # Limit string representation length
                        value_str = repr(value)
                        if len(value_str) > 100:
                            value_str = value_str[:97] + "..."
                        arg_items.append(f"{name}={value_str}")

                args_str = ", ".join(arg_items)

            # Log function entry
            logger.log(level, f"Calling {module_name}.{func_name}({args_str})")

            # Execute the function with timing
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time

                # Add to performance stats if requested
                if include_in_stats:
                    if not hasattr(local_storage, 'performance_stats'):
                        local_storage.performance_stats = {}

                    stats_name = f"{module_name}.{func_name}"
                    if stats_name not in local_storage.performance_stats:
                        local_storage.performance_stats[stats_name] = {
                            'count': 0,
                            'total_time': 0,
                            'min_time': float('inf'),
                            'max_time': 0
                        }

                    stats = local_storage.performance_stats[stats_name]
                    stats['count'] += 1
                    stats['total_time'] += elapsed
                    stats['min_time'] = min(stats['min_time'], elapsed)
                    stats['max_time'] = max(stats['max_time'], elapsed)

                # Log function exit
                extra = {"duration": elapsed}
                if include_result:
                    result_str = repr(result)
                    if len(result_str) > 100:
                        result_str = result_str[:97] + "..."
                    extra["result"] = result_str

                logger.log(
                    level,
                    f"Completed {module_name}.{func_name} in {elapsed:.3f}s",
                    extra=extra
                )

                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(
                    f"Failed {module_name}.{func_name} in {elapsed:.3f}s: {str(e)}",
                    exc_info=True,
                    extra={"duration": elapsed, "error": str(e)}
                )
                raise

        return wrapper

    return decorator