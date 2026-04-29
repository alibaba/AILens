"""Tests for PromQL Rank API — /api/v1/query/rank"""

RANK_URL = "/api/v1/query/rank"
EXP_ID = "exp-grpo-cc"


class TestPromQLRank:
    """PromQL Rank API 测试"""

    def test_rank_bottom_10(self, client):
        """测试 Bottom 10 查询"""
        response = client.post(
            RANK_URL,
            json={
                "query": 'experiment_task_pass_rate{experiment_id="' + EXP_ID + '"} by (task_id)',
                "sort_by": "value",
                "sort_order": "asc",
                "limit": 10,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 10
        assert data["sort_order"] == "asc"
        assert data["sort_by"] == "value"
        assert data["limit"] == 10

        # Verify response structure
        for item in data["items"]:
            assert "labels" in item
            assert "task_id" in item["labels"]
            assert "value" in item
            assert "rank" in item
            assert isinstance(item["value"], float)
            assert isinstance(item["rank"], int)

    def test_rank_top_10(self, client):
        """测试 Top 10 查询"""
        response = client.post(
            RANK_URL,
            json={
                "query": 'experiment_task_mean_reward{experiment_id="' + EXP_ID + '"} by (task_id)',
                "sort_by": "value",
                "sort_order": "desc",
                "limit": 10,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 10
        assert data["sort_order"] == "desc"
        assert data["sort_by"] == "value"
        assert data["limit"] == 10

    def test_rank_ascending_order(self, client):
        """测试升序排序结果正确"""
        response = client.post(
            RANK_URL,
            json={
                "query": 'experiment_task_pass_rate{experiment_id="' + EXP_ID + '"} by (task_id)',
                "sort_by": "value",
                "sort_order": "asc",
                "limit": 5,
            },
        )
        data = response.json()
        items = data["items"]

        # Verify ascending order
        for i in range(len(items) - 1):
            assert items[i]["value"] <= items[i + 1]["value"]

        # Verify rank is sequential
        for i, item in enumerate(items):
            assert item["rank"] == i + 1

    def test_rank_descending_order(self, client):
        """测试降序排序结果正确"""
        response = client.post(
            RANK_URL,
            json={
                "query": 'experiment_task_mean_reward{experiment_id="' + EXP_ID + '"} by (task_id)',
                "sort_by": "value",
                "sort_order": "desc",
                "limit": 5,
            },
        )
        data = response.json()
        items = data["items"]

        # Verify descending order
        for i in range(len(items) - 1):
            assert items[i]["value"] >= items[i + 1]["value"]

    def test_rank_limit_respected(self, client):
        """测试 limit 参数被正确限制"""
        response = client.post(
            RANK_URL,
            json={
                "query": 'experiment_task_pass_rate{experiment_id="' + EXP_ID + '"} by (task_id)',
                "sort_by": "value",
                "sort_order": "asc",
                "limit": 3,
            },
        )
        data = response.json()
        assert len(data["items"]) <= 3

    def test_rank_empty_query(self, client):
        """测试空查询返回空结果"""
        response = client.post(RANK_URL, json={"query": "", "sort_by": "value", "sort_order": "asc", "limit": 10})
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []

    def test_rank_no_experiment_id(self, client):
        """测试缺少 experiment_id 返回空结果"""
        response = client.post(
            RANK_URL,
            json={
                "query": "experiment_task_pass_rate{} by (task_id)",
                "sort_by": "value",
                "sort_order": "asc",
                "limit": 10,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []

    def test_rank_invalid_metric(self, client):
        """测试不支持的指标返回空结果"""
        response = client.post(
            RANK_URL,
            json={
                "query": 'experiment_mean_reward{experiment_id="' + EXP_ID + '"} by (task_id)',
                "sort_by": "value",
                "sort_order": "asc",
                "limit": 10,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []

    def test_rank_nonexistent_experiment(self, client):
        """测试不存在的实验返回空结果"""
        response = client.post(
            RANK_URL,
            json={
                "query": 'experiment_task_pass_rate{experiment_id="nonexistent"} by (task_id)',
                "sort_by": "value",
                "sort_order": "asc",
                "limit": 10,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []

    def test_rank_pass_rate_values_in_range(self, client):
        """测试 pass_rate 值在 0-1 范围内"""
        response = client.post(
            RANK_URL,
            json={
                "query": 'experiment_task_pass_rate{experiment_id="' + EXP_ID + '"} by (task_id)',
                "sort_by": "value",
                "sort_order": "asc",
                "limit": 20,
            },
        )
        data = response.json()
        for item in data["items"]:
            assert 0.0 <= item["value"] <= 1.0

    def test_rank_response_structure(self, client):
        """测试响应结构完整"""
        response = client.post(
            RANK_URL,
            json={
                "query": 'experiment_task_pass_rate{experiment_id="' + EXP_ID + '"} by (task_id)',
                "sort_by": "value",
                "sort_order": "asc",
                "limit": 5,
            },
        )
        data = response.json()

        # Check top-level fields
        assert "query" in data
        assert "sort_by" in data
        assert "sort_order" in data
        assert "limit" in data
        assert "items" in data

        # Check types
        assert isinstance(data["query"], str)
        assert isinstance(data["sort_by"], str)
        assert isinstance(data["sort_order"], str)
        assert isinstance(data["limit"], int)
        assert isinstance(data["items"], list)
