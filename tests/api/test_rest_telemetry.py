"""API test suite for telemetry contracts, control actions, and boundary value analysis."""

import pytest
import requests


@pytest.mark.api
class TestTelemetryAndControlsApi:
    """Validates real-time telemetry contracts, setpoint boundaries, and control RBAC."""

    def test_get_live_telemetry_schema_and_bounds(self, api_client: requests.Session, base_url: str) -> None:
        """Verifies physical metrics match expected electrical and battery ranges."""
        resp = api_client.get(f"{base_url}/api/v1/telemetry")
        assert resp.status_code == 200
        data = resp.json()

        # Electrical range assertions
        assert 9.0 <= data["grid_voltage_kv"] <= 15.0
        assert 58.0 <= data["bus_frequency_hz"] <= 62.0
        assert 0.0 <= data["battery_soc_percent"] <= 100.0
        assert 0.0 <= data["battery_soh_percent"] <= 100.0
        assert data["firewall_status"] in ["GRID_CONNECTED", "ISLANDED", "EMERGENCY_BACKUP"]
        assert data["breaker_status"] in ["CLOSED", "TRIPPED"]
        assert data["datacenter_load_mw"] > 0

    @pytest.mark.parametrize("setpoint_mw", [-20.0, -10.5, 0.0, 7.5, 20.0])
    def test_setpoint_dispatch_boundary_values_valid(
        self,
        api_client: requests.Session,
        base_url: str,
        operator_headers: dict[str, str],
        setpoint_mw: float,
    ) -> None:
        """Boundary Value Analysis (BVA): Tests valid bounds (-20MW to +20MW)."""
        resp = api_client.post(
            f"{base_url}/api/v1/controls/dispatch",
            json={"power_mw": setpoint_mw},
            headers=operator_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["details"]["power_mw"] == setpoint_mw

    @pytest.mark.parametrize("invalid_setpoint_mw", [-20.1, -50.0, 20.1, 100.0])
    def test_setpoint_dispatch_boundary_values_invalid(
        self,
        api_client: requests.Session,
        base_url: str,
        operator_headers: dict[str, str],
        invalid_setpoint_mw: float,
    ) -> None:
        """Boundary Value Analysis (BVA): Tests values exceeding bounds produce HTTP 422 Unprocessable Entity."""
        resp = api_client.post(
            f"{base_url}/api/v1/controls/dispatch",
            json={"power_mw": invalid_setpoint_mw},
            headers=operator_headers,
        )
        assert resp.status_code == 422

    def test_viewer_role_rejected_on_control_actions_403(
        self, api_client: requests.Session, base_url: str, viewer_headers: dict[str, str]
    ) -> None:
        """Verifies RBAC protection: VIEWER role receives 403 Forbidden when attempting control actions."""
        resp = api_client.post(
            f"{base_url}/api/v1/controls/dispatch",
            json={"power_mw": 5.0},
            headers=viewer_headers,
        )
        assert resp.status_code == 403
        assert "lacks operator clearance" in resp.json()["detail"]

    def test_grid_trip_and_restore_cycle(
        self, api_client: requests.Session, base_url: str, operator_headers: dict[str, str]
    ) -> None:
        """Validates simulated grid blackout triggers ISLANDED mode and alarms."""
        # 1. Trip the grid
        trip_resp = api_client.post(f"{base_url}/api/v1/sim/trip-grid", headers=operator_headers)
        assert trip_resp.status_code == 200

        # 2. Check telemetry reflects islanded firewall
        t_resp = api_client.get(f"{base_url}/api/v1/telemetry")
        assert t_resp.json()["firewall_status"] == "ISLANDED"
        assert t_resp.json()["breaker_status"] == "TRIPPED"

        # 3. Check alarms
        alarms_resp = api_client.get(f"{base_url}/api/v1/alarms")
        alarm_codes = [a["code"] for a in alarms_resp.json()]
        assert "GRID_UNDER_VOLTAGE" in alarm_codes

        # 4. Acknowledge alarm
        ack_resp = api_client.post(
            f"{base_url}/api/v1/alarms/GRID_UNDER_VOLTAGE/ack",
            headers=operator_headers,
        )
        assert ack_resp.status_code == 200

        # 5. Restore grid
        restore_resp = api_client.post(f"{base_url}/api/v1/sim/restore-grid", headers=operator_headers)
        assert restore_resp.status_code == 200

