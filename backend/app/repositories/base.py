"""Repository Protocol definitions.

These interfaces define the data access contracts that routers depend on,
enabling dependency inversion and independent testing.
"""

from typing import Dict, List, Optional

from typing_extensions import Protocol


class ProjectRepository(Protocol):
    """Project data access interface."""

    def get_projects(self) -> List[Dict]:
        """Get all projects."""
        ...

    def get_project(self, project_id: str) -> Optional[Dict]:
        """Get a single project by ID."""
        ...

    def add_project(self, data: Dict) -> Dict:
        """Create a new project."""
        ...


class ExperimentRepository(Protocol):
    """Experiment data access interface."""

    def get_experiments(self, project_id: Optional[str] = None) -> List[Dict]:
        """Get experiments, optionally filtered by project."""
        ...

    def get_experiment(self, experiment_id: str) -> Optional[Dict]:
        """Get a single experiment by ID."""
        ...


class IterationRepository(Protocol):
    """Iteration data access interface."""

    def get_iterations(self, experiment_id: str) -> List[Dict]:
        """Get all iterations for an experiment."""
        ...

    def get_iteration(self, iteration_id: str) -> Optional[Dict]:
        """Get a single iteration by ID."""
        ...


class TrajectoryRepository(Protocol):
    """Trajectory data access interface."""

    def get_trajectories(
        self,
        experiment_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> List[Dict]:
        """Get trajectories, optionally filtered by experiment or project."""
        ...

    def get_trajectory(self, trajectory_id: str) -> Optional[Dict]:
        """Get a single trajectory by ID."""
        ...

    def get_turns(self, trajectory_id: str) -> List[Dict]:
        """Get turns for a trajectory."""
        ...


class TraceRepository(Protocol):
    """Trace data access interface."""

    def get_traces(self) -> List[Dict]:
        """Get all traces."""
        ...

    def get_trace(self, trace_id: str) -> Optional[Dict]:
        """Get a single trace by ID."""
        ...


class AgentServiceRepository(Protocol):
    """Agent service data access interface."""

    def get_agent_services(
        self,
        project_id: Optional[str] = None,
    ) -> List[Dict]:
        """Get agent services, optionally filtered by project."""
        ...

    def get_agent_service(self, service_id: str) -> Optional[Dict]:
        """Get a single agent service by ID."""
        ...

    def get_agent_service_metrics(self, service_id: str) -> List[Dict]:
        """Get metrics for an agent service."""
        ...

    def get_agent_metrics(self) -> List[Dict]:
        """Get all agent metrics."""
        ...


class AlertRepository(Protocol):
    """Alert data access interface."""

    def get_alert_rules(self) -> List[Dict]:
        """Get all alert rules."""
        ...

    def add_alert_rule(self, rule: Dict) -> Dict:
        """Create a new alert rule."""
        ...

    def get_active_alerts(self) -> List[Dict]:
        """Get active alerts."""
        ...


class AnnotationRepository(Protocol):
    """Annotation data access interface."""

    def get_annotations(self) -> List[Dict]:
        """Get all annotations."""
        ...

    def add_annotation(self, annotation: Dict) -> Dict:
        """Create a new annotation."""
        ...


class TaskRepository(Protocol):
    """Task data access interface."""

    def get_tasks(self) -> List[Dict]:
        """Get all tasks."""
        ...

    def get_tasks_by_benchmark(self, benchmark_id: str) -> List[Dict]:
        """Get tasks for a benchmark."""
        ...


class MetricRepository(Protocol):
    """Metric data access interface (for query API)."""

    def get_experiments(self, project_id: Optional[str] = None) -> List[Dict]:
        """Get experiments for metric queries."""
        ...

    def get_trajectories(
        self,
        experiment_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> List[Dict]:
        """Get trajectories for metric queries."""
        ...
