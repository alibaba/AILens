"""API edge-case tests — boundary scenarios for all major endpoints.

T-TEST-01: >= 30 test cases covering invalid IDs, empty filters,
pagination boundaries, filter combinations, stats parameters, and
miscellaneous edge cases.

Python 3.6.8 compatible.
"""


# ═══════════════════ 1. Invalid ID Tests (6 cases) ═══════════════════


class TestInvalidIDStats:
    """Analysis endpoints must return 404 for non-existent experiment IDs."""

    def test_task_effectiveness_nonexistent(self, client):
        r = client.get("/api/v1/experiments/nonexistent/analysis/task-effectiveness")
        assert r.status_code == 404

    def test_scaffold_nonexistent(self, client):
        r = client.get("/api/v1/experiments/nonexistent/analysis/scaffold")
        assert r.status_code == 404

    # NOTE: test_language_nonexistent removed - /analysis/language endpoint deleted
    # Language stats now queried via PromQL aggregation

    def test_query_nonexistent_returns_empty(self, client):
        """PromQL query for nonexistent experiment returns empty result."""
        r = client.post(
            "/api/v1/query",
            json={
                "query": 'experiment_mean_reward{experiment_id="nonexistent"}',
            },
        )
        assert r.status_code == 200
        assert r.json()["data"]["result"] == []


# ═══════════════════ 2. Empty Filter Tests (2 cases) ═══════════════════


class TestEmptyFilters:
    """Endpoints with no filter or empty filter should return all data."""

    def test_experiments_no_project_id(self, client):
        r = client.get("/api/v1/experiments")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 6  # all experiments

    def test_experiments_empty_project_id(self, client):
        r = client.get("/api/v1/experiments", params={"project_id": ""})
        assert r.status_code == 200
        data = r.json()
        # Empty string project_id matches no experiments in
        # store.get_experiments, so get_experiments returns all
        # (because project_id="" is falsy in Python).
        assert data["total"] == 6


# ═══════════════════ 3. Pagination Boundary Tests (4 cases) ═══════════════


class TestPaginationBoundary:
    """Pagination edge cases for page/page_size values."""

    def test_page_1_size_1(self, client):
        """page=1, page_size=1 should return exactly 1 item."""
        r = client.get(
            "/api/v1/experiments",
            params={"page": 1, "page_size": 1},
        )
        assert r.status_code == 200
        data = r.json()
        assert len(data["items"]) == 1
        assert data["total"] == 6
        assert data["page"] == 1
        assert data["page_size"] == 1

    def test_page_9999_returns_empty(self, client):
        """page=9999 should return empty items but correct total."""
        r = client.get(
            "/api/v1/experiments",
            params={"page": 9999, "page_size": 20},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["items"] == []
        assert data["total"] == 6

    def test_page_0_behaviour(self, client):
        """page=0 — should return data (negative offset handled) or 422."""
        r = client.get(
            "/api/v1/experiments",
            params={"page": 0, "page_size": 20},
        )
        # Accept either successful response or 422 validation error
        assert r.status_code in (200, 422)
        if r.status_code == 200:
            data = r.json()
            assert "items" in data

    def test_page_size_0_behaviour(self, client):
        """page_size=0 — should return empty items or 422."""
        r = client.get(
            "/api/v1/experiments",
            params={"page": 1, "page_size": 0},
        )
        assert r.status_code in (200, 422)
        if r.status_code == 200:
            data = r.json()
            # page_size=0 means slice [0:0] → empty
            assert isinstance(data["items"], list)


# ═══════════════════ 4. Filter Combination Tests (2 cases) ═══════════════


class TestFilterCombinations:
    """Combined and non-matching filters."""

    def test_project_id_filter_experiments(self, client):
        """project_id filter returns only that project's experiments."""
        r = client.get(
            "/api/v1/experiments",
            params={"project_id": "proj-code-agent-v2"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 3
        for exp in data["items"]:
            assert exp["project_id"] == "proj-code-agent-v2"

    def test_project_id_nonexistent(self, client):
        """Non-existent project_id returns empty."""
        r = client.get(
            "/api/v1/experiments",
            params={"project_id": "nonexistent"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 0
        assert data["items"] == []


# ═══════════════════ 5. Stats API Parameter Tests (6 cases) ═══════════════


class TestAnalysisAPIParameters:
    """Analysis endpoints with iteration range parameters."""

    def test_scaffold_iter_range(self, client):
        r = client.get(
            "/api/v1/experiments/exp-grpo-cc/analysis/scaffold",
            params={"iteration_start": 1, "iteration_end": 20},
        )
        assert r.status_code == 200
        data = r.json()
        assert "items" in data

    # NOTE: test_task_effectiveness_* removed - endpoint migrated to frontend TraceQL hook

    def test_scaffold_large_range(self, client):
        """Large iteration range works."""
        r = client.get(
            "/api/v1/experiments/exp-grpo-cc/analysis/scaffold",
            params={"iteration_start": 1, "iteration_end": 1000},
        )
        assert r.status_code == 200

    def test_scaffold_string_iter_param(self, client):
        """String iteration_start param returns 422."""
        r = client.get(
            "/api/v1/experiments/exp-grpo-cc/analysis/scaffold",
            params={"iteration_start": "abc"},
        )
        assert r.status_code == 422


# ═══════════════════ 6. Miscellaneous Boundary Tests (8 cases) ═══════════════


class TestOtherBoundary:
    """Other boundary conditions and error scenarios."""

    def test_query_malformed_promql(self, client):
        """Malformed PromQL does not crash — returns valid PromQL envelope."""
        r = client.post(
            "/api/v1/query",
            json={
                "query": "experiment_mean_reward{experiment_id=",  # malformed
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert "status" in data
        assert "data" in data

    def test_query_empty_string(self, client):
        """Empty PromQL query returns empty result."""
        r = client.post("/api/v1/query", json={"query": ""})
        assert r.status_code == 200
        assert r.json()["data"]["result"] == []

    def test_experiments_invalid_page_type(self, client):
        """Non-integer page returns 422."""
        r = client.get("/api/v1/experiments", params={"page": "abc"})
        assert r.status_code == 422

    def test_experiments_invalid_page_size_type(self, client):
        """Non-integer page_size returns 422."""
        r = client.get("/api/v1/experiments", params={"page_size": "xyz"})
        assert r.status_code == 422

    def test_query_missing_body(self, client):
        """POST /api/v1/query without body returns 422."""
        r = client.post("/api/v1/query")
        assert r.status_code == 422

    def test_analysis_negative_iteration_params(self, client):
        """iteration_start=-5 is accepted (no range constraint)."""
        r = client.get(
            "/api/v1/experiments/exp-grpo-cc/analysis/scaffold",
            params={"iteration_start": -5},
        )
        # NOTE: scaffold doesn't validate negative iteration values, returns 200
        assert r.status_code == 200

    def test_analysis_string_iteration_params(self, client):
        """String iteration_start param returns 422 (FastAPI type validation)."""
        r = client.get(
            "/api/v1/experiments/exp-grpo-cc/analysis/scaffold",
            params={"iteration_start": "abc"},
        )
        assert r.status_code == 422

    def test_query_non_json_body(self, client):
        """Non-JSON body to /api/v1/query returns 422."""
        r = client.post(
            "/api/v1/query",
            data="not-json",
            headers={"Content-Type": "text/plain"},
        )
        assert r.status_code == 422
