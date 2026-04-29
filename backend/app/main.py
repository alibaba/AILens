"""FastAPI application entry point — AgentLens API."""

import os

from dotenv import find_dotenv, load_dotenv

# Load environment variables from .env file (auto-discover regardless of nesting depth)
load_dotenv(find_dotenv(usecwd=False) or ".env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from .config import (
    API_V1_PREFIX,
    APP_DESCRIPTION,
    APP_TITLE,
    APP_VERSION,
    CORS_ALLOW_HEADERS,
    CORS_ALLOW_METHODS,
    CORS_ORIGINS,
)
from .observability.logging import setup_logging
from .observability.metrics.system import start_gc_metrics_collector
from .observability.middleware import AccessLogMiddleware, ErrorHandlingMiddleware
from .observability.telemetry import instrument_fastapi_app, setup_telemetry
from .routers import (
    agent_services,
    alerts,
    analysis,
    annotations,
    experiments,
    iterations,
    metrics,
    observability,
    projects,
    query,
    stats,
    tasks,
    trace_query,
    traceql,
    traces,
)


# Setup observability
def create_app() -> FastAPI:
    """Create and configure FastAPI application with observability."""

    # Setup logging first
    setup_logging(
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        log_format=os.getenv("LOG_FORMAT", "json"),
        log_file_path=os.getenv("LOG_FILE_PATH"),
        access_log_file_path=os.getenv("ACCESS_LOG_FILE_PATH"),
        error_log_file_path=os.getenv("ERROR_LOG_FILE_PATH"),
    )

    # Setup OpenTelemetry
    setup_telemetry(
        app_name=os.getenv("OTEL_SERVICE_NAME", "ailens-api"),
        app_version=os.getenv("OTEL_SERVICE_VERSION", APP_VERSION),
        environment=os.getenv("ENVIRONMENT", "development"),
        otlp_endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"),
        metrics_endpoint=os.getenv("OTEL_EXPORTER_OTLP_METRICS_ENDPOINT"),
        sample_rate=float(os.getenv("OTEL_TRACE_SAMPLE_RATE", "1.0")),
    )

    # Create FastAPI app
    app = FastAPI(
        title=APP_TITLE,
        version=APP_VERSION,
        description=APP_DESCRIPTION,
    )

    # Add observability middleware (order matters!)
    app.add_middleware(ErrorHandlingMiddleware, debug=os.getenv("DEBUG", "false").lower() == "true")
    app.add_middleware(AccessLogMiddleware, exclude_paths=["/health", "/ready", "/metrics", "/favicon.ico"])

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=CORS_ALLOW_METHODS,
        allow_headers=CORS_ALLOW_HEADERS,
    )

    # Apply FastAPI instrumentation
    instrument_fastapi_app(app)

    return app


app = create_app()


# Initialize system on startup
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    from .observability.logging import get_app_logger

    logger = get_app_logger()
    logger.info(
        "AgentLens API starting up",
        extra={"version": APP_VERSION, "environment": os.getenv("ENVIRONMENT", "development")},
    )

    # Start system metrics collection in background
    start_gc_metrics_collector(interval=30)
    logger.info("System metrics collector started")

    # Initialize existing tracing providers if they exist
    try:
        from .tracing.providers import init_providers

        init_providers()
        logger.info("Legacy tracing providers initialized")
    except ImportError:
        logger.info("No legacy tracing providers found, using OpenTelemetry")


# Mount routers
app.include_router(projects.router, prefix=API_V1_PREFIX)
app.include_router(experiments.router, prefix=API_V1_PREFIX)
app.include_router(iterations.router, prefix=API_V1_PREFIX)

app.include_router(analysis.router, prefix=API_V1_PREFIX)
app.include_router(query.router, prefix=API_V1_PREFIX)
app.include_router(traceql.router, prefix=API_V1_PREFIX)
app.include_router(trace_query.router, prefix=API_V1_PREFIX)
app.include_router(stats.router, prefix=API_V1_PREFIX)
app.include_router(agent_services.router, prefix=API_V1_PREFIX)
app.include_router(traces.router, prefix=API_V1_PREFIX)
app.include_router(metrics.router, prefix=API_V1_PREFIX)
app.include_router(tasks.router, prefix=API_V1_PREFIX)
app.include_router(annotations.router, prefix=API_V1_PREFIX)
app.include_router(alerts.router, prefix=API_V1_PREFIX)

# Observability endpoints
app.include_router(observability.router)


@app.get("/status.taobao", response_class=PlainTextResponse)
def health():
    return "success"


@app.get("/")
def root():
    return {"message": "AgentLens API", "version": APP_VERSION}
