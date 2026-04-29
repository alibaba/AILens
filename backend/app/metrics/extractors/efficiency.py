"""Efficiency metric extractors.

Extractors for success turns and efficiency-related metrics.

Python 3.6.8 compatible.
"""

from ...mock import store
from .base import (
    _filter_iterations,
    _get_trajectories_for_iteration,
)

# ═══════════════════ Success Turns PromQL extractors ═══════════════════

# Bucket boundaries for success turns histogram
SUCCESS_TURNS_BUCKETS = [1, 3, 5, 7, 10, 12, 15, 17, 20, float("inf")]


def _extract_success_turns_stat(stat_type):
    # type: (str) -> Any
    """Factory: creates extractor for success trajectory turns statistics.

    stat_type: 'mean', 'p90', or 'p99'
    """

    def extractor(metric_name, experiment_id, labels_filter, iteration_range):
        # type: (str, str, Dict[str, str], Optional[Tuple[int, int]]) -> List[Dict]
        exp = store.get_experiment(experiment_id)
        if not exp:
            return []

        iterations = _filter_iterations(experiment_id, iteration_range)
        scaffold_filter = labels_filter.get("scaffold")
        language_filter = labels_filter.get("language")
        system_prompt_filter = labels_filter.get("system_prompt")
        tool_schema_filter = labels_filter.get("tool_schema")

        values = []  # type: List[List]
        for it in iterations:
            trajs = _get_trajectories_for_iteration(experiment_id, it["iteration_num"])
            if scaffold_filter:
                trajs = [t for t in trajs if t.get("scaffold") == scaffold_filter]
            if language_filter:
                trajs = [t for t in trajs if t.get("task_language") == language_filter]
            if system_prompt_filter:
                trajs = [t for t in trajs if t.get("system_prompt") == system_prompt_filter]
            if tool_schema_filter:
                trajs = [t for t in trajs if t.get("tool_schema") == tool_schema_filter]

            success_trajs = [t for t in trajs if t.get("passed")]
            if not success_trajs:
                continue

            turns = sorted([t["total_turns"] for t in success_trajs])
            n = len(turns)
            # Use iteration_num for x-axis (success turns is not a duration metric)
            x_val = it["iteration_num"]

            if stat_type == "mean":
                val = round(sum(turns) / n, 1)
            elif stat_type == "p90":
                val = turns[min(n - 1, int(n * 0.90))]
            elif stat_type == "p99":
                val = turns[min(n - 1, int(n * 0.99))]
            else:
                continue

            values.append([x_val, str(val)])

        if not values:
            return []

        metric_labels = {
            "__name__": metric_name,
            "experiment_id": experiment_id,
            "x_axis_type": "iteration",
        }
        if scaffold_filter:
            metric_labels["scaffold"] = scaffold_filter
        if language_filter:
            metric_labels["language"] = language_filter
        if system_prompt_filter:
            metric_labels["system_prompt"] = system_prompt_filter
        if tool_schema_filter:
            metric_labels["tool_schema"] = tool_schema_filter

        return [
            {
                "metric": metric_labels,
                "values": values,
            }
        ]

    return extractor


def _extract_success_turns_count(metric_name, experiment_id, labels_filter, iteration_range):
    # type: (str, str, Dict[str, str], Optional[Tuple[int, int]]) -> List[Dict]
    """Extract count of successful trajectories."""
    return _extract_success_turns_agg(metric_name, experiment_id, labels_filter, iteration_range, "count")


def _extract_success_turns_min(metric_name, experiment_id, labels_filter, iteration_range):
    # type: (str, str, Dict[str, str], Optional[Tuple[int, int]]) -> List[Dict]
    """Extract min turns of successful trajectories."""
    return _extract_success_turns_agg(metric_name, experiment_id, labels_filter, iteration_range, "min")


def _extract_success_turns_max(metric_name, experiment_id, labels_filter, iteration_range):
    # type: (str, str, Dict[str, str], Optional[Tuple[int, int]]) -> List[Dict]
    """Extract max turns of successful trajectories."""
    return _extract_success_turns_agg(metric_name, experiment_id, labels_filter, iteration_range, "max")


def _extract_success_turns_sum(metric_name, experiment_id, labels_filter, iteration_range):
    # type: (str, str, Dict[str, str], Optional[Tuple[int, int]]) -> List[Dict]
    """Extract sum of turns of successful trajectories."""
    return _extract_success_turns_agg(metric_name, experiment_id, labels_filter, iteration_range, "sum")


def _extract_success_turns_agg(metric_name, experiment_id, labels_filter, iteration_range, agg_type):
    # type: (str, str, Dict[str, str], Optional[Tuple[int, int]], str) -> List[Dict]
    """Generic aggregator for success turns statistics.

    agg_type: 'count', 'min', 'max', 'sum'
    """
    exp = store.get_experiment(experiment_id)
    if not exp:
        return []

    iterations = _filter_iterations(experiment_id, iteration_range)
    scaffold_filter = labels_filter.get("scaffold")
    language_filter = labels_filter.get("language")
    system_prompt_filter = labels_filter.get("system_prompt")
    tool_schema_filter = labels_filter.get("tool_schema")

    values = []  # type: List[List]
    for it in iterations:
        trajs = _get_trajectories_for_iteration(experiment_id, it["iteration_num"])
        if scaffold_filter:
            trajs = [t for t in trajs if t.get("scaffold") == scaffold_filter]
        if language_filter:
            trajs = [t for t in trajs if t.get("task_language") == language_filter]
        if system_prompt_filter:
            trajs = [t for t in trajs if t.get("system_prompt") == system_prompt_filter]
        if tool_schema_filter:
            trajs = [t for t in trajs if t.get("tool_schema") == tool_schema_filter]

        success_trajs = [t for t in trajs if t.get("passed")]
        if not success_trajs:
            continue

        turns = [t["total_turns"] for t in success_trajs]
        n = len(turns)
        # Use iteration_num for x-axis
        x_val = it["iteration_num"]

        if agg_type == "count":
            val = n
        elif agg_type == "min":
            val = min(turns)
        elif agg_type == "max":
            val = max(turns)
        elif agg_type == "sum":
            val = sum(turns)
        else:
            continue

        values.append([x_val, str(val)])

    if not values:
        return []

    metric_labels = {
        "__name__": metric_name,
        "experiment_id": experiment_id,
        "x_axis_type": "iteration",
    }
    if scaffold_filter:
        metric_labels["scaffold"] = scaffold_filter
    if language_filter:
        metric_labels["language"] = language_filter
    if system_prompt_filter:
        metric_labels["system_prompt"] = system_prompt_filter
    if tool_schema_filter:
        metric_labels["tool_schema"] = tool_schema_filter

    return [
        {
            "metric": metric_labels,
            "values": values,
        }
    ]


def _extract_success_turns_bucket(metric_name, experiment_id, labels_filter, iteration_range):
    # type: (str, str, Dict[str, str], Optional[Tuple[int, int]]) -> List[Dict]
    """Extract histogram buckets for success trajectory turns distribution."""
    exp = store.get_experiment(experiment_id)
    if not exp:
        return []

    iterations = _filter_iterations(experiment_id, iteration_range)
    scaffold_filter = labels_filter.get("scaffold")
    language_filter = labels_filter.get("language")
    system_prompt_filter = labels_filter.get("system_prompt")
    tool_schema_filter = labels_filter.get("tool_schema")

    # Return one series per bucket (le label)
    bucket_series = {}  # type: Dict[str, List[List]]
    for bucket_le in SUCCESS_TURNS_BUCKETS:
        bucket_key = str(bucket_le) if bucket_le != float("inf") else "+Inf"
        bucket_series[bucket_key] = []

    for it in iterations:
        trajs = _get_trajectories_for_iteration(experiment_id, it["iteration_num"])
        if scaffold_filter:
            trajs = [t for t in trajs if t.get("scaffold") == scaffold_filter]
        if language_filter:
            trajs = [t for t in trajs if t.get("task_language") == language_filter]
        if system_prompt_filter:
            trajs = [t for t in trajs if t.get("system_prompt") == system_prompt_filter]
        if tool_schema_filter:
            trajs = [t for t in trajs if t.get("tool_schema") == tool_schema_filter]

        success_trajs = [t for t in trajs if t.get("passed")]
        # Use iteration_num for x-axis
        x_val = it["iteration_num"]

        # Count cumulative for each bucket
        turns = [t["total_turns"] for t in success_trajs]
        for bucket_le in SUCCESS_TURNS_BUCKETS:
            bucket_key = str(bucket_le) if bucket_le != float("inf") else "+Inf"
            cumulative = sum(1 for t in turns if t <= bucket_le)
            bucket_series[bucket_key].append([x_val, str(cumulative)])

    if not any(bucket_series.values()):
        return []

    result = []  # type: List[Dict]
    for bucket_key, values in bucket_series.items():
        if not values:
            continue
        metric_labels = {
            "__name__": metric_name,
            "experiment_id": experiment_id,
            "le": bucket_key,
            "x_axis_type": "iteration",
        }
        if scaffold_filter:
            metric_labels["scaffold"] = scaffold_filter
        if language_filter:
            metric_labels["language"] = language_filter
        if system_prompt_filter:
            metric_labels["system_prompt"] = system_prompt_filter
        if tool_schema_filter:
            metric_labels["tool_schema"] = tool_schema_filter

        result.append(
            {
                "metric": metric_labels,
                "values": values,
            }
        )

    return result
