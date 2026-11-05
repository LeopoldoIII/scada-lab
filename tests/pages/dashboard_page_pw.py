"""Playwright Page Object for SCADA Dashboard, Single-Line Diagram, and Supervisory Controls."""

from playwright.sync_api import Locator, Page, expect
from tests.pages.base_page_pw import BasePagePlaywright


class DashboardPagePlaywright(BasePagePlaywright):
    """Encapsulates dashboard telemetry and control panel operations in Playwright."""

    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page, base_url)
        self.firewall_mode_tag: Locator = page.locator("#firewallModeTag")
        self.breaker_state_text: Locator = page.locator("#breakerStateText")
        self.grid_voltage_val: Locator = page.locator("#valGridVoltage")
        self.bus_frequency_val: Locator = page.locator("#valBusFrequency")
        self.battery_soc_val: Locator = page.locator("#valBatterySoc")
        self.power_flow_val: Locator = page.locator("#valPowerFlow")

        # Controls
        self.setpoint_input: Locator = page.locator("#setpointInput")
        self.dispatch_btn: Locator = page.locator("#dispatchBtn")
        self.dispatch_feedback: Locator = page.locator("#dispatchFeedbackText")
        self.trip_grid_btn: Locator = page.locator("#tripGridBtn")
        self.restore_grid_btn: Locator = page.locator("#restoreGridBtn")

        # Alarms
        self.alarm_badge: Locator = page.locator("#alarmCountBadge")
        self.alarms_list: Locator = page.locator("#alarmsList")

    def dispatch_setpoint(self, power_mw: float) -> None:
        """Dispatches a power setpoint and waits for asynchronous confirmation."""
        self.setpoint_input.fill(str(power_mw))
        self.dispatch_btn.click()
        # Verify transient state then confirmation state without using time.sleep()
        expect(self.dispatch_feedback).to_contain_text("CONFIRMED", timeout=6000)

    def simulate_grid_trip(self) -> None:
        """Triggers grid under-voltage trip simulation."""
        self.trip_grid_btn.click()

    def simulate_grid_restore(self) -> None:
        """Restores grid back to normal."""
        self.restore_grid_btn.click()

    def assert_firewall_mode(self, expected_mode: str) -> None:
        """Asserts that firewall status tag displays the expected mode."""
        expect(self.firewall_mode_tag).to_contain_text(expected_mode, timeout=6000)

    def assert_breaker_status(self, expected_status: str) -> None:
        """Asserts that SLD circuit breaker text shows CLOSED or TRIPPED."""
        expect(self.breaker_state_text).to_contain_text(expected_status, timeout=6000)

    def assert_active_alarms_count(self, expected_count: int) -> None:
        """Asserts the alarm badge count."""
        expect(self.alarm_badge).to_contain_text(f"{expected_count} ACTIVE", timeout=6000)

    def acknowledge_first_alarm(self) -> None:
        """Clicks ACK button on the first unacknowledged alarm card."""
        ack_btn = self.alarms_list.locator("button:has-text('ACK')").first
        ack_btn.click()
        expect(self.alarms_list).to_contain_text("ACK'D", timeout=6000)

