# Test Plan: SCADA BESS & MV-UPS Control System

## 1. Scope & Objective
This Test Plan defines the verification strategy for the **Industrial Medium-Voltage (13.8 kV) UPS and Battery Energy Storage System (BESS)** control software. The system acts as a physical and electrical firewall protecting data center workloads from utility grid disturbances.

The test automation framework verifies:
1. **Purdue Level 1/2 (Fieldbus OT)**: Modbus TCP holding registers (13.8kV MV, 60Hz bus frequency, SoC%, Breaker status).
2. **Purdue Level 3 (Supervisory SCADA Gateway)**: REST API contracts, operator authentication (JWT/RBAC), and SQL database audit trails.
3. **Purdue Level 4 (Operations HMI)**: Web dashboard, SVG single-line diagrams, alarm annunciators, and resilience under high-latency network conditions.

---

## 2. Test Design Techniques Applied

### 2.1 Boundary Value Analysis (BVA) - Power Dispatch Setpoints
The battery inverter accepts dispatch setpoints between `-20.0 MW` (maximum charging) and `+20.0 MW` (maximum discharging).

| Test Case ID | Value Tested | Boundary Category | Expected Result | HTTP Status |
| :--- | :--- | :--- | :--- | :--- |
| **TC-BVA-01** | `-20.1 MW` | Just below minimum valid | Rejected (Out of bounds) | `422 Unprocessable` |
| **TC-BVA-02** | `-20.0 MW` | Minimum valid boundary | Accepted | `200 OK` |
| **TC-BVA-03** | `0.0 MW` | Nominal midpoint boundary | Accepted (Floating state) | `200 OK` |
| **TC-BVA-04** | `+20.0 MW` | Maximum valid boundary | Accepted | `200 OK` |
| **TC-BVA-05** | `+20.1 MW` | Just above maximum valid | Rejected (Out of bounds) | `422 Unprocessable` |

### 2.2 Equivalence Partitioning (EP) - Medium Voltage Levels (13.8 kV Nominal)

| Partition Class | Input Range | System Behavior | Firewall Operating Mode |
| :--- | :--- | :--- | :--- |
| **Valid Nominal** | `13.1 kV to 14.5 kV` | Normal utility grid synchronization | `GRID_CONNECTED` |
| **Under-Voltage Fault** | `< 12.0 kV` | Instantaneous breaker trip, battery discharge | `ISLANDED (BACKUP)` |
| **Over-Voltage Transient** | `> 15.0 kV` | Surge protection isolation, alarm generation | `ISLANDED (BACKUP)` |

---

## 3. Test Layers & Tooling Matrix

```
       / \
      / BDD \         pytest-bdd (Gherkin user stories)
     /-------\
    /   UI    \       Playwright (Auto-wait) & Selenium (WebDriverWait)
   /-----------\
  /  API & OT   \     requests (REST) & pymodbus (TCP port 5020)
 /---------------\
/  Database (SQL) \   SQLAlchemy & SQLite Historian query assertions
-------------------
```

---

## 4. Defect Severity & Priority Classification

* **Severity 1 (Blocker/Critical)**: MV-UPS fails to transition to `ISLANDED` mode when grid voltage drops below 12.0 kV; unauthenticated user allowed to dispatch setpoints.
* **Severity 2 (Major)**: Alarm annunciator fails to display `GRID_UNDER_VOLTAGE` within 2 seconds; audit log missing `operator_id`.
* **Severity 3 (Minor)**: Telemetry gauge font misaligned or cosmetic rounding error in kW readout.

---

## 5. Synchronization & Flakiness Defense

1. **Elimination of `time.sleep()`**: Tests strictly prohibit hardcoded sleeps.
2. **Playwright Auto-Retrying Locators**: Uses web-first assertions (`expect(locator).to_have_text(...)`) that poll until the DOM settles.
3. **Selenium Stale Element Recovery**: Uses custom expected condition loops catching `StaleElementReferenceException` during rapid SCADA polling refreshes.
