# TraceQL 语法文档

TraceQL 是 Trace 域的查询语言，语法参考 [Grafana Tempo TraceQL](https://grafana.com/docs/tempo/latest/traceql/)、LogQL 和 PromQL，具备较高的可扩展性和低学习成本。

## SpanSet

SpanSet 是 TraceQL 的基本且必要结构，用于表示满足条件的 Span 集合。支持三种等价形式：

### PromQL 风格

```
{<field> [=|!=] <string>, <field> [=|!=] <string>, ...}
```

逗号分隔的条件之间是 AND 关系：

```
{service_name = 'buy2', status_code = 'OK'}
```

### LogQL 风格

```
{} | <field> <op> <value> [and|or] ...
```

使用 `|` 在空 SpanSet 后扩展逻辑表达式，`|` 前后是 AND 关系：

```
{} | (service_name = 'buy2' and duration > 1000)
{} | ((name = 'getUserById' and host = '127.0.0.1') or name = 'getUserByType')
```

### Tempo 风格（推荐）

```
{<field> <op> <value> [and|or] ...}
```

Tempo 风格是 LogQL 的简写，将 `|` 后的逻辑表达式直接放到 `{}` 内：

```
{service_name = 'buy2' and duration > 1000}
{(name = 'getUserById' and host = '127.0.0.1') or name = 'getUserByType'}
```

### 值类型

| 类型 | 示例 |
|------|------|
| 单引号字符串 | `'value'` |
| 双引号字符串 | `"value"` |
| 数字（整数/小数） | `100`, `3.14`, `-5` |
| null | `null` |
| 通配符 | `'com.test.*'` |

### 比较操作符

`=`, `!=`, `>`, `>=`, `<`, `<=`

### null 检查

```
{attributes.gen_ai.span_kind_name != null}   -- 字段不为空
{resources.service.name = null}              -- 字段为空
```

Map 类型属性（`attributes.*` / `resources.*`）的 null 检查映射为空字符串检查。

### 通配符匹配

字符串值中包含 `*` 时，自动转为模糊匹配：

```
{service_name = 'com.test.*'}     -- 前缀匹配
{service_name = '*Service'}       -- 后缀匹配
{service_name = '*test*'}         -- 包含匹配
{service_name != 'com.test.*'}    -- 排除匹配
```

## SpanSet 操作符

```
<spanset> <operator> <spanset>
```

SpanSet 之间支持以下二元运算符，表示 Span 在完整 Trace 链路中的关系：

| 操作符 | 含义 | 状态 |
|--------|------|------|
| `&&` | 两类 Span 在 Trace 中同时存在，返回并集 | 已实现 |
| `\|\|` | 两类 Span 在 Trace 中至少存在其一，返回并集 | 已实现 |
| `=>` | spansetA 是 spansetB 的直接父 Span | 暂未实现 |
| `->` | spansetA 是 spansetB 的间接父 Span | 暂未实现 |

示例：

```
{service_name = 'buy2'} && {service_name = 'carts2'} | query_by(trace_id)
{service_name = 'a'} || {service_name = 'b'} | query_by(trace_id)
```

## Pipeline 扩展语法

使用 `|` 符号拼接扩展功能。

### Filter 管道

在 SpanSet 之后追加过滤条件：

```
{} | (service_name = 'ads-ai' and duration > 100)
```

### Query By

按指定字段查询 Span，作为新的 SpanSet。主要用于 Trace 查询、Session 查询等场景：

```
{service_name = 'buy2'} | query_by(trace_id)
```

返回包含 `service_name = 'buy2'` 的 Span 所在 Trace 的所有 Span。

### Select By

筛选需要的字段，或按指定字段聚合返回统计结果：

```
select(<field | agg_field>, ...) [by (<field>, ...)]
```

#### 指定返回字段

```
{name = 'getUserById'} | select(duration, span_id, trace_id)
```

#### 别名

所有 select 项支持 `as` 别名：

```
{...} | select(trace_id as traceId, min(start_time) as startTime)
```

#### 聚合统计

```
{name = 'getUserById'} | select(trace_id, avg(duration), count()) by (trace_id)
```

支持的聚合函数：

| 函数 | 说明 | 示例 |
|------|------|------|
| `count()` | 计数 | `count() as num` |
| `count_distinct(field)` | 去重计数 | `count_distinct(trace_id)` |
| `max(expr)` | 最大值 | `max(duration)` |
| `min(expr)` | 最小值 | `min(start_time)` |
| `avg(expr)` | 平均值 | `avg(duration)` |
| `sum(expr)` | 求和 | `sum(duration)` |
| `p99(expr)` | P99 分位数 | `p99(duration)` |
| `p95(expr)` | P95 分位数 | `p95(duration)` |
| `p50(expr)` | P50 分位数 | `p50(duration)` |
| `quantile(expr, double)` | 自定义分位数 | `quantile(duration, 0.99)` |
| `first(field)` | start_time 最早的 span 的字段值 | `first(name) as rootName` |
| `first_ai(field)` | start_time 最早的 AI span 的字段值 | `first_ai(status_code)` |

#### 算术表达式

聚合结果之间支持四则运算 `+` `-` `*` `/`，支持括号：

```
select(max(duration + start_time) - min(start_time) as duration)
select((max(duration) - min(duration)) / 1000 as range)
```

#### if() 条件表达式

```
select(sum(if(attributes.gen_ai.span_kind_name = 'LLM', attributes.gen_ai.usage.input_tokens, 0)) as totalInputTokens)
```

#### 通用函数调用

聚合结果可以被通用函数包裹，支持任意 ClickHouse 函数：

```
select(round(avg(reward), 4) as mean_reward)
select(ceil(max(duration) / 1000) as max_sec)
```

以下函数名会自动映射为 ClickHouse 对应函数：

| TraceQL 写法 | ClickHouse 函数 | 说明 |
|-------------|----------------|------|
| `stddev(expr)` | `stddevPop(expr)` | 总体标准差 |
| `stddev_pop(expr)` | `stddevPop(expr)` | 总体标准差 |
| `stddev_samp(expr)` | `stddevSamp(expr)` | 样本标准差 |
| `variance(expr)` | `varPop(expr)` | 总体方差 |
| `var_pop(expr)` | `varPop(expr)` | 总体方差 |
| `var_samp(expr)` | `varSamp(expr)` | 样本方差 |
| `round(expr, n)` | `round(expr, n)` | 四舍五入到 n 位小数 |
| `ceil(expr)` | `ceil(expr)` | 向上取整 |
| `floor(expr)` | `floor(expr)` | 向下取整 |
| `median(expr)` | `median(expr)` | 中位数 |

未在映射表中的函数名会直接透传给 ClickHouse，如果 ClickHouse 不支持会返回错误。

示例：嵌套函数组合

```
select(
  round(avg(reward), 4) as mean_reward,
  stddev(reward) as reward_std,
  round(avg(if(verify_code = 'success', 1, 0)), 4) as pass_rate
) by (model)
```

## 字段映射

| TraceQL 字段 | ClickHouse 列 |
|-------------|--------------|
| `trace_id` | `TraceId` |
| `span_id` | `SpanId` |
| `parent_span_id` | `ParentSpanId` |
| `service_name` | `ServiceName` |
| `span_name` | `SpanName` |
| `span_kind` | `SpanKind` |
| `duration` | `Duration / 1000000`（纳秒 → 毫秒） |
| `start_time` | `toUnixTimestamp64Nano(Timestamp)`（DateTime64 → 纳秒） |
| `status_code` | `StatusCode` |
| `status_message` | `StatusMessage` |
| `attributes.<key>` | `SpanAttributes['<key>']` |
| `resources.<key>` | `ResourceAttributes['<key>']` |

### 多级嵌套 Pipeline

Pipeline 中可以交替出现 Filter 和 Select，每增加一层 Select 会生成子查询嵌套。适用于需要对聚合结果做二次过滤或再聚合的场景。

```
<spanset> | select(...) by (...) | (filter_condition) | select(...) by (...)
```

每一层的执行逻辑：
1. **第一层 Select**：基于原始数据聚合 → 生成基础 SQL
2. **中间层 Filter**：对上一层结果过滤 → `SELECT * FROM (上层 SQL) WHERE condition`
3. **后续层 Select**：对过滤后的结果再聚合 → `SELECT ... FROM (上层 SQL) GROUP BY ...`

#### 示例：对聚合结果二次过滤

```
{service_name = 'buy2'}
  | select(span_name, count() as cnt, avg(duration) as avg_dur) by (span_name)
  | (cnt > 10)
  | select(span_name, avg_dur) by (span_name)
```

生成的 SQL 结构：

```sql
SELECT span_name, avg_dur
FROM (
  SELECT * FROM (
    SELECT SpanName, count() AS cnt, avg(Duration / 1000000) AS avg_dur
    FROM otel_traces
    WHERE ... AND ServiceName = 'buy2'
    GROUP BY SpanName
  ) WHERE cnt > 10
) GROUP BY span_name
```

#### 示例：多级聚合

```
{} | select(service_name, trace_id, max(duration) as max_dur) by (service_name, trace_id)
   | select(service_name, avg(max_dur) as avg_max_dur) by (service_name)
```

先按 `(service_name, trace_id)` 聚合取每条 trace 的最大耗时，再按 `service_name` 求各服务的平均最大耗时。

## View 视图

View 允许将常用的 TraceQL 查询预定义为命名视图，查询时通过 `view(name)` 引用并可追加额外的 Pipeline。

### 语法

```
view(<name>) [| <pipeline>]*
```

### 视图定义

视图通过 `application.yml` 配置：

```yaml
traceql:
  views:
    buy2_host_stats: "{service_name = 'buy2'} | select(span_name, avg(duration) as avg_dur, count() as cnt) by (span_name)"
    rl_experiment_summary: "{} | select(experiment_id, model, avg(reward) as avg_reward, count() as num) by (experiment_id, model)"
```

### 使用示例

#### 直接引用视图

```
view(buy2_host_stats)
```

等价于执行视图定义中的完整查询。

#### 视图 + 过滤

```
view(buy2_host_stats) | (avg_dur > 1000)
```

展开后等价于：

```
{service_name = 'buy2'}
  | select(span_name, avg(duration) as avg_dur, count() as cnt) by (span_name)
  | (avg_dur > 1000)
```

视图的过滤条件中使用的字段名是视图 SELECT 中定义的**别名**（如 `avg_dur`），而非原始字段名。

#### 视图 + 再聚合

```
view(buy2_host_stats) | (cnt > 5) | select(avg(avg_dur) as overall_avg) by ()
```

利用多级嵌套能力，对视图结果做二次过滤和聚合。

### 限制

- 不支持嵌套视图（视图定义中不能引用另一个视图）
- 视图名称只能包含字母、数字和下划线

## RL（增强学习）场景

RL 场景的训练轨迹数据通过 otel-collector 的 **log 协议**写入 ClickHouse 的 `otel_logs` 表，通过**物化视图** `rl_traces` 提取 RL 专用字段。

### 使用方式

查询 RL 数据时，在请求中指定 `scope: "rl"`：

```json
{
  "start": 1700000000,
  "end": 1798761599,
  "query": "{experiment_id = 'exp001' and model = 'qwen-72b'}",
  "scope": "rl"
}
```

### RL 字段

RL 表的字段与 OTLP 完全不同，所有字段直接映射（无转换）：

| 字段 | 类型 | 说明 |
|------|------|------|
| `start_time` | DateTime64 | 记录时间 |
| `experiment_id` | String | 实验 ID |
| `iteration` | Int32 | 迭代轮次 |
| `task_id` | String | 任务 ID |
| `task_language` | String | 任务语言 |
| `tool_schema` | String | 工具 schema |
| `scaffold` | String | 脚手架类型 |
| `model` | String | 模型名称 |
| `reward` | Float64 | 奖励分数 |
| `duration_ms` | Int64 | 总耗时（毫秒） |
| `total_tokens` | Int64 | 总 token 数 |
| `input_tokens` | Int64 | 输入 token 数 |
| `output_tokens` | Int64 | 输出 token 数 |
| `run_code` | String | 运行结果代码 |
| `run_duration_ms` | Int64 | 运行耗时（毫秒） |
| `sandbox_create_duration_ms` | Int64 | 沙箱创建耗时 |
| `turns` | Int32 | 对话轮次 |
| `verify_code` | String | 验证结果代码 |
| `verify_duration_ms` | Int64 | 验证耗时（毫秒） |

### RL 查询特点

- **无时间过滤**：RL 查询不自动添加时间范围条件
- **字段直接映射**：字段名即 ClickHouse 列名，无 OTLP 式转换
- **独立 scope**：`scope="rl"` 路由到 `rl_traces` 物化视图，与 OTLP 数据完全隔离

### RL 查询示例

#### 查询指定实验的轨迹

```
{experiment_id = 'exp001'}
```

#### 按模型统计奖励

```
{} | select(model, avg(reward) as avg_reward, count() as num) by (model)
```

#### 高奖励轨迹筛选

```
{experiment_id = 'exp001' and reward > 0.8}
  | select(model, task_id, reward, total_tokens, turns)
```

#### 使用 View 简化 RL 查询

```yaml
# application.yml
traceql:
  views:
    rl_model_stats: "{} | select(model, avg(reward) as avg_reward, avg(total_tokens) as avg_tokens, count() as num) by (model)"
```

```
view(rl_model_stats) | (num > 100 and avg_reward > 0.5)
```

## 完整查询示例

### 查询指定 Trace

```
{trace_id = '0b5fe68c17562750482575184e129d'}
```

### SpanQuery

```
{service_name = 'buy2' and (duration > 3000 or status_code = 'ERROR')}
```

### TraceQuery（多 SpanSet）

```
{service_name = 'buy2'} && {service_name = 'carts2'} | query_by(trace_id)
  | select(trace_id, max(duration), count()) by (trace_id)
```

### AI Trace 查询

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

### AI Session 列表查询

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
