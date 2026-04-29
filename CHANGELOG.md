# Changelog

[English](#english) | [中文](#chinese)

---

<a name="english"></a>

## English

### v0.1.1 — April 15, 2026

#### New Features

##### Dataset Dashboard

> Get a bird's-eye view of all datasets — quickly assess task quality and coverage.

- Summary cards aggregating total datasets, tasks, experiments, trajectories, and the highest pass rate across all datasets
- Per-dataset table showing task count, experiment count, trajectory count, and pass rate — all columns sortable
- Click any dataset row to jump directly into Task Explorer scoped to that dataset

[Learn more](#dataset-dashboard-1)

##### Task Explorer

> Analyze task performance across experiments and datasets — pinpoint weak spots by language, scaffold, or pass rate.

- Filter tasks by Language and Pass Rate range
- Live summary bar showing total tasks, total trajectories, and pass / fail counts
- Sortable columns: Task ID, Language, Dataset, Trajectories, Pass, Fail, Pass Rate
- Click any task row to drill down into Trajectory Explorer for that task's detailed trajectories
- Supports **experiment mode** (tasks scoped to a single experiment) and **dataset mode** (tasks scoped to a single dataset across all experiments)

[Learn more](#task-explorer-1)

#### Improvements

##### Trajectory Explorer

> The platform has unified the concept of "Rollout" to **Trajectory** throughout. Trajectory Explorer adopts a new dual-mode architecture, reusable from Experiment, Task, and Dataset entry points.

- Single Trajectory Explorer component reused across Experiment, Task, and Dataset entry points
- Multi-dimensional filtering: Outcome (Success / Failure / Timeout / Error), Iteration, Language, Reward range, Turns range, Task ID
- Click any trajectory row to open a **detail Drawer** — view the full trajectory without leaving the list
- Sidebar shows Outcome distribution at a glance
- Pagination and column sorting for efficient browsing of large result sets

[Learn more](#trajectory-explorer-refactor-1)

##### Other

- **Terminology unification**: "Rollout" renamed to "Trajectory" platform-wide for conceptual clarity
- **Filter refactor**: All filter pages migrated to Ant Design `Form` for consistent state management and better UX
- **Dockerfile**: Added Dockerfiles for containerized deployments

#### Bug Fixes

- Fixed breadcrumb losing experiment attributes after switching tabs on the Experiment detail page
- Fixed "All" filter option being unresponsive when selected
- Fixed TraceQL Row type definition validation logic against raw response format
- Fixed multiple line-break rendering issues

---

#### Details

<a name="dataset-dashboard-1"></a>

##### Dataset Dashboard

**When to use:**
Before diving into a specific experiment, you may want to understand which datasets are in use, how many tasks and experiments they cover, and whether task quality is sufficient. Dataset Dashboard provides:

- **Quick quality snapshot** — summary cards show total datasets, tasks, experiments, trajectories, and the highest pass rate across all datasets
- **Per-dataset metrics** — each row shows task count, experiment count, trajectory count, and pass rate, all sortable
- **One-click exploration** — click any dataset row to jump to its Task Explorer, automatically scoped to that dataset

<a name="task-explorer-1"></a>

##### Task Explorer

**When to use:**
When experiment-level pass rates are below target, or when you want to compare task difficulty across datasets:

- **Compare by language** — use the Language filter to break down tasks by programming language
- **Find weak tasks** — set a Pass Rate range (e.g. 0%–50%) to quickly surface persistently failing tasks
- **Drill down** — click any task row to view its trajectories in Trajectory Explorer; Task ID and Language filters are pre-populated automatically
- **Dual-mode** — enter from an Experiment detail page (scoped to that experiment's tasks) or from Dataset Dashboard (all tasks under that dataset across experiments)

**Navigation flow:**
Experiment detail → Task Analysis tab → click "View All" to open pre-filtered Task Explorer
— or —
Dataset Dashboard → click a dataset row → Task Explorer scoped to that dataset

<a name="trajectory-explorer-refactor-1"></a>

##### Trajectory Explorer

**When to use:**
When you spot anomalous metrics at the Experiment or Task level, Trajectory Explorer lets you investigate row by row:

- **Quickly isolate failures** — use the Outcome filter to focus on failed, timed-out, or errored trajectories
- **Narrow down precisely** — combine Reward range, Turns range, Iteration, Language, and Task ID filters
- **Inspect in context** — click any row to open a drawer panel with the full trajectory detail while keeping the list visible
- **Outcome distribution** — sidebar shows pass / fail / timeout / error breakdown at a glance

---

<a name="chinese"></a>

## 中文

### v0.1.1 — 2026 年 4 月 15 日

#### 新功能

##### Dataset Dashboard

> 从全局视角掌握所有数据集的整体情况——快速评估 Task 质量和覆盖范围

- 数据集总览卡片，聚合展示总数据集数、总任务数、总实验数、总轨迹数和最高通过率
- 按数据集逐行展示任务数、实验数、轨迹数和通过率，支持排序
- 点击任意数据集行，直接进入该数据集范围内的 Task Explorer 页面

[了解详情](#dataset-dashboard-2)

##### Task Explorer

> 跨实验、跨数据集分析任务效果——按语言、Scaffold 或通过率定位薄弱环节

- 按 Language 和 Pass Rate 范围过滤任务
- 顶部摘要栏实时展示任务总数、轨迹总数、通过/失败数量
- 可排序列：Task ID、Language、Dataset、Trajectories、Pass、Fail、Pass Rate
- 点击任意任务行，下钻到 Trajectory Explorer 查看该任务的详细轨迹
- 支持**实验模式**（限定单个实验内的任务）和**数据集模式**（限定单个数据集下的所有任务）

[了解详情](#task-explorer-2)

#### 改进

##### Trajectory Explorer

> 将平台中的"Rollout"概念全面统一为 **Trajectory**，提升术语一致性。Trajectory Explorer 采用全新的双模式架构，支持从 Experiment、Task、Dataset 多个入口复用同一组件。

- 从 Experiment、Task、Dataset 入口查看轨迹时，复用统一的 Trajectory Explorer 组件
- 支持多维度过滤：Outcome（Success / Failure / Timeout / Error）、Iteration、Language、Reward 范围、Turns 范围、Task ID
- 点击任意轨迹行，弹出**详情抽屉（Drawer）**，无需离开列表页即可查看完整的轨迹明细
- 侧边栏展示 Outcome 分布统计，一目了然
- 分页和列排序，提升大数据量下的浏览效率

[了解详情](#trajectory-explorer-2)

##### 其他

- **术语统一**：平台全面将"Rollout"更名为"Trajectory"，概念更清晰
- **过滤器重构**：所有过滤器页面统一迁移为 Ant Design `Form` 管理，状态处理更一致，用户体验更好
- **Dockerfile**：新增 Dockerfile，支持容器化环境部署

#### Bugfix

- 修复 Experiment 详情页切换标签后面包屑中实验属性消失的问题
- 修复过滤项选择"All"时无响应的问题
- 修复 TraceQL Row 类型定义对原始返回格式的校验逻辑
- 修复多处换行渲染问题

---

#### 详细介绍

<a name="dataset-dashboard-2"></a>

##### Dataset Dashboard

**使用场景：**
在深入分析具体实验之前，你可能希望了解当前使用了哪些数据集，它们覆盖了多少任务与实验，以及 Task 质量是否足够。Dataset Dashboard 为你提供：

- **快速质量快照**——摘要卡片展示数据集总数、任务总数、实验总数、轨迹总数，以及所有数据集中的最高通过率
- **逐数据集指标**——每行展示任务数、实验数、轨迹数和通过率，全部支持排序
- **一键深入探索**——点击任意数据集行，跳转到其 Task Explorer，自动限定在该数据集范围内

<a name="task-explorer-2"></a>

##### Task Explorer

**使用场景：**
当实验整体通过率不达标，或者你想跨数据集对比任务难度时：

- **按语言对比**——使用 Language 过滤器，按编程语言拆分任务
- **找出薄弱任务**——设置 Pass Rate 范围（如 0%–50%），快速筛出持续失败的任务
- **下钻分析**——点击任意任务行，在 Trajectory Explorer 中查看该任务的详细轨迹，Task ID 和 Language 过滤器已自动预填
- **双模式使用**——从 Experiment 详情页进入（仅展示该实验下的任务），或从 Dataset Dashboard 进入（展示该数据集下跨所有实验的任务）

**产品动线：**
Experiment 详情页 → Task Analysis 标签页 → 点击"View All"打开已预过滤的 Task Explorer
— 或 —
Dataset Dashboard → 点击某个数据集行 → 打开限定在该数据集范围内的 Task Explorer

<a name="trajectory-explorer-2"></a>

##### Trajectory Explorer 重构

**使用场景：**
当你在 Experiment 或 Task 层面发现异常指标时，Trajectory Explorer 帮你逐条排查：

- **快速定位失败轨迹**——通过 Outcome 过滤器聚焦失败、超时或出错的轨迹
- **精确缩小范围**——结合 Reward 范围、Turns 范围、Iteration、Language、Task ID 等多维度过滤
- **原地查看详情**——点击任意行弹出抽屉面板，展示完整轨迹明细，同时保持列表上下文可见
- **Outcome 分布统计**——侧边栏展示通过/失败/超时/错误的分布，一目了然
