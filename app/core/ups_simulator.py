"""Physics simulation engine for Medium-Voltage (13.8kV) UPS and BESS battery storage."""

import datetime
import random
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class TelemetrySnapshot:
    """Current snapshot of all SCADA electrical and battery metrics."""

    timestamp: str
    grid_voltage_kv: float
    bus_frequency_hz: float
    battery_soc_percent: float
    battery_soh_percent: float
    battery_temp_c: float
    power_flow_mw: float
    firewall_status: str  # GRID_CONNECTED, ISLANDED, EMERGENCY_BACKUP
    breaker_status: str   # CLOSED, TRIPPED
    datacenter_load_mw: float
    active_alarms_count: int


@dataclass
class SimulatedAlarm:
    """Active or historical alarm item."""

    code: str
    severity: str  # INFO, WARNING, CRITICAL
    message: str
    triggered_at: str
    acknowledged: bool = False
    acknowledged_by: str | None = None
    acknowledged_at: str | None = None


class UpsSimulationEngine:
    """Simulates real-world power engineering physics for an industrial MV-UPS firewall."""

    def __init__(self, db_session_factory: Any = None) -> None:
        self.db_session_factory = db_session_factory
        self._lock = threading.Lock()
        self._running = False
        self._thread: threading.Thread | None = None

        # Electrical setpoints & baseline state
        self.nominal_voltage_kv = 13.8
        self.grid_voltage_kv = 13.8
        self.bus_frequency_hz = 60.0
        self.battery_soc_percent = 84.5
        self.battery_soh_percent = 99.1
        self.battery_temp_c = 23.4
        self.power_flow_mw = 0.0
        self.target_power_mw = 0.0
        self.datacenter_load_mw = 4.8
        self.firewall_status = "GRID_CONNECTED"
        self.breaker_status = "CLOSED"

        # Fault state flags
        self.is_grid_faulted = False

        # Active alarms dictionary: code -> SimulatedAlarm
        self.alarms: dict[str, SimulatedAlarm] = {}

        # Callbacks for telemetry updates (e.g. Modbus sync)
        self.on_telemetry_listeners: list[Callable[[TelemetrySnapshot], None]] = []

    def start(self) -> None:
        """Starts background physics tick loop."""
        with self._lock:
            if not self._running:
                self._running = True
                self._thread = threading.Thread(target=self._run_loop, daemon=True)
                self._thread.start()

    def stop(self) -> None:
        """Stops background physics tick loop."""
        with self._lock:
            self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)

    def _run_loop(self) -> None:
        """Continuous simulation loop ticking every 1.0 second."""
        while self._running:
            self.tick()
            time.sleep(1.0)

    def tick(self) -> TelemetrySnapshot:
        """Executes a single physics simulation tick."""
        with self._lock:
            now_iso = datetime.datetime.utcnow().isoformat() + "Z"

            if self.is_grid_faulted:
                # Severe under-voltage on utility grid side
                self.grid_voltage_kv = round(random.uniform(9.8, 10.5), 2)
                self.bus_frequency_hz = round(random.uniform(58.8, 59.4), 2)
                self.firewall_status = "ISLANDED"
                self.breaker_status = "TRIPPED"
                # Battery supplies the entire data center load cleanly
                self.power_flow_mw = -round(self.datacenter_load_mw, 2)
                self.battery_soc_percent = max(0.0, round(self.battery_soc_percent - 0.05, 2))
                self.battery_temp_c = round(min(45.0, self.battery_temp_c + 0.02), 2)

                # Ensure alarm is present
                if "GRID_UNDER_VOLTAGE" not in self.alarms:
                    self.alarms["GRID_UNDER_VOLTAGE"] = SimulatedAlarm(
                        code="GRID_UNDER_VOLTAGE",
                        severity="CRITICAL",
                        message=f"Grid voltage dropped to {self.grid_voltage_kv}kV. Firewall isolated data center.",
                        triggered_at=now_iso,
                    )
            else:
                # Normal grid conditions with subtle electrical noise
                jitter_v = random.uniform(-0.04, 0.04)
                jitter_f = random.uniform(-0.015, 0.015)
                self.grid_voltage_kv = round(self.nominal_voltage_kv + jitter_v, 2)
                self.bus_frequency_hz = round(60.0 + jitter_f, 2)
                self.firewall_status = "GRID_CONNECTED"
                self.breaker_status = "CLOSED"

                # Gradually converge power flow towards target setpoint
                diff = self.target_power_mw - self.power_flow_mw
                if abs(diff) > 0.05:
                    self.power_flow_mw = round(self.power_flow_mw + (diff * 0.4), 2)
                else:
                    self.power_flow_mw = self.target_power_mw

                # Battery temperature responds to power flow
                if abs(self.power_flow_mw) > 2.0:
                    self.battery_temp_c = round(min(40.0, self.battery_temp_c + 0.01), 2)
                else:
                    self.battery_temp_c = round(max(22.0, self.battery_temp_c - 0.01), 2)

            snapshot = TelemetrySnapshot(
                timestamp=now_iso,
                grid_voltage_kv=self.grid_voltage_kv,
                bus_frequency_hz=self.bus_frequency_hz,
                battery_soc_percent=self.battery_soc_percent,
                battery_soh_percent=self.battery_soh_percent,
                battery_temp_c=self.battery_temp_c,
                power_flow_mw=self.power_flow_mw,
                firewall_status=self.firewall_status,
                breaker_status=self.breaker_status,
                datacenter_load_mw=self.datacenter_load_mw,
                active_alarms_count=len(self.alarms),
            )

        # Notify external protocol bridges (e.g., Modbus)
        for listener in self.on_telemetry_listeners:
            try:
                listener(snapshot)
            except Exception:
                pass

        # Persist snapshot to database if factory is provided
        if self.db_session_factory:
            self._persist_to_historian(snapshot)

        return snapshot

    def _persist_to_historian(self, snapshot: TelemetrySnapshot) -> None:
        """Writes current telemetry to the Historian table."""
        try:
            from app.core.database import TelemetryHistory
            with self.db_session_factory() as session:
                entry = TelemetryHistory(
                    grid_voltage_kv=snapshot.grid_voltage_kv,
                    bus_frequency_hz=snapshot.bus_frequency_hz,
                    battery_soc_percent=snapshot.battery_soc_percent,
                    battery_temp_c=snapshot.battery_temp_c,
                    power_flow_mw=snapshot.power_flow_mw,
                    firewall_status=snapshot.firewall_status,
                )
                session.add(entry)
                session.commit()
        except Exception:
            pass

    def trip_grid(self) -> None:
        """Simulates immediate external grid blackout / severe voltage collapse."""
        with self._lock:
            self.is_grid_faulted = True
            now_iso = datetime.datetime.utcnow().isoformat() + "Z"
            self.alarms["GRID_UNDER_VOLTAGE"] = SimulatedAlarm(
                code="GRID_UNDER_VOLTAGE",
                severity="CRITICAL",
                message="Grid voltage collapsed to 10.1 kV. Firewall tripped to protect data center.",
                triggered_at=now_iso,
            )

    def restore_grid(self) -> None:
        """Restores normal utility grid conditions and reconnects the firewall."""
        with self._lock:
            self.is_grid_faulted = False
            self.alarms.pop("GRID_UNDER_VOLTAGE", None)

    def set_dispatch_target(self, target_mw: float) -> None:
        """Sets new power dispatch setpoint."""
        with self._lock:
            self.target_power_mw = float(target_mw)

    def acknowledge_alarm(self, alarm_code: str, operator_id: str) -> bool:
        """Acknowledges an active alarm by code and operator."""
        with self._lock:
            alarm = self.alarms.get(alarm_code)
            if alarm:
                alarm.acknowledged = True
                alarm.acknowledged_by = operator_id
                alarm.acknowledged_at = datetime.datetime.utcnow().isoformat() + "Z"
                return True
            return False

    def get_telemetry(self) -> TelemetrySnapshot:
        """Returns the current state snapshot."""
        return self.tick()

    def get_alarms(self) -> list[dict[str, Any]]:
        """Returns list of all active alarms."""
        with self._lock:
            return [
                {
                    "code": a.code,
                    "severity": a.severity,
                    "message": a.message,
                    "triggered_at": a.triggered_at,
                    "acknowledged": a.acknowledged,
                    "acknowledged_by": a.acknowledged_by,
                    "acknowledged_at": a.acknowledged_at,
                }
                for a in self.alarms.values()
            ]

