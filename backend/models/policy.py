import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Float, Date, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class PolicyRecord(Base):
    __tablename__ = "policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_number = Column(String(50), unique=True, nullable=False, index=True)
    policy_type = Column(
        Enum("AUTO", "HOME", "HEALTH", "TRAVEL", "COMMERCIAL", "RENTERS", name="policy_type"),
        nullable=False,
    )
    holder_name = Column(String(255), nullable=False)
    holder_email = Column(String(255))
    effective_date = Column(Date, nullable=False)
    expiration_date = Column(Date, nullable=False)
    is_active = Column(Boolean, default=True)

    # Coverage limits
    coverage_limit = Column(Float)
    deductible = Column(Float)
    premium_amount = Column(Float)
    sub_limits = Column(Text)

    # Policy document
    document_text = Column(Text, nullable=False)
    document_path = Column(String(500))
    chunk_count = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
