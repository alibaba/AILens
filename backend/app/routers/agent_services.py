"""Agent Services API — /api/v1/agent-services"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from ..repositories.base import AgentServiceRepository
from ..repositories.dependencies import get_agent_service_repo

router = APIRouter(prefix="/agent-services", tags=["agent-services"])


@router.get("")
@router.get("/")
def list_agent_services(
    project_id: Optional[str] = None,
    repo: AgentServiceRepository = Depends(get_agent_service_repo),
):
    items = repo.get_agent_services(project_id=project_id)
    return {"total": len(items), "items": items}


@router.get("/{service_id}")
def get_agent_service(
    service_id: str,
    repo: AgentServiceRepository = Depends(get_agent_service_repo),
):
    svc = repo.get_agent_service(service_id)
    if not svc:
        raise HTTPException(404, "Agent service {} not found".format(service_id))
    return svc


@router.get("/{service_id}/metrics")
def get_agent_service_metrics(
    service_id: str,
    category: Optional[str] = None,
    metric_name: Optional[str] = None,
    repo: AgentServiceRepository = Depends(get_agent_service_repo),
):
    svc = repo.get_agent_service(service_id)
    if not svc:
        raise HTTPException(404, "Agent service {} not found".format(service_id))

    metrics = repo.get_agent_service_metrics(service_id)

    if category:
        metrics = [m for m in metrics if m.get("category") == category]
    if metric_name:
        metrics = [m for m in metrics if m["metric_name"] == metric_name]

    return {"total": len(metrics), "series": metrics}
