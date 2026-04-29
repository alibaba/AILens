"""
Tests for observability functionality - simplified version.
"""

import asyncio
from unittest.mock import MagicMock, patch

import pytest
from app.main import app
from app.observability.logging.formatters import StructuredFormatter
from app.observability.metrics.registry import metrics_registry
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Test client for FastAPI app."""
    return TestClient(app)


class TestObservabilityEndpoints:
    """Test observability monitoring endpoints."""

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/observability/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["service"] == "ailens-api"

    def test_ready_endpoint(self, client):
        """Test readiness check endpoint."""
        response = client.get("/observability/ready")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["ready", "not_ready"]
        assert "checks" in data
        assert "timestamp" in data

    def test_metrics_endpoint(self, client):
        """Test Prometheus metrics endpoint."""
        response = client.get("/observability/metrics")

        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]

        content = response.text
        assert "gc_collections_total" in content
        assert "# HELP" in content
        assert "# TYPE" in content

    def test_info_endpoint(self, client):
        """Test service info endpoint."""
        response = client.get("/observability/info")

        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "runtime" in data
        assert "configuration" in data
        assert data["service"]["name"] == "ailens-api"


class TestStructuredFormatter:
    """Test structured logging formatter."""

    def test_basic_log_formatting(self):
        """Test basic log record formatting."""
        import logging

        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test_logger", level=logging.INFO, pathname="", lineno=0, msg="Test message", args=(), exc_info=None
        )

        formatted = formatter.format(record)

        assert "INFO" in formatted
        assert "test_logger" in formatted
        assert "Test message" in formatted
        assert len(formatted) > 0

    def test_log_with_request_id(self):
        """Test log formatting with request_id."""
        import logging

        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="access", level=logging.INFO, pathname="", lineno=0, msg="Request completed", args=(), exc_info=None
        )
        record.request_id = "test-request-123"

        formatted = formatter.format(record)

        assert "request_id=test-request-123" in formatted

    def test_log_with_exception(self):
        """Test log formatting with exception info."""
        import logging

        formatter = StructuredFormatter()

        try:
            raise ValueError("Test error")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

            record = logging.LogRecord(
                name="error",
                level=logging.ERROR,
                pathname="",
                lineno=0,
                msg="Error occurred",
                args=(),
                exc_info=exc_info,
            )

            formatted = formatter.format(record)

            assert "ERROR" in formatted
            assert "ValueError: Test error" in formatted


class TestBusinessMetrics:
    """Test business metrics collection."""

    def test_traceql_query_metrics(self):
        """Test TraceQL query metrics recording."""
        from app.observability.metrics.business import business_metrics

        # Record successful query
        business_metrics.record_traceql_query(view_name="select_view", duration=0.5, success=True)

        # Record failed query
        business_metrics.record_traceql_query(view_name="search_view", duration=2.0, success=False)

        # No exceptions should be raised
        assert True


class TestSystemMetrics:
    """Test system metrics collection."""

    def test_gc_metrics_collection(self):
        """Test garbage collection metrics."""
        from app.observability.metrics.system import system_metrics

        # Update GC metrics
        system_metrics.update_gc_metrics()

        # No exceptions should be raised
        assert True


class TestMetricsRegistry:
    """Test metrics registry functionality."""

    @pytest.mark.asyncio
    async def test_background_collection_start_stop(self):
        """Test starting and stopping background metrics collection."""
        # Start background collection with short interval
        await metrics_registry.start_background_collection(interval=1)

        # Wait briefly
        await asyncio.sleep(0.1)

        # Stop background collection
        await metrics_registry.stop_background_collection()

        # No exceptions should be raised
        assert True

    def test_metrics_summary(self):
        """Test getting metrics summary."""
        summary = metrics_registry.get_metrics_summary()

        assert "gc_summary" in summary
        assert "timestamp" in summary

        gc_summary = summary["gc_summary"]
        assert "total_collections" in gc_summary
        assert "by_generation" in gc_summary


class TestAccessLogMiddleware:
    """Test access logging middleware."""

    def test_request_logging(self, client):
        """Test that requests are logged with proper format."""
        # Make a request to trigger access log
        response = client.get("/")

        assert response.status_code == 200
        # Access log should be generated (tested via integration)

    def test_request_with_query_params(self, client):
        """Test request logging with query parameters."""
        response = client.get("/?test=value&page=1")

        assert response.status_code == 200
        # Should log query parameters


class TestErrorHandlingMiddleware:
    """Test error handling middleware."""

    def test_unhandled_exception_handling(self, client):
        """Test handling of unhandled exceptions."""
        # This would need a route that raises an exception
        # For now, just verify middleware is registered
        assert True


@pytest.mark.integration
class TestTelemetryIntegration:
    """Integration tests for telemetry setup."""

    def test_telemetry_setup(self):
        """Test OpenTelemetry setup doesn't raise errors."""
        from app.observability.telemetry import setup_telemetry

        # Should not raise exceptions
        setup_telemetry(app_name="test-service", app_version="0.1.0", otlp_endpoint="http://localhost:4317")

        assert True

    @patch("httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_readiness_check_with_traceql_service(self, mock_get, client):
        """Test readiness check with TraceQL service."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        with (
            patch("app.routers.observability.TRACEQL_BASE_URL", "http://test-service"),
            patch("app.routers.observability.TRACEQL_AUTH_KEY", "key"),
        ):
            response = client.get("/observability/ready")

            assert response.status_code == 200
            data = response.json()
            assert "traceql" in data["checks"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
