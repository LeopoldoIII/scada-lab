"""Selenium Chrome DevTools Protocol (CDP) network throttling and offline fixtures."""

import pytest
from selenium.webdriver.remote.webdriver import WebDriver


@pytest.fixture
def throttled_network_selenium(driver: WebDriver):
    """Emulates high-latency cellular / satellite link (1500ms RTT, 512kbps) via CDP."""
    driver.execute_cdp_cmd(
        "Network.emulateNetworkConditions",
        {
            "offline": False,
            "latency": 1500,
            "downloadThroughput": 512 * 1024,
            "uploadThroughput": 256 * 1024,
        },
    )
    yield driver
    driver.execute_cdp_cmd(
        "Network.emulateNetworkConditions",
        {"offline": False, "latency": 0, "downloadThroughput": -1, "uploadThroughput": -1},
    )


@pytest.fixture
def offline_mode_selenium(driver: WebDriver):
    """Forces browser into complete offline disconnected state via CDP."""
    driver.execute_cdp_cmd(
        "Network.emulateNetworkConditions",
        {"offline": True, "latency": 0, "downloadThroughput": 0, "uploadThroughput": 0},
    )
    yield driver
    driver.execute_cdp_cmd(
        "Network.emulateNetworkConditions",
        {"offline": False, "latency": 0, "downloadThroughput": -1, "uploadThroughput": -1},
    )

