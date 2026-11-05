# SCADA Test Automation Framework: Agent Directives & Guidelines

Welcome to the **SCADA / BESS Test Automation Framework** workspace. This repository contains an enterprise-grade QA test automation framework tailored for industrial automation, Battery Energy Storage Systems (BESS), and medium-voltage UPS systems (substation grid firewall architecture).

## Core Directives

1. **Language Requirement:** All code, comments, docstrings, commit messages, filenames, Gherkin features, and test definitions must be written in **100% English**. (User communication may occur in Spanish or English as requested).
2. **Strict Vendor Neutrality & Generic Domain:**
   - Keep the project completely generic, robust, and enterprise-focused.
   - Strictly avoid referencing any specific corporate entity, private employer, trademarked product, or recruitment/hiring context.
   - Enforce standards defined in `.agents/rules/vendor_neutrality.md`.
3. **Strict Python Standards:**
   - Target Python 3.10+.
   - Enforce type annotations on all public functions, classes, and methods.
   - Follow Google-style Python docstrings for all classes, methods, and modules.
4. **Zero-Sleep Flakiness Policy:**
   - Never use arbitrary `time.sleep()` in test scripts.
   - Utilize Playwright's built-in auto-waiting assertions (`expect(locator).to_have_text(...)`) and Selenium's explicit `WebDriverWait` with custom expected conditions.
5. **OT / IT Safety & Auditing:**
   - Treat control actions (setpoint dispatch, breaker trip) as sensitive transactions requiring authenticated operator identity and database audit logging.
6. **Environment Agnostic:**
   - Framework must operate seamlessly against local Python runs, Docker Compose networks, or remote staging web services (`--env=local|docker|staging`).

## Workspace Customizations

- `.agents/rules/vendor_neutrality.md`: Strict rules for vendor-neutrality and generic industrial nomenclature.
- `.agents/rules/coding_standards.md`: Python standards, type annotations, schemas, and clean architecture.
- `.agents/rules/testing_guidelines.md`: Test naming, Pytest markers, POM conventions, and synchronization patterns.
- `.agents/skills/network-fault-fixtures/SKILL.md`: Runbook and code patterns for building network interference, throttling, and fault injection fixtures across Playwright, Selenium CDP, and REST APIs.
