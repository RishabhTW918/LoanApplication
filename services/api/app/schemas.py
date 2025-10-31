from pydantic import BaseModel, Field, field_validator
from typing import Optional
from decimal import Decimal
from enum import Enum
import re
from datetime import datetime
from uuid import UUID


class LoanType(str, Enum):
    PERSONAL = "PERSONAL"
    HOME = "HOME"
    AUTO = "AUTO"


class ApplicationStatus(str, Enum):
    PENDING = "PENDING"
    PRE_APPROVED = "PRE_APPROVED"
    REJECTED = "REJECTED"
    MANUAL_REVIEW = "MANUAL_REVIEW"


class ApplicationCreate(BaseModel):
    pan_number: str = Field(
        ...,
        min_length=10,
        max_length=10,
        description="PAN number in format: ABCDE1234F",
    )
    applicant_name: Optional[str] = Field(
        None, max_length=255, description="Full name of the applicant"
    )
    monthly_income_inr: Decimal = Field(
        ..., gt=0, decimal_places=2, description="Gross monthly income in INR"
    )
    loan_amount_inr: Decimal = Field(
        ...,
        gt=0,
        le=10000000,  # Max 1 crore
        decimal_places=2,
        description="Requested loan amount in INR",
    )
    loan_type: LoanType = Field(..., description="Type of loan (PERSONAL, HOME, AUTO)")

    @field_validator("pan_number")
    @classmethod
    def validate_pan(cls, v: str) -> str:
        v = v.upper().strip()
        pan_pattern = r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$"

        if not re.match(pan_pattern, v):
            raise ValueError(
                "Invalid PAN format. Expected format: ABCDE1234F "
                "(5 letters, 4 digits, 1 letter)"
            )
        return v

    @field_validator("applicant_name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v:
            v = v.strip()
            if len(v) < 2:
                raise ValueError("Name must be at least 2 characters")
            if not re.match(r"^[a-zA-Z\s.]+$", v):
                raise ValueError("Name can only contain letters, spaces, and dots")
        return v

    @field_validator("monthly_income_inr")
    @classmethod
    def validate_income(cls, v: Decimal) -> Decimal:
        if v < Decimal("5000"):
            raise ValueError("Monthly income must be at least INR 5,000")
        if v > Decimal("10000000"):  # 1 crore per month
            raise ValueError("Monthly income seems unreasonably high")
        return v

    @field_validator("loan_amount_inr")
    @classmethod
    def validate_loan_amount(cls, v: Decimal) -> Decimal:
        if v < Decimal("10000"):
            raise ValueError("Loan amount must be at least INR 10,000")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "pan_number": "ABCDE1234F",
                    "applicant_name": "Rajesh Kumar",
                    "monthly_income_inr": 50000,
                    "loan_amount_inr": 200000,
                    "loan_type": "PERSONAL",
                }
            ]
        }
    }


class ApplicationResponse(BaseModel):

    application_id: UUID
    status: ApplicationStatus

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "application_id": "123e4567-e89b-12d3-a456-426614174000",
                    "status": "PENDING",
                }
            ]
        },
    }


class ApplicationStatusResponse(BaseModel):
    application_id: UUID
    status: ApplicationStatus
    cibil_score: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
