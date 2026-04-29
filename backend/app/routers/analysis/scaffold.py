"""/scaffold endpoint - Scaffold statistics.

Python 3.6.8 compatible.
"""

from typing import Optional

from fastapi import APIRouter, Depends

from ...repositories.base import ExperimentRepository, TrajectoryRepository
from ...repositories.dependencies import get_experiment_repo, get_trajectory_repo
from .helpers import get_filtered_trajectories, group_by_key

router = APIRouter(
    tags=["analysis"],
)


@router.get("/scaffold")
def analysis_scaffold(
    experiment_id: str,
    iteration_start: Optional[int] = None,
    iteration_end: Optional[int] = None,
    split_by: Optional[str] = None,
    scaffold: Optional[str] = None,
    language: Optional[str] = None,
    tool_schema: Optional[str] = None,
    exp_repo: ExperimentRepository = Depends(get_experiment_repo),
    traj_repo: TrajectoryRepository = Depends(get_trajectory_repo),
):
    trajs = get_filtered_trajectories(
        experiment_id,
        iteration_start,
        iteration_end,
        scaffold=scaffold,
        language=language,
        exp_repo=exp_repo,
        traj_repo=traj_repo,
    )

    by_scaffold = group_by_key(trajs, "scaffold")
    result = []  # type: List[Dict]

    for scaffold, s_trajs in by_scaffold.items():
        n = len(s_trajs)
        passed_trajs = [t for t in s_trajs if t["passed"]]
        p_count = len(passed_trajs)

        turns_passed = [t["total_turns"] for t in passed_trajs]
        dur_passed = [t["duration_ms"] for t in passed_trajs]

        entry = {
            "scaffold": scaffold,
            "count": n,
            "pass_rate": round(p_count / max(n, 1), 4),
        }

        if turns_passed:
            entry["max_turns_passed"] = max(turns_passed)
            entry["avg_turns_passed"] = round(sum(turns_passed) / len(turns_passed), 1)
        else:
            entry["max_turns_passed"] = 0
            entry["avg_turns_passed"] = 0.0

        if dur_passed:
            entry["max_duration_passed_ms"] = max(dur_passed)
            entry["avg_duration_passed_ms"] = round(sum(dur_passed) / len(dur_passed), 1)
        else:
            entry["max_duration_passed_ms"] = 0
            entry["avg_duration_passed_ms"] = 0.0

        result.append(entry)

    return {"items": result}
