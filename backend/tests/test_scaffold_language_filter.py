# -*- coding: utf-8 -*-
"""Tests for scaffold/language filtering — REQ-001

Covers:
  - _get_filtered_trajectories with scaffold/language params
  - Analysis API endpoints with scaffold/language query params
  - PromQL extractor with language label filtering
  - Languages endpoint

Python 3.6.8 compatible.
"""

import pytest

EXP_ID = "exp-grpo-cc"
BASE = "/api/v1/experiments/{}/analysis".format(EXP_ID)


# ═══════════════════ Helper: get valid scaffold & language values ═══════════════════


@pytest.fixture(scope="session")
def valid_scaffold(mock_store):
    """Return a scaffold value that exists in the test experiment."""
    trajs = mock_store.get_trajectories(experiment_id=EXP_ID)
    scaffolds = set(t.get("scaffold") for t in trajs if t.get("scaffold"))
    assert len(scaffolds) > 0, "No scaffolds found in test data"
    return sorted(scaffolds)[0]


@pytest.fixture(scope="session")
def valid_language(mock_store):
    """Return a language value that exists in the test experiment."""
    trajs = mock_store.get_trajectories(experiment_id=EXP_ID)
    languages = set(t.get("task_language") for t in trajs if t.get("task_language"))
    assert len(languages) > 0, "No languages found in test data"
    return sorted(languages)[0]


@pytest.fixture(scope="session")
def total_trajectory_count(mock_store):
    """Total unfiltered trajectory count for the experiment."""
    trajs = mock_store.get_trajectories(experiment_id=EXP_ID)
    return len(trajs)


# ═══════════════════ Languages endpoint ═══════════════════


class TestLanguagesEndpoint:
    def test_returns_languages(self, client):
        r = client.get("{}/languages".format(BASE))
        assert r.status_code == 200
        data = r.json()
        assert "languages" in data
        assert isinstance(data["languages"], list)
        assert len(data["languages"]) > 0

    def test_languages_are_sorted(self, client):
        r = client.get("{}/languages".format(BASE))
        langs = r.json()["languages"]
        assert langs == sorted(langs)

    def test_nonexistent_experiment_404(self, client):
        r = client.get("/api/v1/experiments/nonexistent/analysis/languages")
        assert r.status_code == 404


# ═══════════════════ _get_filtered_trajectories behavior ═══════════════════


class TestFilteredTrajectories:
    """Test that scaffold/language filters actually reduce the result set."""

    def test_scaffold_filter_reduces_results(self, client, valid_scaffold):
        # Without filter
        r_all = client.get("{}/scaffold".format(BASE))
        all_items = r_all.json()["items"]
        total_all = sum(item["count"] for item in all_items)

        # With scaffold filter
        r_filtered = client.get(
            "{}/scaffold".format(BASE),
            params={
                "scaffold": valid_scaffold,
            },
        )
        filtered_items = r_filtered.json()["items"]
        total_filtered = sum(item["count"] for item in filtered_items)

        assert total_filtered > 0, "Filtered should have some results"
        assert total_filtered <= total_all, "Filtered count {} should be <= total {}".format(total_filtered, total_all)

    # NOTE: test_language_filter_reduces_results removed
    # /analysis/language endpoint deleted, language stats now via PromQL

    # ═══════════════════ Analysis endpoints with scaffold/language ═══════════════════


FILTERABLE_ENDPOINTS = [
    "scaffold",
    # NOTE: "task-effectiveness" removed - now uses frontend TraceQL hook
    # NOTE: "language" removed - now uses PromQL aggregation
    # NOTE: "turns" removed - now uses PromQL metrics
    # NOTE: "tool-quality", "tool-latency" removed - now use TraceQL implementation
]


class TestAllEndpointsAcceptFilters:
    @pytest.mark.parametrize("endpoint", FILTERABLE_ENDPOINTS)
    def test_scaffold_param_accepted(self, client, endpoint, valid_scaffold):
        r = client.get(
            "{}/{}".format(BASE, endpoint),
            params={
                "scaffold": valid_scaffold,
            },
        )
        assert r.status_code == 200, "Expected 200 for {} with scaffold filter, got {}".format(endpoint, r.status_code)

    @pytest.mark.parametrize("endpoint", FILTERABLE_ENDPOINTS)
    def test_language_param_accepted(self, client, endpoint, valid_language):
        r = client.get(
            "{}/{}".format(BASE, endpoint),
            params={
                "language": valid_language,
            },
        )
        assert r.status_code == 200, "Expected 200 for {} with language filter, got {}".format(endpoint, r.status_code)

    @pytest.mark.parametrize("endpoint", FILTERABLE_ENDPOINTS)
    def test_combined_params_accepted(self, client, endpoint, valid_scaffold, valid_language):
        r = client.get(
            "{}/{}".format(BASE, endpoint),
            params={
                "scaffold": valid_scaffold,
                "language": valid_language,
            },
        )
        assert r.status_code == 200, "Expected 200 for {} with both filters, got {}".format(endpoint, r.status_code)


# ═══════════════════ Specific endpoint data validation ═══════════════════
# NOTE: TestTurnsFiltered removed - Turn Analysis now uses PromQL metrics
# PromQL metrics support scaffold/language filtering via labels

# ═══════════════════ PromQL extractor with language label ═══════════════════


class TestPromQLLanguageFilter:
    def test_mean_reward_with_language(self, client, valid_language):
        """PromQL query with language label should return filtered data."""
        query = ('experiment_mean_reward{{experiment_id="{}", language="{}"}}').format(EXP_ID, valid_language)
        r = client.post("/api/v1/query", json={"query": query})
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "success"
        results = data["data"]["result"]
        # Should have at least one series
        assert len(results) > 0
        # Check metric label includes language
        for series in results:
            assert series["metric"].get("language") == valid_language

    def test_mean_reward_with_scaffold_and_language(self, client, valid_scaffold, valid_language):
        """PromQL query with both scaffold and language labels."""
        query = ('experiment_mean_reward{{experiment_id="{}", scaffold="{}", language="{}"}}').format(
            EXP_ID, valid_scaffold, valid_language
        )
        r = client.post("/api/v1/query", json={"query": query})
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "success"
        results = data["data"]["result"]
        for series in results:
            assert series["metric"].get("scaffold") == valid_scaffold
            assert series["metric"].get("language") == valid_language
