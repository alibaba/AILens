"""Tasks API — /api/v1/tasks (功能下线)"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from ..repositories.base import ExperimentRepository, TrajectoryRepository
from ..repositories.dependencies import get_experiment_repo, get_trajectory_repo

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/{task_id}/history")
def get_task_history(
    task_id: str,
    experiment_id: Optional[str] = None,
    project_id: Optional[str] = None,
    traj_repo: TrajectoryRepository = Depends(get_trajectory_repo),
    exp_repo: ExperimentRepository = Depends(get_experiment_repo),
):
    """Tasks功能已下线 - 功能建设中"""
    raise HTTPException(
        status_code=501,
        detail={
            "message": "Tasks功能暂时下线，正在重新建设中",
            "status": "under_construction",
            "code": "FEATURE_OFFLINE",
        },
    )


@router.get("/")
def list_tasks():
    """Tasks功能已下线 - 功能建设中"""
    raise HTTPException(
        status_code=501,
        detail={
            "message": "Tasks功能暂时下线，正在重新建设中",
            "status": "under_construction",
            "code": "FEATURE_OFFLINE",
        },
    )


@router.get("/{task_id}")
def get_task(task_id: str):
    """Tasks功能已下线 - 功能建设中"""
    raise HTTPException(
        status_code=501,
        detail={
            "message": "Tasks功能暂时下线，正在重新建设中",
            "status": "under_construction",
            "code": "FEATURE_OFFLINE",
        },
    )
