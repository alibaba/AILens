"""Task effectiveness metric extractors.

Extractors for task-level effectiveness metrics.

Python 3.6.8 compatible.
"""

from ...mock import store
from .base import (
    _filter_iterations,
    _get_trajectories_for_iteration,
)

# ═══════════════════ Task Effectiveness Metrics (P0) ═══════════════════


def _extract_task_all_correct_rate(metric_name, experiment_id, labels_filter, iteration_range):
    # type: (str, str, Dict[str, str], Optional[Tuple[int, int]]) -> List[Dict]
    """Extract task all correct rate: tasks where ALL trajectories passed."""
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
        if not trajs:
            continue

        # Group by task_id
        task_stats = {}  # type: Dict[str, Dict[str, int]]
        for t in trajs:
            tid = t.get("task_id", "")
            if tid not in task_stats:
                task_stats[tid] = {"passed": 0, "total": 0}
            task_stats[tid]["total"] += 1
            if t.get("passed"):
                task_stats[tid]["passed"] += 1

        # Count tasks where all trajectories passed
        all_correct_count = sum(1 for stats in task_stats.values() if stats["passed"] == stats["total"])
        total_tasks = len(task_stats)
        if total_tasks == 0:
            continue

        rate = round(all_correct_count / total_tasks, 4)
        # Use iteration_num for x-axis
        x_val = it["iteration_num"]
        values.append([x_val, str(rate)])

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


def _extract_task_all_wrong_rate(metric_name, experiment_id, labels_filter, iteration_range):
    # type: (str, str, Dict[str, str], Optional[Tuple[int, int]]) -> List[Dict]
    """Extract task all wrong rate: tasks where NO trajectories passed."""
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
        if not trajs:
            continue

        # Group by task_id
        task_stats = {}  # type: Dict[str, Dict[str, int]]
        for t in trajs:
            tid = t.get("task_id", "")
            if tid not in task_stats:
                task_stats[tid] = {"passed": 0, "total": 0}
            task_stats[tid]["total"] += 1
            if t.get("passed"):
                task_stats[tid]["passed"] += 1

        # Count tasks where no trajectories passed
        all_wrong_count = sum(1 for stats in task_stats.values() if stats["passed"] == 0)
        total_tasks = len(task_stats)
        if total_tasks == 0:
            continue

        rate = round(all_wrong_count / total_tasks, 4)
        # Use iteration_num for x-axis
        x_val = it["iteration_num"]
        values.append([x_val, str(rate)])

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


def _extract_task_mixed_rate(metric_name, experiment_id, labels_filter, iteration_range):
    # type: (str, str, Dict[str, str], Optional[Tuple[int, int]]) -> List[Dict]
    """Extract task mixed rate: tasks with both passed and failed trajectories."""
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
        if not trajs:
            continue

        # Group by task_id
        task_stats = {}  # type: Dict[str, Dict[str, int]]
        for t in trajs:
            tid = t.get("task_id", "")
            if tid not in task_stats:
                task_stats[tid] = {"passed": 0, "total": 0}
            task_stats[tid]["total"] += 1
            if t.get("passed"):
                task_stats[tid]["passed"] += 1

        # Count tasks with mixed results (some passed, some failed)
        mixed_count = sum(
            1 for stats in task_stats.values() if stats["passed"] > 0 and stats["passed"] < stats["total"]
        )
        total_tasks = len(task_stats)

        if total_tasks == 0:
            continue

        rate = round(mixed_count / total_tasks, 4)
        # Use iteration_num for x-axis
        x_val = it["iteration_num"]
        values.append([x_val, str(rate)])

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
