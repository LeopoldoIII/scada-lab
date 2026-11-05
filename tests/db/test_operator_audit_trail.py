"""SQL validation test suite for Operator Audit Trail records (NERC-CIP / SOE)."""

import json
import pytest
import requests
from sqlalchemy import text
from sqlalchemy.orm import Session


@pytest.mark.db
class TestOperatorAuditTrailDb:
    """Verifies that control actions triggered via API or UI produce auditable SQL records."""

    def test_dispatch_action_logged_in_audit_table(
        self,
        api_client: requests.Session,
        base_url: str,
        operator_headers: dict[str, str],
        db_session: Session,
    ) -> None:
        """Triggers a 3.5 MW setpoint and validates that an audit entry is committed with operator ID."""
        # 1. Dispatch setpoint via API
        resp = api_client.post(
            f"{base_url}/api/v1/controls/dispatch",
            json={"power_mw": 3.5},
            headers=operator_headers,
        )
        assert resp.status_code == 200

        # 2. Query database audit trail directly via SQL
        query = text("""
            SELECT id, operator_id, action, payload_json, status
            FROM control_audit_log
            WHERE action = 'DISPATCH_SETPOINT' AND operator_id = 'operator_alice'
            ORDER BY id DESC
            LIMIT 1
        """)
        row = db_session.execute(query).fetchone()

        assert row is not None, "Expected audit log record for DISPATCH_SETPOINT"
        assert row.operator_id == "operator_alice"
        assert row.status == "SUCCESS"
        payload = json.loads(row.payload_json)
        assert payload["power_mw"] == 3.5

