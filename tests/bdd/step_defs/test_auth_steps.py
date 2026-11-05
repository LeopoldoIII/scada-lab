"""Step definitions for operator_auth.feature."""

import pytest
import requests
from pytest_bdd import given, parsers, scenarios, then, when

scenarios("../features/operator_auth.feature")


@pytest.fixture
def auth_context():
    return {}


@given("the SCADA API is available and healthy")
def api_healthy(api_client: requests.Session, base_url: str):
    resp = api_client.get(f"{base_url}/health")
    assert resp.status_code == 200


@when(
    parsers.parse('the operator "{username}" submits valid credentials "{password}"'),
    target_fixture="auth_context",
)
def submit_credentials(api_client: requests.Session, base_url: str, username: str, password: str):
    resp = api_client.post(
        f"{base_url}/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    return {"response": resp, "json": resp.json() if resp.status_code == 200 else {}}


@then(parsers.parse("the authentication response must return HTTP status {status_code:d}"))
def check_status(auth_context: dict, status_code: int):
    assert auth_context["response"].status_code == status_code


@then(parsers.parse('the user profile must confirm role "{expected_role}"'))
def check_role(auth_context: dict, expected_role: str):
    assert auth_context["json"]["role"] == expected_role


@then("an access token must be issued")
def check_token(auth_context: dict):
    assert "access_token" in auth_context["json"]


@given(
    parsers.parse('an authenticated session for user "{username}" with role "{role}"'),
    target_fixture="viewer_session",
)
def viewer_session(api_client: requests.Session, base_url: str, username: str, role: str):
    resp = api_client.post(
        f"{base_url}/api/v1/auth/login",
        json={"username": username, "password": "Readonly2026!"},
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"token": token, "headers": {"Authorization": f"Bearer {token}"}}


@when(
    parsers.parse("the viewer attempts to dispatch a power setpoint of {setpoint_mw:f} MW"),
    target_fixture="dispatch_result",
)
def viewer_dispatch(api_client: requests.Session, base_url: str, viewer_session: dict, setpoint_mw: float):
    resp = api_client.post(
        f"{base_url}/api/v1/controls/dispatch",
        json={"power_mw": setpoint_mw},
        headers=viewer_session["headers"],
    )
    return resp


@then(parsers.parse("the system must reject the command with HTTP status {expected_code:d}"))
def reject_command(dispatch_result: requests.Response, expected_code: int):
    assert dispatch_result.status_code == expected_code

