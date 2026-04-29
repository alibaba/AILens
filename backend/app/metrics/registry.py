"""Metric registry — defines all queryable time-series metrics.

Python 3.6.8 compatible.
"""

from collections import OrderedDict

from .extractors import (
    _extract_format_correct_rate_factory,
    _extract_repeat_rate_factory,
    _extract_reward_range,
    _extract_stop_reason_rate,
    _extract_success_turns_bucket,
    _extract_success_turns_count,
    _extract_success_turns_max,
    _extract_success_turns_min,
    _extract_success_turns_stat,
    _extract_success_turns_sum,
    _extract_task_all_correct_rate,
    _extract_task_all_wrong_rate,
    _extract_task_mixed_rate,
    _extract_turns_count,
    _extract_turns_duration_count,
    _extract_turns_duration_max,
    _extract_turns_duration_sum,
    _extract_turns_passed_count,
)

# Import SQL-based extractors
from .extractors.sql_aggregated import (
    extract_duration_avg_sql,
    extract_input_output_ratio_sql,
    extract_input_tokens_sum_sql,
    extract_output_tokens_sum_sql,
    extract_pass_rate_baseline,
    extract_pass_rate_sql,
    extract_passed_count_sql,
    extract_reward_avg_sql,
    extract_reward_stddev_sql,
    extract_sandbox_duration_avg_sql,
    extract_tokens_per_reward_sql,
    extract_tokens_per_trajectory_avg_sql,
    extract_trajectory_count_sql,
    extract_turns_avg_sql,
    extract_verify_duration_avg_sql,
)

# ── Common labels ──
_COMMON_LABELS = ["experiment_id", "scaffold", "language", "system_prompt", "tool_schema"]

# ═══════════════════ Registry ═══════════════════

METRIC_REGISTRY = OrderedDict(
    [
        # ── Convergence (3) - SQL optimized ──
        (
            "experiment_trajectory_count",
            {
                "type": "counter",
                "unit": "",
                "description": "Total trajectory count per iteration",
                "labels": _COMMON_LABELS[:],
                "extractor": extract_trajectory_count_sql,  # SQL COUNT(*)
            },
        ),
        (
            "experiment_passed_count",
            {
                "type": "counter",
                "unit": "",
                "description": "Passed trajectory count per iteration",
                "labels": _COMMON_LABELS[:],
                "extractor": extract_passed_count_sql,  # SQL COUNT(*) WHERE passed = true
            },
        ),
        (
            "experiment_mean_reward",
            {
                "type": "gauge",
                "unit": "",
                "description": "Mean reward per iteration",
                "labels": _COMMON_LABELS[:],
                "extractor": extract_reward_avg_sql,  # SQL AVG(reward)
            },
        ),
        (
            "experiment_pass_rate",
            {
                "type": "gauge",
                "unit": "",
                "description": "Pass rate per iteration",
                "labels": _COMMON_LABELS[:],
                "extractor": extract_pass_rate_sql,  # SQL AVG(CASE WHEN passed THEN 1.0 ELSE 0.0 END)
            },
        ),
        (
            "experiment_reward_std",
            {
                "type": "gauge",
                "unit": "",
                "description": "Reward standard deviation per iteration",
                "labels": _COMMON_LABELS[:],
                "extractor": extract_reward_stddev_sql,  # SQL STDDEV(reward)
            },
        ),
        # ── Efficiency (8) ──
        (
            "experiment_input_tokens",
            {
                "type": "counter",
                "unit": "tokens",
                "description": "Total input tokens per iteration",
                "labels": _COMMON_LABELS[:],
                "extractor": extract_input_tokens_sum_sql,  # SQL SUM(input_tokens)
            },
        ),
        (
            "experiment_output_tokens",
            {
                "type": "counter",
                "unit": "tokens",
                "description": "Total output tokens per iteration",
                "labels": _COMMON_LABELS[:],
                "extractor": extract_output_tokens_sum_sql,  # SQL SUM(output_tokens)
            },
        ),
        (
            "experiment_tokens_per_trajectory",
            {
                "type": "gauge",
                "unit": "tokens",
                "description": "Mean tokens per trajectory per iteration",
                "labels": _COMMON_LABELS[:],
                "extractor": extract_tokens_per_trajectory_avg_sql,  # SQL AVG(total_tokens)
            },
        ),
        (
            "experiment_tokens_per_reward",
            {
                "type": "gauge",
                "unit": "tokens",
                "description": "Tokens per unit reward per iteration",
                "labels": _COMMON_LABELS[:],
                "extractor": extract_tokens_per_reward_sql,  # SQL AVG(total_tokens / reward)
            },
        ),
        (
            "experiment_io_tokens_ratio",
            {
                "type": "gauge",
                "unit": "",
                "description": "Input/output token ratio per iteration",
                "labels": _COMMON_LABELS[:],
                "extractor": extract_input_output_ratio_sql,  # SQL AVG(input_tokens / output_tokens)
            },
        ),
        (
            "experiment_mean_turns",
            {
                "type": "gauge",
                "unit": "turns",
                "description": "Mean turns per trajectory per iteration",
                "labels": _COMMON_LABELS[:],
                "extractor": extract_turns_avg_sql,  # SQL AVG(total_turns)
            },
        ),
        (
            "experiment_mean_duration_ms",
            {
                "type": "gauge",
                "unit": "ms",
                "description": "Mean trajectory duration per iteration",
                "labels": _COMMON_LABELS[:],
                "extractor": extract_duration_avg_sql,  # SQL AVG(duration_ms)
            },
        ),
        # ── TASK-048: Sandbox Create and Verify Duration ──
        (
            "experiment_mean_sandbox_create_duration_ms",
            {
                "type": "gauge",
                "unit": "ms",
                "description": "Mean sandbox creation duration per iteration",
                "labels": _COMMON_LABELS[:],
                "extractor": extract_sandbox_duration_avg_sql,  # SQL AVG(sandbox_create_duration_ms)
            },
        ),
        (
            "experiment_mean_verify_duration_ms",
            {
                "type": "gauge",
                "unit": "ms",
                "description": "Mean verification duration per iteration",
                "labels": _COMMON_LABELS[:],
                "extractor": extract_verify_duration_avg_sql,  # SQL AVG(verify_duration_ms)
            },
        ),
        # ── Pass Rate Baseline (1) — M2 ──
        (
            "experiment_pass_rate_baseline",
            {
                "type": "gauge",
                "unit": "",
                "description": "Historical pass rate baseline from other experiments",
                "labels": ["experiment_id"],
                "extractor": extract_pass_rate_baseline,
            },
        ),
        # ── Success Turns (6) — M2 ──
        (
            "experiment_success_mean_turns",
            {
                "type": "gauge",
                "unit": "turns",
                "description": "Mean turns of successful trajectories per iteration",
                "labels": _COMMON_LABELS[:],
                "extractor": _extract_success_turns_stat("mean"),
            },
        ),
        (
            "experiment_success_turns_count",
            {
                "type": "gauge",
                "unit": "",
                "description": "Count of successful trajectories per iteration",
                "labels": _COMMON_LABELS[:],
                "extractor": _extract_success_turns_count,
            },
        ),
        (
            "experiment_success_turns_min",
            {
                "type": "gauge",
                "unit": "turns",
                "description": "Min turns of successful trajectories per iteration",
                "labels": _COMMON_LABELS[:],
                "extractor": _extract_success_turns_min,
            },
        ),
        (
            "experiment_success_turns_max",
            {
                "type": "gauge",
                "unit": "turns",
                "description": "Max turns of successful trajectories per iteration",
                "labels": _COMMON_LABELS[:],
                "extractor": _extract_success_turns_max,
            },
        ),
        (
            "experiment_success_turns_sum",
            {
                "type": "gauge",
                "unit": "turns",
                "description": "Sum of turns of successful trajectories per iteration",
                "labels": _COMMON_LABELS[:],
                "extractor": _extract_success_turns_sum,
            },
        ),
        (
            "experiment_success_turns_bucket",
            {
                "type": "histogram",
                "unit": "turns",
                "description": "Histogram of successful trajectory turns distribution",
                "labels": _COMMON_LABELS[:] + ["le"],
                "extractor": _extract_success_turns_bucket,
            },
        ),
        # ── M4: Format Correct Rate (1) — TASK-029 ──
        (
            "experiment_format_correct_rate",
            {
                "type": "gauge",
                "unit": "",
                "description": "Format correctness rate per iteration",
                "labels": _COMMON_LABELS[:],
                "extractor": _extract_format_correct_rate_factory(),
            },
        ),
        # ── M4: Repeat Rates (2) — TASK-031 ──
        (
            "experiment_repeat_tool_call_rate",
            {
                "type": "gauge",
                "unit": "",
                "description": "Rate of trajectories with repeated tool calls per iteration",
                "labels": _COMMON_LABELS[:],
                "extractor": _extract_repeat_rate_factory("repeat_tool_call_count"),
            },
        ),
        (
            "experiment_repeat_response_rate",
            {
                "type": "gauge",
                "unit": "",
                "description": "Rate of trajectories with repeated responses per iteration",
                "labels": _COMMON_LABELS[:],
                "extractor": _extract_repeat_rate_factory("repeat_response_count"),
            },
        ),
        # ── Turn Analysis (5) ─ PromQL Implementation ──
        (
            "experiment_turns_count",
            {
                "type": "gauge",
                "unit": "",
                "description": "Total trajectory count per total_turns value",
                "labels": ["experiment_id", "total_turns"],
                "extractor": _extract_turns_count,
            },
        ),
        (
            "experiment_turns_passed_count",
            {
                "type": "gauge",
                "unit": "",
                "description": "Passed trajectory count per total_turns value",
                "labels": ["experiment_id", "total_turns"],
                "extractor": _extract_turns_passed_count,
            },
        ),
        (
            "experiment_turns_duration_max",
            {
                "type": "gauge",
                "unit": "ms",
                "description": "Max duration of passed trajectories per total_turns value",
                "labels": ["experiment_id", "total_turns"],
                "extractor": _extract_turns_duration_max,
            },
        ),
        (
            "experiment_turns_duration_sum",
            {
                "type": "gauge",
                "unit": "ms",
                "description": "Sum of durations of passed trajectories per total_turns value",
                "labels": ["experiment_id", "total_turns"],
                "extractor": _extract_turns_duration_sum,
            },
        ),
        (
            "experiment_turns_duration_count",
            {
                "type": "gauge",
                "unit": "",
                "description": "Count of passed trajectories per total_turns value (for avg calculation)",
                "labels": ["experiment_id", "total_turns"],
                "extractor": _extract_turns_duration_count,
            },
        ),
        # ── P0: Task Effectiveness Metrics (3) ──
        (
            "experiment_task_all_correct_rate",
            {
                "type": "gauge",
                "unit": "",
                "description": "Rate of tasks where all trajectories passed per iteration",
                "labels": _COMMON_LABELS[:],
                "extractor": _extract_task_all_correct_rate,
            },
        ),
        (
            "experiment_task_all_wrong_rate",
            {
                "type": "gauge",
                "unit": "",
                "description": "Rate of tasks where no trajectories passed per iteration",
                "labels": _COMMON_LABELS[:],
                "extractor": _extract_task_all_wrong_rate,
            },
        ),
        (
            "experiment_task_mixed_rate",
            {
                "type": "gauge",
                "unit": "",
                "description": "Rate of tasks with both passed and failed trajectories per iteration",
                "labels": _COMMON_LABELS[:],
                "extractor": _extract_task_mixed_rate,
            },
        ),
        # ── P2: Quality Verification Metrics (2) ──
        (
            "experiment_stop_reason_rate",
            {
                "type": "gauge",
                "unit": "",
                "description": "Distribution of stop reasons (exec_result) per iteration",
                "labels": _COMMON_LABELS[:] + ["exec_result"],
                "extractor": _extract_stop_reason_rate,
            },
        ),
        (
            "experiment_reward_range",
            {
                "type": "gauge",
                "unit": "",
                "description": "Reward range (max - min) per iteration",
                "labels": _COMMON_LABELS[:],
                "extractor": _extract_reward_range,
            },
        ),
    ]
)
