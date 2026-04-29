"""Constants for mock data generation.

This module contains all constant values used throughout the mock data
generation system, including task categories, scaffolds, tools, and
base configuration values.
"""

# ── Deterministic seed ──
# Using a fixed seed for reproducible mock data
RNG_SEED = 42

# ── Task Configuration ──
TASK_CATEGORIES = ["code-fix", "test-gen", "refactor", "debug"]
DIFFICULTIES = ["easy", "medium", "hard"]
LANGUAGES = ["python", "java", "typescript", "go"]

# ── Agent Configuration ──
SCAFFOLDS = ["claude_code", "openclaw", "aider"]
SYSTEM_PROMPTS = ["p2", "p3"]
TOOL_SCHEMAS = ["json", "xml"]
# TOOLS constant removed - now using TraceQL dynamic discovery

# ── Pattern Types for Annotations ──
PATTERN_TYPES = [
    "action_loop",
    "tool_error",
    "timeout",
    "token_explosion",
    "ineffective_action",
    "early_abandon",
    "repeat_error",
]

# ── Category-specific base pass rates ──
# Used for trajectory outcome generation
CAT_BASE_PASS = {
    "code-fix": 0.55,
    "test-gen": 0.70,
    "debug": 0.40,
    "refactor": 0.30,
}

# ── Default Configuration ──
DEFAULT_MAX_TURNS = 20
DEFAULT_TOTAL_TASKS = 20
TRAJECTORIES_PER_ITERATION = 100
ITERATIONS_PER_EXPERIMENT = 50
