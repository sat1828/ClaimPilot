import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Text, Enum, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class DecisionRecord(Base):
    __tablename__ = "claim_decisions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False, index=True)
    decision = Column(
        Enum("APPROVED", "REJECTED", "ESCALATED", name="decision_type"),
        nullable=False,
    )
    settlement_amount = Column(Float)
    deductible_applied = Column(Float)
    payout_amount = Column(Float)
    reasoning_chain = Column(JSONB, default=list)
    confidence_score = Column(Float)
    decision_letter_path = Column(String(500))

    # Escalation tracking
    is_human_reviewed = Column(Boolean, default=False)
    human_adjuster_id = Column(String(100))
    human_decision = Column(String(50))
    human_notes = Column(Text)
    human_reviewed_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FraudScoreRecord(Base):
    __tablename__ = "fraud_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False, index=True)
    claimant_id = Column(String(100), index=True)
    fraud_probability = Column(Float, nullable=False)
    risk_tier = Column(Enum("LOW", "MEDIUM", "HIGH", name="risk_tier"), nullable=False)
    ml_score = Column(Float)
    rule_based_score = Column(Float)
    cited_flags = Column(JSONB, default=list)
    model_version = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)


class AgentAuditLog(Base):
    __tablename__ = "agent_audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False, index=True)
    agent_name = Column(String(100), nullable=False)
    action = Column(String(255), nullable=False)
    tool_used = Column(String(100))
    input_summary = Column(Text)
    output_summary = Column(Text)
    confidence_score = Column(Float)
    duration_ms = Column(Text)
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    reasoning = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
