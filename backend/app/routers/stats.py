"""Stats API router - Aggregated statistics endpoints."""

from collections import defaultdict
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..repositories.dependencies import RepositoryContainer, get_repositories
from ..tracing.traceql.engine import TraceQLEngine

router = APIRouter(prefix="/stats", tags=["stats"])


# ── Request/Response Models ──


class ToolAnalysisRequest(BaseModel):
    """Request for tool analysis aggregated metrics."""

    experiment_id: str
    scaffold: Optional[str] = None
    language: Optional[str] = None
    tool_schema: Optional[str] = None
    split_by: str = "none"  # none/scaffold/language/tool_schema


class ToolAnalysisItem(BaseModel):
    """Single tool analysis item with all metrics."""

    tool: str
    scaffold: str = ""  # Empty when split_by=none
    call_count: int = 0
    success_rate: float = 0.0
    avg_ms: float = 0.0
    p50_ms: float = 0.0
    p99_ms: float = 0.0
    trajectory_count: int = 0
    error_task_rate: float = 0.0
    success_task_rate: float = 0.0


class ToolAnalysisResponse(BaseModel):
    """Response containing tool analysis items."""

    items: List[ToolAnalysisItem]


# ── Helper Functions ──


def get_traceql_engine(repos: RepositoryContainer = Depends(get_repositories)) -> TraceQLEngine:
    """Get TraceQL engine with data store."""
    from ..repositories.dependencies import _get_store

    store = _get_store()
    return TraceQLEngine(store)


def _get_group_key(span: Dict[str, Any], split_by: str) -> str:
    """Get grouping key based on split_by parameter."""
    tool_name = span.get("span.tool_name") or "unknown"

    if split_by == "none":
        return tool_name
    elif split_by == "scaffold":
        scaffold = span.get("resource.scaffold") or "unknown"
        return f"{tool_name}|{scaffold}"
    elif split_by == "language":
        language = span.get("resource.task_language") or "unknown"
        return f"{tool_name}|{language}"
    elif split_by == "tool_schema":
        # tool_schema might be in resource or span attributes
        tool_schema = span.get("resource.tool_schema") or span.get("span.tool_schema") or "unknown"
        return f"{tool_name}|{tool_schema}"
    else:
        return tool_name


def _get_split_value(span: Dict[str, Any], split_by: str) -> str:
    """Get the split dimension value for display."""
    if split_by == "none":
        return ""
    elif split_by == "scaffold":
        return span.get("resource.scaffold") or ""
    elif split_by == "language":
        return span.get("resource.task_language") or ""
    elif split_by == "tool_schema":
        return span.get("resource.tool_schema") or span.get("span.tool_schema") or ""
    else:
        return ""


def _extract_spans_from_trajectories(
    engine: TraceQLEngine,
    experiment_id: str,
    scaffold: Optional[str] = None,
    language: Optional[str] = None,
    tool_schema: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Extract tool spans from trajectories using TraceQL."""
    # Build base query for tool spans
    result = engine.query(
        "{ span.tool_name != nil }",
        experiment_id=experiment_id,
        scaffold=scaffold,
        language=language,
        tool_schema=tool_schema,
    )

    if result.get("status") != "success":
        return []

    return result.get("data", {}).get("result", [])


def _calculate_percentile(values: List[float], p: float) -> float:
    """Calculate percentile from values."""
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    idx = int(len(sorted_vals) * p)
    idx = min(idx, len(sorted_vals) - 1)
    return sorted_vals[idx]


# ── API Endpoint ──


@router.post("/tool-analysis", response_model=ToolAnalysisResponse)
def get_tool_analysis(
    request: ToolAnalysisRequest,
    engine: TraceQLEngine = Depends(get_traceql_engine),
) -> ToolAnalysisResponse:
    """
    Get aggregated tool analysis metrics.

    Returns all tool metrics in a single API call:
    - call_count: Total number of tool calls
    - success_rate: Percentage of successful calls
    - avg_ms, p50_ms, p99_ms: Latency metrics
    - trajectory_count: Number of unique trajectories
    - error_task_rate, success_task_rate: Task-level rates

    Parameters:
    - experiment_id: Required experiment ID
    - scaffold, language, tool_schema: Optional filters
    - split_by: Grouping dimension (none/scaffold/language/tool_schema)

    This endpoint replaces multiple TraceQL queries with a single aggregated response,
    reducing network requests from 9 to 1 for the Behavior Analysis page.
    """
    try:
        # Extract all tool spans
        spans = _extract_spans_from_trajectories(
            engine,
            request.experiment_id,
            scaffold=request.scaffold,
            language=request.language,
            tool_schema=request.tool_schema,
        )

        if not spans:
            return ToolAnalysisResponse(items=[])

        # Group spans by tool + split dimension
        grouped_data = defaultdict(list)
        for span in spans:
            key = _get_group_key(span, request.split_by)
            grouped_data[key].append(span)

        # Calculate metrics for each group
        items = []
        for group_key, group_spans in grouped_data.items():
            # Extract tool name and split value
            if "|" in group_key:
                tool_name, split_value = group_key.split("|", 1)
            else:
                tool_name = group_key
                split_value = ""

            # Get first span for split dimension value
            first_span = group_spans[0] if group_spans else {}

            # Calculate call count
            call_count = len(group_spans)

            # Calculate success rate
            successful_calls = sum(
                1 for s in group_spans if s.get("span.tool_succeeded") is True or s.get("span:status") == "ok"
            )
            success_rate = successful_calls / call_count if call_count > 0 else 0.0

            # Calculate latency metrics
            durations = [
                s.get("span:duration", 0) for s in group_spans if isinstance(s.get("span:duration"), (int, float))
            ]
            avg_ms = sum(durations) / len(durations) if durations else 0.0
            p50_ms = _calculate_percentile(durations, 0.50)
            p99_ms = _calculate_percentile(durations, 0.99)

            # Calculate trajectory count (unique trajectory IDs)
            trajectory_ids = set()
            for s in group_spans:
                traj_id = s.get("trace:id") or s.get("resource.trajectory_id") or s.get("span.trajectory_id")
                if traj_id:
                    trajectory_ids.add(traj_id)
            trajectory_count = len(trajectory_ids)

            # Calculate task-level rates
            error_task_ids = set()
            success_task_ids = set()
            all_task_ids = set()

            for s in group_spans:
                task_id = s.get("resource.task_id")
                if task_id:
                    all_task_ids.add(task_id)
                    if s.get("span.tool_succeeded") is False or s.get("span:status") == "error":
                        error_task_ids.add(task_id)
                    elif s.get("span.tool_succeeded") is True or s.get("span:status") == "ok":
                        success_task_ids.add(task_id)

            total_tasks = len(all_task_ids)
            error_task_rate = len(error_task_ids) / total_tasks if total_tasks > 0 else 0.0
            success_task_rate = len(success_task_ids) / total_tasks if total_tasks > 0 else 0.0

            # Build item
            items.append(
                ToolAnalysisItem(
                    tool=tool_name,
                    scaffold=split_value
                    if request.split_by != "none"
                    else _get_split_value(first_span, request.split_by),
                    call_count=call_count,
                    success_rate=success_rate,
                    avg_ms=avg_ms,
                    p50_ms=p50_ms,
                    p99_ms=p99_ms,
                    trajectory_count=trajectory_count,
                    error_task_rate=error_task_rate,
                    success_task_rate=success_task_rate,
                )
            )

        # Sort by call_count descending
        items.sort(key=lambda x: x.call_count, reverse=True)

        return ToolAnalysisResponse(items=items)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tool analysis error: {str(e)}")
