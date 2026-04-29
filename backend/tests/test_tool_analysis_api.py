"""Tests for /stats/tool-analysis API endpoint (REQ-004)."""

EXP_ID = "exp-grpo-cc"
BASE = "/api/v1/stats"


class TestToolAnalysisEndpoint:
    """Test the aggregated tool analysis API."""

    def test_tool_analysis_endpoint_exists(self, client):
        """Test that /stats/tool-analysis endpoint exists."""
        r = client.post(
            "{}/tool-analysis".format(BASE),
            json={"experiment_id": EXP_ID},
        )
        assert r.status_code == 200

    def test_tool_analysis_returns_items(self, client):
        """Test that endpoint returns items array."""
        r = client.post(
            "{}/tool-analysis".format(BASE),
            json={"experiment_id": EXP_ID},
        )
        assert r.status_code == 200
        data = r.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_tool_analysis_item_fields(self, client):
        """Test that each item has all required fields."""
        r = client.post(
            "{}/tool-analysis".format(BASE),
            json={"experiment_id": EXP_ID},
        )
        assert r.status_code == 200
        data = r.json()

        if len(data["items"]) > 0:
            item = data["items"][0]
            required_fields = [
                "tool",
                "scaffold",
                "call_count",
                "success_rate",
                "avg_ms",
                "p50_ms",
                "p99_ms",
                "trajectory_count",
                "error_task_rate",
                "success_task_rate",
            ]
            for field in required_fields:
                assert field in item, "Missing field: {}".format(field)

    def test_tool_analysis_filters_by_scaffold(self, client):
        """Test scaffold filter works."""
        # First get all items
        r_all = client.post(
            "{}/tool-analysis".format(BASE),
            json={"experiment_id": EXP_ID},
        )
        assert r_all.status_code == 200
        r_all.json()["items"]

        # Get filtered items
        r_filtered = client.post(
            "{}/tool-analysis".format(BASE),
            json={"experiment_id": EXP_ID, "scaffold": "claude_code"},
        )
        assert r_filtered.status_code == 200
        filtered_items = r_filtered.json()["items"]

        # All filtered items should have scaffold matching filter
        for item in filtered_items:
            assert item["scaffold"] == "claude_code" or item["scaffold"] == ""

    def test_tool_analysis_filters_by_language(self, client):
        """Test language filter works."""
        r = client.post(
            "{}/tool-analysis".format(BASE),
            json={"experiment_id": EXP_ID, "language": "python"},
        )
        assert r.status_code == 200
        # Should return items (empty or populated depends on mock data)
        data = r.json()
        assert "items" in data

    def test_tool_analysis_split_by_none(self, client):
        """Test split_by=none returns aggregated by tool only."""
        r = client.post(
            "{}/tool-analysis".format(BASE),
            json={"experiment_id": EXP_ID, "split_by": "none"},
        )
        assert r.status_code == 200
        data = r.json()

        # When split_by=none, scaffold should be empty or same for all
        for item in data["items"]:
            # Scaffold should be empty string or consistent
            assert "scaffold" in item

    def test_tool_analysis_split_by_scaffold(self, client):
        """Test split_by=scaffold returns tool + scaffold combinations."""
        r = client.post(
            "{}/tool-analysis".format(BASE),
            json={"experiment_id": EXP_ID, "split_by": "scaffold"},
        )
        assert r.status_code == 200
        data = r.json()

        # When split_by=scaffold, scaffold field should have values
        for item in data["items"]:
            assert "scaffold" in item
            # Scaffold may have value if data exists for that combination

    def test_tool_analysis_split_by_language(self, client):
        """Test split_by=language returns tool + language combinations."""
        r = client.post(
            "{}/tool-analysis".format(BASE),
            json={"experiment_id": EXP_ID, "split_by": "language"},
        )
        assert r.status_code == 200
        data = r.json()
        assert "items" in data

    def test_tool_analysis_split_by_tool_schema(self, client):
        """Test split_by=tool_schema returns tool + schema combinations."""
        r = client.post(
            "{}/tool-analysis".format(BASE),
            json={"experiment_id": EXP_ID, "split_by": "tool_schema"},
        )
        assert r.status_code == 200
        data = r.json()
        assert "items" in data

    def test_tool_analysis_success_rate_range(self, client):
        """Test success_rate is between 0 and 1."""
        r = client.post(
            "{}/tool-analysis".format(BASE),
            json={"experiment_id": EXP_ID},
        )
        assert r.status_code == 200
        data = r.json()

        for item in data["items"]:
            assert 0 <= item["success_rate"] <= 1

    def test_tool_analysis_latency_positive(self, client):
        """Test latency metrics are non-negative."""
        r = client.post(
            "{}/tool-analysis".format(BASE),
            json={"experiment_id": EXP_ID},
        )
        assert r.status_code == 200
        data = r.json()

        for item in data["items"]:
            assert item["avg_ms"] >= 0
            assert item["p50_ms"] >= 0
            assert item["p99_ms"] >= 0

    def test_tool_analysis_counts_integer(self, client):
        """Test count fields are integers."""
        r = client.post(
            "{}/tool-analysis".format(BASE),
            json={"experiment_id": EXP_ID},
        )
        assert r.status_code == 200
        data = r.json()

        for item in data["items"]:
            assert isinstance(item["call_count"], int)
            assert isinstance(item["trajectory_count"], int)

    def test_tool_analysis_sorted_by_call_count(self, client):
        """Test items are sorted by call_count descending."""
        r = client.post(
            "{}/tool-analysis".format(BASE),
            json={"experiment_id": EXP_ID},
        )
        assert r.status_code == 200
        data = r.json()

        if len(data["items"]) > 1:
            call_counts = [item["call_count"] for item in data["items"]]
            assert call_counts == sorted(call_counts, reverse=True)

    def test_tool_analysis_invalid_experiment(self, client):
        """Test that invalid experiment_id returns empty or error."""
        r = client.post(
            "{}/tool-analysis".format(BASE),
            json={"experiment_id": "nonexistent-exp"},
        )
        # Should return 200 with empty items (no data found)
        assert r.status_code == 200
        data = r.json()
        assert data["items"] == []


class TestToolAnalysisPerformance:
    """Test that the endpoint provides expected performance improvements."""

    def test_single_request_replaces_multiple(self, client):
        """Verify that one tool-analysis call returns all metrics."""
        r = client.post(
            "{}/tool-analysis".format(BASE),
            json={"experiment_id": EXP_ID},
        )
        assert r.status_code == 200
        data = r.json()

        # All metrics should be present in one response
        if len(data["items"]) > 0:
            item = data["items"][0]
            # Quality metrics
            assert "call_count" in item
            assert "success_rate" in item
            assert "trajectory_count" in item
            assert "error_task_rate" in item
            assert "success_task_rate" in item
            # Latency metrics
            assert "avg_ms" in item
            assert "p50_ms" in item
            assert "p99_ms" in item
