"""Tests for Pydantic schemas — serialization/deserialization."""

from datetime import datetime, timezone

from app.models.schemas import (
    AgentService,
    Benchmark,
    CreateProject,
    Event,
    EventAction,
    Experiment,
    ExperimentConfig,
    IterationMetrics,
    Project,
    Task,
    Trajectory,
    Turn,
)


class TestProject:
    def test_project_create(self):
        p = Project(
            id="proj-1",
            name="Test",
            description="desc",
            owner="alice",
            tags={"team": "a"},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        assert p.id == "proj-1"
        assert p.name == "Test"
        d = p.dict()
        assert "id" in d
        assert "tags" in d

    def test_project_defaults(self):
        p = Project(
            id="proj-2",
            name="Test2",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        assert p.description == ""
        assert p.tags == {}

    def test_create_project(self):
        cp = CreateProject(name="New Project", owner="bob")
        d = cp.dict()
        assert d["name"] == "New Project"
        assert d["owner"] == "bob"


class TestBenchmark:
    def test_benchmark_create(self):
        b = Benchmark(
            id="bench-1",
            project_id="proj-1",
            name="SWE-bench",
            version="1.0",
            source="test",
            total_tasks=100,
        )
        assert b.project_id == "proj-1"
        assert b.total_tasks == 100

    def test_task_create(self):
        t = Task(
            id="task-001",
            benchmark_id="bench-1",
            category="code-fix",
            difficulty="easy",
            language="python",
            repo="django/django",
        )
        assert t.benchmark_id == "bench-1"
        assert t.category == "code-fix"


class TestExperiment:
    def test_experiment_config_scaffolds_list(self):
        cfg = ExperimentConfig(
            model="qwen3-8b",
            scaffolds=["claude_code", "openclaw"],
            algorithm="GRPO",
            reward_function="composite_v2",
            reward_components=["task", "format"],
            benchmark_id="bench-1",
        )
        assert isinstance(cfg.scaffolds, list)
        assert len(cfg.scaffolds) == 2

    def test_experiment_full(self):
        cfg = ExperimentConfig(
            model="qwen3-8b",
            scaffolds=["claude_code"],
            algorithm="PPO",
            reward_function="v1",
            reward_components=["task"],
            benchmark_id="bench-1",
        )
        exp = Experiment(
            id="exp-1",
            project_id="proj-1",
            name="Test Exp",
            status="running",
            config=cfg,
            created_at=datetime.now(timezone.utc),
        )
        assert exp.project_id == "proj-1"
        assert exp.config.scaffolds == ["claude_code"]
        d = exp.dict()
        assert d["config"]["scaffolds"] == ["claude_code"]


class TestIteration:
    def test_iteration_metrics(self):
        m = IterationMetrics(
            mean_reward=0.5,
            median_reward=0.45,
            reward_std=0.1,
            reward_p5=0.1,
            reward_p25=0.3,
            reward_p75=0.7,
            reward_p95=0.9,
            pass_rate=0.6,
            pass_rate_delta=0.02,
            total_trajectories=100,
            total_tokens=50000,
            total_input_tokens=30000,
            total_output_tokens=20000,
            mean_tokens_per_trajectory=500.0,
            tokens_per_reward=100000.0,
            input_output_ratio=1.5,
            mean_turns=10.0,
            mean_duration_ms=5000,
            mean_sandbox_create_duration_ms=600,
            mean_verify_duration_ms=400,
            tool_call_count=800,
        )
        assert m.pass_rate == 0.6
        assert m.tokens_per_reward == 100000.0


class TestTrajectory:
    def test_trajectory_full(self):
        t = Trajectory(
            id="traj-1",
            experiment_id="exp-1",
            iteration_id="iter-1",
            task_id="task-001",
            scaffold="claude_code",
            outcome="success",
            reward=0.85,
            reward_components={"task": 1.0, "format": 0.8},
            passed=True,
            total_turns=8,
            total_events=24,
            duration_ms=12000,
            sandbox_create_duration_ms=1500,
            verify_duration_ms=800,
            total_tokens=3000,
            input_tokens=2000,
            output_tokens=1000,
            tool_call_count=7,
            tool_success_rate=0.95,
            error_turn_count=0,
            first_error_turn=-1,
            llm_time_ratio=0.6,
            tokens_per_turn=375.0,
            tags={},
            otel_trace_id="abc123",
            created_at=datetime.now(timezone.utc),
        )
        assert t.passed is True
        assert t.reward_components["task"] == 1.0


class TestTurnEvent:
    def test_event_action(self):
        ea = EventAction(
            tool_name="bash",
            tool_input="ls -la",
            tool_output="total 0",
            status="success",
        )
        assert ea.status == "success"

    def test_event_types(self):
        e = Event(
            id="ev-1",
            turn_id="turn-1",
            trajectory_id="traj-1",
            event_num=1,
            type="action",
            action=EventAction(
                tool_name="bash",
                tool_input="ls",
                tool_output="ok",
                status="success",
            ),
            timestamp=datetime.now(timezone.utc),
            duration_ms=100,
            otel_span_id="span1",
        )
        assert e.type == "action"
        assert e.action is not None
        assert e.llm is None

    def test_turn_with_events(self):
        t = Turn(
            id="turn-1",
            trajectory_id="traj-1",
            turn_num=1,
            total_tokens=500,
            duration_ms=2000,
            reward=0.1,
            has_error=False,
            tool_name="bash",
            tool_succeeded=True,
            otel_root_span_id="rootspan1",
        )
        assert t.events == []
        assert t.tool_succeeded is True


class TestAgentService:
    def test_agent_service(self):
        svc = AgentService(
            id="svc-1",
            project_id="proj-1",
            name="coding-agent-prod",
            scaffold="claude_code",
            model="qwen3-72b",
            environment="production",
            status="active",
            endpoint="https://example.com/agent",
            otel_service_name="coding-agent-prod",
            tags={"region": "us-east-1"},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        assert svc.environment == "production"
        assert svc.status == "active"
        d = svc.dict()
        assert "otel_service_name" in d
