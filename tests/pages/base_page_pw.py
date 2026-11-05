"""Playwright Base Page encapsulating auto-retrying web-first locator patterns."""

from playwright.sync_api import Locator, Page, expect


class BasePagePlaywright:
    """Foundational Page Object for Playwright test automation."""

    def __init__(self, page: Page, base_url: str) -> None:
        self.page = page
        self.base_url = base_url.rstrip("/")

    def navigate(self, path: str = "/") -> None:
        """Navigates to the specified path."""
        url = f"{self.base_url}{path}" if path.startswith("/") else f"{self.base_url}/{path}"
        self.page.goto(url)

    def wait_for_element_text(self, locator: Locator, expected_text: str, timeout_ms: float = 8000) -> None:
        """Auto-retries until locator contains the expected text."""
        expect(locator).to_contain_text(expected_text, timeout=timeout_ms)

    def wait_for_element_visible(self, locator: Locator, timeout_ms: float = 8000) -> None:
        """Auto-retries until locator becomes visible."""
        expect(locator).to_be_visible(timeout=timeout_ms)

