"""Selenium End-to-End test suite for SCADA HMI, authentication, and controls."""

import pytest
from selenium.webdriver.remote.webdriver import WebDriver
from tests.fixtures.network_selenium import throttled_network_selenium
from tests.pages.dashboard_page_se import DashboardPageSelenium
from tests.pages.login_page_se import LoginPageSelenium


@pytest.mark.ui
@pytest.mark.selenium
class TestScadaSeleniumE2E:
    """End-to-End browser test suite using Selenium explicit WebDriverWait."""

    def test_operator_login_flow(self, driver: WebDriver, base_url: str) -> None:
        """Verifies operator authentication modal and badge update using Selenium POM."""
        login_page = LoginPageSelenium(driver, base_url)
        login_page.navigate("/")
        login_page.open_login_modal()
        login_page.login("operator_alice", "ControlRoom2026!")
        login_page.assert_logged_in_as("operator_alice", "OPERATOR")

    def test_supervisory_controls_and_setpoint_dispatch(self, driver: WebDriver, base_url: str) -> None:
        """Verifies operator login and asynchronous power setpoint dispatch in Selenium."""
        login_page = LoginPageSelenium(driver, base_url)
        login_page.navigate("/")
        login_page.open_login_modal()
        login_page.login("operator_alice", "ControlRoom2026!")

        dashboard = DashboardPageSelenium(driver, base_url)
        dashboard.dispatch_setpoint(6.0)

    def test_grid_disturbance_firewall_islanding_and_alarm_ack(self, driver: WebDriver, base_url: str) -> None:
        """Validates simulated grid trip isolates the MV-UPS firewall in Selenium."""
        login_page = LoginPageSelenium(driver, base_url)
        login_page.navigate("/")
        login_page.open_login_modal()
        login_page.login("operator_alice", "ControlRoom2026!")

        dashboard = DashboardPageSelenium(driver, base_url)
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

    def test_throttled_network_cdp_resilience(
        self, throttled_network_selenium: WebDriver, base_url: str
    ) -> None:
        """Verifies explicit WebDriverWait stability under CDP network throttling (1500ms RTT)."""
        driver = throttled_network_selenium
        login_page = LoginPageSelenium(driver, base_url)
        login_page.navigate("/")
        login_page.open_login_modal()
        login_page.login("operator_alice", "ControlRoom2026!")
        login_page.assert_logged_in_as("operator_alice", "OPERATOR")

