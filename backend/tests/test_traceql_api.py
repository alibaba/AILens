"""Tests for TraceQL API endpoints."""

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


class TestTraceQLAPI:
    """Test TraceQL query API endpoints."""

    def test_traceql_query_tool_count(self):
        """Test TraceQL query for tool call counts."""
        query_request = {
            "query": "{ span.tool_name != nil } | count() by (span.tool_name, resource.scaffold)",
            "experiment_id": "exp-test-123",
            "filters": {"scaffold": "basic"},
        }

        response = client.post("/api/v1/traceql/query", json=query_request)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert data["data"]["resultType"] == "matrix"
        assert isinstance(data["data"]["result"], list)

    def test_traceql_query_tool_success(self):
        """Test TraceQL query for tool success rates."""
        query_request = {
            "query": "{ span.tool_succeeded = true } | count() by (span.tool_name, resource.scaffold)",
            "experiment_id": "exp-test-123",
        }

        response = client.post("/api/v1/traceql/query", json=query_request)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_traceql_query_avg_duration(self):
        """Test TraceQL query for average duration."""
        query_request = {
            "query": "{ span.tool_name != nil } | avg(span:duration) by (span.tool_name)",
            "experiment_id": "exp-test-123",
        }

        response = client.post("/api/v1/traceql/query", json=query_request)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_traceql_query_p95_duration(self):
        """Test TraceQL query for P95 duration."""
        query_request = {
            "query": "{ span.tool_name != nil } | quantile_over_time(span:duration, 0.95) by (span.tool_name)",
            "experiment_id": "exp-test-123",
        }

        response = client.post("/api/v1/traceql/query", json=query_request)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_traceql_syntax_endpoint(self):
        """Test TraceQL syntax documentation endpoint."""
        response = client.get("/api/v1/traceql/syntax")

        assert response.status_code == 200
        data = response.json()
        assert "supported_selectors" in data
        assert "supported_aggregations" in data
        assert "supported_grouping" in data
        assert "example_queries" in data

    def test_traceql_health_endpoint(self):
        """Test TraceQL health check endpoint."""
        response = client.get("/api/v1/traceql/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "traceql"

    def test_traceql_query_with_filters(self):
        """Test TraceQL query with multiple filters."""
        query_request = {
            "query": "{ span.tool_name != nil } | count() by (span.tool_name, resource.scaffold)",
            "experiment_id": "exp-test-123",
            "filters": {"scaffold": "advanced", "language": "python", "tool_schema": "v1"},
        }

        response = client.post("/api/v1/traceql/query", json=query_request)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_traceql_query_invalid_syntax(self):
        """Test TraceQL query with invalid syntax."""
        query_request = {"query": "invalid query syntax", "experiment_id": "exp-test-123"}

        response = client.post("/api/v1/traceql/query", json=query_request)

        # Should still return success with empty results for now
        assert response.status_code == 200
        data = response.json()
        # May return success with empty results or error status
        assert "status" in data
