"""TraceQL engine - Main interface for executing TraceQL queries."""

from typing import Any, Dict

from .executor import TraceQLExecutor
from .parser import TraceQLParser


class TraceQLEngine:
    """Main TraceQL engine that combines parsing and execution."""

    def __init__(self, store):
        """Initialize with data store."""
        self.parser = TraceQLParser()
        self.executor = TraceQLExecutor(store)

    def query(self, query_string: str, **filters) -> Dict[str, Any]:
        """Execute TraceQL query string."""
        try:
            # Parse query
            parsed_query = self.parser.parse(query_string)

            # Execute query
            result = self.executor.execute(parsed_query, **filters)

            return {
                "status": "success",
                "data": result,
                "query": {
                    "original": query_string,
                    "parsed": {
                        "selector_conditions": len(parsed_query.selector.conditions),
                        "has_aggregation": parsed_query.aggregation is not None,
                        "aggregation_type": parsed_query.aggregation.function.value
                        if parsed_query.aggregation
                        else None,
                    },
                },
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "query": query_string,
            }
