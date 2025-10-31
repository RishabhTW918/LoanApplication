import random
import logging

logger = logging.getLogger(__name__)


class CIBILSimulator:
    """
    Simulates CIBIL credit score generation.

    In production, this would call the actual CIBIL API.
    For this project, we simulate scores based on business rules.
    """

    MIN_SCORE = 300
    MAX_SCORE = 900
    BASE_SCORE = 650

    @classmethod
    def generate_score(
        cls, pan_number: str, monthly_income_inr: float, loan_type: str
    ) -> int:
        """
        Generate a simulated CIBIL score.

        Args:
            pan_number: Applicant's PAN
            monthly_income_inr: Monthly income
            loan_type: Type of loan

        Returns:
            int: CIBIL score between 300 and 900
        """

        score = cls.BASE_SCORE

        # Income-based adjustments
        if monthly_income_inr > 75000:
            score += 40
            logger.debug("High income: +40 points")
        elif monthly_income_inr < 30000:
            score -= 20
            logger.debug("Low income: -20 points")

        # Loan type adjustments
        if loan_type == "PERSONAL":
            score -= 10  # Unsecured loan - higher risk
            logger.debug("Personal loan: -10 points")
        elif loan_type == "HOME":
            score += 10  # Secured loan - lower risk
            logger.debug("Home loan: +10 points")
        # AUTO loans: no adjustment (neutral)

        # Add random variation for realism
        random_adjustment = random.randint(-5, 5)
        score += random_adjustment
        logger.debug(f"Random adjustment: {random_adjustment:+d} points")

        # Ensure score is within valid range
        score = max(cls.MIN_SCORE, min(cls.MAX_SCORE, score))

        logger.info(
            f"Generated CIBIL score {score} for PAN {pan_number} "
            f"(income: {monthly_income_inr}, loan_type: {loan_type})"
        )

        return score

    @classmethod
    def get_score_category(cls, score: int) -> str:
        if score >= 750:
            return "EXCELLENT"
        elif score >= 700:
            return "GOOD"
        elif score >= 650:
            return "FAIR"
        elif score >= 600:
            return "POOR"
        else:
            return "VERY_POOR"
