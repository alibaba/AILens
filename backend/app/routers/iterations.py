"""Iterations API — /api/v1/iterations"""

from fastapi import APIRouter, Depends, HTTPException

from ..repositories.base import IterationRepository
from ..repositories.dependencies import get_iteration_repo

router = APIRouter(prefix="/iterations", tags=["iterations"])


@router.get("")
@router.get("/")
def list_iterations(
    experiment_id: str,
    sort_by: str = "iteration_num",
    sort_order: str = "asc",
    page: int = 1,
    page_size: int = 50,
    repo: IterationRepository = Depends(get_iteration_repo),
):
    items = repo.get_iterations(experiment_id)
    if not items:
        return {
            "total": 0,
            "page": page,
            "page_size": page_size,
            "items": [],
        }

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


@router.get("/{iteration_id}/metrics")
def get_iteration_metrics(
    iteration_id: str,
    repo: IterationRepository = Depends(get_iteration_repo),
):
    it = repo.get_iteration(iteration_id)
    if not it:
        raise HTTPException(404, "Iteration {} not found".format(iteration_id))
    return it
