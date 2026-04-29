"""TraceQL query parser - Parses TraceQL syntax into executable AST.

Supports basic TraceQL syntax:
- Span selectors: { span.foo = "bar" }
- Intrinsics: { span:name = "HTTP GET" }
- Aggregations: | count(), | rate() by (field)
- Comparisons: =, !=, >, <, >=, <=, =~, !~
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Union


class OperatorType(Enum):
    """Comparison operator types."""

    EQ = "="
    NE = "!="
    GT = ">"
    LT = "<"
    GE = ">="
    LE = "<="
    MATCH = "=~"
    NOT_MATCH = "!~"


class AggregationType(Enum):
    """Aggregation function types."""

    COUNT = "count"
    RATE = "rate"
    AVG = "avg"
    SUM = "sum"
    MAX = "max"
    MIN = "min"
    QUANTILE = "quantile_over_time"


@dataclass
class TraceQLCondition:
    """Single condition in TraceQL selector."""

    scope: str  # "span", "resource", "trace", "event"
    field: str  # "http.method", "name", "duration"
    operator: OperatorType
    value: Union[str, int, float, bool]
    is_intrinsic: bool = False  # True for span:name, False for span.http.method


@dataclass
class TraceQLSelector:
    """Span selector with conditions."""

    conditions: List[TraceQLCondition]


@dataclass
class TraceQLAggregation:
    """Aggregation function."""

    function: AggregationType
    field: Optional[str] = None  # For avg(field), sum(field), etc.
    group_by: List[str] = None  # For by (field1, field2)
    quantile: Optional[float] = None  # For quantile_over_time(field, 0.95)


@dataclass
class TraceQLQuery:
    """Parsed TraceQL query."""

    selector: TraceQLSelector
    aggregation: Optional[TraceQLAggregation] = None


class TraceQLParser:
    """TraceQL query parser."""

    def __init__(self):
        self.operators = {
            "=": OperatorType.EQ,
            "!=": OperatorType.NE,
            ">": OperatorType.GT,
            "<": OperatorType.LT,
            ">=": OperatorType.GE,
            "<=": OperatorType.LE,
            "=~": OperatorType.MATCH,
            "!~": OperatorType.NOT_MATCH,
        }

    def parse(self, query: str) -> TraceQLQuery:
        """Parse TraceQL query string into AST."""
        query = query.strip()

        # Split selector and aggregation
        if "|" in query:
            selector_part, agg_part = query.split("|", 1)
            selector = self._parse_selector(selector_part.strip())
            aggregation = self._parse_aggregation(agg_part.strip())
        else:
            selector = self._parse_selector(query)
            aggregation = None

        return TraceQLQuery(selector=selector, aggregation=aggregation)

    def _parse_selector(self, selector_str: str) -> TraceQLSelector:
        """Parse selector part: { span.foo = "bar" && resource.service = "frontend" }"""
        # Remove braces
        selector_str = selector_str.strip()
        if selector_str.startswith("{") and selector_str.endswith("}"):
            selector_str = selector_str[1:-1].strip()

        # Handle empty selector
        if not selector_str:
            return TraceQLSelector(conditions=[])

        # Split conditions by &&
        condition_strs = self._split_conditions(selector_str)
        conditions = []

        for cond_str in condition_strs:
            condition = self._parse_condition(cond_str.strip())
            if condition:
                conditions.append(condition)

        return TraceQLSelector(conditions=conditions)

    def _split_conditions(self, conditions_str: str) -> List[str]:
        """Split conditions by && operator."""
        # Current implementation handles simple AND conditions (&&)
        # NOTE: Does not support OR (||) operations or complex nested parentheses
        # Future enhancement needed for: (field1 = val1 || field2 = val2) && field3 = val3
        parts = []
        current = ""
        i = 0

        while i < len(conditions_str):
            if i < len(conditions_str) - 1 and conditions_str[i : i + 2] == "&&":
                parts.append(current.strip())
                current = ""
                i += 2
                while i < len(conditions_str) and conditions_str[i] == " ":
                    i += 1
            else:
                current += conditions_str[i]
                i += 1

        if current.strip():
            parts.append(current.strip())

        return parts

    def _parse_condition(self, cond_str: str) -> Optional[TraceQLCondition]:
        """Parse single condition: span.http.method = "GET" """
        # Pattern: field operator value
        pattern = r"^(\w+(?:\.\w+)*|\w+:\w+)\s*(>=|<=|!=|=~|!~|=|>|<)\s*(.+)$"
        match = re.match(pattern, cond_str)

        if not match:
            return None

        field_path = match.group(1)
        operator_str = match.group(2)
        value_str = match.group(3).strip()

        # Parse field path (scope.field or scope:field)
        if ":" in field_path:
            scope, field = field_path.split(":", 1)
            is_intrinsic = True
        elif "." in field_path:
            parts = field_path.split(".", 1)
            scope = parts[0]
            field = parts[1]
            is_intrinsic = False
        else:
            # Default to span scope
            scope = "span"
            field = field_path
            is_intrinsic = False

        # Parse operator
        operator = self.operators.get(operator_str)
        if not operator:
            return None

        # Parse value
        value = self._parse_value(value_str)

        return TraceQLCondition(
            scope=scope,
            field=field,
            operator=operator,
            value=value,
            is_intrinsic=is_intrinsic,
        )

    def _parse_value(self, value_str: str) -> Union[str, int, float, bool]:
        """Parse value: "string", 123, 1.5, true, false, nil"""
        value_str = value_str.strip()

        # String literal
        if value_str.startswith('"') and value_str.endswith('"'):
            return value_str[1:-1]  # Remove quotes

        # Boolean
        if value_str.lower() == "true":
            return True
        elif value_str.lower() == "false":
            return False
        elif value_str.lower() == "nil":
            return None

        # Number
        try:
            if "." in value_str:
                return float(value_str)
            else:
                return int(value_str)
        except ValueError:
            pass

        # Duration (convert to milliseconds)
        duration_match = re.match(r"^(\d+(?:\.\d+)?)(ns|us|ms|s|m|h)$", value_str)
        if duration_match:
            number = float(duration_match.group(1))
            unit = duration_match.group(2)

            # Convert to milliseconds
            multipliers = {
                "ns": 0.000001,
                "us": 0.001,
                "ms": 1.0,
                "s": 1000.0,
                "m": 60000.0,
                "h": 3600000.0,
            }
            return int(number * multipliers[unit])

        # Default: return as string without quotes
        return value_str

    def _parse_aggregation(self, agg_str: str) -> Optional[TraceQLAggregation]:
        """Parse aggregation: count() > 5, rate() by (service), avg(duration) by (tool)"""
        # Pattern for aggregation with optional grouping
        # Examples:
        # - count()
        # - count() > 5  (filter, not aggregation)
        # - rate() by (service)
        # - avg(duration) by (tool, scaffold)
        # - quantile_over_time(duration, 0.95) by (service)

        # First check for 'by' clause
        group_by = []
        by_match = re.search(r"by\s*\(\s*([^)]+)\s*\)", agg_str)
        if by_match:
            group_by_str = by_match.group(1)
            group_by = [field.strip() for field in group_by_str.split(",")]
            # Remove 'by' clause from agg_str for function parsing
            agg_str = agg_str[: by_match.start()].strip()

        # Parse aggregation function
        # Simple functions: count(), rate()
        simple_match = re.match(r"^(count|rate)\s*\(\s*\)$", agg_str)
        if simple_match:
            func_name = simple_match.group(1)
            return TraceQLAggregation(
                function=AggregationType(func_name),
                group_by=group_by or None,
            )

        # Functions with field: avg(field), sum(field)
        field_match = re.match(r"^(avg|sum|max|min)\s*\(\s*([^)]+)\s*\)$", agg_str)
        if field_match:
            func_name = field_match.group(1)
            field_name = field_match.group(2).strip()
            return TraceQLAggregation(
                function=AggregationType(func_name),
                field=field_name,
                group_by=group_by or None,
            )

        # Quantile function: quantile_over_time(field, 0.95)
        quantile_match = re.match(r"^quantile_over_time\s*\(\s*([^,]+)\s*,\s*([0-9.]+)\s*\)$", agg_str)
        if quantile_match:
            field_name = quantile_match.group(1).strip()
            quantile_value = float(quantile_match.group(2))
            return TraceQLAggregation(
                function=AggregationType.QUANTILE,
                field=field_name,
                quantile=quantile_value,
                group_by=group_by or None,
            )

        # If we can't parse the aggregation, return None
        return None
