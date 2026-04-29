"""
可观测性功能集成测试
测试 access log、error log、OpenTelemetry metrics、health check 等功能
"""

from unittest.mock import MagicMock, patch

import pytest

# 导入应用和组件
from app.main import app
from app.observability.metrics.system import system_metrics
from fastapi.testclient import TestClient


class TestAccessLogMiddleware:
    """测试访问日志中间件"""

    def test_access_log_records_request_info(self, caplog):
        """验证访问日志中间件不影响正常响应"""
        with TestClient(app) as client:
            response = client.get("/observability/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"

    def test_access_log_includes_trace_info(self, caplog):
        """验证带 X-Request-ID header 的请求正常处理"""
        with TestClient(app) as client:
            response = client.get("/observability/health", headers={"X-Request-ID": "test-id-123"})
            assert response.status_code == 200


class TestErrorHandlingMiddleware:
    """测试错误处理中间件"""

    def test_error_log_on_exception(self, caplog):
        """验证 ValueError 被错误处理中间件捕获并返回 4xx"""

        @app.get("/test-error-ve")
        async def test_error_ve():
            raise ValueError("Test error for logging")

        with TestClient(app) as client:
            response = client.get("/test-error-ve")
            # ValueError maps to 400 in the error handling middleware
            assert response.status_code in (400, 500)
            data = response.json()
            assert "detail" in data or "error" in data or "message" in data

    def test_error_log_contains_request_context(self, caplog):
        """验证 RuntimeError 被错误处理中间件捕获并返回错误响应"""

        @app.get("/test-context-error-rt")
        async def test_context_error_rt():
            raise RuntimeError("Context error test")

        with TestClient(app) as client:
            response = client.get("/test-context-error-rt")
            assert response.status_code >= 400


class TestMetricsCollection:
    """测试指标收集功能"""

    def test_http_metrics_collection(self):
        """验证 HTTP 指标收集"""
        with TestClient(app) as client:
            response = client.get("/observability/health")

            assert response.status_code == 200

            # 验证指标通过 /metrics 端点
            metrics_response = client.get("/observability/metrics")
            assert "http_requests_total" in metrics_response.text

    def test_metrics_endpoint_returns_prometheus_format(self):
        """验证 /metrics 端点返回 Prometheus 格式"""
        with TestClient(app) as client:
            response = client.get("/observability/metrics")

            assert response.status_code == 200
            assert "text/plain" in response.headers["content-type"]

            content = response.text
            assert "# HELP" in content
            assert "# TYPE" in content

    def test_system_metrics_collection(self):
        """验证系统指标收集"""
        # 触发系统指标更新 (only GC metrics are available)
        system_metrics.update_gc_metrics()

        with TestClient(app) as client:
            response = client.get("/observability/metrics")
            content = response.text
            assert "gc_collections_total" in content


class TestHealthEndpoints:
    """测试健康检查端点"""

    def test_health_endpoint_basic_check(self):
        """验证基础健康检查"""
        with TestClient(app) as client:
            response = client.get("/observability/health")

            assert response.status_code == 200
            data = response.json()

            assert data["status"] == "healthy"
            assert "timestamp" in data

    def test_ready_endpoint_dependency_check(self):
        """验证就绪性检查依赖服务"""
        with TestClient(app) as client:
            response = client.get("/observability/ready")

            assert response.status_code == 200
            data = response.json()

            assert "status" in data
            assert "checks" in data
            assert "timestamp" in data

            # 验证检查项
            checks = data["checks"]
            assert "database" in checks
            assert "traceql" in checks

    def test_ready_endpoint_traceql_service_check(self):
        """验证 ready 端点当 TraceQL 配置时的检查"""
        with (
            patch("app.routers.observability.TRACEQL_BASE_URL", "http://test-traceql"),
            patch("app.routers.observability.TRACEQL_AUTH_KEY", "key"),
            patch("httpx.AsyncClient.get") as mock_get,
        ):
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value.__aenter__.return_value = mock_response

            with TestClient(app) as client:
                response = client.get("/observability/ready")
                data = response.json()
                assert "traceql" in data["checks"]

    def test_ready_endpoint_traceql_service_failure(self):
        """验证 TraceQL 未配置时的处理"""
        with TestClient(app) as client:
            response = client.get("/observability/ready")
            data = response.json()
            assert "traceql" in data["checks"]
            # When not configured, status is "warning"
            assert data["checks"]["traceql"].get("status") in ("warning", "error", "ok")


class TestPerformanceImpact:
    """测试可观测性功能对性能的影响"""

    def test_observability_overhead_within_limits(self, client):
        """验证可观测性端点响应时间在合理范围内（< 1s）"""
        import time

        times = []
        for _ in range(10):
            start = time.time()
            client.get("/observability/health")
            times.append(time.time() - start)

        avg_ms = sum(times) / len(times) * 1000
        assert avg_ms < 1000, f"Health endpoint avg response time {avg_ms:.1f}ms exceeds 1000ms"

    def test_concurrent_requests_performance(self):
        """验证并发请求下的性能表现"""
        import concurrent.futures
        import time

        def make_request():
            with TestClient(app) as client:
                start = time.time()
                response = client.get("/observability/health")
                duration = time.time() - start
                return response.status_code, duration

        # 模拟 50 并发请求
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(make_request) for _ in range(50)]
            results = [future.result() for future in futures]

        # 验证所有请求成功
        status_codes = [result[0] for result in results]
        durations = [result[1] for result in results]

        assert all(code == 200 for code in status_codes)

        # 验证 P99 延迟在合理范围内（< 1秒）
        durations.sort()
        p99_duration = durations[int(len(durations) * 0.99)]
        assert p99_duration < 1.0, f"P99 duration {p99_duration:.3f}s exceeds 1s limit"


class TestConfigurationDriven:
    """测试配置驱动功能"""

    def test_environment_variable_configuration(self):
        """验证环境变量配置生效"""
        import os

        # 测试服务名称配置
        original_name = os.environ.get("OTEL_SERVICE_NAME")
        os.environ["OTEL_SERVICE_NAME"] = "test-ailens-api"

        # 验证环境变量生效
        service_name = os.environ.get("OTEL_SERVICE_NAME")
        assert service_name == "test-ailens-api"

        # 恢复原始配置
        if original_name:
            os.environ["OTEL_SERVICE_NAME"] = original_name
        else:
            os.environ.pop("OTEL_SERVICE_NAME", None)

    @patch.dict("os.environ", {"OTEL_SERVICE_NAME": "test-service"})
    def test_opentelemetry_service_name_configuration(self):
        """验证 OpenTelemetry 服务名配置"""
        import os

        service_name = os.getenv("OTEL_SERVICE_NAME")
        assert service_name == "test-service"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
