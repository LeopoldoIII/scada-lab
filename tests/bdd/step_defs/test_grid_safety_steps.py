"""Step definitions for grid_safety.feature."""

import pytest
import requests
from pytest_bdd import given, parsers, scenarios, then, when

scenarios("../features/grid_safety.feature")


@given(parsers.parse('the MV-UPS is operating normally in "{expected_mode}" mode'))
def verify_normal_mode(api_client: requests.Session, base_url: str, operator_headers: dict[str, str], expected_mode: str):
    # Ensure grid is restored
    api_client.post(f"{base_url}/api/v1/sim/restore-grid", headers=operator_headers)
    resp = api_client.get(f"{base_url}/api/v1/telemetry")
    assert resp.status_code == 200
    assert resp.json()["firewall_status"] == expected_mode


@given("the data center load is stable")
def verify_dc_load(api_client: requests.Session, base_url: str):
    resp = api_client.get(f"{base_url}/api/v1/telemetry")
    assert resp.json()["datacenter_load_mw"] > 0


@when("a severe grid under-voltage disturbance is simulated")
def trigger_under_voltage(api_client: requests.Session, base_url: str, operator_headers: dict[str, str]):
    resp = api_client.post(f"{base_url}/api/v1/sim/trip-grid", headers=operator_headers)
    assert resp.status_code == 200


@then(parsers.parse('the MV-UPS firewall status must transition to "{expected_mode}"'))
def verify_islanded_mode(api_client: requests.Session, base_url: str, expected_mode: str):
    resp = api_client.get(f"{base_url}/api/v1/telemetry")
    assert resp.json()["firewall_status"] == expected_mode


@then(parsers.parse('the circuit breaker CB-101 status must change to "{expected_status}"'))
def verify_breaker_tripped(api_client: requests.Session, base_url: str, expected_status: str):
    resp = api_client.get(f"{base_url}/api/v1/telemetry")
    assert resp.json()["breaker_status"] == expected_status


@then(parsers.parse('a critical alarm "{expected_alarm}" must be annunciated'))
def verify_alarm_annunciated(api_client: requests.Session, base_url: str, expected_alarm: str):
    resp = api_client.get(f"{base_url}/api/v1/alarms")
    alarm_codes = [a["code"] for a in resp.json()]
    assert expected_alarm in alarm_codes

