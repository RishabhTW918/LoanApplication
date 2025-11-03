import unittest
import pytest
from unittest.mock import patch
from ..app.cibil_simulator import CIBILSimulator


class TestCIBILSimulator(unittest.TestCase):
    """Test suite for CIBILSimulator."""

    # Test data constants
    HIGH_INCOME = 100000  # > 75000
    MEDIUM_INCOME = 50000  # Between 30000 and 75000
    LOW_INCOME = 25000  # < 30000
    SAMPLE_PAN = "ABCDE1234F"

    def test_generate_score_high_income_personal_loan(self):
        """Test score generation with high income and personal loan."""
        # High income (+40), Personal loan (-10), Base (650)
        # Expected range with random: 650 + 40 - 10 + (-5 to +5) = 675-685
        with patch('random.randint', return_value=0):
            score = CIBILSimulator.generate_score(
                pan_number=self.SAMPLE_PAN,
                monthly_income_inr=self.HIGH_INCOME,
                loan_type="PERSONAL"
            )

            assert score == 680  # 650 + 40 - 10 + 0
            assert CIBILSimulator.MIN_SCORE <= score <= CIBILSimulator.MAX_SCORE

    def test_generate_score_high_income_home_loan(self):
        """Test score generation with high income and home loan."""
        # High income (+40), Home loan (+10), Base (650)
        # Expected: 650 + 40 + 10 = 700 (without random)
        with patch('random.randint', return_value=0):
            score = CIBILSimulator.generate_score(
                pan_number=self.SAMPLE_PAN,
                monthly_income_inr=self.HIGH_INCOME,
                loan_type="HOME"
            )

            assert score == 700  # 650 + 40 + 10 + 0

    def test_generate_score_high_income_auto_loan(self):
        """Test score generation with high income and auto loan (neutral)."""
        # High income (+40), Auto loan (0), Base (650)
        # Expected: 650 + 40 = 690 (without random)
        with patch('random.randint', return_value=0):
            score = CIBILSimulator.generate_score(
                pan_number=self.SAMPLE_PAN,
                monthly_income_inr=self.HIGH_INCOME,
                loan_type="AUTO"
            )

            assert score == 690  # 650 + 40 + 0

    def test_generate_score_low_income_personal_loan(self):
        """Test score generation with low income and personal loan."""
        # Low income (-20), Personal loan (-10), Base (650)
        # Expected: 650 - 20 - 10 = 620 (without random)
        with patch('random.randint', return_value=0):
            score = CIBILSimulator.generate_score(
                pan_number=self.SAMPLE_PAN,
                monthly_income_inr=self.LOW_INCOME,
                loan_type="PERSONAL"
            )

            assert score == 620  # 650 - 20 - 10 + 0

    def test_generate_score_low_income_home_loan(self):
        """Test score generation with low income and home loan."""
        # Low income (-20), Home loan (+10), Base (650)
        # Expected: 650 - 20 + 10 = 640 (without random)
        with patch('random.randint', return_value=0):
            score = CIBILSimulator.generate_score(
                pan_number=self.SAMPLE_PAN,
                monthly_income_inr=self.LOW_INCOME,
                loan_type="HOME"
            )

            assert score == 640  # 650 - 20 + 10 + 0

    def test_generate_score_medium_income_auto_loan(self):
        """Test score generation with medium income (no adjustments)."""
        # Medium income (0), Auto loan (0), Base (650)
        # Expected: 650 (without random)
        with patch('random.randint', return_value=0):
            score = CIBILSimulator.generate_score(
                pan_number=self.SAMPLE_PAN,
                monthly_income_inr=self.MEDIUM_INCOME,
                loan_type="AUTO"
            )

            assert score == 650  # Base score only

    def test_generate_score_random_variation_positive(self):
        """Test that positive random variation is applied correctly."""
        # Base (650), High income (+40), Auto loan (0), Random (+5)
        with patch('random.randint', return_value=5):
            score = CIBILSimulator.generate_score(
                pan_number=self.SAMPLE_PAN,
                monthly_income_inr=self.HIGH_INCOME,
                loan_type="AUTO"
            )

            assert score == 695  # 650 + 40 + 0 + 5

    def test_generate_score_random_variation_negative(self):
        """Test that negative random variation is applied correctly."""
        # Base (650), High income (+40), Auto loan (0), Random (-5)
        with patch('random.randint', return_value=-5):
            score = CIBILSimulator.generate_score(
                pan_number=self.SAMPLE_PAN,
                monthly_income_inr=self.HIGH_INCOME,
                loan_type="AUTO"
            )

            assert score == 685  # 650 + 40 + 0 - 5

    def test_generate_score_upper_bound_enforcement(self):
        """Test that score cannot exceed MAX_SCORE (900)."""
        # Create scenario that would exceed 900
        # High income (+40), Home loan (+10), Max random (+5) = 650 + 40 + 10 + 5 = 705
        # This won't exceed 900, so let's test with extreme values
        with patch('random.randint', return_value=5):
            with patch.object(CIBILSimulator, 'BASE_SCORE', 890):
                score = CIBILSimulator.generate_score(
                    pan_number=self.SAMPLE_PAN,
                    monthly_income_inr=self.HIGH_INCOME,
                    loan_type="HOME"
                )

                # 890 + 40 + 10 + 5 = 945, should be capped at 900
                assert score == CIBILSimulator.MAX_SCORE

    def test_generate_score_lower_bound_enforcement(self):
        """Test that score cannot go below MIN_SCORE (300)."""
        # Create scenario that would go below 300
        with patch('random.randint', return_value=-5):
            with patch.object(CIBILSimulator, 'BASE_SCORE', 310):
                score = CIBILSimulator.generate_score(
                    pan_number=self.SAMPLE_PAN,
                    monthly_income_inr=self.LOW_INCOME,
                    loan_type="PERSONAL"
                )

                # 310 - 20 - 10 - 5 = 275, should be capped at 300
                assert score == CIBILSimulator.MIN_SCORE

    def test_generate_score_income_threshold_75000(self):
        """Test income adjustment at 75000 threshold."""
        # Just above threshold (should get +40)
        with patch('random.randint', return_value=0):
            score_above = CIBILSimulator.generate_score(
                pan_number=self.SAMPLE_PAN,
                monthly_income_inr=75001,
                loan_type="AUTO"
            )
            assert score_above == 690  # 650 + 40

        # Just at threshold (should not get +40)
        with patch('random.randint', return_value=0):
            score_at = CIBILSimulator.generate_score(
                pan_number=self.SAMPLE_PAN,
                monthly_income_inr=75000,
                loan_type="AUTO"
            )
            assert score_at == 650  # Base only

    def test_generate_score_income_threshold_30000(self):
        """Test income adjustment at 30000 threshold."""
        # Just below threshold (should get -20)
        with patch('random.randint', return_value=0):
            score_below = CIBILSimulator.generate_score(
                pan_number=self.SAMPLE_PAN,
                monthly_income_inr=29999,
                loan_type="AUTO"
            )
            assert score_below == 630  # 650 - 20

        # Just at threshold (should not get -20)
        with patch('random.randint', return_value=0):
            score_at = CIBILSimulator.generate_score(
                pan_number=self.SAMPLE_PAN,
                monthly_income_inr=30000,
                loan_type="AUTO"
            )
            assert score_at == 650  # Base only

    def test_generate_score_with_real_random(self):
        """Test score generation with actual random variation."""
        # Without mocking random, verify score is within expected range
        score = CIBILSimulator.generate_score(
            pan_number=self.SAMPLE_PAN,
            monthly_income_inr=self.HIGH_INCOME,
            loan_type="AUTO"
        )

        # High income (+40), Auto (0), Random (-5 to +5)
        # Expected range: 650 + 40 + (-5 to +5) = 685 to 695
        assert 685 <= score <= 695
        assert isinstance(score, int)

    def test_generate_score_returns_integer(self):
        """Test that generate_score always returns an integer."""
        with patch('random.randint', return_value=0):
            score = CIBILSimulator.generate_score(
                pan_number=self.SAMPLE_PAN,
                monthly_income_inr=self.MEDIUM_INCOME,
                loan_type="PERSONAL"
            )

            assert isinstance(score, int)

    def test_get_score_category_excellent(self):
        """Test EXCELLENT category (score >= 750)."""
        assert CIBILSimulator.get_score_category(750) == "EXCELLENT"
        assert CIBILSimulator.get_score_category(800) == "EXCELLENT"
        assert CIBILSimulator.get_score_category(900) == "EXCELLENT"

    def test_get_score_category_good(self):
        """Test GOOD category (700 <= score < 750)."""
        assert CIBILSimulator.get_score_category(700) == "GOOD"
        assert CIBILSimulator.get_score_category(725) == "GOOD"
        assert CIBILSimulator.get_score_category(749) == "GOOD"

    def test_get_score_category_fair(self):
        """Test FAIR category (650 <= score < 700)."""
        assert CIBILSimulator.get_score_category(650) == "FAIR"
        assert CIBILSimulator.get_score_category(675) == "FAIR"
        assert CIBILSimulator.get_score_category(699) == "FAIR"

    def test_get_score_category_poor(self):
        """Test POOR category (600 <= score < 650)."""
        assert CIBILSimulator.get_score_category(600) == "POOR"
        assert CIBILSimulator.get_score_category(625) == "POOR"
        assert CIBILSimulator.get_score_category(649) == "POOR"

    def test_get_score_category_very_poor(self):
        """Test VERY_POOR category (score < 600)."""
        assert CIBILSimulator.get_score_category(599) == "VERY_POOR"
        assert CIBILSimulator.get_score_category(500) == "VERY_POOR"
        assert CIBILSimulator.get_score_category(300) == "VERY_POOR"

    def test_get_score_category_boundary_values(self):
        """Test all boundary values for score categories."""
        # Test boundaries
        assert CIBILSimulator.get_score_category(749) == "GOOD"
        assert CIBILSimulator.get_score_category(750) == "EXCELLENT"

        assert CIBILSimulator.get_score_category(699) == "FAIR"
        assert CIBILSimulator.get_score_category(700) == "GOOD"

        assert CIBILSimulator.get_score_category(649) == "POOR"
        assert CIBILSimulator.get_score_category(650) == "FAIR"

        assert CIBILSimulator.get_score_category(599) == "VERY_POOR"
        assert CIBILSimulator.get_score_category(600) == "POOR"

    def test_cibil_simulator_constants(self):
        """Test that CIBILSimulator constants are set correctly."""
        assert CIBILSimulator.MIN_SCORE == 300
        assert CIBILSimulator.MAX_SCORE == 900
        assert CIBILSimulator.BASE_SCORE == 650

    def test_generate_score_all_loan_types(self):
        """Test score generation with all valid loan types."""
        with patch('random.randint', return_value=0):
            # Test all three loan types
            personal_score = CIBILSimulator.generate_score(
                self.SAMPLE_PAN, self.MEDIUM_INCOME, "PERSONAL"
            )
            home_score = CIBILSimulator.generate_score(
                self.SAMPLE_PAN, self.MEDIUM_INCOME, "HOME"
            )
            auto_score = CIBILSimulator.generate_score(
                self.SAMPLE_PAN, self.MEDIUM_INCOME, "AUTO"
            )

            # Verify relative differences
            assert personal_score == 640  # 650 - 10
            assert home_score == 660      # 650 + 10
            assert auto_score == 650      # 650 (no change)

            # Home loan should have highest score, personal lowest
            assert home_score > auto_score > personal_score

    def test_generate_score_extreme_income_values(self):
        """Test score generation with extreme income values."""
        with patch('random.randint', return_value=0):
            # Very high income
            high_score = CIBILSimulator.generate_score(
                self.SAMPLE_PAN, 1000000, "AUTO"
            )
            assert high_score == 690  # 650 + 40

            # Very low income
            low_score = CIBILSimulator.generate_score(
                self.SAMPLE_PAN, 5000, "AUTO"
            )
            assert low_score == 630  # 650 - 20
