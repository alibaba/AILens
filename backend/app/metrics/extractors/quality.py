"""Quality metric extractors.

Extractors for format correctness, repeat rates, and quality verification metrics.

Python 3.6.8 compatible.
"""

from ...mock import store
from .base import (
    _filter_iterations,
    _get_trajectories_for_iteration,
)

# ═══════════════════ Format Correct Rate extractor (TASK-029) ═══════════════════


def _extract_format_correct_rate_factory():
    # type: () -> Any
    """Factory: creates extractor for format_correct_rate metric."""

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
        split_by = labels_filter.get("split_by")

        if split_by == "scaffold":
            scaffolds = exp.get("config", {}).get("scaffolds", [])
            if scaffolds:
                result = []  # type: List[Dict]
                for sc in scaffolds:
                    series = _extract_format_correct_filtered(
                        metric_name,
                        experiment_id,
                        iterations,
                        sc,
                        language_filter,
                        system_prompt_filter,
                        tool_schema_filter,
                    )
                    result.extend(series)
                return result

        if split_by == "system_prompt":
            from ...mock import SYSTEM_PROMPTS

            result = []  # type: List[Dict]
            for sp in SYSTEM_PROMPTS:
                series = _extract_format_correct_filtered(
                    metric_name,
                    experiment_id,
                    iterations,
                    scaffold_filter,
                    language_filter,
                    sp,
                    tool_schema_filter,
                )
                result.extend(series)
            return result

        if split_by == "tool_schema":
            from ...mock import TOOL_SCHEMAS

            result = []  # type: List[Dict]
            for ts_val in TOOL_SCHEMAS:
                series = _extract_format_correct_filtered(
                    metric_name,
                    experiment_id,
                    iterations,
                    scaffold_filter,
                    language_filter,
                    system_prompt_filter,
                    ts_val,
                )
                result.extend(series)
            return result

        return _extract_format_correct_filtered(
            metric_name,
            experiment_id,
            iterations,
            scaffold_filter,
            language_filter,
            system_prompt_filter,
            tool_schema_filter,
        )

    return extractor


def _extract_format_correct_filtered(
    metric_name,
    experiment_id,
    iterations,
    scaffold_filter,
    language_filter,
    system_prompt_filter,
    tool_schema_filter,
):
    # type: (str, str, List[Dict], Optional[str], Optional[str], Optional[str], Optional[str]) -> List[Dict]
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

        n = len(trajs)
        fc_count = sum(1 for t in trajs if t.get("format_correct", False))
        # Use iteration_num for x-axis
        x_val = it["iteration_num"]
        values.append([x_val, str(round(fc_count / n, 4))])

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


# ═══════════════════ Repeat Rate extractors (TASK-031) ═══════════════════


def _extract_repeat_rate_factory(field_name):
    # type: (str) -> Any
    """Factory: creates extractor for repeat_tool_call_rate or repeat_response_rate."""

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
            if not trajs:
                continue

            n = len(trajs)
            affected = sum(1 for t in trajs if t.get(field_name, 0) > 0)
            # Use iteration_num for x-axis
            x_val = it["iteration_num"]
            values.append([x_val, str(round(affected / n, 4))])

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


# ═══════════════════ Quality Verification Metrics (P2) ═══════════════════


def _extract_stop_reason_rate(metric_name, experiment_id, labels_filter, iteration_range):
    # type: (str, str, Dict[str, str], Optional[Tuple[int, int]]) -> List[Dict]
    """Extract stop reason rate: distribution by exec_result (outcome in mock data).

    Returns one series per unique exec_result value.
    """
    exp = store.get_experiment(experiment_id)
    if not exp:
        return []

    iterations = _filter_iterations(experiment_id, iteration_range)
    scaffold_filter = labels_filter.get("scaffold")
    language_filter = labels_filter.get("language")
    system_prompt_filter = labels_filter.get("system_prompt")
    tool_schema_filter = labels_filter.get("tool_schema")

    # Group by exec_result (outcome), then by iteration
    # Structure: {exec_result: {iteration_num: count, total_per_iter}}
    result_data = {}  # type: Dict[str, Dict[int, Dict[str, int]]]

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

        # Use iteration_num for x-axis
        x_val = it["iteration_num"]
        total_count = len(trajs)

        # Count by outcome (mapped to exec_result)
        for t in trajs:
            # Map outcome to exec_result
            # In mock data: outcome is "success"/"failure"/"timeout"/"error"
            # exec_result values: success/max_turns/error/timeout/finish/Unknown/etc
            outcome = t.get("outcome", "Unknown")
            exec_result = outcome  # Use outcome directly as exec_result

            if exec_result not in result_data:
                result_data[exec_result] = {}
            if x_val not in result_data[exec_result]:
                result_data[exec_result][x_val] = {"count": 0, "total": 0}
            result_data[exec_result][x_val]["count"] += 1
            result_data[exec_result][x_val]["total"] = total_count

    if not result_data:
        return []

    # Build result series - one per exec_result value
    result = []  # type: List[Dict]
    for exec_result in sorted(result_data.keys()):
        values = []  # type: List[List]
        for x_val, data in sorted(result_data[exec_result].items()):
            if data["total"] > 0:
                rate = round(data["count"] / data["total"], 4)
                values.append([x_val, str(rate)])

        if values:
            metric_labels = {
                "__name__": metric_name,
                "experiment_id": experiment_id,
                "exec_result": exec_result,
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


def _extract_reward_range(metric_name, experiment_id, labels_filter, iteration_range):
    # type: (str, str, Dict[str, str], Optional[Tuple[int, int]]) -> List[Dict]
    """Extract reward range: max(reward) - min(reward) per iteration."""
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

        rewards = [t.get("reward", 0) for t in trajs]
        if not rewards:
            continue

        reward_range = round(max(rewards) - min(rewards), 4)
        # Use iteration_num for x-axis
        x_val = it["iteration_num"]
        values.append([x_val, str(reward_range)])

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
