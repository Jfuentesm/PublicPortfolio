
# app/utils/log_utils.py
import time
import functools
import uuid
import json
import traceback
import logging # Import standard logging
import inspect # Import inspect
import asyncio # Import asyncio
from typing import Dict, Any, Optional, Callable
from contextlib import contextmanager

# Import context functions from the new module
from core.log_context import (
    local_storage, # Need local_storage for LogTimer stats
    get_correlation_id,
    set_correlation_id, # <<< ADDED IMPORT
    set_log_context,
    get_performance_stats,
    clear_performance_stats
)

# Configure logger for this utility module itself
logger = logging.getLogger("vendor_classification.log_utils")
# --- ADDED: Log confirmation ---
logger.debug("Successfully imported set_correlation_id from core.log_context.")
# --- END ADDED ---

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
        if self.start_time is None: # Avoid error if __enter__ failed
            return
        elapsed = time.monotonic() - self.start_time

        if self.include_in_stats:
            # Use the imported local_storage
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
    Handles both sync and async functions.
    """
    def decorator(func):
        logger_instance.debug(f"Applying @log_function_call decorator to function: {func.__module__}.{func.__name__}")

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
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

            log_extra_start = {"function_args": args_repr} if include_args else {}
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

            log_extra_start = {"function_args": args_repr} if include_args else {}
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

        if asyncio.iscoroutinefunction(func):
            logger_instance.debug(f"Function {func.__module__}.{func.__name__} is async, using async_wrapper.")
            return async_wrapper
        else:
            logger_instance.debug(f"Function {func.__module__}.{func.__name__} is sync, using sync_wrapper.")
            return sync_wrapper
    return decorator

# --- Other utility functions from the original log_utils.py ---

def log_api_request(service_name: str):
    """
    Decorator to log API requests with detailed metrics.
    (Implementation remains the same as provided in the original log_utils.py)
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            request_id = str(uuid.uuid4())
            correlation_id = get_correlation_id() or request_id
            url = kwargs.get("url") or (args[0] if len(args) > 0 and isinstance(args[0], str) else None)
            method = func.__name__
            request_data = kwargs.get("json", {})
            if isinstance(request_data, dict):
                if "api_key" in request_data: request_data["api_key"] = "[REDACTED]"
                if "password" in request_data: request_data["password"] = "[REDACTED]"

            start_time = time.time()
            logger.info(
                f"API request to {service_name} started",
                extra={ "service": service_name, "url": url, "method": method, "request_id": request_id, "correlation_id": correlation_id, "request_data": json.dumps(request_data)[:500] if request_data else None }
            )
            try:
                response = await func(*args, **kwargs)
                duration = time.time() - start_time
                # Update metrics (simplified example)
                set_log_context({f"{service_name}_api_call_count": 1, f"{service_name}_api_call_time": duration})

                status_code = getattr(response, 'status_code', None)
                response_data_str = "[Response data omitted]" # Simplified logging
                logger.info(
                    f"API request to {service_name} completed",
                    extra={ "service": service_name, "url": url, "method": method, "request_id": request_id, "correlation_id": correlation_id, "duration": duration, "status_code": status_code, "response_snippet": response_data_str }
                )
                return response
            except Exception as e:
                duration = time.time() - start_time
                set_log_context({f"{service_name}_api_error_count": 1})
                logger.error(
                    f"API request to {service_name} failed", exc_info=True,
                    extra={ "service": service_name, "url": url, "method": method, "request_id": request_id, "correlation_id": correlation_id, "duration": duration, "error": str(e) }
                )
                raise
        return wrapper
    return decorator

def log_method(level=logging.DEBUG, include_args=True, include_result=False):
    """
    Enhanced method logging decorator for class methods.
    (Implementation remains the same as provided in the original log_utils.py)
    """
    def decorator(method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            class_name = self.__class__.__name__
            method_name = method.__name__
            method_logger = getattr(self, 'logger', logger)
            log_level = level or getattr(method_logger, 'level', logging.DEBUG)
            operation = f"{class_name}.{method_name}"
            args_str = ""
            if include_args:
                arg_items = []
                for i, arg in enumerate(args):
                    arg_str = repr(arg); arg_str = arg_str[:97] + "..." if len(arg_str) > 100 else arg_str
                    arg_items.append(f"arg{i+1}={arg_str}")
                for name, value in kwargs.items():
                    value_str = repr(value); value_str = value_str[:97] + "..." if len(value_str) > 100 else value_str
                    arg_items.append(f"{name}={value_str}")
                args_str = ", ".join(arg_items)

            log_msg = f"Calling {operation}" + (f"({args_str})" if args_str else "")
            method_logger.log(log_level, log_msg)

            with LogTimer(method_logger, operation, level=log_level, include_in_stats=True):
                try:
                    result = method(self, *args, **kwargs)
                    result_str = ""
                    if include_result:
                        result_str = repr(result); result_str = result_str[:97] + "..." if len(result_str) > 100 else result_str
                        method_logger.log(log_level, f"{operation} returned: {result_str}")
                    else:
                        method_logger.log(log_level, f"{operation} completed")
                    return result
                except Exception as e:
                    method_logger.error(f"{operation} failed: {str(e)}", exc_info=True, extra={"error_type": type(e).__name__})
                    raise
        return wrapper
    return decorator

def setup_request_context(request=None):
    """
    Set up a new request context with correlation ID and other metadata.
    (Implementation remains the same as provided in the original log_utils.py)
    """
    correlation_id = str(uuid.uuid4())
    set_correlation_id(correlation_id) # Use the imported function
    if request:
        client_ip = request.client.host if hasattr(request, 'client') and request.client else None
        user_agent = request.headers.get('user-agent') if hasattr(request, 'headers') else None
        set_log_context({ 'client_ip': client_ip, 'user_agent': user_agent, 'request_path': getattr(request, 'url', None) })
    return correlation_id

def log_critical_operation(operation_name: str, include_in_stats=True):
    """
    Context manager for logging critical operations with mandatory timing.
    (Implementation remains the same as provided in the original log_utils.py)
    """
    return LogTimer(logger, operation_name, level=logging.INFO, include_in_stats=include_in_stats)