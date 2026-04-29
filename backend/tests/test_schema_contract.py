# -*- coding: utf-8 -*-
"""Schema contract tests — verifies PRD 5.1 entity field completeness.

Ensures every entity returned by the API contains all fields defined
in the PRD schema specification. Python 3.6.8 compatible.
"""

EXP_ID = "exp-grpo-cc"


class TestProjectSchema:
    """PRD 5.1 — Project entity fields."""

    REQUIRED_FIELDS = [
        "id",
        "name",
        "description",
        "owner",
        "tags",
        "created_at",
        "updated_at",
    ]

    def test_project_has_all_fields(self, client):
        r = client.get("/api/v1/projects")
        assert r.status_code == 200
        projects = r.json()["items"]
        assert len(projects) > 0
        proj = projects[0]
        for field in self.REQUIRED_FIELDS:
            assert field in proj, "Project missing field: {}".format(field)

    def test_project_field_types(self, client):
        r = client.get("/api/v1/projects")
        proj = r.json()["items"][0]
        assert isinstance(proj["id"], str)
        assert isinstance(proj["name"], str)
        assert isinstance(proj["description"], str)
        assert isinstance(proj["owner"], str)
        assert isinstance(proj["tags"], dict)
        assert isinstance(proj["created_at"], str)
        assert isinstance(proj["updated_at"], str)


class TestExperimentSchema:
    """PRD 5.1 — Experiment entity fields."""

    REQUIRED_FIELDS = [
        "id",
        "project_id",
        "name",
        "status",
        "config",
        "tags",
        "created_at",
        "latest_iteration",
        "mean_reward",
        "pass_rate",
    ]
    CONFIG_FIELDS = [
        "model",
        "scaffolds",
        "algorithm",
        "reward_function",
        "reward_components",
        "hyperparams",
    ]

    def test_experiment_has_all_fields(self, client):
        r = client.get("/api/v1/experiments")
        assert r.status_code == 200
        items = r.json()["items"]
        assert len(items) > 0
        exp = items[0]
        for field in self.REQUIRED_FIELDS:
            assert field in exp, "Experiment missing field: {}".format(field)

    def test_experiment_config_has_all_fields(self, client):
        r = client.get("/api/v1/experiments/{}".format(EXP_ID))
        assert r.status_code == 200
        config = r.json()["config"]
        for field in self.CONFIG_FIELDS:
            assert field in config, "Config missing field: {}".format(field)

    def test_experiment_config_types(self, client):
        r = client.get("/api/v1/experiments/{}".format(EXP_ID))
        config = r.json()["config"]
        assert isinstance(config["model"], str)
        assert isinstance(config["scaffolds"], list)
        assert isinstance(config["algorithm"], str)
        assert isinstance(config["reward_function"], str)
        assert isinstance(config["reward_components"], list)
        assert isinstance(config["hyperparams"], dict)

    def test_experiment_status_valid(self, client):
        r = client.get("/api/v1/experiments")
        items = r.json()["items"]
        valid_statuses = {"running", "completed", "failed", "cancelled"}
        for exp in items:
            assert exp["status"] in valid_statuses, "Invalid status: {}".format(exp["status"])


class TestIterationSchema:
    """PRD 5.1 — Iteration entity fields."""

    REQUIRED_FIELDS = [
        "id",
        "experiment_id",
        "iteration_num",
        "timestamp",
        "checkpoint",
        "metrics",
    ]
    CHECKPOINT_FIELDS = ["saved", "path", "policy_version"]
    METRICS_FIELDS = [
        "mean_reward",
        "median_reward",
        "reward_std",
        "pass_rate",
        "total_trajectories",
        "total_tokens",
        "total_input_tokens",
        "total_output_tokens",
        "mean_tokens_per_trajectory",
        "tokens_per_reward",
        "input_output_ratio",
        "mean_turns",
        "mean_duration_ms",
        "mean_sandbox_create_duration_ms",
        "mean_verify_duration_ms",
        "tool_call_count",
    ]

    def test_iteration_has_all_fields(self, client):
        r = client.get("/api/v1/experiments/{}/iterations".format(EXP_ID))
        assert r.status_code == 200
        items = r.json()["items"]
        assert len(items) > 0
        it = items[0]
        for field in self.REQUIRED_FIELDS:
            assert field in it, "Iteration missing field: {}".format(field)

    def test_iteration_checkpoint_fields(self, client):
        r = client.get("/api/v1/experiments/{}/iterations".format(EXP_ID))
        it = r.json()["items"][0]
        ckpt = it["checkpoint"]
        for field in self.CHECKPOINT_FIELDS:
            assert field in ckpt, "Checkpoint missing field: {}".format(field)
        assert isinstance(ckpt["saved"], bool)
        assert isinstance(ckpt["path"], str)
        assert isinstance(ckpt["policy_version"], str)

    def test_iteration_metrics_fields(self, client):
        r = client.get("/api/v1/experiments/{}/iterations".format(EXP_ID))
        it = r.json()["items"][0]
        metrics = it["metrics"]
        for field in self.METRICS_FIELDS:
            assert field in metrics, "Metrics missing field: {}".format(field)

    def test_iteration_nums_sequential(self, client):
        r = client.get("/api/v1/experiments/{}/iterations".format(EXP_ID))
        items = r.json()["items"]
        nums = [it["iteration_num"] for it in items]
        for i in range(len(nums) - 1):
            assert nums[i + 1] == nums[i] + 1
