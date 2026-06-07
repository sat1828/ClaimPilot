from typing import TypedDict, Optional, Any
from datetime import datetime


class ClaimPayload(TypedDict, total=False):
    claim_id: str
    claim_number: str
    claim_type: str  # auto, medical, property, travel, etc.
    claimant_name: str
    claimant_email: str
    claimant_phone: str
    claimant_address: str
    policy_number: str
    policy_type: str
    event_date: str
    event_description: str
    incident_location: str
    incident_lat: float
    incident_lon: float
    claim_amount: float
    currency: str
    supporting_documents: list[dict]
    raw_input_type: str
    raw_input_path: str
    submission_date: str


class ValidationResult(TypedDict, total=False):
    coverage_status: str  # COVERED, NOT_COVERED, PARTIALLY_COVERED
    policy_period_valid: bool
    missing_fields: list[str]
    coverage_type: str
    policy_limits: dict
    deductible: float
    sub_limits: dict
    policy_exclusions: list[str]
    reasoning: str
    confidence_score: float


class InvestigationBundle(TypedDict, total=False):
    weather_data: Optional[dict]
    incident_reports: list[dict]
    fhir_records: Optional[dict]
    icd10_validation: Optional[dict]
    geocode_data: Optional[dict]
    disaster_records: Optional[dict]
    evidence_items: list[dict]
    evidence_gaps: list[str]
    investigation_summary: str
    confidence_score: float


class FraudFlag(TypedDict, total=False):
    flag_type: str
    severity: str  # LOW, MEDIUM, HIGH
    description: str
    evidence: str
    source: str


class FraudAssessment(TypedDict, total=False):
    fraud_probability_score: float
    risk_tier: str  # LOW, MEDIUM, HIGH
    ml_score: float
    rule_based_score: float
    cited_flags: list[FraudFlag]
    duplicate_claim_check: Optional[dict]
    timing_anomaly_check: Optional[dict]
    inconsistency_check: Optional[dict]
    network_analysis: Optional[dict]
    reasoning: str
    confidence_score: float


class SettlementDecision(TypedDict, total=False):
    decision: str  # APPROVE, REJECT, ESCALATE
    settlement_amount: float
    deductible_applied: float
    payout_amount: float
    policy_limits_used: dict
    losses_assessed: list[dict]
    reasoning_chain: list[dict]
    decision_letter_text: str
    confidence_score: float


class ClaimState(TypedDict, total=False):
    claim_id: str
    raw_input: dict
    claim_payload: ClaimPayload
    validation_result: ValidationResult
    investigation_bundle: InvestigationBundle
    fraud_assessment: FraudAssessment
    settlement_decision: SettlementDecision
    reasoning_chain: list[dict]
    current_status: str
    current_agent: str
    error_log: list[str]
    retry_count: dict
    pipeline_started_at: str
    pipeline_completed_at: str
