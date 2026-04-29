# Observability Gateway

开源**可观测查询网关**，后端存储为 ClickHouse。当前支持 **Trace 查询**（TraceQL），**指标查询**（PromQL）规划中。

[English](README.md) | [中文](README_CN.md)

---

## 功能特性

- **TraceQL 查询语言** — 兼容 Tempo/LogQL/PromQL 语法，查询 Trace 和轨迹数据
- **ClickHouse 后端** — 针对列式存储优化的 SQL 生成
- **多 Scope 支持** — 通过同一 API 查询 OTLP Trace（`scope=otlp`）和 RL 增强学习轨迹（`scope=rl`）
- **View 视图** — 在 YAML 中预定义命名查询，通过 `view(name)` 语法引用
- **Prometheus 兼容的 Stat API** — 聚合结果以 PromQL 风格的 `{metric, values}` 格式返回
- **可扩展架构** — 插件化的 `FieldMapper` 和查询引擎模块，已为 PromQL 指标查询做好扩展准备
- **ANTLR4 语法引擎** — 易于添加新函数和操作符

## 快速开始

### 环境要求

- Java 21+
- Maven 3.6+
- ClickHouse（或使用内置的 docker-compose）

### 使用 Docker Compose

```bash
# 启动 ClickHouse 并初始化示例数据
docker-compose up -d

# 启动网关服务
mvn -pl gateway-server spring-boot:run
```

### 手动配置

1. 创建 ClickHouse 表：

```bash
clickhouse-client < gateway-server/src/main/resources/sql/schema.sql
```

2. 配置连接信息：

```bash
export CLICKHOUSE_URL=jdbc:clickhouse://localhost:8123/default
export CLICKHOUSE_USERNAME=default
export CLICKHOUSE_PASSWORD=
```

3. 构建并启动：

```bash
mvn clean package -DskipTests
mvn -pl gateway-server spring-boot:run
```

服务启动在 `http://localhost:8080`。

## API 接口

### Trace 数据查询

**POST** `/api/v1/trace/query`

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| query | String | 是 | | TraceQL 查询语句 |
| start | Long | 否 | | 开始时间（秒），不传则不限制 |
| end | Long | 否 | | 结束时间（秒），不传则不限制 |
| pageSize | int | 否 | 100 | 返回结果数（支持 `page_size` 下划线写法） |
| scope | String | 否 | otlp | 数据范围：`otlp` / `rl` |

```bash
curl -X POST http://localhost:8080/api/v1/trace/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{service_name = '\''my-service'\'' and duration > 1000}",
    "pageSize": 100
  }'
```

### Trace 转指标查询

**POST** `/api/v1/trace/stat/query`

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| querys | Object[] | 是 | | 查询列表 |
| querys[n].alias | String | 否 | | 指标名（对应返回的 `__name__`） |
| querys[n].query | String | 是 | | TraceQL 聚合查询语句 |
| start | Long | 否 | | 开始时间（秒） |
| end | Long | 否 | | 结束时间（秒） |
| scope | String | 否 | otlp | 数据范围 |

返回格式（Prometheus 风格）：
```json
{
  "code": 0,
  "success": true,
  "data": {
    "result": [
      {
        "metric": {"ServiceName": "my-service", "__name__": "svc_latency"},
        "values": [[null, "42"]]
      }
    ]
  }
}
```

### TraceQL 查询示例

```
# 简单 Span 查询
{service_name = 'my-service' and duration > 1000}

# Trace 查询（查找跨多个服务的调用链）
{service_name = 'frontend'} && {service_name = 'backend'} | query_by(trace_id)

# 聚合统计
{} | select(service_name, p99(duration) as p99_dur, count() as cnt) by (service_name)

# AI Trace 分析
{}|(attributes.gen_ai.span_kind_name != null)
  | query_by(trace_id)
  | select(
      trace_id as traceId,
      first(span_name) as rootName,
      sum(if(attributes.gen_ai.span_kind_name = 'LLM',
        attributes.gen_ai.usage.input_tokens, 0)) as totalInputTokens,
      count() as spanNum
    ) by (trace_id)

# RL 增强学习轨迹查询（scope=rl）
{experiment_id = 'my-experiment' and reward > 0.8}
  | select(model, round(avg(reward), 4) as mean_reward, stddev(reward) as std) by (model)

# 使用命名视图
view(my_view) | (avg_dur > 1000)
```

## 文档

- [TraceQL Syntax Reference (English)](docs/traceql-syntax-en.md)
- [TraceQL 语法文档 (中文)](docs/traceql-syntax.md)

## 项目结构

```
gateway-parent/
├── gateway-core/              # 核心层：FieldMapper 接口、查询执行器、共享抽象
├── gateway-traceql/           # TraceQL 引擎：ANTLR4 语法、AST、SQL 生成器
│   ├── src/main/antlr4/       # TraceQL.g4 语法文件
│   └── src/main/java/         # 解析器、AST 节点、ClickHouse SQL 生成器
├── gateway-promql/            # （规划中）PromQL 指标查询引擎
├── gateway-server/            # Spring Boot REST API 服务
│   ├── src/main/java/         # Controller、Service、Repository
│   └── src/main/resources/
│       ├── application.yml    # 配置文件
│       └── sql/               # ClickHouse DDL
├── docker/                    # Docker 初始化脚本（Schema + 示例数据）
└── docs/                      # 文档
```

## 配置说明

```yaml
spring:
  datasource:
    url: ${CLICKHOUSE_URL:jdbc:clickhouse://localhost:8123/default}
    username: ${CLICKHOUSE_USERNAME:default}
    password: ${CLICKHOUSE_PASSWORD:}

clickhouse:
  tables:
    otlp: otel_traces        # OTLP Trace 表
    rl: rl_traces             # RL 轨迹物化视图

traceql:
  views:                      # 命名视图定义
    my_view: "{service_name = 'x'} | select(avg(duration) as avg_dur) by (service_name)"
```

## 开源协议

[Apache License 2.0](LICENSE)
