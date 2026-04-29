"""Trace data generation.

This module contains builders for OpenTelemetry Trace entities.
"""

import hashlib
import random
from datetime import timedelta

from ..constants import RNG_SEED, SCAFFOLDS
from .helpers import iso, now

_RNG = random.Random(RNG_SEED)


def build_traces(trajectories, exp_defs):
    # type: (List[Dict], List[Dict]) -> List[Dict]
    """Build 20 mock traces, some linked to trajectories.

    Args:
        trajectories: List of trajectory dictionaries
        exp_defs: List of experiment definitions

    Returns:
        List of trace dictionaries
    """
    traces = []  # type: List[Dict]
    linked = trajectories[:15]
    for i, traj in enumerate(linked):
        trace_id = traj["otel_trace_id"]
        span_count = _RNG.randint(5, 15)
        has_error = traj["outcome"] in ("failure", "error")
        traces.append(
            build_single_trace(
                trace_id,
                traj["scaffold"],
                span_count,
                has_error,
                now() - timedelta(minutes=_RNG.randint(5, 120)),
                rl_traj=traj,
                exp_defs=exp_defs,
            )
        )
    # 5 unlinked traces (production Agent)
    for i in range(5):
        trace_id = hashlib.md5("prod-trace-{}".format(i).encode()).hexdigest()
        scaffold = _RNG.choice(SCAFFOLDS)
        span_count = _RNG.randint(5, 15)
        has_error = _RNG.random() < 0.3
        traces.append(
            build_single_trace(
                trace_id,
                scaffold,
                span_count,
                has_error,
                now() - timedelta(minutes=_RNG.randint(5, 60)),
                rl_traj=None,
                exp_defs=exp_defs,
            )
        )
    return traces


def build_single_trace(trace_id, scaffold, span_count, has_error, start, rl_traj=None, exp_defs=None):
    # type: (str, str, int, bool, datetime, Optional[Dict], Optional[List[Dict]]) -> Dict
    """Build a single trace with spans.

    Args:
        trace_id: The trace ID
        scaffold: Scaffold name
        span_count: Number of spans to generate
        has_error: Whether the trace has errors
        start: Start timestamp
        rl_traj: Optional linked trajectory
        exp_defs: Optional experiment definitions for context

    Returns:
        Trace dictionary with spans
    """
    spans = build_spans(trace_id, span_count, has_error, start)
    total_dur = max(s["duration_ms"] for s in spans) if spans else 0
    rl_context = None
    if rl_traj:
        exp_name = rl_traj["experiment_id"]
        if exp_defs:
            for ed in exp_defs:
                if ed["id"] == rl_traj["experiment_id"]:
                    exp_name = ed["name"]
                    break
        rl_context = {
            "trajectory_id": rl_traj["id"],
            "experiment_id": rl_traj["experiment_id"],
            "experiment_name": exp_name,
            "iteration_num": rl_traj.get("iteration_num", 1),
            "reward": rl_traj["reward"],
            "outcome": rl_traj["outcome"],
            "turn_num": _RNG.randint(1, rl_traj["total_turns"]),
            "task_id": rl_traj["task_id"],
        }
    return {
        "trace_id": trace_id,
        "spans": spans,
        "duration_ms": total_dur,
        "span_count": len(spans),
        "has_error": has_error,
        "scaffold": scaffold,
        "start_time": iso(start),
        "service_name": "agent-scaffold",
        "status": "error" if has_error else "ok",
        "has_rl_context": rl_context is not None,
        "rl_context": rl_context,
    }


def build_spans(trace_id, count, has_error, start):
    # type: (str, int, bool, datetime) -> List[Dict]
    """Build spans for a trace.

    Args:
        trace_id: The trace ID
        count: Number of spans to generate
        has_error: Whether the trace has errors
        start: Start timestamp

    Returns:
        List of span dictionaries
    """
    span_names = [
        "agent.episode",
        "scaffold.dispatch",
        "tool.file_edit",
        "fs.read",
        "fs.write",
        "fs.cleanup",
        "tool.bash",
        "exec.run",
        "tool.web_search",
        "http.request",
        "llm.inference",
        "tool.grep",
        "tool.test_runner",
        "exec.compile",
        "exec.test",
    ]
    spans = []  # type: List[Dict]
    root_id = hashlib.md5("span:root:{}".format(trace_id).encode()).hexdigest()[:16]

    root_dur = _RNG.randint(1500, 8000)
    spans.append(
        {
            "span_id": root_id,
            "parent_span_id": None,
            "operation_name": "agent.episode",
            "service_name": "agent-scaffold",
            "start_time": iso(start),
            "duration_ms": root_dur,
            "status": "error" if has_error else "ok",
            "attributes": [{"key": "rl.trace_id", "value": trace_id}],
            "events": [],
            "children": [],
        }
    )

    offset = 0
    for i in range(1, count):
        sp_id = hashlib.md5("span:{}:{}".format(trace_id, i).encode()).hexdigest()[:16]
        op = span_names[i % len(span_names)]
        dur = _RNG.randint(100, root_dur // max(1, count - 1))
        is_err = has_error and i == count - 1
        offset += dur // 2

        attrs = [{"key": "service.name", "value": "agent-scaffold"}]
        evts = []  # type: List[Dict[str, Any]]
        if is_err:
            attrs.append({"key": "error", "value": "true"})
            attrs.append(
                {
                    "key": "error.message",
                    "value": "EACCES: permission denied",
                }
            )
            evts.append(
                {
                    "name": "exception",
                    "timestamp": iso(start + timedelta(milliseconds=offset)),
                    "attributes": {
                        "message": "EACCES: permission denied",
                    },
                }
            )

        p_id = root_id if i <= 3 else spans[max(1, i // 2)]["span_id"]

        spans.append(
            {
                "span_id": sp_id,
                "parent_span_id": p_id,
                "operation_name": op,
                "service_name": "agent-scaffold",
                "start_time": iso(start + timedelta(milliseconds=offset)),
                "duration_ms": dur,
                "status": "error" if is_err else "ok",
                "attributes": attrs,
                "events": evts,
                "children": [],
            }
        )

    return spans
