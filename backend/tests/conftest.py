import pytest
import uuid
from datetime import datetime


@pytest.fixture
def sample_claim_payload():
    return {
        "claim_id": str(uuid.uuid4()),
        "claim_number": f"CP-20240601-{str(uuid.uuid4())[:8].upper()}",
        "claim_type": "auto",
        "claimant_name": "John Doe",
        "claimant_email": "john.doe@example.com",
        "policy_number": "POL-AUTO-001",
        "policy_type": "AUTO",
        "event_date": "2024-06-20",
        "event_description": "Rear-end collision at intersection of Main St and Oak Ave. The claimant was stopped at a red light when another vehicle struck them from behind. Airbags deployed.",
        "incident_location": "Main St & Oak Ave, Springfield",
        "incident_lat": 42.1015,
        "incident_lon": -72.5898,
        "claim_amount": 12500.00,
        "currency": "USD",
        "submission_date": "2024-06-21",
        "raw_input_type": "text",
    }


@pytest.fixture
def sample_state(sample_claim_payload):
    return {
        "claim_id": sample_claim_payload["claim_id"],
        "raw_input": {"type": "text", "content": str(sample_claim_payload)},
        "claim_payload": sample_claim_payload,
        "validation_result": {},
        "investigation_bundle": {},
        "fraud_assessment": {},
        "settlement_decision": {},
        "reasoning_chain": [],
        "current_status": "SUBMITTED",
        "current_agent": "",
        "error_log": [],
        "retry_count": {},
        "pipeline_started_at": datetime.utcnow().isoformat(),
        "pipeline_completed_at": "",
    }
