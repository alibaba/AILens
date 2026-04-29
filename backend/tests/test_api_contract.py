# -*- coding: utf-8 -*-
"""API contract tests verifying response format matches frontend TypeScript types.

These tests verify that the API responses contain all fields the frontend
needs, validating the contract between backend and frontend.
Skipped if backend service is not running.
"""

import pytest

try:
    import requests

    _has_requests = True
except ImportError:
    _has_requests = False


def _service_running():
    if not _has_requests:
        return False
    try:
        r = requests.get("http://localhost:8000/api/v1/projects", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


_skip = not _service_running()
BASE = "http://localhost:8000/api/v1"

pytestmark = pytest.mark.skipif(_skip, reason="Backend service not running on localhost:8000")


def _get_first_experiment_id():
    projects = requests.get(BASE + "/projects").json()["items"]
    project_id = projects[0]["id"]
    experiments = requests.get(BASE + "/experiments", params={"project_id": project_id}).json()["items"]
    return experiments[0]["id"]


class TestApiContract(object):
    """Verify API responses match frontend TypeScript type contracts."""

    def test_experiment_config_contract(self):
        """Experiment config contains scaffolds(list), algorithm, reward_function, reward_components."""
        exp_id = _get_first_experiment_id()
        data = requests.get(BASE + "/experiments/" + exp_id).json()
        config = data["config"]

        assert isinstance(config["scaffolds"], list)
        assert len(config["scaffolds"]) > 0
        assert isinstance(config["algorithm"], str)
        assert isinstance(config["reward_function"], str)
        assert isinstance(config["reward_components"], list)

    def test_task_effectiveness_contract(self):
        """Task effectiveness response has pie_summary + tasks with classification field."""
        exp_id = _get_first_experiment_id()
        data = requests.get(BASE + "/experiments/" + exp_id + "/analysis/task-effectiveness").json()

        assert "summary" in data
        assert "tasks" in data

        summary = data["summary"]
        for field in ["all_pass", "all_fail", "mixed", "unverified"]:
            assert field in summary, "Missing pie_summary field: %s" % field

        tasks = data["tasks"]
        assert len(tasks) > 0
        assert "classification" in tasks[0]
        valid_classifications = ["all_pass", "all_fail", "mixed", "unverified"]
        assert tasks[0]["classification"] in valid_classifications
