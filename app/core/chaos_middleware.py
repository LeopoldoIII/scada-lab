"""Middleware for injecting artificial network latency, jitter, and transient faults."""

import asyncio
import random
import time
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class ChaosMiddleware(BaseHTTPMiddleware):
    """Intercepts incoming HTTP requests to inject configurable latency and jitter."""

    def __init__(self, app: Any, default_latency_ms: float = 0.0, default_jitter_ms: float = 0.0) -> None:
        super().__init__(app)
        self.latency_ms = default_latency_ms
        self.jitter_ms = default_jitter_ms
        self.drop_rate = 0.0

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check header override (useful for specific test runs)
        custom_lag = request.headers.get("X-Simulate-Lag-Ms")
        if custom_lag:
            try:
                lag = float(custom_lag)
                await asyncio.sleep(lag / 1000.0)
            except ValueError:
                pass
        elif self.latency_ms > 0:
            jitter = random.uniform(0, self.jitter_ms) if self.jitter_ms > 0 else 0
            total_delay_sec = (self.latency_ms + jitter) / 1000.0
            await asyncio.sleep(total_delay_sec)

        response = await call_next(request)
        return response

