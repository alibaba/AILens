"""Tests for Tasks API offline functionality.

Verifies that Tasks API endpoints return 501 Not Implemented status
when the feature is offline.
"""

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


class TestTasksAPIOffline:
    """Test Tasks API endpoints return 501 when offline."""

    def test_get_task_history_returns_501(self):
        """Test that task history endpoint returns 501 Not Implemented."""
        response = client.get("/api/v1/tasks/test-task-123/history")

        assert response.status_code == 501
        assert response.json()["detail"]["message"] == "Tasks功能暂时下线，正在重新建设中"
        assert response.json()["detail"]["status"] == "under_construction"
        assert response.json()["detail"]["code"] == "FEATURE_OFFLINE"

    def test_list_tasks_returns_501(self):
        """Test that list tasks endpoint returns 501 Not Implemented."""
        response = client.get("/api/v1/tasks/")

        assert response.status_code == 501
        assert response.json()["detail"]["message"] == "Tasks功能暂时下线，正在重新建设中"
        assert response.json()["detail"]["status"] == "under_construction"
        assert response.json()["detail"]["code"] == "FEATURE_OFFLINE"

    def test_get_task_returns_501(self):
        """Test that get single task endpoint returns 501 Not Implemented."""
        response = client.get("/api/v1/tasks/test-task-123")

        assert response.status_code == 501
        assert response.json()["detail"]["message"] == "Tasks功能暂时下线，正在重新建设中"
        assert response.json()["detail"]["status"] == "under_construction"
        assert response.json()["detail"]["code"] == "FEATURE_OFFLINE"

    def test_tasks_api_with_query_params(self):
        """Test that tasks API with query params also returns 501."""
        response = client.get(
            "/api/v1/tasks/test-task-123/history", params={"experiment_id": "exp-123", "project_id": "proj-123"}
        )

        assert response.status_code == 501
        assert "under_construction" in response.json()["detail"]["status"]
