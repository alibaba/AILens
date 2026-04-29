"""OpenTelemetry configuration and setup."""

import os
import socket

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from .logging import get_app_logger

logger = get_app_logger()


def setup_telemetry(
    app_name: str = "ailens-api",
    app_version: str = "1.0.0",
    environment: str = None,
    otlp_endpoint: str = None,
    metrics_endpoint: str = None,
    sample_rate: float = 1.0,
    enable_auto_instrumentation: bool = True,
) -> tuple[TracerProvider, MeterProvider]:
    """Setup OpenTelemetry tracing and metrics.

    Args:
        app_name: Service name for telemetry
        app_version: Service version
        environment: Deployment environment (dev/staging/prod)
        otlp_endpoint: OTLP endpoint for traces
        metrics_endpoint: OTLP endpoint for metrics
        sample_rate: Sampling rate for traces (0.0-1.0)
        enable_auto_instrumentation: Whether to enable auto instrumentation

    Returns:
        Tuple of (tracer_provider, meter_provider)
    """

    # Get configuration from environment
    environment = environment or os.getenv("ENVIRONMENT", "development")
    otlp_endpoint = otlp_endpoint or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    metrics_endpoint = metrics_endpoint or os.getenv("OTEL_EXPORTER_OTLP_METRICS_ENDPOINT", otlp_endpoint)

    # Create resource with service information
    resource = Resource.create(
        {
            "service.name": app_name,
            "service.version": app_version,
            "service.instance.id": socket.gethostname(),
            "deployment.environment": environment,
            "host.name": socket.gethostname(),
            "process.pid": str(os.getpid()),
        }
    )

    logger.info(
        "Setting up OpenTelemetry",
        extra={
            "app_name": app_name,
            "app_version": app_version,
            "environment": environment,
            "otlp_endpoint": otlp_endpoint,
            "metrics_endpoint": metrics_endpoint,
            "sample_rate": sample_rate,
        },
    )

    # Setup Tracing
    tracer_provider = setup_tracing(resource, otlp_endpoint, sample_rate)

    # Setup Metrics
    meter_provider = setup_metrics(resource, metrics_endpoint)

    # Setup auto instrumentation
    if enable_auto_instrumentation:
        setup_auto_instrumentation()

    logger.info("OpenTelemetry setup completed")

    return tracer_provider, meter_provider


def setup_tracing(resource: Resource, otlp_endpoint: str, sample_rate: float) -> TracerProvider:
    """Setup OpenTelemetry tracing."""

    # Create tracer provider with sampling
    from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

    tracer_provider = TracerProvider(resource=resource, sampler=TraceIdRatioBased(sample_rate))

    # Set global tracer provider
    trace.set_tracer_provider(tracer_provider)

    # Setup OTLP exporter for traces
    try:
        otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)

        # Add batch span processor
        span_processor = BatchSpanProcessor(
            otlp_exporter,
            max_queue_size=2048,
            schedule_delay_millis=5000,
            export_timeout_millis=30000,
            max_export_batch_size=512,
        )

        tracer_provider.add_span_processor(span_processor)

        logger.info("OTLP trace exporter configured", extra={"endpoint": otlp_endpoint})

    except Exception as e:
        logger.warning("Failed to setup OTLP trace exporter", extra={"error": str(e)})

    return tracer_provider


def setup_metrics(resource: Resource, metrics_endpoint: str) -> MeterProvider:
    """Setup OpenTelemetry metrics."""

    # Setup OTLP exporter for metrics
    try:
        metrics_exporter = OTLPMetricExporter(endpoint=metrics_endpoint)

        # Create periodic exporting metric reader
        metrics_reader = PeriodicExportingMetricReader(
            exporter=metrics_exporter,
            export_interval_millis=30000,  # 30 seconds
            export_timeout_millis=30000,
        )

        # Create meter provider with metric reader
        meter_provider = MeterProvider(resource=resource, metric_readers=[metrics_reader])

        logger.info("OTLP metrics exporter configured", extra={"endpoint": metrics_endpoint})

    except Exception as e:
        logger.warning("Failed to setup OTLP metrics exporter", extra={"error": str(e)})

        # Fallback: create meter provider without OTLP export
        meter_provider = MeterProvider(resource=resource)

    # Set global meter provider
    metrics.set_meter_provider(meter_provider)

    return meter_provider


def setup_auto_instrumentation():
    """Setup automatic instrumentation for common libraries."""

    try:
        # FastAPI instrumentation - will be applied when app is provided
        logger.info("FastAPI auto-instrumentation configured")

        # HTTP requests instrumentation
        RequestsInstrumentor().instrument()
        logger.info("Requests auto-instrumentation enabled")

        # Database instrumentation
        # Psycopg2Instrumentor().instrument()
        # logger.info("Psycopg2 auto-instrumentation enabled")
        logger.info("Database auto-instrumentation skipped (psycopg2 not available)")

    except Exception as e:
        logger.warning("Failed to setup auto instrumentation", extra={"error": str(e)})


def instrument_fastapi_app(app):
    """Apply FastAPI instrumentation to the app."""
    try:
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI app instrumentation applied")
    except Exception as e:
        logger.warning("Failed to instrument FastAPI app", extra={"error": str(e)})


def get_current_trace_id() -> str:
    """Get current trace ID as hex string."""
    span = trace.get_current_span()
    if span and span.context and span.context.trace_id:
        return f"{span.context.trace_id:032x}"
    return None


def get_current_span_id() -> str:
    """Get current span ID as hex string."""
    span = trace.get_current_span()
    if span and span.context and span.context.span_id:
        return f"{span.context.span_id:016x}"
    return None


def create_custom_span(name: str, attributes: dict = None):
    """Create a custom span for manual tracing."""
    tracer = trace.get_tracer(__name__)
    span = tracer.start_span(name)

    if attributes:
        for key, value in attributes.items():
            span.set_attribute(key, value)

    return span
