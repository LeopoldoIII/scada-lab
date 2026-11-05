"""API test suite for operator authentication and role-based access control (RBAC)."""

import pytest
import requests


@pytest.mark.api
class TestAuthApi:
    """Validates login credentials, JWT token structure, and RBAC enforcement."""

    def test_operator_login_success(self, api_client: requests.Session, base_url: str) -> None:
        """Verifies operator_alice login returns valid JWT token and OPERATOR role."""
        resp = api_client.post(
            f"{base_url}/api/v1/auth/login",
            json={"username": "operator_alice", "password": "ControlRoom2026!"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["username"] == "operator_alice"
        assert data["role"] == "OPERATOR"

    def test_viewer_login_success(self, api_client: requests.Session, base_url: str) -> None:
        """Verifies viewer_guest login returns VIEWER role."""
        resp = api_client.post(
            f"{base_url}/api/v1/auth/login",
            json={"username": "viewer_guest", "password": "Readonly2026!"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["role"] == "VIEWER"

    def test_invalid_credentials_returns_401(self, api_client: requests.Session, base_url: str) -> None:
        """Verifies bad password returns HTTP 401 Unauthorized."""
        resp = api_client.post(
            f"{base_url}/api/v1/auth/login",
            json={"username": "operator_alice", "password": "WrongPassword999"},
        )
        assert resp.status_code == 401
        assert "Invalid" in resp.json()["detail"]

    def test_token_introspection_me_endpoint(
        self, api_client: requests.Session, base_url: str, operator_headers: dict[str, str]
    ) -> None:
        """Verifies /me endpoint returns authenticated user identity from Bearer token."""
        resp = api_client.get(f"{base_url}/api/v1/auth/me", headers=operator_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "operator_alice"
        assert data["role"] == "OPERATOR"

    def test_unauthenticated_request_rejected(self, api_client: requests.Session, base_url: str) -> None:
        """Verifies /me endpoint without credentials returns HTTP 401."""
        resp = api_client.get(f"{base_url}/api/v1/auth/me")
        assert resp.status_code == 401

