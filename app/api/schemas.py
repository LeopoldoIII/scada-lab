"""Pydantic schemas for SCADA REST API requests and responses."""

from typing import Any
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Credentials payload for operator authentication."""

    username: str = Field(..., example="operator_alice")
    password: str = Field(..., example="ControlRoom2026!")


class TokenResponse(BaseModel):
    """JWT bearer token and operator profile envelope."""

    access_token: str
    token_type: str = "bearer"
    username: str
    role: str  # VIEWER or OPERATOR


class UserResponse(BaseModel):
    """User profile details."""

    id: int
    username: str
    role: str


class TelemetryResponse(BaseModel):
    """Real-time SCADA telemetry snapshot."""

    timestamp: str
    grid_voltage_kv: float
    bus_frequency_hz: float
    battery_soc_percent: float
    battery_soh_percent: float
    battery_temp_c: float
    power_flow_mw: float
    firewall_status: str
    breaker_status: str
    datacenter_load_mw: float
    active_alarms_count: int


class AlarmItem(BaseModel):
    """Alarm item definition."""

    code: str
    severity: str
    message: str
    triggered_at: str
    acknowledged: bool
    acknowledged_by: str | None = None
    acknowledged_at: str | None = None


class AlarmAckRequest(BaseModel):
    """Payload to acknowledge an active alarm."""

    operator_note: str | None = None


class DispatchSetpointRequest(BaseModel):
    """Setpoint command to dispatch or charge battery storage."""

    power_mw: float = Field(..., ge=-20.0, le=20.0, description="Target power flow (-20MW to +20MW)")


class ChaosConfigRequest(BaseModel):
    """Configures artificial server latency and jitter."""

    latency_ms: float = Field(..., ge=0.0, le=10000.0)
    jitter_ms: float = Field(0.0, ge=0.0, le=5000.0)


class GenericActionResponse(BaseModel):
    """Standard action execution confirmation."""

    success: bool
    action: str
    message: str
    details: dict[str, Any] | None = None

