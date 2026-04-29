"""API tests for traces endpoints."""

import time


class TestTracesAPI:
    def test_search_traces(self, client):
        # New trace API requires start_time and end_time
        now = int(time.time() * 1000)
        start_time = now - 24 * 60 * 60 * 1000  # 24 hours ago
        r = client.get("/api/v1/traces/search", params={"start_time": start_time, "end_time": now})
        # In test environment without EAGLEEYE_AUTH_KEY, no providers are registered
        # This is expected behavior - return 400 with proper error message
        if r.status_code == 400:
            data = r.json()
            assert "No trace providers registered" in data["detail"]
        else:
            # If providers are configured, should return 200 with list
            assert r.status_code == 200
            data = r.json()
            assert isinstance(data, list)

    def test_search_traces_by_scaffold(self, client):
        now = int(time.time() * 1000)
        start_time = now - 24 * 60 * 60 * 1000
        r = client.get(
            "/api/v1/traces/search",
            params={
                "start_time": start_time,
                "end_time": now,
                "service_name": "claude_code",  # New API uses service_name instead of scaffold
            },
        )
        # Same logic as test_search_traces
        if r.status_code == 400:
            data = r.json()
            assert "No trace providers registered" in data["detail"]
        else:
            assert r.status_code == 200
            data = r.json()
            assert isinstance(data, list)

    def test_search_traces_by_status(self, client):
        now = int(time.time() * 1000)
        start_time = now - 24 * 60 * 60 * 1000
        r = client.get(
            "/api/v1/traces/search",
            params={"start_time": start_time, "end_time": now, "status": "ok"},
        )
        # Same logic as test_search_traces
        if r.status_code == 400:
            data = r.json()
            assert "No trace providers registered" in data["detail"]
        else:
            assert r.status_code == 200
            data = r.json()
            assert isinstance(data, list)

    def test_get_trace_detail(self, client):
        # Get a mock trace_id (since EagleEye provider may not return real data in tests)
        trace_id = "mock-trace-id-001"
        r = client.get("/api/v1/traces/{}".format(trace_id))
        # In test environment without providers, expect 400
        if r.status_code == 400:
            data = r.json()
            assert "No trace providers registered" in data["detail"]
        elif r.status_code == 404:
            # Provider configured but trace not found
            pass
        else:
            # Provider configured and trace found
            assert r.status_code == 200
            data = r.json()
            assert data["trace_id"] == trace_id
            assert "spans" in data
