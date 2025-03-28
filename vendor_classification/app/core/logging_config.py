
# --- file path='app/core/logging_config.py' ---
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
from logging.handlers import RotatingFileHandler, QueueHandler, QueueListener, TimedRotatingFileHandler
from typing import Dict, Any, Optional, List, Callable
import queue
from contextlib import contextmanager
import functools
import asyncio

# Create a thread-local storage for correlation IDs and context
local_storage = threading.local()

class JsonFormatter(logging.Formatter):
    """Format logs as JSON for better parsing and analysis."""

    def format(self, record):
        timestamp = datetime.utcfromtimestamp(record.created).isoformat() + "Z"

        # Base log data
        log_data = {
            "timestamp": timestamp,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(), # Ensure message is formatted
        }

        # --- Add Context Fields ---
        # Order matters for readability in some viewers
        context_fields = {}
        if hasattr(local_storage, 'correlation_id'):
            context_fields["correlation_id"] = local_storage.correlation_id
        if hasattr(local_storage, 'job_id'):
            context_fields["job_id"] = local_storage.job_id
        if hasattr(local_storage, 'request_id'):
             context_fields["request_id"] = local_storage.request_id
        if hasattr(local_storage, 'user'):
             # Ensure user info is serializable
             user_info = local_storage.user
             if not isinstance(user_info, (str, int, float, bool, type(None), list, dict)):
                  user_info = str(user_info) # Convert complex objects to string
             context_fields["user"] = user_info

        # Merge context fields
        log_data.update(context_fields)

        # --- Add Caller Info ---
        caller_info = {
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        log_data.update(caller_info)

        # --- Add Process/Thread Info ---
        process_info = {
            "process_id": record.process,
            "thread_id": record.thread,
            "host": socket.gethostname(),
        }
        log_data.update(process_info)

        # --- Add Exception Info ---
        if record.exc_info:
            exc_type, exc_value, exc_traceback = record.exc_info
            exception_info = {
                "type": exc_type.__name__ if exc_type else "Unknown",
                "message": str(exc_value) if exc_value else "",
                "traceback": self.formatException(record.exc_info) if exc_traceback else None
            }
            log_data["exception"] = exception_info

        if record.stack_info:
            log_data["stack_info"] = record.stack_info

        # --- Add Extra Attributes ---
        # Get 'extra' data passed to the logging call
        # --- MODIFIED: Check for 'function_args' instead of 'args' ---
        extra_data = {}
        # Iterate over record attributes that are not standard or already handled
        standard_attrs = set(logging.LogRecord('', '', '', '', '', '', '', '').__dict__.keys()) | {'message', 'asctime', 'relativeCreated', 'exc_text', 'stack_info'} | set(log_data.keys())
        for key, value in record.__dict__.items():
            if key not in standard_attrs:
                extra_data[key] = value

        # Add the renamed function arguments if present in extra_data
        if 'function_args' in extra_data:
             log_data['function_args'] = extra_data.pop('function_args') # Move it to log_data
        if 'result' in extra_data:
             log_data['result'] = extra_data.pop('result') # Move result too

        # Merge remaining extra data, ensuring serializability
        if extra_data:
            for key, value in extra_data.items():
                if key not in log_data:
                    try:
                        json.dumps({key: value}) # Test serialization
                        log_data[key] = value
                    except TypeError:
                        log_data[key] = f"[Unserializable Extra: {type(value).__name__}] {str(value)[:100]}"
        # --- END MODIFIED ---

        # Add thread-local context dictionary items
        if hasattr(local_storage, 'context') and local_storage.context:
            for key, value in local_storage.context.items():
                if key not in log_data:
                     try:
                        json.dumps({key: value})
                        log_data[key] = value
                     except TypeError:
                        log_data[key] = f"[Unserializable Context: {type(value).__name__}] {str(value)[:100]}"

        try:
            return json.dumps(log_data, default=str) # Use default=str as fallback for non-serializable types
        except Exception as dump_err:
            # Fallback if JSON dumping fails completely
            error_log = {
                 "timestamp": timestamp,
                 "level": "ERROR",
                 "logger": "logging.JsonFormatter",
                 "message": "Failed to serialize log record to JSON.",
                 "original_logger": record.name,
                 "original_level": record.levelname,
                 "error": str(dump_err),
                 "record_preview": str(record.__dict__)[:500]
            }
            return json.dumps(error_log)


class ContextAdapter(logging.LoggerAdapter):
    """Adapter that adds context to log records. (DEPRECATED - formatter now handles context)"""
    def process(self, msg, kwargs):
        if kwargs:
             kwargs.setdefault('extra', {})
             if 'stacklevel' not in kwargs:
                 kwargs['stacklevel'] = 3
        return msg, kwargs


def set_correlation_id(correlation_id=None):
    """Set a correlation ID for the current thread."""
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())
    local_storage.correlation_id = correlation_id
    return correlation_id


def get_correlation_id():
    """Get the current correlation ID."""
    return getattr(local_storage, 'correlation_id', None)


def set_request_id(request_id=None):
    """Set a request ID for the current thread."""
    if request_id is None:
        request_id = str(uuid.uuid4())
    local_storage.request_id = request_id
    return request_id


def get_request_id():
    """Get the current request ID."""
    return getattr(local_storage, 'request_id', None)


def set_job_id(job_id):
    """Set a job ID for the current thread."""
    local_storage.job_id = job_id
    return job_id


def get_job_id():
    """Get the current job ID."""
    return getattr(local_storage, 'job_id', None)


def set_user(user):
    """Set user information for the current thread."""
    user_info = {}
    if isinstance(user, dict):
        user_info = user.copy() # Avoid modifying original dict
    elif hasattr(user, 'username'):
        user_info['username'] = user.username
        user_info['id'] = getattr(user, 'id', None)
    else:
        user_info['username'] = str(user)

    # Ensure serializability
    serializable_user_info = {}
    for k, v in user_info.items():
        try:
            json.dumps({k: v})
            serializable_user_info[k] = v
        except TypeError:
            serializable_user_info[k] = str(v)

    local_storage.user = serializable_user_info
    return local_storage.user


def get_user():
    """Get the current user information."""
    return getattr(local_storage, 'user', None)


def set_log_context(context_dict):
    """Add or update context data to logs for the current thread."""
    if not hasattr(local_storage, 'context'):
        local_storage.context = {}
    if isinstance(context_dict, dict):
        local_storage.context.update(context_dict)


def clear_log_context(keys: Optional[List[str]] = None):
    """Clear specific or all log context for the current thread."""
    if hasattr(local_storage, 'context'):
        if keys:
            for key in keys:
                local_storage.context.pop(key, None)
        else:
            local_storage.context = {}


def get_log_context():
    """Get the current log context."""
    return getattr(local_storage, 'context', {}).copy()


def clear_all_context():
    """Clear all context data for the current thread."""
    # Iterate through known attributes and remove them
    for attr in ['correlation_id', 'request_id', 'job_id', 'user', 'context', 'performance_stats']:
        if hasattr(local_storage, attr):
            try:
                delattr(local_storage, attr)
            except AttributeError:
                pass # Should not happen with hasattr check, but belt-and-suspenders


# Global variable to hold the queue listener instance
_queue_listener: Optional[QueueListener] = None

def get_logger(name):
    """Get a logger with the specified name."""
    logger = logging.getLogger(name)
    return logger # Return the raw logger


def setup_logging(log_level=None, log_to_file=True, log_dir="/data/logs",
                  log_format="json", async_logging=True,
                  llm_trace_log_file="llm_api_trace.log"):
    """
    Setup application logging.
    (Setup logic remains the same as provided previously)
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
                # Use absolute path
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
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S,%f' # Add milliseconds
        )

    handlers = []

    # Create console handler (always add this one)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter) # Use JSON formatter for console too
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
            llm_trace_formatter = JsonFormatter()
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


# Timer utility for performance logging
class LogTimer:
    def __init__(self, logger_instance, description="Operation", level=logging.DEBUG,
                 include_in_stats=False, stats_name=None):
        self.logger = logger_instance
        self.description = description
        self.level = level
        self.start_time = None
        self.include_in_stats = include_in_stats
        self.stats_name = stats_name or description.replace(" ", "_").lower()

    def __enter__(self):
        self.start_time = time.monotonic()
        self.logger.log(self.level, f"Starting: {self.description}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.monotonic() - self.start_time

        if self.include_in_stats:
            if not hasattr(local_storage, 'performance_stats'):
                local_storage.performance_stats = {}
            if self.stats_name not in local_storage.performance_stats:
                local_storage.performance_stats[self.stats_name] = { 'count': 0, 'total_time': 0.0, 'min_time': float('inf'), 'max_time': 0.0 }
            stats = local_storage.performance_stats[self.stats_name]
            stats['count'] += 1
            stats['total_time'] += elapsed
            stats['min_time'] = min(stats['min_time'], elapsed)
            stats['max_time'] = max(stats['max_time'], elapsed)

        log_extra = {"duration_seconds": round(elapsed, 3)}
        if exc_type:
            log_extra["error"] = str(exc_val) if exc_val else exc_type.__name__
            self.logger.error(
                f"Failed: {self.description} after {elapsed:.3f}s",
                exc_info=(exc_type, exc_val, exc_tb) if exc_tb else False,
                extra=log_extra
            )
        else:
            self.logger.log(
                self.level,
                f"Completed: {self.description} in {elapsed:.3f}s",
                extra=log_extra
            )


def get_performance_stats():
    """Get the current performance statistics."""
    return getattr(local_storage, 'performance_stats', {}).copy()


def clear_performance_stats():
    """Clear the performance statistics."""
    if hasattr(local_storage, 'performance_stats'):
        delattr(local_storage, 'performance_stats')


@contextmanager
def log_duration(logger_instance, description="Operation", level=logging.DEBUG, include_in_stats=False):
    """Context manager for logging the duration of a code block using LogTimer."""
    timer = LogTimer(logger_instance, description, level, include_in_stats)
    with timer:
        yield


def log_function_call(logger_instance, level=logging.DEBUG, include_args=True,
                      include_result=False, arg_char_limit=100, result_char_limit=100,
                      include_in_stats=False):
    """
    Decorator to log function calls with parameters and return value.
    """
    def decorator(func):
        logger_instance.debug(f"Applying @log_function_call decorator to function: {func.__module__}.{func.__name__}")

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            module_name = func.__module__
            full_func_name = f"{module_name}.{func_name}"
            timer_name = full_func_name

            args_repr = ""
            if include_args:
                try:
                    sig = inspect.signature(func)
                    bound_args = sig.bind_partial(*args, **kwargs)
                    bound_args.apply_defaults()
                    arg_items = []
                    for name, value in bound_args.arguments.items():
                        try: value_repr = repr(value)
                        except Exception: value_repr = "[repr error]"
                        if len(value_repr) > arg_char_limit:
                             type_name = type(value).__name__
                             value_repr = f"<{type_name} object>" if type_name != 'object' else value_repr[:arg_char_limit-3] + "..."
                        arg_items.append(f"{name}={value_repr}")
                    args_repr = ", ".join(arg_items)
                except Exception as sig_err:
                    logger_instance.warning(f"Could not format arguments for {full_func_name}: {sig_err}")
                    args_repr = "[Arg formatting error]"

            # --- FIX: Rename 'args' key in extra dictionary ---
            log_extra_start = {"function_args": args_repr} if include_args else {}
            # --- END FIX ---
            logger_instance.log(level, f"Calling: {full_func_name}", extra=log_extra_start)

            start_time = time.monotonic()
            try:
                result = func(*args, **kwargs)
                elapsed = time.monotonic() - start_time

                if include_in_stats:
                    if not hasattr(local_storage, 'performance_stats'): local_storage.performance_stats = {}
                    if timer_name not in local_storage.performance_stats: local_storage.performance_stats[timer_name] = {'count': 0, 'total_time': 0.0, 'min_time': float('inf'), 'max_time': 0.0}
                    stats = local_storage.performance_stats[timer_name]
                    stats['count'] += 1; stats['total_time'] += elapsed; stats['min_time'] = min(stats['min_time'], elapsed); stats['max_time'] = max(stats['max_time'], elapsed)

                log_extra_end = {"duration_seconds": round(elapsed, 3)}
                result_repr = ""
                if include_result:
                    try:
                        result_repr = repr(result)
                        if len(result_repr) > result_char_limit:
                             type_name = type(result).__name__
                             result_repr = f"<{type_name} object>" if type_name != 'object' else result_repr[:result_char_limit-3] + "..."
                    except Exception: result_repr = "[repr error]"
                    log_extra_end["result"] = result_repr

                logger_instance.log(
                    level,
                    f"Completed: {full_func_name} in {elapsed:.3f}s",
                    extra=log_extra_end
                )
                return result

            except Exception as e:
                elapsed = time.monotonic() - start_time
                logger_instance.error(
                    f"Failed: {full_func_name} after {elapsed:.3f}s",
                    exc_info=True,
                    extra={"duration_seconds": round(elapsed, 3), "error": str(e)}
                )
                raise

        is_async = asyncio.iscoroutinefunction(func)
        logger_instance.debug(f"Function {func.__module__}.{func.__name__} is async: {is_async}")
        if is_async:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                func_name = func.__name__
                module_name = func.__module__
                full_func_name = f"{module_name}.{func_name}"
                timer_name = full_func_name

                args_repr = ""
                if include_args:
                    try:
                        sig = inspect.signature(func)
                        bound_args = sig.bind_partial(*args, **kwargs)
                        bound_args.apply_defaults()
                        arg_items = []
                        for name, value in bound_args.arguments.items():
                            try: value_repr = repr(value)
                            except Exception: value_repr = "[repr error]"
                            if len(value_repr) > arg_char_limit:
                                type_name = type(value).__name__
                                value_repr = f"<{type_name} object>" if type_name != 'object' else value_repr[:arg_char_limit-3] + "..."
                            arg_items.append(f"{name}={value_repr}")
                        args_repr = ", ".join(arg_items)
                    except Exception as sig_err:
                        logger_instance.warning(f"Could not format arguments for async {full_func_name}: {sig_err}")
                        args_repr = "[Arg formatting error]"

                # --- FIX: Rename 'args' key in extra dictionary ---
                log_extra_start = {"function_args": args_repr} if include_args else {}
                # --- END FIX ---
                logger_instance.log(level, f"Calling async: {full_func_name}", extra=log_extra_start)

                start_time = time.monotonic()
                try:
                    result = await func(*args, **kwargs) # Await the async function
                    elapsed = time.monotonic() - start_time

                    if include_in_stats:
                        if not hasattr(local_storage, 'performance_stats'): local_storage.performance_stats = {}
                        if timer_name not in local_storage.performance_stats: local_storage.performance_stats[timer_name] = {'count': 0, 'total_time': 0.0, 'min_time': float('inf'), 'max_time': 0.0}
                        stats = local_storage.performance_stats[timer_name]
                        stats['count'] += 1; stats['total_time'] += elapsed; stats['min_time'] = min(stats['min_time'], elapsed); stats['max_time'] = max(stats['max_time'], elapsed)

                    log_extra_end = {"duration_seconds": round(elapsed, 3)}
                    result_repr = ""
                    if include_result:
                        try:
                            result_repr = repr(result)
                            if len(result_repr) > result_char_limit:
                                type_name = type(result).__name__
                                result_repr = f"<{type_name} object>" if type_name != 'object' else result_repr[:result_char_limit-3] + "..."
                        except Exception: result_repr = "[repr error]"
                        log_extra_end["result"] = result_repr

                    logger_instance.log(
                        level,
                        f"Completed async: {full_func_name} in {elapsed:.3f}s",
                        extra=log_extra_end
                    )
                    return result

                except Exception as e:
                    elapsed = time.monotonic() - start_time
                    logger_instance.error(
                        f"Failed async: {full_func_name} after {elapsed:.3f}s",
                        exc_info=True,
                        extra={"duration_seconds": round(elapsed, 3), "error": str(e)}
                    )
                    raise
            return async_wrapper
        else:
            return wrapper
    return decorator