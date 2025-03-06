# core/middleware/logging_middleware.py
import json
import logging
import time
from django.utils import timezone

request_logger = logging.getLogger('apps.requests')

class LoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Log the request details
        start_time = time.time()
        
        # Process the request
        response = self.get_response(request)
        
        # Calculate request duration
        duration = time.time() - start_time
        
        # Prepare logging information
        log_data = {
            'timestamp': timezone.now().isoformat(),
            'method': request.method,
            'path': request.path,
            'user': str(request.user) if request.user.is_authenticated else 'anonymous',
            'status_code': response.status_code,
            'duration': round(duration * 1000, 2),  # Convert to milliseconds
            'content_type': response.get('Content-Type', ''),
        }
        
        # Add query params without sensitive data
        params = {}
        for key, value in request.GET.items():
            if key.lower() not in ('password', 'token', 'auth', 'key'):
                params[key] = value
        if params:
            log_data['query_params'] = params
        
        # Log request details
        log_message = f"{log_data['method']} {log_data['path']} - {log_data['status_code']} in {log_data['duration']}ms"
        
        # Use appropriate log level based on response status
        if response.status_code >= 500:
            request_logger.error(log_message, extra={'log_data': log_data})
        elif response.status_code >= 400:
            request_logger.warning(log_message, extra={'log_data': log_data})
        else:
            request_logger.info(log_message, extra={'log_data': log_data})
        
        return response