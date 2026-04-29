"""/pass-rate-diff endpoint - Compare pass rates between two steps.

Python 3.6.8 compatible.
"""

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, Query

from ...repositories.base import ExperimentRepository, TrajectoryRepository
from ...repositories.dependencies import get_experiment_repo, get_trajectory_repo
from .helpers import check_experiment_exists, get_step_trajectories

router = APIRouter(
    tags=["analysis"],
)


@router.get("/pass-rate-diff")
def analysis_pass_rate_diff(
    experiment_id: str,
    step_a: int = Query(...),
    step_b: int = Query(...),
    scaffold: Optional[str] = None,
    language: Optional[str] = None,
    tool_schema: Optional[str] = None,
    exp_repo: ExperimentRepository = Depends(get_experiment_repo),
    traj_repo: TrajectoryRepository = Depends(get_trajectory_repo),
):
    """Compare pass rates between two steps for each task_id."""
    check_experiment_exists(experiment_id, exp_repo)

    trajs_a = get_step_trajectories(
        experiment_id,
        int(step_a),
        scaffold=scaffold,
        language=language,
        exp_repo=exp_repo,
        traj_repo=traj_repo,
    )
    trajs_b = get_step_trajectories(
        experiment_id,
        int(step_b),
        scaffold=scaffold,
        language=language,
        exp_repo=exp_repo,
        traj_repo=traj_repo,
    )

    # Group by task_id and compute pass rates
    def _task_pass_rates(trajs: List[Dict]) -> Dict[str, Dict]:
        groups = {}  # type: Dict[str, Dict]
        for t in trajs:
            tid = t.get("task_id", "")
            if tid not in groups:
                groups[tid] = {
                    "total": 0,
                    "passed": 0,
                    "language": t.get("task_language", "unknown"),
                }
            groups[tid]["total"] += 1
            if t.get("passed"):
                groups[tid]["passed"] += 1
        result = {}  # type: Dict[str, Dict]
        for tid, info in groups.items():
            rate = round(info["passed"] / max(info["total"], 1), 4)
            result[tid] = {
                "pass_rate": rate,
                "language": info["language"],
            }
        return result

    rates_a = _task_pass_rates(trajs_a)
    rates_b = _task_pass_rates(trajs_b)

    all_tasks = sorted(set(list(rates_a.keys()) + list(rates_b.keys())))

    improved = 0
    unchanged = 0
    degraded = 0
    items = []  # type: List[Dict]

    for tid in all_tasks:
        info_a = rates_a.get(tid, {"pass_rate": 0.0, "language": "unknown", "category": "unknown"})
        info_b = rates_b.get(tid, {"pass_rate": 0.0, "language": "unknown", "category": "unknown"})
        pr_a = info_a["pass_rate"]
        pr_b = info_b["pass_rate"]
        change = round(pr_b - pr_a, 4)

        if change > 0:
            change_group = "improved"
            improved += 1
        elif change < 0:
            change_group = "degraded"
            degraded += 1
        else:
            change_group = "unchanged"
            unchanged += 1

        lang = info_b.get("language", info_a.get("language", "unknown"))
        cat = info_b.get("category", info_a.get("category", "unknown"))

        items.append(
            {
                "task_id": tid,
                "language": lang,
                "category": cat,
                "pass_rate_a": pr_a,
                "pass_rate_b": pr_b,
                "change": change,
                "change_group": change_group,
            }
        )

    # Sort by |change| descending
    items.sort(key=lambda x: abs(x["change"]), reverse=True)

    return {
        "step_a": int(step_a),
        "step_b": int(step_b),
        "total_tasks": len(all_tasks),
        "summary": {
            "improved": improved,
            "unchanged": unchanged,
            "degraded": degraded,
        },
        "items": items,
    }
