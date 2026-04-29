"""Application configuration."""

import os

API_V1_PREFIX = "/api/v1"
APP_TITLE = "AgentLens API"
APP_VERSION = "0.1.0"
APP_DESCRIPTION = "AgentLens — Agent Training & Production Observability API"

# CORS settings
CORS_ORIGINS = ["*"]
CORS_ALLOW_METHODS = ["*"]
CORS_ALLOW_HEADERS = ["*"]

TRACEQL_BASE_URL = os.environ.get("TRACEQL_BASE_URL", "")
TRACEQL_AUTH_KEY = os.environ.get("TRACEQL_AUTH_KEY", "")
