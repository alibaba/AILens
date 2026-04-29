# -*- coding: utf-8 -*-
"""Tests for M2 features — REQ-005 + REQ-006 + REQ-008

Covers:
  - experiment_pass_rate_baseline PromQL metric
  - experiment_success_mean_turns / p90 / p99 PromQL metrics
  - experiment_success_turns_count/min/max/sum/bucket PromQL metrics
  - timeout trajectory total_turns >= max_turns
  - experiment config has max_turns field

Python 3.6.8 compatible.
"""

EXP_ID = "exp-grpo-cc"
BASE = "/api/v1/experiments/{}/analysis".format(EXP_ID)


# ═══════════════════ TASK-016: max_turns config and timeout trajectories ═══════════════════


class TestMaxTurnsConfig:
    def test_experiment_config_has_max_turns(self, mock_store):
        exp = mock_store.get_experiment(EXP_ID)
        assert exp is not None
        config = exp.get("config", {})
        assert "max_turns" in config, "Experiment config missing max_turns"
        assert config["max_turns"] == 20

    def test_timeout_trajectories_have_max_turns(self, mock_store):
        trajs = mock_store.get_trajectories(experiment_id=EXP_ID)
        timeout_trajs = [t for t in trajs if t["outcome"] == "timeout"]
        assert len(timeout_trajs) > 0, "No timeout trajectories found"
        for t in timeout_trajs:
            assert t["total_turns"] >= 20, "Timeout trajectory {} has total_turns={}, expected >= 20".format(
                t["id"], t["total_turns"]
            )


# ═══════════════════ TASK-012: Pass Rate Baseline ═══════════════════


class TestPassRateBaseline:
    def test_pass_rate_baseline_returns_data(self, client):
        query = 'experiment_pass_rate_baseline{{experiment_id="{}"}}'.format(EXP_ID)
        r = client.post("/api/v1/query", json={"query": query})
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "success"
        results = data["data"]["result"]
        assert len(results) > 0, "Expected at least one series for pass_rate_baseline"

    def test_pass_rate_baseline_values_in_range(self, client):
        query = 'experiment_pass_rate_baseline{{experiment_id="{}"}}'.format(EXP_ID)
        r = client.post("/api/v1/query", json={"query": query})
        results = r.json()["data"]["result"]
        if results:
            for ts_val, val_str in results[0]["values"]:
                val = float(val_str)
                assert 0.0 <= val <= 1.0, "Baseline value {} out of range [0, 1]".format(val)


# ═══════════════════ TASK-014: Success Turns PromQL metrics ═══════════════════


class TestSuccessTurnsPromQL:
    def test_success_mean_turns_has_data(self, client):
        query = 'experiment_success_mean_turns{{experiment_id="{}"}}'.format(EXP_ID)
        r = client.post("/api/v1/query", json={"query": query})
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "success"
        results = data["data"]["result"]
        assert len(results) > 0
