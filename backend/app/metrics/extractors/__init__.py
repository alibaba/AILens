"""Metric extractors — pull time-series data from MockStore iterations.

This module provides unified exports from the refactored extractor modules,
maintaining backward compatibility with the original extractors.py.

Each extractor has signature:
    (metric_name, experiment_id, labels_filter, iteration_range) -> List[dict]

Python 3.6.8 compatible.
"""

# Base utilities (internal use)
from .base import (
    _compute_metric_from_trajs,
    _filter_iterations,
    _get_trajectories_for_iteration,
    _safe_tokens_per_reward,
    _std,
    _ts_epoch,
)

# Efficiency metrics
from .efficiency import (
    SUCCESS_TURNS_BUCKETS,
    _extract_success_turns_agg,
    _extract_success_turns_bucket,
    _extract_success_turns_count,
    _extract_success_turns_max,
    _extract_success_turns_min,
    _extract_success_turns_stat,
    _extract_success_turns_sum,
)

# Quality metrics
from .quality import (
    _extract_format_correct_filtered,
    _extract_format_correct_rate_factory,
    _extract_repeat_rate_factory,
    _extract_reward_range,
    _extract_stop_reason_rate,
)

# Pass rate baseline (moved to SQL aggregated)
# SQL aggregated metrics (high-performance)
from .sql_aggregated import (
    create_sql_aggregated_extractor,
    extract_duration_avg_sql,
    extract_duration_sum_sql,
    extract_failed_count_sql,
    extract_pass_rate_baseline,
    extract_passed_count_sql,
    extract_reward_avg_sql,
    extract_reward_max_sql,
    extract_reward_min_sql,
    extract_reward_stddev_sql,
    extract_trajectory_count_sql,
    extract_turns_avg_sql,
    extract_turns_max_sql,
    extract_turns_min_sql,
    extract_turns_sum_sql,
)

# Task effectiveness metrics
from .task_effectiveness import (
    _extract_task_all_correct_rate,
    _extract_task_all_wrong_rate,
    _extract_task_mixed_rate,
)

# Turn analysis metrics
from .turns import (
    _extract_turns_count,
    _extract_turns_duration_count,
    _extract_turns_duration_max,
    _extract_turns_duration_sum,
    _extract_turns_passed_count,
)

# Export all public and internal functions for backward compatibility
__all__ = [
    # Base utilities
    "_filter_iterations",
    "_get_trajectories_for_iteration",
    "_std",
    "_ts_epoch",
    "_compute_metric_from_trajs",
    "_safe_tokens_per_reward",
    # Pass rate baseline
    "extract_pass_rate_baseline",
    # Efficiency
    "SUCCESS_TURNS_BUCKETS",
    "_extract_success_turns_stat",
    "_extract_success_turns_count",
    "_extract_success_turns_min",
    "_extract_success_turns_max",
    "_extract_success_turns_sum",
    "_extract_success_turns_agg",
    "_extract_success_turns_bucket",
    # Quality
    "_extract_format_correct_rate_factory",
    "_extract_format_correct_filtered",
    "_extract_repeat_rate_factory",
    "_extract_stop_reason_rate",
    "_extract_reward_range",
    # Task effectiveness
    "_extract_task_all_correct_rate",
    "_extract_task_all_wrong_rate",
    "_extract_task_mixed_rate",
    # Turns
    "_extract_turns_count",
    "_extract_turns_passed_count",
    "_extract_turns_duration_max",
    "_extract_turns_duration_sum",
    "_extract_turns_duration_count",
    # SQL aggregated
    "create_sql_aggregated_extractor",
    "extract_trajectory_count_sql",
    "extract_passed_count_sql",
    "extract_failed_count_sql",
    "extract_reward_avg_sql",
    "extract_reward_stddev_sql",
    "extract_turns_avg_sql",
    "extract_duration_avg_sql",
    "extract_turns_sum_sql",
    "extract_duration_sum_sql",
    "extract_turns_min_sql",
    "extract_turns_max_sql",
    "extract_reward_min_sql",
    "extract_reward_max_sql",
]
