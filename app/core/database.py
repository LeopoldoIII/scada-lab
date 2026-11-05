"""Industrial Database and Historian models for SCADA telemetry and events."""

import datetime
from typing import Generator
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy declarative models."""
    pass


class User(Base):
    """User account entity with Role-Based Access Control (RBAC)."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="VIEWER")  # VIEWER or OPERATOR
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class TelemetryHistory(Base):
    """Industrial Historian table recording continuous time-series process metrics."""

    __tablename__ = "telemetry_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    grid_voltage_kv = Column(Float, nullable=False)
    bus_frequency_hz = Column(Float, nullable=False)
    battery_soc_percent = Column(Float, nullable=False)
    battery_temp_c = Column(Float, nullable=False)
    power_flow_mw = Column(Float, nullable=False)
    firewall_status = Column(String(20), nullable=False)  # GRID_CONNECTED, ISLANDED


class AlarmEvent(Base):
    """Sequence of Events (SOE) alarm logs and operator acknowledgement status."""

    __tablename__ = "alarm_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    alarm_code = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False)  # INFO, WARNING, CRITICAL
    message = Column(Text, nullable=False)
    triggered_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    acknowledged = Column(Boolean, default=False, nullable=False)
    acknowledged_by = Column(String(50), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    cleared = Column(Boolean, default=False, nullable=False)
    cleared_at = Column(DateTime, nullable=True)


class ControlAuditLog(Base):
    """Audit trail recording every control setpoint and breaker action with operator identity."""

    __tablename__ = "control_audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    operator_id = Column(String(50), nullable=False, index=True)
    action = Column(String(50), nullable=False)  # DISPATCH_SETPOINT, TRIP_GRID, ACK_ALARM
    payload_json = Column(Text, nullable=False)
    status = Column(String(20), nullable=False)  # SUCCESS, REJECTED, FAILED
    details = Column(String(255), nullable=True)


def init_database(db_url: str = "sqlite:///./scada_historian.db") -> sessionmaker[Session]:
    """Initializes the database schema and returns a session factory."""
    engine = create_engine(db_url, connect_args={"check_same_thread": False} if "sqlite" in db_url else {})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)

