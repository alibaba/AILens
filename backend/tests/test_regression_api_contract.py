# -*- coding: utf-8 -*-
"""Layer 1: API Contract Regression Tests

Validates that every API endpoint returns field names, types, and value ranges
that exactly match the frontend TypeScript type definitions.

Based on PRD v0.8.2 — all endpoints verified against:
  - frontend/src/types/index.ts

Python 3.6.8 compatible (no f-strings, no dataclass).
"""


# ═══════════════════ Constants ═══════════════════

EXP_ID = "exp-grpo-cc"
ANALYSIS_BASE = "/api/v1/experiments/{}/analysis".format(EXP_ID)


# ═══════════════════ Helpers ═══════════════════


def assert_type(val, expected, path=""):
    """Assert value matches expected type with descriptive message."""
    assert isinstance(val, expected), "Field '{}' expected type {}, got {} (value={!r})".format(
        path, expected.__name__, type(val).__name__, val
    )


def assert_range(val, lo, hi, path=""):
    """Assert numeric value is within [lo, hi]."""
    assert lo <= val <= hi, "Field '{}' expected range [{}, {}], got {}".format(path, lo, hi, val)


def assert_keys_present(obj, keys, path=""):
    """Assert all keys are present in dict."""
    for k in keys:
        assert k in obj, "Missing key '{}' in {} (available: {})".format(k, path, list(obj.keys()))


# task-effectiveness contract tests removed - endpoint migrated to frontend TraceQL hook

# Tool Quality and Tool Latency Contract tests removed
# ═══════════════════ 5. Scaffold Stats Contract ═══════════════════


class TestScaffoldContract(object):
    """Validates /analysis/scaffold matches ScaffoldStatsResponse."""

    def test_status_200(self, client):
        r = client.get(ANALYSIS_BASE + "/scaffold")
        assert r.status_code == 200

    def test_uses_items_not_data(self, client):
        data = client.get(ANALYSIS_BASE + "/scaffold").json()
        assert "items" in data, "Missing 'items' — frontend expects 'items'"
        assert "data" not in data, "Found 'data' — frontend expects 'items'"

    def test_uses_count_not_frequency(self, client):
        """Frontend expects 'count', NOT 'frequency'."""
        data = client.get(ANALYSIS_BASE + "/scaffold").json()
        for item in data["items"]:
            assert "count" in item, "Missing 'count'"
            assert "frequency" not in item, "Found 'frequency' — frontend expects 'count'"

    def test_item_fields(self, client):
        """ScaffoldStatsItem fields."""
        data = client.get(ANALYSIS_BASE + "/scaffold").json()
        for item in data["items"]:
            assert_keys_present(
                item,
                [
                    "scaffold",
                    "count",
                    "pass_rate",
                    "max_turns_passed",
                    "avg_turns_passed",
                    "max_duration_passed_ms",
                    "avg_duration_passed_ms",
                ],
                "items[]",
            )
            assert_type(item["scaffold"], str, "items[].scaffold")
            assert_type(item["count"], int, "items[].count")
            assert_type(item["pass_rate"], (int, float), "items[].pass_rate")


# ═══════════════════ 9. Language Stats Contract ═══════════════════
# NOTE: TestLanguageContract removed - /analysis/language endpoint deleted
# Language stats now queried via PromQL aggregation

# ═══════════════════ 10. Turns Distribution Contract ═══════════════════
# NOTE: TestTurnsContract removed - Turn Analysis now uses PromQL metrics
# See test_turn_metrics.py for PromQL metric tests
# Old /analysis/turns endpoint returns 404


class TestTurnsContractRemoved(object):
    """Validates /analysis/turns returns 404 (migrated to PromQL)."""

    def test_turns_endpoint_returns_404(self, client):
        r = client.get(ANALYSIS_BASE + "/turns")
        assert r.status_code == 404


# ═══════════════════ 14. Annotations Contract ═══════════════════


class TestAnnotationsContract(object):
    """Validates GET /annotations/ matches AnnotationsResponse."""

    def test_status_200(self, client):
        r = client.get("/api/v1/annotations/")
        assert r.status_code == 200

    def test_top_level_keys(self, client):
        data = client.get("/api/v1/annotations/").json()
        assert_keys_present(data, ["total", "page", "page_size", "items"])

    def test_annotation_item_fields(self, client):
        data = client.get("/api/v1/annotations/").json()
        if data["items"]:
            item = data["items"][0]
            assert_keys_present(
                item,
                [
                    "id",
                    "trajectory_id",
                    "experiment_id",
                    "source",
                    "pattern_type",
                    "description",
                    "affected_turns",
                    "severity",
                    "created_at",
                ],
                "items[]",
            )
            assert_type(item["affected_turns"], list, "items[].affected_turns")

    def test_filter_by_trajectory_id(self, client):
        # Get a trajectory ID that has annotations
        all_data = client.get("/api/v1/annotations/", params={"page_size": 1}).json()
        if all_data["items"]:
            tid = all_data["items"][0]["trajectory_id"]
            filtered = client.get("/api/v1/annotations/", params={"trajectory_id": tid}).json()
            for item in filtered["items"]:
                assert item["trajectory_id"] == tid


# ═══════════════════ 15. PromQL Query Contract ═══════════════════


class TestPromQLQueryContract(object):
    """Validates POST /query returns Prometheus-format response."""

    def test_status_200(self, client):
        r = client.post("/api/v1/query", json={"query": 'experiment_mean_reward{{experiment_id="{}"}}'.format(EXP_ID)})
        assert r.status_code == 200

    def test_prometheus_format(self, client):
        r = client.post("/api/v1/query", json={"query": 'experiment_mean_reward{{experiment_id="{}"}}'.format(EXP_ID)})
        data = r.json()
        assert_keys_present(data, ["status", "data"])
        assert data["status"] == "success"
        assert_keys_present(data["data"], ["resultType", "result"])
        assert data["data"]["resultType"] == "matrix"

    def test_result_series_structure(self, client):
        r = client.post("/api/v1/query", json={"query": 'experiment_mean_reward{{experiment_id="{}"}}'.format(EXP_ID)})
        data = r.json()
        for series in data["data"]["result"]:
            assert_keys_present(series, ["metric", "values"])
            assert_type(series["metric"], dict, "result[].metric")
            assert_type(series["values"], list, "result[].values")
            # Each value is [timestamp, string_value]
            for v in series["values"]:
                assert len(v) == 2, "value should be [ts, str_val]"
                assert_type(v[0], (int, float), "value[0] timestamp")
                assert_type(v[1], str, "value[1] string value")

    def test_empty_query_returns_empty_result(self, client):
        r = client.post("/api/v1/query", json={"query": ""})
        data = r.json()
        assert data["data"]["result"] == []

    def test_unknown_metric_returns_empty_result(self, client):
        r = client.post("/api/v1/query", json={"query": "nonexistent_metric_xyz"})
        data = r.json()
        assert data["data"]["result"] == []


# ═══════════════════ 16. Experiments List Contract ═══════════════════


class TestExperimentsListContract(object):
    """Validates GET /experiments matches ExperimentsResponse."""

    def test_status_200(self, client):
        r = client.get("/api/v1/experiments")
        assert r.status_code == 200

    def test_top_level_keys(self, client):
        data = client.get("/api/v1/experiments").json()
        assert_keys_present(data, ["total", "page", "page_size", "items"])

    def test_experiment_item_fields(self, client):
        data = client.get("/api/v1/experiments").json()
        for item in data["items"]:
            assert_keys_present(
                item,
                [
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
                    "total_trajectories",
                    "total_tokens",
                ],
                "items[]",
            )

    def test_experiment_config_fields(self, client):
        data = client.get("/api/v1/experiments").json()
        for item in data["items"]:
            config = item["config"]
            assert_keys_present(
                config, ["model", "scaffolds", "algorithm", "reward_function", "reward_components"], "config"
            )
            assert_type(config["scaffolds"], list, "config.scaffolds")

    def test_experiment_status_enum(self, client):
        data = client.get("/api/v1/experiments").json()
        valid = {"running", "completed", "failed", "cancelled", "paused"}
        for item in data["items"]:
            assert item["status"] in valid, "Invalid status: {}".format(item["status"])


# ═══════════════════ 17. Projects List Contract ═══════════════════


class TestProjectsListContract(object):
    """Validates GET /projects matches ProjectsResponse."""

    def test_status_200(self, client):
        r = client.get("/api/v1/projects")
        assert r.status_code == 200

    def test_top_level_keys(self, client):
        data = client.get("/api/v1/projects").json()
        assert_keys_present(data, ["total", "items"])

    def test_project_item_fields(self, client):
        data = client.get("/api/v1/projects").json()
        for item in data["items"]:
            assert_keys_present(
                item, ["id", "name", "description", "owner", "tags", "created_at", "updated_at"], "items[]"
            )
            assert_type(item["id"], str, "items[].id")
            assert_type(item["name"], str, "items[].name")
