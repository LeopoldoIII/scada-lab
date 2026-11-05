"""Main application entry point orchestrating FastAPI, Modbus TCP, SQLite DB, and Web HMI."""

import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import auth_routes, routes
from app.core.auth import hash_password
from app.core.chaos_middleware import ChaosMiddleware
from app.core.database import User, init_database
from app.core.modbus_server import ScadaModbusServer
from app.core.ups_simulator import UpsSimulationEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("scada_main")

# Database setup
DB_URL = os.getenv("DATABASE_URL", "sqlite:///./scada_historian.db")
db_session_factory = init_database(DB_URL)
auth_routes.set_db_factory(db_session_factory)

# Initialize simulator and Modbus server
simulator = UpsSimulationEngine(db_session_factory=db_session_factory)
routes.set_simulator(simulator)

MODBUS_PORT = int(os.getenv("MODBUS_PORT", "5020"))
modbus_server = ScadaModbusServer(simulator=simulator, port=MODBUS_PORT)


def seed_default_users() -> None:
    """Seeds initial default test accounts for Operator and Viewer roles."""
    with db_session_factory() as session:
        # Operator Alice
        if not session.query(User).filter(User.username == "operator_alice").first():
            alice = User(
                username="operator_alice",
                password_hash=hash_password("ControlRoom2026!"),
                role="OPERATOR",
            )
            session.add(alice)

        # Viewer Guest
        if not session.query(User).filter(User.username == "viewer_guest").first():
            guest = User(
                username="viewer_guest",
                password_hash=hash_password("Readonly2026!"),
                role="VIEWER",
            )
            session.add(guest)

        session.commit()
    logger.info("Default user accounts seeded (operator_alice, viewer_guest)")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager starting up background physics simulator and Modbus server."""
    logger.info("Initializing SCADA database and default users...")
    seed_default_users()

    logger.info("Starting BESS & MV-UPS physics simulation engine...")
    simulator.start()

    logger.info(f"Starting Modbus TCP industrial fieldbus server on port {MODBUS_PORT}...")
    modbus_server.start()

    yield

    logger.info("Stopping physics simulation engine...")
    simulator.stop()


app = FastAPI(
    title="Industrial SCADA BESS & MV-UPS Control Gateway",
    description="Industrial Control System simulator and REST API for medium-voltage UPS data center protection.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Chaos & latency injection middleware
chaos_mw = ChaosMiddleware(app)
app.add_middleware(ChaosMiddleware)
routes.set_chaos_middleware(chaos_mw)

# Register routers
app.include_router(auth_routes.router)
app.include_router(routes.router)


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint for Docker container readiness probes."""
    return {
        "status": "healthy",
        "service": "scada-core",
        "modbus_port": MODBUS_PORT,
        "database": "connected",
    }


# Mount static assets for Industrial Web HMI
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    logger.info(f"Launching SCADA Web Gateway on http://0.0.0.0:{port}")
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)

