"""Selenium Page Object for Operator Authentication modal."""

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from tests.pages.base_page_se import BasePageSelenium


class LoginPageSelenium(BasePageSelenium):
    """Encapsulates login dialog interactions in Selenium WebDriver."""

    AUTH_BTN = (By.ID, "authBtn")
    MODAL_BACKDROP = (By.ID, "authModalBackdrop")
    USERNAME_INPUT = (By.ID, "usernameInput")
    PASSWORD_INPUT = (By.ID, "passwordInput")
    SUBMIT_BTN = (By.ID, "loginSubmitBtn")
    ERROR_MSG = (By.ID, "authErrorMsg")
    OPERATOR_BADGE = (By.ID, "operatorBadge")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open_login_modal(self) -> None:
        """Opens the login modal dialog."""
        btn = self.find_visible(*self.AUTH_BTN)
        btn.click()
        self.find_visible(*self.MODAL_BACKDROP)

    def login(self, username: str, password: str) -> None:
        """Enters credentials and submits the login form."""
        u = self.find_visible(*self.USERNAME_INPUT)
        u.clear()
        u.send_keys(username)
        p = self.find_visible(*self.PASSWORD_INPUT)
        p.clear()
        p.send_keys(password)
        self.find_visible(*self.SUBMIT_BTN).click()

    def assert_logged_in_as(self, username: str, role: str) -> None:
        """Asserts that operator badge displays the authenticated operator profile."""
        expected = f"OPERATOR: {username} ({role})"
        assert self.wait_for_text(*self.OPERATOR_BADGE, expected, timeout=5.0)

    def assert_login_error_visible(self, expected_snippet: str = "Invalid") -> None:
        """Asserts that the error message is displayed."""
        assert self.wait_for_text(*self.ERROR_MSG, expected_snippet, timeout=5.0)

