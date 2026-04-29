"""Tests for PromQL-compatible query API — /api/v1/query/*"""

import pytest

EXP_ID = "exp-grpo-cc"
QUERY_URL = "/api/v1/query"
METRICS_URL = "/api/v1/query/metrics"
METADATA_URL = "/api/v1/query/metadata"


class TestQueryMetricsList:
    def test_list_metrics(self, client):
        r = client.get(METRICS_URL)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) >= 17
        names = [m["name"] for m in data]
        assert "experiment_mean_reward" in names
        assert "experiment_pass_rate" in names

    def test_list_metrics_structure(self, client):
        r = client.get(METRICS_URL)
        data = r.json()
        for m in data:
            assert "name" in m
            assert "labels" in m
            assert "type" in m
            assert isinstance(m["labels"], list)
            assert m["type"] in ("gauge", "counter", "histogram")


class TestQueryMetadata:
    def test_metadata(self, client):
        r = client.get(METADATA_URL)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict)
        assert len(data) >= 17
        assert "experiment_mean_reward" in data

    def test_metadata_structure(self, client):
        r = client.get(METADATA_URL)
        data = r.json()
        for name, meta in data.items():
            assert "type" in meta
            assert "unit" in meta
            assert "help" in meta


class TestQueryRange:
    def test_query_single_metric_with_experiment(self, client):
        """Query single metric with experiment_id label returns granular series (scaffold×language)."""
        r = client.post(
            QUERY_URL,
            json={
                "query": 'experiment_mean_reward{{experiment_id="{}"}}'.format(EXP_ID),
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "success"
        assert data["data"]["resultType"] == "matrix"
        result = data["data"]["result"]
        # New behavior: returns granular series (scaffold×language combinations)
        assert len(result) >= 1
        series = result[0]
        assert series["metric"]["__name__"] == "experiment_mean_reward"
        assert series["metric"]["experiment_id"] == EXP_ID
        assert len(series["values"]) == 50  # 50 iterations

    def test_query_single_metric_with_aggregation(self, client):
        """Query with aggregation returns single aggregated series."""
        r = client.post(
            QUERY_URL,
            json={
                "query": 'avg(experiment_mean_reward{{experiment_id="{}"}}) by (experiment_id)'.format(EXP_ID),
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "success"
        assert data["data"]["resultType"] == "matrix"
        result = data["data"]["result"]
        # Aggregation by experiment_id returns single series
        assert len(result) == 1
        series = result[0]
        assert "experiment_id" in series["metric"]
        assert len(series["values"]) == 50

    def test_query_values_format(self, client):
        """Each value is [timestamp, string_value]."""
        r = client.post(
            QUERY_URL,
            json={
                "query": 'experiment_mean_reward{{experiment_id="{}"}}'.format(EXP_ID),
            },
        )
        result = r.json()["data"]["result"]
        for ts, val in result[0]["values"][:3]:
            assert isinstance(ts, (int, float))
            assert isinstance(val, str)
            float(val)  # should be parseable as float

    def test_query_with_scaffold_label(self, client):
        """Query with scaffold filter."""
        r = client.post(
            QUERY_URL,
            json={
                "query": 'experiment_mean_reward{{experiment_id="{}", scaffold="claude_code"}}'.format(EXP_ID),
            },
        )
        assert r.status_code == 200
        result = r.json()["data"]["result"]
        assert len(result) == 1
        assert result[0]["metric"]["scaffold"] == "claude_code"
        assert len(result[0]["values"]) > 0

    def test_query_no_labels(self, client):
        """Query without any labels returns all experiments."""
        r = client.post(
            QUERY_URL,
            json={
                "query": "experiment_mean_reward",
            },
        )
        assert r.status_code == 200
        result = r.json()["data"]["result"]
        assert len(result) >= 6  # 6 experiments

    def test_query_nonexistent_metric(self, client):
        """Unknown metric returns empty result."""
        r = client.post(
            QUERY_URL,
            json={
                "query": "nonexistent_metric",
            },
        )
        assert r.status_code == 200
        result = r.json()["data"]["result"]
        assert len(result) == 0

    def test_query_empty_string(self, client):
        """Empty query returns empty result."""
        r = client.post(
            QUERY_URL,
            json={
                "query": "",
            },
        )
        assert r.status_code == 200
        result = r.json()["data"]["result"]
        assert len(result) == 0

    def test_query_pass_rate(self, client):
        """Query pass_rate metric returns granular series."""
        r = client.post(
            QUERY_URL,
            json={
                "query": 'experiment_pass_rate{{experiment_id="{}"}}'.format(EXP_ID),
            },
        )
        assert r.status_code == 200
        result = r.json()["data"]["result"]
        # New behavior: returns granular series (scaffold×language combinations)
        assert len(result) >= 1
        values = result[0]["values"]
        assert len(values) == 50
        # Pass rates should be between 0 and 1
        for ts, val in values:
            v = float(val)
            assert 0.0 <= v <= 1.0

    def test_query_reward_std(self, client):
        """Query reward_std metric returns granular series."""
        r = client.post(
            QUERY_URL,
            json={
                "query": 'experiment_reward_std{{experiment_id="{}"}}'.format(EXP_ID),
            },
        )
        assert r.status_code == 200
        result = r.json()["data"]["result"]
        # New behavior: returns granular series (scaffold×language combinations)
        assert len(result) >= 1

    def test_query_io_tokens_ratio(self, client):
        """Query io_tokens_ratio metric returns granular series."""
        r = client.post(
            QUERY_URL,
            json={
                "query": 'experiment_io_tokens_ratio{{experiment_id="{}"}}'.format(EXP_ID),
            },
        )
        assert r.status_code == 200
        result = r.json()["data"]["result"]
        # New behavior: returns granular series (scaffold×language combinations)
        assert len(result) >= 1


class TestQueryAllSimpleMetrics:
    """Verify every simple metric can be queried successfully."""

    SIMPLE_METRICS = [
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

    @pytest.mark.parametrize("metric_name", SIMPLE_METRICS)
    def test_simple_metric_queryable(self, client, metric_name):
        r = client.post(
            QUERY_URL,
            json={
                "query": '{}{{experiment_id="{}"}}'.format(metric_name, EXP_ID),
            },
        )
        assert r.status_code == 200
        result = r.json()["data"]["result"]
        assert len(result) >= 1
        # tokens_per_reward may have None values filtered out
        if metric_name != "experiment_tokens_per_reward":
            assert len(result[0]["values"]) == 50
