"""Observability endpoints for health checks and metrics."""

import os
from datetime import datetime
from typing import Any, Dict

import httpx
from fastapi import APIRouter, HTTPException, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from ..config import TRACEQL_AUTH_KEY, TRACEQL_BASE_URL
from ..observability.metrics import get_metrics_registry
from ..observability.metrics.system import system_metrics

router = APIRouter(prefix="/observability", tags=["observability"])


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint.

    Returns basic service health status without external dependencies.
    Used by load balancers and monitoring systems for basic liveness.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "service": "ailens-api",
        "version": "1.0.0",
    }


@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """Readiness check endpoint with dependency validation.

    Checks external service dependencies to determine if the service
    is ready to handle requests. Used by Kubernetes readiness probes.
    """
    checks = {}
    overall_status = "ready"
    start_time = datetime.utcnow()

    # Check database connection
    try:
        # Simple database configuration check
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            checks["database"] = {"status": "ok", "details": "Database URL configured"}
        else:
            checks["database"] = {"status": "warning", "details": "Database URL not configured"}

    except Exception as e:
        checks["database"] = {"status": "error", "details": f"Database check failed: {str(e)}"}
        overall_status = "not_ready"

    # Check TraceQL service
    try:
        if TRACEQL_BASE_URL and TRACEQL_AUTH_KEY:
            timeout = httpx.Timeout(5.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                # Try to reach TraceQL service health endpoint
                health_url = f"{TRACEQL_BASE_URL.rstrip('/')}/health"
                response = await client.get(
                    health_url, params={"authKey": TRACEQL_AUTH_KEY} if TRACEQL_AUTH_KEY else {}
                )

                if response.status_code == 200:
                    checks["traceql"] = {
                        "status": "ok",
                        "details": f"TraceQL service reachable (HTTP {response.status_code})",
                    }
                else:
                    checks["traceql"] = {
                        "status": "warning",
                        "details": f"TraceQL service returned HTTP {response.status_code}",
                    }
        else:
            checks["traceql"] = {
                "status": "warning",
                "details": "TraceQL not configured (TRACEQL_BASE_URL or TRACEQL_AUTH_KEY missing)",
            }
    except httpx.TimeoutException:
        checks["traceql"] = {"status": "error", "details": "TraceQL service timeout"}
        overall_status = "not_ready"
    except Exception as e:
        checks["traceql"] = {"status": "error", "details": f"TraceQL check failed: {str(e)}"}
        overall_status = "not_ready"

    # Check system resources
    try:
        # Update GC metrics for current values
        system_metrics.update_gc_metrics()

        checks["system"] = {"status": "ok", "details": "GC metrics collected successfully"}
    except Exception as e:
        checks["system"] = {"status": "warning", "details": f"System metrics collection failed: {str(e)}"}

    # Calculate total check duration
    duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "checks": checks,
        "check_duration_ms": round(duration_ms, 2),
    }


@router.get("/metrics")
async def metrics_endpoint() -> Response:
    """Prometheus metrics endpoint.

    Exports metrics in Prometheus format for scraping by monitoring systems.
    Updates system metrics before export to ensure current values.
    """
    try:
        # Update GC metrics to get current values
        system_metrics.update_gc_metrics()

        # Generate Prometheus format metrics
        registry = get_metrics_registry()
        metrics_data = generate_latest(registry)

        return Response(
            content=metrics_data,
            media_type=CONTENT_TYPE_LATEST,
            headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate metrics: {str(e)}")


@router.get("/info")
async def service_info() -> Dict[str, Any]:
    """Service information endpoint.

    Provides detailed information about the service, environment,
    and configuration for debugging and monitoring purposes.
    """
    import platform
    import sys

    return {
        "service": {
            "name": "ailens-api",
            "version": "1.0.0",
            "description": "AgentLens API - Agent Training & Production Observability",
        },
        "runtime": {
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "platform": platform.platform(),
            "architecture": platform.machine(),
            "processor": platform.processor() or "unknown",
        },
        "environment": {
            "deployment_env": os.getenv("ENVIRONMENT", "development"),
            "debug_mode": os.getenv("DEBUG", "false").lower() == "true",
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
        },
        "configuration": {
            "traceql_configured": bool(TRACEQL_BASE_URL and TRACEQL_AUTH_KEY),
            "traceql_base_url": TRACEQL_BASE_URL[:50] + "..."
            if TRACEQL_BASE_URL and len(TRACEQL_BASE_URL) > 50
            else TRACEQL_BASE_URL,
            "opentelemetry": {
                "otlp_endpoint": os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "not_configured"),
                "service_name": os.getenv("OTEL_SERVICE_NAME", "ailens-api"),
                "service_version": os.getenv("OTEL_SERVICE_VERSION", "1.0.0"),
            },
        },
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
