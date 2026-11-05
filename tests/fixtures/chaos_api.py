"""REST API chaos fixtures providing custom HTTP adapters for transient failure testing."""

import pytest
import requests
from requests.adapters import HTTPAdapter


class TransientFaultAdapter(HTTPAdapter):
    """Custom HTTP adapter that fails the first N attempts with HTTP 503 before passing."""

    def __init__(self, failure_budget: int = 2, status_code: int = 503):
        super().__init__()
        self.failure_budget = failure_budget
        self.attempts = 0
        self.status_code = status_code

    def send(self, request, **kwargs):
        self.attempts += 1
        if self.attempts <= self.failure_budget:
            resp = requests.Response()
            resp.status_code = self.status_code
            resp._content = b'{"detail": "SCADA Gateway Temporarily Overloaded", "retryable": true}'
            resp.request = request
            return resp
        return super().send(request, **kwargs)


@pytest.fixture
def transient_503_session():
    """Provides a requests.Session configured to fail twice with HTTP 503 before succeeding."""
    session = requests.Session()
    adapter = TransientFaultAdapter(failure_budget=2, status_code=503)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

