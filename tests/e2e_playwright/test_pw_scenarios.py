"""Playwright End-to-End test suite for SCADA HMI, authentication, and fault resilience."""

import pytest
from playwright.sync_api import Page, expect
from tests.fixtures.network_playwright import slow_telemetry_network
from tests.pages.dashboard_page_pw import DashboardPagePlaywright
from tests.pages.login_page_pw import LoginPagePlaywright


@pytest.mark.ui
@pytest.mark.playwright
class TestScadaPlaywrightE2E:
    """End-to-End browser test suite using Playwright auto-waiting assertions."""

    def test_operator_login_flow(self, page: Page, base_url: str) -> None:
        """Verifies operator authentication modal and badge update."""
        login_page = LoginPagePlaywright(page, base_url)
        login_page.navigate("/")
        login_page.open_login_modal()
        login_page.login("operator_alice", "ControlRoom2026!")
        login_page.assert_logged_in_as("operator_alice", "OPERATOR")

    def test_supervisory_controls_and_setpoint_dispatch(self, page: Page, base_url: str) -> None:
        """Verifies operator login and asynchronous power setpoint dispatch."""
        login_page = LoginPagePlaywright(page, base_url)
        login_page.navigate("/")
        login_page.open_login_modal()
        login_page.login("operator_alice", "ControlRoom2026!")

        dashboard = DashboardPagePlaywright(page, base_url)
        dashboard.dispatch_setpoint(4.5)

    def test_grid_disturbance_firewall_islanding_and_alarm_ack(self, page: Page, base_url: str) -> None:
        """Validates simulated grid trip isolates the MV-UPS firewall and triggers alarms."""
        login_page = LoginPagePlaywright(page, base_url)
        login_page.navigate("/")
        login_page.open_login_modal()
        login_page.login("operator_alice", "ControlRoom2026!")

        dashboard = DashboardPagePlaywright(page, base_url)
        dashboard.simulate_grid_trip()

        dashboard.assert_firewall_mode("ISLANDED")
        dashboard.assert_breaker_status("TRIPPED")
        dashboard.assert_active_alarms_count(1)

        # Acknowledge the alarm
        dashboard.acknowledge_first_alarm()

        # Restore grid
        dashboard.simulate_grid_restore()
        dashboard.assert_firewall_mode("GRID_CONNECTED")
        dashboard.assert_breaker_status("CLOSED")

    def test_slow_network_polling_resilience(self, slow_telemetry_network: Page, base_url: str) -> None:
        """Verifies that Playwright auto-retrying assertions succeed under 1.5s network lag."""
        page = slow_telemetry_network
        login_page = LoginPagePlaywright(page, base_url)
        login_page.navigate("/")

        dashboard = DashboardPagePlaywright(page, base_url)
        # Even with artificial 1.5-second polling delay, web-first assertion waits without flakiness
        expect(dashboard.grid_voltage_val).to_be_visible(timeout=8000)

