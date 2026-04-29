# AI Lens Dashboard Reference

> Updated: 2026-04-17

---

## 实验详情页结构

```
Experiment Detail Page
├── Header（实验信息 + 全局筛选器）
│   ├── 实验名称、状态、Scaffolds、Algorithm、Model
│   ├── Trajectory Explorer 按钮
│   └── 筛选器：Scaffold / Language / Tool Schema / Split By
│
├── Tab 1: 📈 Training Overview（训练概览）
├── Tab 2: 🎯 Task Analysis（任务分析）
├── Tab 3: 🤖 Behavior Analysis（行为分析）
└── Tab 4: ⚖️ Quality Assessment（质量评估）
```

---

## Tab 1: 📈 Training Overview（训练概览）

### 1.1 Mean Reward

| 属性 | 值 |
|------|-----|
| **图表类型** | 时序折线图（TimeSeriesChart） |
| **X轴** | 迭代序号（#iteration_num） |
| **Y轴** | Reward（奖励值） |
| **支持 Split By** | ✅ scaffold / tool_schema |
| **特殊功能** | 可叠加标准差区域（showSigmaTip） |

**引用指标（PromQL）：**
```promql
experiment_mean_reward{experiment_name="<name>"}
```

**指标定义：** `Σ(reward) / N`，每个迭代的平均奖励值

---

### 1.2 Pass Rate

> **📋 训练总览对应图表**：
> - 「1.1 按System Prompt的通过率趋势」（Split By scaffold）
> - 「1.2 通过率趋势 vs 历史通过率」（含 Historical Baseline）
> - 「2.1 按step的通过率趋势」

| 属性 | 值 |
|------|-----|
| **图表类型** | 时序折线图（带面积） |
| **X轴** | 迭代序号 |
| **Y轴** | Pass Rate（0-1，显示为百分比） |
| **支持 Split By** | ✅ scaffold / tool_schema |
| **特殊功能** | 叠加 Historical Baseline 虚线 |

**引用指标（PromQL）：**
```promql
experiment_pass_rate{experiment_name="<name>"}
experiment_pass_rate_baseline{experiment_name="<name>"}  # 虚线参考线
```

**指标定义：** `Σ(verify_code='success') / N`，每个迭代的通过率

---

### 1.3 Tokens per Trajectory

| 属性 | 值 |
|------|-----|
| **图表类型** | 时序折线图 |
| **X轴** | 迭代序号 |
| **Y轴** | Tokens |
| **支持 Split By** | ✅ scaffold, tool_schema |

**引用指标（PromQL）：**
```promql
# 平均每条轨迹的 token 消耗
(experiment_input_tokens{experiment_name="<name>"} + experiment_output_tokens{experiment_name="<name>"})
  / experiment_trajectory_count{experiment_name="<name>"}

# 按 scaffold 分组
(experiment_input_tokens{experiment_name="<name>"} by (scaffold) + experiment_output_tokens{experiment_name="<name>"} by (scaffold))
  / experiment_trajectory_count{experiment_name="<name>"} by (scaffold)
```

**计算口径：** `Σ(input_tokens + output_tokens) / N`，每条轨迹的平均 token 消耗

---

### 1.4 Token Efficiency (Tokens/Reward)

| 属性 | 值 |
|------|-----|
| **图表类型** | 时序折线图 |
| **X轴** | 迭代序号 |
| **Y轴** | Tokens/Reward |
| **支持 Split By** | ✅ scaffold, tool_schema |

**引用指标（PromQL）：**
```promql
experiment_tokens_per_reward{experiment_name="<name>"}

# 按 scaffold 分组
experiment_tokens_per_reward{experiment_name="<name>"} by (scaffold)
```

**指标定义：** `Σ(total_tokens) / Σ(reward)`，单位奖励的 token 成本

---

### 1.5 Input/Output Ratio

| 属性 | 值 |
|------|-----|
| **图表类型** | 时序折线图 |
| **X轴** | 迭代序号 |
| **Y轴** | Ratio |

**引用指标（PromQL）：**
```promql
experiment_input_tokens{experiment_name="<name>"} / experiment_output_tokens{experiment_name="<name>"}
```

**计算口径：** `Σ(input_tokens) / Σ(output_tokens)`，输入输出 token 比率

---

### 1.6 Success Mean Turns Trend

| 属性 | 值 |
|------|-----|
| **图表类型** | 时序折线图 |
| **X轴** | 迭代序号 |
| **Y轴** | Turns |

**引用指标（PromQL）：**
```promql
experiment_success_mean_turns{experiment_name="<name>"}
```

**指标定义：** 成功轨迹（`verify_code='success'`）的 `Σ(user_turns + assistant_turns) / N_success`

---

### 1.7 Scaffold Stats Section

| 属性 | 值 |
|------|-----|
| **图表类型** | 表格 |
| **数据来源** | PromQL 查询（使用 `by (scaffold)`） |
| **展示维度** | 按 Scaffold 分组 |

**表格列：**

| 列名 | PromQL | 说明 |
|------|--------|------|
| Scaffold | - | 维度标签，从返回结果的 `scaffold` label 获取 |
| Trajectories | `experiment_trajectory_count{experiment_name="<name>"} by (scaffold)` | 轨迹数 |
| Passed | `experiment_passed_count{experiment_name="<name>"} by (scaffold)` | 通过数 |
| Pass Rate | `experiment_pass_rate{experiment_name="<name>"} by (scaffold)` | 通过率 |
| Avg Reward | `experiment_mean_reward{experiment_name="<name>"} by (scaffold)` | 平均奖励 |
| Avg Turns | `experiment_mean_turns{experiment_name="<name>"} by (scaffold)` | 平均轮次 |
| Avg Tokens | `(experiment_input_tokens + experiment_output_tokens) by (scaffold) / experiment_trajectory_count by (scaffold)` | 平均 token 消耗 |
| Avg Duration | `experiment_mean_duration_ms{experiment_name="<name>"} by (scaffold)` | 平均耗时（ms） |

**查询示例：**

```promql
# 按 scaffold 分组的通过率
experiment_pass_rate{experiment_name="exp-grpo-cc"} by (scaffold)

# 返回结果示例
{scaffold="claude_code"} 0.54
{scaffold="openclaw"} 0.52
```

**前端处理：**
1. 查询上述指标（带 `by (scaffold)`）
2. 从返回结果的 `scaffold` label 提取 scaffold 名称
3. 聚合为表格行数据，每个 scaffold 一行

---

### 1.9 Success Trajectory Turns Distribution

> **📋 训练总览对应图表**：「1.3 成功解决问题时的交互轮次分布」
> - 子图表1: 最大与最小交互轮次 → Min Turns / Max Turns 卡片
> - 子图表2: P99与P90交互轮次 → P90 Turns / P99 Turns 卡片
> - 子图表3: 交互轮次分布图 → 柱状图

| 属性 | 值 |
|------|-----|
| **图表类型** | 指标卡片 + 柱状图 |
| **数据来源** | PromQL 查询 |
| **展示维度** | - |

**指标卡片：**

| 卡片 | PromQL |
|------|--------|
| Total Success | `experiment_success_turns_count{experiment_name="<name>"}` |
| Min Turns | `experiment_success_min_turns{experiment_name="<name>"}` |
| Max Turns | `experiment_success_max_turns{experiment_name="<name>"}` |
| Mean Turns | `experiment_success_turns_sum / experiment_success_turns_count` |
| P90 Turns | `histogram_quantile(0.90, rate(experiment_success_turns_bucket{experiment_name="<name>"}[5m]))` |
| P99 Turns | `histogram_quantile(0.99, rate(experiment_success_turns_bucket{experiment_name="<name>"}[5m]))` |

**柱状图（分布直方图）：**

```promql
experiment_success_turns_bucket{experiment_name="<name>"}
```

**Bucket 边界：** `[1, 3, 5, 7, 10, 12, 15, 17, 20, +Inf]`

**前端处理：**
- 从 bucket 数据计算增量（当前 bucket - 前一个 bucket）
- 绘制区间分布柱状图，X 轴为轮次区间，Y 轴为轨迹数量

**指标定义：** 成功轨迹（`verify_code='success'`）的轮次分布 histogram

---

### 1.10 Training Duration Statistics

> **📋 训练总览对应图表**：「3.1 训练时长统计」

| 属性 | 值 |
|------|-----|
| **图表类型** | 多线时序折线图 |
| **X轴** | 迭代序号（iteration_num） |
| **Y轴** | 耗时（毫秒） |
| **数据来源** | PromQL 查询 |

**展示指标：**

| 线条 | PromQL | 说明 |
|------|--------|------|
| Verify Duration | `experiment_mean_verify_duration_ms{experiment_name="<name>"}` | 平均验证耗时 |
| Sandbox Create | `experiment_mean_sandbox_create_duration_ms{experiment_name="<name>"}` | 平均 Sandbox 创建耗时 |

**图表配置：**
- 两条独立时序线，不同颜色区分
- Y 轴单位：毫秒（ms）
- 支持图例切换显示/隐藏

---

### 1.11 Turn Analysis Section

| 属性 | 值 |
|------|-----|
| **图表类型** | 表格 |
| **数据来源** | PromQL 查询 |
| **展示维度** | 按 total_turns 分组 |

**引用指标（PromQL）：**

| 指标名 | 说明 |
|--------|------|
| `experiment_turns_count` | 每个 total_turns 值的轨迹总数 |
| `experiment_turns_passed_count` | 每个 total_turns 值的成功轨迹数 |
| `experiment_turns_duration_max` | 成功轨迹的最大时长(ms) |
| `experiment_turns_duration_sum` | 成功轨迹的时长总和(ms) |
| `experiment_turns_duration_count` | 成功轨迹的时长计数 |

**表格列计算：**

| 列名 | 计算方式 |
|------|----------|
| Turns | `total_turns` label 值 |
| 频次 | `experiment_turns_count` 最新值 |
| Pass% | `experiment_turns_passed_count / experiment_turns_count` |
| MaxDuration(passed) | `experiment_turns_duration_max` 最新值 |
| AvgDuration(passed) | `experiment_turns_duration_sum / experiment_turns_duration_count` |

---

## Tab 2: 🎯 Task Analysis（任务分析）

### 2.1 Language Stats Section

| 属性 | 值 |
|------|-----|
| **图表类型** | 表格 |
| **数据来源** | ~~REST API `/analysis/language`~~ **PromQL 聚合查询**（REQ-001） |
| **展示维度** | 按编程语言分组 |

**引用指标（PromQL）：**

| 字段 | PromQL 查询 |
|------|-------------|
| Trajectories | `sum(experiment_trajectory_count{experiment_name="<name>"}) by (language)` |
| Pass Rate | `avg(experiment_pass_rate{experiment_name="<name>"}) by (language)` |
| Max Turns (passed) | `max(experiment_success_turns_max{experiment_name="<name>"}) by (language)` |
| Avg Turns (passed) | `avg(experiment_success_mean_turns{experiment_name="<name>"}) by (language)` |
| Max Duration (passed) | `max(experiment_success_duration_max{experiment_name="<name>"}) by (language)` |
| Avg Duration (passed) | `avg(experiment_success_duration_mean{experiment_name="<name>"}) by (language)` |

**前端实现：**
- 使用 `useLanguageStats` hook 聚合上述指标
- 从返回结果的 `language` label 提取语言名称
- 组装为表格行数据


---

### 2.2 Task Effectiveness Section

| 属性 | 值 |
|------|-----|
| **图表类型** | 饼图 + 表格 |
| **数据来源** | REST API `/analysis/task-effectiveness` |

**饼图内容：**
- All Correct（全通过）
- All Wrong（全失败）
- Mixed（混合）

**引用指标（PromQL）：**
```promql
experiment_task_all_correct_rate{experiment_name="<name>"}
experiment_task_all_wrong_rate{experiment_name="<name>"}
experiment_task_mixed_rate{experiment_name="<name>"}
```

**指标定义：** 三个指标之和为 1，表示 task 效果性分布

---

## Tab 3: 🤖 Behavior Analysis（行为分析）

### 3.1 Tool Quality Section

| 属性 | 值 |
|------|-----|
| **图表类型** | 表格（含 Latency 列） |
| **数据来源** | REST API `/analysis/tool-quality` + `/analysis/tool-latency` |
| **展示维度** | 按工具名分组 |

**表格列：**
- Tool
- Total Calls / Success Calls / Success Rate
- Error Tasks / Success Tasks
- Mean / P50 / P90 / P99 / Max Latency（来自 Tool Latency API）

**引用指标：**
- `experiment_tool_call_count`
- `experiment_tool_success_rate`
- `experiment_tool_error_task_rate`
- `experiment_tool_success_task_rate`

---

## Tab 4: ⚖️ Quality Assessment（质量评估）

### 4.1 Format Correctness Rate

| 属性 | 值 |
|------|-----|
| **图表类型** | 时序折线图 |
| **X轴** | 迭代序号 |
| **Y轴** | Rate（0-1，显示为百分比） |
| **支持 Split By** | ✅ scaffold / tool_schema |

**引用指标（PromQL）：**
```promql
experiment_format_correct_rate{experiment_name="<name>"}
```

**指标定义：** `Σ(format_correct=true) / N`，输出格式正确率

---

### 4.2 Repetition Detection

| 属性 | 值 |
|------|-----|
| **图表类型** | 指标卡片 + 时序折线图 |
| **数据来源** | REST API `/analysis/repetition-detection` |

#### 指标卡片

| 卡片 | 说明 |
|------|------|
| Tool Call Repeat % | 工具调用重复率（受影响轨迹占比） |
| Tool Repeats | 工具调用重复次数 |
| Response Repeat % | 响应重复率（受影响轨迹占比） |
| Response Repeats | 响应重复次数 |

#### 时序图

**引用指标（PromQL）：**
```promql
experiment_repeat_tool_call_rate{experiment_name="<name>"}
experiment_repeat_response_rate{experiment_name="<name>"}
```

**指标定义：**
- `experiment_repeat_tool_call_rate`: 存在工具调用重复的轨迹占比
- `experiment_repeat_response_rate`: 存在响应重复的轨迹占比

---
