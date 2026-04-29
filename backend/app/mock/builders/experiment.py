"""Experiment data generation.

This module contains definitions and builders for Experiment entities.
"""

import random
from datetime import timedelta

from ..constants import RNG_SEED
from .helpers import iso, now

_RNG = random.Random(RNG_SEED)


# ═══════════════════ Experiment Definitions ═══════════════════

_EXP_DEFS = [
    # Project 1: Code Agent v2 — 3 experiments
    {
        "id": "exp-grpo-cc",
        "project_id": "proj-code-agent-v2",
        "name": "GRPO Claude+OpenClaw Qwen3-8B",
        "status": "running",
        "algorithm": "GRPO",
        "scaffolds": ["claude_code", "openclaw"],
        "model": "qwen3-8b",
        "benchmark_id": "bench-swe-lite",
    },
    {
        "id": "exp-ppo-oc",
        "project_id": "proj-code-agent-v2",
        "name": "PPO OpenClaw Qwen3-8B",
        "status": "completed",
        "algorithm": "PPO",
        "scaffolds": ["openclaw"],
        "model": "qwen3-8b",
        "benchmark_id": "bench-swe-lite",
    },
    {
        "id": "exp-gigpo-aider",
        "project_id": "proj-code-agent-v2",
        "name": "GiGPO Aider+Claude Qwen3-72B",
        "status": "completed",
        "algorithm": "GiGPO",
        "scaffolds": ["aider", "claude_code"],
        "model": "qwen3-72b",
        "benchmark_id": "bench-humaneval",
    },
    # Project 2: Reasoning Model — 3 experiments
    {
        "id": "exp-grpo-reason",
        "project_id": "proj-reasoning",
        "name": "GRPO Reasoning Claude Qwen3-8B",
        "status": "running",
        "algorithm": "GRPO",
        "scaffolds": ["claude_code"],
        "model": "qwen3-8b",
        "benchmark_id": "bench-agentbench",
    },
    {
        "id": "exp-ppo-reason",
        "project_id": "proj-reasoning",
        "name": "PPO Reasoning OpenClaw Qwen3-72B",
        "status": "completed",
        "algorithm": "PPO",
        "scaffolds": ["openclaw", "aider"],
        "model": "qwen3-72b",
        "benchmark_id": "bench-agentbench",
    },
    {
        "id": "exp-gigpo-math",
        "project_id": "proj-reasoning",
        "name": "GiGPO MathQA All-Scaffold Qwen3-8B",
        "status": "running",
        "algorithm": "GiGPO",
        "scaffolds": ["claude_code", "openclaw", "aider"],
        "model": "qwen3-8b",
        "benchmark_id": "bench-mathqa",
    },
]


def build_experiments(iterations_dict):
    # type: (Dict[str, List[Dict]]) -> List[Dict]
    """Build experiment records with aggregated metrics.

    Args:
        iterations_dict: Dictionary mapping experiment ID to iteration list

    Returns:
        List of experiment dictionaries with metrics
    """
    exps = []  # type: List[Dict]
    _now_ts = now()
    for ed in _EXP_DEFS:
        iters = iterations_dict.get(ed["id"], [])
        latest = iters[-1] if iters else None
        exps.append(
            {
                "id": ed["id"],
                "project_id": ed["project_id"],
                "name": ed["name"],
                "status": ed["status"],
                "config": {
                    "model": ed["model"],
                    "scaffolds": ed["scaffolds"],
                    "algorithm": ed["algorithm"],
                    "reward_function": "composite_v2",
                    "reward_components": ["task", "format", "efficiency"],
                    "hyperparams": {
                        "lr": 1e-5,
                        "batch_size": 64,
                        "kl_coeff": 0.02,
                    },
                    "benchmark_id": ed["benchmark_id"],
                    "max_turns": 20,
                },
                "tags": {"team": "agent-rl"},
                "created_at": iso(_now_ts - timedelta(days=14)),
                "latest_iteration": (latest["iteration_num"] if latest else None),
                "mean_reward": (latest["metrics"]["mean_reward"] if latest else None),
                "pass_rate": (latest["metrics"]["pass_rate"] if latest else None),
                "total_trajectories": (sum(it["metrics"]["total_trajectories"] for it in iters) if iters else 0),
                "total_tokens": (sum(it["metrics"]["total_tokens"] for it in iters) if iters else 0),
            }
        )
    return exps


def get_experiment_defs():
    # type: () -> List[Dict]
    """Get the raw experiment definitions.

    Returns:
        List of experiment definition dictionaries
    """
    return _EXP_DEFS
