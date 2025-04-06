
# app/middleware/logging_middleware.py
import time
import json
import uuid
import logging # <<< ADDED IMPORT
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

# Import context functions from the new module
from core.log_context import (
    set_request_id, get_request_id, set_correlation_id, get_correlation_id,
    set_user, set_log_context, clear_all_context
)
# Import logger and log helpers
from core.logging_config import get_logger
from utils.log_utils import log_duration

# Configure logger for this module
logger = get_logger("vendor_classification.middleware")
# --- ADDED: Log confirmation ---
logger.debug("Successfully imported standard logging module.")
# --- END ADDED ---

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests and responses."""

    async def dispatch(self, request: Request, call_next):
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        # Set request ID and correlation ID
        set_request_id(request_id)
        correlation_id = request.headers.get("X-Correlation-ID")
        if correlation_id:
            set_correlation_id(correlation_id)
        else:
            set_correlation_id(request_id)  # Use request_id as correlation_id if none provided

        # Add context data
        set_log_context({
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "path": request.url.path,
            "method": request.method,
        })

        # Log request
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "query_params": dict(request.query_params),
                "path_params": request.path_params,
                "headers": { k.lower(): v for k, v in request.headers.items() }
            }
        )

        # Process the request and measure time
        start_time = time.time()
        try:
            response = await call_next(request)

            # Log response
            process_time = time.time() - start_time
            logger.info(
                f"Request completed: {request.method} {request.url.path}",
                extra={
                    "status_code": response.status_code,
                    "duration": process_time,
                    "response_headers": {
                        k.lower(): v for k, v in response.headers.items()
                    }
                }
            )

            # Add the request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as exc:
            # Log any unhandled exceptions
            process_time = time.time() - start_time
            logger.exception(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    "duration": process_time,
                    "error": str(exc)
                }
            )
            raise
        finally:
            # Clear context data to prevent leaks between requests
            clear_all_context()


class RequestBodyLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log request and response bodies.
    Note: Use only in development/debugging.
    """

    def __init__(
        self,
        app: ASGIApp,
        exclude_paths: list = None,
        max_body_size: int = 10000
    ):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/health", "/metrics", "/static"]
        self.max_body_size = max_body_size

    async def dispatch(self, request: Request, call_next):
        # Skip excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # Get request ID
        request_id = get_request_id() or str(uuid.uuid4())

        # Clone the request to access the body
        copied_body = await self._get_request_body(request)

        if copied_body:
            body_str = self._get_body_str(copied_body)
            logger.debug(
                f"Request body: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "request_body": body_str
                }
            )

        # Process the request
        response = await call_next(request)

        # Try to get response body for certain content types
        if response.status_code != 204 and hasattr(response, "body"):
            body = response.body
            if body:
                body_str = self._get_body_str(body)
                logger.debug(
                    f"Response body: {request.method} {request.url.path}",
                    extra={
                        "request_id": request_id,
                        "response_body": body_str,
                        "status_code": response.status_code
                    }
                )

        return response

    def _get_body_str(self, body: bytes) -> str:
        """Convert body bytes to string, truncating if needed."""
        if len(body) > self.max_body_size:
            return f"{body[:self.max_body_size].decode('utf-8', errors='replace')}... [truncated]"

        try:
            body_str = body.decode('utf-8')
            # Try to pretty-print JSON
            try:
                json_body = json.loads(body_str)
                body_str = json.dumps(json_body, indent=2)
            except:
                pass
            return body_str
        except:
            return f"[binary data, length: {len(body)}]"

    async def _get_request_body(self, request: Request) -> bytes:
        """Get and restore the request body."""
        body = await request.body()
        # Reset the request body
        async def receive():
            return {"type": "http.request", "body": body}
        request._receive = receive
        return body


async def log_request_middleware(request: Request, call_next) -> Response:
    """
    Alternative logging middleware function that can be used with middleware decorator.
    """
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    set_request_id(request_id)
    correlation_id = request.headers.get("X-Correlation-ID")
    if correlation_id:
        set_correlation_id(correlation_id)
    else:
        set_correlation_id(request_id)

    # Add context data
    set_log_context({
        "client_ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "path": request.url.path,
        "method": request.method,
    })

    # Log request
    logger.info(
        f"Request started: {request.method} {request.url.path}",
        extra={
            "request_id": request_id,
            "query_params": dict(request.query_params),
            "path_params": request.path_params,
        }
    )

    try:
        with log_duration(logger, f"Request {request.method} {request.url.path}",
                         level=logging.INFO, include_in_stats=True): # Use INFO level for request duration
            # Process the request
            response = await call_next(request)

        # Log response summary
        logger.info(
            f"Request completed: {request.method} {request.url.path}",
            extra={
                "status_code": response.status_code,
            }
        )

        # Add the request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response

    except Exception as e:
        logger.exception(f"Request failed: {request.method} {request.url.path}")
        raise
    finally:
        # Clear context data to prevent leaks between requests
        clear_all_context()