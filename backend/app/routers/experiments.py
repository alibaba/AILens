"""Experiments API — /api/v1/experiments"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from ..repositories.base import (
    ExperimentRepository,
    IterationRepository,
    TrajectoryRepository,
)
from ..repositories.dependencies import (
    get_experiment_repo,
    get_iteration_repo,
    get_trajectory_repo,
)

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.get("")
@router.get("/")
def list_experiments(
    project_id: Optional[str] = None,
    status: Optional[str] = None,
    scaffold: Optional[str] = None,
    algorithm: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    page: int = 1,
    page_size: int = 20,
    repo: ExperimentRepository = Depends(get_experiment_repo),
):
    items = repo.get_experiments(project_id=project_id)

    if status:
        items = [e for e in items if e["status"] == status]
    if scaffold:
        items = [e for e in items if scaffold in e["config"].get("scaffolds", [])]
    if algorithm:
        items = [e for e in items if e["config"]["algorithm"] == algorithm]

    reverse = sort_order == "desc"
    if sort_by in ("mean_reward", "pass_rate", "total_tokens", "total_trajectories"):
        items = sorted(items, key=lambda x: x.get(sort_by) or 0, reverse=reverse)
    elif sort_by == "name":
        items = sorted(items, key=lambda x: x.get("name", ""), reverse=reverse)
    else:
        items = sorted(items, key=lambda x: x.get("created_at", ""), reverse=reverse)

    total = len(items)
    p = int(page)
    ps = int(page_size)
    start = (p - 1) * ps
    end = start + ps

    return {
        "total": total,
        "page": p,
        "page_size": ps,
        "items": items[start:end],
    }


@router.get("/{experiment_id}")
def get_experiment(
    experiment_id: str,
    repo: ExperimentRepository = Depends(get_experiment_repo),
):
    exp = repo.get_experiment(experiment_id)
    if not exp:
        raise HTTPException(404, "Experiment {} not found".format(experiment_id))
    return exp


@router.get("/{experiment_id}/iterations")
def list_iterations(
    experiment_id: str,
    sort_by: str = "iteration_num",
    sort_order: str = "asc",
    page: int = 1,
    page_size: int = 50,
    exp_repo: ExperimentRepository = Depends(get_experiment_repo),
    iter_repo: IterationRepository = Depends(get_iteration_repo),
):
    exp = exp_repo.get_experiment(experiment_id)
    if not exp:
        raise HTTPException(404, "Experiment {} not found".format(experiment_id))

    items = iter_repo.get_iterations(experiment_id)

    reverse = sort_order == "desc"
    if sort_by == "mean_reward":
        items = sorted(
            items,
            key=lambda x: x["metrics"].get("mean_reward", 0),
            reverse=reverse,
        )
    elif sort_by == "pass_rate":
        items = sorted(
            items,
            key=lambda x: x["metrics"].get("pass_rate", 0),
            reverse=reverse,
        )
    else:
        items = sorted(
            items,
            key=lambda x: x.get("iteration_num", 0),
            reverse=reverse,
        )

    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items[start:end],
    }


@router.get("/{experiment_id}/iterations/{iteration_num}/trajectories")
def list_iteration_trajectories(
    experiment_id: str,
    iteration_num: int,
    scaffold: Optional[str] = None,
    outcome: Optional[str] = None,
    task_id: Optional[str] = None,
    sort_by: str = "reward",
    sort_order: str = "desc",
    page: int = 1,
    page_size: int = 50,
    exp_repo: ExperimentRepository = Depends(get_experiment_repo),
    traj_repo: TrajectoryRepository = Depends(get_trajectory_repo),
):
    exp = exp_repo.get_experiment(experiment_id)
    if not exp:
        raise HTTPException(404, "Experiment {} not found".format(experiment_id))

    trajs = traj_repo.get_trajectories(experiment_id=experiment_id)
    it_num = int(iteration_num)
    trajs = [t for t in trajs if t.get("iteration_num") == it_num]

    if scaffold:
        trajs = [t for t in trajs if t["scaffold"] == scaffold]
    if outcome:
        outcomes = set(outcome.split(","))
        trajs = [t for t in trajs if t["outcome"] in outcomes]
    if task_id:
        trajs = [t for t in trajs if t["task_id"] == task_id]

    reverse = sort_order == "desc"
    if sort_by == "reward":
        trajs = sorted(trajs, key=lambda x: x.get("reward", 0), reverse=reverse)
    elif sort_by == "total_turns":
        trajs = sorted(trajs, key=lambda x: x.get("total_turns", 0), reverse=reverse)
    elif sort_by == "duration_ms":
        trajs = sorted(trajs, key=lambda x: x.get("duration_ms", 0), reverse=reverse)
    else:
        trajs = sorted(trajs, key=lambda x: x.get("created_at", ""), reverse=reverse)

    total = len(trajs)
    p = int(page)
    ps = int(page_size)
    start = (p - 1) * ps
    end = start + ps

    return {
        "total": total,
        "page": p,
        "page_size": ps,
        "items": trajs[start:end],
    }
