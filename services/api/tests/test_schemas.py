import unittest

import pytest
from pydantic import ValidationError
from decimal import Decimal
from uuid import UUID
from datetime import datetime
from ..app.schemas import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationStatusResponse,
    LoanType,
    ApplicationStatus,
    ErrorResponse
)


class TestApplicationCreate(unittest.TestCase):
    """Test suite for ApplicationCreate schema and validators."""

    VALID_PAN = "ABCDE1234F"
    VALID_NAME = "Rajesh Kumar"
    VALID_INCOME = Decimal("50000")
    VALID_LOAN_AMOUNT = Decimal("200000")
    VALID_LOAN_TYPE = LoanType.PERSONAL

    def test_create_valid_application(self):
        """Test creating a valid application with all fields."""
        app = ApplicationCreate(
            pan_number=self.VALID_PAN,
            applicant_name=self.VALID_NAME,
            monthly_income_inr=self.VALID_INCOME,
            loan_amount_inr=self.VALID_LOAN_AMOUNT,
            loan_type=self.VALID_LOAN_TYPE
        )

        assert app.pan_number == self.VALID_PAN
        assert app.applicant_name == self.VALID_NAME
        assert app.monthly_income_inr == self.VALID_INCOME
        assert app.loan_amount_inr == self.VALID_LOAN_AMOUNT
        assert app.loan_type == self.VALID_LOAN_TYPE

    def test_create_application_without_name(self):
        """Test creating application without optional name field."""
        app = ApplicationCreate(
            pan_number=self.VALID_PAN,
            monthly_income_inr=self.VALID_INCOME,
            loan_amount_inr=self.VALID_LOAN_AMOUNT,
            loan_type=self.VALID_LOAN_TYPE
        )

        assert app.applicant_name is None

    # PAN Validation Tests
    def test_pan_validation_valid_format(self):
        """Test PAN validation with valid format."""
        app = ApplicationCreate(
            pan_number="ABCDE1234F",
            monthly_income_inr=self.VALID_INCOME,
            loan_amount_inr=self.VALID_LOAN_AMOUNT,
            loan_type=self.VALID_LOAN_TYPE
        )
        assert app.pan_number == "ABCDE1234F"

    def test_pan_validation_uppercase_conversion(self):
        """Test that lowercase PAN is converted to uppercase."""
        app = ApplicationCreate(
            pan_number="abcde1234f",
            monthly_income_inr=self.VALID_INCOME,
            loan_amount_inr=self.VALID_LOAN_AMOUNT,
            loan_type=self.VALID_LOAN_TYPE
        )
        assert app.pan_number == "ABCDE1234F"

    def test_pan_validation_case_insensitive(self):
        """Test that PAN is case insensitive (converted to uppercase)."""
        # Mixed case should be converted to uppercase
        app = ApplicationCreate(
            pan_number="abCDe1234f",
            monthly_income_inr=self.VALID_INCOME,
            loan_amount_inr=self.VALID_LOAN_AMOUNT,
            loan_type=self.VALID_LOAN_TYPE
        )
        assert app.pan_number == "ABCDE1234F"

    def test_pan_validation_invalid_too_short(self):
        """Test PAN validation fails with too short PAN."""
        with pytest.raises(ValidationError) as exc_info:
            ApplicationCreate(
                pan_number="ABCD123F",  # Too short
                monthly_income_inr=self.VALID_INCOME,
                loan_amount_inr=self.VALID_LOAN_AMOUNT,
                loan_type=self.VALID_LOAN_TYPE
            )
        assert "String should have at least 10 characters" in str(exc_info.value)

    def test_pan_validation_invalid_too_long(self):
        """Test PAN validation fails with too long PAN."""
        with pytest.raises(ValidationError) as exc_info:
            ApplicationCreate(
                pan_number="ABCDE12345F",  # Too long
                monthly_income_inr=self.VALID_INCOME,
                loan_amount_inr=self.VALID_LOAN_AMOUNT,
                loan_type=self.VALID_LOAN_TYPE
            )
        assert "String should have at most 10 characters" in str(exc_info.value)

    def test_pan_validation_invalid_format_all_letters(self):
        """Test PAN validation fails with all letters."""
        with pytest.raises(ValidationError) as exc_info:
            ApplicationCreate(
                pan_number="ABCDEFGHIJ",
                monthly_income_inr=self.VALID_INCOME,
                loan_amount_inr=self.VALID_LOAN_AMOUNT,
                loan_type=self.VALID_LOAN_TYPE
            )
        assert "Invalid PAN format" in str(exc_info.value)

    def test_pan_validation_invalid_format_all_digits(self):
        """Test PAN validation fails with all digits."""
        with pytest.raises(ValidationError) as exc_info:
            ApplicationCreate(
                pan_number="1234567890",
                monthly_income_inr=self.VALID_INCOME,
                loan_amount_inr=self.VALID_LOAN_AMOUNT,
                loan_type=self.VALID_LOAN_TYPE
            )
        assert "Invalid PAN format" in str(exc_info.value)

    def test_pan_validation_invalid_format_special_chars(self):
        """Test PAN validation fails with special characters."""
        with pytest.raises(ValidationError) as exc_info:
            ApplicationCreate(
                pan_number="ABCD@1234F",
                monthly_income_inr=self.VALID_INCOME,
                loan_amount_inr=self.VALID_LOAN_AMOUNT,
                loan_type=self.VALID_LOAN_TYPE
            )
        assert "Invalid PAN format" in str(exc_info.value)

    def test_pan_validation_invalid_format_wrong_positions(self):
        """Test PAN validation fails with letters/digits in wrong positions."""
        with pytest.raises(ValidationError) as exc_info:
            ApplicationCreate(
                pan_number="1BCDE1234F",  # Digit in first position
                monthly_income_inr=self.VALID_INCOME,
                loan_amount_inr=self.VALID_LOAN_AMOUNT,
                loan_type=self.VALID_LOAN_TYPE
            )
        assert "Invalid PAN format" in str(exc_info.value)

    # Name Validation Tests
    def test_name_validation_valid_simple_name(self):
        """Test name validation with simple valid name."""
        app = ApplicationCreate(
            pan_number=self.VALID_PAN,
            applicant_name="John Doe",
            monthly_income_inr=self.VALID_INCOME,
            loan_amount_inr=self.VALID_LOAN_AMOUNT,
            loan_type=self.VALID_LOAN_TYPE
        )
        assert app.applicant_name == "John Doe"

    def test_name_validation_valid_with_dots(self):
        """Test name validation with dots (Dr., Mr., etc.)."""
        app = ApplicationCreate(
            pan_number=self.VALID_PAN,
            applicant_name="Dr. John A. Doe",
            monthly_income_inr=self.VALID_INCOME,
            loan_amount_inr=self.VALID_LOAN_AMOUNT,
            loan_type=self.VALID_LOAN_TYPE
        )
        assert app.applicant_name == "Dr. John A. Doe"

    def test_name_validation_strips_whitespace(self):
        """Test that name strips leading/trailing whitespace."""
        app = ApplicationCreate(
            pan_number=self.VALID_PAN,
            applicant_name="  John Doe  ",
            monthly_income_inr=self.VALID_INCOME,
            loan_amount_inr=self.VALID_LOAN_AMOUNT,
            loan_type=self.VALID_LOAN_TYPE
        )
        assert app.applicant_name == "John Doe"

    def test_name_validation_minimum_length(self):
        """Test name validation with minimum valid length (2 chars)."""
        app = ApplicationCreate(
            pan_number=self.VALID_PAN,
            applicant_name="AB",
            monthly_income_inr=self.VALID_INCOME,
            loan_amount_inr=self.VALID_LOAN_AMOUNT,
            loan_type=self.VALID_LOAN_TYPE
        )
        assert app.applicant_name == "AB"

    def test_name_validation_too_short(self):
        """Test name validation fails with too short name."""
        with pytest.raises(ValidationError) as exc_info:
            ApplicationCreate(
                pan_number=self.VALID_PAN,
                applicant_name="A",
                monthly_income_inr=self.VALID_INCOME,
                loan_amount_inr=self.VALID_LOAN_AMOUNT,
                loan_type=self.VALID_LOAN_TYPE
            )
        assert "Name must be at least 2 characters" in str(exc_info.value)

    def test_name_validation_with_numbers(self):
        """Test name validation fails with numbers."""
        with pytest.raises(ValidationError) as exc_info:
            ApplicationCreate(
                pan_number=self.VALID_PAN,
                applicant_name="John123",
                monthly_income_inr=self.VALID_INCOME,
                loan_amount_inr=self.VALID_LOAN_AMOUNT,
                loan_type=self.VALID_LOAN_TYPE
            )
        assert "Name can only contain letters, spaces, and dots" in str(exc_info.value)

    def test_name_validation_with_special_chars(self):
        """Test name validation fails with special characters."""
        with pytest.raises(ValidationError) as exc_info:
            ApplicationCreate(
                pan_number=self.VALID_PAN,
                applicant_name="John@Doe",
                monthly_income_inr=self.VALID_INCOME,
                loan_amount_inr=self.VALID_LOAN_AMOUNT,
                loan_type=self.VALID_LOAN_TYPE
            )
        assert "Name can only contain letters, spaces, and dots" in str(exc_info.value)

    # Income Validation Tests
    def test_income_validation_valid_amount(self):
        """Test income validation with valid amount."""
        app = ApplicationCreate(
            pan_number=self.VALID_PAN,
            monthly_income_inr=Decimal("50000"),
            loan_amount_inr=self.VALID_LOAN_AMOUNT,
            loan_type=self.VALID_LOAN_TYPE
        )
        assert app.monthly_income_inr == Decimal("50000")

    def test_income_validation_minimum_valid(self):
        """Test income validation at minimum threshold (5000)."""
        app = ApplicationCreate(
            pan_number=self.VALID_PAN,
            monthly_income_inr=Decimal("5000"),
            loan_amount_inr=self.VALID_LOAN_AMOUNT,
            loan_type=self.VALID_LOAN_TYPE
        )
        assert app.monthly_income_inr == Decimal("5000")

    def test_income_validation_below_minimum(self):
        """Test income validation fails below minimum (5000)."""
        with pytest.raises(ValidationError) as exc_info:
            ApplicationCreate(
                pan_number=self.VALID_PAN,
                monthly_income_inr=Decimal("4999"),
                loan_amount_inr=self.VALID_LOAN_AMOUNT,
                loan_type=self.VALID_LOAN_TYPE
            )
        assert "Monthly income must be at least INR 5,000" in str(exc_info.value)

    def test_income_validation_zero(self):
        """Test income validation fails with zero."""
        with pytest.raises(ValidationError) as exc_info:
            ApplicationCreate(
                pan_number=self.VALID_PAN,
                monthly_income_inr=Decimal("0"),
                loan_amount_inr=self.VALID_LOAN_AMOUNT,
                loan_type=self.VALID_LOAN_TYPE
            )
        assert "greater than 0" in str(exc_info.value).lower()

    def test_income_validation_negative(self):
        """Test income validation fails with negative value."""
        with pytest.raises(ValidationError) as exc_info:
            ApplicationCreate(
                pan_number=self.VALID_PAN,
                monthly_income_inr=Decimal("-1000"),
                loan_amount_inr=self.VALID_LOAN_AMOUNT,
                loan_type=self.VALID_LOAN_TYPE
            )
        assert "greater than 0" in str(exc_info.value).lower()

    def test_income_validation_maximum_valid(self):
        """Test income validation at maximum threshold (10M)."""
        app = ApplicationCreate(
            pan_number=self.VALID_PAN,
            monthly_income_inr=Decimal("10000000"),
            loan_amount_inr=self.VALID_LOAN_AMOUNT,
            loan_type=self.VALID_LOAN_TYPE
        )
        assert app.monthly_income_inr == Decimal("10000000")

    def test_income_validation_above_maximum(self):
        """Test income validation fails above maximum (10M)."""
        with pytest.raises(ValidationError) as exc_info:
            ApplicationCreate(
                pan_number=self.VALID_PAN,
                monthly_income_inr=Decimal("10000001"),
                loan_amount_inr=self.VALID_LOAN_AMOUNT,
                loan_type=self.VALID_LOAN_TYPE
            )
        assert "unreasonably high" in str(exc_info.value).lower()

    # Loan Amount Validation Tests
    def test_loan_amount_validation_valid(self):
        """Test loan amount validation with valid amount."""
        app = ApplicationCreate(
            pan_number=self.VALID_PAN,
            monthly_income_inr=self.VALID_INCOME,
            loan_amount_inr=Decimal("500000"),
            loan_type=self.VALID_LOAN_TYPE
        )
        assert app.loan_amount_inr == Decimal("500000")

    def test_loan_amount_validation_minimum_valid(self):
        """Test loan amount validation at minimum (10000)."""
        app = ApplicationCreate(
            pan_number=self.VALID_PAN,
            monthly_income_inr=self.VALID_INCOME,
            loan_amount_inr=Decimal("10000"),
            loan_type=self.VALID_LOAN_TYPE
        )
        assert app.loan_amount_inr == Decimal("10000")

    def test_loan_amount_validation_below_minimum(self):
        """Test loan amount validation fails below minimum (10000)."""
        with pytest.raises(ValidationError) as exc_info:
            ApplicationCreate(
                pan_number=self.VALID_PAN,
                monthly_income_inr=self.VALID_INCOME,
                loan_amount_inr=Decimal("9999"),
                loan_type=self.VALID_LOAN_TYPE
            )
        assert "Loan amount must be at least INR 10,000" in str(exc_info.value)

    def test_loan_amount_validation_maximum_valid(self):
        """Test loan amount validation at maximum (10M)."""
        app = ApplicationCreate(
            pan_number=self.VALID_PAN,
            monthly_income_inr=self.VALID_INCOME,
            loan_amount_inr=Decimal("10000000"),
            loan_type=self.VALID_LOAN_TYPE
        )
        assert app.loan_amount_inr == Decimal("10000000")

    def test_loan_amount_validation_above_maximum(self):
        """Test loan amount validation fails above maximum (10M)."""
        with pytest.raises(ValidationError) as exc_info:
            ApplicationCreate(
                pan_number=self.VALID_PAN,
                monthly_income_inr=self.VALID_INCOME,
                loan_amount_inr=Decimal("10000001"),
                loan_type=self.VALID_LOAN_TYPE
            )
        assert "less than or equal to" in str(exc_info.value).lower()

    def test_loan_amount_validation_zero(self):
        """Test loan amount validation fails with zero."""
        with pytest.raises(ValidationError) as exc_info:
            ApplicationCreate(
                pan_number=self.VALID_PAN,
                monthly_income_inr=self.VALID_INCOME,
                loan_amount_inr=Decimal("0"),
                loan_type=self.VALID_LOAN_TYPE
            )
        assert "greater than 0" in str(exc_info.value).lower()

    # Loan Type Validation Tests
    def test_loan_type_personal(self):
        """Test loan type with PERSONAL."""
        app = ApplicationCreate(
            pan_number=self.VALID_PAN,
            monthly_income_inr=self.VALID_INCOME,
            loan_amount_inr=self.VALID_LOAN_AMOUNT,
            loan_type=LoanType.PERSONAL
        )
        assert app.loan_type == LoanType.PERSONAL

    def test_loan_type_home(self):
        """Test loan type with HOME."""
        app = ApplicationCreate(
            pan_number=self.VALID_PAN,
            monthly_income_inr=self.VALID_INCOME,
            loan_amount_inr=self.VALID_LOAN_AMOUNT,
            loan_type=LoanType.HOME
        )
        assert app.loan_type == LoanType.HOME

    def test_loan_type_auto(self):
        """Test loan type with AUTO."""
        app = ApplicationCreate(
            pan_number=self.VALID_PAN,
            monthly_income_inr=self.VALID_INCOME,
            loan_amount_inr=self.VALID_LOAN_AMOUNT,
            loan_type=LoanType.AUTO
        )
        assert app.loan_type == LoanType.AUTO

    def test_loan_type_string_conversion(self):
        """Test loan type accepts string values."""
        app = ApplicationCreate(
            pan_number=self.VALID_PAN,
            monthly_income_inr=self.VALID_INCOME,
            loan_amount_inr=self.VALID_LOAN_AMOUNT,
            loan_type="PERSONAL"
        )
        assert app.loan_type == LoanType.PERSONAL

    def test_loan_type_invalid(self):
        """Test loan type validation fails with invalid type."""
        with pytest.raises(ValidationError) as exc_info:
            ApplicationCreate(
                pan_number=self.VALID_PAN,
                monthly_income_inr=self.VALID_INCOME,
                loan_amount_inr=self.VALID_LOAN_AMOUNT,
                loan_type="INVALID"
            )
        assert "Input should be" in str(exc_info.value)


class TestApplicationResponse:
    """Test suite for ApplicationResponse schema."""

    def test_create_application_response(self):
        """Test creating application response."""
        app_id = UUID("123e4567-e89b-12d3-a456-426614174000")
        response = ApplicationResponse(
            application_id=app_id,
            status=ApplicationStatus.PENDING
        )

        assert response.application_id == app_id
        assert response.status == ApplicationStatus.PENDING

    def test_application_response_all_statuses(self):
        """Test application response with all status types."""
        app_id = UUID("123e4567-e89b-12d3-a456-426614174000")

        for status in ApplicationStatus:
            response = ApplicationResponse(
                application_id=app_id,
                status=status
            )
            assert response.status == status


class TestApplicationStatusResponse:
    """Test suite for ApplicationStatusResponse schema."""

    def test_create_status_response_with_score(self):
        """Test creating status response with CIBIL score."""
        app_id = UUID("123e4567-e89b-12d3-a456-426614174000")
        now = datetime.now()

        response = ApplicationStatusResponse(
            application_id=app_id,
            status=ApplicationStatus.PRE_APPROVED,
            cibil_score=750,
            created_at=now,
            updated_at=now
        )

        assert response.application_id == app_id
        assert response.status == ApplicationStatus.PRE_APPROVED
        assert response.cibil_score == 750
        assert response.created_at == now
        assert response.updated_at == now

    def test_create_status_response_without_score(self):
        """Test creating status response without CIBIL score."""
        app_id = UUID("123e4567-e89b-12d3-a456-426614174000")
        now = datetime.now()

        response = ApplicationStatusResponse(
            application_id=app_id,
            status=ApplicationStatus.PENDING,
            created_at=now,
            updated_at=now
        )

        assert response.cibil_score is None


class TestErrorResponse:
    """Test suite for ErrorResponse schema."""

    def test_create_error_response_with_code(self):
        """Test creating error response with error code."""
        error = ErrorResponse(
            detail="Application not found",
            error_code="APP_NOT_FOUND"
        )

        assert error.detail == "Application not found"
        assert error.error_code == "APP_NOT_FOUND"

    def test_create_error_response_without_code(self):
        """Test creating error response without error code."""
        error = ErrorResponse(detail="Internal server error")

        assert error.detail == "Internal server error"
        assert error.error_code is None


class TestEnums:
    """Test suite for enum types."""

    def test_loan_type_enum_values(self):
        """Test LoanType enum values."""
        assert LoanType.PERSONAL.value == "PERSONAL"
        assert LoanType.HOME.value == "HOME"
        assert LoanType.AUTO.value == "AUTO"

    def test_application_status_enum_values(self):
        """Test ApplicationStatus enum values."""
        assert ApplicationStatus.PENDING.value == "PENDING"
        assert ApplicationStatus.PRE_APPROVED.value == "PRE_APPROVED"
        assert ApplicationStatus.REJECTED.value == "REJECTED"
        assert ApplicationStatus.MANUAL_REVIEW.value == "MANUAL_REVIEW"
