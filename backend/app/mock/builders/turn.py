"""Turn and Event data generation.

This module contains builders for Turn and Event entities.
"""

import hashlib
from datetime import datetime, timedelta, timezone

from ..constants import RNG_SEED

# Mock tools for testing (TraceQL discovery available but not used in mocks)
MOCK_TOOLS = ["bash", "file_edit", "web_search", "read_file", "submit"]
import random

from .helpers import iso, now, uid

_RNG = random.Random(RNG_SEED)


# ═══════════════════ Reasoning Prompts ─══════════════════

_REASONING_PROMPTS = [
    "I need to understand the failing test before making changes...",
    "Let me read the source file to find the issue...",
    "I'll try running the tests to see current state...",
    "The error suggests a missing import, let me fix that...",
    "Let me verify my changes by running the test suite...",
    "I need to check if there are related test files...",
    "Looking at the stack trace, the issue is in the handler...",
    "Let me refactor this function to handle edge cases...",
    "I should check the configuration file for issues...",
    "Let me try a different approach to solve this...",
    "The previous attempt failed, I'll check permissions...",
    "Running the full test suite to confirm the fix...",
    "Let me look at the documentation for this API...",
    "I need to add error handling for this edge case...",
    "Checking if there are similar issues in the codebase...",
]


def build_turns_for_trajectory(traj):
    # type: (Dict) -> List[Dict]
    """Generate turns + events for a single trajectory (on-demand).

    Args:
        traj: The trajectory dictionary

    Returns:
        List of turn dictionaries with embedded events
    """
    turns = []  # type: List[Dict]
    raw = traj["created_at"].replace("Z", "+00:00")
    try:
        base_ts = datetime.strptime(raw[:23], "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=timezone.utc)
    except Exception:
        base_ts = now()

    for t_num in range(1, traj["total_turns"] + 1):
        turn_id = uid("turn", traj["id"], t_num)
        tool = _RNG.choice(MOCK_TOOLS)
        has_error = traj["outcome"] != "success" and t_num >= traj.get("first_error_turn", 999) and _RNG.random() < 0.4
        turn_dur = _RNG.randint(1200, 4500)
        turn_tok = _RNG.randint(200, 900)

        events = []  # type: List[Dict]
        ev_ts = base_ts + timedelta(seconds=t_num * 3)

        # Event 1: reasoning
        events.append(
            {
                "id": uid("ev", turn_id, 1),
                "turn_id": turn_id,
                "trajectory_id": traj["id"],
                "event_num": 1,
                "type": "reasoning",
                "action": None,
                "llm": {
                    "prompt_tokens": _RNG.randint(100, 500),
                    "completion_tokens": _RNG.randint(30, 200),
                    "model": "qwen3-8b",
                    "latency_ms": _RNG.randint(300, 1200),
                },
                "observation": None,
                "timestamp": iso(ev_ts),
                "duration_ms": _RNG.randint(300, 1200),
                "error": None,
                "otel_span_id": hashlib.md5("span:r:{}".format(turn_id).encode()).hexdigest()[:16],
            }
        )

        # Event 2: action
        err_msg = None
        if has_error:
            err_msg = _RNG.choice(
                [
                    "EACCES: permission denied",
                    "TIMEOUT after 30s",
                    "FileNotFoundError: No such file or directory",
                    "subprocess.CalledProcessError: exit code 1",
                ]
            )
        tool_output = "Success" if not has_error else (err_msg or "")
        events.append(
            {
                "id": uid("ev", turn_id, 2),
                "turn_id": turn_id,
                "trajectory_id": traj["id"],
                "event_num": 2,
                "type": "action",
                "action": {
                    "tool_name": tool,
                    "tool_input": "{} command for turn {}".format(tool, t_num),
                    "tool_output": tool_output,
                    "status": "error" if has_error else "success",
                },
                "llm": None,
                "observation": None,
                "timestamp": iso(ev_ts + timedelta(milliseconds=500)),
                "duration_ms": _RNG.randint(200, 2000),
                "error": err_msg,
                "otel_span_id": hashlib.md5("span:a:{}".format(turn_id).encode()).hexdigest()[:16],
            }
        )

        # Event 3: observation
        obs_content = _RNG.choice(_REASONING_PROMPTS) if not has_error else "Error: {}".format(err_msg)
        events.append(
            {
                "id": uid("ev", turn_id, 3),
                "turn_id": turn_id,
                "trajectory_id": traj["id"],
                "event_num": 3,
                "type": "observation",
                "action": None,
                "llm": None,
                "observation": {
                    "content": obs_content,
                    "reward": round(_RNG.uniform(-0.1, 0.3), 3) if not has_error else 0.0,
                },
                "timestamp": iso(ev_ts + timedelta(seconds=1)),
                "duration_ms": _RNG.randint(50, 300),
                "error": None,
                "otel_span_id": hashlib.md5("span:o:{}".format(turn_id).encode()).hexdigest()[:16],
            }
        )

        turns.append(
            {
                "id": turn_id,
                "trajectory_id": traj["id"],
                "turn_num": t_num,
                "total_tokens": turn_tok,
                "duration_ms": turn_dur,
                "reward": round(_RNG.uniform(-0.1, 0.3), 3),
                "has_error": has_error,
                "tool_name": tool,
                "tool_succeeded": not has_error,
                "otel_root_span_id": hashlib.md5("rootspan:{}".format(turn_id).encode()).hexdigest()[:16],
                "events": events,
            }
        )

    return turns
