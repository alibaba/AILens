"""Helper functions for mock data generation.

This module provides utility functions used across all builder modules,
including ID generation, timestamp formatting, and statistical helpers.
"""

import hashlib
import math

# Import the RNG seed for deterministic generation
import random
from datetime import datetime, timezone

_RNG = random.Random(42)  # Must match constants.RNG_SEED


def uid(prefix, *parts):
    # type: (str, *Any) -> str
    """Generate a unique identifier with a given prefix.

    Args:
        prefix: The prefix for the ID (e.g., 'traj', 'iter', 'proj')
        *parts: Components to include in the hash

    Returns:
        A unique identifier like 'traj-abc123def456'
    """
    raw = "{}:{}".format(prefix, "|".join(str(p) for p in parts))
    return "{}-{}".format(prefix, hashlib.md5(raw.encode()).hexdigest()[:12])


def iso(dt):
    # type: (datetime) -> str
    """Format a datetime as ISO 8601 string with milliseconds.

    Args:
        dt: The datetime to format

    Returns:
        ISO 8601 formatted string like '2024-01-15T10:30:00.123Z'
    """
    return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def now():
    # type: () -> datetime
    """Get the reference 'now' timestamp for mock data.

    Returns:
        A fixed datetime (2026-03-21 14:00:00 UTC) for reproducible data
    """
    return datetime(2026, 3, 21, 14, 0, 0, tzinfo=timezone.utc)


def std(vals):
    # type: (list) -> float
    """Calculate the standard deviation of a list of values.

    Args:
        vals: List of numeric values

    Returns:
        The standard deviation
    """
    if not vals:
        return 0.0
    m = sum(vals) / len(vals)
    return math.sqrt(sum((v - m) ** 2 for v in vals) / len(vals))


def convergence_curve(iteration_num, base, ceil, rate=0.06):
    # type: (int, float, float, float) -> float
    """Generate a logistic-like convergence value with noise.

    Used to simulate improving metrics over training iterations.

    Args:
        iteration_num: The current iteration number
        base: The minimum/baseline value
        ceil: The maximum/ceiling value
        rate: The convergence rate (default 0.06)

    Returns:
        A value between base and ceil, increasing with iteration
    """
    progress = 1 - math.exp(-rate * iteration_num)
    value = base + (ceil - base) * progress
    noise = _RNG.gauss(0, 0.02)
    return max(0.0, min(1.0, value + noise))


# Export RNG for use in other modules that need consistent randomness
def get_rng():
    # type: () -> random.Random
    """Get the shared random number generator.

    Returns:
        The shared RNG instance for deterministic mock data generation
    """
    return _RNG
