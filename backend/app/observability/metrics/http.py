"""HTTP-related metrics using OpenTelemetry."""

# OpenTelemetry instruments are created from meter, not imported directly
from prometheus_client import Counter as PromCounter
from prometheus_client import Gauge as PromGauge
from prometheus_client import Histogram as PromHistogram

from .registry import get_meter, get_metrics_registry


class HTTPMetrics:
    """HTTP metrics collector using OpenTelemetry and Prometheus."""

    def __init__(self):
        """Initialize HTTP metrics."""
        meter = get_meter()
        registry = get_metrics_registry()

        # OpenTelemetry metrics
        self.requests_total = meter.create_counter(
            name="http_requests_total", description="Total number of HTTP requests", unit="1"
        )

        self.request_duration = meter.create_histogram(
            name="http_request_duration_seconds", description="HTTP request duration in seconds", unit="s"
        )

        self.requests_active = meter.create_up_down_counter(
            name="http_requests_active", description="Number of active HTTP requests", unit="1"
        )

        self.response_size = meter.create_histogram(
            name="http_response_size_bytes", description="HTTP response size in bytes", unit="By"
        )

        # Prometheus metrics (for /metrics endpoint)
        self.prom_requests_total = PromCounter(
            "http_requests_total", "Total number of HTTP requests", ["method", "path", "status_code"], registry=registry
        )

        self.prom_request_duration = PromHistogram(
            "http_request_duration_seconds",
            "HTTP request duration in seconds",
            ["method", "path"],
            buckets=[0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0],
            registry=registry,
        )

        self.prom_requests_active = PromGauge(
            "http_requests_active", "Number of active HTTP requests", registry=registry
        )

        self.prom_response_size = PromHistogram(
            "http_response_size_bytes",
            "HTTP response size in bytes",
            ["method", "path"],
            buckets=[128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536],
            registry=registry,
        )

    def record_request(self, method: str, path: str, status_code: int, duration: float, response_size: int = None):
        """Record HTTP request metrics."""
        # OpenTelemetry metrics
        self.requests_total.add(1, {"method": method, "path": path, "status_code": str(status_code)})

        self.request_duration.record(duration, {"method": method, "path": path})

        if response_size is not None:
            self.response_size.record(response_size, {"method": method, "path": path})

        # Prometheus metrics
        self.prom_requests_total.labels(method=method, path=path, status_code=str(status_code)).inc()

        self.prom_request_duration.labels(method=method, path=path).observe(duration)

        if response_size is not None:
            self.prom_response_size.labels(method=method, path=path).observe(response_size)

    def increment_active_requests(self):
        """Increment active requests counter."""
        self.requests_active.add(1)
        self.prom_requests_active.inc()

    def decrement_active_requests(self):
        """Decrement active requests counter."""
        self.requests_active.add(-1)
        self.prom_requests_active.dec()


# Global instance
http_metrics = HTTPMetrics()
