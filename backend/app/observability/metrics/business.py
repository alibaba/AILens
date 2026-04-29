"""Business-related metrics using OpenTelemetry."""

from prometheus_client import Counter as PromCounter
from prometheus_client import Histogram as PromHistogram

from .registry import get_meter, get_metrics_registry


class BusinessMetrics:
    """Business metrics collector for AgentLens application."""

    def __init__(self):
        """Initialize business metrics."""
        meter = get_meter()
        registry = get_metrics_registry()

        # TraceQL metrics
        self.traceql_queries_total = meter.create_counter(
            name="traceql_queries_total", description="Total number of TraceQL queries", unit="1"
        )

        self.traceql_query_duration = meter.create_histogram(
            name="traceql_query_duration_seconds", description="TraceQL query duration in seconds", unit="s"
        )

        self.traceql_query_errors_total = meter.create_counter(
            name="traceql_query_errors_total", description="Total number of TraceQL query errors", unit="1"
        )

        # Prometheus metrics for TraceQL
        self.prom_traceql_queries = PromCounter(
            "traceql_queries_total", "Total number of TraceQL queries", ["view_name", "status"], registry=registry
        )

        self.prom_traceql_duration = PromHistogram(
            "traceql_query_duration_seconds",
            "TraceQL query duration in seconds",
            ["view_name"],
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
            registry=registry,
        )

    def record_traceql_query(self, view_name: str, duration: float, success: bool = True):
        """Record TraceQL query metrics."""
        status = "success" if success else "error"

        self.traceql_queries_total.add(1, {"view_name": view_name, "status": status})

        if success:
            self.traceql_query_duration.record(duration, {"view_name": view_name})
        else:
            self.traceql_query_errors_total.add(1, {"view_name": view_name})

        # Prometheus metrics
        self.prom_traceql_queries.labels(view_name=view_name, status=status).inc()

        if success:
            self.prom_traceql_duration.labels(view_name=view_name).observe(duration)


# Global instance
business_metrics = BusinessMetrics()
