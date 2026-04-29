"""API tests for experiments endpoints."""


class TestExperimentsAPI:
    def test_list_experiments(self, client):
        r = client.get("/api/v1/experiments")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 6
        assert "items" in data

    def test_list_experiments_by_project(self, client):
        r = client.get(
            "/api/v1/experiments",
            params={"project_id": "proj-code-agent-v2"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 3
        for e in data["items"]:
            assert e["project_id"] == "proj-code-agent-v2"

    def test_list_experiments_by_status(self, client):
        r = client.get(
            "/api/v1/experiments",
            params={"status": "running"},
        )
        assert r.status_code == 200
        data = r.json()
        for e in data["items"]:
            assert e["status"] == "running"

    def test_list_experiments_by_scaffold(self, client):
        r = client.get(
            "/api/v1/experiments",
            params={"scaffold": "openclaw"},
        )
        assert r.status_code == 200
        data = r.json()
        for e in data["items"]:
            assert "openclaw" in e["config"]["scaffolds"]

    def test_get_experiment(self, client):
        r = client.get("/api/v1/experiments/exp-grpo-cc")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == "exp-grpo-cc"
        assert isinstance(data["config"]["scaffolds"], list)
        assert data["config"]["algorithm"] == "GRPO"

    def test_get_experiment_not_found(self, client):
        r = client.get("/api/v1/experiments/nonexistent")
        assert r.status_code == 404

    def test_list_iterations(self, client):
        r = client.get("/api/v1/experiments/exp-grpo-cc/iterations")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 50
        # Check first iteration has full metrics
        it = data["items"][0]
        assert "metrics" in it
        assert "checkpoint" in it
        m = it["metrics"]
        assert "mean_reward" in m
        assert "pass_rate" in m
        assert "total_tokens" in m

    def test_list_iterations_not_found(self, client):
        r = client.get("/api/v1/experiments/nonexistent/iterations")
        assert r.status_code == 404

    def test_list_iteration_trajectories(self, client):
        r = client.get("/api/v1/experiments/exp-grpo-cc/iterations/1/trajectories")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 100
        for t in data["items"]:
            assert t["iteration_num"] == 1

    def test_list_iteration_trajectories_filter_scaffold(self, client):
        r = client.get(
            "/api/v1/experiments/exp-grpo-cc/iterations/1/trajectories",
            params={"scaffold": "claude_code"},
        )
        assert r.status_code == 200
        data = r.json()
        for t in data["items"]:
            assert t["scaffold"] == "claude_code"

    def test_list_iteration_trajectories_filter_outcome(self, client):
        r = client.get(
            "/api/v1/experiments/exp-grpo-cc/iterations/1/trajectories",
            params={"outcome": "success"},
        )
        assert r.status_code == 200
        data = r.json()
        for t in data["items"]:
            assert t["outcome"] == "success"
