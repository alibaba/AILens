"""Builder modules for mock data generation.

This package contains individual builder modules for each data type,
each with a single responsibility for generating that specific entity.
"""

from .agent_service import (
    build_agent_metrics,
    build_agent_service_metrics,
    build_agent_services,
    get_agent_service_defs,
)
from .alert import (
    build_active_alerts,
    build_alert_rules,
)
from .benchmark import (
    build_benchmarks,
    build_tasks_for_benchmark,
    get_benchmark_defs,
)
from .experiment import (
    build_experiments,
    get_experiment_defs,
)
from .helpers import (
    convergence_curve,
    get_rng,
    iso,
    now,
    std,
    uid,
)
from .iteration import (
    build_iterations,
)
from .project import (
    add_project,
    build_projects,
    get_project_defs,
)
from .trace import (
    build_single_trace,
    build_spans,
    build_traces,
)
from .trajectory import (
    build_annotation,
    build_trajectories_for_iteration,
)
from .turn import (
    build_turns_for_trajectory,
)

__all__ = [
    # Helpers
    "uid",
    "iso",
    "now",
    "std",
    "convergence_curve",
    "get_rng",
    # Project
    "build_projects",
    "add_project",
    "get_project_defs",
    # Benchmark
    "build_benchmarks",
    "build_tasks_for_benchmark",
    "get_benchmark_defs",
    # Experiment
    "build_experiments",
    "get_experiment_defs",
    # Iteration
    "build_iterations",
    # Trajectory
    "build_trajectories_for_iteration",
    "build_annotation",
    # Turn
    "build_turns_for_trajectory",
    # Trace
    "build_traces",
    "build_single_trace",
    "build_spans",
    # Alert
    "build_alert_rules",
    "build_active_alerts",
    # Agent Service
    "build_agent_services",
    "build_agent_service_metrics",
    "build_agent_metrics",
    "get_agent_service_defs",
]
