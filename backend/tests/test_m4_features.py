# -*- coding: utf-8 -*-
"""Tests for M4 features — TASK-029 through TASK-038

Covers:
  - format_correct trajectory field
  - format_correct_rate PromQL metric
  - repetition detection API + PromQL metrics
  - sandbox_count PromQL metric
  - extreme-cases API
  - tool-quality enhanced fields

Python 3.6.8 compatible.
"""

EXP_ID = "exp-grpo-cc"
BASE = "/api/v1/experiments/{}/analysis".format(EXP_ID)


# ═══════════════════ TASK-026: Task Difficulty ═══════════════════


class TestFormatCorrect:
    def test_trajectory_has_format_correct(self, mock_store):
        trajs = mock_store.get_trajectories(experiment_id=EXP_ID)
        for t in trajs[:10]:
            assert "format_correct" in t
            assert isinstance(t["format_correct"], bool)

    def test_format_correct_rate_promql(self, client):
        query = 'experiment_format_correct_rate{{experiment_id="{}"}}'.format(EXP_ID)
        r = client.post("/api/v1/query", json={"query": query})
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "success"
        results = data["data"]["result"]
        assert len(results) > 0

    def test_format_correct_rate_values_in_range(self, client):
        query = 'experiment_format_correct_rate{{experiment_id="{}"}}'.format(EXP_ID)
        r = client.post("/api/v1/query", json={"query": query})
        results = r.json()["data"]["result"]
        if results:
            for ts_val, val_str in results[0]["values"]:
                val = float(val_str)
                assert 0.0 <= val <= 1.0


# ═══════════════════ TASK-031: Repetition Detection ═══════════════════


class TestRepetitionDetection:
    def test_trajectory_has_repeat_fields(self, mock_store):
        trajs = mock_store.get_trajectories(experiment_id=EXP_ID)
        for t in trajs[:10]:
            assert "repeat_tool_call_count" in t
            assert "repeat_response_count" in t
            assert isinstance(t["repeat_tool_call_count"], int)
            assert isinstance(t["repeat_response_count"], int)

    def test_repetition_detection_api(self, client):
        r = client.get(BASE + "/repetition-detection")
        assert r.status_code == 200
        data = r.json()
        assert "total_trajectories" in data
        assert "tool_call_repetition" in data
        assert "response_repetition" in data

    def test_repetition_detection_structure(self, client):
        r = client.get(BASE + "/repetition-detection")
        data = r.json()
        tc = data["tool_call_repetition"]
        assert "affected_trajectories" in tc
        assert "affected_rate" in tc
        assert "total_repeats" in tc
        assert "mean_repeats_per_affected" in tc
        assert 0.0 <= tc["affected_rate"] <= 1.0

    def test_repeat_tool_call_rate_promql(self, client):
        query = 'experiment_repeat_tool_call_rate{{experiment_id="{}"}}'.format(EXP_ID)
        r = client.post("/api/v1/query", json={"query": query})
        assert r.status_code == 200
        results = r.json()["data"]["result"]
        assert len(results) > 0
        for ts_val, val_str in results[0]["values"]:
            val = float(val_str)
            assert 0.0 <= val <= 1.0

    def test_repeat_response_rate_promql(self, client):
        query = 'experiment_repeat_response_rate{{experiment_id="{}"}}'.format(EXP_ID)
        r = client.post("/api/v1/query", json={"query": query})
        assert r.status_code == 200
        results = r.json()["data"]["result"]
        assert len(results) > 0


# ═══════════════════ TASK-034: Extreme Cases ═══════════════════


class TestExtremeCases:
    def test_extreme_cases_returns_200(self, client):
        r = client.get(
            BASE + "/extreme-cases",
            params={"step_a": 1, "step_b": 50, "threshold": 0.2},
        )
        assert r.status_code == 200

    def test_extreme_cases_structure(self, client):
        r = client.get(
            BASE + "/extreme-cases",
            params={"step_a": 1, "step_b": 50, "threshold": 0.2},
        )
        data = r.json()
        assert "threshold" in data
        assert data["threshold"] == 0.2
        assert "extreme_improved" in data
        assert "extreme_degraded" in data
        assert "total_extreme" in data

    def test_extreme_cases_threshold_filter(self, client):
        r = client.get(
            BASE + "/extreme-cases",
            params={"step_a": 1, "step_b": 50, "threshold": 0.2},
        )
        data = r.json()
        for item in data["extreme_improved"]:
            assert abs(item["change"]) > 0.2
        for item in data["extreme_degraded"]:
            assert abs(item["change"]) > 0.2

    def test_extreme_cases_type_improved(self, client):
        r = client.get(
            BASE + "/extreme-cases",
            params={
                "step_a": 1,
                "step_b": 50,
                "threshold": 0.1,
                "type": "improved",
            },
        )
        data = r.json()
        assert len(data["extreme_degraded"]) == 0

    def test_extreme_cases_type_degraded(self, client):
        r = client.get(
            BASE + "/extreme-cases",
            params={
                "step_a": 1,
                "step_b": 50,
                "threshold": 0.1,
                "type": "degraded",
            },
        )
        data = r.json()
        assert len(data["extreme_improved"]) == 0

    def test_extreme_cases_total_extreme(self, client):
        r = client.get(
            BASE + "/extreme-cases",
            params={"step_a": 1, "step_b": 50, "threshold": 0.1},
        )
        data = r.json()
        assert data["total_extreme"] == (len(data["extreme_improved"]) + len(data["extreme_degraded"]))


# ═══════════════════ TASK-036: Tool Quality Enhanced Fields ═══════════════════
