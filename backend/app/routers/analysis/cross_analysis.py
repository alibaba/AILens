"""/cross-analysis endpoint - Cross-analysis: Prompt x Schema matrix.

Python 3.6.8 compatible.
"""

from typing import Dict, List

from fastapi import APIRouter, Depends, Query

from ...repositories.base import ExperimentRepository, TrajectoryRepository
from ...repositories.dependencies import get_experiment_repo, get_trajectory_repo
from .helpers import check_experiment_exists, get_step_trajectories

router = APIRouter(
    tags=["analysis"],
)


@router.get("/cross-analysis")
def analysis_cross_analysis(
    experiment_id: str,
    step_a: int = Query(...),
    step_b: int = Query(...),
    row_dimension: str = Query("scaffold"),
    col_dimension: str = Query("tool_schema"),
    exp_repo: ExperimentRepository = Depends(get_experiment_repo),
    traj_repo: TrajectoryRepository = Depends(get_trajectory_repo),
):
    """Cross-analysis: Prompt x Schema matrix of pass rate changes."""
    check_experiment_exists(experiment_id, exp_repo)

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

    # Map dimension name to trajectory field
    dim_field_map = {
        "scaffold": "scaffold",
        "tool_schema": "tool_schema",
        "language": "task_language",
    }

    row_field = dim_field_map.get(row_dimension, "scaffold")
    col_field = dim_field_map.get(col_dimension, "tool_schema")

    # Group by task_id in each step
    def _task_pass_map(trajs: List[Dict]) -> Dict[str, Dict]:
        """task_id -> {passed: int, total: int, row_val, col_val}"""
        groups = {}  # type: Dict[str, Dict]
        for t in trajs:
            tid = t.get("task_id", "")
            if tid not in groups:
                groups[tid] = {
                    "passed": 0,
                    "total": 0,
                    "row_val": str(t.get(row_field, "unknown")),
                    "col_val": str(t.get(col_field, "unknown")),
                }
            groups[tid]["total"] += 1
            if t.get("passed"):
                groups[tid]["passed"] += 1
        return groups

    map_a = _task_pass_map(trajs_a)
    map_b = _task_pass_map(trajs_b)

    all_tasks = set(list(map_a.keys()) + list(map_b.keys()))  # type: Set[str]

    # Determine change group for each task, then cross-tabulate
    rows_set = set()  # type: Set[str]
    cols_set = set()  # type: Set[str]
    cells = {}  # type: Dict[str, Dict[str, Dict[str, int]]]

    for tid in all_tasks:
        info_a = map_a.get(tid, {"passed": 0, "total": 0, "row_val": "unknown", "col_val": "unknown"})
        info_b = map_b.get(tid, {"passed": 0, "total": 0, "row_val": "unknown", "col_val": "unknown"})

        pr_a = info_a["passed"] / max(info_a["total"], 1)
        pr_b = info_b["passed"] / max(info_b["total"], 1)
        change = pr_b - pr_a

        if change > 0:
            group = "improved"
        elif change < 0:
            group = "degraded"
        else:
            group = "unchanged"

        # Use info from b preferably (the later step)
        row_val = info_b.get("row_val", info_a.get("row_val", "unknown"))
        col_val = info_b.get("col_val", info_a.get("col_val", "unknown"))
        rows_set.add(row_val)
        cols_set.add(col_val)

        if row_val not in cells:
            cells[row_val] = {}
        if col_val not in cells[row_val]:
            cells[row_val][col_val] = {"improved": 0, "unchanged": 0, "degraded": 0}
        cells[row_val][col_val][group] += 1

    return {
        "row_dimension": row_dimension,
        "col_dimension": col_dimension,
        "rows": sorted(rows_set),
        "cols": sorted(cols_set),
        "cells": cells,
    }
