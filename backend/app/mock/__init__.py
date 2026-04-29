"""Mock data package for AI Lens.

This package provides consistent, reproducible mock data for testing
and development. Data is generated on-demand using a fixed seed.

Usage:
    from ailens.app.mock import store

    # Get all projects
    projects = store.get_projects()

    # Get trajectories for an experiment
    trajectories = store.get_trajectories(experiment_id='exp-grpo-cc')

    # Get turns for a trajectory (on-demand generation)
    turns = store.get_turns('traj-abc123')

The store is a singleton - data is generated once and cached.
"""

# Export constants for backward compatibility
from .constants import (
    CAT_BASE_PASS,
    DIFFICULTIES,
    LANGUAGES,
    PATTERN_TYPES,
    SCAFFOLDS,
    SYSTEM_PROMPTS,
    TASK_CATEGORIES,
    TOOL_SCHEMAS,
)
from .store import MockDataStore, store

# TOOLS removed - using TraceQL dynamic discovery

__all__ = [
    "store",
    "MockDataStore",
    "TASK_CATEGORIES",
    "SCAFFOLDS",
    "DIFFICULTIES",
    "LANGUAGES",
    "PATTERN_TYPES",
    "SYSTEM_PROMPTS",
    "TOOL_SCHEMAS",
    "CAT_BASE_PASS",
]
# TOOLS removed from exports
