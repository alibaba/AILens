# -*- coding: utf-8 -*-
"""Layer 2: Backend Feature Regression Tests

Validates page-level functional requirements from PRD v0.8.2.
Each test group maps to a page/tab in the UI and verifies the
backend API produces correct data for that feature.

Python 3.6.8 compatible (no f-strings, no dataclass).
"""

import pytest
from app.metrics.registry import METRIC_REGISTRY

EXP_ID = "exp-grpo-cc"
ANALYSIS_BASE = "/api/v1/experiments/{}/analysis".format(EXP_ID)


# ═══════════════════════════════════════════════════════
# A. Experiment Detail — Tab 1: Training Overview (PromQL)
# ═══════════════════════════════════════════════════════


class TestTrainingOverviewPromQL(object):
    """Tab 1 reads PromQL metrics for convergence + efficiency charts."""

    # 3 convergence + 7 efficiency = 10
    CONVERGENCE_METRICS = [
        "experiment_mean_reward",
        "experiment_pass_rate",
        "experiment_reward_std",
    ]

    EFFICIENCY_METRICS = [
        "experiment_input_tokens",
        "experiment_output_tokens",
        "experiment_tokens_per_trajectory",
        "experiment_tokens_per_reward",
        "experiment_io_tokens_ratio",
        "experiment_mean_turns",
        "experiment_mean_duration_ms",
    ]

    ALL_METRICS = CONVERGENCE_METRICS + EFFICIENCY_METRICS

    @pytest.mark.parametrize("metric", ALL_METRICS)
    def test_metric_registered(self, metric):
        """All metrics exist in registry."""
        assert metric in METRIC_REGISTRY, "Metric '{}' not in METRIC_REGISTRY".format(metric)

    @pytest.mark.parametrize("metric", CONVERGENCE_METRICS + EFFICIENCY_METRICS[:4])
    def test_promql_returns_matrix_data(self, client, metric):
        """Each metric returns non-empty matrix result."""
        r = client.post("/api/v1/query", json={"query": '{}{{experiment_id="{}"}}'.format(metric, EXP_ID)})
        assert r.status_code == 200
        data = r.json()
        assert data["data"]["resultType"] == "matrix"
        assert len(data["data"]["result"]) > 0, "Metric '{}' returned empty result".format(metric)

    def test_aggregation_sum_by_scaffold(self, client):
        """sum(...) by (scaffold) should return one series per scaffold."""
        r = client.post(
            "/api/v1/query",
            json={"query": 'sum(experiment_trajectory_count{{experiment_id="{}"}}) by (scaffold)'.format(EXP_ID)},
        )
        data = r.json()
        result = data["data"]["result"]
        # Should return one series per scaffold
        assert len(result) >= 1, "Expected >= 1 series for sum by scaffold, got {}".format(len(result))
        scaffolds = set()
        for series in result:
            s = series["metric"].get("scaffold")
            if s:
                scaffolds.add(s)
        assert len(scaffolds) >= 1, "Expected >= 1 distinct scaffolds, got: {}".format(scaffolds)

    def test_no_aggregation_returns_granular_series(self, client):
        """Without aggregation, returns fine-grained series (one per scaffold+language)."""
        r = client.post("/api/v1/query", json={"query": 'experiment_mean_reward{{experiment_id="{}"}}'.format(EXP_ID)})
        data = r.json()
        result = data["data"]["result"]
        # Should return fine-grained series (scaffold x language combinations)
        assert len(result) >= 1, "Expected >= 1 fine-grained series, got {}".format(len(result))

    def test_empty_experiment_returns_empty(self, client):
        """Non-existent experiment_id returns empty result, no 500."""
        r = client.post("/api/v1/query", json={"query": 'experiment_mean_reward{experiment_id="nonexistent"}'})
        assert r.status_code == 200
        data = r.json()
        assert data["data"]["result"] == []


# ═══════════════════════════════════════════════════════
# B. Experiment Detail — Tab 2: Task Analysis
# ═══════════════════════════════════════════════════════


class TestTaskAnalysisFeatures(object):
    """Tab 2 task analysis functional tests."""

    # task-effectiveness tests removed - endpoint migrated to frontend TraceQL hook (useTaskEffectiveness)
    # NOTE: test_language_items_sorted_by_pass_rate_desc removed
    # /analysis/language endpoint deleted, language stats now via PromQL


# ═══════════════════════════════════════════════════════
# C. Experiment Detail — Tab 3: Behavior Analysis
# ═══════════════════════════════════════════════════════


class TestBehaviorAnalysisFeatures(object):
    """Tab 3 behavior analysis functional tests."""

    # test_tool_quality_has_tool_scaffold_dimensions and test_tool_latency_p99_gte_p50 removed

    def test_scaffold_count_positive(self, client):
        """Each scaffold should have count > 0."""
        data = client.get(ANALYSIS_BASE + "/scaffold").json()
        for item in data["items"]:
            assert item["count"] > 0, "scaffold '{}' has count=0".format(item["scaffold"])

    # NOTE: test_turns_p99_gte_p90 removed - Turn Analysis now uses PromQL metrics
    # PromQL metrics don't have p90/p99 percentiles in the same format

    # NOTE: test_turns_bucket_count_positive removed - Turn Analysis now uses PromQL metrics
    # See test_turn_metrics.py for PromQL metric tests


# ═══════════════════════════════════════════════════════
# G. Analysis endpoints — iteration range filtering
# ═══════════════════════════════════════════════════════


class TestAnalysisIterationFiltering(object):
    """Verify analysis endpoints support iteration_start/iteration_end."""

    ENDPOINTS = [
        "scaffold",
        # NOTE: "task-effectiveness" removed - now uses frontend TraceQL hook
        # NOTE: "language" removed - now uses PromQL aggregation
        # NOTE: "turns" removed - now uses PromQL metrics
    ]

    @pytest.mark.parametrize("endpoint", ENDPOINTS)
    def test_with_iteration_range(self, client, endpoint):
        """Should return 200 with iteration_start and iteration_end."""
        r = client.get(ANALYSIS_BASE + "/{}".format(endpoint), params={"iteration_start": 1, "iteration_end": 10})
        assert r.status_code == 200


# ═══════════════════════════════════════════════════════
# H. PromQL query edge cases
# ═══════════════════════════════════════════════════════


class TestPromQLEdgeCases(object):
    """Edge cases for the PromQL query API."""

    def test_query_metrics_list(self, client):
        """GET /query/metrics returns all metric names."""
        r = client.get("/api/v1/query/metrics")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        names = [m["name"] for m in data]
        assert "experiment_mean_reward" in names
        assert "experiment_pass_rate" in names

    def test_query_metadata(self, client):
        """GET /query/metadata returns metadata for all metrics."""
        r = client.get("/api/v1/query/metadata")
        assert r.status_code == 200
        data = r.json()
        assert "experiment_mean_reward" in data
        meta = data["experiment_mean_reward"]
        assert "type" in meta
        assert "unit" in meta
        assert "help" in meta

    def test_metric_values_are_string_type(self, client):
        """Prometheus format requires values to be strings."""
        r = client.post("/api/v1/query", json={"query": 'experiment_pass_rate{{experiment_id="{}"}}'.format(EXP_ID)})
        data = r.json()
        for series in data["data"]["result"]:
            for ts, val in series["values"]:
                assert isinstance(val, str), "Value should be string, got {}".format(type(val).__name__)
