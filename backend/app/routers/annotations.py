"""Annotations API — /api/v1/annotations"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from ..repositories.base import AnnotationRepository
from ..repositories.dependencies import get_annotation_repo

router = APIRouter(prefix="/annotations", tags=["annotations"])


@router.get("/")
def list_annotations(
    trajectory_id: Optional[str] = Query(None),
    experiment_id: Optional[str] = Query(None),
    source: Optional[str] = Query(None, description="auto / manual"),
    pattern_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    repo: AnnotationRepository = Depends(get_annotation_repo),
):
    items = repo.get_annotations()

    if trajectory_id:
        items = [a for a in items if a["trajectory_id"] == trajectory_id]
    if experiment_id:
        items = [a for a in items if a["experiment_id"] == experiment_id]
    if source:
        items = [a for a in items if a["source"] == source]
    if pattern_type:
        items = [a for a in items if a["pattern_type"] == pattern_type]
    if severity:
        items = [a for a in items if a["severity"] == severity]

    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    return {"total": total, "page": page, "page_size": page_size, "items": items[start:end]}


class CreateAnnotationRequest(BaseModel):
    trajectory_id: str
    experiment_id: str
    pattern_type: str
    description: str
    affected_turns: List[int] = Field(default_factory=list)
    severity: str = "info"


@router.post("/")
def create_annotation(
    body: CreateAnnotationRequest,
    repo: AnnotationRepository = Depends(get_annotation_repo),
):
    ann = repo.add_annotation(body.dict())
    return ann
