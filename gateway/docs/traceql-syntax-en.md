# TraceQL Syntax Reference

TraceQL is a query language for the Trace domain, inspired by [Grafana Tempo TraceQL](https://grafana.com/docs/tempo/latest/traceql/), LogQL, and PromQL. It is designed for extensibility and ease of use.

## SpanSet

A SpanSet is the fundamental building block of TraceQL, representing a set of spans matching given conditions. Three equivalent syntaxes are supported:

### PromQL Style

```
{<field> [=|!=] <string>, <field> [=|!=] <string>, ...}
```

Comma-separated conditions are combined with AND:

```
{service_name = 'my-service', status_code = 'OK'}
```

### LogQL Style

```
{} | <field> <op> <value> [and|or] ...
```

Uses `|` after an empty SpanSet to add filter expressions (AND relationship between `|` segments):

```
{} | (service_name = 'my-service' and duration > 1000)
{} | ((name = 'getUserById' and host = '127.0.0.1') or name = 'getUserByType')
```

### Tempo Style (Recommended)

```
{<field> <op> <value> [and|or] ...}
```

Shorthand for LogQL style — place the filter expression directly inside `{}`:

```
{service_name = 'my-service' and duration > 1000}
{(name = 'getUserById' and host = '127.0.0.1') or name = 'getUserByType'}
```

### Value Types

| Type | Examples |
|------|----------|
| Single-quoted string | `'value'` |
| Double-quoted string | `"value"` |
| Number (integer/decimal) | `100`, `3.14`, `-5` |
| Null | `null` |
| Wildcard | `'com.test.*'` |

### Comparison Operators

`=`, `!=`, `>`, `>=`, `<`, `<=`

### Null Checks

```
{attributes.gen_ai.span_kind_name != null}   -- field is not empty
{resources.service.name = null}              -- field is empty
```

For Map-type attributes (`attributes.*` / `resources.*`), null checks are mapped to empty-string checks.

### Wildcard Matching

When a string value contains `*`, it is automatically converted to pattern matching:

```
{service_name = 'com.test.*'}     -- prefix match
{service_name = '*Service'}       -- suffix match
{service_name = '*test*'}         -- contains match
{service_name != 'com.test.*'}    -- exclusion match
```

## SpanSet Operators

```
<spanset> <operator> <spanset>
```

Binary operators between SpanSets express relationships between spans within a complete trace:

| Operator | Meaning | Status |
|----------|---------|--------|
| `&&` | Both span types exist in the trace; returns union | Implemented |
| `\|\|` | At least one span type exists; returns union | Implemented |
| `=>` | spansetA is a direct parent of spansetB | Not yet implemented |
| `->` | spansetA is an indirect parent of spansetB | Not yet implemented |

Example:

```
{service_name = 'frontend'} && {service_name = 'backend'} | query_by(trace_id)
{service_name = 'a'} || {service_name = 'b'} | query_by(trace_id)
```

## Pipeline Extensions

Use `|` to chain extension operations.

### Filter Pipeline

Append filter conditions after a SpanSet:

```
{} | (service_name = 'my-service' and duration > 100)
```

### Query By

Query spans by a specified field, producing a new SpanSet. Used primarily for trace-level and session-level queries:

```
{service_name = 'my-service'} | query_by(trace_id)
```

Returns all spans belonging to traces that contain a span matching `service_name = 'my-service'`.

### Select By

Select specific fields or aggregate results grouped by specified fields:

```
select(<field | agg_field>, ...) [by (<field>, ...)]
```

#### Select Fields

```
{name = 'getUserById'} | select(duration, span_id, trace_id)
```

#### Aliases

All select items support `as` aliases (keywords like `count`, `max` can also be used as alias names):

```
{...} | select(trace_id as traceId, min(start_time) as startTime)
{...} | select(count() as count)
```

#### Aggregation

```
{name = 'getUserById'} | select(trace_id, avg(duration), count()) by (trace_id)
```

Supported aggregate functions:

| Function | Description | Example |
|----------|-------------|---------|
| `count()` | Count rows | `count() as num` |
| `count_distinct(field)` | Count distinct values | `count_distinct(trace_id)` |
| `max(expr)` | Maximum value | `max(duration)` |
| `min(expr)` | Minimum value | `min(start_time)` |
| `avg(expr)` | Average value | `avg(duration)` |
| `sum(expr)` | Sum | `sum(duration)` |
| `p99(expr)` | 99th percentile | `p99(duration)` |
| `p95(expr)` | 95th percentile | `p95(duration)` |
| `p50(expr)` | 50th percentile (median) | `p50(duration)` |
| `quantile(expr, double)` | Custom percentile | `quantile(duration, 0.99)` |
| `first(field)` | Value from the span with earliest start_time | `first(name) as rootName` |
| `first_ai(field)` | Value from the earliest AI span | `first_ai(status_code)` |

#### Arithmetic Expressions

Aggregate results can be combined with `+` `-` `*` `/`, with parentheses for grouping:

```
select(max(duration + start_time) - min(start_time) as duration)
select((max(duration) - min(duration)) / 1000 as range)
```

#### if() Conditional Expression

```
select(sum(if(attributes.gen_ai.span_kind_name = 'LLM', attributes.gen_ai.usage.input_tokens, 0)) as totalInputTokens)
```

#### General Function Calls

Aggregate results can be wrapped with any ClickHouse function:

```
select(round(avg(reward), 4) as mean_reward)
select(ceil(max(duration) / 1000) as max_sec)
```

The following function names are automatically mapped to ClickHouse equivalents:

| TraceQL | ClickHouse | Description |
|---------|-----------|-------------|
| `stddev(expr)` | `stddevPop(expr)` | Population standard deviation |
| `stddev_pop(expr)` | `stddevPop(expr)` | Population standard deviation |
| `stddev_samp(expr)` | `stddevSamp(expr)` | Sample standard deviation |
| `variance(expr)` | `varPop(expr)` | Population variance |
| `var_pop(expr)` | `varPop(expr)` | Population variance |
| `var_samp(expr)` | `varSamp(expr)` | Sample variance |
| `round(expr, n)` | `round(expr, n)` | Round to n decimal places |
| `ceil(expr)` | `ceil(expr)` | Round up |
| `floor(expr)` | `floor(expr)` | Round down |
| `median(expr)` | `median(expr)` | Median |

Unmapped function names are passed through to ClickHouse as-is.

Example — nested function composition:

```
select(
  round(avg(reward), 4) as mean_reward,
  stddev(reward) as reward_std,
  round(avg(if(verify_code = 'success', 1, 0)), 4) as pass_rate
) by (model)
```

## Field Mapping (OTLP Scope)

| TraceQL Field | ClickHouse Column |
|---------------|-------------------|
| `trace_id` | `TraceId` |
| `span_id` | `SpanId` |
| `parent_span_id` | `ParentSpanId` |
| `service_name` | `ServiceName` |
| `span_name` | `SpanName` |
| `span_kind` | `SpanKind` |
| `duration` | `Duration / 1000000` (ns → ms) |
| `start_time` | `toUnixTimestamp64Nano(Timestamp)` (DateTime64 → ns) |
| `status_code` | `StatusCode` |
| `status_message` | `StatusMessage` |
| `attributes.<key>` | `SpanAttributes['<key>']` |
| `resources.<key>` | `ResourceAttributes['<key>']` |

## Multi-level Nested Pipeline

Pipelines can alternate between Filter and Select stages. Each additional Select stage generates a nested subquery. This is useful for secondary filtering or re-aggregation of aggregated results.

```
<spanset> | select(...) by (...) | (filter_condition) | select(...) by (...)
```

Execution logic per layer:
1. **First Select**: Aggregates raw data → base SQL
2. **Intermediate Filter**: Filters previous results → `SELECT * FROM (prev) WHERE condition`
3. **Subsequent Select**: Re-aggregates filtered results → `SELECT ... FROM (prev) GROUP BY ...`

#### Example: Filter aggregated results

```
{service_name = 'my-service'}
  | select(span_name, count() as cnt, avg(duration) as avg_dur) by (span_name)
  | (cnt > 10)
  | select(span_name, avg_dur) by (span_name)
```

#### Example: Multi-level aggregation

```
{} | select(service_name, trace_id, max(duration) as max_dur) by (service_name, trace_id)
   | select(service_name, avg(max_dur) as avg_max_dur) by (service_name)
```

First aggregates by `(service_name, trace_id)` to get the max duration per trace, then averages across traces per service.

## View

Views allow you to pre-define commonly used TraceQL queries as named references. At query time, use `view(name)` to expand the definition and optionally append additional pipelines.

### Syntax

```
view(<name>) [| <pipeline>]*
```

### Defining Views

Views are configured in `application.yml`:

```yaml
traceql:
  views:
    svc_stats: "{service_name = 'my-service'} | select(span_name, avg(duration) as avg_dur, count() as cnt) by (span_name)"
```

### Usage Examples

#### Direct reference

```
view(svc_stats)
```

#### View + filter

```
view(svc_stats) | (avg_dur > 1000)
```

Expands to the view definition with an additional filter pipeline appended.

**Note**: Filter conditions after a view use the **aliased column names** from the view's SELECT (e.g., `avg_dur`), not the original field names.

#### View + re-aggregation

```
view(svc_stats) | (cnt > 5) | select(avg(avg_dur) as overall_avg) by ()
```

### Limitations

- Nested views are not supported (a view definition cannot reference another view)
- View names may only contain letters, digits, and underscores

## RL (Reinforcement Learning) Scope

RL training trajectory data is ingested via the otel-collector **log protocol** into the ClickHouse `otel_logs` table. A **materialized view** `rl_traces` extracts RL-specific fields automatically.

### Usage

Specify `scope: "rl"` in the request to query RL data:

```json
{
  "query": "{experiment_id = 'exp001' and model = 'qwen-72b'}",
  "scope": "rl"
}
```

### RL Fields

RL table fields are completely different from OTLP. All fields map directly to column names (no transformation):

| Field | Type | Description |
|-------|------|-------------|
| `id` | String | Trajectory ID |
| `start_time` | Int64 | Timestamp (milliseconds) |
| `experiment_id` | String | Experiment ID |
| `iteration` | Int32 | Iteration number |
| `task_id` | String | Task ID |
| `task_language` | String | Task language |
| `tool_schema` | String | Tool schema |
| `scaffold` | String | Scaffold type |
| `model` | String | Model name |
| `reward` | Float64 | Reward score |
| `duration_ms` | Int64 | Total duration (ms) |
| `total_tokens` | Int64 | Total tokens |
| `input_tokens` | Int64 | Input tokens |
| `output_tokens` | Int64 | Output tokens |
| `run_code` | String | Run result code |
| `run_duration_ms` | Int64 | Run duration (ms) |
| `sandbox_create_duration_ms` | Int64 | Sandbox creation time |
| `turns` | Int32 | Conversation turns |
| `verify_code` | String | Verification result code |
| `verify_duration_ms` | Int64 | Verification duration (ms) |

### RL Query Characteristics

- **No time filter**: RL queries do not automatically add time range conditions
- **Direct field mapping**: Field names are ClickHouse column names as-is, no OTLP transformations
- **Isolated scope**: `scope="rl"` routes to the `rl_traces` materialized view, fully isolated from OTLP data

### RL Query Examples

#### Query trajectories for an experiment

```
{experiment_id = 'exp001'}
```

#### Aggregate reward by model

```
{} | select(model, round(avg(reward), 4) as mean_reward, stddev(reward) as std, count() as num) by (model)
```

#### Filter high-reward trajectories

```
{experiment_id = 'exp001' and reward > 0.8}
  | select(model, task_id, reward, total_tokens, turns)
```

## Complete Query Examples

### Query a specific trace

```
{trace_id = '0b5fe68c17562750482575184e129d'}
```

### Span query

```
{service_name = 'my-service' and (duration > 3000 or status_code = 'ERROR')}
```

### Trace query (multi-SpanSet)

```
{service_name = 'frontend'} && {service_name = 'backend'} | query_by(trace_id)
  | select(trace_id, max(duration), count()) by (trace_id)
```

### AI trace analysis

```
{}|(attributes.gen_ai.span_kind_name != null and service_name = 'agent-server')
  | query_by(trace_id)
  | select(
      trace_id as traceId,
      first(span_name) as rootName,
      first_ai(status_code) as rootAiStatusCode,
      min(start_time) as startTime,
      max(duration + start_time) - min(start_time) as duration,
      sum(if(attributes.gen_ai.span_kind_name = 'LLM',
        attributes.gen_ai.usage.input_tokens, 0)) as totalInputTokens,
      sum(if(attributes.gen_ai.span_kind_name = 'LLM',
        attributes.gen_ai.usage.output_tokens, 0)) as totalOutputTokens,
      avg(duration) as avgDuration,
      quantile(duration, 0.99) as durationP99,
      count() as spanNum
    ) by (trace_id)
```

### AI session list query

```
{service_name = 'agent-server' and duration > 100}
  | select(
      attributes.gen_ai.conversation.id as sessionId,
      min(start_time) as startTime,
      max(start_time + duration) as endTime,
      count_distinct(trace_id) as traceNum,
      sum(if(attributes.gen_ai.span_kind_name = 'LLM', attributes.gen_ai.usage.input_tokens, 0)
        + if(attributes.gen_ai.span_kind_name = 'LLM', attributes.gen_ai.usage.output_tokens, 0)) as totalTokens
    ) by (attributes.gen_ai.conversation.id)
```
