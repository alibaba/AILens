"""Tests for mock data generator — integrity and consistency."""

from app.mock import (
    DIFFICULTIES,
    LANGUAGES,
    SCAFFOLDS,
    TASK_CATEGORIES,
    MockDataStore,
)

# Mock tools for testing (TraceQL discovery available but not used in mocks)
TEST_TOOLS = ["bash", "file_edit", "web_search", "read_file", "submit"]


class TestMockDataIntegrity:
    """Verify mock data completeness and consistency."""

    def test_projects_count(self, mock_store):
        # At least 2 (may be more if test_create_project ran first)
        assert len(mock_store.projects) >= 2

    def test_project_fields(self, mock_store):
        for p in mock_store.projects:
            assert "id" in p
            assert "name" in p
            assert "description" in p
            assert "owner" in p
            assert "tags" in p
            assert "created_at" in p
            assert "updated_at" in p

    def test_tasks_count(self, mock_store):
        # 80 standalone tasks
        assert len(mock_store.tasks) == 80

    def test_tasks_have_valid_enums(self, mock_store):
        for t in mock_store.tasks:
            assert t["category"] in TASK_CATEGORIES
            assert t["difficulty"] in DIFFICULTIES
            assert t["language"] in LANGUAGES

    def test_experiments_count(self, mock_store):
        assert len(mock_store.experiments) == 6

    def test_experiments_project_fk(self, mock_store):
        project_ids = set(p["id"] for p in mock_store.projects)
        for e in mock_store.experiments:
            assert e["project_id"] in project_ids

    def test_experiments_per_project(self, mock_store):
        # Check original projects have 3 experiments each
        for pid in ["proj-code-agent-v2", "proj-reasoning"]:
            exps = [e for e in mock_store.experiments if e["project_id"] == pid]
            assert len(exps) == 3

    def test_experiment_config_scaffolds_is_list(self, mock_store):
        for e in mock_store.experiments:
            scaffolds = e["config"]["scaffolds"]
            assert isinstance(scaffolds, list)
            assert len(scaffolds) >= 1
            for s in scaffolds:
                assert s in SCAFFOLDS

    def test_iterations_count(self, mock_store):
        # 6 experiments * 50 iterations = 300
        total = sum(len(v) for v in mock_store.iterations.values())
        assert total == 300

    def test_iterations_experiment_fk(self, mock_store):
        exp_ids = set(e["id"] for e in mock_store.experiments)
        for exp_id, iters in mock_store.iterations.items():
            assert exp_id in exp_ids
            for it in iters:
                assert it["experiment_id"] == exp_id

    def test_iteration_nums_sequential(self, mock_store):
        for exp_id, iters in mock_store.iterations.items():
            nums = [it["iteration_num"] for it in iters]
            assert nums == list(range(1, 51))

    def test_trajectories_count(self, mock_store):
        # 6 experiments * 50 iterations * 100 trajectories = 30000
        assert len(mock_store.trajectories) == 30000

    def test_trajectory_experiment_fk(self, mock_store):
        exp_ids = set(e["id"] for e in mock_store.experiments)
        for t in mock_store.trajectories[:100]:
            assert t["experiment_id"] in exp_ids

    def test_trajectory_outcome_valid(self, mock_store):
        valid_outcomes = {"success", "failure", "timeout", "error"}
        for t in mock_store.trajectories[:200]:
            assert t["outcome"] in valid_outcomes

    def test_trajectory_scaffold_valid(self, mock_store):
        for t in mock_store.trajectories[:200]:
            assert t["scaffold"] in SCAFFOLDS

    def test_trajectory_reward_range(self, mock_store):
        for t in mock_store.trajectories[:200]:
            assert -0.5 <= t["reward"] <= 1.5

    def test_trajectory_passed_matches_outcome(self, mock_store):
        for t in mock_store.trajectories[:200]:
            if t["outcome"] == "success":
                assert t["passed"] is True
            else:
                assert t["passed"] is False

    def test_trajectory_turns_range(self, mock_store):
        for t in mock_store.trajectories[:200]:
            assert 5 <= t["total_turns"] <= 20

    def test_trajectory_has_reward_components(self, mock_store):
        for t in mock_store.trajectories[:100]:
            rc = t["reward_components"]
            assert "task" in rc
            assert "format" in rc
            assert "efficiency" in rc

    def test_trajectory_token_consistency(self, mock_store):
        for t in mock_store.trajectories[:100]:
            assert t["total_tokens"] == t["input_tokens"] + t["output_tokens"]

    def test_trajectory_has_agent_behavior_fields(self, mock_store):
        for t in mock_store.trajectories[:100]:
            assert "tool_call_count" in t
            assert "tool_success_rate" in t
            assert "error_turn_count" in t
            assert "first_error_turn" in t
            assert "llm_time_ratio" in t
            assert "tokens_per_turn" in t
            assert "otel_trace_id" in t

    def test_agent_services_count(self, mock_store):
        assert len(mock_store.agent_services) == 2

    def test_agent_services_project_fk(self, mock_store):
        project_ids = set(p["id"] for p in mock_store.projects)
        for s in mock_store.agent_services:
            assert s["project_id"] in project_ids

    def test_agent_services_valid_enums(self, mock_store):
        valid_env = {"production", "staging", "development"}
        valid_status = {"active", "inactive", "degraded"}
        for s in mock_store.agent_services:
            assert s["environment"] in valid_env
            assert s["status"] in valid_status

    def test_traces_count(self, mock_store):
        assert len(mock_store.traces) == 20

    def test_annotations_exist(self, mock_store):
        assert len(mock_store.annotations) > 0

    def test_annotation_fields(self, mock_store):
        for a in mock_store.annotations[:50]:
            assert "id" in a
            assert "trajectory_id" in a
            assert "experiment_id" in a
            assert "source" in a
            assert "pattern_type" in a
            assert "severity" in a

    def test_iteration_metrics_fields(self, mock_store):
        iters = list(mock_store.iterations.values())[0]
        for it in iters[:5]:
            m = it["metrics"]
            assert "mean_reward" in m
            assert "median_reward" in m
            assert "reward_std" in m
            assert "pass_rate" in m
            assert "total_trajectories" in m
            assert "total_tokens" in m

    def test_convergence_trend(self, mock_store):
        """Early iterations should have lower reward than later ones."""
        iters = list(mock_store.iterations.values())[0]
        early_reward = iters[0]["metrics"]["mean_reward"]
        late_reward = iters[-1]["metrics"]["mean_reward"]
        assert late_reward > early_reward


class TestMockStoreSingleton:
    def test_singleton(self):
        s1 = MockDataStore()
        s2 = MockDataStore()
        assert s1 is s2

    def test_store_is_initialized(self, mock_store):
        assert mock_store._initialized is True
