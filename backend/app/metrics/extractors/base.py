"""Base utilities for metric extractors.

Python 3.6.8 compatible.
"""

import math

from ...mock import store

# ═══════════════════ Helpers ═══════════════════


def _filter_iterations(experiment_id, iteration_range):
    # type: (str, Optional[Tuple[int, int]]) -> List[Dict]
    iterations = store.get_iterations(experiment_id)
    if not iterations:
        return []
    if iteration_range:
        lo, hi = iteration_range
        iterations = [it for it in iterations if lo <= it["iteration_num"] <= hi]
    return iterations


def _get_trajectories_for_iteration(experiment_id, iter_num):
    # type: (str, int) -> List[Dict]
    trajs = store.get_trajectories(experiment_id=experiment_id)
    return [t for t in trajs if t.get("iteration_num") == iter_num]


def _std(vals):
    # type: (List[float]) -> float
    if len(vals) < 2:
        return 0.0
    m = sum(vals) / len(vals)
    return math.sqrt(sum((v - m) ** 2 for v in vals) / len(vals))


def _ts_epoch(iso_str):
    # type: (str) -> float
    """Parse ISO timestamp to epoch seconds."""
    from datetime import datetime, timezone

    s = iso_str.replace("Z", "+00:00")
    try:
        dt = datetime.strptime(s[:23], "%Y-%m-%dT%H:%M:%S.%f")
    except Exception:
        dt = datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S")
    return dt.replace(tzinfo=timezone.utc).timestamp()


def _compute_metric_from_trajs(metric_field, trajs, iteration):
    # type: (str, List[Dict], Dict) -> Optional[float]
    """Compute a metric value from a subset of trajectories."""
    n = len(trajs)
    if n == 0:
        return None

    rewards = [t["reward"] for t in trajs]

    field_map = {
        "trajectory_count": lambda: n,
        "passed_count": lambda: sum(1 for t in trajs if t["passed"]),
        "mean_reward": lambda: round(sum(rewards) / n, 4),
        "pass_rate": lambda: round(sum(1 for t in trajs if t["passed"]) / n, 4),
        "reward_std": lambda: round(_std(rewards), 4),
        "total_input_tokens": lambda: sum(t["input_tokens"] for t in trajs),
        "total_output_tokens": lambda: sum(t["output_tokens"] for t in trajs),
        "mean_tokens_per_trajectory": lambda: round(sum(t["total_tokens"] for t in trajs) / n, 1),
        "tokens_per_reward": lambda: _safe_tokens_per_reward(trajs),
        "input_output_ratio": lambda: round(
            sum(t["input_tokens"] for t in trajs) / max(sum(t["output_tokens"] for t in trajs), 1), 2
        ),
        "mean_turns": lambda: round(sum(t["total_turns"] for t in trajs) / n, 1),
        "mean_duration_ms": lambda: int(sum(t["duration_ms"] for t in trajs) / n),
        "mean_sandbox_create_duration_ms": lambda: int(sum(t.get("sandbox_create_duration_ms", 0) for t in trajs) / n),
        "mean_verify_duration_ms": lambda: int(sum(t.get("verify_duration_ms", 0) for t in trajs) / n),
    }

    fn = field_map.get(metric_field)
    if fn is None:
        return None
    return fn()


def _safe_tokens_per_reward(trajs):
    # type: (List[Dict]) -> Optional[float]
    n = len(trajs)
    if n == 0:
        return None
    total_tok = sum(t["total_tokens"] for t in trajs)
    mean_r = sum(t["reward"] for t in trajs) / n
    if mean_r < 0.001:
        return None
    return round(total_tok / mean_r, 1)
