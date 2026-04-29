# -*- coding: utf-8 -*-
"""Tests for Turn Analysis PromQL metrics.

Validates the 5 new PromQL metrics:
  - experiment_turns_count
  - experiment_turns_passed_count
  - experiment_turns_duration_max
  - experiment_turns_duration_sum
  - experiment_turns_duration_count

Python 3.6.8 compatible.
"""

EXP_ID = "exp-grpo-cc"


class TestTurnMetricsPromQL:
    """Test Turn Analysis metrics via PromQL query endpoint."""

    def test_turns_count_metric(self, client):
        """experiment_turns_count should return series grouped by total_turns."""
        query = 'experiment_turns_count{experiment_id="%s"}' % EXP_ID
        r = client.post(
            "/api/v1/query",
            json={
                "query": query,
                "start": "2026-01-01T00:00:00",
                "end": "2026-12-31T23:59:59",
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "success"
        # Should return at least one series
        assert len(data["data"]["result"]) > 0
        # Each series should have total_turns label
        for series in data["data"]["result"]:
            assert "total_turns" in series["metric"]
            assert "experiment_id" in series["metric"]

    def test_turns_passed_count_metric(self, client):
        """experiment_turns_passed_count should return passed counts."""
        query = 'experiment_turns_passed_count{experiment_id="%s"}' % EXP_ID
        r = client.post("/api/v1/query", json={"query": query})
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "success"

    def test_turns_duration_max_metric(self, client):
        """experiment_turns_duration_max should return max durations."""
        query = 'experiment_turns_duration_max{experiment_id="%s"}' % EXP_ID
        r = client.post("/api/v1/query", json={"query": query})
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "success"

    def test_turns_duration_sum_metric(self, client):
        """experiment_turns_duration_sum should return duration sums."""
        query = 'experiment_turns_duration_sum{experiment_id="%s"}' % EXP_ID
        r = client.post("/api/v1/query", json={"query": query})
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "success"

    def test_turns_duration_count_metric(self, client):
        """experiment_turns_duration_count should return duration counts."""
        query = 'experiment_turns_duration_count{experiment_id="%s"}' % EXP_ID
        r = client.post("/api/v1/query", json={"query": query})
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "success"

    def test_turns_api_endpoint_removed(self, client):
        """Old /analysis/turns endpoint should return 404."""
        r = client.get("/api/v1/experiments/%s/analysis/turns" % EXP_ID)
        assert r.status_code == 404
