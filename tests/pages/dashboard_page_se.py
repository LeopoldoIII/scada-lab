"""Selenium Page Object for SCADA Dashboard, Single-Line Diagram, and Controls."""

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from tests.pages.base_page_se import BasePageSelenium


class DashboardPageSelenium(BasePageSelenium):
    """Encapsulates dashboard telemetry and control panel operations in Selenium WebDriver."""

    MODE_TAG = (By.ID, "firewallModeTag")
    BREAKER_TEXT = (By.ID, "breakerStateText")
    SETPOINT_INPUT = (By.ID, "setpointInput")
    DISPATCH_BTN = (By.ID, "dispatchBtn")
    DISPATCH_FEEDBACK = (By.ID, "dispatchFeedbackText")
    TRIP_GRID_BTN = (By.ID, "tripGridBtn")
    RESTORE_GRID_BTN = (By.ID, "restoreGridBtn")
    ALARM_BADGE = (By.ID, "alarmCountBadge")
    ALARMS_LIST = (By.ID, "alarmsList")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def dispatch_setpoint(self, power_mw: float) -> None:
        """Dispatches a power setpoint and waits for asynchronous confirmation."""
        inp = self.find_visible(*self.SETPOINT_INPUT)
        inp.clear()
        inp.send_keys(str(power_mw))
        self.find_visible(*self.DISPATCH_BTN).click()
        assert self.wait_for_text(*self.DISPATCH_FEEDBACK, "CONFIRMED", timeout=6.0)

    def simulate_grid_trip(self) -> None:
        """Triggers grid under-voltage trip simulation."""
        self.find_visible(*self.TRIP_GRID_BTN).click()

    def simulate_grid_restore(self) -> None:
        """Restores grid back to normal."""
        self.find_visible(*self.RESTORE_GRID_BTN).click()

    def assert_firewall_mode(self, expected_mode: str) -> None:
        """Asserts that firewall status tag displays the expected mode."""
        assert self.wait_for_text(*self.MODE_TAG, expected_mode, timeout=6.0)

    def assert_breaker_status(self, expected_status: str) -> None:
        """Asserts that SLD circuit breaker text shows CLOSED or TRIPPED."""
        assert self.wait_for_text(*self.BREAKER_TEXT, expected_status, timeout=6.0)

    def assert_active_alarms_count(self, expected_count: int) -> None:
        """Asserts the alarm badge count."""
        assert self.wait_for_text(*self.ALARM_BADGE, f"{expected_count} ACTIVE", timeout=6.0)

    def acknowledge_first_alarm(self) -> None:
        """Clicks ACK button on the first unacknowledged alarm card."""
        ack_btn = self.find_visible(By.XPATH, "//div[@id='alarmsList']//button[contains(text(), 'ACK')]")
        ack_btn.click()
        assert self.wait_for_text(*self.ALARMS_LIST, "ACK'D", timeout=6.0)

