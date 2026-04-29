"""PromQL-compatible query API — /api/v1/query/*

Supports simplified PromQL syntax for time-series metric queries.
Python 3.6.8 compatible.
"""

import re
from typing import Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..metrics.registry import METRIC_REGISTRY
from ..repositories.base import MetricRepository
from ..repositories.dependencies import get_metric_repo

router = APIRouter(prefix="/query", tags=["query"])


# ═══════════════════ Schema ═══════════════════


class QueryRequest(BaseModel):
    query: str = ""
    start: Optional[str] = None
    end: Optional[str] = None
    step: Optional[str] = None


class RankRequest(BaseModel):
    """Rank 请求"""

    query: str
    sort_by: str = "value"
    sort_order: str = "asc"
    limit: int = 10


class RankItem(BaseModel):
    """Rank 项"""

    labels: Dict[str, str]
    value: float
    rank: int


class RankResponse(BaseModel):
    """Rank 响应"""

    query: str
    sort_by: str
    sort_order: str
    limit: int
    items: List[RankItem]


# ═══════════════════ Query Parser ═══════════════════


def parse_query(query_str: str) -> Tuple[str, Dict[str, str]]:
    """Parse simplified PromQL query string.

    Supports:
      - "metric_name"
      - "metric_name{label1=\"val1\", label2=\"val2\"}"

    Returns (metric_name, labels_dict).
    """
    query_str = query_str.strip()
    if not query_str:
        return ("", {})

    brace_start = query_str.find("{")
    if brace_start == -1:
        return (query_str, {})

    metric_name = query_str[:brace_start].strip()
    brace_end = query_str.rfind("}")
    if brace_end == -1:
        return (metric_name, {})

    labels_str = query_str[brace_start + 1 : brace_end]
    labels = {}  # type: Dict[str, str]

    # Match key="value" pairs
    pattern = r'(\w+)\s*=\s*"([^"]*)"'
    for match in re.finditer(pattern, labels_str):
        labels[match.group(1)] = match.group(2)

    return (metric_name, labels)


def parse_aggregation_query(query_str: str) -> Tuple[Optional[str], str, Dict[str, str], Optional[List[str]]]:
    """Parse PromQL aggregation query.

    Supports:
      - "metric_name{labels}"                              # 无聚合
      - "sum(metric_name{labels}) by (scaffold)"           # 按 scaffold 求和
      - "avg(metric_name{labels}) by (language)"           # 按 language 平均
      - "max(metric_name{labels}) by (scaffold, language)" # 多维度分组
      - "min(metric_name{labels}) by (scaffold)"           # 最小值
      - "count(metric_name{labels}) by (scaffold)"         # 计数

    Returns:
        (agg_func, metric_name, labels_dict, group_by)
        - agg_func: None for non-aggregation queries, or "sum"/"avg"/"max"/"min"/"count"
        - metric_name: the metric name
        - labels_dict: labels from the query
        - group_by: None for non-aggregation, or list of dimension names
    """
    query_str = query_str.strip()
    if not query_str:
        return (None, "", {}, None)

    # Pattern for aggregation: agg_func(metric{labels}) by (dims)
    agg_pattern = r"^(sum|avg|max|min|count)\s*\(\s*([^)]+)\s*\)\s*by\s*\(([\w,\s]+)\)$"
    agg_match = re.match(agg_pattern, query_str)

    if agg_match:
        agg_func = agg_match.group(1)
        inner_query = agg_match.group(2)
        group_by_str = agg_match.group(3)
        group_by = [dim.strip() for dim in group_by_str.split(",") if dim.strip()]
        metric_name, labels = parse_query(inner_query)
        return (agg_func, metric_name, labels, group_by)

    # Non-aggregation query
    metric_name, labels = parse_query(query_str)
    return (None, metric_name, labels, None)


def aggregate_series(result: List[Dict], agg_func: Optional[str], group_by: Optional[List[str]]) -> List[Dict]:
    """对 series 进行聚合分组。

    Args:
        result: List of series from extractor, each with "metric" and "values"
        agg_func: "sum", "avg", "max", "min", or "count"
        group_by: List of dimension names to group by (e.g., ["scaffold"] or ["scaffold", "language"])

    Returns:
        Aggregated series list, one per group
    """
    if not agg_func or not group_by:
        return result

    groups = {}  # type: Dict[str, Dict]

    for series in result:
        metric = series.get("metric", {})
        values = series.get("values", [])

        # Build group key from group_by dimensions
        group_key_parts = []
        for dim in group_by:
            val = metric.get(dim, "unknown")
            group_key_parts.append("{}={}".format(dim, val))
        group_key = "|".join(group_key_parts)

        if group_key not in groups:
            groups[group_key] = {
                "metrics": [],
                "values_by_x": {},
            }

        groups[group_key]["metrics"].append(metric)

        # Collect values by x-axis point
        for x_val, val_str in values:
            val = float(val_str)
            if x_val not in groups[group_key]["values_by_x"]:
                groups[group_key]["values_by_x"][x_val] = []
            groups[group_key]["values_by_x"][x_val].append(val)

    # Compute aggregated values for each group
    aggregated = []  # type: List[Dict]
    for group_key, group_data in sorted(groups.items()):
        values = []
        for x_val, vals in sorted(group_data["values_by_x"].items()):
            if agg_func == "sum":
                agg_val = sum(vals)
            elif agg_func == "avg":
                agg_val = sum(vals) / len(vals) if vals else 0
            elif agg_func == "max":
                agg_val = max(vals) if vals else 0
            elif agg_func == "min":
                agg_val = min(vals) if vals else 0
            elif agg_func == "count":
                agg_val = len(vals)
            else:
                agg_val = sum(vals)
            values.append([x_val, str(round(agg_val, 4))])

        # Build metric labels for aggregated series
        base_metric = group_data["metrics"][0] if group_data["metrics"] else {}
        agg_metric = {
            "__name__": "{}_{}".format(agg_func, base_metric.get("__name__", "unknown")),
            "experiment_id": base_metric.get("experiment_id", ""),
            "x_axis_type": base_metric.get("x_axis_type", "iteration"),
        }
        for dim in group_by:
            agg_metric[dim] = base_metric.get(dim, "unknown")

        aggregated.append({"metric": agg_metric, "values": values})

    return aggregated


# ═══════════════════ Routes ═══════════════════


@router.post("")
def query_range(
    request: QueryRequest,
    repo: MetricRepository = Depends(get_metric_repo),
):
    """Execute a PromQL-compatible query and return Prometheus-format results.

    Supports aggregation syntax:
      - "metric_name{labels}"                              # 无聚合，返回细粒度 series
      - "sum(metric_name{labels}) by (scaffold)"           # 按 scaffold 求和
      - "avg(metric_name{labels}) by (language)"           # 按 language 平均
      - "max(metric_name{labels}) by (scaffold, language)" # 多维度分组
    """
    agg_func, metric_name, labels, group_by = parse_aggregation_query(request.query)

    if not metric_name:
        return {
            "status": "success",
            "data": {"resultType": "matrix", "result": []},
        }

    metric_def = METRIC_REGISTRY.get(metric_name)
    if not metric_def:
        return {
            "status": "success",
            "data": {"resultType": "matrix", "result": []},
        }

    extractor = metric_def["extractor"]
    experiment_id = labels.get("experiment_id")

    # Build iteration range (not used for now, future extension)
    iteration_range = None  # type: Optional[Tuple[int, int]]

    # Filter out experiment_id from labels passed to extractor
    extractor_labels = {k: v for k, v in labels.items() if k != "experiment_id"}

    # BUGFIX: When grouping by dimensions, tell extractor to split by that dimension
    # This ensures we get separate series for each group value instead of aggregated data
    if group_by:
        # For multi-dimension group_by, prioritize the most commonly used dimensions
        if "language" in group_by:
            extractor_labels["split_by"] = "language"
        elif "scaffold" in group_by:
            extractor_labels["split_by"] = "scaffold"
        elif "system_prompt" in group_by:
            extractor_labels["split_by"] = "system_prompt"
        elif "tool_schema" in group_by:
            extractor_labels["split_by"] = "tool_schema"

    if experiment_id:
        # Query single experiment
        result = extractor(metric_name, experiment_id, extractor_labels, iteration_range)
    else:
        # Query all experiments
        result = []  # type: List[Dict]
        experiments = repo.get_experiments()
        for exp in experiments:
            series = extractor(metric_name, exp["id"], extractor_labels, iteration_range)
            result.extend(series)

    # Apply aggregation if specified
    if agg_func and group_by:
        result = aggregate_series(result, agg_func, group_by)

    return {
        "status": "success",
        "data": {"resultType": "matrix", "result": result},
    }


@router.get("/metrics")
def list_metrics():
    """Return all available metric names with their labels."""
    return [{"name": name, "labels": info["labels"], "type": info["type"]} for name, info in METRIC_REGISTRY.items()]


@router.get("/metadata")
def get_metadata():
    """Return metric metadata (type, unit, help text)."""
    return {
        name: {
            "type": info["type"],
            "unit": info["unit"],
            "help": info["description"],
        }
        for name, info in METRIC_REGISTRY.items()
    }


# ═══════════════════ Rank API ═══════════════════


def _parse_rank_query(query_str: str) -> Tuple[str, Dict[str, str], Optional[str]]:
    """Parse PromQL query with optional 'by (label)' clause.

    Supports:
      - "metric_name{label1=\"val1\"}"
      - "metric_name{label1=\"val1\"} by (label)"

    Returns (metric_name, labels_dict, group_by_label).
    """
    query_str = query_str.strip()
    if not query_str:
        return ("", {}, None)

    # Check for 'by (label)' clause
    group_by = None
    by_match = re.search(r"\s+by\s*\(\s*(\w+)\s*\)\s*$", query_str)
    if by_match:
        group_by = by_match.group(1)
        query_str = query_str[: by_match.start()]

    # Parse metric name and labels
    brace_start = query_str.find("{")
    if brace_start == -1:
        return (query_str.strip(), {}, group_by)

    metric_name = query_str[:brace_start].strip()
    brace_end = query_str.rfind("}")
    if brace_end == -1:
        return (metric_name, {}, group_by)

    labels_str = query_str[brace_start + 1 : brace_end]
    labels = {}  # type: Dict[str, str]

    # Match key="value" pairs
    pattern = r'(\w+)\s*=\s*"([^"]*)"'
    for match in re.finditer(pattern, labels_str):
        labels[match.group(1)] = match.group(2)

    return (metric_name, labels, group_by)


def _compute_task_metric(
    experiment_id: str,
    metric_name: str,
    task_id: str,
    repo: MetricRepository,
) -> Optional[float]:
    """Compute a metric value for a specific task."""
    trajs = repo.get_trajectories(experiment_id=experiment_id)
    task_trajs = [t for t in trajs if t.get("task_id") == task_id]

    if not task_trajs:
        return None

    if metric_name == "experiment_task_pass_rate":
        passed = sum(1 for t in task_trajs if t.get("passed", False))
        return round(passed / len(task_trajs), 4)
    elif metric_name == "experiment_task_mean_reward":
        rewards = [t.get("reward", 0) for t in task_trajs]
        return round(sum(rewards) / len(rewards), 4)

    return None


@router.post("/rank", response_model=RankResponse)
def rank_query(
    request: RankRequest,
    repo: MetricRepository = Depends(get_metric_repo),
):
    """
    PromQL Rank 查询

    支持排序和限制的 PromQL 查询，用于 TopK/BottomK 场景。
    """
    # 1. 解析查询
    metric_name, labels, group_by = _parse_rank_query(request.query)

    if not metric_name:
        return RankResponse(
            query=request.query,
            sort_by=request.sort_by,
            sort_order=request.sort_order,
            limit=request.limit,
            items=[],
        )

    # Check if metric supports task-level grouping
    if metric_name not in ("experiment_task_pass_rate", "experiment_task_mean_reward"):
        return RankResponse(
            query=request.query,
            sort_by=request.sort_by,
            sort_order=request.sort_order,
            limit=request.limit,
            items=[],
        )

    experiment_id = labels.get("experiment_id")
    if not experiment_id:
        return RankResponse(
            query=request.query,
            sort_by=request.sort_by,
            sort_order=request.sort_order,
            limit=request.limit,
            items=[],
        )

    # 2. 获取所有任务
    trajs = repo.get_trajectories(experiment_id=experiment_id)
    task_ids = sorted(set(t.get("task_id") for t in trajs if t.get("task_id")))

    # 3. 计算每个任务的指标值
    items = []
    for task_id in task_ids:
        value = _compute_task_metric(experiment_id, metric_name, task_id, repo)
        if value is not None:
            items.append(
                {
                    "labels": {"task_id": task_id},
                    "value": value,
                }
            )

    # 4. 排序
    reverse = request.sort_order == "desc"
    items.sort(key=lambda x: x["value"], reverse=reverse)

    # 5. 限制数量
    items = items[: request.limit]

    # 6. 添加排名
    for i, item in enumerate(items):
        item["rank"] = i + 1

    return RankResponse(
        query=request.query,
        sort_by=request.sort_by,
        sort_order=request.sort_order,
        limit=request.limit,
        items=items,
    )
