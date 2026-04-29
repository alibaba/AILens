"""Access logging middleware for FastAPI."""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from opentelemetry import trace
from starlette.middleware.base import BaseHTTPMiddleware

from ..logging import get_access_logger


class AccessLogMiddleware(BaseHTTPMiddleware):
    """Middleware to log all HTTP requests and responses."""

    def __init__(self, app, exclude_paths=None):
        """Initialize access log middleware.

        Args:
            app: FastAPI application instance
            exclude_paths: List of paths to exclude from logging (e.g., health checks)
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/health", "/metrics", "/favicon.ico"]
        self.logger = get_access_logger()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process HTTP request and log access information."""
        # Skip logging for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Record start time
        start_time = time.time()

        # Get trace context
        span = trace.get_current_span()
        trace_id = None
        span_id = None

        if span and span.context.trace_id:
            trace_id = f"{span.context.trace_id:032x}"
            span_id = f"{span.context.span_id:016x}"

        # Extract request info
        method = request.method
        path = str(request.url.path)
        query_params = str(request.url.query) if request.url.query else None
        user_agent = request.headers.get("user-agent")
        remote_addr = getattr(request.client, "host", None) if request.client else None
        forwarded_for = request.headers.get("x-forwarded-for")
        content_length = request.headers.get("content-length")

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = round((time.time() - start_time) * 1000, 2)

        # Get response size
        response_size = None
        if hasattr(response, "headers") and "content-length" in response.headers:
            response_size = int(response.headers["content-length"])

        # Log access information
        self.logger.info(
            "request_completed",
            extra={
                "request_id": request_id,
                "method": method,
                "path": path,
                "query_params": query_params,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "user_agent": user_agent,
                "remote_addr": remote_addr,
                "forwarded_for": forwarded_for,
                "request_size": int(content_length) if content_length else None,
                "response_size": response_size,
                "trace_id": trace_id,
                "span_id": span_id,
            },
        )

        # Add request ID to response headers for correlation
        response.headers["X-Request-ID"] = request_id

        return response
