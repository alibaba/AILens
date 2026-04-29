"""Agent Service Metrics data generation.

This module contains builders for Agent Service and Metrics entities.
"""

import random
from datetime import timedelta

from ..constants import RNG_SEED, SCAFFOLDS
from .helpers import iso, now

_RNG = random.Random(RNG_SEED)


# ═══════════════════ Agent Service Definitions ═══════════════════

_AGENT_SERVICE_DEFS = [
    {
        "id": "svc-coding-prod",
        "project_id": "proj-code-agent-v2",
        "name": "coding-agent-prod",
        "scaffold": "claude_code",
        "model": "qwen3-72b",
        "environment": "production",
        "status": "active",
        "endpoint": "https://agent.example.com/coding",
        "otel_service_name": "coding-agent-prod",
        "tags": {"region": "us-east-1", "version": "v2.1"},
    },
    {
        "id": "svc-qa-staging",
        "project_id": "proj-code-agent-v2",
        "name": "qa-agent-staging",
        "scaffold": "openclaw",
        "model": "qwen3-8b",
        "environment": "staging",
        "status": "active",
        "endpoint": "https://agent-staging.example.com/qa",
        "otel_service_name": "qa-agent-staging",
        "tags": {"region": "us-west-2", "version": "v1.3"},
    },
]


def build_agent_services():
    # type: () -> List[Dict]
    """Build agent service records from definitions.

    Returns:
        List of agent service dictionaries
    """
    _now_ts = now()
    services = []  # type: List[Dict]
    for sd in _AGENT_SERVICE_DEFS:
        svc = dict(sd)
        svc["created_at"] = iso(_now_ts - timedelta(days=14))
        svc["updated_at"] = iso(_now_ts)
        services.append(svc)
    return services


def build_agent_service_metrics(services):
    # type: (List[Dict]) -> Dict[str, List[Dict]]
    """Build time-series metrics for each agent service (last 1h, per minute).

    Args:
        services: List of agent service dictionaries

    Returns:
        Dict keyed by service id, each containing a list of metrics
    """
    result = {}  # type: Dict[str, List[Dict]]
    metric_categories = {
        "llm": [
            "llm_call_count",
            "llm_latency_p50_ms",
            "llm_latency_p99_ms",
            "llm_input_tokens_per_min",
            "llm_output_tokens_per_min",
            "llm_error_rate",
            "llm_retry_rate",
        ],
        "tool": [
            "tool_call_count",
            "tool_success_rate",
            "tool_latency_p50_ms",
            "tool_latency_p99_ms",
        ],
        "skill": [
            "skill_trigger_count",
            "skill_success_rate",
        ],
        "cross": [
            "request_rpm",
            "e2e_latency_p50_ms",
            "e2e_latency_p99_ms",
            "request_success_rate",
            "concurrent_requests",
            "llm_time_ratio",
            "tool_time_ratio",
            "tokens_per_request",
        ],
    }
    base = now() - timedelta(hours=1)

    for svc in services:
        svc_metrics = []  # type: List[Dict]
        for cat, names in metric_categories.items():
            for mname in names:
                values = []  # type: List[Dict]
                for minute in range(60):
                    ts = base + timedelta(minutes=minute)
                    if "count" in mname or "rpm" in mname:
                        v = 5.0 + _RNG.gauss(0, 1.5)
                    elif "latency" in mname or "duration" in mname:
                        if "p99" in mname:
                            v = 3000.0 + _RNG.gauss(0, 800)
                        else:
                            v = 800.0 + _RNG.gauss(0, 200)
                    elif "rate" in mname or "ratio" in mname:
                        if "error" in mname:
                            v = 0.02 + _RNG.gauss(0, 0.01)
                        elif "success" in mname:
                            v = 0.95 + _RNG.gauss(0, 0.02)
                        else:
                            v = 0.5 + _RNG.gauss(0, 0.1)
                    elif "tokens" in mname:
                        v = 45000.0 + _RNG.gauss(0, 5000)
                    elif "concurrent" in mname:
                        v = 3.0 + _RNG.gauss(0, 1)
                    else:
                        v = 10.0 + _RNG.gauss(0, 2)
                    values.append(
                        {
                            "timestamp": iso(ts),
                            "value": round(max(0, v), 4),
                        }
                    )
                svc_metrics.append(
                    {
                        "metric_name": mname,
                        "category": cat,
                        "labels": {
                            "service": svc["name"],
                            "scaffold": svc["scaffold"],
                        },
                        "values": values,
                    }
                )
        result[svc["id"]] = svc_metrics
    return result


def build_agent_metrics():
    # type: () -> List[Dict]
    """Build legacy agent metrics (pre-service model).

    Returns:
        List of legacy agent metric dictionaries
    """
    agent_instances = [
        "coding-agent-01",
        "coding-agent-02",
        "qa-agent-01",
        "debug-agent-01",
        "refactor-agent-01",
    ]
    metric_names = [
        "agent_request_rpm",
        "agent_request_latency_p99_ms",
        "agent_error_rate",
        "agent_llm_tokens_per_min",
        "agent_concurrent_requests",
    ]
    metrics = []  # type: List[Dict]
    base = now() - timedelta(hours=1)

    for agent in agent_instances:
        for mname in metric_names:
            values = []  # type: List[Dict]
            for minute in range(60):
                ts = base + timedelta(minutes=minute)
                if mname == "agent_request_rpm":
                    v = 5.0 + _RNG.gauss(0, 1.5)
                elif mname == "agent_request_latency_p99_ms":
                    v = 3000.0 + _RNG.gauss(0, 800)
                elif mname == "agent_error_rate":
                    v = 0.02 + _RNG.gauss(0, 0.01)
                elif mname == "agent_llm_tokens_per_min":
                    v = 45000.0 + _RNG.gauss(0, 5000)
                else:
                    v = 3.0 + _RNG.gauss(0, 1)
                values.append(
                    {
                        "timestamp": iso(ts),
                        "value": round(max(0, v), 4),
                    }
                )
            metrics.append(
                {
                    "metric_name": mname,
                    "labels": {
                        "agent": agent,
                        "scaffold": _RNG.choice(SCAFFOLDS),
                    },
                    "values": values,
                }
            )
    return metrics


def get_agent_service_defs():
    # type: () -> List[Dict]
    """Get the raw agent service definitions.

    Returns:
        List of agent service definition dictionaries
    """
    return _AGENT_SERVICE_DEFS
