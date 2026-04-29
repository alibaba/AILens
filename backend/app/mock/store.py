"""Mock Data Store - Singleton that lazily generates and holds all mock data.

This module provides the MockDataStore class which generates consistent,
reproducible mock data for the AI Lens application. The data is generated
on-demand and cached for subsequent accesses.

PRD v0.8.2 aligned. Python 3.6.8 compatible.

Key invariants:
  * 2 Projects, each with 2 Benchmarks and 3 Experiments
  * Each Benchmark has 20 Tasks (diverse category/difficulty/language)
  * Each Experiment has 50 Iterations, each with 100 Trajectories
  * Reward / pass_rate improve over iterations (convergence) with noise
  * Different task_categories have clearly different pass_rates
  * Multiple scaffolds per experiment (claude_code, openclaw, aider)
  * Tool diversity (bash, file_edit, web_search, read_file, submit) with success/failure
  * 2 AgentServices (coding-agent-prod, qa-agent-staging)
  * Mock trace data with RL correlation
"""

import random

from .builders import (
    add_project,
    build_active_alerts,
    build_agent_metrics,
    build_agent_service_metrics,
    build_agent_services,
    build_alert_rules,
    build_benchmarks,
    build_experiments,
    build_iterations,
    build_projects,
    build_tasks_for_benchmark,
    build_traces,
    build_turns_for_trajectory,
    get_experiment_defs,
)
from .builders.helpers import iso, now, uid
from .constants import RNG_SEED

_RNG = random.Random(RNG_SEED)


class MockDataStore(object):
    """Singleton that lazily generates and holds all mock data.

    This class provides a centralized store for all mock data entities.
    Data is generated on first access and cached for subsequent calls.

    Usage:
        from ailens.app.mock import store
        projects = store.get_projects()
        trajectories = store.get_trajectories(experiment_id='exp-grpo-cc')
    """

    _instance = None  # type: Optional[MockDataStore]

    def __new__(cls):
        # type: () -> MockDataStore
        if cls._instance is None:
            cls._instance = super(MockDataStore, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def _ensure_init(self):
        # type: () -> None
        """Initialize all mock data if not already done."""
        if self._initialized:
            return
        self._initialized = True

        # Projects
        self.projects = build_projects()

        # Benchmarks and Tasks
        self.benchmarks = build_benchmarks()
        self.tasks = []  # type: List[Dict]
        for bm in self.benchmarks:
            self.tasks.extend(build_tasks_for_benchmark(bm["id"], bm["total_tasks"]))

        # Build task lookup by benchmark_id
        self._tasks_by_benchmark = {}  # type: Dict[str, List[Dict]]
        for t in self.tasks:
            bid = t["benchmark_id"]
            if bid not in self._tasks_by_benchmark:
                self._tasks_by_benchmark[bid] = []
            self._tasks_by_benchmark[bid].append(t)

        # Experiments, Iterations, Trajectories
        self.iterations = {}  # type: Dict[str, List[Dict]]
        self.trajectories = []  # type: List[Dict]
        self.annotations = []  # type: List[Dict]

        for ed in get_experiment_defs():
            bench_id = ed["benchmark_id"]
            exp_tasks = self._tasks_by_benchmark.get(bench_id, self.tasks[:20])
            iters, trajs, anns = build_iterations(ed["id"], ed, exp_tasks)
            self.iterations[ed["id"]] = iters
            self.trajectories.extend(trajs)
            self.annotations.extend(anns)

        self.experiments = build_experiments(self.iterations)

        # Traces
        self.traces = build_traces(self.trajectories, get_experiment_defs())

        # Agent Services
        self.agent_services = build_agent_services()

        # Agent Service Metrics
        self.agent_service_metrics = build_agent_service_metrics(self.agent_services)

        # Legacy agent metrics
        self.agent_metrics = build_agent_metrics()

        # Alerts
        self.alert_rules = build_alert_rules()
        self.active_alerts = build_active_alerts()

    # ── Project Accessors ──

    def get_projects(self):
        # type: () -> List[Dict]
        """Get all projects."""
        self._ensure_init()
        return self.projects

    def get_project(self, project_id):
        # type: (str) -> Optional[Dict]
        """Get a specific project by ID."""
        self._ensure_init()
        for p in self.projects:
            if p["id"] == project_id:
                return p
        return None

    def add_project(self, data):
        # type: (Dict) -> Dict
        """Add a new project."""
        self._ensure_init()
        return add_project(self.projects, data)

    # ── Benchmark Accessors ──

    def get_benchmarks(self, project_id=None):
        # type: (Optional[str]) -> List[Dict]
        """Get benchmarks, optionally filtered by project."""
        self._ensure_init()
        if project_id:
            return [b for b in self.benchmarks if b["project_id"] == project_id]
        return self.benchmarks

    def get_benchmark(self, benchmark_id):
        # type: (str) -> Optional[Dict]
        """Get a specific benchmark by ID."""
        self._ensure_init()
        for b in self.benchmarks:
            if b["id"] == benchmark_id:
                return b
        return None

    def get_tasks_by_benchmark(self, benchmark_id):
        # type: (str) -> List[Dict]
        """Get tasks for a benchmark."""
        self._ensure_init()
        return self._tasks_by_benchmark.get(benchmark_id, [])

    def get_tasks(self):
        # type: () -> List[Dict]
        """Get all tasks."""
        self._ensure_init()
        return self.tasks

    # ── Experiment Accessors ──

    def get_experiments(self, project_id=None):
        # type: (Optional[str]) -> List[Dict]
        """Get experiments, optionally filtered by project."""
        self._ensure_init()
        if project_id:
            return [e for e in self.experiments if e["project_id"] == project_id]
        return self.experiments

    def get_experiment(self, exp_id):
        # type: (str) -> Optional[Dict]
        """Get a specific experiment by ID."""
        self._ensure_init()
        for e in self.experiments:
            if e["id"] == exp_id:
                return e
        return None

    # ── Iteration Accessors ──

    def get_iterations(self, experiment_id):
        # type: (str) -> List[Dict]
        """Get iterations for an experiment."""
        self._ensure_init()
        return self.iterations.get(experiment_id, [])

    def get_iteration(self, iter_id):
        # type: (str) -> Optional[Dict]
        """Get a specific iteration by ID."""
        self._ensure_init()
        for iters in self.iterations.values():
            for it in iters:
                if it["id"] == iter_id:
                    return it
        return None

    # ── Trajectory Accessors ──

    def get_trajectories(self, experiment_id=None, project_id=None):
        # type: (Optional[str], Optional[str]) -> List[Dict]
        """Get trajectories, optionally filtered by experiment or project."""
        self._ensure_init()
        items = self.trajectories
        if experiment_id:
            items = [t for t in items if t["experiment_id"] == experiment_id]
        if project_id:
            proj_exp_ids = set(e["id"] for e in self.experiments if e["project_id"] == project_id)
            items = [t for t in items if t["experiment_id"] in proj_exp_ids]
        return items

    def get_trajectory(self, traj_id):
        # type: (str) -> Optional[Dict]
        """Get a specific trajectory by ID."""
        self._ensure_init()
        for t in self.trajectories:
            if t["id"] == traj_id:
                return t
        return None

    # ── Turn Accessors ──

    def get_turns(self, traj_id):
        # type: (str) -> List[Dict]
        """Get turns for a trajectory (generated on-demand)."""
        self._ensure_init()
        traj = self.get_trajectory(traj_id)
        if not traj:
            return []
        return build_turns_for_trajectory(traj)

    # ── Annotation Accessors ──

    def get_annotations(self):
        # type: () -> List[Dict]
        """Get all annotations."""
        self._ensure_init()
        return self.annotations

    def add_annotation(self, ann):
        # type: (Dict) -> Dict
        """Add a new annotation."""
        self._ensure_init()
        ann["id"] = uid(
            "ann",
            ann.get("trajectory_id", ""),
            str(len(self.annotations)),
        )
        ann["source"] = "manual"
        ann["created_at"] = iso(now())
        self.annotations.append(ann)
        return ann

    # ── Trace Accessors ──

    def get_traces(self):
        # type: () -> List[Dict]
        """Get all traces."""
        self._ensure_init()
        return self.traces

    def get_trace(self, trace_id):
        # type: (str) -> Optional[Dict]
        """Get a specific trace by ID."""
        self._ensure_init()
        for t in self.traces:
            if t["trace_id"] == trace_id:
                return t
        return None

    # ── Agent Service Accessors ──

    def get_agent_services(self, project_id=None):
        # type: (Optional[str]) -> List[Dict]
        """Get agent services, optionally filtered by project."""
        self._ensure_init()
        if project_id:
            return [s for s in self.agent_services if s["project_id"] == project_id]
        return self.agent_services

    def get_agent_service(self, service_id):
        # type: (str) -> Optional[Dict]
        """Get a specific agent service by ID."""
        self._ensure_init()
        for s in self.agent_services:
            if s["id"] == service_id:
                return s
        return None

    def get_agent_service_metrics(self, service_id):
        # type: (str) -> List[Dict]
        """Get metrics for an agent service."""
        self._ensure_init()
        return self.agent_service_metrics.get(service_id, [])

    def get_agent_metrics(self):
        # type: () -> List[Dict]
        """Get legacy agent metrics."""
        self._ensure_init()
        return self.agent_metrics

    # ── Alert Accessors ──

    def get_alert_rules(self):
        # type: () -> List[Dict]
        """Get all alert rules."""
        self._ensure_init()
        return self.alert_rules

    def add_alert_rule(self, rule):
        # type: (Dict) -> Dict
        """Add a new alert rule."""
        self._ensure_init()
        rule["id"] = "rule-{}".format(len(self.alert_rules) + 1)
        rule["enabled"] = True
        rule["created_at"] = iso(now())
        rule["updated_at"] = iso(now())
        self.alert_rules.append(rule)
        return rule

    def get_active_alerts(self):
        # type: () -> List[Dict]
        """Get all active alerts."""
        self._ensure_init()
        return self.active_alerts

    # ── SQL Simulation ──

    def execute_sql(self, sql, params=None):
        # type: (str, List[Any]) -> List[Tuple]
        """Execute raw SQL queries for aggregation.

        Note: In mock environment, simulate SQL execution using in-memory data.
        In production, this would execute real SQL against the database.
        """
        self._ensure_init()
        return self._simulate_sql_execution(sql, params or [])

    def _simulate_sql_execution(self, sql, params):
        # type: (str, List[Any]) -> List[Tuple]
        """Simulate SQL execution using mock data."""
        # Simple SQL parser for trajectory aggregation queries

        # Extract experiment_id from parameters
        if not params:
            return []
        experiment_id = params[0]

        # Get all trajectories for this experiment
        trajs = self.get_trajectories(experiment_id=experiment_id)
        if not trajs:
            return []

        # Parse basic SQL structure - this is a simplified parser for aggregation queries
        sql_lower = sql.lower()

        # Apply WHERE filters from SQL and parameters
        filtered_trajs = self._apply_sql_filters(trajs, sql, params)

        # Determine aggregation function and field
        agg_func, agg_field = self._parse_aggregation(sql)

        # Determine query type based on GROUP BY clause
        if "group by iteration_num" in sql_lower and "group by scaffold" not in sql_lower:
            # Simple aggregation by iteration_num only
            grouped = self._group_trajectories_by_iteration(filtered_trajs)
            results = []
            for iteration_num, group_trajs in grouped.items():
                agg_value = self._apply_aggregation(agg_func, agg_field, group_trajs)
                if agg_value is not None:
                    results.append((iteration_num, agg_value))
            results.sort(key=lambda x: x[0])  # Sort by iteration_num
            return results
        elif any(
            dim in sql_lower
            for dim in ["group by scaffold", "group by tool_schema", "group by language", "group by system_prompt"]
        ):
            # Split query by specific dimension
            split_dim = self._parse_split_dimension(sql)
            grouped = self._group_trajectories_by_split(filtered_trajs, split_dim)
            results = []
            for (split_value, iteration_num), group_trajs in grouped.items():
                agg_value = self._apply_aggregation(agg_func, agg_field, group_trajs)
                if agg_value is not None:
                    results.append((split_value, iteration_num, agg_value))
            results.sort(key=lambda x: x[1])  # Sort by iteration_num
            return results
        else:
            # Legacy: Group by all dimensions (for backward compatibility)
            grouped = self._group_trajectories(filtered_trajs)
            results = []
            for (scaffold, tool_schema, language, system_prompt, iteration_num), group_trajs in grouped.items():
                agg_value = self._apply_aggregation(agg_func, agg_field, group_trajs)
                if agg_value is not None:
                    results.append((scaffold, tool_schema, language, system_prompt, iteration_num, agg_value))
            results.sort(key=lambda x: x[4])  # Sort by iteration_num (index 4)
            return results

    def _apply_sql_filters(self, trajs, sql, params):
        # type: (List[Dict], str, List[Any]) -> List[Dict]
        """Apply WHERE clause filters to trajectories."""
        filtered = list(trajs)  # Start with all trajectories
        param_idx = 1  # Skip experiment_id (index 0)

        sql_lower = sql.lower()

        # Apply passed condition filter
        if "passed = true" in sql_lower:
            filtered = [t for t in filtered if t.get("passed") is True]
        elif "passed = false" in sql_lower:
            filtered = [t for t in filtered if t.get("passed") is False]

        # Apply parameter-based filters (scaffold, tool_schema, language, system_prompt)
        if "scaffold = ?" in sql_lower and param_idx < len(params):
            scaffold_val = params[param_idx]
            filtered = [t for t in filtered if t.get("scaffold") == scaffold_val]
            param_idx += 1

        if "tool_schema = ?" in sql_lower and param_idx < len(params):
            tool_schema_val = params[param_idx]
            filtered = [t for t in filtered if t.get("tool_schema") == tool_schema_val]
            param_idx += 1

        if "task_language = ?" in sql_lower and param_idx < len(params):
            language_val = params[param_idx]
            filtered = [t for t in filtered if t.get("task_language") == language_val]
            param_idx += 1

        if "system_prompt = ?" in sql_lower and param_idx < len(params):
            system_prompt_val = params[param_idx]
            filtered = [t for t in filtered if t.get("system_prompt") == system_prompt_val]
            param_idx += 1

        # Apply iteration range filter (BETWEEN)
        if "iteration_num between ? and ?" in sql_lower and param_idx + 1 < len(params):
            lo = params[param_idx]
            hi = params[param_idx + 1]
            filtered = [t for t in filtered if lo <= t.get("iteration_num", 0) <= hi]

        return filtered

    def _parse_aggregation(self, sql):
        # type: (str) -> Tuple[str, Optional[str]]
        """Parse aggregation function and field from SQL."""
        sql_lower = sql.lower()

        if "count(*)" in sql_lower:
            return ("COUNT", None)
        elif "avg(reward)" in sql_lower:
            return ("AVG", "reward")
        elif "sum(total_turns)" in sql_lower:
            return ("SUM", "total_turns")
        elif "sum(duration_ms)" in sql_lower:
            return ("SUM", "duration_ms")
        elif "avg(total_turns)" in sql_lower:
            return ("AVG", "total_turns")
        elif "avg(duration_ms)" in sql_lower:
            return ("AVG", "duration_ms")
        elif "min(total_turns)" in sql_lower:
            return ("MIN", "total_turns")
        elif "max(total_turns)" in sql_lower:
            return ("MAX", "total_turns")
        elif "min(reward)" in sql_lower:
            return ("MIN", "reward")
        elif "max(reward)" in sql_lower:
            return ("MAX", "reward")
        elif "stddev(reward)" in sql_lower:
            return ("STDDEV", "reward")
        elif "case when passed" in sql_lower:
            return ("PASS_RATE", "passed")
        else:
            return ("COUNT", None)  # Default fallback

    def _group_trajectories(self, trajs):
        # type: (List[Dict]) -> Dict[Tuple[str, str, str, str, int], List[Dict]]
        """Group trajectories by (scaffold, tool_schema, language, system_prompt, iteration_num)."""
        grouped = {}
        for t in trajs:
            key = (
                t.get("scaffold", "unknown"),
                t.get("tool_schema", "unknown"),
                t.get("task_language", "unknown"),
                t.get("system_prompt", "unknown"),
                t.get("iteration_num", 0),
            )
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(t)
        return grouped

    def _group_trajectories_by_iteration(self, trajs):
        # type: (List[Dict]) -> Dict[int, List[Dict]]
        """Group trajectories by iteration_num only."""
        grouped = {}
        for t in trajs:
            iteration_num = t.get("iteration_num", 0)
            if iteration_num not in grouped:
                grouped[iteration_num] = []
            grouped[iteration_num].append(t)
        return grouped

    def _group_trajectories_by_split(self, trajs, split_dim):
        # type: (List[Dict], str) -> Dict[Tuple[str, int], List[Dict]]
        """Group trajectories by (split_dimension_value, iteration_num)."""
        grouped = {}
        for t in trajs:
            if split_dim == "scaffold":
                split_value = t.get("scaffold", "unknown")
            elif split_dim == "tool_schema":
                split_value = t.get("tool_schema", "unknown")
            elif split_dim == "language":
                split_value = t.get("task_language", "unknown")
            elif split_dim == "system_prompt":
                split_value = t.get("system_prompt", "unknown")
            else:
                continue

            iteration_num = t.get("iteration_num", 0)
            key = (split_value, iteration_num)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(t)
        return grouped

    def _parse_split_dimension(self, sql):
        # type: (str) -> str
        """Parse which dimension we're splitting by from GROUP BY clause."""
        sql_lower = sql.lower()
        if "group by scaffold" in sql_lower:
            return "scaffold"
        elif "group by tool_schema" in sql_lower:
            return "tool_schema"
        elif "group by language" in sql_lower:
            return "language"
        elif "group by system_prompt" in sql_lower:
            return "system_prompt"
        else:
            return "iteration_num"

    def _apply_aggregation(self, agg_func, agg_field, trajs):
        # type: (str, Optional[str], List[Dict]) -> Optional[float]
        """Apply aggregation function to trajectory group."""
        if not trajs:
            return None

        if agg_func == "COUNT":
            return float(len(trajs))  # Will be converted to int in formatting

        if agg_func == "PASS_RATE":
            # CASE WHEN passed THEN 1.0 ELSE 0.0 END
            return round(sum(1.0 if t.get("passed") else 0.0 for t in trajs) / len(trajs), 4)

        if agg_field is None:
            return None

        # Extract field values
        values = []
        for t in trajs:
            if agg_field == "reward":
                val = t.get("reward", 0.0)
            elif agg_field == "total_turns":
                val = t.get("total_turns", 0)
            elif agg_field == "duration_ms":
                val = t.get("duration_ms", 0)
            else:
                continue
            values.append(float(val))

        if not values:
            return None

        if agg_func == "AVG":
            avg_val = sum(values) / len(values)
            # Apply same rounding as original implementation
            if agg_field == "reward":
                return round(avg_val, 4)  # mean_reward is rounded to 4 decimals
            else:
                return round(avg_val, 1)  # mean_turns etc. are rounded to 1 decimal
        elif agg_func == "SUM":
            return sum(values)
        elif agg_func == "MIN":
            return min(values)
        elif agg_func == "MAX":
            return max(values)
        elif agg_func == "STDDEV":
            if len(values) < 2:
                return 0.0
            mean = sum(values) / len(values)
            variance = sum((x - mean) ** 2 for x in values) / len(values)
            return round(variance**0.5, 4)  # Round stddev to 4 decimals
        else:
            return None


# Module-level convenience singleton
store = MockDataStore()
