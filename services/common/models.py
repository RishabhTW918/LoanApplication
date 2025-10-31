from sqlalchemy import Column, String, DECIMAL, Integer, TIMESTAMP, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
from .database import Base

class LoanApplication(Base):
    __tablename__ = "applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pan_number = Column(String(10), nullable=False, index=True)
    applicant_name = Column(String(255))
    monthly_income_inr = Column(DECIMAL(12, 2), nullable=False)
    loan_amount_inr = Column(DECIMAL(12, 2), nullable=False)
    loan_type = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="PENDING", index=True)
    cibil_score = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.now(timezone.utc), index=True)
    updated_at = Column(TIMESTAMP, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    __table_args__ = (
        CheckConstraint("monthly_income_inr > 0", name="chk_monthly_income_positive"),
        CheckConstraint("loan_amount_inr > 0", name="chk_loan_amount_positive"),
        CheckConstraint(
            "status IN ('PENDING', 'PRE_APPROVED', 'REJECTED', 'MANUAL_REVIEW')",
            name="chk_valid_status"
        ),
        CheckConstraint(
            "loan_type IN ('PERSONAL', 'HOME', 'AUTO')",
            name="chk_valid_loan_type"
        ),
        CheckConstraint(
            "cibil_score IS NULL OR (cibil_score >= 300 AND cibil_score <= 900)",
            name="chk_valid_cibil_score"
        ),
    )

    def __repr__(self):
        return f"<Application(id={self.id}, pan={self.pan_number}, status={self.status})>"