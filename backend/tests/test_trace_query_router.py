"""Tests for /api/v1/trace/query proxy route."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_returns_503_when_traceql_base_url_not_set():
    """Should return 503 when TRACEQL_BASE_URL is empty."""
    with patch.dict(os.environ, {"TRACEQL_BASE_URL": ""}):
        response = client.post(
            "/api/v1/trace/query",
            json={"query": 'view(experiment_reward_stats) | {experiment_id="abc"}'},
        )
    assert response.status_code == 503
    assert "not configured" in response.json()["detail"].lower()


def test_forwards_query_and_enforces_scope_rl():
    """Should forward query to external service with scope=rl appended."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"data": [{"iteration": 1, "mean_reward": 0.5}]}
    mock_resp.raise_for_status = MagicMock()

    mock_async_client = AsyncMock()
    mock_async_client.post.return_value = mock_resp

    with patch.dict(os.environ, {"TRACEQL_BASE_URL": "http://ext:9090"}):
        with patch("app.routers.trace_query.httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_async_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            response = client.post(
                "/api/v1/trace/query",
                json={"query": 'view(experiment_reward_stats) | {experiment_id="abc"}'},
            )

    assert response.status_code == 200
    payload = mock_async_client.post.call_args.kwargs["json"]
    assert payload["scope"] == "rl"
    assert payload["query"] == 'view(experiment_reward_stats) | {experiment_id="abc"}'
    assert response.json() == {"data": [{"iteration": 1, "mean_reward": 0.5}]}


def test_forwards_pagination_params():
    """Should forward page_size and page_num to external service."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"data": []}
    mock_resp.raise_for_status = MagicMock()

    mock_async_client = AsyncMock()
    mock_async_client.post.return_value = mock_resp

    with patch.dict(os.environ, {"TRACEQL_BASE_URL": "http://ext:9090"}):
        with patch("app.routers.trace_query.httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_async_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            client.post(
                "/api/v1/trace/query",
                json={"query": "view(x)", "page_size": 200, "page_num": 2},
            )

    payload = mock_async_client.post.call_args.kwargs["json"]
    assert payload["page_size"] == 200
    assert payload["page_num"] == 2


def test_returns_503_when_external_service_unreachable():
    """Should return 503 when external service is unreachable."""
    mock_async_client = AsyncMock()
    mock_async_client.post.side_effect = httpx.RequestError("Connection refused")

    with patch.dict(os.environ, {"TRACEQL_BASE_URL": "http://ext:9090"}):
        with patch("app.routers.trace_query.httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_async_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            response = client.post(
                "/api/v1/trace/query",
                json={"query": "view(x)"},
            )

    assert response.status_code == 503
    assert "unavailable" in response.json()["detail"].lower()


def test_propagates_external_service_error_status():
    """Should propagate external service HTTP error status."""
    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.text = "bad query syntax"

    mock_async_client = AsyncMock()
    mock_async_client.post.return_value = mock_resp
    mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        "400 Bad Request",
        request=MagicMock(),
        response=mock_resp,
    )

    with patch.dict(os.environ, {"TRACEQL_BASE_URL": "http://ext:9090"}):
        with patch("app.routers.trace_query.httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_async_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            response = client.post(
                "/api/v1/trace/query",
                json={"query": "view(x)"},
            )

    assert response.status_code == 400
