"""Integration tests for tracing functionality."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from app.main import app
from app.tracing.models import Span, SpanStatus, Trace
from app.tracing.registry import TraceProviderRegistry
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_trace():
    """Mock trace data."""
    return Trace(
        trace_id="test_trace_id",
        spans=[
            Span(
                span_id="0",
                trace_id="test_trace_id",
                operation_name="root_operation",
                service_name="root_service",
                start_time=1000,
                duration_ms=500,
                status=SpanStatus.OK,
            ),
            Span(
                span_id="0.1",
                trace_id="test_trace_id",
                operation_name="child_operation",
                service_name="child_service",
                start_time=1100,
                duration_ms=200,
                parent_span_id="0",
                status=SpanStatus.ERROR,
                status_message="Test error",
            ),
        ],
        duration_ms=500,
        span_count=2,
        has_error=True,
        root_operation="root_operation",
        root_service="root_service",
    )


class TestTraceAPI:
    """Test trace API endpoints."""

    def test_get_trace_success(self, client, mock_trace):
        """Test successful trace retrieval."""
        # Mock provider with AsyncMock for async methods
        mock_provider = Mock()
        mock_provider.get_trace = AsyncMock(return_value=mock_trace)

        with patch("app.routers.traces.get_trace_provider", return_value=mock_provider):
            response = client.get("/api/v1/traces/test_trace_id")

        assert response.status_code == 200
        data = response.json()
        assert data["trace_id"] == "test_trace_id"
        assert data["span_count"] == 2
        assert data["has_error"] is True
        assert len(data["spans"]) == 2

    def test_get_trace_not_found(self, client):
        """Test trace not found."""
        mock_provider = Mock()
        mock_provider.get_trace = AsyncMock(return_value=None)

        with patch("app.routers.traces.get_trace_provider", return_value=mock_provider):
            response = client.get("/api/v1/traces/nonexistent_trace")

        assert response.status_code == 404
        assert response.json()["detail"] == "Trace not found"

    def test_get_trace_with_provider(self, client, mock_trace):
        """Test trace retrieval with specific provider."""
        mock_provider = Mock()
        mock_provider.get_trace = AsyncMock(return_value=mock_trace)

        with patch("app.routers.traces.get_trace_provider", return_value=mock_provider) as mock_get_provider:
            response = client.get("/api/v1/traces/test_trace_id?provider=eagleeye")

        assert response.status_code == 200
        mock_get_provider.assert_called_once_with("eagleeye")

    def test_search_traces(self, client):
        """Test trace search."""
        from app.tracing.models import TraceSearchResult

        search_results = [
            TraceSearchResult(
                trace_id="trace_1",
                start_time=1000,
                duration_ms=100,
                span_count=5,
                status=SpanStatus.OK,
                root_operation="operation_1",
                root_service="service_1",
            )
        ]

        mock_provider = Mock()
        mock_provider.search_traces = AsyncMock(return_value=search_results)

        with patch("app.routers.traces.get_trace_provider", return_value=mock_provider):
            response = client.get("/api/v1/traces/search?start_time=1000&end_time=2000")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["trace_id"] == "trace_1"

    def test_get_trace_url(self, client):
        """Test trace URL retrieval."""
        mock_provider = Mock()
        mock_provider.get_trace_url = Mock(return_value="https://example.com/trace/test_id")

        with patch("app.routers.traces.get_trace_provider", return_value=mock_provider):
            response = client.get("/api/v1/traces/test_id/url")

        assert response.status_code == 200
        data = response.json()
        assert data["trace_id"] == "test_id"
        assert data["url"] == "https://example.com/trace/test_id"

    def test_provider_not_found_error(self, client):
        """Test provider not found error."""
        with patch("app.routers.traces.get_trace_provider", side_effect=ValueError("Provider not found")):
            response = client.get("/api/v1/traces/test_id")

        assert response.status_code == 400
        assert "Provider not found" in response.json()["detail"]


class TestProviderInitialization:
    """Test provider initialization."""

    @pytest.mark.skip(reason="eagleeye provider not available in open-source version")
    def test_provider_initialization_with_config(self):
        """Test provider initialization with configuration."""
        # Reset registry
        TraceProviderRegistry._providers.clear()
        TraceProviderRegistry._default = None

        # Mock settings
        mock_settings = Mock()
        mock_settings.EAGLEEYE_AUTH_KEY = "test_key"
        mock_settings.EAGLEEYE_BASE_URL = "https://test.example.com"

        with patch("app.tracing.config.get_settings", return_value=mock_settings):
            from app.tracing.providers import init_providers

            init_providers()

        # Should have registered eagleeye provider
        providers = TraceProviderRegistry.list_providers()
        assert "eagleeye" in providers

        provider = TraceProviderRegistry.get("eagleeye")
        assert provider is not None
        assert provider.name == "eagleeye"

    def test_provider_initialization_without_config(self):
        """Test provider initialization without configuration."""
        # Reset registry
        TraceProviderRegistry._providers.clear()
        TraceProviderRegistry._default = None

        # Mock settings without auth key
        mock_settings = Mock()
        mock_settings.EAGLEEYE_AUTH_KEY = ""

        with patch("app.tracing.config.get_settings", return_value=mock_settings):
            from app.tracing.providers import init_providers

            init_providers()

        # Should not have registered any providers
        providers = TraceProviderRegistry.list_providers()
        assert len(providers) == 0
