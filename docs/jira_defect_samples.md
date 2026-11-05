# Sample Production Defect Reports (JIRA Format)

These sample defect tickets demonstrate how industrial automation and synchronization defects are identified, documented, and tracked through resolution.

---

### Defect 1: SCADA-104 (Severity: Major / Priority: High)

* **Issue Key**: `SCADA-104`
* **Summary**: Race condition between HMI polling loop and breaker trip dispatch causes stale SLD diagram
* **Component**: `HMI Frontend` / `State Synchronization`
* **Environment**: Red Hat Enterprise Linux 9 / Chromium 124 / Staging Substation MV-01
* **Reporter**: QA Automation Engineer
* **Assignee**: Control Room Frontend Lead

#### Description
When an operator issues a "Trip Grid" command during an active telemetry polling fetch, the UI DOM undergoes a partial update: the circuit breaker icon displays `TRIPPED` in red, but the Single-Line Diagram bus lines continue displaying normal green coloration for up to 3 polling intervals (4.5 seconds).

#### Steps to Reproduce
1. Log in to SCADA HMI as `operator_alice`.
2. Open Network DevTools and throttle fetch requests to 1500ms RTT using the `throttled_network_selenium` fixture.
3. Click "TRIP GRID (UNDER-VOLTAGE)".
4. Observe the SVG Single-Line Diagram nodes.

#### Expected Result
Both breaker `CB-101` and the interconnecting bus lines must synchronously transition to tripped state in the same animation frame.

#### Actual Result
`breakerCb101` turns red immediately, but `busLine1` remains green until the next unthrottled polling cycle completes.

#### Automation Test Reference
`tests/e2e_playwright/test_pw_scenarios.py::test_grid_disturbance_firewall_islanding_and_alarm_ack`

---

### Defect 2: SCADA-105 (Severity: Critical / Priority: Highest)

* **Issue Key**: `SCADA-105`
* **Summary**: Dispatched setpoint command fails to persist operator_id in SQL audit trail under token refresh
* **Component**: `API Backend` / `NERC-CIP Compliance Audit`
* **Environment**: Containerized Staging Gateway / SQLite / PostgreSQL
* **Reporter**: QA Automation Engineer

#### Description
During automated SQL database validation (`tests/db/test_operator_audit_trail.py`), it was observed that when a power setpoint dispatch occurs within 5 seconds of token issuance, the `control_audit_log` records `operator_id = 'unknown_operator'` instead of extracting the JWT subject claim `operator_alice`.

#### Root Cause Analysis (RCA)
FastAPI dependency injection in `routes.py` evaluated the fallback default before claims unpacking was completed in the async lifecycle.

#### Fix Verification
Automated test `tests/db/test_operator_audit_trail.py` now runs on every pull request to ensure strict non-null operator attribution.

---

### Defect 3: SCADA-106 (Severity: Minor / Priority: Medium)

* **Issue Key**: `SCADA-106`
* **Summary**: High-latency link causes duplicate ACK alarm requests due to missing button debounce
* **Component**: `HMI Alarms Panel`
* **Environment**: Remote Substation Cellular Link (1800ms ping)

#### Description
When clicking the "ACK" button on an active alarm card in the Annunciator panel over a high-latency link, the button is not immediately disabled. Fast double-clicks by the operator dispatch duplicate `POST /api/v1/alarms/{code}/ack` requests, resulting in an unhandled 404 on the second call.

#### Resolution
Added `btn.disabled = true` immediately on click in `app.js` prior to awaiting the fetch promise. Verified via Playwright route delay fixture.

