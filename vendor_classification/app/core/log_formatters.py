
# app/core/log_formatters.py
import logging
import json
import socket
from datetime import datetime
from typing import Dict, Any

# Import context functions from the new module
from .log_context import get_correlation_id, get_job_id, get_request_id, get_user, get_log_context

class JsonFormatter(logging.Formatter):
    """Format logs as JSON for better parsing and analysis."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.utcfromtimestamp(record.created).isoformat() + "Z"

        # Base log data
        log_data: Dict[str, Any] = {
            "timestamp": timestamp,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(), # Ensure message is formatted
        }

        # --- Add Context Fields ---
        context_fields = {}
        correlation_id = get_correlation_id()
        if correlation_id:
            context_fields["correlation_id"] = correlation_id
        job_id = get_job_id()
        if job_id:
            context_fields["job_id"] = job_id
        request_id = get_request_id()
        if request_id:
             context_fields["request_id"] = request_id
        user_info = get_user()
        if user_info:
             # User info should already be serializable from set_user
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
        extra_data = {}
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

        # Add thread-local context dictionary items
        log_context_dict = get_log_context()
        if log_context_dict:
            for key, value in log_context_dict.items():
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