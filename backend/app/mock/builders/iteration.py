"""Iteration data generation.

This module contains builders for Iteration entities.
"""

import random
from datetime import timedelta

from ..constants import ITERATIONS_PER_EXPERIMENT, RNG_SEED
from .helpers import convergence_curve, iso, now, std, uid
from .trajectory import build_trajectories_for_iteration

_RNG = random.Random(RNG_SEED)


def build_iterations(exp_id, exp_def, tasks):
    # type: (str, Dict, List[Dict]) -> Tuple[List[Dict], List[Dict], List[Dict]]
    """Build 50 iterations for one experiment.

    Args:
        exp_id: Experiment ID
        exp_def: Experiment definition dictionary
        tasks: List of tasks for the benchmark

    Returns:
        Tuple of (iterations, trajectories, annotations)
    """
    iterations = []  # type: List[Dict]
    all_trajectories = []  # type: List[Dict]
    all_annotations = []  # type: List[Dict]

    scaffolds = exp_def["scaffolds"]
    base_start = now() - timedelta(days=7)

    for it_num in range(1, ITERATIONS_PER_EXPERIMENT + 1):
        it_id = uid("iter", exp_id, it_num)
        it_ts = base_start + timedelta(hours=it_num * 2)

        mean_reward = convergence_curve(it_num, 0.15, 0.78, 0.055)
        pass_rate = convergence_curve(it_num, 0.20, 0.72, 0.050)

        trajs, annots = build_trajectories_for_iteration(
            exp_id,
            it_id,
            it_num,
            scaffolds,
            tasks,
            it_ts,
            mean_reward,
            pass_rate,
        )
        all_trajectories.extend(trajs)
        all_annotations.extend(annots)

        # aggregate metrics from trajectories
        rewards = [t["reward"] for t in trajs]
        passed_flags = [t["passed"] for t in trajs]
        tokens_list = [t["total_tokens"] for t in trajs]
        turns_list = [t["total_turns"] for t in trajs]
        durations = [t["duration_ms"] for t in trajs]
        input_toks = [t["input_tokens"] for t in trajs]
        output_toks = [t["output_tokens"] for t in trajs]
        # TASK-048: aggregate duration fields
        sandbox_create_durations = [t.get("sandbox_create_duration_ms", 0) for t in trajs]
        verify_durations = [t.get("verify_duration_ms", 0) for t in trajs]

        sorted_r = sorted(rewards)
        n = len(sorted_r)
        actual_mean_reward = sum(rewards) / n
        actual_pass_rate = sum(int(p) for p in passed_flags) / n

        total_input = sum(input_toks)
        total_output = sum(output_toks)

        tpr_val = None  # type: Optional[float]
        if actual_mean_reward > 0.001:
            tpr_val = round(sum(tokens_list) / actual_mean_reward, 1)

        metrics = {
            "mean_reward": round(actual_mean_reward, 4),
            "median_reward": round(sorted_r[n // 2], 4),
            "reward_std": round(std(rewards), 4),
            "pass_rate": round(actual_pass_rate, 4),
            "total_trajectories": n,
            "total_tokens": sum(tokens_list),
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "mean_tokens_per_trajectory": round(sum(tokens_list) / n, 1),
            "tokens_per_reward": tpr_val,
            "input_output_ratio": round(total_input / max(total_output, 1), 2),
            "mean_turns": round(sum(turns_list) / n, 1),
            "mean_duration_ms": int(sum(durations) / n),
            # TASK-048: new duration metrics
            "mean_sandbox_create_duration_ms": int(sum(sandbox_create_durations) / n),
            "mean_verify_duration_ms": int(sum(verify_durations) / n),
            "tool_call_count": sum(t["tool_call_count"] for t in trajs),
        }

        iterations.append(
            {
                "id": it_id,
                "experiment_id": exp_id,
                "iteration_num": it_num,
                "timestamp": iso(it_ts),
                "checkpoint": {
                    "saved": it_num % 5 == 0,
                    "path": ("s3://checkpoints/{}/iter-{}".format(exp_id, it_num) if it_num % 5 == 0 else ""),
                    "policy_version": "v{}".format(it_num),
                },
                "metrics": metrics,
            }
        )

    return iterations, all_trajectories, all_annotations
