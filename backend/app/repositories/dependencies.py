"""Dependency injection providers for repositories.

This module provides FastAPI Depends functions for each repository,
allowing routers to receive injected implementations.

Default implementation uses the mock store, which can be replaced
with real database implementations in production.
"""

import os

from fastapi import Depends

from .base import (
    AgentServiceRepository,
    AlertRepository,
    AnnotationRepository,
    ExperimentRepository,
    IterationRepository,
    MetricRepository,
    ProjectRepository,
    TaskRepository,
    TraceRepository,
    TrajectoryRepository,
)


def _get_store():
    """Lazy import and return the mock store singleton."""
    from ..mock import store

    return store


# ── Repository Providers ──


def get_project_repo() -> ProjectRepository:
    """Provide ProjectRepository implementation."""
    return _get_store()


def get_experiment_repo() -> ExperimentRepository:
    """Provide ExperimentRepository implementation."""
    if os.environ.get("TRACEQL_BASE_URL"):
        from .traceql_experiment import TraceQLExperimentRepository

        return TraceQLExperimentRepository()
    return _get_store()


def get_iteration_repo() -> IterationRepository:
    """Provide IterationRepository implementation."""
    if os.environ.get("TRACEQL_BASE_URL"):
        from .traceql_experiment import TraceQLIterationRepository

        return TraceQLIterationRepository()
    return _get_store()


def get_trajectory_repo() -> TrajectoryRepository:
    """Provide TrajectoryRepository implementation."""
    return _get_store()


def get_trace_repo() -> TraceRepository:
    """Provide TraceRepository implementation."""
    return _get_store()


def get_agent_service_repo() -> AgentServiceRepository:
    """Provide AgentServiceRepository implementation."""
    return _get_store()


def get_alert_repo() -> AlertRepository:
    """Provide AlertRepository implementation."""
    return _get_store()


def get_annotation_repo() -> AnnotationRepository:
    """Provide AnnotationRepository implementation."""
    return _get_store()


def get_task_repo() -> TaskRepository:
    """Provide TaskRepository implementation."""
    return _get_store()


def get_metric_repo() -> MetricRepository:
    """Provide MetricRepository implementation (for query API)."""
    return _get_store()


# ── Convenience: Combined Repository ──


class RepositoryContainer:
    """Container providing all repositories.

    Useful for routers that need multiple repository types.
    """

    def __init__(
        self,
        project: ProjectRepository = Depends(get_project_repo),
        experiment: ExperimentRepository = Depends(get_experiment_repo),
        iteration: IterationRepository = Depends(get_iteration_repo),
        trajectory: TrajectoryRepository = Depends(get_trajectory_repo),
        trace: TraceRepository = Depends(get_trace_repo),
        agent_service: AgentServiceRepository = Depends(get_agent_service_repo),
        alert: AlertRepository = Depends(get_alert_repo),
        annotation: AnnotationRepository = Depends(get_annotation_repo),
        task: TaskRepository = Depends(get_task_repo),
        metric: MetricRepository = Depends(get_metric_repo),
    ):
        self.project = project
        self.experiment = experiment
        self.iteration = iteration
        self.trajectory = trajectory
        self.trace = trace
        self.agent_service = agent_service
        self.alert = alert
        self.annotation = annotation
        self.task = task
        self.metric = metric


def get_repositories() -> RepositoryContainer:
    """Provide all repositories in a single container."""
    return RepositoryContainer()
