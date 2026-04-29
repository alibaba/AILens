"""/extreme-cases endpoint - Identify extreme cases from pass-rate diff.

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


@router.get("/extreme-cases")
def analysis_extreme_cases(
    experiment_id: str,
    step_a: int = Query(...),
    step_b: int = Query(...),
    threshold: float = Query(0.2),
    type: Optional[str] = Query(None),
    exp_repo: ExperimentRepository = Depends(get_experiment_repo),
    traj_repo: TrajectoryRepository = Depends(get_trajectory_repo),
):
    """Identify extreme cases from pass-rate diff."""
    check_experiment_exists(experiment_id, exp_repo)

    # Compute pass-rate diff inline (similar to pass_rate_diff endpoint)
    trajs_a = get_step_trajectories(
        experiment_id,
        int(step_a),
        exp_repo=exp_repo,
        traj_repo=traj_repo,
    )
    trajs_b = get_step_trajectories(
        experiment_id,
        int(step_b),
        exp_repo=exp_repo,
        traj_repo=traj_repo,
    )

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

    # Build diff items
    diff_items = []  # type: List[Dict]
    for tid in all_tasks:
        info_a = rates_a.get(tid, {"pass_rate": 0.0, "language": "unknown", "category": "unknown"})
        info_b = rates_b.get(tid, {"pass_rate": 0.0, "language": "unknown", "category": "unknown"})
        pr_a = info_a["pass_rate"]
        pr_b = info_b["pass_rate"]
        change = round(pr_b - pr_a, 4)
        lang = info_b.get("language", info_a.get("language", "unknown"))
        cat = info_b.get("category", info_a.get("category", "unknown"))

        diff_items.append(
            {
                "task_id": tid,
                "language": lang,
                "category": cat,
                "pass_rate_a": pr_a,
                "pass_rate_b": pr_b,
                "change": change,
            }
        )

    # Filter extreme cases
    threshold_val = float(threshold)
    extreme_improved = []  # type: List[Dict]
    extreme_degraded = []  # type: List[Dict]

    for item in diff_items:
        change = item["change"]
        if abs(change) <= threshold_val:
            continue
        entry = {
            "task_id": item["task_id"],
            "language": item.get("language", "unknown"),
            "category": item.get("category", "unknown"),
            "pass_rate_a": item["pass_rate_a"],
            "pass_rate_b": item["pass_rate_b"],
            "change": change,
        }
        if change > 0:
            extreme_improved.append(entry)
        else:
            extreme_degraded.append(entry)

    # Sort by |change| descending
    extreme_improved.sort(key=lambda x: abs(x["change"]), reverse=True)
    extreme_degraded.sort(key=lambda x: abs(x["change"]), reverse=True)

    # Filter by type if specified
    filter_type = type
    if filter_type == "improved":
        extreme_degraded = []
    elif filter_type == "degraded":
        extreme_improved = []

    return {
        "threshold": threshold_val,
        "extreme_improved": extreme_improved,
        "extreme_degraded": extreme_degraded,
        "total_extreme": len(extreme_improved) + len(extreme_degraded),
    }
