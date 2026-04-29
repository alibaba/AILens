"""/repetition-detection endpoint - Detect repetition in tool calls and responses.

Python 3.6.8 compatible.
"""

from typing import Optional

from fastapi import APIRouter, Depends

from ...repositories.base import ExperimentRepository, TrajectoryRepository
from ...repositories.dependencies import get_experiment_repo, get_trajectory_repo
from .helpers import get_filtered_trajectories

router = APIRouter(
    tags=["analysis"],
)


@router.get("/repetition-detection")
def analysis_repetition_detection(
    experiment_id: str,
    iteration_start: Optional[int] = None,
    iteration_end: Optional[int] = None,
    scaffold: Optional[str] = None,
    language: Optional[str] = None,
    tool_schema: Optional[str] = None,
    exp_repo: ExperimentRepository = Depends(get_experiment_repo),
    traj_repo: TrajectoryRepository = Depends(get_trajectory_repo),
):
    """Detect repetition in tool calls and responses."""
    trajs = get_filtered_trajectories(
        experiment_id,
        iteration_start,
        iteration_end,
        scaffold=scaffold,
        language=language,
        exp_repo=exp_repo,
        traj_repo=traj_repo,
    )

    total = len(trajs)
    if total == 0:
        return {
            "total_trajectories": 0,
            "tool_call_repetition": {
                "affected_trajectories": 0,
                "affected_rate": 0.0,
                "total_repeats": 0,
                "mean_repeats_per_affected": 0.0,
            },
            "response_repetition": {
                "affected_trajectories": 0,
                "affected_rate": 0.0,
                "total_repeats": 0,
                "mean_repeats_per_affected": 0.0,
            },
        }

    # Tool call repetition
    tc_affected = sum(1 for t in trajs if t.get("repeat_tool_call_count", 0) > 0)
    tc_total_repeats = sum(t.get("repeat_tool_call_count", 0) for t in trajs)

    # Response repetition
    rr_affected = sum(1 for t in trajs if t.get("repeat_response_count", 0) > 0)
    rr_total_repeats = sum(t.get("repeat_response_count", 0) for t in trajs)

    return {
        "total_trajectories": total,
        "tool_call_repetition": {
            "affected_trajectories": tc_affected,
            "affected_rate": round(tc_affected / total, 4),
            "total_repeats": tc_total_repeats,
            "mean_repeats_per_affected": round(tc_total_repeats / max(tc_affected, 1), 1),
        },
        "response_repetition": {
            "affected_trajectories": rr_affected,
            "affected_rate": round(rr_affected / total, 4),
            "total_repeats": rr_total_repeats,
            "mean_repeats_per_affected": round(rr_total_repeats / max(rr_affected, 1), 1),
        },
    }
