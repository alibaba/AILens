"""TraceQL-based implementations of ExperimentRepository and IterationRepository."""

import logging
import os
import threading
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

# ── Module-level cache ──────────────────────────────────────────────────────
# { experiment_id: { "count": int, "experiment": dict, "iterations": list|None } }
_cache: Dict[str, Dict] = {}
_cache_lock = threading.Lock()

# ── Shared query fragments ───────────────────────────────────────────────────
_AGGS = (
    "experiment_id, model, scaffold,"
    "max(iteration) as latest_iteration,"
    "count() as total_trajectories,"
    "round(avg(reward), 4) as mean_reward,"
    "round(avg(if(verify_code = 'success', 1, 0)), 4) as pass_rate,"
    "sum(total_tokens) as total_tokens,"
    "min(start_time) as first_seen"
)
_AGG_BY = "by (experiment_id, model, scaffold)"


def _traceql_query(query: str, page_size: int = 1000) -> List[Dict]:
    """Execute a TraceQL query and return the ``data`` list from the response.

    Raises:
        RuntimeError: If TRACEQL_BASE_URL is not configured.
        httpx.HTTPStatusError: On 4xx/5xx responses.
        httpx.RequestError: On network-level failures.
    """
    base_url = os.environ.get("TRACEQL_BASE_URL", "")
    if not base_url:
        raise RuntimeError("TRACEQL_BASE_URL not configured")

    auth_key = os.environ.get("TRACEQL_AUTH_KEY", "")
    params = {"authKey": auth_key} if auth_key else {}

    payload = {
        "query": query,
        "scope": "rl",
        "pageSize": page_size,
        "pageNum": 1,
    }

    with httpx.Client(timeout=30.0) as client:
        response = client.post(
            f"{base_url}/api/v1/trace/query",
            json=payload,
            params=params,
        )
        response.raise_for_status()
        result = response.json()

    return result.get("data") or []


def _merge_rows(rows: List[Dict]) -> Dict:
    """Merge TraceQL rows sharing the same experiment_id into one experiment dict."""
    if not rows:
        raise ValueError("_merge_rows requires at least one row")
    experiment_id = rows[0]["experiment_id"]
    model = rows[0].get("model", "")
    scaffolds = sorted({r.get("scaffold", "") for r in rows if r.get("scaffold")})

    total_traj = sum(int(r.get("total_trajectories", 0)) for r in rows)
    total_tokens = sum(int(r.get("total_tokens", 0)) for r in rows)
    latest_iteration = max(int(r.get("latest_iteration", 0)) for r in rows)

    mean_reward = 0.0
    pass_rate = 0.0
    if total_traj > 0:
        mean_reward = (
            sum(float(r.get("mean_reward", 0)) * int(r.get("total_trajectories", 0)) for r in rows) / total_traj
        )
        pass_rate = sum(float(r.get("pass_rate", 0)) * int(r.get("total_trajectories", 0)) for r in rows) / total_traj

    min_first_seen = min(int(r.get("first_seen", 0)) for r in rows)
    # start_time may be milliseconds despite docs saying seconds; normalize to seconds
    ts_sec = min_first_seen / 1000 if min_first_seen > 1e10 else min_first_seen
    created_at = datetime.fromtimestamp(ts_sec, tz=timezone.utc).isoformat() if min_first_seen else ""

    return {
        "id": experiment_id,
        "name": experiment_id,
        "status": "unknown",
        "project_id": "default",
        "config": {
            "model": model,
            "scaffolds": scaffolds,
            "algorithm": "",
            "reward_function": "",
            "reward_components": [],
            "hyperparams": {},
            "benchmark_id": "",
            "max_turns": 0,
        },
        "latest_iteration": latest_iteration,
        "mean_reward": round(mean_reward, 4),
        "pass_rate": round(pass_rate, 4),
        "total_trajectories": total_traj,
        "total_tokens": total_tokens,
        "created_at": created_at,
        "tags": {},
    }


def _fetch_counts() -> Dict[str, int]:
    """Query trajectory count per experiment_id for all experiments.

    Returns mapping: { experiment_id: count }
    """
    rows = _traceql_query("{} | select(count() as total) by (experiment_id)")
    return {row["experiment_id"]: int(row["total"]) for row in rows if "experiment_id" in row}


def _aggregate_all() -> List[Dict]:
    """Aggregate all experiments from TraceQL (no filter)."""
    query = f"{{}} | select({_AGGS}) {_AGG_BY}"
    rows = _traceql_query(query)
    groups: Dict[str, List] = defaultdict(list)
    for row in rows:
        eid = row.get("experiment_id")
        if eid:
            groups[eid].append(row)
    return [_merge_rows(group) for group in groups.values()]


def _aggregate_experiment(experiment_id: str) -> Optional[Dict]:
    """Aggregate a single experiment by ID from TraceQL."""
    query = f'{{experiment_id = "{experiment_id}"}} | select({_AGGS}) {_AGG_BY}'
    rows = _traceql_query(query)
    rows = [r for r in rows if r.get("experiment_id") == experiment_id]
    return _merge_rows(rows) if rows else None


class TraceQLExperimentRepository:
    """ExperimentRepository backed by TraceQL aggregation with count-based cache."""

    def get_experiments(self, project_id: Optional[str] = None) -> List[Dict]:
        """Get all experiments discovered from TraceQL traces."""
        try:
            counts = _fetch_counts()
        except Exception:
            logger.warning("_fetch_counts failed, falling back to aggregate_all", exc_info=True)
            counts = None

        if counts is None:
            # Count query failed — skip cache, aggregate directly
            return _aggregate_all()

        result: List[Dict] = []
        for exp_id, new_count in counts.items():
            cached = _cache.get(exp_id, {})
            if cached.get("count") == new_count and "experiment" in cached:
                result.append(cached["experiment"])
            else:
                exp = _aggregate_experiment(exp_id)
                if exp:
                    with _cache_lock:
                        _cache[exp_id] = {
                            "count": new_count,
                            "experiment": exp,
                            "iterations": cached.get("iterations"),
                        }
                    result.append(exp)

        return result

    def get_experiment(self, experiment_id: str) -> Optional[Dict]:
        """Get a single experiment by ID."""
        try:
            rows = _traceql_query(
                f'{{experiment_id = "{experiment_id}"}} | select(count() as total) by (experiment_id)'
            )
            if not rows:
                return _aggregate_experiment(experiment_id)
            new_count = int(rows[0]["total"])
        except Exception:
            logger.warning(
                "count query failed for experiment %s, falling back to aggregate",
                experiment_id,
                exc_info=True,
            )
            new_count = None

        cached = _cache.get(experiment_id, {})
        if new_count is not None and cached.get("count") == new_count and "experiment" in cached:
            return cached["experiment"]

        exp = _aggregate_experiment(experiment_id)
        if exp and new_count is not None:
            with _cache_lock:
                _cache[experiment_id] = {
                    "count": new_count,
                    "experiment": exp,
                    "iterations": cached.get("iterations"),
                }
        return exp


class TraceQLIterationRepository:
    """IterationRepository backed by TraceQL distinct iteration queries."""

    def get_iterations(self, experiment_id: str) -> List[Dict]:
        """Get iteration list for an experiment.

        Returns lightweight dicts with iteration_num; other fields are empty
        (frontend only uses iteration_num for the filter dropdown).
        """
        try:
            count_rows = _traceql_query(
                f'{{experiment_id = "{experiment_id}"}} | select(count() as total) by (experiment_id)'
            )
            if not count_rows:
                new_count = None
            else:
                new_count = int(count_rows[0]["total"])
        except Exception:
            logger.warning(
                "count query failed for iterations of experiment %s, skipping cache",
                experiment_id,
                exc_info=True,
            )
            new_count = None

        cached = _cache.get(experiment_id, {})
        if new_count is not None and cached.get("count") == new_count and cached.get("iterations") is not None:
            return cached["iterations"]

        rows = _traceql_query(f'{{experiment_id = "{experiment_id}"}} | select(iteration) by (iteration)')
        iteration_nums = sorted({int(r["iteration"]) for r in rows if "iteration" in r})
        items = [
            {
                "id": f"iter-{n}",
                "experiment_id": experiment_id,
                "iteration_num": n,
                "metrics": {},
                "checkpoint": None,
            }
            for n in iteration_nums
        ]

        if new_count is not None:
            with _cache_lock:
                _cache[experiment_id] = {
                    "count": new_count,
                    "experiment": cached.get("experiment"),
                    "iterations": items,
                }
        return items

    def get_iteration(self, iteration_id: str) -> Optional[Dict]:
        """Not used by frontend — returns None."""
        return None
