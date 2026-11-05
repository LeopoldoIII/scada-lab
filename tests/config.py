"""Environment configuration manager supporting Local, Docker, and Remote Staging targets."""

import os
from dataclasses import dataclass


@dataclass
class EnvironmentConfig:
    """Encapsulates URLs, ports, and credentials for the current target environment."""

    env_name: str
    base_url: str
    modbus_host: str
    modbus_port: int
    database_url: str | None
    operator_user: str
    operator_pass: str
    viewer_user: str
    viewer_pass: str


def get_config(env_name: str | None = None) -> EnvironmentConfig:
    """Resolves configuration based on environment profile or environment variables."""
    active_env = env_name or os.getenv("TEST_ENV", "local").lower()

    if active_env == "docker":
        return EnvironmentConfig(
            env_name="docker",
            base_url=os.getenv("BASE_URL", "http://scada-app:8000"),
            modbus_host=os.getenv("MODBUS_HOST", "scada-app"),
            modbus_port=int(os.getenv("MODBUS_PORT", "5020")),
            database_url=os.getenv("DATABASE_URL", "sqlite:///./scada_historian.db"),
            operator_user=os.getenv("OPERATOR_USER", "operator_alice"),
            operator_pass=os.getenv("OPERATOR_PASS", "ControlRoom2026!"),
            viewer_user=os.getenv("VIEWER_USER", "viewer_guest"),
            viewer_pass=os.getenv("VIEWER_PASS", "Readonly2026!"),
        )
    elif active_env == "staging":
        return EnvironmentConfig(
            env_name="staging",
            base_url=os.getenv("BASE_URL", "https://staging-scada.onenergy.internal"),
            modbus_host=os.getenv("MODBUS_HOST", "edge-gateway.onenergy.internal"),
            modbus_port=int(os.getenv("MODBUS_PORT", "5020")),
            database_url=os.getenv("DATABASE_URL", None),  # Might be behind firewall
            operator_user=os.getenv("OPERATOR_USER", "operator_alice"),
            operator_pass=os.getenv("OPERATOR_PASS", "ControlRoom2026!"),
            viewer_user=os.getenv("VIEWER_USER", "viewer_guest"),
            viewer_pass=os.getenv("VIEWER_PASS", "Readonly2026!"),
        )
    else:  # local
        return EnvironmentConfig(
            env_name="local",
            base_url=os.getenv("BASE_URL", "http://127.0.0.1:8000"),
            modbus_host=os.getenv("MODBUS_HOST", "127.0.0.1"),
            modbus_port=int(os.getenv("MODBUS_PORT", "5020")),
            database_url=os.getenv("DATABASE_URL", "sqlite:///./scada_historian.db"),
            operator_user=os.getenv("OPERATOR_USER", "operator_alice"),
            operator_pass=os.getenv("OPERATOR_PASS", "ControlRoom2026!"),
            viewer_user=os.getenv("VIEWER_USER", "viewer_guest"),
            viewer_pass=os.getenv("VIEWER_PASS", "Readonly2026!"),
        )
