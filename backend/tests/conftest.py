"""Shared pytest fixtures for backend tests."""

import os

import pytest
from fastapi.testclient import TestClient

# Force mock mode: set TRACEQL_BASE_URL="" before importing app so
# load_dotenv (override=False) cannot inject a real URL from .env.
os.environ["TRACEQL_BASE_URL"] = ""

from app.main import app  # noqa: E402
from app.mock import store  # noqa: E402

os.environ["TRACEQL_BASE_URL"] = ""  # re-clear in case main.py restored it


@pytest.fixture(scope="session")
def client():
    """FastAPI test client."""
    store._ensure_init()
    return TestClient(app)


@pytest.fixture(scope="session")
def mock_store():
    """Initialized mock data store."""
    store._ensure_init()
    return store
