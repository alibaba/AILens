"""API tests for projects endpoints."""


class TestProjectsAPI:
    def test_list_projects(self, client):
        r = client.get("/api/v1/projects")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    def test_list_projects_trailing_slash(self, client):
        r = client.get("/api/v1/projects/")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 2

    def test_get_project_by_id(self, client):
        r = client.get("/api/v1/projects/proj-code-agent-v2")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == "proj-code-agent-v2"
        assert data["name"] == "Code Agent v2"
        assert "tags" in data
        assert "created_at" in data

    def test_get_project_not_found(self, client):
        r = client.get("/api/v1/projects/nonexistent")
        assert r.status_code == 404

    def test_create_project(self, client):
        r = client.post(
            "/api/v1/projects/",
            json={
                "name": "Test Project",
                "description": "Created in test",
                "owner": "tester",
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "Test Project"
        assert "id" in data
