# AI Lens API Reference

> AI Lens Backend API v1
>
> Base URL: `http://localhost:8000/api/v1`
>
> Interactive docs: [Swagger UI](http://localhost:8000/docs) | [ReDoc](http://localhost:8000/redoc)

---

## Table of Contents

- [1. Projects](#1-projects)
- [2. Experiments](#2-experiments)
- [3. Iterations](#3-iterations)
- [4. Analysis](#4-analysis)
- [5. PromQL Query](#5-promql-query)
- [6. TraceQL (in-process)](#6-traceql-in-process)
- [7. Trace Proxy](#7-trace-proxy)
- [8. Traces](#8-traces)
- [9. Stats](#9-stats)
- [10. Annotations](#10-annotations)
- [11. Alerts](#11-alerts)
- [Common Conventions](#common-conventions)

---

## Common Conventions

### Pagination

Endpoints that return lists support:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number (1-based) |
| `page_size` | int | 20 | Items per page |

Paginated response shape:
```json
{
  "total": 100,
  "page": 1,
  "page_size": 20,
  "items": [...]
}
```

### Analysis Common Parameters

All `/experiments/{id}/analysis/*` endpoints support:

| Parameter | Type | Description |
|-----------|------|-------------|
| `split_by` | string | Group dimension: `scaffold` / `language` / `tool_schema` |
| `iteration_start` | int | Iteration range start |
| `iteration_end` | int | Iteration range end |
| `scaffold` | string | Filter by scaffold |
| `language` | string | Filter by language |
| `tool_schema` | string | Filter by tool schema |

### Error Responses

```json
{
  "detail": "Experiment not found"
}
```

| HTTP Status | Meaning |
|-------------|---------|
| 200 | Success |
| 404 | Resource not found |
| 422 | Validation error |
| 500 | Server error |
| 501 | Feature under construction |

---

## 1. Projects

### GET /projects

List all projects.

**Response:**
```json
{
  "total": 2,
  "items": [
    {
      "id": "proj-code-agent-v2",
      "name": "Code Agent v2",
      "description": "Advanced code generation agent",
      "owner": "ml-team",
      "tags": {"team": "agent", "version": "v2"},
      "created_at": "2026-03-01T00:00:00",
      "updated_at": "2026-03-20T00:00:00"
    }
  ]
}
```

### GET /projects/{project_id}

Get a single project.

### POST /projects

Create a project.

**Request body:**
```json
{
  "name": "My Project",
  "description": "Project description",
  "owner": "team",
  "tags": {"environment": "production"}
}
```

---

## 2. Experiments

### GET /experiments

List experiments.

**Query parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `project_id` | string | Filter by project |
| `status` | string | Filter by status (`running`/`completed`/`failed`/`cancelled`) |
| `scaffold` | string | Filter by scaffold |
| `algorithm` | string | Filter by algorithm |
| `sort_by` | string | Sort field (`created_at`/`name`/`mean_reward`/`pass_rate`/`total_tokens`) |
| `sort_order` | string | Sort direction (`asc`/`desc`) |
| `page` | int | Page number |
| `page_size` | int | Items per page |

**Response:** `PaginatedResponse` with `Experiment[]`

### GET /experiments/{experiment_id}

Get a single experiment.

**Response:**
```json
{
  "id": "demo_qwen72b_swebench",
  "name": "GRPO Qwen72B SWE-bench",
  "project_id": "proj-swebench",
  "status": "completed",
  "config": {
    "algorithm": "GRPO",
    "scaffolds": ["claude_code", "pi_code"],
    "max_iterations": 20
  },
  "metrics": {
    "mean_reward": 0.42,
    "pass_rate": 0.35,
    "total_tokens": 2500000,
    "total_trajectories": 1000
  },
  "created_at": "2026-03-01T00:00:00",
  "updated_at": "2026-03-20T00:00:00"
}
```

### GET /experiments/{experiment_id}/iterations

List iterations for an experiment.

**Query parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `sort_by` | string | Sort field (`iteration_num`/`mean_reward`/`pass_rate`) |
| `sort_order` | string | Sort direction (`asc`/`desc`) |
| `page` | int | Page number |
| `page_size` | int | Items per page |

### GET /experiments/{experiment_id}/iterations/{iteration_num}/trajectories

List trajectories for a specific iteration.

**Query parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `scaffold` | string | Filter by scaffold |
| `outcome` | string | Filter by outcome (comma-separated for multiple) |
| `task_id` | string | Filter by task |
| `sort_by` | string | Sort field (`reward`/`total_turns`/`duration_ms`/`created_at`) |
| `sort_order` | string | Sort direction (`asc`/`desc`) |
| `page` | int | Page number |
| `page_size` | int | Items per page |

---

## 3. Iterations

### GET /iterations

List iterations.

**Query parameters:**
- `experiment_id`: Experiment ID (required)

### GET /iterations/{iteration_id}/metrics

Get metrics for a single iteration.

---

## 4. Analysis

All endpoints are under `/experiments/{experiment_id}/analysis/`.

All endpoints support the [Analysis Common Parameters](#analysis-common-parameters).

### GET .../languages

Get all `task_language` values (for dropdown filters).

**Response:**
```json
{
  "languages": ["python", "javascript", "typescript", "java"]
}
```

### GET .../tool-schemas

Get all `tool_schema` values (for dropdown filters).

**Response:**
```json
{
  "tool_schemas": ["default", "extended", "minimal"]
}
```

### GET .../scaffold

Scaffold dimension statistics.

**Response:**
```json
{
  "items": [
    {
      "scaffold": "claude_code",
      "count": 500,
      "pass_rate": 0.42,
      "max_turns_passed": 15,
      "avg_turns_passed": 7.2,
      "max_duration_passed_ms": 120000,
      "avg_duration_passed_ms": 45000
    }
  ]
}
```

### GET .../pass-rate-diff

Pass rate change analysis (compare two iterations).

**Query parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `step1` | int | Baseline iteration |
| `step2` | int | Comparison iteration |

**Response:**
```json
{
  "step1": 1,
  "step2": 10,
  "improved": [
    {"task_id": "task-001", "step1_rate": 0.2, "step2_rate": 0.8, "improvement": 0.6}
  ],
  "declined": [
    {"task_id": "task-002", "step1_rate": 0.9, "step2_rate": 0.3, "decline": -0.6}
  ],
  "unchanged": [
    {"task_id": "task-003", "step1_rate": 0.5, "step2_rate": 0.5, "change": 0.0}
  ]
}
```

### GET .../cross-analysis

Cross-dimensional analysis (e.g. Scaffold × Language).

**Query parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `dim1` | string | First dimension (`scaffold`/`language`/`tool_schema`) |
| `dim2` | string | Second dimension (`scaffold`/`language`/`tool_schema`) |

**Response:**
```json
{
  "dimensions": ["scaffold", "language"],
  "matrix": {
    "claude_code": {
      "python": {"pass_rate": 0.45, "count": 200},
      "javascript": {"pass_rate": 0.38, "count": 150}
    }
  }
}
```

### GET .../task-difficulty

Task difficulty analysis.

**Response:**
```json
{
  "items": [
    {
      "task_id": "task-001",
      "language": "python",
      "difficulty": "medium",
      "total_rollouts": 20,
      "pass_rate": 0.25,
      "avg_reward": 0.42
    }
  ],
  "summary": {
    "easy": {"count": 50, "avg_pass_rate": 0.85},
    "medium": {"count": 80, "avg_pass_rate": 0.45},
    "hard": {"count": 30, "avg_pass_rate": 0.15}
  }
}
```

### GET .../repetition-detection

Detect repetitive behavior patterns in trajectories.

**Response:**
```json
{
  "items": [
    {
      "trajectory_id": "traj-001",
      "repeat_type": "tool_call",
      "repeat_count": 5,
      "affected_turns": [3, 4, 5, 6, 7],
      "pattern": "bash->bash->bash",
      "severity": "warning"
    }
  ]
}
```

### GET .../extreme-cases

Find extreme trajectories (high reward / low turns, etc.).

**Query parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `case_type` | string | `high_reward_low_turns` / `low_reward_high_turns` |
| `threshold` | float | Threshold value |

**Response:**
```json
{
  "items": [
    {
      "trajectory_id": "traj-001",
      "reward": 0.95,
      "total_turns": 3,
      "task_id": "task-001",
      "case_type": "high_reward_low_turns",
      "score": 0.32
    }
  ]
}
```

---

## 5. PromQL Query

### POST /query

PromQL-style range query over training metrics.

**Request body:**
```json
{
  "query": "experiment_pass_rate{experiment_id=\"demo_qwen72b_swebench\"}",
  "start": "2026-03-01T00:00:00",
  "end": "2026-03-02T00:00:00",
  "step": "1h"
}
```

**Aggregation syntax:**
```json
{
  "query": "sum(experiment_pass_rate{experiment_id=\"demo_qwen72b_swebench\"}) by (scaffold)"
}
```

Supported aggregation functions: `sum`, `avg`, `max`, `min`, `count`

**Response:**
```json
{
  "status": "success",
  "data": {
    "resultType": "matrix",
    "result": [
      {
        "metric": {
          "__name__": "experiment_pass_rate",
          "experiment_id": "demo_qwen72b_swebench",
          "x_axis_type": "iteration"
        },
        "values": [[1, "0.35"], [2, "0.38"], [3, "0.42"]]
      }
    ]
  }
}
```

### POST /query/rank

PromQL rank query (TopK / BottomK).

**Request body:**
```json
{
  "query": "experiment_task_pass_rate{experiment_id=\"demo_qwen72b_swebench\"} by (task_id)",
  "sort_by": "value",
  "sort_order": "asc",
  "limit": 10
}
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | — | PromQL query (supports `by (label)`) |
| `sort_by` | string | `value` | Sort field |
| `sort_order` | string | `asc` | `asc` = BottomK, `desc` = TopK |
| `limit` | int | 10 | Number of results |

**Supported metrics for rank:**

| Metric | Description |
|--------|-------------|
| `experiment_task_pass_rate` | Per-task pass rate |
| `experiment_task_mean_reward` | Per-task mean reward |

**Response:**
```json
{
  "items": [
    {
      "labels": {"task_id": "task-042"},
      "value": 0.05,
      "rank": 1
    }
  ]
}
```

### GET /query/metrics

List all available metrics.

**Response:**
```json
[
  {
    "name": "experiment_pass_rate",
    "labels": ["experiment_id", "scaffold", "language", "tool_schema"],
    "type": "gauge"
  }
]
```

### GET /query/metadata

Get metric metadata (type, unit, help text).

---

## 6. TraceQL (in-process)

An in-process TraceQL engine backed by the mock data store. Used for trajectory span analysis in development/demo mode.

### POST /traceql/query

Execute a TraceQL query.

**Request:**
```json
{
  "query": "{ resource.experiment_id = \"exp-001\" && resource.outcome = \"success\" }",
  "experiment_id": "exp-001"
}
```

**Supported syntax:**
```bash
# All tool calls
{ span.tool_name != nil }

# Count by tool
{ span.tool_name != nil } | count() by (span.tool_name)

# Tool success rate
{ span.tool_succeeded = true } | rate() by (span.tool_name)

# Tool latency
{ span.tool_name != nil } | avg(span:duration) by (span.tool_name)
```

### GET /traceql/examples

Get example TraceQL queries grouped by category.

### GET /traceql/syntax

Get TraceQL syntax documentation (supported selectors, aggregations, grouping).

### GET /traceql/health

Check TraceQL engine health.

---

## 7. Trace Proxy

Proxies TraceQL queries to the external gateway (Java/ClickHouse) for production trajectory data.

### POST /trace/query

**Request:**
```json
{
  "query": "{ id=\"django__django-14608__abc001\" } | select(id, experiment_id, trajectory)",
  "page_size": 1000,
  "page_num": 1
}
```

The proxy automatically adds `scope: "rl"` before forwarding to the gateway. Requires `TRACEQL_BASE_URL` environment variable to be set.

---

## 8. Traces

OpenTelemetry-based agent trace search.

### GET /traces/search

Search traces.

**Query parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `start_time` | int | Start time (ms timestamp) |
| `end_time` | int | End time (ms timestamp) |
| `service_name` | string | Service name filter |
| `operation_name` | string | Operation name filter |
| `status` | string | Status filter (`ok`/`error`) |
| `provider` | string | Trace provider (`internal`) |
| `limit` | int | Max results (max 1000) |

**Response:**
```json
[
  {
    "trace_id": "abc123",
    "scaffold": "claude_code",
    "duration_ms": 5000,
    "span_count": 12,
    "status": "ok",
    "has_rl_context": true,
    "start_time": "2026-03-01T01:00:00",
    "service_name": "agent-service-1"
  }
]
```

### GET /traces/{trace_id}

Get trace detail with span tree.

### GET /traces/{trace_id}/url

Get external trace viewer URL.

---

## 9. Stats

### POST /stats/tool-analysis

Aggregate tool analysis (replaces multiple TraceQL queries).

**Request body:**
```json
{
  "experiment_id": "demo_qwen72b_swebench",
  "scaffold": "claude_code",
  "language": "python",
  "tool_schema": "default",
  "split_by": "scaffold"
}
```

**Response:**
```json
{
  "items": [
    {
      "tool": "bash",
      "scaffold": "claude_code",
      "call_count": 500,
      "success_rate": 0.92,
      "avg_ms": 3200,
      "p50_ms": 2800,
      "p99_ms": 15000,
      "trajectory_count": 100,
      "error_task_rate": 0.15,
      "success_task_rate": 0.85
    }
  ]
}
```

---

## 10. Annotations

### GET /annotations

List root-cause annotations.

**Query parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `experiment_id` | string | Filter by experiment |
| `trajectory_id` | string | Filter by trajectory |
| `source` | string | Source filter (`auto`/`manual`) |
| `pattern_type` | string | Pattern type filter |
| `severity` | string | Severity filter |

### POST /annotations

Create a root-cause annotation.

**Request body:**
```json
{
  "trajectory_id": "traj-001",
  "experiment_id": "demo_qwen72b_swebench",
  "pattern_type": "action_loop",
  "description": "Agent stuck in bash->bash loop at turns 5-8",
  "affected_turns": [5, 6, 7, 8],
  "severity": "warning"
}
```

**Supported `pattern_type` values:**
`action_loop` | `tool_error` | `timeout` | `token_explosion` | `ineffective_action` | `early_abandon` | `repeat_error`

---

## 11. Alerts

### GET /alerts/rules

List alert rules.

### POST /alerts/rules

Create an alert rule.

**Request body:**
```json
{
  "name": "Pass Rate Drop",
  "expression": "pass_rate < threshold",
  "threshold": 0.3,
  "severity": "critical",
  "for_duration": "5m",
  "notification_channels": ["email"]
}
```

### POST /alerts/rules/{rule_id}/silence

Silence an alert rule.

**Query parameters:**
- `duration`: Silence duration (e.g. `"1h"`)

### GET /alerts/active

List active alerts.

---

## API Summary

| Module | Endpoints | Path Prefix | Status |
|--------|-----------|-------------|--------|
| Projects | 3 | `/projects` | Implemented |
| Experiments | 4 | `/experiments` | Implemented |
| Iterations | 2 | `/iterations` | Implemented |
| Analysis | 8 | `/experiments/{id}/analysis` | Implemented |
| PromQL Query | 4 | `/query` | Implemented |
| TraceQL (in-process) | 4 | `/traceql` | Implemented |
| Trace Proxy | 1 | `/trace` | Implemented |
| Traces | 3 | `/traces` | Implemented |
| Stats | 1 | `/stats` | Implemented |
| Annotations | 2 | `/annotations` | Implemented |
| Alerts | 4 | `/alerts` | Implemented |
| Agent Services | 3 | `/agent-services` | Implemented |
| Metrics | 3 | `/metrics` | Implemented |
| Tasks | — | `/tasks` | Under construction |
