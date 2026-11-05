# Coding Standards & Architecture Guidelines

## 1. Language & Documentation
- All code, comments, docstrings, variable names, and error messages must be strictly in **English**.
- Follow **Google-style docstrings** for all modules, classes, and public methods.
- Document the unit of measurement on electrical/physical variables (e.g., `voltage_kv`, `frequency_hz`, `power_mw`, `soc_percent`).

## 2. Typing & Data Validation
- Enforce strict type hints (`typing` module / Python 3.10+ union types `float | None`).
- Use **Pydantic v2** models for API request/response payloads to guarantee strict boundary validation.
- Use **SQLAlchemy 2.0** declarative models with type-annotated mapped columns.

## 3. Clean Separation of Concerns
- `app/core/`: Pure physics models, Modbus register maps, authentication, and database engines. Keep free of HTTP framework logic.
- `app/api/`: FastAPI route controllers, dependency injection, and HTTP status codes.
- `app/static/`: HMI presentation layer (ISA-101 standard dark theme for control rooms).
- `tests/`: Modular test framework isolated from application internals.

## 4. Error Handling
- Never silence exceptions with bare `except: pass`.
- Custom domain exceptions should inherit from a base `ScadaLabError` class.
- API endpoints must return structured JSON error envelopes with explicit error codes.

