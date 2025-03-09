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
        start_time = time.time()
        response = self.get_response(request)
        duration = time.time() - start_time

        # Prepare log data with tenant context
        tenant = None
        if hasattr(request, 'context') and request.context.get('tenant'): 
            tenant = request.context['tenant']

        log_data = {
            'timestamp': timezone.now().isoformat(),
            'method': request.method,
            'path': request.path,
            'user': str(request.user) if request.user.is_authenticated else 'anonymous',
            # Provide a default fallback if tenant is None:
            'tenant': tenant.tenant_name if tenant else 'unknown',
            'status_code': response.status_code,
            'duration': round(duration * 1000, 2),
            'content_type': response.get('Content-Type', ''),
        }

        # Add query params safely, ignoring sensitive keys
        params = {
            k: v for k, v in request.GET.items()
            if k.lower() not in ('password', 'token', 'auth', 'key')
        }
        if params:
            log_data['query_params'] = params

        # Our actual log message
        log_message = (
            f"{log_data['method']} {log_data['path']} "
            f"- {log_data['status_code']} in {log_data['duration']}ms"
        )
        
        # IMPORTANT: include 'tenant' key at the top level,
        # matching the format {tenant} in your logging config.
        extra = {
            'tenant': log_data['tenant'],
            'log_data': log_data
        }

        if response.status_code >= 500:
            request_logger.error(log_message, extra=extra)
        elif response.status_code >= 400:
            request_logger.warning(log_message, extra=extra)
        else:
            request_logger.info(log_message, extra=extra)

        return response