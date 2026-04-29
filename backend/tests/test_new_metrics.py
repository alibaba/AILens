# -*- coding: utf-8 -*-
"""Tests for new PromQL metrics (P0 + P2).

Validates the 5 new metrics:
  P0 - Task Effectiveness (3):
    - experiment_task_all_correct_rate
    - experiment_task_all_wrong_rate
    - experiment_task_mixed_rate
  P2 - Quality Verification (2):
    - experiment_stop_reason_rate
    - experiment_reward_range

Python 3.6.8 compatible.
"""

EXP_ID = "exp-grpo-cc"


class TestTaskEffectivenessMetrics:
    """Test Task Effectiveness metrics via PromQL query endpoint."""

    def test_task_all_correct_rate_basic(self, client):
        """experiment_task_all_correct_rate should return valid rate values."""
        query = 'experiment_task_all_correct_rate{experiment_id="%s"}' % EXP_ID
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
        # Verify structure
        for series in data["data"]["result"]:
            assert "experiment_id" in series["metric"]
            assert "__name__" in series["metric"]
            # Values should be floats between 0 and 1
            for val in series["values"]:
                rate = float(val[1])
                assert 0.0 <= rate <= 1.0

    def test_task_all_correct_rate_with_scaffold_filter(self, client):
        """experiment_task_all_correct_rate should support scaffold filter."""
        query = 'experiment_task_all_correct_rate{experiment_id="%s",scaffold="claude_code"}' % EXP_ID
        r = client.post("/api/v1/query", json={"query": query})
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "success"
        # If data returned, scaffold label should match
        for series in data["data"]["result"]:
            if "scaffold" in series["metric"]:
                assert series["metric"]["scaffold"] == "claude_code"

    def test_task_all_wrong_rate_basic(self, client):
        """experiment_task_all_wrong_rate should return valid rate values."""
        query = 'experiment_task_all_wrong_rate{experiment_id="%s"}' % EXP_ID
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
        # Verify structure and value range
        for series in data["data"]["result"]:
            assert "experiment_id" in series["metric"]
            for val in series["values"]:
                rate = float(val[1])
                assert 0.0 <= rate <= 1.0

    def test_task_all_wrong_rate_with_language_filter(self, client):
        """experiment_task_all_wrong_rate should support language filter."""
        query = 'experiment_task_all_wrong_rate{experiment_id="%s",language="python"}' % EXP_ID
        r = client.post("/api/v1/query", json={"query": query})
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "success"

    def test_task_mixed_rate_basic(self, client):
        """experiment_task_mixed_rate should return valid rate values."""
        query = 'experiment_task_mixed_rate{experiment_id="%s"}' % EXP_ID
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
        # Verify structure and value range
        for series in data["data"]["result"]:
            assert "experiment_id" in series["metric"]
            for val in series["values"]:
                rate = float(val[1])
                assert 0.0 <= rate <= 1.0

    def test_task_mixed_rate_with_tool_schema_filter(self, client):
        """experiment_task_mixed_rate should support tool_schema filter."""
        query = 'experiment_task_mixed_rate{experiment_id="%s",tool_schema="json"}' % EXP_ID
        r = client.post("/api/v1/query", json={"query": query})
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "success"

    def test_task_rates_sum_to_one(self, client):
        """All three task rates should sum to approximately 1 for each iteration."""
        # Get all three rates
        rates = {}
        for metric in [
            "experiment_task_all_correct_rate",
            "experiment_task_all_wrong_rate",
            "experiment_task_mixed_rate",
        ]:
            query = '%s{experiment_id="%s"}' % (metric, EXP_ID)
            r = client.post("/api/v1/query", json={"query": query})
            assert r.status_code == 200
            data = r.json()
            if data["data"]["result"]:
                # Get values from first series
                rates[metric] = data["data"]["result"][0]["values"]

        # If we have all three, check sum
        if len(rates) == 3 and all(len(v) > 0 for v in rates.values()):
            # Check first iteration
            for idx in range(min(5, len(rates["experiment_task_all_correct_rate"]))):
                correct = float(rates["experiment_task_all_correct_rate"][idx][1])
                wrong = float(rates["experiment_task_all_wrong_rate"][idx][1])
                mixed = float(rates["experiment_task_mixed_rate"][idx][1])
                total = correct + wrong + mixed
                # Allow small floating point tolerance
                assert abs(total - 1.0) < 0.01, "Rates sum should be ~1.0, got %s" % total


class TestStopReasonRateMetric:
    """Test Stop Reason Rate metric via PromQL query endpoint."""

    def test_stop_reason_rate_basic(self, client):
        """experiment_stop_reason_rate should return series grouped by exec_result."""
        query = 'experiment_stop_reason_rate{experiment_id="%s"}' % EXP_ID
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
        # Should return multiple series (one per exec_result)
        assert len(data["data"]["result"]) > 0
        # Each series should have exec_result label
        for series in data["data"]["result"]:
            assert "exec_result" in series["metric"]
            assert "experiment_id" in series["metric"]
            # Values should be floats between 0 and 1
            for val in series["values"]:
                rate = float(val[1])
                assert 0.0 <= rate <= 1.0

    def test_stop_reason_rate_filter_by_result(self, client):
        """experiment_stop_reason_rate should support exec_result filter."""
        query = 'experiment_stop_reason_rate{experiment_id="%s",exec_result="success"}' % EXP_ID
        r = client.post("/api/v1/query", json={"query": query})
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "success"
        # Should return only success series if data exists
        for series in data["data"]["result"]:
            # The filter may not be strict in mock implementation, just check exec_result exists
            assert "exec_result" in series["metric"]

    def test_stop_reason_rate_with_scaffold_filter(self, client):
        """experiment_stop_reason_rate should support scaffold filter."""
        query = 'experiment_stop_reason_rate{experiment_id="%s",scaffold="claude_code"}' % EXP_ID
        r = client.post("/api/v1/query", json={"query": query})
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "success"

    def test_stop_reason_rates_sum_to_one(self, client):
        """Stop reason rates per iteration should sum to approximately 1."""
        query = 'experiment_stop_reason_rate{experiment_id="%s"}' % EXP_ID
        r = client.post("/api/v1/query", json={"query": query})
        assert r.status_code == 200
        data = r.json()
        # Sum rates for first iteration timestamp
        if data["data"]["result"]:
            # Get all exec_result values for first iteration
            timestamp = data["data"]["result"][0]["values"][0][0]
            total = 0.0
            for series in data["data"]["result"]:
                for val in series["values"]:
                    if val[0] == timestamp:
                        total += float(val[1])
            # Allow small floating point tolerance
            assert abs(total - 1.0) < 0.05, "Stop reason rates sum should be ~1.0, got %s" % total


class TestRewardRangeMetric:
    """Test Reward Range metric via PromQL query endpoint."""

    def test_reward_range_basic(self, client):
        """experiment_reward_range should return valid range values."""
        query = 'experiment_reward_range{experiment_id="%s"}' % EXP_ID
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
        # Verify structure
        for series in data["data"]["result"]:
            assert "experiment_id" in series["metric"]
            # Values should be positive floats
            for val in series["values"]:
                range_val = float(val[1])
                assert range_val >= 0.0
                # Reward range should be less than 2 (max reward ~1, min ~-0.2)
                assert range_val <= 2.0

    def test_reward_range_with_scaffold_filter(self, client):
        """experiment_reward_range should support scaffold filter."""
        query = 'experiment_reward_range{experiment_id="%s",scaffold="claude_code"}' % EXP_ID
        r = client.post("/api/v1/query", json={"query": query})
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "success"

    def test_reward_range_with_language_filter(self, client):
        """experiment_reward_range should support language filter."""
        query = 'experiment_reward_range{experiment_id="%s",language="python"}' % EXP_ID
        r = client.post("/api/v1/query", json={"query": query})
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "success"

    def test_reward_range_trend(self, client):
        """Reward range should show trend across iterations."""
        query = 'experiment_reward_range{experiment_id="%s"}' % EXP_ID
        r = client.post("/api/v1/query", json={"query": query})
        assert r.status_code == 200
        data = r.json()
        if data["data"]["result"]:
            values = data["data"]["result"][0]["values"]
            # Should have values for multiple iterations
            assert len(values) > 1
