"""System-related metrics using OpenTelemetry and system monitoring."""

import gc
import time
from threading import Thread

from prometheus_client import Counter as PromCounter

from .registry import get_meter, get_metrics_registry


class SystemMetrics:
    """System metrics collector for monitoring resource usage."""

    def __init__(self):
        """Initialize system metrics."""
        meter = get_meter()
        registry = get_metrics_registry()

        # GC metrics only
        self.gc_collections_total = meter.create_counter(
            name="gc_collections_total", description="Total number of garbage collections", unit="1"
        )

        self.prom_gc_collections = PromCounter(
            "gc_collections_total", "Total number of garbage collections", ["generation"], registry=registry
        )

        # Track GC stats
        self._last_gc_stats = self._get_gc_stats()

    def _get_gc_stats(self) -> dict:
        """Get garbage collection statistics."""
        stats = {}
        for i in range(len(gc.get_stats())):
            stat = gc.get_stats()[i]
            stats[i] = {
                "collections": stat.get("collections", 0),
                "collected": stat.get("collected", 0),
                "uncollectable": stat.get("uncollectable", 0),
            }
        return stats

    def update_gc_metrics(self):
        """Update garbage collection metrics."""
        current_stats = self._get_gc_stats()

        for generation, stats in current_stats.items():
            last_stats = self._last_gc_stats.get(generation, {})

            # Calculate delta
            collections_delta = stats["collections"] - last_stats.get("collections", 0)

            if collections_delta > 0:
                self.gc_collections_total.add(collections_delta, {"generation": str(generation)})

                self.prom_gc_collections.labels(generation=str(generation)).inc(collections_delta)

        self._last_gc_stats = current_stats


# Global instance
system_metrics = SystemMetrics()


def start_gc_metrics_collector(interval: int = 30):
    """Start background thread to collect GC metrics."""

    def collector_loop():
        while True:
            try:
                system_metrics.update_gc_metrics()
            except Exception as e:
                # Log error but don't stop collection
                print(f"Error collecting GC metrics: {e}")
            time.sleep(interval)

    thread = Thread(target=collector_loop, daemon=True)
    thread.start()
    return thread
