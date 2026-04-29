"""Turn analysis metric extractors.

Extractors for turn-level analysis metrics.

Python 3.6.8 compatible.
"""

from ...mock import store
from .base import (
    _filter_iterations,
    _get_trajectories_for_iteration,
    _ts_epoch,
)

# ═══════════════════ Turn Analysis PromQL extractors ═══════════════════


def _extract_turns_count(metric_name, experiment_id, labels_filter, iteration_range):
    # type: (str, str, Dict[str, str], Optional[Tuple[int, int]]) -> List[Dict]
    """Extract total trajectory count grouped by total_turns.

    Returns one series per unique total_turns value.
    """
    exp = store.get_experiment(experiment_id)
    if not exp:
        return []

    iterations = _filter_iterations(experiment_id, iteration_range)
    scaffold_filter = labels_filter.get("scaffold")
    language_filter = labels_filter.get("language")
    system_prompt_filter = labels_filter.get("system_prompt")
    tool_schema_filter = labels_filter.get("tool_schema")

    # Group by total_turns, then by timestamp
    # Structure: {total_turns: {timestamp: count}}
    turn_data = {}  # type: Dict[int, Dict[float, int]]

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

        ts = _ts_epoch(it["timestamp"])
        for t in trajs:
            turns = t.get("total_turns", 0)
            if turns not in turn_data:
                turn_data[turns] = {}
            if ts not in turn_data[turns]:
                turn_data[turns][ts] = 0
            turn_data[turns][ts] += 1

    if not turn_data:
        return []

    # Build result series - one per total_turns value
    result = []  # type: List[Dict]
    for turns in sorted(turn_data.keys()):
        values = [[ts, str(count)] for ts, count in sorted(turn_data[turns].items())]
        if values:
            result.append(
                {
                    "metric": {
                        "__name__": metric_name,
                        "experiment_id": experiment_id,
                        "total_turns": str(turns),
                    },
                    "values": values,
                }
            )

    return result


def _extract_turns_passed_count(metric_name, experiment_id, labels_filter, iteration_range):
    # type: (str, str, Dict[str, str], Optional[Tuple[int, int]]) -> List[Dict]
    """Extract passed trajectory count grouped by total_turns.

    Returns one series per unique total_turns value.
    """
    exp = store.get_experiment(experiment_id)
    if not exp:
        return []

    iterations = _filter_iterations(experiment_id, iteration_range)
    scaffold_filter = labels_filter.get("scaffold")
    language_filter = labels_filter.get("language")
    system_prompt_filter = labels_filter.get("system_prompt")
    tool_schema_filter = labels_filter.get("tool_schema")

    # Group by total_turns, then by timestamp
    turn_data = {}  # type: Dict[int, Dict[float, int]]

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

        ts = _ts_epoch(it["timestamp"])
        for t in trajs:
            if not t.get("passed"):
                continue
            turns = t.get("total_turns", 0)
            if turns not in turn_data:
                turn_data[turns] = {}
            if ts not in turn_data[turns]:
                turn_data[turns][ts] = 0
            turn_data[turns][ts] += 1

    if not turn_data:
        return []

    # Build result series - one per total_turns value
    result = []  # type: List[Dict]
    for turns in sorted(turn_data.keys()):
        values = [[ts, str(count)] for ts, count in sorted(turn_data[turns].items())]
        if values:
            result.append(
                {
                    "metric": {
                        "__name__": metric_name,
                        "experiment_id": experiment_id,
                        "total_turns": str(turns),
                    },
                    "values": values,
                }
            )

    return result


def _extract_turns_duration_max(metric_name, experiment_id, labels_filter, iteration_range):
    # type: (str, str, Dict[str, str], Optional[Tuple[int, int]]) -> List[Dict]
    """Extract max duration of passed trajectories grouped by total_turns.

    Returns one series per unique total_turns value.
    """
    exp = store.get_experiment(experiment_id)
    if not exp:
        return []

    iterations = _filter_iterations(experiment_id, iteration_range)
    scaffold_filter = labels_filter.get("scaffold")
    language_filter = labels_filter.get("language")
    system_prompt_filter = labels_filter.get("system_prompt")
    tool_schema_filter = labels_filter.get("tool_schema")

    # Group by total_turns, then by timestamp
    turn_data = {}  # type: Dict[int, Dict[float, List[int]]]

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

        ts = _ts_epoch(it["timestamp"])
        for t in trajs:
            if not t.get("passed"):
                continue
            turns = t.get("total_turns", 0)
            duration = t.get("duration_ms", 0)
            if turns not in turn_data:
                turn_data[turns] = {}
            if ts not in turn_data[turns]:
                turn_data[turns][ts] = []
            turn_data[turns][ts].append(duration)

    if not turn_data:
        return []

    # Build result series - one per total_turns value
    result = []  # type: List[Dict]
    for turns in sorted(turn_data.keys()):
        values = []
        for ts, durations in sorted(turn_data[turns].items()):
            if durations:
                values.append([ts, str(max(durations))])
        if values:
            result.append(
                {
                    "metric": {
                        "__name__": metric_name,
                        "experiment_id": experiment_id,
                        "total_turns": str(turns),
                    },
                    "values": values,
                }
            )

    return result


def _extract_turns_duration_sum(metric_name, experiment_id, labels_filter, iteration_range):
    # type: (str, str, Dict[str, str], Optional[Tuple[int, int]]) -> List[Dict]
    """Extract sum of durations of passed trajectories grouped by total_turns.

    Returns one series per unique total_turns value.
    """
    exp = store.get_experiment(experiment_id)
    if not exp:
        return []

    iterations = _filter_iterations(experiment_id, iteration_range)
    scaffold_filter = labels_filter.get("scaffold")
    language_filter = labels_filter.get("language")
    system_prompt_filter = labels_filter.get("system_prompt")
    tool_schema_filter = labels_filter.get("tool_schema")

    # Group by total_turns, then by timestamp
    turn_data = {}  # type: Dict[int, Dict[float, int]]

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

        ts = _ts_epoch(it["timestamp"])
        for t in trajs:
            if not t.get("passed"):
                continue
            turns = t.get("total_turns", 0)
            duration = t.get("duration_ms", 0)
            if turns not in turn_data:
                turn_data[turns] = {}
            if ts not in turn_data[turns]:
                turn_data[turns][ts] = 0
            turn_data[turns][ts] += duration

    if not turn_data:
        return []

    # Build result series - one per total_turns value
    result = []  # type: List[Dict]
    for turns in sorted(turn_data.keys()):
        values = [[ts, str(sum_val)] for ts, sum_val in sorted(turn_data[turns].items())]
        if values:
            result.append(
                {
                    "metric": {
                        "__name__": metric_name,
                        "experiment_id": experiment_id,
                        "total_turns": str(turns),
                    },
                    "values": values,
                }
            )

    return result


def _extract_turns_duration_count(metric_name, experiment_id, labels_filter, iteration_range):
    # type: (str, str, Dict[str, str], Optional[Tuple[int, int]]) -> List[Dict]
    """Extract count of passed trajectories for duration calculation grouped by total_turns.

    Returns one series per unique total_turns value.
    """
    exp = store.get_experiment(experiment_id)
    if not exp:
        return []

    iterations = _filter_iterations(experiment_id, iteration_range)
    scaffold_filter = labels_filter.get("scaffold")
    language_filter = labels_filter.get("language")
    system_prompt_filter = labels_filter.get("system_prompt")
    tool_schema_filter = labels_filter.get("tool_schema")

    # Group by total_turns, then by timestamp
    turn_data = {}  # type: Dict[int, Dict[float, int]]

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

        ts = _ts_epoch(it["timestamp"])
        for t in trajs:
            if not t.get("passed"):
                continue
            turns = t.get("total_turns", 0)
            if turns not in turn_data:
                turn_data[turns] = {}
            if ts not in turn_data[turns]:
                turn_data[turns][ts] = 0
            turn_data[turns][ts] += 1

    if not turn_data:
        return []

    # Build result series - one per total_turns value
    result = []  # type: List[Dict]
    for turns in sorted(turn_data.keys()):
        values = [[ts, str(count)] for ts, count in sorted(turn_data[turns].items())]
        if values:
            result.append(
                {
                    "metric": {
                        "__name__": metric_name,
                        "experiment_id": experiment_id,
                        "total_turns": str(turns),
                    },
                    "values": values,
                }
            )

    return result
