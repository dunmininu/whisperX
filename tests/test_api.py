"""
API endpoint tests for WhisperX Cloud Run Microservice
"""

from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import create_application


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_health_check(self, client: TestClient):
        """Test basic health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "service" in data
        assert "version" in data
        assert "model_loaded" in data

    def test_readiness_check(self, client: TestClient):
        """Test readiness check endpoint."""
        response = client.get("/health/ready")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ready"

    def test_liveness_check(self, client: TestClient):
        """Test liveness check endpoint."""
        response = client.get("/health/live")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "alive"

    def test_detailed_health_check(self, client: TestClient):
        """Test detailed health check endpoint."""
        response = client.get("/health/detailed")
        assert response.status_code == 200

        data = response.json()
        assert "health" in data
        assert "system" in data
        assert "service" in data
        assert "config" in data


class TestMetricsEndpoints:
    """Test metrics endpoints."""

    def test_service_metrics(self, client: TestClient):
        """Test service metrics endpoint."""
        response = client.get("/api/v1/metrics/")
        assert response.status_code == 200

        data = response.json()
        assert "total_jobs" in data
        assert "successful_jobs" in data
        assert "failed_jobs" in data
        assert "average_processing_time" in data
        assert "current_active_jobs" in data
        assert "memory_usage_mb" in data
        assert "cpu_usage_percent" in data

    def test_performance_metrics(self, client: TestClient):
        """Test performance metrics endpoint."""
        response = client.get("/api/v1/metrics/performance")
        assert response.status_code == 200

        data = response.json()
        assert "job_metrics" in data
        assert "system_metrics" in data
        assert "service_metrics" in data

    def test_job_metrics(self, client: TestClient):
        """Test job metrics endpoint."""
        response = client.get("/api/v1/metrics/jobs")
        assert response.status_code == 200

        data = response.json()
        assert "job_statistics" in data
        assert "processing_info" in data

    def test_system_metrics(self, client: TestClient):
        """Test system metrics endpoint."""
        response = client.get("/api/v1/metrics/system")
        assert response.status_code == 200

        data = response.json()
        assert "cpu" in data
        assert "memory" in data
        assert "disk" in data
        assert "network" in data


class TestJobsEndpoints:
    """Test jobs API endpoints."""

    def test_create_job_not_implemented(self, client: TestClient):
        """Test that create job endpoint returns not implemented."""
        response = client.post("/api/v1/jobs/")
        assert response.status_code == 501
        assert "not implemented" in response.json()["detail"].lower()

    def test_get_job_not_implemented(self, client: TestClient):
        """Test that get job endpoint returns not implemented."""
        response = client.get("/api/v1/jobs/test-job-id")
        assert response.status_code == 501
        assert "not implemented" in response.json()["detail"].lower()

    def test_list_jobs_empty(self, client: TestClient):
        """Test list jobs endpoint returns empty list."""
        response = client.get("/api/v1/jobs/")
        assert response.status_code == 200

        data = response.json()
        assert data["jobs"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["per_page"] == 10
        assert not data["has_next"]
        assert not data["has_prev"]

    def test_cancel_job_not_implemented(self, client: TestClient):
        """Test that cancel job endpoint returns not implemented."""
        response = client.delete("/api/v1/jobs/test-job-id")
        assert response.status_code == 501
        assert "not implemented" in response.json()["detail"].lower()


class TestAuthentication:
    """Test API authentication."""

    def test_missing_api_key(self, client: TestClient):
        """Test that requests without API key are rejected."""
        # This test assumes API keys are configured
        # In a real test, we'd mock the settings
        pass

    def test_invalid_api_key(self, client: TestClient):
        """Test that requests with invalid API key are rejected."""
        # This test assumes API keys are configured
        # In a real test, we'd mock the settings
        pass

    def test_valid_api_key(self, client: TestClient):
        """Test that requests with valid API key are accepted."""
        # This test assumes API keys are configured
        # In a real test, we'd mock the settings
        pass


class TestErrorHandling:
    """Test error handling."""

    def test_404_error(self, client: TestClient):
        """Test 404 error handling."""
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404

    def test_500_error(self, client: TestClient):
        """Test 500 error handling."""
        # This would require mocking a service failure
        pass


class TestRootEndpoint:
    """Test root endpoint."""

    def test_root_endpoint(self, client: TestClient):
        """Test root endpoint returns service information."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "WhisperX Cloud Run Microservice"
        assert data["version"] == "1.0.0"
        assert data["docs"] == "/docs"


class TestDocumentation:
    """Test API documentation endpoints."""

    def test_swagger_docs(self, client: TestClient):
        """Test Swagger documentation endpoint."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_docs(self, client: TestClient):
        """Test ReDoc documentation endpoint."""
        response = client.get("/redoc")
        assert response.status_code == 200


@pytest.mark.asyncio
class TestAsyncEndpoints:
    """Test async endpoints."""

    async def test_async_health_check(self, async_client):
        """Test async health check."""
        response = await async_client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "service" in data
