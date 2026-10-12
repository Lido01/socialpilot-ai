"""Tests for the health endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_returns_200(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200


def test_health_returns_ok_status(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    data = response.json()
    assert data["status"] == "ok"


def test_health_returns_app_name(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    data = response.json()
    assert "app_name" in data
    assert isinstance(data["app_name"], str)
    assert len(data["app_name"]) > 0


def test_health_returns_app_env(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    data = response.json()
    assert "app_env" in data
    assert data["app_env"] in {"development", "staging", "production"}


def test_health_does_not_expose_secrets(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    data = response.json()
    assert "secret_key" not in str(data).lower()
    assert "database_url" not in str(data).lower()
    assert "token" not in str(data).lower()
    assert "password" not in str(data).lower()
