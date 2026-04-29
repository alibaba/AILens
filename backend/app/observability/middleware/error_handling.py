"""Error handling middleware for FastAPI."""

import traceback
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from opentelemetry import trace
from starlette.middleware.base import BaseHTTPMiddleware

from ..logging import get_error_logger


def classify_error_severity(exception: Exception) -> str:
    """Classify error severity based on exception type."""
    error_name = type(exception).__name__

    # Critical errors
    if error_name in {"SystemExit", "KeyboardInterrupt", "MemoryError"}:
        return "critical"

    # High severity errors
    if error_name in {"DatabaseError", "ConnectionError", "TimeoutError"}:
        return "high"

    # Medium severity errors
    if error_name in {"ValueError", "TypeError", "AttributeError", "KeyError"}:
        return "medium"

    # Low severity errors
    if error_name in {"ValidationError", "PermissionError", "FileNotFoundError"}:
        return "low"

    # Default to medium for unknown errors
    return "medium"


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware to handle and log unhandled exceptions."""

    def __init__(self, app, debug: bool = False):
        """Initialize error handling middleware.

        Args:
            app: FastAPI application instance
            debug: Whether to include detailed error info in responses
        """
        super().__init__(app)
        self.debug = debug
        self.logger = get_error_logger()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and handle any unhandled exceptions."""
        try:
            return await call_next(request)
        except Exception as exc:
            return await self._handle_exception(request, exc)

    async def _handle_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """Handle and log an unhandled exception."""
        # Get request context
        request_id = getattr(request.state, "request_id", "unknown")
        method = request.method
        path = str(request.url.path)
        query_params = str(request.url.query) if request.url.query else None
        user_agent = request.headers.get("user-agent")
        remote_addr = getattr(request.client, "host", None) if request.client else None

        # Get trace context
        span = trace.get_current_span()
        trace_id = None
        span_id = None

        if span and span.context.trace_id:
            trace_id = f"{span.context.trace_id:032x}"
            span_id = f"{span.context.span_id:016x}"

        # Classify error
        error_type = type(exc).__name__
        error_message = str(exc)
        severity = classify_error_severity(exc)
        stack_trace = traceback.format_exc()

        # Generate error code based on exception type
        error_code = f"ERR_{error_type.upper()}"

        # Log the error
        self.logger.error(
            "unhandled_exception",
            extra={
                "request_id": request_id,
                "error_type": error_type,
                "error_code": error_code,
                "message": error_message,
                "stack_trace": stack_trace,
                "severity": severity,
                "request_context": {
                    "method": method,
                    "path": path,
                    "query_params": query_params,
                    "user_agent": user_agent,
                    "remote_addr": remote_addr,
                },
                "trace_id": trace_id,
                "span_id": span_id,
            },
        )

        # Determine response status code
        status_code = 500
        if error_type in {"ValidationError", "ValueError"}:
            status_code = 400
        elif error_type in {"PermissionError", "Unauthorized"}:
            status_code = 401
        elif error_type in {"FileNotFoundError", "NotFound"}:
            status_code = 404

        # Create error response
        error_response = {
            "error": "Internal Server Error",
            "request_id": request_id,
        }

        # Include detailed error info in debug mode
        if self.debug:
            error_response.update(
                {
                    "error_type": error_type,
                    "error_code": error_code,
                    "message": error_message,
                    "trace_id": trace_id,
                }
            )

        return JSONResponse(status_code=status_code, content=error_response, headers={"X-Request-ID": request_id})
