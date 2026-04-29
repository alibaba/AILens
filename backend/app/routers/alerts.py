"""Alerts API — /api/v1/alerts"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ..repositories.base import AlertRepository
from ..repositories.dependencies import get_alert_repo

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/rules")
def list_alert_rules(
    repo: AlertRepository = Depends(get_alert_repo),
):
    return {"items": repo.get_alert_rules()}


class CreateAlertRuleRequest(BaseModel):
    name: str
    expression: str
    threshold: float
    severity: str = "warning"
    for_duration: str = "5m"
    notification_channels: List[str] = Field(default_factory=list)


@router.post("/rules")
def create_alert_rule(
    body: CreateAlertRuleRequest,
    repo: AlertRepository = Depends(get_alert_repo),
):
    rule = repo.add_alert_rule(body.dict())
    return rule


@router.get("/active")
def list_active_alerts(
    severity: Optional[str] = Query(None),
    agent_name: Optional[str] = Query(None),
    repo: AlertRepository = Depends(get_alert_repo),
):
    items = repo.get_active_alerts()

    if severity:
        items = [a for a in items if a["severity"] == severity]
    if agent_name:
        items = [a for a in items if a["agent_name"] == agent_name]

    return {"total": len(items), "items": items}


@router.post("/rules/{rule_id}/silence")
def silence_alert(
    rule_id: str,
    duration: str = Query("1h", description="Silence duration"),
    repo: AlertRepository = Depends(get_alert_repo),
):
    rules = repo.get_alert_rules()
    rule = next((r for r in rules if r["id"] == rule_id), None)
    if not rule:
        raise HTTPException(404, f"Rule {rule_id} not found")
    return {"rule_id": rule_id, "silenced": True, "duration": duration}
