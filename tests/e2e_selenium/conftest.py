"""Selenium WebDriver specific fixtures and lifecycle configuration."""

from typing import Generator
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


@pytest.fixture
def driver() -> Generator[webdriver.Chrome, None, None]:
    """Provides a headless Chrome WebDriver session."""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1600,1000")

    driver = None
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except Exception:
        # Fallback to system chrome driver if installed
        driver = webdriver.Chrome(options=chrome_options)

    driver.implicitly_wait(0)  # Enforce explicit waits only!
    try:
        yield driver
    finally:
        if driver:
            driver.quit()

