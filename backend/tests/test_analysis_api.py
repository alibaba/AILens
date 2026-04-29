# -*- coding: utf-8 -*-
"""Tests for analysis endpoints — /api/v1/experiments/{id}/analysis/*

Comprehensive validation of all 10 analysis endpoints:
reachability, data structure, edge cases, and PRD alignment.

Python 3.6.8 compatible.
"""

import pytest

EXP_ID = "exp-grpo-cc"
BASE = "/api/v1/experiments/{}/analysis".format(EXP_ID)
OLD_BASE = "/api/v1/experiments/{}/stats".format(EXP_ID)

ANALYSIS_ENDPOINTS = [
    # NOTE: "task-effectiveness" removed - now implemented via frontend TraceQL hook
    "scaffold",
    # NOTE: "language" removed - now implemented via PromQL metrics (REQ-001)
    # NOTE: "turns" removed - now implemented via PromQL metrics
    # NOTE: "tool-quality", "tool-latency" removed - now implemented via TraceQL
]


# ═══════════════════ Reachability ═══════════════════


class TestAllAnalysisEndpointsReachable:
    @pytest.mark.parametrize("endpoint", ANALYSIS_ENDPOINTS)
    def test_endpoint_200(self, client, endpoint):
        r = client.get("{}/{}".format(BASE, endpoint))
        assert r.status_code == 200, "Expected 200 for {}, got {}".format(endpoint, r.status_code)

    @pytest.mark.parametrize("endpoint", ANALYSIS_ENDPOINTS)
    def test_old_path_404(self, client, endpoint):
        r = client.get("{}/{}".format(OLD_BASE, endpoint))
        assert r.status_code == 404, "Expected 404 for old path {}, got {}".format(endpoint, r.status_code)


class TestAnalysisNotFound:
    def test_nonexistent_experiment(self, client):
        r = client.get("/api/v1/experiments/nonexistent/analysis/task-performance")
        assert r.status_code == 404

    @pytest.mark.parametrize("endpoint", ANALYSIS_ENDPOINTS)
    def test_nonexistent_experiment_all_endpoints(self, client, endpoint):
        r = client.get("/api/v1/experiments/nonexistent/analysis/{}".format(endpoint))
        assert r.status_code == 404


# task-effectiveness endpoint removed - now implemented via frontend TraceQL hook (useTaskEffectiveness)


# ═══════════════════ Scaffold Stats ═══════════════════


class TestScaffoldStats:
    def test_has_data(self, client):
        r = client.get("{}/scaffold".format(BASE))
        data = r.json()
        assert "items" in data
        assert len(data["items"]) > 0

    def test_item_fields(self, client):
        r = client.get("{}/scaffold".format(BASE))
        item = r.json()["items"][0]
        required = [
            "scaffold",
            "count",
            "pass_rate",
            "max_turns_passed",
            "avg_turns_passed",
            "max_duration_passed_ms",
            "avg_duration_passed_ms",
        ]
        for field in required:
            assert field in item, "Missing field: {}".format(field)

    def test_pass_rate_range(self, client):
        r = client.get("{}/scaffold".format(BASE))
        for item in r.json()["items"]:
            assert 0.0 <= item["pass_rate"] <= 1.0


# ═══════════════════ Language Stats ═══════════════════
# NOTE: /analysis/language endpoint removed (REQ-001)
# Language Stats now uses PromQL aggregation queries


# ═══════════════════ Turns Distribution ═══════════════════
# NOTE: Turn Analysis is now implemented via PromQL metrics:
#   - experiment_turns_count
#   - experiment_turns_passed_count
#   - experiment_turns_duration_max
#   - experiment_turns_duration_sum
#   - experiment_turns_duration_count
# The /turns REST endpoint has been removed.


# ═══════════════════ Iteration Range Filter ═══════════════════


class TestIterationRangeFilter:
    def test_iteration_start_filter(self, client):
        """iteration_start param should filter results."""
        r = client.get(
            "{}/scaffold".format(BASE),
            params={
                "iteration_start": "40",
            },
        )
        assert r.status_code == 200
        data = r.json()["items"]
        assert len(data) > 0

    def test_iteration_end_filter(self, client):
        """iteration_end param should filter results."""
        r = client.get(
            "{}/scaffold".format(BASE),
            params={
                "iteration_end": "10",
            },
        )
        assert r.status_code == 200
        data = r.json()["items"]
        assert len(data) > 0

    def test_iteration_range(self, client):
        """Combined start + end range."""
        r = client.get(
            "{}/scaffold".format(BASE),
            params={
                "iteration_start": "20",
                "iteration_end": "30",
            },
        )
        assert r.status_code == 200
        data = r.json()["items"]
        assert len(data) > 0
