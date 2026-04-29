"""API tests for agent services endpoints."""


class TestAgentServicesAPI:
    def test_list_agent_services(self, client):
        r = client.get("/api/v1/agent-services")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 2

    def test_list_agent_services_by_project(self, client):
        r = client.get(
            "/api/v1/agent-services",
            params={"project_id": "proj-code-agent-v2"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 2
        for s in data["items"]:
            assert s["project_id"] == "proj-code-agent-v2"

    def test_get_agent_service(self, client):
        r = client.get("/api/v1/agent-services/svc-coding-prod")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == "svc-coding-prod"
        assert data["name"] == "coding-agent-prod"
        assert data["environment"] == "production"

    def test_get_agent_service_not_found(self, client):
        r = client.get("/api/v1/agent-services/nonexistent")
        assert r.status_code == 404

    def test_get_agent_service_metrics(self, client):
        r = client.get("/api/v1/agent-services/svc-coding-prod/metrics")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] > 0
        assert "series" in data

    def test_get_agent_service_metrics_by_category(self, client):
        r = client.get(
            "/api/v1/agent-services/svc-coding-prod/metrics",
            params={"category": "llm"},
        )
        assert r.status_code == 200
        data = r.json()
        for s in data["series"]:
            assert s["category"] == "llm"

    def test_get_agent_service_metrics_not_found(self, client):
        r = client.get("/api/v1/agent-services/nonexistent/metrics")
        assert r.status_code == 404
