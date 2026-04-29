"""SQL-based metric extractors for high performance aggregation.

Direct SQL queries replace in-memory trajectory processing.
Python 3.6.8 compatible.
"""

from ...mock import store


def create_sql_aggregated_extractor(aggregation_func, metric_field=None, condition=None):
    # type: (str, Optional[str], Optional[str]) -> Any
    """Factory to create SQL-based metric extractors.

    Args:
        aggregation_func: SQL aggregation function (COUNT, AVG, SUM, etc.)
        metric_field: Field name to aggregate (for AVG, SUM)
        condition: Additional WHERE condition (for filtered counts)

    Returns:
        Extractor function that uses direct SQL aggregation
    """

    def extractor(metric_name, experiment_id, labels_filter, iteration_range):
        # type: (str, str, Dict[str, str], Optional[Tuple[int, int]]) -> List[Dict]

        # Check if we need to split by dimensions
        split_by = labels_filter.get("split_by")
        if split_by and split_by in ["scaffold", "tool_schema", "language", "system_prompt"]:
            # For split queries, group by the split dimension
            return _execute_split_query(
                aggregation_func,
                metric_field,
                condition,
                metric_name,
                experiment_id,
                labels_filter,
                iteration_range,
                split_by,
            )

        # For non-split queries, aggregate across all dimensions
        # This is more accurate for AVG calculations
        sql_parts = ["SELECT iteration_num"]

        # Add aggregation expression
        if metric_field:
            sql_parts.append(", {}({}) as metric_value".format(aggregation_func, metric_field))
        else:
            sql_parts.append(", {}(*) as metric_value".format(aggregation_func))

        sql_parts.extend(["FROM trajectories", "WHERE experiment_id = ?"])

        # Add additional condition if specified
        params = [experiment_id]
        if condition:
            sql_parts.append("AND {}".format(condition))

        # Add labels filters
        if labels_filter.get("scaffold"):
            sql_parts.append("AND scaffold = ?")
            params.append(labels_filter["scaffold"])
        if labels_filter.get("tool_schema"):
            sql_parts.append("AND tool_schema = ?")
            params.append(labels_filter["tool_schema"])
        if labels_filter.get("language"):
            sql_parts.append("AND task_language = ?")
            params.append(labels_filter["language"])
        if labels_filter.get("system_prompt"):
            sql_parts.append("AND system_prompt = ?")
            params.append(labels_filter["system_prompt"])

        # Add iteration range filter
        if iteration_range:
            lo, hi = iteration_range
            sql_parts.append("AND iteration_num BETWEEN ? AND ?")
            params.extend([lo, hi])

        # Group only by iteration_num for accurate aggregation
        sql_parts.extend(["GROUP BY iteration_num", "ORDER BY iteration_num"])

        sql = " ".join(sql_parts)

        # Execute SQL query
        rows = store.execute_sql(sql, params)

        # Convert results to metric format (simpler format for non-split queries)
        return _convert_simple_sql_results_to_metrics(rows, metric_name, experiment_id, labels_filter)

    # Set a descriptive name for the function to help with testing
    extractor.__name__ = "sql_extractor_{}".format(aggregation_func.lower())
    return extractor


def _execute_split_query(
    aggregation_func, metric_field, condition, metric_name, experiment_id, labels_filter, iteration_range, split_by
):
    # type: (str, Optional[str], Optional[str], str, str, Dict[str, str], Optional[Tuple[int, int]], str) -> List[Dict]
    """Execute split query that groups by the split dimension."""
    sql_parts = ["SELECT", "  {},".format(split_by), "  iteration_num,"]

    # Add aggregation expression
    if metric_field:
        sql_parts.append("  {}({}) as metric_value".format(aggregation_func, metric_field))
    else:
        sql_parts.append("  {}(*) as metric_value".format(aggregation_func))

    sql_parts.extend(["FROM trajectories", "WHERE experiment_id = ?"])

    # Add additional condition if specified
    params = [experiment_id]
    if condition:
        sql_parts.append("AND {}".format(condition))

    # Add labels filters (exclude the split_by dimension)
    for key in ["scaffold", "tool_schema", "language", "system_prompt"]:
        if key != split_by and labels_filter.get(key):
            # Map 'language' to 'task_language' in SQL
            sql_field = "task_language" if key == "language" else key
            sql_parts.append("AND {} = ?".format(sql_field))
            params.append(labels_filter[key])

    # Add iteration range filter
    if iteration_range:
        lo, hi = iteration_range
        sql_parts.append("AND iteration_num BETWEEN ? AND ?")
        params.extend([lo, hi])

    # Group by split dimension and iteration_num
    sql_parts.extend(["GROUP BY {}, iteration_num".format(split_by), "ORDER BY iteration_num, {}".format(split_by)])

    sql = " ".join(sql_parts)

    # Execute SQL query
    rows = store.execute_sql(sql, params)

    # Convert results to metric format for split queries
    return _convert_split_sql_results_to_metrics(rows, metric_name, experiment_id, split_by)


def _convert_simple_sql_results_to_metrics(rows, metric_name, experiment_id, labels_filter):
    # type: (List[Tuple], str, str, Dict[str, str]) -> List[Dict]
    """Convert simple SQL query results (iteration_num, metric_value) to standard metric format."""
    if not rows:
        return []

    metric_labels = {
        "__name__": metric_name,
        "experiment_id": experiment_id,
        "x_axis_type": "iteration",
    }

    # Add filter labels to metric labels
    for key in ["scaffold", "tool_schema", "language", "system_prompt"]:
        if labels_filter.get(key):
            metric_labels[key] = labels_filter[key]

    # Convert to values format
    values = []  # type: List[List]
    for row in rows:
        iteration_num, metric_value = row
        # Format integer values properly (e.g., COUNT results)
        if isinstance(metric_value, float) and metric_value.is_integer():
            formatted_val = str(int(metric_value))
        else:
            formatted_val = str(metric_value)
        values.append([iteration_num, formatted_val])

    return [
        {
            "metric": metric_labels,
            "values": values,
        }
    ]


def _convert_sql_results_to_metrics(rows, metric_name, experiment_id, labels_filter):
    # type: (List[Tuple], str, str, Dict[str, str]) -> List[Dict]
    """Convert SQL query results to standard metric format."""
    if not rows:
        return []

    metric_labels = {
        "__name__": metric_name,
        "experiment_id": experiment_id,
        "x_axis_type": "iteration",
    }

    # Add filter labels to metric labels
    for key in ["scaffold", "tool_schema", "language", "system_prompt"]:
        if labels_filter.get(key):
            metric_labels[key] = labels_filter[key]

    # Check if we need to split by dimensions
    split_by = labels_filter.get("split_by")
    if split_by and split_by in ["scaffold", "tool_schema", "language", "system_prompt"]:
        return _convert_split_results(rows, metric_name, experiment_id, split_by)

    # Aggregate results (sum across dimensions for same iteration)
    iteration_values = {}  # type: Dict[int, float]
    for row in rows:
        scaffold, tool_schema, language, system_prompt, iteration_num, metric_value = row
        if iteration_num not in iteration_values:
            iteration_values[iteration_num] = 0
        iteration_values[iteration_num] += metric_value

    # Convert to values format
    values = []  # type: List[List]
    for iteration_num in sorted(iteration_values.keys()):
        # Format integer values properly (e.g., COUNT results)
        val = iteration_values[iteration_num]
        if isinstance(val, float) and val.is_integer():
            formatted_val = str(int(val))
        else:
            formatted_val = str(val)
        values.append([iteration_num, formatted_val])

    return [
        {
            "metric": metric_labels,
            "values": values,
        }
    ]


def _convert_split_sql_results_to_metrics(rows, metric_name, experiment_id, split_by):
    # type: (List[Tuple], str, str, str) -> List[Dict]
    """Convert split SQL query results (split_value, iteration_num, metric_value) to standard metric format."""
    if not rows:
        return []

    # Group by split dimension
    split_results = {}  # type: Dict[str, Dict[int, float]]
    for row in rows:
        split_value, iteration_num, metric_value = row

        if split_value not in split_results:
            split_results[split_value] = {}
        split_results[split_value][iteration_num] = metric_value

    # Convert to metric format
    results = []  # type: List[Dict]
    for split_value, iterations in split_results.items():
        values = []  # type: List[List]
        for iteration_num in sorted(iterations.keys()):
            # Format integer values properly (e.g., COUNT results)
            val = iterations[iteration_num]
            if isinstance(val, float) and val.is_integer():
                formatted_val = str(int(val))
            else:
                formatted_val = str(val)
            values.append([iteration_num, formatted_val])

        metric_labels = {
            "__name__": metric_name,
            "experiment_id": experiment_id,
            "x_axis_type": "iteration",
            split_by: split_value,
        }

        results.append(
            {
                "metric": metric_labels,
                "values": values,
            }
        )

    return results


def _convert_split_results(rows, metric_name, experiment_id, split_by):
    # type: (List[Tuple], str, str, str) -> List[Dict]
    """Convert results when split_by dimension is specified (legacy format)."""
    # Group by split dimension
    split_results = {}  # type: Dict[str, Dict[int, float]]
    for row in rows:
        scaffold, tool_schema, language, system_prompt, iteration_num, metric_value = row

        # Get split value
        if split_by == "scaffold":
            split_value = scaffold
        elif split_by == "tool_schema":
            split_value = tool_schema
        elif split_by == "language":
            split_value = language
        elif split_by == "system_prompt":
            split_value = system_prompt
        else:
            continue

        if split_value not in split_results:
            split_results[split_value] = {}
        if iteration_num not in split_results[split_value]:
            split_results[split_value][iteration_num] = 0
        split_results[split_value][iteration_num] += metric_value

    # Convert to metric format
    results = []  # type: List[Dict]
    for split_value, iterations in split_results.items():
        values = []  # type: List[List]
        for iteration_num in sorted(iterations.keys()):
            # Format integer values properly (e.g., COUNT results)
            val = iterations[iteration_num]
            if isinstance(val, float) and val.is_integer():
                formatted_val = str(int(val))
            else:
                formatted_val = str(val)
            values.append([iteration_num, formatted_val])

        metric_labels = {
            "__name__": metric_name,
            "experiment_id": experiment_id,
            "x_axis_type": "iteration",
            split_by: split_value,
        }

        results.append(
            {
                "metric": metric_labels,
                "values": values,
            }
        )

    return results


# ═══════════════════ Specific Metric Extractors ═══════════════════

# COUNT(*) metrics
extract_trajectory_count_sql = create_sql_aggregated_extractor("COUNT")
extract_passed_count_sql = create_sql_aggregated_extractor("COUNT", condition="passed = true")
extract_failed_count_sql = create_sql_aggregated_extractor("COUNT", condition="passed = false")

# AVG metrics
extract_reward_avg_sql = create_sql_aggregated_extractor("AVG", "reward")
extract_turns_avg_sql = create_sql_aggregated_extractor("AVG", "total_turns")


def extract_duration_avg_sql(metric_name, experiment_id, labels_filter, iteration_range):
    # type: (str, str, Dict[str, str], Optional[Tuple[int, int]]) -> List[Dict]
    """Extract average duration, converting ms to seconds."""
    base_extractor = create_sql_aggregated_extractor("AVG", "duration_ms")
    results = base_extractor(metric_name, experiment_id, labels_filter, iteration_range)

    # Convert ms to seconds
    for result in results:
        for value_pair in result["values"]:
            # value_pair is [iteration_num, duration_ms_str]
            duration_ms = float(value_pair[1])
            duration_seconds = duration_ms / 1000.0
            value_pair[1] = str(round(duration_seconds, 2))  # Round to 2 decimals for seconds

    return results


# SUM metrics
extract_turns_sum_sql = create_sql_aggregated_extractor("SUM", "total_turns")


def extract_duration_sum_sql(metric_name, experiment_id, labels_filter, iteration_range):
    # type: (str, str, Dict[str, str], Optional[Tuple[int, int]]) -> List[Dict]
    """Extract sum duration, converting ms to seconds."""
    base_extractor = create_sql_aggregated_extractor("SUM", "duration_ms")
    results = base_extractor(metric_name, experiment_id, labels_filter, iteration_range)

    # Convert ms to seconds
    for result in results:
        for value_pair in result["values"]:
            # value_pair is [iteration_num, duration_ms_str]
            duration_ms = float(value_pair[1])
            duration_seconds = duration_ms / 1000.0
            value_pair[1] = str(round(duration_seconds, 2))  # Round to 2 decimals for seconds

    return results


# MIN/MAX metrics
extract_turns_min_sql = create_sql_aggregated_extractor("MIN", "total_turns")
extract_turns_max_sql = create_sql_aggregated_extractor("MAX", "total_turns")
extract_reward_min_sql = create_sql_aggregated_extractor("MIN", "reward")
extract_reward_max_sql = create_sql_aggregated_extractor("MAX", "reward")


# Standard deviation (using database functions if available)
def extract_reward_stddev_sql(metric_name, experiment_id, labels_filter, iteration_range):
    # type: (str, str, Dict[str, str], Optional[Tuple[int, int]]) -> List[Dict]
    """Extract reward standard deviation using SQL."""
    # Use database STDDEV function or calculate manually
    extractor = create_sql_aggregated_extractor("STDDEV", "reward")
    return extractor(metric_name, experiment_id, labels_filter, iteration_range)


# Token metrics
extract_input_tokens_sum_sql = create_sql_aggregated_extractor("SUM", "input_tokens")
extract_output_tokens_sum_sql = create_sql_aggregated_extractor("SUM", "output_tokens")


def extract_tokens_per_trajectory_avg_sql(metric_name, experiment_id, labels_filter, iteration_range):
    # type: (str, str, Dict[str, str], Optional[Tuple[int, int]]) -> List[Dict]
    """Extract average tokens per trajectory using SQL."""
    extractor = create_sql_aggregated_extractor("AVG", "total_tokens")
    return extractor(metric_name, experiment_id, labels_filter, iteration_range)


# Duration metrics
extract_sandbox_duration_avg_sql = create_sql_aggregated_extractor("AVG", "sandbox_create_duration_ms")
extract_verify_duration_avg_sql = create_sql_aggregated_extractor("AVG", "verify_duration_ms")


# Pass rate - calculated as (passed_count / trajectory_count)
def extract_pass_rate_sql(metric_name, experiment_id, labels_filter, iteration_range):
    # type: (str, str, Dict[str, str], Optional[Tuple[int, int]]) -> List[Dict]
    """Extract pass rate using SQL aggregation."""
    # Calculate as AVG(CASE WHEN passed THEN 1.0 ELSE 0.0 END)
    from ...mock import store

    # Build WHERE conditions
    conditions = ["experiment_id = ?"]
    params = [experiment_id]

    # Add iteration range filtering
    if iteration_range:
        start_iter, end_iter = iteration_range
        conditions.append("iteration_num BETWEEN ? AND ?")
        params.extend([start_iter, end_iter])

    # Add label filters
    for label_key in ["scaffold", "tool_schema", "language", "system_prompt"]:
        if label_key == "language":
            db_field = "task_language"
        else:
            db_field = label_key
        if label_key in labels_filter:
            conditions.append("{} = ?".format(db_field))
            params.append(labels_filter[label_key])

    # Check for split_by
    split_by = labels_filter.get("split_by")
    if split_by:
        # Handle split queries
        if split_by == "language":
            db_field = "task_language"
        else:
            db_field = split_by
        sql = "SELECT {}, iteration_num, AVG(CASE WHEN passed THEN 1.0 ELSE 0.0 END) FROM trajectories WHERE {} GROUP BY {}, iteration_num ORDER BY iteration_num, {}".format(
            db_field, " AND ".join(conditions), db_field, db_field
        )
        rows = store.execute_sql(sql, params)
        return _convert_split_sql_results_to_metrics(rows, metric_name, experiment_id, split_by)
    else:
        sql = "SELECT iteration_num, AVG(CASE WHEN passed THEN 1.0 ELSE 0.0 END) FROM trajectories WHERE {} GROUP BY iteration_num ORDER BY iteration_num".format(
            " AND ".join(conditions)
        )
        rows = store.execute_sql(sql, params)
        return _convert_simple_sql_results_to_metrics(rows, metric_name, experiment_id, labels_filter)


# Complex calculated metrics
def extract_tokens_per_reward_sql(metric_name, experiment_id, labels_filter, iteration_range):
    # type: (str, str, Dict[str, str], Optional[Tuple[int, int]]) -> List[Dict]
    """Extract tokens per reward using SQL."""
    # This requires safe division: total_tokens / NULLIF(reward, 0)
    from ...mock import store

    conditions = ["experiment_id = ?", "reward > 0"]  # Avoid division by zero
    params = [experiment_id]

    if iteration_range:
        start_iter, end_iter = iteration_range
        conditions.append("iteration_num BETWEEN ? AND ?")
        params.extend([start_iter, end_iter])

    # Add label filters
    for label_key in ["scaffold", "tool_schema", "language", "system_prompt"]:
        if label_key == "language":
            db_field = "task_language"
        else:
            db_field = label_key
        if label_key in labels_filter:
            conditions.append("{} = ?".format(db_field))
            params.append(labels_filter[label_key])

    split_by = labels_filter.get("split_by")
    if split_by:
        if split_by == "language":
            db_field = "task_language"
        else:
            db_field = split_by
        sql = "SELECT {}, iteration_num, AVG(total_tokens / reward) FROM trajectories WHERE {} GROUP BY {}, iteration_num ORDER BY iteration_num, {}".format(
            db_field, " AND ".join(conditions), db_field, db_field
        )
        rows = store.execute_sql(sql, params)
        return _convert_split_sql_results_to_metrics(rows, metric_name, experiment_id, split_by)
    else:
        sql = "SELECT iteration_num, AVG(total_tokens / reward) FROM trajectories WHERE {} GROUP BY iteration_num ORDER BY iteration_num".format(
            " AND ".join(conditions)
        )
        rows = store.execute_sql(sql, params)
        return _convert_simple_sql_results_to_metrics(rows, metric_name, experiment_id, labels_filter)


def extract_input_output_ratio_sql(metric_name, experiment_id, labels_filter, iteration_range):
    # type: (str, str, Dict[str, str], Optional[Tuple[int, int]]) -> List[Dict]
    """Extract input/output token ratio using SQL."""
    from ...mock import store

    conditions = ["experiment_id = ?", "output_tokens > 0"]
    params = [experiment_id]

    if iteration_range:
        start_iter, end_iter = iteration_range
        conditions.append("iteration_num BETWEEN ? AND ?")
        params.extend([start_iter, end_iter])

    for label_key in ["scaffold", "tool_schema", "language", "system_prompt"]:
        if label_key == "language":
            db_field = "task_language"
        else:
            db_field = label_key
        if label_key in labels_filter:
            conditions.append("{} = ?".format(db_field))
            params.append(labels_filter[label_key])

    split_by = labels_filter.get("split_by")
    if split_by:
        if split_by == "language":
            db_field = "task_language"
        else:
            db_field = split_by
        sql = "SELECT {}, iteration_num, AVG(CAST(input_tokens AS FLOAT) / output_tokens) FROM trajectories WHERE {} GROUP BY {}, iteration_num ORDER BY iteration_num, {}".format(
            db_field, " AND ".join(conditions), db_field, db_field
        )
        rows = store.execute_sql(sql, params)
        return _convert_split_sql_results_to_metrics(rows, metric_name, experiment_id, split_by)
    else:
        sql = "SELECT iteration_num, AVG(CAST(input_tokens AS FLOAT) / output_tokens) FROM trajectories WHERE {} GROUP BY iteration_num ORDER BY iteration_num".format(
            " AND ".join(conditions)
        )
        rows = store.execute_sql(sql, params)
        return _convert_simple_sql_results_to_metrics(rows, metric_name, experiment_id, labels_filter)


# ═══════════════════ Pass Rate Baseline extractor ═══════════════════


def extract_pass_rate_baseline(metric_name, experiment_id, labels_filter, iteration_range):
    # type: (str, str, Dict[str, str], Optional[Tuple[int, int]]) -> List[Dict]
    """Extract historical pass rate baseline across other experiments.

    For each iteration of the current experiment, collects the task_ids used,
    then computes the average pass rate for those tasks across all OTHER experiments.
    """
    from ...mock import store
    from .base import _filter_iterations, _get_trajectories_for_iteration

    exp = store.get_experiment(experiment_id)
    if not exp:
        return []

    iterations = _filter_iterations(experiment_id, iteration_range)
    if not iterations:
        return []

    # Collect all trajectories from OTHER experiments that share the same benchmark
    all_experiments = store.get_experiments()
    bench_id = exp.get("config", {}).get("benchmark_id")

    other_trajs = []  # type: List[Dict]
    for other_exp in all_experiments:
        if other_exp["id"] == experiment_id:
            continue
        other_bench = other_exp.get("config", {}).get("benchmark_id")
        if other_bench == bench_id:
            other_trajs.extend(store.get_trajectories(experiment_id=other_exp["id"]))

    if not other_trajs:
        return []

    # Build task_id -> pass_rate lookup for other experiments
    task_pass_counts = {}  # type: Dict[str, List[bool]]
    for t in other_trajs:
        tid = t.get("task_id", "")
        if tid not in task_pass_counts:
            task_pass_counts[tid] = []
        task_pass_counts[tid].append(t.get("passed", False))

    task_pass_rates = {}  # type: Dict[str, float]
    for tid, flags in task_pass_counts.items():
        n = len(flags)
        if n > 0:
            task_pass_rates[tid] = sum(1 for f in flags if f) / n

    # For each iteration, compute baseline from the tasks used
    values = []  # type: List[List]
    for it in iterations:
        trajs = _get_trajectories_for_iteration(experiment_id, it["iteration_num"])
        if not trajs:
            continue

        task_ids = set(t.get("task_id", "") for t in trajs)
        rates = [task_pass_rates[tid] for tid in task_ids if tid in task_pass_rates]
        if not rates:
            continue

        baseline = round(sum(rates) / len(rates), 4)
        # Use iteration_num for x-axis
        x_val = it["iteration_num"]
        values.append([x_val, str(baseline)])

    if not values:
        return []

    return [
        {
            "metric": {
                "__name__": metric_name,
                "experiment_id": experiment_id,
                "x_axis_type": "iteration",
            },
            "values": values,
        }
    ]
