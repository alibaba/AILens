"""Benchmark and Task data generation.

This module contains definitions and builders for Benchmark and Task entities.
"""

import random

from ..constants import DEFAULT_TOTAL_TASKS, DIFFICULTIES, LANGUAGES, RNG_SEED, TASK_CATEGORIES

_RNG = random.Random(RNG_SEED)


# ═══════════════════ Benchmark Definitions ═══════════════════

_BENCHMARK_DEFS = [
    # Project 1 benchmarks
    {
        "id": "bench-swe-lite",
        "project_id": "proj-code-agent-v2",
        "name": "SWE-bench Lite",
        "version": "1.0",
        "source": "princeton-nlp/SWE-bench",
        "total_tasks": 20,
    },
    {
        "id": "bench-humaneval",
        "project_id": "proj-code-agent-v2",
        "name": "HumanEval Plus",
        "version": "2.1",
        "source": "openai/human-eval",
        "total_tasks": 20,
    },
    # Project 2 benchmarks
    {
        "id": "bench-agentbench",
        "project_id": "proj-reasoning",
        "name": "AgentBench",
        "version": "1.0",
        "source": "thudm/AgentBench",
        "total_tasks": 20,
    },
    {
        "id": "bench-mathqa",
        "project_id": "proj-reasoning",
        "name": "MathQA Extended",
        "version": "3.0",
        "source": "math-ai/MathQA",
        "total_tasks": 20,
    },
]


def build_benchmarks():
    # type: () -> List[Dict]
    """Build benchmark records from definitions.

    Returns:
        List of benchmark dictionaries
    """
    return [
        {
            "id": bd["id"],
            "project_id": bd["project_id"],
            "name": bd["name"],
            "version": bd["version"],
            "source": bd["source"],
            "total_tasks": bd["total_tasks"],
            "metadata": {},
        }
        for bd in _BENCHMARK_DEFS
    ]


def build_tasks_for_benchmark(benchmark_id, n=DEFAULT_TOTAL_TASKS):
    # type: (str, int) -> List[Dict]
    """Build tasks for a benchmark.

    Args:
        benchmark_id: The benchmark ID
        n: Number of tasks to generate (default 20)

    Returns:
        List of task dictionaries
    """
    repos = [
        "django/django",
        "flask/flask",
        "pytorch/pytorch",
        "numpy/numpy",
        "pandas-dev/pandas",
        "scikit-learn/scikit-learn",
    ]
    tasks = []  # type: List[Dict]
    for i in range(n):
        cat = TASK_CATEGORIES[i % len(TASK_CATEGORIES)]
        diff = DIFFICULTIES[i % len(DIFFICULTIES)]
        lang = LANGUAGES[i % len(LANGUAGES)]
        repo = repos[i % len(repos)]
        tasks.append(
            {
                "id": "{}-task-{:04d}".format(benchmark_id, i),
                "benchmark_id": benchmark_id,
                "category": cat,
                "difficulty": diff,
                "language": lang,
                "repo": repo,
                "metadata": {},
            }
        )
    return tasks


def get_benchmark_defs():
    # type: () -> List[Dict]
    """Get the raw benchmark definitions.

    Returns:
        List of benchmark definition dictionaries
    """
    return _BENCHMARK_DEFS
