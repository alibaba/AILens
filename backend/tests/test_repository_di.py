"""Unit tests for router dependency injection.

Tests that routers can work with mock repository implementations
independently of the real mock store.
"""

from typing import Dict, List, Optional

from app.routers.experiments import router as experiments_router
from app.routers.projects import router as projects_router
from fastapi import FastAPI
from fastapi.testclient import TestClient


class MockProjectRepo:
    """Mock ProjectRepository for testing."""

    def get_projects(self) -> List[Dict]:
        return [
            {"id": "proj-1", "name": "Test Project 1"},
            {"id": "proj-2", "name": "Test Project 2"},
        ]

    def get_project(self, project_id: str) -> Optional[Dict]:
        if project_id == "proj-1":
            return {"id": "proj-1", "name": "Test Project 1"}
        return None

    def add_project(self, data: Dict) -> Dict:
        return {"id": "proj-new", "name": data.get("name", "")}


class MockExperimentRepo:
    """Mock ExperimentRepository for testing."""

    def get_experiments(self, project_id: Optional[str] = None) -> List[Dict]:
        return [
            {"id": "exp-1", "name": "Test Experiment 1", "project_id": "proj-1"},
            {"id": "exp-2", "name": "Test Experiment 2", "project_id": "proj-1"},
        ]

    def get_experiment(self, experiment_id: str) -> Optional[Dict]:
        if experiment_id == "exp-1":
            return {"id": "exp-1", "name": "Test Experiment 1"}
        return None


class MockTrajectoryRepo:
    """Mock TrajectoryRepository for testing."""

    def get_trajectories(
        self,
        experiment_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> List[Dict]:
        return [
            {"id": "traj-1", "experiment_id": "exp-1", "reward": 0.5},
            {"id": "traj-2", "experiment_id": "exp-1", "reward": 0.8},
        ]

    def get_trajectory(self, trajectory_id: str) -> Optional[Dict]:
        if trajectory_id == "traj-1":
            return {"id": "traj-1", "experiment_id": "exp-1", "reward": 0.5}
        return None

    def get_turns(self, trajectory_id: str) -> List[Dict]:
        return [{"id": "turn-1", "trajectory_id": trajectory_id}]

    def get_iterations(self, experiment_id: str) -> List[Dict]:
        return [{"id": "iter-1", "experiment_id": experiment_id}]


# ── Tests ──


class TestRouterDependencyInjection:
    """Tests for router dependency injection."""

    def test_projects_router_with_mock_repo(self):
        """Projects router works with mock repository."""
        app = FastAPI()
        app.dependency_overrides[
            lambda: None  # placeholder
        ] = lambda: MockProjectRepo()

        # Override the dependency
        from app.repositories.dependencies import get_project_repo

        app.dependency_overrides[get_project_repo] = lambda: MockProjectRepo()

        app.include_router(projects_router)
        client = TestClient(app)

        # List projects
        resp = client.get("/projects")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

        # Get single project
        resp = client.get("/projects/proj-1")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Test Project 1"

        # Project not found
        resp = client.get("/projects/not-exist")
        assert resp.status_code == 404

    def test_experiments_router_with_mock_repo(self):
        """Experiments router works with mock repositories."""
        app = FastAPI()

        from app.repositories.dependencies import (
            get_experiment_repo,
            get_trajectory_repo,
        )

        app.dependency_overrides[get_experiment_repo] = lambda: MockExperimentRepo()
        app.dependency_overrides[get_trajectory_repo] = lambda: MockTrajectoryRepo()

        app.include_router(experiments_router)
        client = TestClient(app)

        # List experiments
        resp = client.get("/experiments")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2

        # Get single experiment
        resp = client.get("/experiments/exp-1")
        assert resp.status_code == 200

        # Experiment not found
        resp = client.get("/experiments/not-exist")
        assert resp.status_code == 404

    def test_repository_protocol_compliance(self):
        """Mock repos satisfy Protocol contracts."""
        # Python's Protocol doesn't enforce at runtime, but we can
        # verify that the mock has all required methods

        mock_project = MockProjectRepo()
        assert hasattr(mock_project, "get_projects")
        assert hasattr(mock_project, "get_project")
        assert hasattr(mock_project, "add_project")

        mock_exp = MockExperimentRepo()
        assert hasattr(mock_exp, "get_experiments")
        assert hasattr(mock_exp, "get_experiment")

        mock_traj = MockTrajectoryRepo()
        assert hasattr(mock_traj, "get_trajectories")
        assert hasattr(mock_traj, "get_trajectory")
        assert hasattr(mock_traj, "get_turns")
