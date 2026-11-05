"""Global Pytest configuration, command-line hooks, and foundational fixtures."""

import os
import threading
import time
from typing import Generator
import pytest
import requests
import uvicorn
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base
from tests.config import EnvironmentConfig, get_config


def pytest_addoption(parser: pytest.Parser) -> None:
    """Registers custom CLI flags for multi-environment execution."""
    parser.addoption(
        "--env",
        action="store",
        default=os.getenv("TEST_ENV", "local"),
        help="Target environment: local | docker | staging",
    )


@pytest.fixture(scope="session")
def test_config(request: pytest.FixtureRequest) -> EnvironmentConfig:
    """Returns the resolved environment configuration for the test session."""
    env_name = request.config.getoption("--env")
    return get_config(env_name)


@pytest.fixture(scope="session")
def base_url(test_config: EnvironmentConfig) -> str:
    """Returns the target SCADA Web API base URL."""
    return test_config.base_url.rstrip("/")


@pytest.fixture(scope="session", autouse=True)
def live_server(test_config: EnvironmentConfig) -> Generator[None, None, None]:
    """Ensures SCADA backend is running. Starts local background thread if targeting local."""
    if test_config.env_name == "local":
        # Check if already running on 8000
        try:
            resp = requests.get(f"{test_config.base_url}/health", timeout=1.0)
            if resp.status_code == 200:
                yield
                return
        except Exception:
            pass

        # Start embedded server in thread
        import app.main
        config = uvicorn.Config(app.main.app, host="127.0.0.1", port=8000, log_level="warning")
        server = uvicorn.Server(config)
        t = threading.Thread(target=server.run, daemon=True)
        t.start()

        # Wait for health probe
        for _ in range(30):
            try:
                resp = requests.get(f"{test_config.base_url}/health", timeout=1.0)
                if resp.status_code == 200:
                    break
            except Exception:
                time.sleep(0.2)
        yield
    else:
        yield


@pytest.fixture(scope="session")
def api_client(base_url: str, live_server: None) -> requests.Session:
    """Provides a requests.Session initialized with target base_url."""
    session = requests.Session()
    return session


@pytest.fixture(scope="session")
def operator_token(api_client: requests.Session, base_url: str, test_config: EnvironmentConfig) -> str:
    """Authenticates as operator_alice and returns valid JWT token."""
    resp = api_client.post(
        f"{base_url}/api/v1/auth/login",
        json={"username": test_config.operator_user, "password": test_config.operator_pass},
    )
    assert resp.status_code == 200, f"Operator login failed: {resp.text}"
    return resp.json()["access_token"]


@pytest.fixture(scope="session")
def viewer_token(api_client: requests.Session, base_url: str, test_config: EnvironmentConfig) -> str:
    """Authenticates as viewer_guest and returns valid JWT token."""
    resp = api_client.post(
        f"{base_url}/api/v1/auth/login",
        json={"username": test_config.viewer_user, "password": test_config.viewer_pass},
    )
    assert resp.status_code == 200, f"Viewer login failed: {resp.text}"
    return resp.json()["access_token"]


@pytest.fixture(scope="session")
def operator_headers(operator_token: str) -> dict[str, str]:
    """HTTP headers with operator authorization."""
    return {"Authorization": f"Bearer {operator_token}"}


@pytest.fixture(scope="session")
def viewer_headers(viewer_token: str) -> dict[str, str]:
    """HTTP headers with viewer authorization."""
    return {"Authorization": f"Bearer {viewer_token}"}


@pytest.fixture(scope="session")
def db_session(test_config: EnvironmentConfig) -> Generator[Session, None, None]:
    """Provides direct SQLAlchemy database session for SQL assertions."""
    if not test_config.database_url:
        pytest.skip("Target environment does not expose direct database connection")

    engine = create_engine(
        test_config.database_url,
        connect_args={"check_same_thread": False} if "sqlite" in test_config.database_url else {},
    )
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
