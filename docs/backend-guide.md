# Backend Developer Guide

> AI Lens Backend — Python FastAPI

---

## 1. Tech Stack

| Technology | Version | Notes |
|-----------|---------|-------|
| Python | 3.11+ | Required |
| FastAPI | latest | Web framework |
| Pydantic | v2 (`>=2.0.0`) | Data validation |
| Uvicorn | latest | ASGI server |
| OpenTelemetry | `>=1.20.0` | Distributed tracing |
| Prometheus Client | `>=0.17.0` | Metrics export |
| pytest | `>=7.0.0` | Test framework |
| httpx | `>=0.24.0` | Async HTTP client (also used by TestClient) |

---

## 2. Directory Structure

```
backend/
├── requirements.txt
├── app/
│   ├── __init__.py
│   ├── main.py               # FastAPI entry point, middleware + router registration
│   ├── config.py             # Configuration constants
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py        # Pydantic v2 data models
│   ├── mock/
│   │   ├── __init__.py
│   │   └── store.py          # In-memory mock data store
│   ├── metrics/
│   │   ├── registry.py       # METRIC_REGISTRY — all PromQL metric definitions
│   │   └── extractors/       # Per-metric extractor functions
│   ├── repositories/
│   │   ├── base.py           # Repository interfaces
│   │   ├── dependencies.py   # FastAPI dependency injection
│   │   └── mock/             # Mock repository implementations
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── projects.py       # /api/v1/projects
│   │   ├── experiments.py    # /api/v1/experiments
│   │   ├── iterations.py     # /api/v1/iterations
│   │   ├── analysis/         # /api/v1/experiments/{id}/analysis/*
│   │   │   ├── __init__.py   # Aggregates sub-routers
│   │   │   ├── languages.py
│   │   │   ├── scaffold.py
│   │   │   ├── tool_schemas.py
│   │   │   ├── pass_rate_diff.py
│   │   │   ├── cross_analysis.py
│   │   │   ├── task_difficulty.py
│   │   │   ├── repetition.py
│   │   │   └── extreme_cases.py
│   │   ├── query.py          # /api/v1/query (PromQL-style)
│   │   ├── traceql.py        # /api/v1/traceql (in-process TraceQL engine)
│   │   ├── trace_query.py    # /api/v1/trace (proxy to gateway)
│   │   ├── stats.py          # /api/v1/stats
│   │   ├── agent_services.py # /api/v1/agent-services
│   │   ├── traces.py         # /api/v1/traces
│   │   ├── metrics.py        # /api/v1/metrics
│   │   ├── tasks.py          # /api/v1/tasks (under construction)
│   │   ├── annotations.py    # /api/v1/annotations
│   │   ├── alerts.py         # /api/v1/alerts
│   │   └── observability.py  # /health, /ready, /metrics (Prometheus)
│   ├── tracing/
│   │   ├── providers/        # Pluggable trace providers
│   │   └── traceql/
│   │       └── engine.py     # In-process TraceQL engine
│   └── observability/
│       ├── logging.py        # Structured logging (structlog)
│       ├── metrics/          # Application metrics
│       ├── telemetry.py      # OpenTelemetry setup
│       └── middleware.py     # Access log + error handling middleware
└── tests/
    ├── conftest.py
    ├── test_api_experiments.py
    ├── test_api_projects.py
    ├── test_analysis_api.py
    ├── test_query_api.py
    ├── test_traceql_api.py
    └── ...                   # Full pytest suite
```

---

## 3. Startup

**Important:** The backend must be started from the **monorepo root**, not from `backend/`:

```bash
cd /path/to/AILens    # monorepo root
pip3 install -r backend/requirements.txt

TRACEQL_BASE_URL=http://localhost:8080 \
  python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

The startup sequence:
1. Load `.env` via `python-dotenv`
2. Initialize logging (structlog, JSON format by default)
3. Set up OpenTelemetry tracing
4. Register CORS + observability middleware
5. Register all routers under `/api/v1`
6. Start GC metrics collector (background thread)

---

## 4. Router Conventions

### 4.1 Router Definition

```python
from fastapi import APIRouter

router = APIRouter(
    prefix="/experiments",
    tags=["experiments"],
)
```

### 4.2 Router Registration

All routers are registered in `main.py` under `/api/v1`:

```python
API_V1_PREFIX = "/api/v1"
app.include_router(experiments.router, prefix=API_V1_PREFIX)
```

### 4.3 Endpoint Naming

| Operation | HTTP | Path | Function |
|-----------|------|------|----------|
| List | GET | `/resources` | `list_resources()` |
| Detail | GET | `/resources/{id}` | `get_resource()` |
| Create | POST | `/resources` | `create_resource()` |
| Sub-resource list | GET | `/resources/{id}/sub` | `list_sub_resources()` |
| Aggregation | GET | `/resources/{id}/analysis/xxx` | `get_xxx()` |

### 4.4 Pagination Pattern

```python
@router.get("")
def list_experiments(
    page: int = 1,
    page_size: int = 20,
):
    items = repo.get_all()
    total = len(items)
    start = (page - 1) * page_size
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items[start : start + page_size],
    }
```

### 4.5 404 Handling

```python
from fastapi import HTTPException

experiment = repo.get_experiment(experiment_id)
if not experiment:
    raise HTTPException(status_code=404, detail="Experiment not found")
```

---

## 5. Schema Conventions (Pydantic v2)

Models are defined in `app/models/schemas.py`:

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Experiment(BaseModel):
    id: str
    project_id: str
    name: str
    status: str  # running / completed / failed / cancelled
    config: ExperimentConfig
    created_at: datetime
    updated_at: Optional[datetime] = None
```

Key schema groups:

```
Pagination   → PaginatedResponse
Projects     → Project, CreateProject
Experiments  → Experiment, ExperimentConfig
Iterations   → Iteration, IterationMetrics
Trajectories → Trajectory
Traces       → Span, TraceSearchResult, TraceDetail
Services     → AgentService
Metrics      → MetricSeries, MetricDataPoint
Annotations  → Annotation, CreateAnnotation
Alerts       → AlertRule, ActiveAlert
```

---

## 6. PromQL Metrics System

Metrics are defined in `app/metrics/registry.py` as `METRIC_REGISTRY` (an `OrderedDict`). Each entry maps a metric name to:

```python
{
    "type": "gauge",          # gauge / counter / histogram
    "unit": "",
    "description": "...",
    "labels": ["experiment_id", "scaffold", ...],
    "extractor": some_function,  # callable that returns List[MetricSeries]
}
```

The `/api/v1/query` endpoint reads `METRIC_REGISTRY` to look up extractors and execute queries. Supported PromQL syntax:

```
# Basic query
experiment_pass_rate{experiment_id="exp-001"}

# Aggregation
sum(experiment_pass_rate{experiment_id="exp-001"}) by (scaffold)
avg(experiment_mean_reward{experiment_id="exp-001"}) by (language)
```

---

## 7. Mock Data

The backend ships with an in-memory mock store (`app/mock/store.py`) that provides experiment/iteration metadata for development without a real ClickHouse instance.

For trajectory data, ClickHouse init scripts in `deploy/docker/clickhouse/` provide 12 sample trajectories:

- `demo_qwen72b_swebench` — 8 trajectories (2 iterations)
- `demo_glm5_java` — 4 trajectories (2 iterations)

In production, connect a real ClickHouse backend via the gateway by setting `TRACEQL_BASE_URL`.

---

## 8. Testing

```bash
# Run from monorepo root
cd /path/to/AILens
python3 -m pytest backend/tests/ -v

# Specific file
python3 -m pytest backend/tests/test_api_experiments.py -v

# With coverage
python3 -m pytest backend/tests/ --cov=backend/app --cov-report=term-missing
```

Test client setup:

```python
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_list_experiments():
    response = client.get("/api/v1/experiments")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
```

---

## 9. Error Handling

Standard HTTP exceptions:

```python
# 404 — resource not found
raise HTTPException(status_code=404, detail="Experiment not found")

# 422 — validation error (automatic from Pydantic)

# 501 — not implemented
raise HTTPException(status_code=501, detail="Feature under construction")
```

Global middleware (`observability/middleware.py`):
- `AccessLogMiddleware` — structured access logging (excludes `/health`, `/ready`, `/metrics`)
- `ErrorHandlingMiddleware` — catches unhandled exceptions, returns JSON error response

---

## 10. Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TRACEQL_BASE_URL` | `""` | Gateway URL for TraceQL proxy |
| `TRACEQL_AUTH_KEY` | `""` | Optional auth key for gateway |
| `LOG_LEVEL` | `INFO` | Logging level |
| `LOG_FORMAT` | `json` | Log format (`json` or `text`) |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | — | OpenTelemetry collector endpoint |
| `OTEL_SERVICE_NAME` | `ailens-api` | Service name for traces |
| `ENVIRONMENT` | `development` | Deployment environment |

Copy `.env.example` to `.env` and customize before starting.

---

## 11. Development Checklist

- [ ] Backend started from monorepo root (not from `backend/`)
- [ ] New router registered in `main.py`
- [ ] New schemas defined in `models/schemas.py` using Pydantic v2 syntax
- [ ] Pagination returns `{total, page, page_size, items}` shape
- [ ] 404 handling in place for all resource lookups
- [ ] New endpoint has a pytest test
- [ ] `python3 -m pytest backend/tests/ -v` passes
