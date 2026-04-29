# Observability Gateway

An open-source **observability query gateway** backed by ClickHouse. Currently supports **Trace queries** via TraceQL, with **Metric queries** (PromQL) planned.

[English](README.md) | [中文](README_CN.md)

---

## Features

- **TraceQL Query Language** — Tempo/LogQL/PromQL-compatible syntax for querying trace and trajectory data
- **ClickHouse Backend** — Optimized SQL generation for ClickHouse's columnar storage
- **Multi-scope Support** — Query OTLP traces (`scope=otlp`) and RL trajectories (`scope=rl`) through the same API
- **View Definitions** — Pre-define named queries in YAML, reference them with `view(name)` syntax
- **Prometheus-compatible Stat API** — Aggregation results in PromQL-like `{metric, values}` format
- **Extensible Architecture** — Pluggable `FieldMapper` and query engine modules; ready for PromQL metric queries
- **ANTLR4-based Grammar** — Easy to add new functions and operators

## Quick Start

### Prerequisites

- Java 21+
- Maven 3.6+
- ClickHouse (or use the bundled docker-compose)

### Using Docker Compose

```bash
# Start ClickHouse with sample data
docker-compose up -d

# Start the gateway
mvn -pl gateway-server spring-boot:run
```

### Manual Setup

1. Set up ClickHouse and create the schema:

```bash
clickhouse-client < gateway-server/src/main/resources/sql/schema.sql
```

2. Configure the connection:

```bash
export CLICKHOUSE_URL=jdbc:clickhouse://localhost:8123/default
export CLICKHOUSE_USERNAME=default
export CLICKHOUSE_PASSWORD=
```

3. Build and run:

```bash
mvn clean package -DskipTests
mvn -pl gateway-server spring-boot:run
```

The gateway starts on `http://localhost:8080`.

## API

### Trace Query

```bash
curl -X POST http://localhost:8080/api/v1/trace/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{service_name = '\''my-service'\'' and duration > 1000}",
    "start": 1700000000,
    "end": 1700003600,
    "pageSize": 100
  }'
```

### Stat Query (Aggregation)

```bash
curl -X POST http://localhost:8080/api/v1/trace/stat/query \
  -H "Content-Type: application/json" \
  -d '{
    "querys": [{
      "alias": "svc_latency",
      "query": "{} | select(service_name, avg(duration) as avg_dur, count() as cnt) by (service_name)"
    }]
  }'
```

### TraceQL Examples

```
# Simple span query
{service_name = 'my-service' and duration > 1000}

# Trace query (find traces spanning multiple services)
{service_name = 'frontend'} && {service_name = 'backend'} | query_by(trace_id)

# Aggregation with aliases
{} | select(service_name, p99(duration) as p99_dur, count() as cnt) by (service_name)

# AI trace analysis
{}|(attributes.gen_ai.span_kind_name != null)
  | query_by(trace_id)
  | select(
      trace_id as traceId,
      first(span_name) as rootName,
      sum(if(attributes.gen_ai.span_kind_name = 'LLM',
        attributes.gen_ai.usage.input_tokens, 0)) as totalInputTokens,
      count() as spanNum
    ) by (trace_id)

# RL trajectory query (scope=rl)
{experiment_id = 'my-experiment' and reward > 0.8}
  | select(model, avg(reward), count()) by (model)

# Named view
view(my_view) | (avg_dur > 1000)
```

## Documentation

- [TraceQL Syntax Reference (English)](docs/traceql-syntax-en.md)
- [TraceQL 语法文档 (中文)](docs/traceql-syntax.md)

## Project Structure

```
gateway-parent/
├── gateway-core/              # Core layer: FieldMapper interface, query executor, shared abstractions
├── gateway-traceql/           # TraceQL engine: ANTLR4 grammar, AST, SQL generator
│   ├── src/main/antlr4/       # TraceQL.g4 grammar file
│   └── src/main/java/         # Parser, AST nodes, ClickHouse SQL generator
├── gateway-promql/            # (Planned) PromQL engine for metric queries
├── gateway-server/            # Spring Boot REST API server
│   ├── src/main/java/         # Controllers, services, repositories
│   └── src/main/resources/
│       ├── application.yml    # Configuration
│       └── sql/               # ClickHouse DDL schemas
├── docker/                    # Docker init scripts (schema + sample data)
└── docs/                      # Documentation
```

## Configuration

```yaml
spring:
  datasource:
    url: ${CLICKHOUSE_URL:jdbc:clickhouse://localhost:8123/default}
    username: ${CLICKHOUSE_USERNAME:default}
    password: ${CLICKHOUSE_PASSWORD:}

clickhouse:
  tables:
    otlp: otel_traces        # OTLP trace table
    rl: rl_traces             # RL trajectory materialized view

traceql:
  views:                      # Named view definitions
    my_view: "{service_name = 'x'} | select(avg(duration) as avg_dur) by (service_name)"
```

## License

[Apache License 2.0](LICENSE)
