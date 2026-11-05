---
name: network-fault-fixtures
description: >-
  Runbook and code templates for building Pytest fixtures that simulate network disruptions,
  bandwidth throttling, latency spikes, packet drops, and socket timeouts across Playwright,
  Selenium CDP, and HTTP/REST clients.
---

# Network Fault & Interference Fixtures Runbook

Use this skill when designing, debugging, or extending fixtures that simulate degraded industrial network conditions, high-latency satellite/cellular links, or server-side disconnections.

---

## 1. Playwright Route Interception Patterns

Playwright's `page.route` intercepts browser-level network requests. This works seamlessly against local and remote staging targets.

### Pattern 1.1: Artificial Polling Latency
Simulates slow telemetry polling in an industrial SCADA HMI without touching backend servers:

```python
import time
import pytest
from playwright.sync_api import Page, Route

@pytest.fixture
def slow_telemetry_network(page: Page):
    """Injects a 1.5-second artificial delay into all /api/v1/telemetry requests."""
    def handle_route(route: Route) -> None:
        time.sleep(1.5)  # Delay the response by 1.5 seconds
        route.continue_()

    page.route("**/api/v1/telemetry*", handle_route)
    yield page
    page.unroute("**/api/v1/telemetry*")
```

### Pattern 1.2: Synthetic Connection Drop / Abort
Simulates sudden radio/cellular loss between SCADA HMI and the controller:

```python
@pytest.fixture
def dropped_network_link(page: Page):
    """Aborts all outgoing telemetry calls to simulate network disconnect."""
    def abort_route(route: Route) -> None:
        route.abort("failed")  # Options: 'failed', 'timedout', 'connectionreset'

    page.route("**/api/v1/telemetry*", abort_route)
    yield page
    page.unroute("**/api/v1/telemetry*")
```

### Pattern 1.3: Synthetic Server 504 Gateway Timeout
Verifies how the HMI handles upstream gateway timeouts:

```python
@pytest.fixture
def gateway_timeout_simulation(page: Page):
    """Returns synthetic HTTP 504 with an industrial error envelope."""
    def mock_504(route: Route) -> None:
        route.fulfill(
            status=504,
            content_type="application/json",
            body='{"error": "GATEWAY_TIMEOUT", "detail": "Substation RTU unreachable"}'
        )

    page.route("**/api/v1/**", mock_504)
    yield page
    page.unroute("**/api/v1/**")
```

---

## 2. Selenium CDP (Chrome DevTools Protocol) Patterns

Selenium 4+ allows executing CDP commands to emulate network interface throttles at the Chromium level.

### Pattern 2.1: Cellular / Slow 3G Emulation
Emulates a remote wind farm or solar field telemetry link:

```python
import pytest
from selenium.webdriver.remote.webdriver import WebDriver

@pytest.fixture
def throttled_network_selenium(driver: WebDriver):
    """Emulates high-latency cellular link via Chrome DevTools Protocol."""
    driver.execute_cdp_cmd(
        "Network.emulateNetworkConditions",
        {
            "offline": False,
            "latency": 1500,               # 1.5 second round-trip time (RTT)
            "downloadThroughput": 512 * 1024,  # 512 kbps
            "uploadThroughput": 256 * 1024,    # 256 kbps
        },
    )
    yield driver
    # Reset to normal unrestricted network
    driver.execute_cdp_cmd(
        "Network.emulateNetworkConditions",
        {"offline": False, "latency": 0, "downloadThroughput": -1, "uploadThroughput": -1},
    )
```

### Pattern 2.2: Offline Toggle
```python
@pytest.fixture
def offline_mode_selenium(driver: WebDriver):
    """Forces browser into complete offline state."""
    driver.execute_cdp_cmd(
        "Network.emulateNetworkConditions",
        {"offline": True, "latency": 0, "downloadThroughput": 0, "uploadThroughput": 0},
    )
    yield driver
    driver.execute_cdp_cmd(
        "Network.emulateNetworkConditions",
        {"offline": False, "latency": 0, "downloadThroughput": -1, "uploadThroughput": -1},
    )
```

---

## 3. REST API Chaos & Retry Testing (Requests Adapter)

For API-level resilience, attach a custom `HTTPAdapter` or policy engine that injects transient failures before succeeding, validating exponential backoff retry policies.

```python
import pytest
import requests
from requests.adapters import HTTPAdapter

class TransientFaultAdapter(HTTPAdapter):
    """Fails the first N attempts with HTTP 503 before passing cleanly."""
    def __init__(self, failure_budget: int = 2, status_code: int = 503):
        super().__init__()
        self.failure_budget = failure_budget
        self.attempts = 0
        self.status_code = status_code

    def send(self, request, **kwargs):
        self.attempts += 1
        if self.attempts <= self.failure_budget:
            resp = requests.Response()
            resp.status_code = self.status_code
            resp._content = b'{"error": "SCADA_GATEWAY_BUSY", "retryable": true}'
            resp.request = request
            return resp
        return super().send(request, **kwargs)

@pytest.fixture
def transient_fault_session():
    """Provides a requests.Session configured to fail twice with 503 before passing."""
    session = requests.Session()
    adapter = TransientFaultAdapter(failure_budget=2, status_code=503)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session
```

---

## 4. Verification Checklist
When using these fixtures in test cases:
1. Ensure the fixture properly tears down (`unroute` in Playwright, reset CDP in Selenium).
2. Avoid hardcoded `time.sleep()` in test assertions; let Playwright's locator assertions await state resolution.
3. Validate that appropriate error banners or retry spinners appear in the HMI without throwing uncaught JavaScript errors in the console.

