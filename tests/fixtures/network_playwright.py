"""Playwright network route interception fixtures for simulating degraded field communication."""

import time
import pytest
from playwright.sync_api import Page, Route


@pytest.fixture
def slow_telemetry_network(page: Page):
    """Injects 1.5-second artificial delay into telemetry polling to test UI loading stability."""
    def handle_route(route: Route) -> None:
        time.sleep(1.5)
        route.continue_()

    page.route("**/api/v1/telemetry*", handle_route)
    yield page
    try:
        page.unroute("**/api/v1/telemetry*")
    except Exception:
        pass


@pytest.fixture
def dropped_telemetry_network(page: Page):
    """Aborts all outgoing telemetry calls to simulate radio/socket connection failure."""
    def abort_route(route: Route) -> None:
        route.abort("failed")

    page.route("**/api/v1/telemetry*", abort_route)
    yield page
    try:
        page.unroute("**/api/v1/telemetry*")
    except Exception:
        pass


@pytest.fixture
def gateway_timeout_network(page: Page):
    """Returns synthetic HTTP 504 Gateway Timeout to verify HMI error resilience."""
    def mock_504(route: Route) -> None:
        route.fulfill(
            status=504,
            content_type="application/json",
            body='{"detail": "Substation field gateway timeout"}',
        )

    page.route("**/api/v1/telemetry*", mock_504)
    yield page
    try:
        page.unroute("**/api/v1/telemetry*")
    except Exception:
        pass

