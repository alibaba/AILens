"""Projects API — /api/v1/projects"""

from typing import Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..repositories.base import ProjectRepository
from ..repositories.dependencies import get_project_repo

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("")
@router.get("/")
def list_projects(
    repo: ProjectRepository = Depends(get_project_repo),
):
    items = repo.get_projects()
    return {"total": len(items), "items": items}


@router.get("/{project_id}")
def get_project(
    project_id: str,
    repo: ProjectRepository = Depends(get_project_repo),
):
    proj = repo.get_project(project_id)
    if not proj:
        raise HTTPException(404, "Project {} not found".format(project_id))
    return proj


class CreateProjectRequest(BaseModel):
    name: str = ""
    description: str = ""
    owner: str = ""
    tags: Dict[str, str] = Field(default_factory=dict)


@router.post("/")
def create_project(
    body: CreateProjectRequest,
    repo: ProjectRepository = Depends(get_project_repo),
):
    proj = repo.add_project(body.dict())
    return proj
