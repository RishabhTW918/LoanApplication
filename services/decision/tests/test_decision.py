import unittest

import pytest
from ..app.decision_engine import DecisionEngine


class TestDecisionEngine(unittest.TestCase):
    """Test suite for DecisionEngine business logic."""

    # Test data constants
    SUFFICIENT_INCOME = 100000  # INR per month
    INSUFFICIENT_INCOME = 10000  # INR per month
    LOAN_AMOUNT_480K = 480000  # 480K loan requires 10K/month (480000/48)
    LOAN_AMOUNT_1M = 1000000

    def test_make_decision_rejected_low_cibil_score(self):
        """Test rejection when CIBIL score is below minimum threshold (650)."""
        # Test with score = 649 (just below threshold)
        status, reason = DecisionEngine.make_decision(
            cibil_score=649,
            monthly_income_inr=self.SUFFICIENT_INCOME,
            loan_amount_inr=self.LOAN_AMOUNT_480K,
        )

        assert status == DecisionEngine.STATUS_REJECTED
        assert "649" in reason
        assert "650" in reason
        assert "below minimum threshold" in reason.lower()

    def test_make_decision_rejected_very_low_cibil_score(self):
        """Test rejection with very low CIBIL score (300)."""
        status, reason = DecisionEngine.make_decision(
            cibil_score=300,
            monthly_income_inr=self.SUFFICIENT_INCOME,
            loan_amount_inr=self.LOAN_AMOUNT_480K,
        )

        assert status == DecisionEngine.STATUS_REJECTED
        assert "300" in reason

    def test_make_decision_pre_approved_sufficient_income(self):
        """Test pre-approval when CIBIL >= 650 and income is sufficient."""
        status, reason = DecisionEngine.make_decision(
            cibil_score=750,
            monthly_income_inr=50000,  # 50K income for 480K loan (requires 10K)
            loan_amount_inr=self.LOAN_AMOUNT_480K,
        )

        assert status == DecisionEngine.STATUS_PRE_APPROVED
        assert "750" in reason
        assert "sufficient" in reason.lower()

    def test_make_decision_pre_approved_at_threshold_cibil(self):
        """Test pre-approval at exact CIBIL threshold (650)."""
        status, reason = DecisionEngine.make_decision(
            cibil_score=650,
            monthly_income_inr=50000,
            loan_amount_inr=self.LOAN_AMOUNT_480K,
        )

        assert status == DecisionEngine.STATUS_PRE_APPROVED
        assert "650" in reason

    def test_make_decision_pre_approved_high_cibil(self):
        """Test pre-approval with excellent CIBIL score (850)."""
        status, reason = DecisionEngine.make_decision(
            cibil_score=850,
            monthly_income_inr=100000,
            loan_amount_inr=self.LOAN_AMOUNT_1M,
        )

        assert status == DecisionEngine.STATUS_PRE_APPROVED

    def test_make_decision_manual_review_insufficient_income(self):
        """Test manual review when CIBIL is good but income insufficient."""
        status, reason = DecisionEngine.make_decision(
            cibil_score=750,
            monthly_income_inr=10000,  # 10K income for 480K loan (requires >10K)
            loan_amount_inr=self.LOAN_AMOUNT_480K,
        )

        assert status == DecisionEngine.STATUS_MANUAL_REVIEW
        assert "insufficient" in reason.lower()
        assert "manual review" in reason.lower()

    def test_make_decision_manual_review_exact_income_threshold(self):
        """Test manual review when income equals exact threshold (edge case)."""
        # Loan of 480K requires income > 10000 (480000/48 = 10000)
        # Income exactly at 10000 should fail the > check
        status, reason = DecisionEngine.make_decision(
            cibil_score=700,
            monthly_income_inr=10000.0,  # Exactly at threshold
            loan_amount_inr=480000,
        )

        assert status == DecisionEngine.STATUS_MANUAL_REVIEW

    def test_make_decision_manual_review_marginally_insufficient(self):
        """Test manual review with income just below required amount."""
        status, reason = DecisionEngine.make_decision(
            cibil_score=750,
            monthly_income_inr=20833,  # Just below 20833.34 required for 1M loan
            loan_amount_inr=self.LOAN_AMOUNT_1M,
        )

        assert status == DecisionEngine.STATUS_MANUAL_REVIEW
        assert "20833" in reason

    def test_make_decision_income_calculation_accuracy(self):
        """Test that income calculation is accurate (loan/48)."""
        # For a 960000 loan, minimum required income = 960000/48 = 20000
        # Income of 20001 should be sufficient
        status, _ = DecisionEngine.make_decision(
            cibil_score=700, monthly_income_inr=20001, loan_amount_inr=960000
        )

        assert status == DecisionEngine.STATUS_PRE_APPROVED

        # Income of 20000 should be insufficient (not > 20000)
        status, _ = DecisionEngine.make_decision(
            cibil_score=700, monthly_income_inr=20000, loan_amount_inr=960000
        )

        assert status == DecisionEngine.STATUS_MANUAL_REVIEW

    def test_make_decision_small_loan_amount(self):
        """Test decision with minimum loan amount (10000)."""
        status, reason = DecisionEngine.make_decision(
            cibil_score=700,
            monthly_income_inr=5000,  # 5K income for 10K loan (requires >208.33)
            loan_amount_inr=10000,
        )

        assert status == DecisionEngine.STATUS_PRE_APPROVED

    def test_make_decision_large_loan_amount(self):
        """Test decision with maximum loan amount (10M)."""
        status, reason = DecisionEngine.make_decision(
            cibil_score=800,
            monthly_income_inr=300000,  # 300K income for 10M loan (requires >208333)
            loan_amount_inr=10000000,
        )

        assert status == DecisionEngine.STATUS_PRE_APPROVED

    def test_calculate_emi_standard_loan(self):
        """Test EMI calculation for a standard loan."""
        # Loan: 1,000,000, Interest: 12% annual, Tenure: 48 months
        emi = DecisionEngine.calculate_emi(
            principal=1000000, annual_interest_rate=12, tenure_months=48
        )

        # Expected EMI ≈ 26333.60 (calculated using standard EMI formula)
        assert 26000 < emi < 27000
        assert isinstance(emi, float)
        # Check rounding to 2 decimal places
        assert emi == round(emi, 2)

    def test_calculate_emi_zero_interest(self):
        """Test EMI calculation with 0% interest rate.

        Note: The current implementation uses the standard EMI formula which
        results in division by zero for 0% interest. In production, this
        edge case should be handled separately (EMI = principal/tenure).
        This test documents the current limitation.
        """
        with pytest.raises(ZeroDivisionError):
            DecisionEngine.calculate_emi(
                principal=480000, annual_interest_rate=0, tenure_months=48
            )

    def test_calculate_emi_high_interest_rate(self):
        """Test EMI calculation with high interest rate (24%)."""
        emi = DecisionEngine.calculate_emi(
            principal=500000, annual_interest_rate=24, tenure_months=36
        )

        # EMI should be significantly higher than principal/tenure
        simple_emi = 500000 / 36
        assert emi > simple_emi
        assert isinstance(emi, float)

    def test_calculate_emi_short_tenure(self):
        """Test EMI calculation with short tenure (12 months)."""
        emi = DecisionEngine.calculate_emi(
            principal=100000, annual_interest_rate=10, tenure_months=12
        )

        # EMI should be high due to short tenure
        assert emi > 8000  # Should be > 100000/12
        assert isinstance(emi, float)

    def test_calculate_emi_long_tenure(self):
        """Test EMI calculation with long tenure (60 months)."""
        emi = DecisionEngine.calculate_emi(
            principal=1000000, annual_interest_rate=12, tenure_months=60
        )

        # EMI should be lower than 48 month tenure
        emi_48_months = DecisionEngine.calculate_emi(
            principal=1000000, annual_interest_rate=12, tenure_months=48
        )

        assert emi < emi_48_months

    def test_calculate_emi_rounding(self):
        """Test that EMI is rounded to 2 decimal places."""
        emi = DecisionEngine.calculate_emi(
            principal=123456, annual_interest_rate=11.5, tenure_months=37
        )

        # Check that result has at most 2 decimal places
        assert len(str(emi).split(".")[-1]) <= 2

    def test_decision_engine_constants(self):
        """Test that decision engine constants are set correctly."""
        assert DecisionEngine.MIN_CIBIL_SCORE == 650
        assert DecisionEngine.LOAN_TENURE_MONTHS == 48
        assert DecisionEngine.STATUS_PRE_APPROVED == "PRE_APPROVED"
        assert DecisionEngine.STATUS_REJECTED == "REJECTED"
        assert DecisionEngine.STATUS_MANUAL_REVIEW == "MANUAL_REVIEW"
