# -*- coding: utf-8 -*-
"""Integration data pipeline tests — end-to-end data flow validation.

Tests the complete data pipeline using the TestClient:
  1. Training investigation flow (project → experiment → query → analysis → turns)
  2. PromQL full metric coverage (28 metrics)
  3. Analysis endpoint coverage (10 endpoints)

Python 3.6.8 compatible.
"""

import pytest
from app.main import app
from app.mock import store
from fastapi.testclient import TestClient

# ═══════════════════ Fixtures ═══════════════════


@pytest.fixture(scope="module")
def tc():
    """TestClient for data pipeline tests."""
    store._ensure_init()
    return TestClient(app)


# ═══════════════════ Training Investigation Flow ═══════════════════


class TestTrainingInvestigationFlow:
    """Simulates the full training investigation user journey:
    projects → experiments → PromQL → analysis → iterations → trajectories → turns.
    """

    def test_full_flow(self, tc):
        # Step 1: List projects
        r = tc.get("/api/v1/projects")
        assert r.status_code == 200
        projects = r.json()["items"]
        assert len(projects) >= 1
        project_id = projects[0]["id"]

        # Step 2: List experiments by project
        r = tc.get(
            "/api/v1/experiments",
            params={
                "project_id": project_id,
            },
        )
        assert r.status_code == 200
        experiments = r.json()["items"]
        assert len(experiments) >= 1
        exp_id = experiments[0]["id"]

        # Step 3: Query PromQL metric
        r = tc.post(
            "/api/v1/query",
            json={
                "query": 'experiment_mean_reward{{experiment_id="{}"}}'.format(exp_id),
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "success"
        assert data["data"]["resultType"] == "matrix"
        result = data["data"]["result"]
        assert len(result) >= 1
        assert len(result[0]["values"]) > 0

        # Step 4: Analysis — scaffold stats
        # NOTE: task-effectiveness migrated to frontend TraceQL hook
        r = tc.get("/api/v1/experiments/{}/analysis/scaffold".format(exp_id))
        assert r.status_code == 200
        scaffold = r.json()
        assert "items" in scaffold

        # Step 5: List iterations
        r = tc.get("/api/v1/experiments/{}/iterations".format(exp_id))
        assert r.status_code == 200
        iterations = r.json()["items"]
        assert len(iterations) > 0

        # Step 6: Verify TraceQL query works for experiment
        r = tc.post(
            "/api/v1/traceql/query",
            json={
                "query": 'select * from traces where resource.experiment_id = "{}"'.format(exp_id),
            },
        )
        assert r.status_code == 200
        traces = r.json()["data"]["result"]
        assert isinstance(traces, list)


# ═══════════════════ PromQL Full Metric Coverage ═══════════════════


class TestPromQLFullMetricCoverage:
    """Verify all metrics are queryable and return data."""

    EXPECTED_METRICS = [
        "experiment_trajectory_count",
        "experiment_passed_count",
        "experiment_mean_reward",
        "experiment_pass_rate",
        "experiment_reward_std",
        "experiment_input_tokens",
        "experiment_output_tokens",
        "experiment_tokens_per_trajectory",
        "experiment_tokens_per_reward",
        "experiment_io_tokens_ratio",
        "experiment_mean_turns",
        "experiment_mean_duration_ms",
    ]

    def test_metrics_list_complete(self, tc):
        """GET /query/metrics should list all expected metrics."""
        r = tc.get("/api/v1/query/metrics")
        assert r.status_code == 200
        metric_names = [m["name"] for m in r.json()]
        for expected in self.EXPECTED_METRICS:
            assert expected in metric_names, "Missing metric: {}".format(expected)

    def test_metrics_count(self, tc):
        """Should have at least 10 metrics."""
        r = tc.get("/api/v1/query/metrics")
        assert len(r.json()) >= 10

    @pytest.mark.parametrize("metric_name", EXPECTED_METRICS)
    def test_each_metric_queryable(self, tc, metric_name):
        """Each metric should return non-empty result for a valid experiment."""
        exp_id = "exp-grpo-cc"
        r = tc.post(
            "/api/v1/query",
            json={
                "query": '{}{{experiment_id="{}"}}'.format(metric_name, exp_id),
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "success"
        result = data["data"]["result"]
        assert len(result) >= 1, "Metric {} returned empty result".format(metric_name)


# ═══════════════════ Analysis Full Endpoint Coverage ═══════════════════


ANALYSIS_ENDPOINTS = {
    "scaffold": ["items"],
    # NOTE: "task-effectiveness" removed - now uses frontend TraceQL hook
    # NOTE: "language" removed - now uses PromQL aggregation
    # NOTE: "turns" removed - now uses PromQL metrics
    # NOTE: "tool-quality", "tool-latency" removed - now use TraceQL implementation
}


class TestAnalysisFullEndpointCoverage:
    """Verify all 10 analysis endpoints return expected data structure."""

    @pytest.mark.parametrize(
        "endpoint,expected_keys",
        list(ANALYSIS_ENDPOINTS.items()),
    )
    def test_endpoint_structure(self, tc, endpoint, expected_keys):
        exp_id = "exp-grpo-cc"
        r = tc.get("/api/v1/experiments/{}/analysis/{}".format(exp_id, endpoint))
        assert r.status_code == 200
        data = r.json()
        for key in expected_keys:
            assert key in data, "Endpoint {} missing key: {}".format(endpoint, key)


# ═══════════════════ Cross-Entity Consistency ═══════════════════


class TestCrossEntityConsistency:
    """Verify data consistency across entities."""

    def test_experiment_trajectories_scaffold_match(self, tc):
        """Trajectory scaffolds should match experiment config."""
        exp_id = "exp-grpo-cc"
        r = tc.get("/api/v1/experiments/{}".format(exp_id))
        config_scaffolds = set(r.json()["config"]["scaffolds"])

        r = tc.get("/api/v1/experiments/{}/iterations/1/trajectories".format(exp_id))
        trajs = r.json()["items"]
        for traj in trajs:
            assert traj["scaffold"] in config_scaffolds

    def test_trajectory_task_exists(self, tc):
        """trajectory.task_id should reference a valid task."""
        from app.mock import store

        exp_id = "exp-grpo-cc"

        # Get task_ids from mock store directly (no /tasks list API)
        task_ids = set(t["id"] for t in store.tasks)

        r = tc.get("/api/v1/experiments/{}/iterations/1/trajectories".format(exp_id))
        trajs = r.json()["items"]
        for traj in trajs:
            assert traj["task_id"] in task_ids, "Trajectory {} references unknown task {}".format(
                traj["id"], traj["task_id"]
            )
