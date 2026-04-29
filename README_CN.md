# AI-Lens

**AI-Lens** 是面向 AI Agent 训练与生产系统的开源可观测平台。提供强化学习（RL）训练全链路可见性——从实验管理、轨迹分析，到实时服务监控和链路查询。

[English](README.md) | [中文](README_CN.md)

---

## 功能特性

### 已上线 — RL 训练可观测

**Experiments（实验）**
- **Experiment List** — 一览所有实验的核心指标（通过率、Reward、Token 用量、迭代数）
- **Experiment Overview** — 单实验的收敛曲线、Reward 分布与效率指标可视化
- **Task Analysis** — 按 Language / Category 维度的 Pass Rate，识别薄弱 Task 和训练瓶颈
- **Tool Analysis** — 工具调用质量、错误模式与实验内行为趋势分析
- **Trajectory Explorer** — 多维度过滤（Outcome、Iteration、Language、Reward、Turns、Task ID），行内抽屉查看详情；可从 Experiment、Task、Dataset 多个入口复用
- **Trajectory View** — 逐 Turn 回放单条轨迹，还原推理过程、工具调用与观察结果，定位失败根因

**Datasets（数据集）**
- **Dataset Dashboard** — 全局聚合视图：数据集总数、任务数、实验数、轨迹数及最高通过率；点击任意行直达 Task Explorer
- **Task Explorer** — 跨实验的 Task 分析，支持锁定数据集或实验；按 Language、Pass Rate 范围过滤；点击 Task 下钻到 Trajectory Explorer

**Traces（链路追踪）**
- **Trace Search** — 基于 OpenTelemetry + TraceQL 的 Agent Trace 查询与 Span Waterfall 视图

### 规划中

- **个人维度 Agent 可观测** — 单用户 Session 追踪与行为分析
- **Agent 服务指标** — LLM / Tool / Skill 分层运行时指标

## 信息架构

```
AILens（主产品）
│
├── Training（RL 可观测）
│   │
│   ├── Experiments
│   │   └── Experiment List                                          # list 所有实验和核心指标
│   │       └── Experiment Detail                                    # 深入理解单一实验全貌，定位问题与验证效果
│   │           ├── Experiment Overview                              # 实验整体训练效果的宏观判断
│   │           ├── Task Analysis                                    # 识别 Task 级别的趋势和短板
│   │           │   └── Task Explorer（锁定 Experiment 和 DataSet）  # 在 Experiment 上下文中逐一排查所有 Task
│   │           │       └── Trajectory Explorer（锁定 Experiment 和 Task）  # 同 Task 多次执行的横向对比
│   │           │           └── Trajectory View                     # 推理过程回放，逐 Turn 还原单次轨迹，定位失败根因
│   │           ├── Tool Analysis                                    # 评估工具调用质量与瓶颈
│   │           ├── ...
│   │           └── Trajectory Explorer（锁定 Experiment）           # 从实验维度全局查看轨迹质量与分布
│   │               └── Trajectory View                             # 推理过程回放，逐 Turn 还原单次轨迹，定位失败根因
│   │
│   └── DataSets                                                     # 管理评测数据集，掌握数据资产全景
│       └── DataSet List                                             # list 所有数据集
│           └── Task Explorer（锁定 DataSet）                        # list 特定数据集下所有 Task 及核心指标
│               └── Task Detail                                      # 从数据视角分析 Task 跨实验、跨 Scaffold、跨模型表现
│                   └── Trajectory Explorer（锁定 Task）             # 查看该 Task 所有执行轨迹的原始数据
│                       └── Trajectory View                         # 推理过程回放，逐 Turn 还原单次轨迹，定位失败根因
```

## 系统架构

### 查询链路（读）

```
┌──────────────┐   REST/JSON   ┌─────────────────┐   TraceQL   ┌─────────────────┐
│    前端       │ ────────────▶ │      后端        │ ──────────▶ │     网关        │
│  React + TS  │               │  Python FastAPI  │             │ Java/ClickHouse │
└──────────────┘               └─────────────────┘             └─────────────────┘
                                                                        │
                                                               ┌────────▼────────┐
                                                               │   ClickHouse    │
                                                               └─────────────────┘
```

### 写入链路（数据上报）

```
RL 训练轨迹：
  HarborSDK ──▶ OTel Collector（logs pipeline）   ──▶ otel_logs ──▶ rl_traces（MV）
                      │                                                ClickHouse
Agent 服务链路追踪：  │
  OTel SDK  ──▶ OTel Collector（traces pipeline） ──▶ otel_traces
                      └── 单个 otelcol-contrib 实例，端口 4317/4318
```

| 服务 | 技术栈 | 端口 |
|------|--------|------|
| 前端 | React 19, TypeScript, Vite, Ant Design, ECharts | 3000 |
| 后端 | Python 3.11+, FastAPI, Pydantic v2, Prometheus | 8000 |
| 网关 | Java 21, Spring Boot, ANTLR4, ClickHouse | 8080 |
| OTel Collector | otelcol-contrib（logs + traces 双 pipeline） | 4317（gRPC）/ 4318（HTTP） |

## 快速开始

### 方式一 — Docker Compose（推荐）

```bash
git clone https://github.com/alibaba/AILens.git
cd AILens/deploy
docker-compose up -d
```

启动后访问：

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost:3000 |
| 后端 API | http://localhost:8000 |
| 后端 Swagger | http://localhost:8000/docs |
| 网关 | http://localhost:8080 |
| OTel Collector gRPC | localhost:4317 |
| OTel Collector HTTP | localhost:4318 |

**数据上报：**

- **Agent 链路追踪** — 将 OTel SDK 的 exporter endpoint 指向 `http://localhost:4318`（HTTP）或 `localhost:4317`（gRPC）
- **RL 训练轨迹** — 将 HarborSDK 的 logs exporter 指向 `http://localhost:4318`，数据写入 `otel_logs` 后由 `rl_traces` 物化视图自动聚合

### 方式二 — 本地开发

**前置条件：** Python 3.11+、Node.js 20+、**Java 21+**、Maven 3.6+

> 注意：网关需要 Java 21。若系统默认版本较低，需手动指定 `JAVA_HOME`（见下方步骤）。

**1. 启动网关**

```bash
# 首次运行需先编译
cd gateway
JAVA_HOME=/path/to/jdk-21 mvn clean package -DskipTests -q

# 运行，通过环境变量传入 ClickHouse 连接信息
JAVA_HOME=/path/to/jdk-21 \
  CLICKHOUSE_URL="jdbc:clickhouse://<host>:8123/default" \
  CLICKHOUSE_USERNAME="<user>" \
  CLICKHOUSE_PASSWORD="<password>" \
  $JAVA_HOME/bin/java -jar gateway-server/target/gateway-server-*.jar
```

**2. 启动后端** — 必须在 **monorepo 根目录**执行（内部使用相对导入）

```bash
cd /path/to/AILens        # monorepo 根目录，不是 backend/ 目录
pip3 install -r backend/requirements.txt

TRACEQL_BASE_URL=http://localhost:8080 \
  python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

**3. 启动前端**

```bash
cd frontend
npm install
npm run dev
```

## 目录结构

```
AILens/
├── backend/          # Python FastAPI 后端（从 monorepo 根目录启动）
│   ├── app/                  # 应用主包
│   │   ├── main.py           # 应用入口
│   │   ├── config.py         # 配置
│   │   ├── routers/          # API 路由
│   │   ├── models/           # Pydantic 数据模型
│   │   ├── mock/             # 内置 Mock 数据
│   │   ├── metrics/          # 指标提取器
│   │   ├── repositories/     # 数据访问层
│   │   └── observability/    # 日志、指标、链路追踪
│   └── tests/                # pytest 测试套件
├── frontend/         # React/TypeScript 前端
│   └── src/
│       ├── api/              # API 请求层
│       ├── components/       # 通用 UI 组件
│       ├── pages/            # 页面组件
│       ├── stores/           # Zustand 状态管理
│       └── queries/          # TanStack Query Hooks
├── gateway/          # Java Spring Boot 查询网关
│   ├── gateway-core/         # 核心抽象层
│   ├── gateway-traceql/      # ANTLR4 TraceQL 引擎 + ClickHouse SQL 生成
│   └── gateway-server/       # REST API 服务
├── deploy/           # Docker Compose 部署
│   ├── docker-compose.yml
│   └── docker/clickhouse/    # ClickHouse Schema + 示例数据
├── docs/             # 文档
└── scripts/          # 开发脚本
```

## 数据模型

```
Project（项目）
 └── Experiment（实验）
      ├── Config（模型/scaffold/算法/Reward 配置）
      └── Iteration（一轮迭代）
           └── Trajectory（一条轨迹 = Agent 完成一个 Task 的完整记录）
                └── Turn（一轮交互）
                     └── Event（reasoning / action / observation）
```

## Mock 数据

后端内置内存 Mock Store（实验/迭代元数据），ClickHouse 初始化脚本包含 12 条样例轨迹，覆盖 2 个实验、2 个数据集：

- **demo_qwen72b_swebench** — 8 条轨迹（qwen-72b 在 SWE-bench Python 任务上的 2 个迭代）
- **demo_glm5_java** — 4 条轨迹（glm-5 在 SWE-bench Java 任务上的 2 个迭代）

当您有生产数据时，通过 Gateway 接入真实 ClickHouse 即可替换 Mock。

## 环境配置

将 `.env.example` 复制为 `.env` 并按需修改：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `TRACEQL_BASE_URL` | Gateway 服务地址 | `http://localhost:8080` |
| `LOG_LEVEL` | 日志级别 | `INFO` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OpenTelemetry Collector | `http://localhost:4317` |

完整配置项见 `.env.example`。

## 参与贡献

欢迎提交 Issue 和 Pull Request！请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 开源协议

[Apache License 2.0](LICENSE)
