"""TraceQL executor - Executes parsed TraceQL queries against mock data.

Converts TraceQL AST to operations on mock store data (trajectories, turns, events).
"""

import re
import statistics
from collections import defaultdict
from typing import Any, Dict, List

from .parser import AggregationType, OperatorType, TraceQLAggregation, TraceQLCondition, TraceQLQuery


class TraceQLExecutor:
    """Executes TraceQL queries against mock data store."""

    def __init__(self, store):
        """Initialize with mock data store."""
        self.store = store

    def execute(self, query: TraceQLQuery, **filters) -> Dict[str, Any]:
        """Execute TraceQL query and return results."""
        # Get base data
        experiment_id = filters.get("experiment_id")
        if not experiment_id:
            return {"resultType": "empty", "result": []}

        # Get trajectories and their turns/events
        trajectories = self.store.get_trajectories(experiment_id=experiment_id)

        # Apply additional filters
        if filters.get("scaffold"):
            trajectories = [t for t in trajectories if t.get("scaffold") == filters["scaffold"]]
        if filters.get("language"):
            trajectories = [t for t in trajectories if t.get("task_language") == filters["language"]]

        # Execute selector to get matching spans
        matching_spans = self._execute_selector(query.selector, trajectories)

        # Apply aggregation if present
        if query.aggregation:
            return self._execute_aggregation(query.aggregation, matching_spans)
        else:
            # Return raw spans (for debugging/testing)
            return {
                "resultType": "spans",
                "result": matching_spans[:100],  # Limit for performance
            }

    def _execute_selector(self, selector, trajectories: List[Dict]) -> List[Dict]:
        """Execute selector conditions to find matching spans."""
        matching_spans = []

        for trajectory in trajectories:
            turns = self.store.get_turns(trajectory["id"])

            for turn in turns:
                # Create span representation from turn + events
                events = turn.get("events", [])

                for event in events:
                    span = self._create_span_from_event(event, turn, trajectory)

                    # Check if span matches all conditions
                    if self._span_matches_conditions(span, selector.conditions):
                        matching_spans.append(span)

                # Also create span from turn itself (for tool-level analysis)
                turn_span = self._create_span_from_turn(turn, trajectory)
                if self._span_matches_conditions(turn_span, selector.conditions):
                    matching_spans.append(turn_span)

        return matching_spans

    def _create_span_from_event(self, event: Dict, turn: Dict, trajectory: Dict) -> Dict:
        """Create span representation from event data."""
        span = {
            "span_id": event["id"],
            "trace_id": trajectory.get("otel_trace_id", f"mock-{trajectory['id']}"),
            "parent_span_id": turn["id"],
            # Intrinsics (span:*)
            "span:name": event.get("type", "unknown"),
            "span:duration": event.get("duration_ms", 0),
            "span:status": "error" if event.get("error") else "ok",
            "span:statusMessage": event.get("error") or "",
            "span:kind": "internal",
            "span:id": event["id"],
            "span:parentID": turn["id"],
            # Trace intrinsics (trace:*)
            "trace:duration": trajectory.get("duration_ms", 0),
            "trace:rootName": f"{trajectory.get('scaffold', 'unknown')} execution",
            "trace:rootService": "ai-lens",
            "trace:id": trajectory.get("otel_trace_id", f"mock-{trajectory['id']}"),
            # Span attributes (span.*)
            "span.type": event.get("type"),
            "span.error": event.get("error"),
            "span.otel_span_id": event.get("otel_span_id"),
            # Resource attributes (resource.*)
            "resource.service.name": "ai-lens",
            "resource.scaffold": trajectory.get("scaffold"),
            "resource.deployment.environment": "mock",
            "resource.experiment_id": trajectory.get("experiment_id"),
            # Tool attributes for action events
            "span.tool_name": None,
            "span.tool_input": None,
            "span.tool_output": None,
            "span.tool_succeeded": None,
        }

        # Add tool-specific attributes for action events
        if event.get("type") == "action" and event.get("action"):
            action = event["action"]
            span.update(
                {
                    "span.tool_name": action.get("tool_name"),
                    "span.tool_input": action.get("tool_input"),
                    "span.tool_output": action.get("tool_output"),
                    "span.tool_succeeded": not bool(event.get("error")),
                }
            )

        return span

    def _create_span_from_turn(self, turn: Dict, trajectory: Dict) -> Dict:
        """Create span representation from turn data (for tool-level analysis)."""
        return {
            "span_id": turn["id"],
            "trace_id": trajectory.get("otel_trace_id", f"mock-{trajectory['id']}"),
            "parent_span_id": trajectory["id"],
            # Intrinsics
            "span:name": f"Tool: {turn.get('tool_name', 'unknown')}",
            "span:duration": turn.get("duration_ms", 0),
            "span:status": "error" if turn.get("has_error") else "ok",
            "span:kind": "internal",
            "span:id": turn["id"],
            "span:parentID": trajectory["id"],
            # Trace intrinsics
            "trace:duration": trajectory.get("duration_ms", 0),
            "trace:rootName": f"{trajectory.get('scaffold', 'unknown')} execution",
            "trace:rootService": "ai-lens",
            "trace:id": trajectory.get("otel_trace_id", f"mock-{trajectory['id']}"),
            # Span attributes
            "span.tool_name": turn.get("tool_name"),
            "span.tool_succeeded": turn.get("tool_succeeded"),
            "span.has_error": turn.get("has_error"),
            "span.reward": turn.get("reward"),
            "span.total_tokens": turn.get("total_tokens"),
            # Resource attributes
            "resource.service.name": "ai-lens",
            "resource.scaffold": trajectory.get("scaffold"),
            "resource.deployment.environment": "mock",
            "resource.experiment_id": trajectory.get("experiment_id"),
            "resource.task_id": trajectory.get("task_id"),
            "resource.task_language": trajectory.get("task_language"),
        }

    def _span_matches_conditions(self, span: Dict, conditions: List[TraceQLCondition]) -> bool:
        """Check if span matches all conditions."""
        for condition in conditions:
            if not self._span_matches_condition(span, condition):
                return False
        return True

    def _span_matches_condition(self, span: Dict, condition: TraceQLCondition) -> bool:
        """Check if span matches single condition."""
        # Get field value from span
        if condition.is_intrinsic:
            field_key = f"{condition.scope}:{condition.field}"
        else:
            field_key = f"{condition.scope}.{condition.field}"

        span_value = span.get(field_key)

        # Handle nil comparisons
        if condition.value is None:
            if condition.operator == OperatorType.EQ:
                return span_value is None
            elif condition.operator == OperatorType.NE:
                return span_value is not None

        # If span value is None and we're not checking for nil
        if span_value is None:
            return False

        # Apply operator
        return self._compare_values(span_value, condition.operator, condition.value)

    def _compare_values(self, span_value, operator: OperatorType, condition_value) -> bool:
        """Compare span value with condition value using operator."""
        try:
            if operator == OperatorType.EQ:
                return span_value == condition_value
            elif operator == OperatorType.NE:
                return span_value != condition_value
            elif operator == OperatorType.GT:
                return span_value > condition_value
            elif operator == OperatorType.LT:
                return span_value < condition_value
            elif operator == OperatorType.GE:
                return span_value >= condition_value
            elif operator == OperatorType.LE:
                return span_value <= condition_value
            elif operator == OperatorType.MATCH:
                return re.search(str(condition_value), str(span_value)) is not None
            elif operator == OperatorType.NOT_MATCH:
                return re.search(str(condition_value), str(span_value)) is None
        except (TypeError, ValueError):
            # Type mismatch or invalid regex
            return False

        return False

    def _execute_aggregation(self, aggregation: TraceQLAggregation, spans: List[Dict]) -> Dict[str, Any]:
        """Execute aggregation function on matching spans."""
        if not spans:
            return {"resultType": "matrix", "result": []}

        # Group spans if group_by is specified
        if aggregation.group_by:
            groups = self._group_spans(spans, aggregation.group_by)
        else:
            groups = {"": spans}  # Single group

        # Apply aggregation function to each group
        result = []
        for group_key, group_spans in groups.items():
            agg_result = self._apply_aggregation_function(aggregation, group_spans)

            # Build metric labels
            metric_labels = {}
            if aggregation.group_by and group_key:
                # Parse group key back to labels
                for i, field in enumerate(aggregation.group_by):
                    parts = group_key.split("|")
                    if i < len(parts):
                        field_value = parts[i].split("=", 1)[1] if "=" in parts[i] else parts[i]
                        metric_labels[field] = field_value

            result.append(
                {
                    "metric": metric_labels,
                    "value": agg_result,
                }
            )

        return {
            "resultType": "matrix",
            "result": result,
        }

    def _group_spans(self, spans: List[Dict], group_by: List[str]) -> Dict[str, List[Dict]]:
        """Group spans by specified fields."""
        groups = defaultdict(list)

        for span in spans:
            # Build group key
            group_parts = []
            for field in group_by:
                # Handle both intrinsic and attribute fields
                if ":" in field:
                    value = span.get(field, "unknown")
                elif "." in field:
                    value = span.get(field, "unknown")
                else:
                    # Try both intrinsic and attribute
                    value = (
                        span.get(f"span:{field}")
                        or span.get(f"span.{field}")
                        or span.get(f"resource.{field}")
                        or "unknown"
                    )

                group_parts.append(f"{field}={value}")

            group_key = "|".join(group_parts)
            groups[group_key].append(span)

        return dict(groups)

    def _apply_aggregation_function(self, aggregation: TraceQLAggregation, spans: List[Dict]) -> float:
        """Apply aggregation function to spans."""
        if not spans:
            return 0.0

        if aggregation.function == AggregationType.COUNT:
            return len(spans)

        elif aggregation.function == AggregationType.RATE:
            # Mock implementation: return count per second
            # In real implementation, this would consider time window
            return len(spans) / 60.0  # Assume 1-minute window

        elif aggregation.function in (
            AggregationType.AVG,
            AggregationType.SUM,
            AggregationType.MAX,
            AggregationType.MIN,
            AggregationType.QUANTILE,
        ):
            # Need field value for these functions
            field = aggregation.field
            if not field:
                return 0.0

            # Extract values
            values = []
            for span in spans:
                # Handle intrinsic vs attribute fields
                if ":" in field:
                    value = span.get(field)
                elif "." in field:
                    value = span.get(field)
                else:
                    # Try different prefixes
                    value = span.get(f"span:{field}") or span.get(f"span.{field}") or span.get(f"resource.{field}")

                if isinstance(value, (int, float)):
                    values.append(value)

            if not values:
                return 0.0

            # Apply function
            if aggregation.function == AggregationType.AVG:
                return sum(values) / len(values)
            elif aggregation.function == AggregationType.SUM:
                return sum(values)
            elif aggregation.function == AggregationType.MAX:
                return max(values)
            elif aggregation.function == AggregationType.MIN:
                return min(values)
            elif aggregation.function == AggregationType.QUANTILE:
                if aggregation.quantile is not None:
                    return statistics.quantiles(values, n=100)[int(aggregation.quantile * 100) - 1]
                else:
                    return statistics.median(values)

        return 0.0
