# Testing Guidelines & Synchronization Rules

## 1. Zero-Sleep Policy
- **Strictly prohibit `time.sleep()`** in UI and API test automation scripts.
- In **Playwright**: Use auto-retrying web-first assertions (`expect(locator).to_be_visible()`, `expect(locator).to_have_text(...)`) and `page.wait_for_response()`.
- In **Selenium**: Use `WebDriverWait(driver, timeout).until(EC....)`. If DOM nodes are periodically swapped due to polling, catch `StaleElementReferenceException` using custom resilient polling wait predicates.

## 2. Page Object Model (POM) Structure
- Every page object must encapsulate page-specific locators and user interactions.
- Test scenarios must never contain raw CSS/XPath selectors; they interact strictly via Page Object action methods and assertions.
- Keep Playwright POM (`pages/*_pw.py`) and Selenium POM (`pages/*_se.py`) clean and cleanly separated.

## 3. Pytest Markers
Every test function or class must carry appropriate pytest markers:
- `@pytest.mark.ui`: Browser-based end-to-end tests.
- `@pytest.mark.playwright`: Playwright engine tests.
- `@pytest.mark.selenium`: Selenium WebDriver tests.
- `@pytest.mark.api`: REST API contract and status code tests.
- `@pytest.mark.modbus`: Industrial Modbus TCP protocol tests.
- `@pytest.mark.db`: SQL assertions and database validation tests.
- `@pytest.mark.bdd`: Gherkin-backed behavior-driven tests.
- `@pytest.mark.resilience`: Tests involving network throttling, chaos injection, or latency.

## 4. Environment Agnosticism
- Tests must never hardcode `http://localhost:8000`.
- All endpoints, hosts, and ports must be resolved via `tests.config.Config` / environment variables (`BASE_URL`, `MODBUS_HOST`, `DATABASE_URL`).

