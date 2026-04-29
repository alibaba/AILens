"""Metrics registry for collecting all application metrics."""

from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from prometheus_client import REGISTRY, CollectorRegistry

# Global metrics registry
_meter_provider: MeterProvider = None
_meter = None
_prometheus_registry = CollectorRegistry()


def get_meter_provider() -> MeterProvider:
    """Get the global meter provider."""
    global _meter_provider
    if _meter_provider is None:
        _meter_provider = metrics.get_meter_provider()
    return _meter_provider


def get_meter():
    """Get the application meter."""
    global _meter
    if _meter is None:
        _meter = get_meter_provider().get_meter(name="ailens-api", version="1.0.0")
    return _meter


def get_metrics_registry() -> CollectorRegistry:
    """Get the Prometheus metrics registry."""
    return _prometheus_registry


def get_default_registry() -> CollectorRegistry:
    """Get the default Prometheus registry."""
    return REGISTRY


class MetricsRegistry:
    """High-level metrics registry with background collection support."""

    async def start_background_collection(self, interval: int = 30):
        """Start background metrics collection (no-op stub)."""
        pass

    async def stop_background_collection(self):
        """Stop background metrics collection (no-op stub)."""
        pass

    def get_metrics_summary(self) -> dict:
        """Get a summary of collected GC metrics."""
        import gc
        from datetime import datetime, timezone

        stats = gc.get_stats()
        by_generation = {str(i): stat.get("collections", 0) for i, stat in enumerate(stats)}
        total = sum(by_generation.values())
        return {
            "gc_summary": {
                "total_collections": total,
                "by_generation": by_generation,
            },
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        }


metrics_registry = MetricsRegistry()
