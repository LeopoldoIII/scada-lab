"""Core SCADA REST API routes for telemetry, controls, alarms, and simulation."""

import json
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.auth_routes import get_db
from app.api.schemas import (
    AlarmAckRequest,
    AlarmItem,
    ChaosConfigRequest,
    DispatchSetpointRequest,
    GenericActionResponse,
    TelemetryResponse,
)
from app.core.auth import get_current_user, require_operator_role
from app.core.database import AlarmEvent, ControlAuditLog, TelemetryHistory
from app.core.ups_simulator import UpsSimulationEngine

router = APIRouter(prefix="/api/v1", tags=["SCADA Core"])

_simulator: UpsSimulationEngine | None = None
_chaos_middleware = None


def set_simulator(simulator: UpsSimulationEngine) -> None:
    global _simulator
    _simulator = simulator


def set_chaos_middleware(middleware: Any) -> None:
    global _chaos_middleware
    _chaos_middleware = middleware


def get_simulator() -> UpsSimulationEngine:
    if _simulator is None:
        raise RuntimeError("Simulator engine not initialized")
    return _simulator


@router.get("/telemetry", response_model=TelemetryResponse)
def get_live_telemetry(sim: UpsSimulationEngine = Depends(get_simulator)) -> TelemetryResponse:
    """Returns the latest physical telemetry metrics from the MV-UPS firewall."""
    s = sim.get_telemetry()
    return TelemetryResponse(
        timestamp=s.timestamp,
        grid_voltage_kv=s.grid_voltage_kv,
        bus_frequency_hz=s.bus_frequency_hz,
        battery_soc_percent=s.battery_soc_percent,
        battery_soh_percent=s.battery_soh_percent,
        battery_temp_c=s.battery_temp_c,
        power_flow_mw=s.power_flow_mw,
        firewall_status=s.firewall_status,
        breaker_status=s.breaker_status,
        datacenter_load_mw=s.datacenter_load_mw,
        active_alarms_count=s.active_alarms_count,
    )


@router.get("/alarms", response_model=list[AlarmItem])
def get_active_alarms(sim: UpsSimulationEngine = Depends(get_simulator)) -> list[AlarmItem]:
    """Returns active alarms from the annunciator system."""
    alarms = sim.get_alarms()
    return [AlarmItem(**a) for a in alarms]


@router.post("/alarms/{alarm_code}/ack", response_model=GenericActionResponse)
def acknowledge_alarm(
    alarm_code: str,
    payload: AlarmAckRequest = None,
    user: dict = Depends(require_operator_role),
    sim: UpsSimulationEngine = Depends(get_simulator),
    db: Session = Depends(get_db),
) -> GenericActionResponse:
    """Acknowledges an active alarm. Requires OPERATOR role clearance."""
    operator_id = user.get("sub", "unknown_operator")
    success = sim.acknowledge_alarm(alarm_code, operator_id)

    # Record in database audit log
    audit_entry = ControlAuditLog(
        operator_id=operator_id,
        action="ACK_ALARM",
        payload_json=json.dumps({"alarm_code": alarm_code, "note": payload.operator_note if payload else None}),
        status="SUCCESS" if success else "FAILED",
        details=f"Alarm {alarm_code} acknowledgement requested",
    )
    db.add(audit_entry)

    # Update or insert alarm event
    alarm_db = db.query(AlarmEvent).filter(AlarmEvent.alarm_code == alarm_code).order_by(AlarmEvent.id.desc()).first()
    if alarm_db:
        alarm_db.acknowledged = True
        alarm_db.acknowledged_by = operator_id
    db.commit()

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alarm code '{alarm_code}' was not found among active alarms",
        )

    return GenericActionResponse(
        success=True,
        action="ACK_ALARM",
        message=f"Alarm '{alarm_code}' successfully acknowledged by operator {operator_id}",
    )


@router.post("/controls/dispatch", response_model=GenericActionResponse)
def dispatch_setpoint(
    payload: DispatchSetpointRequest,
    user: dict = Depends(require_operator_role),
    sim: UpsSimulationEngine = Depends(get_simulator),
    db: Session = Depends(get_db),
) -> GenericActionResponse:
    """Dispatches a new battery power setpoint (-20 MW to +20 MW). Requires OPERATOR role."""
    operator_id = user.get("sub", "unknown_operator")
    sim.set_dispatch_target(payload.power_mw)

    # Persist action to audit trail
    audit_entry = ControlAuditLog(
        operator_id=operator_id,
        action="DISPATCH_SETPOINT",
        payload_json=json.dumps({"power_mw": payload.power_mw}),
        status="SUCCESS",
        details=f"Dispatched power flow setpoint to {payload.power_mw} MW",
    )
    db.add(audit_entry)
    db.commit()

    return GenericActionResponse(
        success=True,
        action="DISPATCH_SETPOINT",
        message=f"Setpoint target of {payload.power_mw} MW registered successfully",
        details={"power_mw": payload.power_mw, "operator_id": operator_id},
    )


@router.post("/sim/trip-grid", response_model=GenericActionResponse)
def simulate_grid_trip(
    user: dict = Depends(require_operator_role),
    sim: UpsSimulationEngine = Depends(get_simulator),
    db: Session = Depends(get_db),
) -> GenericActionResponse:
    """Simulates immediate utility grid voltage collapse / blackout."""
    operator_id = user.get("sub", "unknown_operator")
    sim.trip_grid()

    # Log to audit trail and alarm events
    audit_entry = ControlAuditLog(
        operator_id=operator_id,
        action="TRIP_GRID_FAULT",
        payload_json="{}",
        status="SUCCESS",
        details="Simulated grid under-voltage fault triggered",
    )
    db.add(audit_entry)

    alarm_entry = AlarmEvent(
        alarm_code="GRID_UNDER_VOLTAGE",
        severity="CRITICAL",
        message="Grid voltage collapsed to 10.1 kV. MV-UPS isolated data center.",
        acknowledged=False,
    )
    db.add(alarm_entry)
    db.commit()

    return GenericActionResponse(
        success=True,
        action="TRIP_GRID_FAULT",
        message="Utility grid voltage collapse simulated. Firewall is now in ISLANDED mode.",
    )


@router.post("/sim/restore-grid", response_model=GenericActionResponse)
def simulate_grid_restore(
    user: dict = Depends(require_operator_role),
    sim: UpsSimulationEngine = Depends(get_simulator),
    db: Session = Depends(get_db),
) -> GenericActionResponse:
    """Restores utility grid back to nominal 13.8kV condition."""
    operator_id = user.get("sub", "unknown_operator")
    sim.restore_grid()

    audit_entry = ControlAuditLog(
        operator_id=operator_id,
        action="RESTORE_GRID",
        payload_json="{}",
        status="SUCCESS",
        details="Utility grid restored to 13.8kV",
    )
    db.add(audit_entry)
    db.commit()

    return GenericActionResponse(
        success=True,
        action="RESTORE_GRID",
        message="Utility grid restored. MV-UPS reconnecting to grid.",
    )


@router.post("/chaos/configure", response_model=GenericActionResponse)
def configure_chaos_latency(payload: ChaosConfigRequest) -> GenericActionResponse:
    """Configures artificial latency and jitter on the HTTP middleware."""
    if _chaos_middleware is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Chaos middleware is not active",
        )
    _chaos_middleware.latency_ms = payload.latency_ms
    _chaos_middleware.jitter_ms = payload.jitter_ms

    return GenericActionResponse(
        success=True,
        action="CONFIGURE_CHAOS",
        message=f"Chaos latency set to {payload.latency_ms}ms (jitter: {payload.jitter_ms}ms)",
    )


@router.get("/audit/logs")
def get_audit_logs(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """Returns recent operator audit log records."""
    logs = db.query(ControlAuditLog).order_by(ControlAuditLog.id.desc()).limit(limit).all()
    return [
        {
            "id": l.id,
            "timestamp": l.timestamp.isoformat() if l.timestamp else None,
            "operator_id": l.operator_id,
            "action": l.action,
            "payload": json.loads(l.payload_json) if l.payload_json else {},
            "status": l.status,
            "details": l.details,
        }
        for l in logs
    ]

