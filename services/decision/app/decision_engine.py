import logging
from typing import Dict, Tuple
from decimal import Decimal

logger = logging.getLogger(__name__)

class DecisionEngine:
    """
    Business logic for loan prequalification decisions.
    """

    # Thresholds
    MIN_CIBIL_SCORE = 650
    LOAN_TENURE_MONTHS = 48  # 4 years standard tenure

    # Status constants
    STATUS_PRE_APPROVED = "PRE_APPROVED"
    STATUS_REJECTED = "REJECTED"
    STATUS_MANUAL_REVIEW = "MANUAL_REVIEW"

    @classmethod
    def make_decision(
        cls,
        cibil_score: int,
        monthly_income_inr: float,
        loan_amount_inr: float
    ) -> Tuple[str, str]:
        """
        Make a prequalification decision based on business rules.

        Decision Logic:
        1. CIBIL < 650: REJECTED (High Risk)
        2. CIBIL >= 650 AND income sufficient: PRE_APPROVED
        3. CIBIL >= 650 AND income insufficient: MANUAL_REVIEW

        Income sufficiency: Monthly income should be > (Loan Amount / 48)
        This assumes a 4-year loan tenure and basic EMI calculation.

        """
        logger.info(
            f"Making decision: score={cibil_score}, "
            f"income={monthly_income_inr}, loan={loan_amount_inr}"
        )

        # Rule 1: Check CIBIL score threshold
        if cibil_score < cls.MIN_CIBIL_SCORE:
            reason = (
                f"CIBIL score {cibil_score} is below minimum threshold "
                f"of {cls.MIN_CIBIL_SCORE}"
            )
            logger.info(f"Decision: REJECTED - {reason}")
            return cls.STATUS_REJECTED, reason

        # Rule 2 & 3: Check income-to-loan ratio
        # Simple EMI calculation: Loan / Tenure
        # In reality, would use EMI formula with interest rate
        min_monthly_income_required = Decimal(loan_amount_inr) / Decimal(cls.LOAN_TENURE_MONTHS)

        logger.debug(
            f"Minimum income required: {min_monthly_income_required:.2f}, "
            f"Actual income: {monthly_income_inr}"
        )

        if monthly_income_inr > float(min_monthly_income_required):
            reason = (
                f"CIBIL score {cibil_score} meets threshold and "
                f"income is sufficient for loan repayment"
            )
            logger.info(f"Decision: PRE_APPROVED - {reason}")
            return cls.STATUS_PRE_APPROVED, reason
        else:
            reason = (
                f"CIBIL score {cibil_score} is good, but income "
                f"({monthly_income_inr:.2f}) is insufficient for "
                f"requested loan amount. Manual review required."
            )
            logger.info(f"Decision: MANUAL_REVIEW - {reason}")
            return cls.STATUS_MANUAL_REVIEW, reason

    @classmethod
    def calculate_emi(
        cls,
        principal: float,
        annual_interest_rate: float,
        tenure_months: int
    ) -> float:
        """
        Calculate EMI using the standard formula.

        EMI = P × r × (1 + r)^n / ((1 + r)^n - 1)
        where:
        P = Principal loan amount
        r = Monthly interest rate (annual rate / 12 / 100)
        n = Loan tenure in months

        Args:
            principal: Loan amount
            annual_interest_rate: Annual interest rate (e.g., 12 for 12%)
            tenure_months: Loan tenure in months

        Returns:
            float: Monthly EMI amount
        """
        monthly_rate = annual_interest_rate / 12 / 100
        emi = (
            principal * monthly_rate * (1 + monthly_rate) ** tenure_months
        ) / ((1 + monthly_rate) ** tenure_months - 1)

        return round(emi, 2)