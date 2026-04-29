"""Unit tests for TraceQL-based experiment/iteration repositories.

All httpx.Client calls are mocked — no network required.
"""

import os
from unittest.mock import MagicMock, patch

import app.repositories.traceql_experiment as repo_module
import pytest
from app.repositories.traceql_experiment import (
    TraceQLExperimentRepository,
    TraceQLIterationRepository,
    _aggregate_all,
    _aggregate_experiment,
    _fetch_counts,
    _merge_rows,
    _traceql_query,
)

# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def clear_cache():
    """Reset module-level cache between tests."""
    repo_module._cache.clear()
    yield
    repo_module._cache.clear()


def _make_mock_client(data):
    """Return a mock httpx.Client context manager that yields ``data``."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"code": 0, "data": data, "success": True}
    mock_response.raise_for_status = MagicMock()

    mock_ctx = MagicMock()
    mock_ctx.post.return_value = mock_response
    mock_ctx.__enter__ = MagicMock(return_value=mock_ctx)
    mock_ctx.__exit__ = MagicMock(return_value=False)
    return mock_ctx


# ── _traceql_query tests ─────────────────────────────────────────────────────


class TestTraceqlQuery:
    def test_raises_if_no_base_url(self):
        env = dict(os.environ)
        env.pop("TRACEQL_BASE_URL", None)
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(RuntimeError, match="TRACEQL_BASE_URL not configured"):
                _traceql_query("{} | select(count())")

    @patch("app.repositories.traceql_experiment.httpx.Client")
    def test_returns_data_list(self, mock_cls):
        rows = [{"experiment_id": "e1", "total": 5}]
        mock_cls.return_value = _make_mock_client(rows)
        with patch.dict(os.environ, {"TRACEQL_BASE_URL": "http://test.local"}):
            result = _traceql_query("some query")
        assert result == rows

    @patch("app.repositories.traceql_experiment.httpx.Client")
    def test_sends_correct_payload(self, mock_cls):
        mock_ctx = _make_mock_client([])
        mock_cls.return_value = mock_ctx
        with patch.dict(
            os.environ,
            {
                "TRACEQL_BASE_URL": "http://test.local",
                "TRACEQL_AUTH_KEY": "my-key",
            },
        ):
            _traceql_query("my query", page_size=500)

        call_kwargs = mock_ctx.post.call_args
        assert call_kwargs[0][0] == "http://test.local/api/v1/trace/query"
        payload = call_kwargs[1]["json"]
        assert payload["query"] == "my query"
        assert payload["scope"] == "rl"
        assert payload["pageSize"] == 500
        assert payload["pageNum"] == 1
        assert call_kwargs[1]["params"] == {"authKey": "my-key"}

    @patch("app.repositories.traceql_experiment.httpx.Client")
    def test_no_auth_key_omits_params(self, mock_cls):
        mock_ctx = _make_mock_client([])
        mock_cls.return_value = mock_ctx
        env_without_auth = {k: v for k, v in os.environ.items() if k != "TRACEQL_AUTH_KEY"}
        env_without_auth["TRACEQL_BASE_URL"] = "http://test.local"
        with patch.dict(os.environ, env_without_auth, clear=True):
            _traceql_query("q")
        params = mock_ctx.post.call_args[1]["params"]
        assert params == {}

    @patch("app.repositories.traceql_experiment.httpx.Client")
    def test_empty_data_returns_empty_list(self, mock_cls):
        mock_response = MagicMock()
        mock_response.json.return_value = {"code": 0, "data": None, "success": True}
        mock_response.raise_for_status = MagicMock()
        mock_ctx = MagicMock()
        mock_ctx.post.return_value = mock_response
        mock_ctx.__enter__ = MagicMock(return_value=mock_ctx)
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_cls.return_value = mock_ctx
        with patch.dict(os.environ, {"TRACEQL_BASE_URL": "http://test.local"}):
            result = _traceql_query("q")
        assert result == []


# ── _merge_rows tests ────────────────────────────────────────────────────────


class TestMergeRows:
    def test_single_row(self):
        rows = [
            {
                "experiment_id": "e1",
                "model": "gpt-4",
                "scaffold": "claude_code",
                "latest_iteration": 3,
                "total_trajectories": 100,
                "mean_reward": 0.6,
                "pass_rate": 0.7,
                "total_tokens": 10000,
                "first_seen": 1700000000,
            }
        ]
        result = _merge_rows(rows)
        assert result["id"] == "e1"
        assert result["name"] == "e1"
        assert result["status"] == "unknown"
        assert result["project_id"] == "default"
        assert result["config"]["model"] == "gpt-4"
        assert result["config"]["scaffolds"] == ["claude_code"]
        assert result["latest_iteration"] == 3
        assert result["total_trajectories"] == 100
        assert result["total_tokens"] == 10000
        assert result["mean_reward"] == 0.6
        assert result["pass_rate"] == 0.7
        assert "2023" in result["created_at"]  # from timestamp 1700000000

    def test_multiple_rows_merge_scaffolds(self):
        rows = [
            {
                "experiment_id": "e1",
                "model": "gpt-4",
                "scaffold": "claude_code",
                "latest_iteration": 5,
                "total_trajectories": 100,
                "mean_reward": 0.6,
                "pass_rate": 0.7,
                "total_tokens": 10000,
                "first_seen": 1700000000,
            },
            {
                "experiment_id": "e1",
                "model": "gpt-4",
                "scaffold": "aider",
                "latest_iteration": 3,
                "total_trajectories": 50,
                "mean_reward": 0.4,
                "pass_rate": 0.5,
                "total_tokens": 5000,
                "first_seen": 1700000100,
            },
        ]
        result = _merge_rows(rows)
        assert result["config"]["scaffolds"] == ["aider", "claude_code"]  # sorted
        assert result["latest_iteration"] == 5  # max
        assert result["total_trajectories"] == 150  # sum
        assert result["total_tokens"] == 15000  # sum
        expected_reward = round((0.6 * 100 + 0.4 * 50) / 150, 4)
        assert abs(result["mean_reward"] - expected_reward) < 0.0001
        expected_pass = round((0.7 * 100 + 0.5 * 50) / 150, 4)
        assert abs(result["pass_rate"] - expected_pass) < 0.0001
        from datetime import datetime, timezone

        expected_ts = datetime.fromtimestamp(1700000000, tz=timezone.utc).isoformat()
        assert result["created_at"] == expected_ts

    def test_zero_trajectories(self):
        rows = [
            {
                "experiment_id": "e1",
                "model": "m",
                "scaffold": "s",
                "latest_iteration": 0,
                "total_trajectories": 0,
                "mean_reward": 0,
                "pass_rate": 0,
                "total_tokens": 0,
                "first_seen": 0,
            }
        ]
        result = _merge_rows(rows)
        assert result["mean_reward"] == 0.0
        assert result["pass_rate"] == 0.0
        assert result["created_at"] == ""


# ── _fetch_counts tests ──────────────────────────────────────────────────────


class TestFetchCounts:
    @patch("app.repositories.traceql_experiment.httpx.Client")
    def test_returns_count_map(self, mock_cls):
        mock_cls.return_value = _make_mock_client(
            [
                {"experiment_id": "exp_a", "total": "110"},
                {"experiment_id": "exp_b", "total": "55"},
            ]
        )
        with patch.dict(os.environ, {"TRACEQL_BASE_URL": "http://test.local"}):
            counts = _fetch_counts()
        assert counts == {"exp_a": 110, "exp_b": 55}

    @patch("app.repositories.traceql_experiment.httpx.Client")
    def test_query_targets_count_by_experiment_id(self, mock_cls):
        mock_ctx = _make_mock_client([])
        mock_cls.return_value = mock_ctx
        with patch.dict(os.environ, {"TRACEQL_BASE_URL": "http://test.local"}):
            _fetch_counts()
        payload = mock_ctx.post.call_args[1]["json"]
        assert "count()" in payload["query"]
        assert "experiment_id" in payload["query"]


# ── _aggregate_experiment tests ───────────────────────────────────────────────


class TestAggregateExperiment:
    @patch("app.repositories.traceql_experiment.httpx.Client")
    def test_returns_experiment_dict(self, mock_cls):
        mock_cls.return_value = _make_mock_client(
            [
                {
                    "experiment_id": "e1",
                    "model": "gpt-4",
                    "scaffold": "claude_code",
                    "latest_iteration": 2,
                    "total_trajectories": 80,
                    "mean_reward": 0.5,
                    "pass_rate": 0.6,
                    "total_tokens": 8000,
                    "first_seen": 1700000000,
                }
            ]
        )
        with patch.dict(os.environ, {"TRACEQL_BASE_URL": "http://test.local"}):
            result = _aggregate_experiment("e1")
        assert result is not None
        assert result["id"] == "e1"
        assert result["config"]["scaffolds"] == ["claude_code"]

    @patch("app.repositories.traceql_experiment.httpx.Client")
    def test_returns_none_when_no_rows(self, mock_cls):
        mock_cls.return_value = _make_mock_client([])
        with patch.dict(os.environ, {"TRACEQL_BASE_URL": "http://test.local"}):
            result = _aggregate_experiment("missing-exp")
        assert result is None

    @patch("app.repositories.traceql_experiment.httpx.Client")
    def test_filters_by_experiment_id_in_query(self, mock_cls):
        mock_ctx = _make_mock_client([])
        mock_cls.return_value = mock_ctx
        with patch.dict(os.environ, {"TRACEQL_BASE_URL": "http://test.local"}):
            _aggregate_experiment("my-exp")
        payload = mock_ctx.post.call_args[1]["json"]
        assert 'experiment_id = "my-exp"' in payload["query"]


# ── _aggregate_all tests ─────────────────────────────────────────────────────


class TestAggregateAll:
    @patch("app.repositories.traceql_experiment.httpx.Client")
    def test_groups_by_experiment_id(self, mock_cls):
        mock_cls.return_value = _make_mock_client(
            [
                {
                    "experiment_id": "e1",
                    "model": "gpt-4",
                    "scaffold": "claude_code",
                    "latest_iteration": 3,
                    "total_trajectories": 100,
                    "mean_reward": 0.6,
                    "pass_rate": 0.7,
                    "total_tokens": 10000,
                    "first_seen": 1700000000,
                },
                {
                    "experiment_id": "e2",
                    "model": "gpt-4",
                    "scaffold": "aider",
                    "latest_iteration": 2,
                    "total_trajectories": 50,
                    "mean_reward": 0.4,
                    "pass_rate": 0.5,
                    "total_tokens": 5000,
                    "first_seen": 1700000100,
                },
            ]
        )
        with patch.dict(os.environ, {"TRACEQL_BASE_URL": "http://test.local"}):
            result = _aggregate_all()
        assert len(result) == 2
        ids = {e["id"] for e in result}
        assert ids == {"e1", "e2"}

    @patch("app.repositories.traceql_experiment.httpx.Client")
    def test_empty_response_returns_empty_list(self, mock_cls):
        mock_cls.return_value = _make_mock_client([])
        with patch.dict(os.environ, {"TRACEQL_BASE_URL": "http://test.local"}):
            result = _aggregate_all()
        assert result == []

    @patch("app.repositories.traceql_experiment.httpx.Client")
    def test_rows_without_experiment_id_are_skipped(self, mock_cls):
        mock_cls.return_value = _make_mock_client(
            [
                {
                    "model": "gpt-4",
                    "scaffold": "s",
                    "latest_iteration": 1,
                    "total_trajectories": 10,
                    "mean_reward": 0.5,
                    "pass_rate": 0.5,
                    "total_tokens": 100,
                    "first_seen": 1700000000,
                },
                {
                    "experiment_id": "e1",
                    "model": "gpt-4",
                    "scaffold": "claude_code",
                    "latest_iteration": 3,
                    "total_trajectories": 100,
                    "mean_reward": 0.6,
                    "pass_rate": 0.7,
                    "total_tokens": 10000,
                    "first_seen": 1700000000,
                },
            ]
        )
        with patch.dict(os.environ, {"TRACEQL_BASE_URL": "http://test.local"}):
            result = _aggregate_all()
        assert len(result) == 1
        assert result[0]["id"] == "e1"

    @patch("app.repositories.traceql_experiment.httpx.Client")
    def test_merges_same_experiment_id_rows(self, mock_cls):
        mock_cls.return_value = _make_mock_client(
            [
                {
                    "experiment_id": "e1",
                    "model": "gpt-4",
                    "scaffold": "claude_code",
                    "latest_iteration": 5,
                    "total_trajectories": 100,
                    "mean_reward": 0.6,
                    "pass_rate": 0.7,
                    "total_tokens": 10000,
                    "first_seen": 1700000000,
                },
                {
                    "experiment_id": "e1",
                    "model": "gpt-4",
                    "scaffold": "aider",
                    "latest_iteration": 3,
                    "total_trajectories": 50,
                    "mean_reward": 0.4,
                    "pass_rate": 0.5,
                    "total_tokens": 5000,
                    "first_seen": 1700000100,
                },
            ]
        )
        with patch.dict(os.environ, {"TRACEQL_BASE_URL": "http://test.local"}):
            result = _aggregate_all()
        assert len(result) == 1
        exp = result[0]
        assert exp["id"] == "e1"
        assert exp["total_trajectories"] == 150
        assert set(exp["config"]["scaffolds"]) == {"claude_code", "aider"}


# ── TraceQLExperimentRepository tests ───────────────────────────────────────


class TestTraceQLExperimentRepository:
    @patch("app.repositories.traceql_experiment._fetch_counts")
    @patch("app.repositories.traceql_experiment._aggregate_experiment")
    def test_get_experiments_aggregates_each_id(self, mock_agg, mock_counts):
        mock_counts.return_value = {"exp_a": 100, "exp_b": 50}
        mock_agg.side_effect = lambda eid: {"id": eid, "name": eid}
        repo = TraceQLExperimentRepository()
        result = repo.get_experiments()
        assert len(result) == 2
        ids = {e["id"] for e in result}
        assert ids == {"exp_a", "exp_b"}
        assert mock_agg.call_count == 2

    @patch("app.repositories.traceql_experiment._fetch_counts")
    @patch("app.repositories.traceql_experiment._aggregate_experiment")
    def test_get_experiments_uses_cache_when_count_unchanged(self, mock_agg, mock_counts):
        # Pre-populate cache
        repo_module._cache["exp_a"] = {
            "count": 100,
            "experiment": {"id": "exp_a", "name": "exp_a"},
            "iterations": None,
        }
        mock_counts.return_value = {"exp_a": 100}  # same count
        repo = TraceQLExperimentRepository()
        result = repo.get_experiments()
        assert len(result) == 1
        assert result[0]["id"] == "exp_a"
        mock_agg.assert_not_called()  # cache hit — no aggregation

    @patch("app.repositories.traceql_experiment._fetch_counts")
    @patch("app.repositories.traceql_experiment._aggregate_experiment")
    def test_get_experiments_re_aggregates_when_count_changes(self, mock_agg, mock_counts):
        # Pre-populate cache with old count
        repo_module._cache["exp_a"] = {
            "count": 99,
            "experiment": {"id": "exp_a", "name": "old"},
            "iterations": None,
        }
        mock_counts.return_value = {"exp_a": 100}  # count changed!
        mock_agg.return_value = {"id": "exp_a", "name": "new"}
        repo = TraceQLExperimentRepository()
        result = repo.get_experiments()
        assert result[0]["name"] == "new"
        mock_agg.assert_called_once_with("exp_a")

    @patch("app.repositories.traceql_experiment._fetch_counts")
    @patch("app.repositories.traceql_experiment._aggregate_all")
    def test_get_experiments_falls_back_to_aggregate_all_on_count_failure(self, mock_agg_all, mock_counts):
        mock_counts.side_effect = Exception("network error")
        mock_agg_all.return_value = [{"id": "exp_x"}]
        repo = TraceQLExperimentRepository()
        result = repo.get_experiments()
        assert result == [{"id": "exp_x"}]
        mock_agg_all.assert_called_once()

    @patch("app.repositories.traceql_experiment._traceql_query")
    @patch("app.repositories.traceql_experiment._aggregate_experiment")
    def test_get_experiment_returns_none_for_missing(self, mock_agg, mock_query):
        mock_query.return_value = []  # count query → empty → count = 0
        mock_agg.return_value = None
        repo = TraceQLExperimentRepository()
        result = repo.get_experiment("nonexistent")
        assert result is None

    @patch("app.repositories.traceql_experiment._traceql_query")
    @patch("app.repositories.traceql_experiment._aggregate_experiment")
    def test_get_experiment_uses_cache(self, mock_agg, mock_query):
        # Pre-populate cache
        repo_module._cache["e1"] = {
            "count": 10,
            "experiment": {"id": "e1"},
            "iterations": None,
        }
        mock_query.return_value = [{"experiment_id": "e1", "total": "10"}]
        repo = TraceQLExperimentRepository()
        result = repo.get_experiment("e1")
        assert result == {"id": "e1"}
        mock_agg.assert_not_called()

    @patch("app.repositories.traceql_experiment._traceql_query")
    @patch("app.repositories.traceql_experiment._aggregate_experiment")
    def test_get_experiment_falls_back_on_count_failure(self, mock_agg, mock_query):
        mock_query.side_effect = Exception("network error")
        mock_agg.return_value = {"id": "e1"}
        repo = TraceQLExperimentRepository()
        result = repo.get_experiment("e1")
        assert result == {"id": "e1"}

    @patch("app.repositories.traceql_experiment._traceql_query")
    @patch("app.repositories.traceql_experiment._aggregate_experiment")
    def test_get_experiment_writes_cache_on_first_call(self, mock_agg, mock_query):
        mock_query.return_value = [{"experiment_id": "e1", "total": "10"}]
        mock_agg.return_value = {"id": "e1", "name": "e1"}
        repo = TraceQLExperimentRepository()
        result = repo.get_experiment("e1")
        assert result == {"id": "e1", "name": "e1"}
        # Verify cache was written
        assert "e1" in repo_module._cache
        assert repo_module._cache["e1"]["count"] == 10
        assert repo_module._cache["e1"]["experiment"] == {"id": "e1", "name": "e1"}


# ── TraceQLIterationRepository tests ────────────────────────────────────────


class TestTraceQLIterationRepository:
    @patch("app.repositories.traceql_experiment._traceql_query")
    def test_get_iterations_returns_sorted_items(self, mock_query):
        # Two calls: count query + iteration distinct query
        mock_query.side_effect = [
            [{"experiment_id": "e1", "total": "30"}],  # count
            [{"iteration": "2"}, {"iteration": "0"}, {"iteration": "1"}],  # iterations
        ]
        repo = TraceQLIterationRepository()
        result = repo.get_iterations("e1")
        assert len(result) == 3
        assert [r["iteration_num"] for r in result] == [0, 1, 2]
        assert result[0]["id"] == "iter-0"
        assert result[0]["experiment_id"] == "e1"
        assert result[0]["metrics"] == {}
        assert result[0]["checkpoint"] is None

    @patch("app.repositories.traceql_experiment._traceql_query")
    def test_get_iterations_uses_cache(self, mock_query):
        cached_items = [{"id": "iter-0", "iteration_num": 0, "experiment_id": "e1"}]
        repo_module._cache["e1"] = {
            "count": 30,
            "experiment": None,
            "iterations": cached_items,
        }
        # Count query returns same count
        mock_query.return_value = [{"experiment_id": "e1", "total": "30"}]
        repo = TraceQLIterationRepository()
        result = repo.get_iterations("e1")
        assert result == cached_items
        assert mock_query.call_count == 1  # only count query, no iteration query

    @patch("app.repositories.traceql_experiment._traceql_query")
    def test_get_iterations_re_queries_when_count_changes(self, mock_query):
        repo_module._cache["e1"] = {
            "count": 29,  # old count
            "experiment": None,
            "iterations": [{"id": "iter-0"}],
        }
        mock_query.side_effect = [
            [{"experiment_id": "e1", "total": "30"}],  # count changed!
            [{"iteration": "0"}, {"iteration": "1"}],  # re-fetch iterations
        ]
        repo = TraceQLIterationRepository()
        result = repo.get_iterations("e1")
        assert len(result) == 2
        assert mock_query.call_count == 2

    @patch("app.repositories.traceql_experiment._traceql_query")
    def test_get_iterations_skips_cache_on_count_failure(self, mock_query):
        mock_query.side_effect = [
            Exception("network"),  # count query fails
            [{"iteration": "0"}],  # iteration query succeeds
        ]
        repo = TraceQLIterationRepository()
        result = repo.get_iterations("e1")
        assert len(result) == 1
        assert result[0]["iteration_num"] == 0
        assert repo_module._cache.get("e1") is None

    def test_get_iteration_returns_none(self):
        repo = TraceQLIterationRepository()
        assert repo.get_iteration("iter-0") is None

    @patch("app.repositories.traceql_experiment._traceql_query")
    def test_get_iterations_writes_cache(self, mock_query):
        mock_query.side_effect = [
            [{"experiment_id": "e1", "total": "5"}],
            [{"iteration": "0"}, {"iteration": "1"}],
        ]
        repo = TraceQLIterationRepository()
        repo.get_iterations("e1")
        assert "e1" in repo_module._cache
        assert repo_module._cache["e1"]["count"] == 5
        assert len(repo_module._cache["e1"]["iterations"]) == 2

    @patch("app.repositories.traceql_experiment._traceql_query")
    def test_get_iterations_empty_count_rows_still_fetches(self, mock_query):
        mock_query.side_effect = [
            [],  # count 查询返回空列表 → new_count = None
            [{"iteration": "0"}],  # 仍然执行迭代查询
        ]
        repo = TraceQLIterationRepository()
        result = repo.get_iterations("e1")
        assert len(result) == 1
        assert result[0]["iteration_num"] == 0
        # new_count 为 None，不写缓存
        assert repo_module._cache.get("e1") is None


# ── dependencies.py switching tests ──────────────────────────────────────────


class TestDependencyInjectionSwitching:
    def test_returns_traceql_repo_when_base_url_set(self):
        from app.repositories import dependencies

        with patch.dict(os.environ, {"TRACEQL_BASE_URL": "http://test.local"}):
            repo = dependencies.get_experiment_repo()
        assert isinstance(repo, TraceQLExperimentRepository)

    def test_returns_traceql_iteration_repo_when_base_url_set(self):
        from app.repositories import dependencies

        with patch.dict(os.environ, {"TRACEQL_BASE_URL": "http://test.local"}):
            repo = dependencies.get_iteration_repo()
        assert isinstance(repo, TraceQLIterationRepository)

    def test_returns_mock_store_when_no_base_url(self):
        from app.repositories import dependencies

        env = {k: v for k, v in os.environ.items() if k != "TRACEQL_BASE_URL"}
        with patch.dict(os.environ, env, clear=True):
            repo = dependencies.get_experiment_repo()
        assert not isinstance(repo, TraceQLExperimentRepository)

    def test_returns_mock_store_iteration_when_no_base_url(self):
        from app.repositories import dependencies

        env = {k: v for k, v in os.environ.items() if k != "TRACEQL_BASE_URL"}
        with patch.dict(os.environ, env, clear=True):
            repo = dependencies.get_iteration_repo()
        assert not isinstance(repo, TraceQLIterationRepository)
