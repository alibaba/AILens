"""Trajectory data generation.

This module contains builders for Trajectory entities.
"""

import hashlib
import math
from datetime import timedelta

from ..constants import CAT_BASE_PASS, RNG_SEED, SYSTEM_PROMPTS, TOOL_SCHEMAS, TRAJECTORIES_PER_ITERATION

# Mock tools for testing (TraceQL discovery available but not used in mocks)
MOCK_TOOLS = ["bash", "file_edit", "web_search", "read_file", "submit"]
import random

from .helpers import iso, now, uid

_RNG = random.Random(RNG_SEED)


def build_trajectories_for_iteration(
    exp_id,  # type: str
    iter_id,  # type: str
    iter_num,  # type: int
    scaffolds,  # type: List[str]
    tasks,  # type: List[Dict]
    base_ts,  # type: datetime
    target_mean_reward,  # type: float
    target_pass_rate,  # type: float
):
    # type: (...) -> Tuple[List[Dict], List[Dict]]
    """Generate 100 trajectories for one iteration.

    Args:
        exp_id: Experiment ID
        iter_id: Iteration ID
        iter_num: Iteration number (1-50)
        scaffolds: List of scaffold names
        tasks: List of tasks to sample from
        base_ts: Base timestamp for trajectory creation
        target_mean_reward: Target mean reward for convergence
        target_pass_rate: Target pass rate for convergence

    Returns:
        Tuple of (trajectories, annotations)
    """
    trajectories = []  # type: List[Dict]
    annotations = []  # type: List[Dict]

    for idx in range(TRAJECTORIES_PER_ITERATION):
        task = tasks[idx % len(tasks)]
        cat = task["category"]
        scaffold = scaffolds[idx % len(scaffolds)]

        # outcome weighted by category + iteration progress
        cat_bonus = CAT_BASE_PASS.get(cat, 0.4)
        progress = 1 - math.exp(-0.05 * iter_num)
        pass_prob = min(0.95, cat_bonus + (target_pass_rate - 0.45) * progress)

        roll = _RNG.random()
        if roll < pass_prob * 0.75:
            outcome = "success"
        elif roll < pass_prob * 0.75 + 0.25:
            outcome = "failure"
        elif roll < pass_prob * 0.75 + 0.35:
            outcome = "timeout"
        else:
            outcome = "error"

        passed = outcome == "success"

        # reward correlated with outcome + noise
        if outcome == "success":
            task_r = _RNG.uniform(0.7, 1.0)
            fmt_r = _RNG.uniform(0.6, 1.0)
            eff_r = _RNG.uniform(0.3, 0.9)
        elif outcome == "failure":
            task_r = _RNG.uniform(0.0, 0.3)
            fmt_r = _RNG.uniform(0.3, 0.8)
            eff_r = _RNG.uniform(0.0, 0.4)
        elif outcome == "timeout":
            task_r = 0.0
            fmt_r = _RNG.uniform(0.2, 0.5)
            eff_r = 0.0
        else:
            task_r = _RNG.uniform(-0.2, 0.1)
            fmt_r = _RNG.uniform(0.0, 0.3)
            eff_r = 0.0

        reward = round(0.5 * task_r + 0.3 * fmt_r + 0.2 * eff_r, 4)
        reward_components = {
            "task": round(task_r, 3),
            "format": round(fmt_r, 3),
            "efficiency": round(eff_r, 3),
        }

        if outcome == "timeout":
            total_turns = 20  # equals max_turns
        else:
            total_turns = _RNG.randint(5, 20)
        total_events = total_turns * 3
        duration_ms = total_turns * _RNG.randint(1500, 4000)
        # TASK-048: sandbox_create_duration_ms and verify_duration_ms
        sandbox_create_duration_ms = int(duration_ms * _RNG.uniform(0.10, 0.15))
        verify_duration_ms = int(duration_ms * _RNG.uniform(0.05, 0.10))
        inp_tok = _RNG.randint(200, 800) * total_turns
        out_tok = _RNG.randint(50, 300) * total_turns
        total_tok = inp_tok + out_tok

        tool_count = _RNG.randint(total_turns - 2, total_turns + 3)
        tool_succ = max(0.0, min(1.0, _RNG.gauss(0.85 if outcome == "success" else 0.55, 0.1)))

        error_turns = 0 if outcome == "success" else _RNG.randint(1, max(1, total_turns // 3))
        first_err = -1 if error_turns == 0 else _RNG.randint(1, total_turns)

        traj_id = uid("traj", exp_id, iter_num, idx)
        trace_id = hashlib.md5("trace:{}".format(traj_id).encode()).hexdigest()

        # TASK-029: format_correct field
        if outcome == "success":
            format_correct = _RNG.random() < 0.9
        elif outcome == "failure":
            format_correct = _RNG.random() < 0.6
        else:
            format_correct = _RNG.random() < 0.3

        # TASK-031: repetition detection fields
        repeat_tool_call_count = _RNG.randint(0, 5)
        repeat_response_count = _RNG.randint(0, 3)

        traj = {
            "id": traj_id,
            "experiment_id": exp_id,
            "iteration_id": iter_id,
            "task_id": task["id"],
            "scaffold": scaffold,
            "system_prompt": SYSTEM_PROMPTS[idx % len(SYSTEM_PROMPTS)],
            "tool_schema": TOOL_SCHEMAS[idx % len(TOOL_SCHEMAS)],
            "outcome": outcome,
            "reward": reward,
            "reward_components": reward_components,
            "passed": passed,
            "total_turns": total_turns,
            "total_events": total_events,
            "duration_ms": duration_ms,
            "sandbox_create_duration_ms": sandbox_create_duration_ms,
            "verify_duration_ms": verify_duration_ms,
            "total_tokens": total_tok,
            "input_tokens": inp_tok,
            "output_tokens": out_tok,
            "tool_call_count": tool_count,
            "tool_success_rate": round(tool_succ, 3),
            "error_turn_count": error_turns,
            "first_error_turn": first_err,
            "llm_time_ratio": round(_RNG.uniform(0.4, 0.8), 3),
            "tokens_per_turn": round(total_tok / total_turns, 1),
            "tags": {},
            "otel_trace_id": trace_id,
            "created_at": iso(base_ts + timedelta(seconds=idx)),
            # Additional fields used internally for filtering
            "task_category": task["category"],
            "task_difficulty": task["difficulty"],
            "task_language": task["language"],
            "iteration_num": iter_num,
            # M4: format correctness (TASK-029)
            "format_correct": format_correct,
            # M4: repetition detection (TASK-031)
            "repeat_tool_call_count": repeat_tool_call_count,
            "repeat_response_count": repeat_response_count,
        }

        # annotations for failed/timeout trajectories
        if outcome in ("failure", "timeout", "error"):
            ann = build_annotation(traj_id, exp_id, outcome, total_turns)
            annotations.append(ann)

        trajectories.append(traj)

    return trajectories, annotations


def build_annotation(traj_id, exp_id, outcome, total_turns):
    # type: (str, str, str, int) -> Dict
    """Build an annotation for a failed/timeout/error trajectory.

    Args:
        traj_id: Trajectory ID
        exp_id: Experiment ID
        outcome: The trajectory outcome (failure/timeout/error)
        total_turns: Total number of turns in trajectory

    Returns:
        Annotation dictionary
    """
    if outcome == "timeout":
        ptype = "timeout"
        desc = "Trajectory exceeded time limit"
        affected = list(range(max(1, total_turns - 3), total_turns + 1))
        sev = "warning"
    elif outcome == "error":
        ptype = _RNG.choice(["tool_error", "repeat_error"])
        desc = _RNG.choice(
            [
                "Tool returned permission denied error repeatedly",
                "Subprocess crashed with non-zero exit code",
            ]
        )
        affected = [_RNG.randint(1, total_turns)]
        sev = "error"
    else:  # failure
        ptype = _RNG.choice(
            [
                "action_loop",
                "ineffective_action",
                "early_abandon",
            ]
        )
        desc = _RNG.choice(
            [
                "Agent repeated the same bash command 3+ times",
                "Agent action produced no observable change",
                "Agent abandoned task after very few turns",
            ]
        )
        mid = total_turns // 2
        affected = list(range(max(1, mid - 1), min(total_turns + 1, mid + 3)))
        sev = "warning"

    return {
        "id": uid("ann", traj_id),
        "trajectory_id": traj_id,
        "experiment_id": exp_id,
        "source": "auto",
        "pattern_type": ptype,
        "description": desc,
        "affected_turns": affected,
        "severity": sev,
        "created_at": iso(now()),
    }
