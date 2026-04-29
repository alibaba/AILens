"""Pydantic models for all Request/Response schemas.

Aligned to PRD v0.8.2 Section 5.1 Core Schema.
Python 3.6.8 compatible — uses List[X], Dict[X,Y], Optional[X].
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# ──────────────────────────── Generic ────────────────────────────


class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[Any]


# ──────────────────────────── Project ────────────────────────────


class Project(BaseModel):
    id: str
    name: str
    description: str = ""
    owner: str = ""
    tags: Dict[str, str] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class CreateProject(BaseModel):
    name: str
    description: str = ""
    owner: str = ""
    tags: Dict[str, str] = Field(default_factory=dict)


# ──────────────────────────── Benchmark (was TaskSuite) ──────────


class Benchmark(BaseModel):
    id: str
    project_id: str
    name: str
    version: str
    source: str
    total_tasks: int
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Task(BaseModel):
    id: str
    benchmark_id: str
    category: str
    difficulty: str
    language: str
    repo: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ──────────────────────────── Experiment ─────────────────────────


class ExperimentConfig(BaseModel):
    model: str
    scaffolds: List[str]
    algorithm: str
    reward_function: str
    reward_components: List[str]
    hyperparams: Dict[str, Any] = Field(default_factory=dict)
    benchmark_id: str


class Experiment(BaseModel):
    id: str
    project_id: str
    name: str
    status: str  # running / completed / failed / cancelled
    config: ExperimentConfig
    tags: Dict[str, str] = Field(default_factory=dict)
    created_at: datetime

    # summary metrics (latest iteration)
    latest_iteration: Optional[int] = None
    mean_reward: Optional[float] = None
    pass_rate: Optional[float] = None
    total_trajectories: Optional[int] = None
    total_tokens: Optional[int] = None


# ──────────────────────────── Iteration ──────────────────────────


class Checkpoint(BaseModel):
    saved: bool
    path: str
    policy_version: str


class IterationMetrics(BaseModel):
    # A. Convergence
    mean_reward: float
    median_reward: float
    reward_std: float
    reward_p5: float
    reward_p25: float
    reward_p75: float
    reward_p95: float
    pass_rate: float
    pass_rate_delta: float
    total_trajectories: int

    # D. Efficiency
    total_tokens: int
    total_input_tokens: int
    total_output_tokens: int
    mean_tokens_per_trajectory: float
    tokens_per_reward: Optional[float] = None
    input_output_ratio: float
    mean_turns: float
    mean_duration_ms: int
    mean_sandbox_create_duration_ms: int
    mean_verify_duration_ms: int

    # C. Agent behaviour
    tool_call_count: int


class Iteration(BaseModel):
    id: str
    experiment_id: str
    iteration_num: int
    timestamp: datetime
    checkpoint: Checkpoint
    metrics: IterationMetrics


# ──────────────────────────── Trajectory ─────────────────────────


class Trajectory(BaseModel):
    id: str
    experiment_id: str
    iteration_id: str
    task_id: str
    scaffold: str
    outcome: str  # success / failure / timeout / error
    reward: float
    reward_components: Dict[str, float] = Field(default_factory=dict)
    passed: bool
    total_turns: int
    total_events: int
    duration_ms: int
    sandbox_create_duration_ms: int
    verify_duration_ms: int
    total_tokens: int
    input_tokens: int
    output_tokens: int
    # Agent behaviour stats
    tool_call_count: int
    tool_success_rate: float
    error_turn_count: int
    first_error_turn: int
    llm_time_ratio: float
    tokens_per_turn: float
    tags: Dict[str, str] = Field(default_factory=dict)
    otel_trace_id: str
    created_at: datetime


# ──────────────────────────── Turn / Event ───────────────────────


class EventAction(BaseModel):
    tool_name: str
    tool_input: str
    tool_output: str
    status: str = "success"  # success / error


class EventLLM(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    model: str
    latency_ms: int


class EventObservation(BaseModel):
    content: str
    reward: float


class Event(BaseModel):
    id: str
    turn_id: str
    trajectory_id: str
    event_num: int
    type: str  # reasoning / action / observation
    action: Optional[EventAction] = None
    llm: Optional[EventLLM] = None
    observation: Optional[EventObservation] = None
    timestamp: datetime
    duration_ms: int
    error: Optional[str] = None
    otel_span_id: str


class Turn(BaseModel):
    id: str
    trajectory_id: str
    turn_num: int
    total_tokens: int
    duration_ms: int
    reward: float
    has_error: bool
    tool_name: Optional[str] = None
    tool_succeeded: Optional[bool] = None
    otel_root_span_id: str
    events: List[Event] = Field(default_factory=list)


# ──────────────────────────── Trace / Span ───────────────────────


class SpanAttribute(BaseModel):
    key: str
    value: str


class Span(BaseModel):
    span_id: str
    parent_span_id: Optional[str] = None
    operation_name: str
    service_name: str
    start_time: datetime
    duration_ms: int
    status: str  # ok / error
    attributes: List[SpanAttribute] = Field(default_factory=list)
    events: List[Dict[str, Any]] = Field(default_factory=list)
    children: List["Span"] = Field(default_factory=list)


Span.update_forward_refs()


class TraceSearchResult(BaseModel):
    trace_id: str
    scaffold: str
    duration_ms: int
    span_count: int
    status: str  # ok / error
    has_rl_context: bool
    start_time: datetime
    service_name: str


class RLContext(BaseModel):
    trajectory_id: str
    experiment_id: str
    experiment_name: str
    iteration_num: int
    reward: float
    outcome: str
    turn_num: Optional[int] = None
    task_id: str


class TraceDetail(BaseModel):
    trace_id: str
    spans: List[Span]
    duration_ms: int
    span_count: int
    has_error: bool
    rl_context: Optional[RLContext] = None


# ──────────────────────────── Agent Service ──────────────────────


class AgentService(BaseModel):
    id: str
    project_id: str
    name: str
    scaffold: str
    model: str
    environment: str  # production / staging / development
    status: str  # active / inactive / degraded
    endpoint: str
    otel_service_name: str
    tags: Dict[str, str] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


# ──────────────────────────── Metrics ────────────────────────────


class MetricDataPoint(BaseModel):
    timestamp: datetime
    value: float


class MetricSeries(BaseModel):
    metric_name: str
    labels: Dict[str, str] = Field(default_factory=dict)
    values: List[MetricDataPoint]


class MetricQueryResult(BaseModel):
    series: List[MetricSeries]


class MetricLabel(BaseModel):
    name: str
    values: List[str]


# ──────────────────────────── Annotation ─────────────────────────


class Annotation(BaseModel):
    id: str
    trajectory_id: str
    experiment_id: str
    source: str  # auto / manual
    pattern_type: str
    description: str
    affected_turns: List[int]
    severity: str  # info / warning / error
    created_at: datetime


class CreateAnnotation(BaseModel):
    trajectory_id: str
    experiment_id: str
    pattern_type: str
    description: str
    affected_turns: List[int] = Field(default_factory=list)
    severity: str = "info"


# ──────────────────────────── Alerts ─────────────────────────────


class AlertRule(BaseModel):
    id: str
    name: str
    expression: str
    threshold: float
    severity: str  # critical / warning / info
    for_duration: str
    enabled: bool
    notification_channels: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class CreateAlertRule(BaseModel):
    name: str
    expression: str
    threshold: float
    severity: str = "warning"
    for_duration: str = "5m"
    notification_channels: List[str] = Field(default_factory=list)


class ActiveAlert(BaseModel):
    id: str
    rule_id: str
    rule_name: str
    severity: str
    agent_name: str
    current_value: float
    threshold: float
    firing_since: datetime
    status: str  # firing / resolved
    labels: Dict[str, str] = Field(default_factory=dict)
