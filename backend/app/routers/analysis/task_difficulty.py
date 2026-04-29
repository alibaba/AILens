"""/task-difficulty endpoint - Dynamic task difficulty classification.

Python 3.6.8 compatible.
"""

from fastapi import APIRouter, Depends

from ...repositories.base import ExperimentRepository, TrajectoryRepository
from ...repositories.dependencies import get_experiment_repo, get_trajectory_repo
from .helpers import check_experiment_exists

router = APIRouter(
    tags=["analysis"],
)


@router.get("/task-difficulty")
def analysis_task_difficulty(
    experiment_id: str,
    exp_repo: ExperimentRepository = Depends(get_experiment_repo),
    traj_repo: TrajectoryRepository = Depends(get_trajectory_repo),
):
    """Dynamic task difficulty classification based on historical pass rates."""
    check_experiment_exists(experiment_id, exp_repo)

    # Collect all trajectories across ALL experiments
    all_trajs = traj_repo.get_trajectories()

    # Group by task_id
    task_stats = {}  # type: Dict[str, Dict]
    task_experiments = {}  # type: Dict[str, Set[str]]

    for t in all_trajs:
        tid = t.get("task_id", "")
        if tid not in task_stats:
            task_stats[tid] = {
                "total": 0,
                "passed": 0,
                "language": t.get("task_language", "unknown"),
            }
            task_experiments[tid] = set()
        task_stats[tid]["total"] += 1
        if t.get("passed"):
            task_stats[tid]["passed"] += 1
        task_experiments[tid].add(t.get("experiment_id", ""))

    items = []  # type: List[Dict]
    dist = {"easy": 0, "medium": 0, "hard": 0}

    for tid, info in task_stats.items():
        rate = round(info["passed"] / max(info["total"], 1), 4)

        # Classify difficulty
        if rate >= 0.30:
            difficulty = "easy"
        elif rate >= 0.10:
            difficulty = "medium"
        else:
            difficulty = "hard"

        dist[difficulty] += 1
        items.append(
            {
                "task_id": tid,
                "language": info["language"],
                "historical_runs": info["total"],
                "historical_experiments": len(task_experiments.get(tid, set())),
                "pass_rate": rate,
                "difficulty": difficulty,
            }
        )

    # Sort by pass_rate ascending
    items.sort(key=lambda x: x["pass_rate"])

    total_items = len(items)
    distribution = {}  # type: Dict[str, Dict]
    for d_name, d_count in dist.items():
        distribution[d_name] = {
            "count": d_count,
            "percentage": round(d_count / max(total_items, 1), 4),
        }

    return {
        "distribution": distribution,
        "items": items,
    }
