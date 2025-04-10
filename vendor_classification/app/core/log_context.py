
# app/core/log_context.py
import threading
import uuid
import json
from typing import Optional, List, Dict, Any

# Create a thread-local storage for correlation IDs and context
local_storage = threading.local()

def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    """Set a correlation ID for the current thread/context."""
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())
    local_storage.correlation_id = correlation_id
    return correlation_id

def get_correlation_id() -> Optional[str]:
    """Get the current correlation ID."""
    return getattr(local_storage, 'correlation_id', None)

def set_request_id(request_id: Optional[str] = None) -> str:
    """Set a request ID for the current thread/context."""
    if request_id is None:
        request_id = str(uuid.uuid4())
    local_storage.request_id = request_id
    return request_id

def get_request_id() -> Optional[str]:
    """Get the current request ID."""
    return getattr(local_storage, 'request_id', None)

def set_job_id(job_id: str) -> str:
    """Set a job ID for the current thread/context."""
    local_storage.job_id = job_id
    return job_id

def get_job_id() -> Optional[str]:
    """Get the current job ID."""
    return getattr(local_storage, 'job_id', None)

def set_user(user: Any) -> Dict[str, Any]:
    """Set user information for the current thread/context, ensuring serializability."""
    user_info = {}
    if isinstance(user, dict):
        user_info = user.copy() # Avoid modifying original dict
    elif hasattr(user, 'username'):
        user_info['username'] = user.username
        user_info['id'] = getattr(user, 'id', None)
    elif user is not None:
        user_info['username'] = str(user)
    else:
        user_info = {'username': 'anonymous'} # Default for None

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

def get_user() -> Optional[Dict[str, Any]]:
    """Get the current user information."""
    return getattr(local_storage, 'user', None)

def set_log_context(context_dict: Dict[str, Any]):
    """Add or update context data to logs for the current thread/context."""
    if not hasattr(local_storage, 'context'):
        local_storage.context = {}
    if isinstance(context_dict, dict):
        local_storage.context.update(context_dict)

def get_log_context() -> Dict[str, Any]:
    """Get the current log context dictionary."""
    return getattr(local_storage, 'context', {}).copy()

def clear_log_context(keys: Optional[List[str]] = None):
    """Clear specific or all log context for the current thread/context."""
    if hasattr(local_storage, 'context'):
        if keys:
            for key in keys:
                local_storage.context.pop(key, None)
        else:
            local_storage.context = {}

def set_performance_stats(stats_dict: Dict[str, Any]):
    """Set performance stats data for the current thread/context."""
    local_storage.performance_stats = stats_dict

def get_performance_stats() -> Dict[str, Any]:
    """Get the current performance statistics."""
    return getattr(local_storage, 'performance_stats', {}).copy()

def update_performance_stat(stat_name: str, value: float):
    """Update a single performance stat (e.g., duration)."""
    if not hasattr(local_storage, 'performance_stats'):
        local_storage.performance_stats = {}
    # Simple update, LogTimer in log_utils provides more detail
    local_storage.performance_stats[stat_name] = value

def clear_performance_stats():
    """Clear the performance statistics."""
    if hasattr(local_storage, 'performance_stats'):
        delattr(local_storage, 'performance_stats')

def clear_all_context():
    """Clear all context data (IDs, user, context dict, stats) for the current thread/context."""
    # Iterate through known attributes and remove them
    for attr in ['correlation_id', 'request_id', 'job_id', 'user', 'context', 'performance_stats']:
        if hasattr(local_storage, attr):
            try:
                delattr(local_storage, attr)
            except AttributeError:
                pass # Should not happen with hasattr check, but belt-and-suspenders