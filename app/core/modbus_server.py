"""Modbus TCP Industrial Server representing fieldbus PLC / RTU communication."""

import asyncio
import logging
import threading
from typing import Any

from pymodbus.datastore import (
    ModbusDeviceContext,
    ModbusSequentialDataBlock,
    ModbusServerContext,
)
from pymodbus.server import StartAsyncTcpServer

from app.core.ups_simulator import TelemetrySnapshot, UpsSimulationEngine

logger = logging.getLogger("scada_modbus")

# Register map definitions (Holding Registers)
REG_VOLTAGE = 0        # Value * 100 (e.g., 1380 = 13.80 kV)
REG_FREQUENCY = 1      # Value * 100 (e.g., 6000 = 60.00 Hz)
REG_SOC = 2            # Value * 100 (e.g., 8450 = 84.50 %)
REG_POWER = 3          # Value * 100 (signed int16, offset 10000 -> 10000 + MW*100)
REG_FIREWALL_MODE = 4  # 0: GRID_CONNECTED, 1: ISLANDED
REG_BREAKER = 5        # 0: CLOSED, 1: TRIPPED
REG_ALARMS = 6         # Total active alarms count
REG_SETPOINT = 10      # Writable setpoint * 100


class ScadaModbusServer:
    """Manages the lifecycle of the local Modbus TCP industrial fieldbus server."""

    def __init__(self, simulator: UpsSimulationEngine, port: int = 5020) -> None:
        self.simulator = simulator
        self.port = port
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

        # Initialize holding registers block (100 registers)
        self.datablock = ModbusSequentialDataBlock(1, [0] * 100)
        self.device_context = ModbusDeviceContext(hr=self.datablock)
        self.context = ModbusServerContext(
            devices=self.device_context,
            single=True,
        )

        # Wire simulator telemetry listener to update registers
        self.simulator.on_telemetry_listeners.append(self._on_telemetry_updated)
        # Populate initial values
        self._on_telemetry_updated(self.simulator.get_telemetry())

    def _on_telemetry_updated(self, snapshot: TelemetrySnapshot) -> None:
        """Pushes physical snapshot values into Modbus holding registers."""
        try:
            v_val = int(round(snapshot.grid_voltage_kv * 100))
            f_val = int(round(snapshot.bus_frequency_hz * 100))
            soc_val = int(round(snapshot.battery_soc_percent * 100))
            p_val = int(round(10000 + (snapshot.power_flow_mw * 100)))
            mode_val = 1 if snapshot.firewall_status == "ISLANDED" else 0
            breaker_val = 1 if snapshot.breaker_status == "TRIPPED" else 0
            alarms_val = snapshot.active_alarms_count

            # Directly update in-memory holding registers values in the SimDevice
            simdata = getattr(self.device_context.simdevice, "simdata", None)
            if simdata and len(simdata) > 2 and simdata[2]:
                simdata[2][0].values[0:7] = [v_val, f_val, soc_val, p_val, mode_val, breaker_val, alarms_val]
        except Exception as exc:
            logger.error(f"Failed to sync registers to Modbus datastore: {exc}")

    def start(self) -> None:
        """Starts Modbus TCP server in a dedicated background daemon thread."""
        self._thread = threading.Thread(target=self._run_server, daemon=True)
        self._thread.start()

    def _run_server(self) -> None:
        """Runs asynchronous Modbus TCP server loop."""
        asyncio.run(self._async_serve())

    async def _async_serve(self) -> None:
        logger.info(f"Starting Modbus TCP server on port {self.port}...")
        try:
            await StartAsyncTcpServer(
                context=self.context,
                address=("0.0.0.0", self.port),
            )
        except Exception as exc:
            logger.error(f"Modbus server exception: {exc}")
