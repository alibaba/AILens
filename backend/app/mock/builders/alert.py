"""Alert data generation.

This module contains builders for Alert Rule and Active Alert entities.
"""

import random
from datetime import timedelta

from ..constants import RNG_SEED
from .helpers import iso, now

_RNG = random.Random(RNG_SEED)


# ═══════════════════ Alert Rule Definitions ═══════════════════

_ALERT_RULE_DEFS = [
    {
        "id": "rule-1",
        "name": "AgentLatencyHigh",
        "expression": "histogram_quantile(0.99, agent_request_duration_seconds_bucket) > 30",
        "threshold": 30.0,
        "severity": "critical",
        "for_duration": "5m",
    },
    {
        "id": "rule-2",
        "name": "AgentErrorRateHigh",
        "expression": "rate(agent_request_errors_total[5m]) > 0.05",
        "threshold": 0.05,
        "severity": "warning",
        "for_duration": "3m",
    },
    {
        "id": "rule-3",
        "name": "LLMErrorRateHigh",
        "expression": "rate(agent_llm_errors_total[5m]) > 0.1",
        "threshold": 0.1,
        "severity": "critical",
        "for_duration": "3m",
    },
    {
        "id": "rule-4",
        "name": "TokenConsumptionSpike",
        "expression": "rate(agent_llm_tokens_total[5m]) > 2",
        "threshold": 2.0,
        "severity": "warning",
        "for_duration": "5m",
    },
    {
        "id": "rule-5",
        "name": "TrainingRewardStagnant",
        "expression": "abs(mean_reward delta) < 0.01",
        "threshold": 0.01,
        "severity": "warning",
        "for_duration": "30m",
    },
]


def build_alert_rules():
    # type: () -> List[Dict]
    """Build alert rule records from definitions.

    Returns:
        List of alert rule dictionaries with timestamps and configuration
    """
    _now_ts = now()
    result = []  # type: List[Dict]
    for r in _ALERT_RULE_DEFS:
        entry = dict(r)
        entry["enabled"] = True
        entry["notification_channels"] = ["dingtalk", "email"]
        entry["created_at"] = iso(_now_ts - timedelta(days=7))
        entry["updated_at"] = iso(_now_ts - timedelta(days=1))
        result.append(entry)
    return result


def add_alert_rule(rules, rule_data):
    # type: (List[Dict], Dict) -> Dict
    """Add a new alert rule to the list.

    Args:
        rules: The list of existing alert rules
        rule_data: The rule data to add

    Returns:
        The newly created alert rule
    """
    rule = dict(rule_data)
    rule["id"] = "rule-{}".format(len(rules) + 1)
    rule["enabled"] = True
    rule["created_at"] = iso(now())
    rule["updated_at"] = iso(now())
    rules.append(rule)
    return rule


# ═══════════════════ Active Alerts ═══════════════════

_ACTIVE_ALERT_DEFS = [
    {
        "id": "alert-1",
        "rule_id": "rule-1",
        "rule_name": "AgentLatencyHigh",
        "severity": "critical",
        "agent_name": "coding-agent-prod",
        "current_value": 35.2,
        "threshold": 30.0,
        "firing_offset_minutes": 25,
        "labels": {
            "agent": "coding-agent-prod",
            "scaffold": "claude_code",
        },
    },
    {
        "id": "alert-2",
        "rule_id": "rule-3",
        "rule_name": "LLMErrorRateHigh",
        "severity": "critical",
        "agent_name": "coding-agent-prod",
        "current_value": 0.12,
        "threshold": 0.1,
        "firing_offset_minutes": 27,
        "labels": {
            "agent": "coding-agent-prod",
            "scaffold": "claude_code",
        },
    },
    {
        "id": "alert-3",
        "rule_id": "rule-4",
        "rule_name": "TokenConsumptionSpike",
        "severity": "warning",
        "agent_name": "qa-agent-staging",
        "current_value": 2.5,
        "threshold": 2.0,
        "firing_offset_minutes": 55,
        "labels": {
            "agent": "qa-agent-staging",
            "scaffold": "openclaw",
        },
    },
]


def build_active_alerts():
    # type: () -> List[Dict]
    """Build active alert records from definitions.

    Returns:
        List of active alert dictionaries with firing timestamps
    """
    _now_ts = now()
    result = []  # type: List[Dict]
    for a in _ACTIVE_ALERT_DEFS:
        entry = {
            "id": a["id"],
            "rule_id": a["rule_id"],
            "rule_name": a["rule_name"],
            "severity": a["severity"],
            "agent_name": a["agent_name"],
            "current_value": a["current_value"],
            "threshold": a["threshold"],
            "firing_since": iso(_now_ts - timedelta(minutes=a["firing_offset_minutes"])),
            "status": "firing",
            "labels": a["labels"],
        }
        result.append(entry)
    return result
