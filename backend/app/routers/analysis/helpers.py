"""Shared helper functions for analysis endpoints.

Python 3.6.8 compatible.
"""

import math
import os
from collections import OrderedDict
from typing import Dict, List, Optional

import httpx
from fastapi import HTTPException

from ...repositories.base import ExperimentRepository, TrajectoryRepository


async def query_traceql_distinct(experiment_id: str, field: str) -> List[str]:
    """Query the external TraceQL service for distinct values of a single field.

    Returns a sorted list of non-empty string values. Falls back to an empty
    list when TRACEQL_BASE_URL is not configured (e.g. in local mock mode).
    """
    base_url = os.environ.get("TRACEQL_BASE_URL", "")
    if not base_url:
        return []

    auth_key = os.environ.get("TRACEQL_AUTH_KEY", "")
    query = '{experiment_id="' + experiment_id + '"}\n| select(' + field + ", count() as count)\n  by (" + field + ")"
    payload = {"query": query, "page_size": 1000, "page_num": 1, "scope": "rl"}

    try:
        async with httpx.AsyncClient() as client:
            params = {"authKey": auth_key} if auth_key else {}
            response = await client.post(
                "{}/api/v1/trace/query".format(base_url),
                json=payload,
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()
    except (httpx.HTTPStatusError, httpx.RequestError):
        return []

    rows = response.json().get("data", [])
    values = sorted(str(row[field]) for row in rows if row.get(field) is not None and str(row.get(field, "")).strip())
    return values


def get_filtered_trajectories(
    experiment_id: str,
    iteration_start: Optional[int],
    iteration_end: Optional[int],
    exp_repo: ExperimentRepository,
    traj_repo: TrajectoryRepository,
    scaffold: Optional[str] = None,
    language: Optional[str] = None,
    tool_schema: Optional[str] = None,
) -> List[Dict]:
    """Get trajectories for experiment, optionally filtered by iteration range,
    scaffold, language and tool_schema."""
    exp = exp_repo.get_experiment(experiment_id)
    if not exp:
        raise HTTPException(404, "Experiment {} not found".format(experiment_id))
    trajs = traj_repo.get_trajectories(experiment_id=experiment_id)
    if iteration_start is not None:
        it_start = int(iteration_start)
        trajs = [t for t in trajs if t.get("iteration_num", 0) >= it_start]
    if iteration_end is not None:
        it_end = int(iteration_end)
        trajs = [t for t in trajs if t.get("iteration_num", 0) <= it_end]
    if scaffold is not None:
        trajs = [t for t in trajs if t.get("scaffold") == scaffold]
    if language is not None:
        trajs = [t for t in trajs if t.get("task_language") == language]
    if tool_schema is not None:
        trajs = [t for t in trajs if t.get("tool_schema") == tool_schema]
    return trajs


def group_by_key(trajs: List[Dict], key: str) -> Dict[str, List[Dict]]:
    """Group trajectories by a given key."""
    groups = OrderedDict()  # type: Dict[str, List[Dict]]
    for t in trajs:
        k = str(t.get(key, "unknown"))
        if k not in groups:
            groups[k] = []
        groups[k].append(t)
    return groups


def percentile(sorted_vals: List[float], p: float) -> float:
    """Calculate percentile from sorted values."""
    if not sorted_vals:
        return 0.0
    idx = int(len(sorted_vals) * p)
    idx = min(idx, len(sorted_vals) - 1)
    return sorted_vals[idx]


def std(vals: List[float]) -> float:
    """Calculate standard deviation."""
    if len(vals) < 2:
        return 0.0
    m = sum(vals) / len(vals)
    return math.sqrt(sum((v - m) ** 2 for v in vals) / len(vals))


def get_step_trajectories(
    experiment_id: str,
    step: int,
    exp_repo: ExperimentRepository,
    traj_repo: TrajectoryRepository,
    scaffold: Optional[str] = None,
    language: Optional[str] = None,
    tool_schema: Optional[str] = None,
) -> List[Dict]:
    """Get trajectories for a specific step (iteration_num)."""
    return get_filtered_trajectories(
        experiment_id,
        step,
        step,
        scaffold=scaffold,
        language=language,
        exp_repo=exp_repo,
        traj_repo=traj_repo,
    )


def check_experiment_exists(
    experiment_id: str,
    exp_repo: ExperimentRepository,
) -> None:
    """Check if experiment exists, raise 404 if not."""
    exp = exp_repo.get_experiment(experiment_id)
    if not exp:
        raise HTTPException(404, "Experiment {} not found".format(experiment_id))
