import time
import functools
import uuid
import json
import traceback
from typing import Dict, Any, Optional, Callable
from contextvars import ContextVar

from core.logging_config import (
    get_logger, set_correlation_id, get_correlation_id, 
    set_log_context, LogTimer, log_function_call
)

# Configure logger
logger = get_logger("vendor_classification.log_utils")

# Define some performance metric tracking
api_request_metrics = ContextVar("api_request_metrics", default={})
db_query_metrics = ContextVar("db_query_metrics", default={})

def log_api_request(service_name: str):
    """
    Decorator to log API requests with detailed metrics.
    
    Args:
        service_name: Name of the external service being called
    
    Returns:
        Decorator function
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate request ID if none exists
            request_id = str(uuid.uuid4())
            correlation_id = get_correlation_id() or request_id
            
            # Extract URL from args or kwargs if possible
            url = None
            method = "UNKNOWN"
            if kwargs.get("url"):
                url = kwargs["url"]
            elif len(args) > 0 and isinstance(args[0], str):
                url = args[0]
            
            if hasattr(func, "__name__"):
                method = func.__name__
                
            # Get any request data while being careful about sensitive info
            request_data = {}
            if "json" in kwargs:
                request_data = kwargs["json"]
                # Redact sensitive data
                if isinstance(request_data, dict):
                    if "api_key" in request_data:
                        request_data["api_key"] = "[REDACTED]"
                    if "password" in request_data:
                        request_data["password"] = "[REDACTED]"
            
            # Log start of API call with safe data
            start_time = time.time()
            logger.info(
                f"API request to {service_name} started",
                extra={
                    "service": service_name,
                    "url": url,
                    "method": method,
                    "request_id": request_id,
                    "correlation_id": correlation_id,
                    "request_data": json.dumps(request_data)[:500] if request_data else None
                }
            )
            
            try:
                # Execute the API call
                response = await func(*args, **kwargs)
                
                # Calculate duration
                duration = time.time() - start_time
                
                # Update metrics
                metrics = api_request_metrics.get()
                if service_name not in metrics:
                    metrics[service_name] = {"count": 0, "total_time": 0, "errors": 0}
                metrics[service_name]["count"] += 1
                metrics[service_name]["total_time"] += duration
                api_request_metrics.set(metrics)
                
                # Log successful response with safely truncated data
                response_data = None
                status_code = None
                
                # Handle different response types
                if hasattr(response, "status_code"):
                    status_code = response.status_code
                
                if hasattr(response, "json") and callable(response.json):
                    try:
                        response_data = response.json()
                        # Truncate for logging
                        response_data_str = json.dumps(response_data)
                        if len(response_data_str) > 1000:
                            response_data_str = response_data_str[:997] + "..."
                    except:
                        response_data_str = "[unparseable JSON]"
                elif hasattr(response, "text"):
                    response_data_str = response.text
                    if len(response_data_str) > 1000:
                        response_data_str = response_data_str[:997] + "..."
                else:
                    response_data_str = str(response)[:100]
                
                logger.info(
                    f"API request to {service_name} completed",
                    extra={
                        "service": service_name,
                        "url": url,
                        "method": method,
                        "request_id": request_id, 
                        "correlation_id": correlation_id,
                        "duration": duration,
                        "status_code": status_code,
                        "response_snippet": response_data_str,
                        "response_size": len(response_data_str) if response_data_str else 0
                    }
                )
                
                return response
                
            except Exception as e:
                # Calculate duration for failed requests too
                duration = time.time() - start_time
                
                # Update error metrics
                metrics = api_request_metrics.get()
                if service_name not in metrics:
                    metrics[service_name] = {"count": 0, "total_time": 0, "errors": 0}
                metrics[service_name]["count"] += 1
                metrics[service_name]["total_time"] += duration
                metrics[service_name]["errors"] += 1
                api_request_metrics.set(metrics)
                
                # Log detailed error information
                logger.error(
                    f"API request to {service_name} failed",
                    exc_info=True,
                    extra={
                        "service": service_name,
                        "url": url, 
                        "method": method,
                        "request_id": request_id,
                        "correlation_id": correlation_id,
                        "duration": duration,
                        "error": str(e),
                        "traceback": traceback.format_exc()
                    }
                )
                raise
                
        return wrapper
    return decorator

def get_api_metrics() -> Dict[str, Dict[str, Any]]:
    """Get current API metrics."""
    return api_request_metrics.get()

def get_db_metrics() -> Dict[str, Dict[str, Any]]:
    """Get current database metrics."""
    return db_query_metrics.get()

def log_method(level=None, include_args=True, include_result=False):
    """
    Enhanced method logging decorator for class methods.
    Automatically adds class name to the log.
    
    Args:
        level: Log level to use
        include_args: Whether to include arguments in log
        include_result: Whether to include return value in log
        
    Returns:
        Decorator function
    """
    def decorator(method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            # Get class and method names
            class_name = self.__class__.__name__
            method_name = method.__name__
            
            # Get logger - try to use the class's logger if available
            method_logger = getattr(self, 'logger', logger)
            log_level = level or getattr(method_logger, 'level', logging.INFO)
            
            # Create a descriptive name for the operation
            operation = f"{class_name}.{method_name}"
            
            # Format arguments if requested
            args_str = ""
            if include_args:
                # Format arguments, but skip self
                arg_items = []
                for i, arg in enumerate(args):
                    # Limit string representation for large objects
                    arg_str = repr(arg)
                    if len(arg_str) > 100:
                        arg_str = arg_str[:97] + "..."
                    arg_items.append(f"arg{i+1}={arg_str}")
                
                for name, value in kwargs.items():
                    # Limit string representation for large objects
                    value_str = repr(value)
                    if len(value_str) > 100:
                        value_str = value_str[:97] + "..."
                    arg_items.append(f"{name}={value_str}")
                
                args_str = ", ".join(arg_items)
            
            # Log method entry
            if args_str:
                method_logger.log(log_level, f"Calling {operation}({args_str})")
            else:
                method_logger.log(log_level, f"Calling {operation}")
            
            # Use LogTimer for more accurate timing
            with LogTimer(method_logger, operation, level=log_level, include_in_stats=True):
                try:
                    result = method(self, *args, **kwargs)
                    
                    # Log method exit with result if requested
                    if include_result:
                        result_str = repr(result)
                        if len(result_str) > 100:
                            result_str = result_str[:97] + "..."
                        method_logger.log(log_level, f"{operation} returned: {result_str}")
                    else:
                        method_logger.log(log_level, f"{operation} completed")
                    
                    return result
                    
                except Exception as e:
                    # Log detailed error information
                    method_logger.error(
                        f"{operation} failed: {str(e)}",
                        exc_info=True,
                        extra={"error_type": type(e).__name__}
                    )
                    raise
                    
        return wrapper
    return decorator

def setup_request_context(request=None):
    """
    Set up a new request context with correlation ID and other metadata.
    
    Args:
        request: Optional request object to extract metadata from
    
    Returns:
        Generated correlation ID
    """
    correlation_id = str(uuid.uuid4())
    set_correlation_id(correlation_id)
    
    # Extract request metadata if provided
    if request:
        client_ip = None
        user_agent = None
        
        if hasattr(request, 'client') and request.client:
            client_ip = request.client.host
            
        if hasattr(request, 'headers'):
            user_agent = request.headers.get('user-agent')
            
        # Add request context
        set_log_context({
            'client_ip': client_ip,
            'user_agent': user_agent,
            'request_path': getattr(request, 'url', None)
        })
    
    return correlation_id

def log_critical_operation(operation_name: str, include_in_stats=True):
    """
    Context manager for logging critical operations with mandatory timing.
    
    Args:
        operation_name: Name of the operation being performed
        include_in_stats: Whether to include timing in performance stats
        
    Usage:
        with log_critical_operation("Database backup"):
            # critical code here
    """
    return LogTimer(logger, operation_name, level=logger.info, include_in_stats=include_in_stats)