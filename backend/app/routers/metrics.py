"""Metrics API — /api/v1/metrics"""

from typing import Optional

from fastapi import APIRouter, Depends, Query

from ..repositories.base import AgentServiceRepository
from ..repositories.dependencies import get_agent_service_repo

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/query")
def query_metrics(
    metric_name: Optional[str] = Query(None, description="Metric name filter"),
    agent: Optional[str] = Query(None, description="Agent instance filter"),
    scaffold: Optional[str] = Query(None),
    repo: AgentServiceRepository = Depends(get_agent_service_repo),
):
    """Instant metric query (latest values)."""
    items = repo.get_agent_metrics()

    if metric_name:
        items = [m for m in items if m["metric_name"] == metric_name]
    if agent:
        items = [m for m in items if m["labels"].get("agent") == agent]
    if scaffold:
        items = [m for m in items if m["labels"].get("scaffold") == scaffold]

    # Return only latest value for instant query
    results = []
    for m in items:
        latest = m["values"][-1] if m["values"] else None
        results.append(
            {
                "metric_name": m["metric_name"],
                "labels": m["labels"],
                "value": latest,
            }
        )

    return {"series": results}


@router.get("/range")
def range_query(
    metric_name: Optional[str] = Query(None),
    agent: Optional[str] = Query(None),
    scaffold: Optional[str] = Query(None),
    start: Optional[str] = Query(None, description="ISO 8601 start time"),
    end: Optional[str] = Query(None, description="ISO 8601 end time"),
    repo: AgentServiceRepository = Depends(get_agent_service_repo),
):
    """Range metric query (full time series)."""
    items = repo.get_agent_metrics()

    if metric_name:
        items = [m for m in items if m["metric_name"] == metric_name]
    if agent:
        items = [m for m in items if m["labels"].get("agent") == agent]
    if scaffold:
        items = [m for m in items if m["labels"].get("scaffold") == scaffold]

    # Filtering by time range would apply here with real data;
    # mock data is already scoped to last 1h
    return {"series": items}


@router.get("/labels")
def list_labels(
    repo: AgentServiceRepository = Depends(get_agent_service_repo),
):
    """List available metric names and label values."""
    items = repo.get_agent_metrics()
    names = sorted(set(m["metric_name"] for m in items))
    agents = sorted(set(m["labels"].get("agent", "") for m in items))
    scaffolds = sorted(set(m["labels"].get("scaffold", "") for m in items))

    return {
        "labels": [
            {"name": "metric_name", "values": names},
            {"name": "agent", "values": agents},
            {"name": "scaffold", "values": scaffolds},
        ]
    }
