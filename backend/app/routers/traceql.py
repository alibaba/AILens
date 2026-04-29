"""TraceQL API router - Execute TraceQL queries against trace data."""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..repositories.dependencies import RepositoryContainer, get_repositories
from ..tracing.traceql.engine import TraceQLEngine

router = APIRouter(prefix="/traceql", tags=["traceql"])


class TraceQLRequest(BaseModel):
    """TraceQL query request."""

    query: str
    experiment_id: Optional[str] = None
    scaffold: Optional[str] = None
    language: Optional[str] = None
    tool_schema: Optional[str] = None


def get_traceql_engine(repos: RepositoryContainer = Depends(get_repositories)) -> TraceQLEngine:
    """Get TraceQL engine with mock data store."""
    from ..repositories.dependencies import _get_store

    store = _get_store()
    return TraceQLEngine(store)


@router.post("/query")
def execute_traceql_query(
    request: TraceQLRequest,
    engine: TraceQLEngine = Depends(get_traceql_engine),
) -> Dict[str, Any]:
    """
    Execute TraceQL query and return results.

    Supports basic TraceQL syntax:
    - Span selectors: { span.tool_name != nil }
    - Aggregations: { span.tool_name != nil } | count() by (span.tool_name)
    - Comparisons: =, !=, >, <, >=, <=, =~, !~

    Examples:
    - Find all tool calls: { span.tool_name != nil }
    - Count by tool: { span.tool_name != nil } | count() by (span.tool_name)
    - Tool success rate: { span.tool_succeeded = true } | rate() by (span.tool_name)
    - Tool latency: { span.tool_name != nil } | avg(span:duration) by (span.tool_name)
    """
    try:
        # Build filters from request
        filters = {}
        if request.experiment_id:
            filters["experiment_id"] = request.experiment_id
        if request.scaffold:
            filters["scaffold"] = request.scaffold
        if request.language:
            filters["language"] = request.language
        if request.tool_schema:
            filters["tool_schema"] = request.tool_schema

        # Execute query
        result = engine.query(request.query, **filters)

        return result

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"TraceQL query error: {str(e)}")


@router.get("/examples")
def get_traceql_examples() -> Dict[str, Any]:
    """Get TraceQL query examples for documentation."""
    return {
        "tool_analysis": {
            "description": "Tool analysis queries for AI Lens",
            "examples": [
                {
                    "name": "All tool calls",
                    "query": "{ span.tool_name != nil }",
                    "description": "Find all spans that represent tool calls",
                },
                {
                    "name": "Tool call count by tool type",
                    "query": "{ span.tool_name != nil } | count() by (span.tool_name)",
                    "description": "Count tool calls grouped by tool name",
                },
                {
                    "name": "Tool success rate",
                    "query": "{ span.tool_succeeded = true } | rate() by (span.tool_name)",
                    "description": "Calculate success rate for each tool",
                },
                {
                    "name": "Tool latency analysis",
                    "query": "{ span.tool_name != nil } | avg(span:duration) by (span.tool_name)",
                    "description": "Average duration of tool calls by tool type",
                },
                {
                    "name": "Tool latency P95",
                    "query": "{ span.tool_name != nil } | quantile_over_time(span:duration, 0.95) by (span.tool_name)",
                    "description": "95th percentile latency by tool type",
                },
                {
                    "name": "Error tools",
                    "query": "{ span.tool_name != nil && span:status = error }",
                    "description": "Find tool calls that resulted in errors",
                },
                {
                    "name": "Slow tools",
                    "query": "{ span.tool_name != nil && span:duration > 1000 }",
                    "description": "Find tool calls that took longer than 1 second",
                },
                {
                    "name": "Multi-dimensional analysis",
                    "query": "{ span.tool_name != nil } | count() by (span.tool_name, resource.scaffold)",
                    "description": "Tool usage by tool type and scaffold",
                },
            ],
        },
        "basic_syntax": {
            "description": "Basic TraceQL syntax examples",
            "examples": [
                {"name": "Empty selector", "query": "{ }", "description": "Select all spans"},
                {
                    "name": "Service filter",
                    "query": '{ resource.service.name = "frontend" }',
                    "description": "Filter by service name",
                },
                {
                    "name": "HTTP status filter",
                    "query": "{ span.http.status_code >= 400 }",
                    "description": "Find HTTP error responses",
                },
                {
                    "name": "Duration filter",
                    "query": "{ span:duration > 100ms }",
                    "description": "Find spans longer than 100ms",
                },
                {
                    "name": "Regular expression",
                    "query": '{ span.http.method =~ "GET|POST" }',
                    "description": "Match HTTP methods with regex",
                },
            ],
        },
    }


@router.get("/syntax")
def get_traceql_syntax() -> Dict[str, Any]:
    """Get TraceQL syntax documentation."""
    return {
        "supported_selectors": [
            "{ }",  # All spans
            "{ span.tool_name != nil }",  # Tool spans only
            '{ resource.service.name = "frontend" }',  # Service filter
            "{ span.http.status_code >= 400 }",  # HTTP errors
        ],
        "supported_aggregations": ["count()", "avg()", "sum()", "min()", "max()", "quantile_over_time()"],
        "supported_grouping": [
            "by (span.tool_name)",
            "by (resource.scaffold)",
            "by (span.tool_name, resource.scaffold)",
        ],
        "example_queries": [
            "{ span.tool_name != nil } | count() by (span.tool_name)",
            "{ span.tool_name != nil } | avg(span:duration) by (span.tool_name)",
            "{ span.tool_succeeded = true } | count() by (span.tool_name, resource.scaffold)",
        ],
    }


@router.get("/health")
def get_traceql_health() -> Dict[str, Any]:
    """Check TraceQL engine health."""
    return {
        "status": "healthy",
        "service": "traceql",
        "version": "1.0.0",
        "features": ["span_selection", "aggregations", "grouping", "filtering"],
    }
