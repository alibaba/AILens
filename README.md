# AI-Lens

**AI-Lens** is an open-source observability platform for AI agent training and production systems. It provides end-to-end visibility into reinforcement learning (RL) training pipelines — from experiment management and trajectory analysis to real-time service monitoring and trace exploration.

[English](README.md) | [中文](README_CN.md)

---

## Features

### Available Now — RL Training Observability

**Experiments**
- **Experiment List** — All experiments at a glance with key metrics (pass rate, reward, token usage, iteration count)
- **Experiment Overview** — Convergence curves, reward distributions, and efficiency metrics for a single experiment
- **Task Analysis** — Per-language / per-category pass rates; identify weak tasks and training bottlenecks
- **Tool Analysis** — Tool call quality, error patterns, and action trends across the experiment
- **Trajectory Explorer** — Multi-dimensional filtering (Outcome, Iteration, Language, Reward, Turns, Task ID) with inline detail Drawer; reusable from Experiment, Task, and Dataset entry points
- **Trajectory View** — Turn-by-turn step-through replay of a single trajectory; inspect reasoning, tool calls, and observations to pinpoint failure root cause

**Datasets**
- **Dataset Dashboard** — Aggregate view of all datasets: total tasks, experiments, trajectories, and highest pass rate; click any row to jump to its Task Explorer
- **Task Explorer** — Cross-experiment task analysis scoped to a dataset or experiment; filter by Language and Pass Rate range; drill down into Trajectory Explorer per task

**Traces**
- **Trace Search** — OpenTelemetry-based agent trace query via TraceQL with Span Waterfall view

### Roadmap

- **Per-user Agent Observability** — Individual user session tracking and behavior analysis
- **Agent Service Metrics** — Runtime metrics by LLM / Tool / Skill layer

## Information Architecture

```
AILens
│
├── Training (RL Observability)
│   │
│   ├── Experiments
│   │   └── Experiment List                                              # All experiments with key metrics
│   │       └── Experiment Detail                                        # Deep-dive into a single experiment
│   │           ├── Experiment Overview                                  # Macro view of overall training performance
│   │           ├── Task Analysis                                        # Identify task-level trends and weak spots
│   │           │   └── Task Explorer (scoped to Experiment + Dataset)   # Inspect every task within the experiment
│   │           │       └── Trajectory Explorer (scoped to Experiment + Task)  # Compare multiple runs of the same task
│   │           │           └── Trajectory View                          # Step-by-step replay — pinpoint failure root cause
│   │           ├── Tool Analysis                                        # Evaluate tool call quality and bottlenecks
│   │           ├── ...
│   │           └── Trajectory Explorer (scoped to Experiment)           # Global view of trajectory quality and distribution
│   │               └── Trajectory View                                  # Step-by-step replay — pinpoint failure root cause
│   │
│   └── Datasets                                                         # Manage evaluation datasets, survey data assets
│       └── Dataset List                                                 # All datasets with key metrics
│           └── Task Explorer (scoped to Dataset)                        # All tasks under a dataset with core metrics
│               └── Task Detail                                          # Cross-experiment / cross-scaffold / cross-model analysis
│                   └── Trajectory Explorer (scoped to Task)             # All execution trajectories for a task
│                       └── Trajectory View                              # Step-by-step replay — pinpoint failure root cause
```

## Architecture

### Read Path (Query)

```
┌──────────────┐   REST/JSON   ┌─────────────────┐   TraceQL   ┌─────────────────┐
│   Frontend   │ ────────────▶ │    Backend       │ ──────────▶ │    Gateway      │
│  React + TS  │               │  Python FastAPI  │             │ Java/ClickHouse │
└──────────────┘               └─────────────────┘             └─────────────────┘
                                                                        │
                                                               ┌────────▼────────┐
                                                               │   ClickHouse    │
                                                               └─────────────────┘
```

### Write Path (Ingestion)

```
RL Training Trajectories:
  HarborSDK ──▶ OTel Collector (logs pipeline)   ──▶ otel_logs ──▶ rl_traces (MV)
                      │                                               ClickHouse
Agent Service Traces: │
  OTel SDK  ──▶ OTel Collector (traces pipeline) ──▶ otel_traces
                      └── single otelcol-contrib instance, ports 4317/4318
```

| Service | Tech | Port |
|---------|------|------|
| Frontend | React 19, TypeScript, Vite, Ant Design, ECharts | 3000 |
| Backend  | Python 3.11+, FastAPI, Pydantic v2, Prometheus | 8000 |
| Gateway  | Java 21, Spring Boot, ANTLR4, ClickHouse | 8080 |
| OTel Collector | otelcol-contrib (logs + traces pipelines) | 4317 (gRPC) / 4318 (HTTP) |

## Quick Start

### Option 1 — Docker Compose (recommended)

```bash
git clone https://github.com/alibaba/AILens.git
cd AILens/deploy
docker-compose up -d
```

Services start at:

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Backend Swagger | http://localhost:8000/docs |
| Gateway | http://localhost:8080 |
| OTel Collector gRPC | localhost:4317 |
| OTel Collector HTTP | localhost:4318 |

**Sending data to the collector:**

- **Agent traces** — configure your OTel SDK to export to `http://localhost:4318` (HTTP) or `localhost:4317` (gRPC)
- **RL training trajectories** — configure HarborSDK to export logs to `http://localhost:4318`; data flows into `otel_logs` and is automatically projected into the `rl_traces` view

### Option 2 — Local Development

**Prerequisites:** Python 3.11+, Node.js 20+, **Java 21+**, Maven 3.6+

> Note: Java 21 is required. If your system default is older, set `JAVA_HOME` explicitly (see gateway step below).

**1. Gateway**

```bash
# Build (required before first run)
cd gateway
JAVA_HOME=/path/to/jdk-21 mvn clean package -DskipTests -q

# Run — supply your ClickHouse connection via environment variables
JAVA_HOME=/path/to/jdk-21 \
  CLICKHOUSE_URL="jdbc:clickhouse://<host>:8123/default" \
  CLICKHOUSE_USERNAME="<user>" \
  CLICKHOUSE_PASSWORD="<password>" \
  $JAVA_HOME/bin/java -jar gateway-server/target/gateway-server-*.jar
```

**2. Backend** — must be run from the **monorepo root** (uses relative imports)

```bash
cd /path/to/AILens        # monorepo root, NOT the backend/ directory
pip3 install -r backend/requirements.txt

TRACEQL_BASE_URL=http://localhost:8080 \
  python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

**3. Frontend**

```bash
cd frontend
npm install
npm run dev
```

## Repository Structure

```
AILens/
├── backend/          # Python FastAPI backend (run from monorepo root)
│   ├── app/                  # Application package
│   │   ├── main.py           # Entry point
│   │   ├── config.py         # Configuration
│   │   ├── routers/          # API route handlers
│   │   ├── models/           # Pydantic schemas
│   │   ├── mock/             # Built-in mock data store
│   │   ├── metrics/          # Metrics extractors
│   │   ├── repositories/     # Data access layer
│   │   └── observability/    # Logging, metrics, tracing
│   └── tests/                # pytest test suite
├── frontend/         # React/TypeScript frontend
│   └── src/
│       ├── api/              # API client layer
│       ├── components/       # Reusable UI components
│       ├── pages/            # Page-level components
│       ├── stores/           # Zustand state management
│       └── queries/          # TanStack Query hooks
├── gateway/          # Java Spring Boot query gateway
│   ├── gateway-core/         # Core abstractions
│   ├── gateway-traceql/      # ANTLR4 TraceQL engine + ClickHouse SQL generator
│   └── gateway-server/       # REST API server
├── deploy/           # Docker Compose deployment
│   ├── docker-compose.yml
│   └── docker/clickhouse/    # ClickHouse schema + sample data
├── docs/             # Documentation
└── scripts/          # Development scripts
```

## Data Model

```
Project
 └── Experiment
      ├── Config (model / scaffold / algorithm / reward)
      └── Iteration
           └── Trajectory (one Agent run for one Task)
                └── Turn
                     └── Event (reasoning / action / observation)
```

## Mock Data

The backend ships with an in-memory mock store (Experiment / Iteration metadata) and the ClickHouse init scripts include 12 sample trajectories across 2 experiments and 2 datasets:

- **demo_qwen72b_swebench** — 8 trajectories (qwen-72b on SWE-bench Python tasks, 2 iterations)
- **demo_glm5_java** — 4 trajectories (glm-5 on SWE-bench Java tasks, 2 iterations)

Connect a real ClickHouse backend via the gateway when you have production data.

## Configuration

Copy `.env.example` to `.env` and update:

| Variable | Description | Default |
|----------|-------------|---------|
| `TRACEQL_BASE_URL` | Gateway endpoint | `http://localhost:8080` |
| `LOG_LEVEL` | Log verbosity | `INFO` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OpenTelemetry collector | `http://localhost:4317` |

See `.env.example` for the full list.

## Contributing

We welcome contributions! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

## License

[Apache License 2.0](LICENSE)
