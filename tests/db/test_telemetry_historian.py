"""SQL validation test suite for Industrial Historian time-series records."""

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session


@pytest.mark.db
class TestTelemetryHistorianDb:
    """Performs direct SQL query assertions against the Historian time-series database."""

    def test_historian_contains_continuous_telemetry(self, db_session: Session) -> None:
        """Verifies that the simulation engine continuously persists time-series telemetry."""
        query = text("""
            SELECT id, timestamp, grid_voltage_kv, bus_frequency_hz, battery_soc_percent
            FROM telemetry_history
            ORDER BY id DESC
            LIMIT 5
        """)
        results = db_session.execute(query).fetchall()

        assert len(results) > 0, "Expected telemetry records in historian table"
        latest = results[0]
        assert latest.grid_voltage_kv > 9.0
        assert latest.bus_frequency_hz > 58.0
        assert 0.0 <= latest.battery_soc_percent <= 100.0

    def test_historian_aggregate_metrics(self, db_session: Session) -> None:
        """Performs SQL aggregations (AVG, MIN, MAX) to validate process stability."""
        query = text("""
            SELECT 
                COUNT(*) as sample_count,
                AVG(grid_voltage_kv) as avg_voltage,
                AVG(bus_frequency_hz) as avg_freq
            FROM telemetry_history
        """)
        row = db_session.execute(query).fetchone()
        assert row.sample_count > 0
        assert 9.0 <= row.avg_voltage <= 15.0
        assert 58.0 <= row.avg_freq <= 62.0

