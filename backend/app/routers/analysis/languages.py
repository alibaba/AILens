"""/languages endpoint - Return distinct task_language values.

Python 3.6.8 compatible.
"""

from fastapi import APIRouter, Depends

from ...repositories.base import ExperimentRepository, TrajectoryRepository
from ...repositories.dependencies import get_experiment_repo, get_trajectory_repo
from .helpers import check_experiment_exists, query_traceql_distinct

router = APIRouter(
    tags=["analysis"],
)


@router.get("/languages")
async def analysis_languages(
    experiment_id: str,
    exp_repo: ExperimentRepository = Depends(get_experiment_repo),
    traj_repo: TrajectoryRepository = Depends(get_trajectory_repo),
):
    """Return distinct task_language values for the given experiment."""
    check_experiment_exists(experiment_id, exp_repo)
    langs = await query_traceql_distinct(experiment_id, "task_language")
    if not langs:
        # Fallback: derive from trajectory repository (mock mode)
        trajs = traj_repo.get_trajectories(experiment_id=experiment_id)
        langs = sorted({str(t["task_language"]) for t in trajs if t.get("task_language")})
    return {"languages": langs}
