# -*- coding: utf-8 -*-
"""Tests for M3 features — TASK-019, TASK-020, TASK-022, TASK-025

Covers:
  - pass-rate-diff API
  - cross-analysis API
  - experiment compare API

Python 3.6.8 compatible.
"""

EXP_ID = "exp-grpo-cc"
BASE = "/api/v1/experiments/{}/analysis".format(EXP_ID)


# ═══════════════════ TASK-019: Pass Rate Diff ═══════════════════


class TestPassRateDiff:
    def test_pass_rate_diff_returns_200(self, client):
        r = client.get(
            BASE + "/pass-rate-diff",
            params={"step_a": 5, "step_b": 10},
        )
        assert r.status_code == 200

    def test_pass_rate_diff_structure(self, client):
        r = client.get(
            BASE + "/pass-rate-diff",
            params={"step_a": 5, "step_b": 10},
        )
        data = r.json()
        assert "step_a" in data
        assert "step_b" in data
        assert data["step_a"] == 5
        assert data["step_b"] == 10
        assert "total_tasks" in data
        assert "summary" in data
        assert "items" in data

    def test_pass_rate_diff_summary_keys(self, client):
        r = client.get(
            BASE + "/pass-rate-diff",
            params={"step_a": 5, "step_b": 10},
        )
        summary = r.json()["summary"]
        assert "improved" in summary
        assert "unchanged" in summary
        assert "degraded" in summary
        total = summary["improved"] + summary["unchanged"] + summary["degraded"]
        assert total == r.json()["total_tasks"]

    def test_pass_rate_diff_items_sorted_by_abs_change(self, client):
        r = client.get(
            BASE + "/pass-rate-diff",
            params={"step_a": 1, "step_b": 50},
        )
        items = r.json()["items"]
        if len(items) > 1:
            for i in range(len(items) - 1):
                assert abs(items[i]["change"]) >= abs(items[i + 1]["change"])

    def test_pass_rate_diff_item_fields(self, client):
        r = client.get(
            BASE + "/pass-rate-diff",
            params={"step_a": 5, "step_b": 10},
        )
        items = r.json()["items"]
        if items:
            item = items[0]
            assert "task_id" in item
            assert "language" in item
            assert "category" in item
            assert "pass_rate_a" in item
            assert "pass_rate_b" in item
            assert "change" in item
            assert "change_group" in item
            assert item["change_group"] in ("improved", "unchanged", "degraded")

    def test_pass_rate_diff_with_scaffold_filter(self, client):
        r = client.get(
            BASE + "/pass-rate-diff",
            params={"step_a": 5, "step_b": 10, "scaffold": "claude_code"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["total_tasks"] >= 0

    def test_pass_rate_diff_with_language_filter(self, client):
        r = client.get(
            BASE + "/pass-rate-diff",
            params={"step_a": 5, "step_b": 10, "language": "python"},
        )
        assert r.status_code == 200

    def test_pass_rate_diff_with_tool_schema_filter(self, client):
        r = client.get(
            BASE + "/pass-rate-diff",
            params={"step_a": 5, "step_b": 10, "tool_schema": "json"},
        )
        assert r.status_code == 200

    def test_pass_rate_diff_same_step(self, client):
        """When step_a == step_b, all should be unchanged."""
        r = client.get(
            BASE + "/pass-rate-diff",
            params={"step_a": 5, "step_b": 5},
        )
        data = r.json()
        assert data["summary"]["improved"] == 0
        assert data["summary"]["degraded"] == 0

    def test_pass_rate_diff_404_for_unknown_experiment(self, client):
        r = client.get(
            "/api/v1/experiments/nonexistent/analysis/pass-rate-diff",
            params={"step_a": 5, "step_b": 10},
        )
        assert r.status_code == 404


# ═══════════════════ TASK-020: Cross Analysis ═══════════════════


class TestCrossAnalysis:
    def test_cross_analysis_returns_200(self, client):
        r = client.get(
            BASE + "/cross-analysis",
            params={
                "step_a": 5,
                "step_b": 10,
                "row_dimension": "scaffold",
                "col_dimension": "tool_schema",
            },
        )
        assert r.status_code == 200

    def test_cross_analysis_structure(self, client):
        r = client.get(
            BASE + "/cross-analysis",
            params={
                "step_a": 5,
                "step_b": 10,
                "row_dimension": "scaffold",
                "col_dimension": "tool_schema",
            },
        )
        data = r.json()
        assert data["row_dimension"] == "scaffold"
        assert data["col_dimension"] == "tool_schema"
        assert "rows" in data
        assert "cols" in data
        assert "cells" in data
        assert isinstance(data["rows"], list)
        assert isinstance(data["cols"], list)

    def test_cross_analysis_cells_have_groups(self, client):
        r = client.get(
            BASE + "/cross-analysis",
            params={
                "step_a": 5,
                "step_b": 10,
                "row_dimension": "scaffold",
                "col_dimension": "tool_schema",
            },
        )
        cells = r.json()["cells"]
        for row_key, row_data in cells.items():
            for col_key, cell in row_data.items():
                assert "improved" in cell
                assert "unchanged" in cell
                assert "degraded" in cell

    def test_cross_analysis_scaffold_x_language(self, client):
        r = client.get(
            BASE + "/cross-analysis",
            params={
                "step_a": 5,
                "step_b": 10,
                "row_dimension": "scaffold",
                "col_dimension": "language",
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data["row_dimension"] == "scaffold"
        assert data["col_dimension"] == "language"

    def test_cross_analysis_404_for_unknown_experiment(self, client):
        r = client.get(
            "/api/v1/experiments/nonexistent/analysis/cross-analysis",
            params={
                "step_a": 5,
                "step_b": 10,
            },
        )
        assert r.status_code == 404


# ═══════════════════ TASK-022: Experiment Compare ═══════════════════
