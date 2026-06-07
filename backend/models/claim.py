import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Text, Enum, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class ClaimRecord(Base):
    __tablename__ = "claims"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_number = Column(String(50), unique=True, nullable=False, index=True)

    # Claimant
    claimant_name = Column(String(255), nullable=False)
    claimant_email = Column(String(255))
    claimant_phone = Column(String(50))
    claimant_address = Column(Text)

    # Policy
    policy_number = Column(String(50), nullable=False, index=True)
    policy_type = Column(String(50))

    # Claim details
    claim_type = Column(String(50), nullable=False)
    event_date = Column(DateTime, nullable=False)
    submission_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    event_description = Column(Text)
    claim_amount = Column(Float)
    currency = Column(String(10), default="USD")

    # Location
    incident_location = Column(Text)
    incident_lat = Column(Float)
    incident_lon = Column(Float)

    # Status
    status = Column(
        Enum(
            "INTAKE_COMPLETE",
            "VALIDATION_PASSED",
            "VALIDATION_FAILED",
            "INVESTIGATION_COMPLETE",
            "FRAUD_ASSESSMENT_COMPLETE",
            "SETTLEMENT_READY",
            "APPROVED",
            "REJECTED",
            "ESCALATED",
            "HUMAN_REVIEW",
            "CLOSED",
            name="claim_status",
        ),
        nullable=False,
        default="INTAKE_COMPLETE",
    )

    # Raw input metadata
    raw_input_type = Column(String(50))
    raw_input_path = Column(Text)

    # Audit
    reasoning_chain = Column(JSONB, default=list)
    current_agent = Column(String(50))
    error_log = Column(JSONB, default=list)
    retry_count = Column(JSONB, default=dict)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
