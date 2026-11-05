"""Industrial OT protocol test suite verifying Modbus TCP holding registers."""

import pytest
from pymodbus.client import ModbusTcpClient
from tests.config import EnvironmentConfig


@pytest.mark.modbus
class TestModbusRegisters:
    """Verifies Purdue Level 1/2 fieldbus communication via raw Modbus TCP registers."""

    def test_read_live_holding_registers(self, test_config: EnvironmentConfig, live_server: None) -> None:
        """Reads registers from the Modbus TCP server and verifies physical scaling."""
        client = ModbusTcpClient(host=test_config.modbus_host, port=test_config.modbus_port, timeout=3.0)
        connected = client.connect()
        assert connected, f"Could not connect to Modbus TCP server at {test_config.modbus_host}:{test_config.modbus_port}"

        try:
            # Read holding registers at starting address 0
            result = client.read_holding_registers(address=0, count=7)
            assert not result.isError(), f"Modbus read error: {result}"
            regs = result.registers
            assert len(regs) == 7

            voltage_kv = regs[0] / 100.0
            freq_hz = regs[1] / 100.0
            soc_percent = regs[2] / 100.0
            power_flow_mw = (regs[3] - 10000) / 100.0
            mode_val = regs[4]
            breaker_val = regs[5]

            # Assert valid physical ranges at the fieldbus protocol layer
            assert 9.0 <= voltage_kv <= 15.0
            assert 58.0 <= freq_hz <= 62.0
            assert 0.0 <= soc_percent <= 100.0
            assert mode_val in [0, 1]
            assert breaker_val in [0, 1]
        finally:
            client.close()
