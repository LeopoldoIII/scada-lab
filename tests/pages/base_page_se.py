"""Selenium Base Page encapsulating explicit WebDriverWait and resilient stale element handlers."""

from typing import Callable
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class BasePageSelenium:
    """Foundational Page Object for Selenium WebDriver with polling resilience."""

    def __init__(self, driver: WebDriver, base_url: str, default_timeout: float = 8.0) -> None:
        self.driver = driver
        self.base_url = base_url.rstrip("/")
        self.default_timeout = default_timeout

    def navigate(self, path: str = "/") -> None:
        """Navigates to the specified path."""
        url = f"{self.base_url}{path}" if path.startswith("/") else f"{self.base_url}/{path}"
        self.driver.get(url)

    def find_visible(self, by: By, selector: str, timeout: float | None = None) -> WebElement:
        """Waits for and returns a visible element."""
        t = timeout or self.default_timeout
        return WebDriverWait(self.driver, t).until(EC.visibility_of_element_located((by, selector)))

    def wait_for_text(self, by: By, selector: str, text: str, timeout: float | None = None) -> bool:
        """Polls for expected text, resilient to StaleElementReferenceException caused by DOM updates."""
        t = timeout or self.default_timeout

        def _check(driver: WebDriver) -> bool:
            try:
                el = driver.find_element(by, selector)
                return text in el.text
            except StaleElementReferenceException:
                return False

        return WebDriverWait(self.driver, t, poll_frequency=0.2).until(_check)

