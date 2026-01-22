"""
Tests for training plan generation functions.
"""

import pytest
from src.training.planner import build_training_plan, suggest_next_week_workout


class TestBuildTrainingPlan:
    """Test suite for build_training_plan() function."""

    def test_generates_13_weeks(self):
        """Plan should generate exactly 13 weeks."""
        plan = build_training_plan(start_1rm=300.0)
        assert len(plan) == 13
        assert all(week in plan for week in range(1, 14))

    def test_week1_uses_start_1rm(self):
        """Week 1 should use the initial 1RM with 70% intensity."""
        start_1rm = 300.0
        plan = build_training_plan(start_1rm=start_1rm)

        week1 = plan[1]
        assert week1['current_1rm'] == start_1rm
        assert week1['percentage'] == 0.7
        assert week1['prescribed_weight'] == start_1rm * 0.7  # 210.0

    def test_default_block_percentages(self):
        """Should use correct default percentages for each block."""
        plan = build_training_plan(start_1rm=300.0)

        # Block 1 (Weeks 1-4): [0.7, 0.75, 0.8, 0.725]
        assert plan[1]['percentage'] == 0.7
        assert plan[2]['percentage'] == 0.75
        assert plan[3]['percentage'] == 0.8
        assert plan[4]['percentage'] == 0.725

        # Block 2 (Weeks 5-8): [0.775, 0.825, 0.85, 0.775]
        assert plan[5]['percentage'] == 0.775
        assert plan[6]['percentage'] == 0.825
        assert plan[7]['percentage'] == 0.85
        assert plan[8]['percentage'] == 0.775

        # Block 3 (Weeks 9-13): [0.8, 0.85, 0.875, 0.9, 0.65]
        assert plan[9]['percentage'] == 0.8
        assert plan[10]['percentage'] == 0.85
        assert plan[11]['percentage'] == 0.875
        assert plan[12]['percentage'] == 0.9
        assert plan[13]['percentage'] == 0.65  # Deload week

    def test_progressive_volume_sets(self):
        """Sets should progress: 3 (Block 1) → 4 (Block 2) → 5 (Block 3)."""
        plan = build_training_plan(start_1rm=300.0)

        # Block 1: 3 sets
        for week in range(1, 5):
            assert plan[week]['sets'] == 3, f"Week {week} should have 3 sets"

        # Block 2: 4 sets
        for week in range(5, 9):
            assert plan[week]['sets'] == 4, f"Week {week} should have 4 sets"

        # Block 3: 5 sets
        for week in range(9, 14):
            assert plan[week]['sets'] == 5, f"Week {week} should have 5 sets"

    def test_amrap_week_identification(self):
        """AMRAP weeks should be 2-4, 6-8, 10-12."""
        plan = build_training_plan(start_1rm=300.0)

        amrap_weeks = {2, 3, 4, 6, 7, 8, 10, 11, 12}
        non_amrap_weeks = {1, 5, 9, 13}

        for week in amrap_weeks:
            assert plan[week]['is_amrap_week'] is True, f"Week {week} should be AMRAP week"

        for week in non_amrap_weeks:
            assert plan[week]['is_amrap_week'] is False, f"Week {week} should not be AMRAP week"

    def test_1rm_update_from_amrap(self):
        """1RM should update based on AMRAP results for subsequent weeks."""
        start_1rm = 300.0

        # Week 2 AMRAP: 10 reps at 225 lbs with 6s TUT
        # Effective reps = 10 * (6/3) = 20
        # New 1RM = 225 * (1 + 20/30) = 225 * 1.667 = 375
        amrap_results = {
            2: {'weight': 225.0, 'actual_reps': 10, 'tut_per_rep': 6.0, 'normal_tempo': 3.0}
        }

        plan = build_training_plan(start_1rm=start_1rm, amrap_results=amrap_results)

        # Week 2 should still use original 1RM
        assert plan[2]['current_1rm'] == start_1rm

        # Week 3 and beyond should use updated 1RM (375)
        expected_new_1rm = 375.0
        assert plan[3]['current_1rm'] == pytest.approx(expected_new_1rm)
        assert plan[4]['current_1rm'] == pytest.approx(expected_new_1rm)

    def test_multiple_amrap_updates(self):
        """Multiple AMRAP results should progressively update 1RM."""
        start_1rm = 300.0

        amrap_results = {
            2: {'weight': 225.0, 'actual_reps': 10},  # New 1RM: 375 (225 * (1 + 20/30))
            3: {'weight': 300.0, 'actual_reps': 8},   # New 1RM: 460 (300 * (1 + 16/30))
        }

        plan = build_training_plan(start_1rm=start_1rm, amrap_results=amrap_results)

        # Week 2 uses start 1RM
        assert plan[2]['current_1rm'] == 300.0

        # Week 3 uses 1RM from week 2 AMRAP (375)
        assert plan[3]['current_1rm'] == pytest.approx(375.0)

        # Week 4 uses 1RM from week 3 AMRAP (460)
        # Week 3: 8 reps at 300 lbs → effective reps = 16 → 300 * (1 + 16/30) = 460
        assert plan[4]['current_1rm'] == pytest.approx(460.0)

    def test_custom_block_percentages(self):
        """Should accept and use custom block percentages."""
        custom_percentages = [
            [0.6, 0.65, 0.7, 0.65],     # Custom Block 1
            [0.7, 0.75, 0.8, 0.75],     # Custom Block 2
            [0.75, 0.8, 0.85, 0.9, 0.6] # Custom Block 3
        ]

        plan = build_training_plan(start_1rm=300.0, block_percentages=custom_percentages)

        assert plan[1]['percentage'] == 0.6
        assert plan[5]['percentage'] == 0.7
        assert plan[9]['percentage'] == 0.75

    def test_prescribed_weight_calculation(self):
        """Prescribed weight should be current_1rm * percentage."""
        start_1rm = 400.0
        plan = build_training_plan(start_1rm=start_1rm)

        for week in range(1, 14):
            expected_weight = plan[week]['current_1rm'] * plan[week]['percentage']
            assert abs(plan[week]['prescribed_weight'] - expected_weight) < 0.01

    def test_amrap_results_with_default_tut(self):
        """AMRAP results should use default TUT values if not provided."""
        start_1rm = 300.0
        amrap_results = {
            2: {'weight': 225.0, 'actual_reps': 10}  # Missing TUT params
        }

        plan = build_training_plan(start_1rm=start_1rm, amrap_results=amrap_results)

        # Should use defaults: tut_per_rep=6.0, normal_tempo=3.0
        # Effective reps = 10 * (6/3) = 20
        # New 1RM = 225 * (1 + 20/30) = 375
        assert plan[3]['current_1rm'] == pytest.approx(375.0)

    def test_zero_reps_amrap(self):
        """AMRAP with 0 reps should set 1RM to the attempted weight."""
        start_1rm = 300.0
        amrap_results = {
            2: {'weight': 300.0, 'actual_reps': 0}
        }

        plan = build_training_plan(start_1rm=start_1rm, amrap_results=amrap_results)

        # Week 3 should use the weight as new 1RM (since 0 reps)
        assert plan[3]['current_1rm'] == 300.0

    def test_invalid_start_1rm(self):
        """Should raise ValueError for non-positive start_1rm."""
        with pytest.raises(ValueError, match="start_1rm must be positive"):
            build_training_plan(start_1rm=0)

        with pytest.raises(ValueError, match="start_1rm must be positive"):
            build_training_plan(start_1rm=-100)

    def test_invalid_block_percentages_length(self):
        """Should raise ValueError if block_percentages doesn't have 3 blocks."""
        invalid_percentages = [
            [0.7, 0.75, 0.8, 0.725],
            [0.775, 0.825, 0.85, 0.775]
            # Missing Block 3
        ]

        with pytest.raises(ValueError, match="must contain exactly 3 blocks"):
            build_training_plan(start_1rm=300.0, block_percentages=invalid_percentages)

    def test_invalid_block_percentages_weeks(self):
        """Should raise ValueError if block weeks are incorrect."""
        invalid_percentages = [
            [0.7, 0.75, 0.8],  # Only 3 weeks instead of 4
            [0.775, 0.825, 0.85, 0.775],
            [0.8, 0.85, 0.875, 0.9, 0.65]
        ]

        with pytest.raises(ValueError, match="must have 4, 4, and 5 weeks"):
            build_training_plan(start_1rm=300.0, block_percentages=invalid_percentages)

    def test_missing_amrap_keys(self):
        """Should raise ValueError if AMRAP data is missing required keys."""
        amrap_results = {
            2: {'weight': 225.0}  # Missing 'actual_reps'
        }

        with pytest.raises(ValueError, match="must contain 'weight' and 'actual_reps'"):
            build_training_plan(start_1rm=300.0, amrap_results=amrap_results)

    def test_integration_full_program(self):
        """Integration test: Complete 13-week program with multiple AMRAP updates."""
        start_1rm = 300.0

        # Simulate AMRAP results across all AMRAP weeks
        amrap_results = {
            2: {'weight': 225.0, 'actual_reps': 10},  # Block 1
            3: {'weight': 281.25, 'actual_reps': 8},
            4: {'weight': 300.0, 'actual_reps': 7},
            6: {'weight': 310.0, 'actual_reps': 9},   # Block 2
            7: {'weight': 330.0, 'actual_reps': 7},
            8: {'weight': 340.0, 'actual_reps': 6},
            10: {'weight': 350.0, 'actual_reps': 8},  # Block 3
            11: {'weight': 360.0, 'actual_reps': 7},
            12: {'weight': 370.0, 'actual_reps': 5},
        }

        plan = build_training_plan(start_1rm=start_1rm, amrap_results=amrap_results)

        # Verify plan structure
        assert len(plan) == 13
        assert all('prescribed_weight' in plan[w] for w in range(1, 14))
        assert all('current_1rm' in plan[w] for w in range(1, 14))
        assert all('percentage' in plan[w] for w in range(1, 14))
        assert all('sets' in plan[w] for w in range(1, 14))
        assert all('is_amrap_week' in plan[w] for w in range(1, 14))

        # Verify 1RM progression (should increase over time with good AMRAP performance)
        assert plan[5]['current_1rm'] > plan[1]['current_1rm']  # Block 2 start > Block 1 start
        assert plan[9]['current_1rm'] > plan[5]['current_1rm']  # Block 3 start > Block 2 start

        # Verify deload week has lower intensity
        assert plan[13]['percentage'] == 0.65
        assert plan[13]['prescribed_weight'] < plan[12]['prescribed_weight']


class TestSuggestNextWeekWorkout:
    """Test suite for suggest_next_week_workout() function."""

    @pytest.fixture
    def sample_plan(self):
        """Create a sample training plan for testing."""
        return build_training_plan(start_1rm=300.0)

    def test_returns_all_required_fields(self, sample_plan):
        """Should return all required workout prescription fields."""
        workout = suggest_next_week_workout(1, "Squat", sample_plan)

        assert 'week' in workout
        assert 'lift' in workout
        assert 'sets' in workout
        assert 'target_reps' in workout
        assert 'weight' in workout
        assert 'is_amrap_week' in workout
        assert 'instructions' in workout

    def test_week1_squat_prescription(self, sample_plan):
        """Should generate correct prescription for Week 1 Squat."""
        workout = suggest_next_week_workout(1, "Squat", sample_plan)

        assert workout['week'] == 1
        assert workout['lift'] == "Squat"
        assert workout['sets'] == 3  # Block 1
        assert workout['target_reps'] == "9-12"  # Squat/Bench range
        assert workout['weight'] == 210.0  # 300 * 0.7
        assert workout['is_amrap_week'] is False

    def test_week2_amrap_instructions(self, sample_plan):
        """Should include AMRAP instructions for Week 2."""
        workout = suggest_next_week_workout(2, "Squat", sample_plan)

        assert workout['is_amrap_week'] is True
        assert "AMRAP" in workout['instructions']
        assert "final set" in workout['instructions']

    def test_week5_block2_sets(self, sample_plan):
        """Should prescribe 4 sets for Block 2."""
        workout = suggest_next_week_workout(5, "Bench Press", sample_plan)

        assert workout['sets'] == 4
        assert workout['week'] == 5

    def test_week10_block3_sets(self, sample_plan):
        """Should prescribe 5 sets for Block 3."""
        workout = suggest_next_week_workout(10, "Pull-ups", sample_plan)

        assert workout['sets'] == 5
        assert workout['week'] == 10

    def test_pullups_rep_range(self, sample_plan):
        """Pull-ups should have 10-15 rep range."""
        workout = suggest_next_week_workout(1, "Pull-ups", sample_plan)

        assert workout['target_reps'] == "10-15"

    def test_squat_rep_range(self, sample_plan):
        """Squat should have 9-12 rep range."""
        workout = suggest_next_week_workout(1, "Squat", sample_plan)

        assert workout['target_reps'] == "9-12"

    def test_bench_press_rep_range(self, sample_plan):
        """Bench Press should have 9-12 rep range."""
        workout = suggest_next_week_workout(1, "Bench Press", sample_plan)

        assert workout['target_reps'] == "9-12"

    def test_instructions_format(self, sample_plan):
        """Instructions should be properly formatted."""
        workout = suggest_next_week_workout(1, "Squat", sample_plan)

        instructions = workout['instructions']
        assert "Week 1" in instructions
        assert "Squat" in instructions
        assert "3 sets" in instructions
        assert "9-12 reps" in instructions
        assert "210.0 lbs" in instructions

    def test_amrap_weeks_have_special_instructions(self, sample_plan):
        """All AMRAP weeks should have special instructions."""
        amrap_weeks = [2, 3, 4, 6, 7, 8, 10, 11, 12]

        for week in amrap_weeks:
            workout = suggest_next_week_workout(week, "Squat", sample_plan)
            assert workout['is_amrap_week'] is True
            assert "SPECIAL" in workout['instructions']
            assert "AMRAP" in workout['instructions']

    def test_non_amrap_weeks_no_special_instructions(self, sample_plan):
        """Non-AMRAP weeks should not have special instructions."""
        non_amrap_weeks = [1, 5, 9, 13]

        for week in non_amrap_weeks:
            workout = suggest_next_week_workout(week, "Squat", sample_plan)
            assert workout['is_amrap_week'] is False
            assert "SPECIAL" not in workout['instructions']

    def test_week13_deload(self, sample_plan):
        """Week 13 should show deload weight."""
        workout = suggest_next_week_workout(13, "Squat", sample_plan)

        assert workout['week'] == 13
        assert workout['sets'] == 5  # Still Block 3
        assert workout['weight'] == 195.0  # 300 * 0.65 (deload)
        assert workout['is_amrap_week'] is False

    def test_invalid_week_below_range(self, sample_plan):
        """Should raise ValueError for week < 1."""
        with pytest.raises(ValueError, match="current_week must be between 1 and 13"):
            suggest_next_week_workout(0, "Squat", sample_plan)

    def test_invalid_week_above_range(self, sample_plan):
        """Should raise ValueError for week > 13."""
        with pytest.raises(ValueError, match="current_week must be between 1 and 13"):
            suggest_next_week_workout(14, "Squat", sample_plan)

    def test_invalid_lift_name(self, sample_plan):
        """Should raise ValueError for invalid lift name."""
        with pytest.raises(ValueError, match="lift_name must be one of"):
            suggest_next_week_workout(1, "Deadlift", sample_plan)

    def test_week_not_in_plan(self):
        """Should raise ValueError if week not in training plan."""
        # Create a plan that's missing week 2
        incomplete_plan = {1: {'prescribed_weight': 210, 'sets': 3, 'is_amrap_week': False}}

        with pytest.raises(ValueError, match="Week 2 not found in training_plan"):
            suggest_next_week_workout(2, "Squat", incomplete_plan)

    def test_all_three_lifts(self, sample_plan):
        """Should work for all three lift types."""
        lifts = ["Squat", "Bench Press", "Pull-ups"]

        for lift in lifts:
            workout = suggest_next_week_workout(1, lift, sample_plan)
            assert workout['lift'] == lift
            assert 'instructions' in workout

    def test_progression_across_weeks(self, sample_plan):
        """Should show weight progression across weeks within a block."""
        week1 = suggest_next_week_workout(1, "Squat", sample_plan)
        week2 = suggest_next_week_workout(2, "Squat", sample_plan)
        week3 = suggest_next_week_workout(3, "Squat", sample_plan)

        # Week 3 should have higher weight than Week 1 (80% vs 70%)
        assert week3['weight'] > week1['weight']

    def test_integration_with_updated_1rm(self):
        """Should work with training plan that has updated 1RMs."""
        # Create plan with AMRAP results
        amrap_results = {
            2: {'weight': 225.0, 'actual_reps': 10}
        }
        plan = build_training_plan(start_1rm=300.0, amrap_results=amrap_results)

        # Week 3 should use updated 1RM from week 2
        workout = suggest_next_week_workout(3, "Squat", plan)
        # 375 * 0.8 = 300 (updated 1RM from AMRAP)
        assert workout['weight'] == pytest.approx(300.0)
