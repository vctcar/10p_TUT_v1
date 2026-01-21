"""
Unit tests for 1RM estimation and effective reps calculation
"""
import pytest
from src.training.one_rm import calculate_effective_reps, estimate_1rm_from_amrap


class TestCalculateEffectiveReps:
    """Test suite for calculate_effective_reps function"""

    def test_basic_calculation(self):
        """Test basic TUT adjustment calculation"""
        # 10 reps at 6s TUT with 3s normal = 20 effective reps
        result = calculate_effective_reps(10, tut_per_rep=6.0, normal_tempo=3.0)
        assert result == 20.0

    def test_normal_tempo_no_adjustment(self):
        """Test that normal tempo results in no adjustment"""
        # 10 reps at 3s TUT with 3s normal = 10 effective reps
        result = calculate_effective_reps(10, tut_per_rep=3.0, normal_tempo=3.0)
        assert result == 10.0

    def test_slower_tempo_increases_effective_reps(self):
        """Test that slower tempo increases effective reps"""
        # 5 reps at 9s TUT with 3s normal = 15 effective reps
        result = calculate_effective_reps(5, tut_per_rep=9.0, normal_tempo=3.0)
        assert result == 15.0

    def test_zero_reps(self):
        """Test edge case: 0 reps"""
        result = calculate_effective_reps(0, tut_per_rep=6.0, normal_tempo=3.0)
        assert result == 0.0

    def test_high_rep_count(self):
        """Test edge case: extremely high reps"""
        result = calculate_effective_reps(50, tut_per_rep=6.0, normal_tempo=3.0)
        assert result == 100.0

    def test_default_parameters(self):
        """Test that default parameters work correctly"""
        # Default is 6s TUT, 3s normal
        result = calculate_effective_reps(8)
        assert result == 16.0

    def test_negative_reps_raises_error(self):
        """Test that negative reps raises ValueError"""
        with pytest.raises(ValueError, match="actual_reps must be non-negative"):
            calculate_effective_reps(-5)

    def test_zero_tut_raises_error(self):
        """Test that zero or negative TUT raises ValueError"""
        with pytest.raises(ValueError, match="tut_per_rep must be positive"):
            calculate_effective_reps(10, tut_per_rep=0)

    def test_negative_normal_tempo_raises_error(self):
        """Test that negative normal_tempo raises ValueError"""
        with pytest.raises(ValueError, match="normal_tempo must be positive"):
            calculate_effective_reps(10, normal_tempo=-3)


class TestEstimate1RMFromAMRAP:
    """Test suite for estimate_1rm_from_amrap function"""

    def test_basic_estimation(self):
        """Test basic 1RM estimation with known values"""
        # 225 lbs × 10 reps at 6s TUT = 20 effective reps
        # Epley: 225 × (1 + 20/30) = 225 × 1.6667 = 375
        result = estimate_1rm_from_amrap(225, 10, tut_per_rep=6.0, normal_tempo=3.0)
        assert result == pytest.approx(375.0, rel=0.01)

    def test_normal_tempo_estimation(self):
        """Test 1RM estimation without TUT adjustment"""
        # 100 lbs × 10 reps at normal tempo
        # Epley: 100 × (1 + 10/30) = 100 × 1.333 = 133.33
        result = estimate_1rm_from_amrap(100, 10, tut_per_rep=3.0, normal_tempo=3.0)
        assert result == pytest.approx(133.33, rel=0.01)

    def test_low_rep_high_weight(self):
        """Test estimation with low reps (closer to 1RM)"""
        # 300 lbs × 3 reps at 6s TUT = 6 effective reps
        # Epley: 300 × (1 + 6/30) = 300 × 1.2 = 360
        result = estimate_1rm_from_amrap(300, 3, tut_per_rep=6.0, normal_tempo=3.0)
        assert result == pytest.approx(360.0, rel=0.01)

    def test_high_rep_lower_weight(self):
        """Test estimation with high reps"""
        # 135 lbs × 20 reps at 6s TUT = 40 effective reps
        # Epley: 135 × (1 + 40/30) = 135 × 2.333 = 315
        result = estimate_1rm_from_amrap(135, 20, tut_per_rep=6.0, normal_tempo=3.0)
        assert result == pytest.approx(315.0, rel=0.01)

    def test_zero_reps_returns_weight(self):
        """Test edge case: 0 reps returns the weight itself"""
        result = estimate_1rm_from_amrap(315, 0)
        assert result == 315.0

    def test_single_rep(self):
        """Test with single rep"""
        # 300 lbs × 1 rep at 6s TUT = 2 effective reps
        # Epley: 300 × (1 + 2/30) = 300 × 1.0667 = 320
        result = estimate_1rm_from_amrap(300, 1, tut_per_rep=6.0, normal_tempo=3.0)
        assert result == pytest.approx(320.0, rel=0.01)

    def test_default_parameters(self):
        """Test that default parameters work correctly"""
        # Default is 6s TUT, 3s normal
        result = estimate_1rm_from_amrap(200, 8)
        # 8 reps × 2 = 16 effective reps
        # 200 × (1 + 16/30) = 200 × 1.533 = 306.67
        assert result == pytest.approx(306.67, rel=0.01)

    def test_negative_weight_raises_error(self):
        """Test that negative weight raises ValueError"""
        with pytest.raises(ValueError, match="weight must be positive"):
            estimate_1rm_from_amrap(-225, 10)

    def test_zero_weight_raises_error(self):
        """Test that zero weight raises ValueError"""
        with pytest.raises(ValueError, match="weight must be positive"):
            estimate_1rm_from_amrap(0, 10)

    def test_negative_reps_raises_error(self):
        """Test that negative reps raises ValueError"""
        with pytest.raises(ValueError, match="actual_reps must be non-negative"):
            estimate_1rm_from_amrap(225, -5)

    def test_extremely_high_reps(self):
        """Test edge case: very high rep count (50+ reps)"""
        # 100 lbs × 50 reps at 6s TUT = 100 effective reps
        # Epley: 100 × (1 + 100/30) = 100 × 4.333 = 433.33
        result = estimate_1rm_from_amrap(100, 50, tut_per_rep=6.0, normal_tempo=3.0)
        assert result == pytest.approx(433.33, rel=0.01)

    def test_bodyweight_pullups_scenario(self):
        """Test realistic scenario: bodyweight pull-ups with added weight"""
        # 45 lbs added × 12 reps at 6s TUT = 24 effective reps
        # Epley: 45 × (1 + 24/30) = 45 × 1.8 = 81
        result = estimate_1rm_from_amrap(45, 12, tut_per_rep=6.0, normal_tempo=3.0)
        assert result == pytest.approx(81.0, rel=0.01)
