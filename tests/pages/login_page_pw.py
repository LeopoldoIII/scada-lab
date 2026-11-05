"""Playwright Page Object for Operator Authentication modal."""

from playwright.sync_api import Locator, Page, expect
from tests.pages.base_page_pw import BasePagePlaywright


class LoginPagePlaywright(BasePagePlaywright):
    """Encapsulates login dialog interactions in Playwright."""

    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page, base_url)
        self.auth_btn: Locator = page.locator("#authBtn")
        self.modal_backdrop: Locator = page.locator("#authModalBackdrop")
        self.username_input: Locator = page.locator("#usernameInput")
        self.password_input: Locator = page.locator("#passwordInput")
        self.submit_btn: Locator = page.locator("#loginSubmitBtn")
        self.error_msg: Locator = page.locator("#authErrorMsg")
        self.operator_badge: Locator = page.locator("#operatorBadge")

    def open_login_modal(self) -> None:
        """Opens the login modal dialog."""
        self.auth_btn.click()
        expect(self.modal_backdrop).to_have_class("modal-backdrop open")

    def login(self, username: str, password: str) -> None:
        """Enters credentials and submits the login form."""
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.submit_btn.click()

    def assert_logged_in_as(self, username: str, role: str) -> None:
        """Asserts that operator badge displays the authenticated operator profile."""
        expect(self.operator_badge).to_contain_text(f"OPERATOR: {username} ({role})")

    def assert_login_error_visible(self, expected_snippet: str = "Invalid") -> None:
        """Asserts that the error message is displayed."""
        expect(self.error_msg).to_be_visible()
        expect(self.error_msg).to_contain_text(expected_snippet)

