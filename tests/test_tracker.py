"""
Tests for performance tracking functions.
"""

import pytest
import pandas as pd
import tempfile
from pathlib import Path
from src.training.tracker import (
    get_block_from_week,
    initialize_performance_log,
    log_performance,
    track_weekly_performance,
    save_performance_log,
    load_performance_log,
    get_performance_by_lift,
    get_performance_by_week,
    get_performance_by_block,
    get_latest_1rm_by_lift
)


class TestGetBlockFromWeek:
    """Test suite for get_block_from_week() function."""

    def test_block1_weeks(self):
        """Weeks 1-4 should be in block 1."""
        assert get_block_from_week(1) == 1
        assert get_block_from_week(2) == 1
        assert get_block_from_week(3) == 1
        assert get_block_from_week(4) == 1

    def test_block2_weeks(self):
        """Weeks 5-8 should be in block 2."""
        assert get_block_from_week(5) == 2
        assert get_block_from_week(6) == 2
        assert get_block_from_week(7) == 2
        assert get_block_from_week(8) == 2

    def test_block3_weeks(self):
        """Weeks 9-13 should be in block 3."""
        assert get_block_from_week(9) == 3
        assert get_block_from_week(10) == 3
        assert get_block_from_week(11) == 3
        assert get_block_from_week(12) == 3
        assert get_block_from_week(13) == 3

    def test_invalid_week_below_range(self):
        """Should raise ValueError for week < 1."""
        with pytest.raises(ValueError, match="week must be between 1 and 13"):
            get_block_from_week(0)

    def test_invalid_week_above_range(self):
        """Should raise ValueError for week > 13."""
        with pytest.raises(ValueError, match="week must be between 1 and 13"):
            get_block_from_week(14)


class TestInitializePerformanceLog:
    """Test suite for initialize_performance_log() function."""

    def test_creates_empty_dataframe(self):
        """Should create an empty DataFrame."""
        df = initialize_performance_log()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_has_correct_columns(self):
        """Should have all required columns."""
        df = initialize_performance_log()
        expected_columns = ['week', 'block', 'lift', 'weight', 'reps', 'total_tut', 'rpe', 'estimated_1rm']
        assert df.columns.tolist() == expected_columns

    def test_column_order(self):
        """Columns should be in the correct order."""
        df = initialize_performance_log()
        assert df.columns[0] == 'week'
        assert df.columns[1] == 'block'
        assert df.columns[2] == 'lift'
        assert df.columns[-1] == 'estimated_1rm'


class TestLogPerformance:
    """Test suite for log_performance() function."""

    def test_adds_single_record(self):
        """Should successfully add a single record."""
        df = initialize_performance_log()
        df = log_performance(df, week=1, lift="Squat", weight=225.0, reps=10, total_tut=60.0, rpe=7.5)

        assert len(df) == 1
        assert df.iloc[0]['week'] == 1
        assert df.iloc[0]['lift'] == "Squat"
        assert df.iloc[0]['weight'] == 225.0
        assert df.iloc[0]['reps'] == 10
        assert df.iloc[0]['total_tut'] == 60.0
        assert df.iloc[0]['rpe'] == 7.5

    def test_auto_calculates_block(self):
        """Should automatically determine the correct block."""
        df = initialize_performance_log()
        df = log_performance(df, week=1, lift="Squat", weight=225, reps=10, total_tut=60, rpe=7)
        assert df.iloc[0]['block'] == 1

        df = log_performance(df, week=5, lift="Squat", weight=225, reps=10, total_tut=60, rpe=7)
        assert df.iloc[1]['block'] == 2

        df = log_performance(df, week=9, lift="Squat", weight=225, reps=10, total_tut=60, rpe=7)
        assert df.iloc[2]['block'] == 3

    def test_auto_calculates_estimated_1rm(self):
        """Should automatically calculate estimated 1RM."""
        df = initialize_performance_log()
        # 10 reps at 225 lbs with 6s TUT → effective reps = 20 → 1RM = 225 * (1 + 20/30) = 375
        df = log_performance(df, week=1, lift="Squat", weight=225, reps=10, total_tut=60, rpe=7)
        assert df.iloc[0]['estimated_1rm'] == pytest.approx(375.0)

    def test_adds_multiple_records(self):
        """Should handle multiple records correctly."""
        df = initialize_performance_log()
        df = log_performance(df, week=1, lift="Squat", weight=225, reps=10, total_tut=60, rpe=7)
        df = log_performance(df, week=1, lift="Bench Press", weight=185, reps=12, total_tut=72, rpe=8)
        df = log_performance(df, week=2, lift="Squat", weight=240, reps=8, total_tut=48, rpe=8.5)

        assert len(df) == 3
        assert df.iloc[0]['lift'] == "Squat"
        assert df.iloc[1]['lift'] == "Bench Press"
        assert df.iloc[2]['week'] == 2

    def test_different_lifts(self):
        """Should handle different lift types."""
        df = initialize_performance_log()
        df = log_performance(df, week=1, lift="Squat", weight=225, reps=10, total_tut=60, rpe=7)
        df = log_performance(df, week=1, lift="Bench Press", weight=185, reps=12, total_tut=72, rpe=7)
        df = log_performance(df, week=1, lift="Pull-ups", weight=200, reps=15, total_tut=90, rpe=6)

        assert len(df) == 3
        lifts = df['lift'].tolist()
        assert "Squat" in lifts
        assert "Bench Press" in lifts
        assert "Pull-ups" in lifts

    def test_zero_reps(self):
        """Should handle 0 reps (failed attempt)."""
        df = initialize_performance_log()
        df = log_performance(df, week=1, lift="Squat", weight=300, reps=0, total_tut=0, rpe=10)

        assert len(df) == 1
        assert df.iloc[0]['reps'] == 0
        assert df.iloc[0]['estimated_1rm'] == 300  # 0 reps means weight is the 1RM

    def test_custom_tut_parameters(self):
        """Should accept custom TUT parameters."""
        df = initialize_performance_log()
        df = log_performance(df, week=1, lift="Squat", weight=225, reps=10,
                           total_tut=60, rpe=7, tut_per_rep=5.0, normal_tempo=2.5)
        assert len(df) == 1
        # Custom TUT calculation: effective reps = 10 * (5/2.5) = 20
        assert df.iloc[0]['estimated_1rm'] == pytest.approx(375.0)

    def test_invalid_week_below_range(self):
        """Should raise ValueError for week < 1."""
        df = initialize_performance_log()
        with pytest.raises(ValueError, match="week must be between 1 and 13"):
            log_performance(df, week=0, lift="Squat", weight=225, reps=10, total_tut=60, rpe=7)

    def test_invalid_week_above_range(self):
        """Should raise ValueError for week > 13."""
        df = initialize_performance_log()
        with pytest.raises(ValueError, match="week must be between 1 and 13"):
            log_performance(df, week=14, lift="Squat", weight=225, reps=10, total_tut=60, rpe=7)

    def test_invalid_lift_empty_string(self):
        """Should raise ValueError for empty lift name."""
        df = initialize_performance_log()
        with pytest.raises(ValueError, match="lift must be a non-empty string"):
            log_performance(df, week=1, lift="", weight=225, reps=10, total_tut=60, rpe=7)

    def test_invalid_weight(self):
        """Should raise ValueError for non-positive weight."""
        df = initialize_performance_log()
        with pytest.raises(ValueError, match="weight must be positive"):
            log_performance(df, week=1, lift="Squat", weight=0, reps=10, total_tut=60, rpe=7)

        with pytest.raises(ValueError, match="weight must be positive"):
            log_performance(df, week=1, lift="Squat", weight=-100, reps=10, total_tut=60, rpe=7)

    def test_invalid_negative_reps(self):
        """Should raise ValueError for negative reps."""
        df = initialize_performance_log()
        with pytest.raises(ValueError, match="reps must be non-negative"):
            log_performance(df, week=1, lift="Squat", weight=225, reps=-1, total_tut=60, rpe=7)

    def test_invalid_negative_tut(self):
        """Should raise ValueError for negative TUT."""
        df = initialize_performance_log()
        with pytest.raises(ValueError, match="total_tut must be non-negative"):
            log_performance(df, week=1, lift="Squat", weight=225, reps=10, total_tut=-5, rpe=7)

    def test_invalid_rpe_below_range(self):
        """Should raise ValueError for RPE < 1."""
        df = initialize_performance_log()
        with pytest.raises(ValueError, match="rpe must be between 1 and 10"):
            log_performance(df, week=1, lift="Squat", weight=225, reps=10, total_tut=60, rpe=0)

    def test_invalid_rpe_above_range(self):
        """Should raise ValueError for RPE > 10."""
        df = initialize_performance_log()
        with pytest.raises(ValueError, match="rpe must be between 1 and 10"):
            log_performance(df, week=1, lift="Squat", weight=225, reps=10, total_tut=60, rpe=11)


class TestTrackWeeklyPerformance:
    """Test suite for track_weekly_performance() function."""

    def test_adds_single_record(self):
        """Should successfully add a single record using lift_name parameter."""
        df = initialize_performance_log()
        df = track_weekly_performance(df, week=1, lift_name="Squat", weight=225.0,
                                     reps=10, total_tut=60.0, rpe=7.5)

        assert len(df) == 1
        assert df.iloc[0]['week'] == 1
        assert df.iloc[0]['lift'] == "Squat"
        assert df.iloc[0]['weight'] == 225.0
        assert df.iloc[0]['reps'] == 10
        assert df.iloc[0]['total_tut'] == 60.0
        assert df.iloc[0]['rpe'] == 7.5

    def test_auto_calculates_block_and_1rm(self):
        """Should automatically calculate block and estimated 1RM."""
        df = initialize_performance_log()
        df = track_weekly_performance(df, week=5, lift_name="Bench Press", weight=185,
                                     reps=12, total_tut=72, rpe=8.0)

        assert df.iloc[0]['block'] == 2  # Week 5 is in Block 2
        # 12 reps at 185 lbs → effective reps = 24 → 1RM = 185 * (1 + 24/30) = 333
        assert df.iloc[0]['estimated_1rm'] == pytest.approx(333.0)

    def test_handles_multiple_lifts(self):
        """Should handle different lift names correctly."""
        df = initialize_performance_log()
        df = track_weekly_performance(df, week=1, lift_name="Squat", weight=225,
                                     reps=10, total_tut=60, rpe=7)
        df = track_weekly_performance(df, week=1, lift_name="Bench Press", weight=185,
                                     reps=12, total_tut=72, rpe=7)
        df = track_weekly_performance(df, week=1, lift_name="Pull-ups", weight=200,
                                     reps=15, total_tut=90, rpe=6)

        assert len(df) == 3
        assert df.iloc[0]['lift'] == "Squat"
        assert df.iloc[1]['lift'] == "Bench Press"
        assert df.iloc[2]['lift'] == "Pull-ups"

    def test_validation_errors(self):
        """Should raise appropriate errors for invalid inputs."""
        df = initialize_performance_log()

        # Invalid week
        with pytest.raises(ValueError, match="week must be between 1 and 13"):
            track_weekly_performance(df, week=0, lift_name="Squat", weight=225,
                                   reps=10, total_tut=60, rpe=7)

        # Invalid lift name
        with pytest.raises(ValueError, match="lift must be a non-empty string"):
            track_weekly_performance(df, week=1, lift_name="", weight=225,
                                   reps=10, total_tut=60, rpe=7)

        # Invalid weight
        with pytest.raises(ValueError, match="weight must be positive"):
            track_weekly_performance(df, week=1, lift_name="Squat", weight=0,
                                   reps=10, total_tut=60, rpe=7)

        # Invalid RPE
        with pytest.raises(ValueError, match="rpe must be between 1 and 10"):
            track_weekly_performance(df, week=1, lift_name="Squat", weight=225,
                                   reps=10, total_tut=60, rpe=11)

    def test_complete_workout_logging(self):
        """Test logging a complete workout with multiple sets."""
        df = initialize_performance_log()

        # Log all sets from a squat workout
        df = track_weekly_performance(df, week=2, lift_name="Squat", weight=240,
                                     reps=10, total_tut=60, rpe=7.0)
        df = track_weekly_performance(df, week=2, lift_name="Squat", weight=240,
                                     reps=9, total_tut=54, rpe=7.5)
        df = track_weekly_performance(df, week=2, lift_name="Squat", weight=240,
                                     reps=8, total_tut=48, rpe=8.5)

        assert len(df) == 3
        assert all(df['week'] == 2)
        assert all(df['lift'] == "Squat")
        assert all(df['weight'] == 240)

        # Verify RPE progression (fatigue across sets)
        assert df.iloc[0]['rpe'] == 7.0
        assert df.iloc[1]['rpe'] == 7.5
        assert df.iloc[2]['rpe'] == 8.5


class TestSaveAndLoadPerformanceLog:
    """Test suite for save_performance_log() and load_performance_log() functions."""

    def test_save_and_load_roundtrip(self):
        """Should save and load data without loss."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test_log.csv"

            # Create and save log
            df = initialize_performance_log()
            df = log_performance(df, week=1, lift="Squat", weight=225, reps=10, total_tut=60, rpe=7.5)
            df = log_performance(df, week=1, lift="Bench Press", weight=185, reps=12, total_tut=72, rpe=8)
            save_performance_log(df, filepath)

            # Load and verify
            loaded_df = load_performance_log(filepath)
            assert len(loaded_df) == 2
            assert loaded_df.iloc[0]['lift'] == "Squat"
            assert loaded_df.iloc[1]['lift'] == "Bench Press"

    def test_save_creates_parent_directories(self):
        """Should create parent directories if they don't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "subdir" / "test_log.csv"

            df = initialize_performance_log()
            df = log_performance(df, week=1, lift="Squat", weight=225, reps=10, total_tut=60, rpe=7)
            save_performance_log(df, filepath)

            assert filepath.exists()
            loaded_df = load_performance_log(filepath)
            assert len(loaded_df) == 1

    def test_load_preserves_dtypes(self):
        """Should preserve correct data types after loading."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test_log.csv"

            df = initialize_performance_log()
            df = log_performance(df, week=1, lift="Squat", weight=225, reps=10, total_tut=60, rpe=7.5)
            save_performance_log(df, filepath)

            loaded_df = load_performance_log(filepath)
            assert loaded_df['week'].dtype == 'int64'
            assert loaded_df['block'].dtype == 'int64'
            assert loaded_df['lift'].dtype == 'object'
            assert loaded_df['weight'].dtype == 'float64'
            assert loaded_df['reps'].dtype == 'int64'
            assert loaded_df['total_tut'].dtype == 'float64'
            assert loaded_df['rpe'].dtype == 'float64'
            assert loaded_df['estimated_1rm'].dtype == 'float64'

    def test_load_nonexistent_file(self):
        """Should raise FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            load_performance_log("nonexistent_file.csv")


class TestFilteringFunctions:
    """Test suite for filtering helper functions."""

    @pytest.fixture
    def sample_log(self):
        """Create a sample performance log for testing."""
        df = initialize_performance_log()
        # Week 1 - Block 1
        df = log_performance(df, week=1, lift="Squat", weight=225, reps=10, total_tut=60, rpe=7)
        df = log_performance(df, week=1, lift="Bench Press", weight=185, reps=12, total_tut=72, rpe=7)
        # Week 2 - Block 1
        df = log_performance(df, week=2, lift="Squat", weight=240, reps=8, total_tut=48, rpe=8)
        df = log_performance(df, week=2, lift="Bench Press", weight=200, reps=10, total_tut=60, rpe=8)
        # Week 5 - Block 2
        df = log_performance(df, week=5, lift="Squat", weight=255, reps=7, total_tut=42, rpe=8.5)
        df = log_performance(df, week=5, lift="Pull-ups", weight=200, reps=15, total_tut=90, rpe=6)
        return df

    def test_get_performance_by_lift(self, sample_log):
        """Should filter by lift correctly."""
        squat_data = get_performance_by_lift(sample_log, "Squat")
        assert len(squat_data) == 3
        assert all(squat_data['lift'] == "Squat")

        bench_data = get_performance_by_lift(sample_log, "Bench Press")
        assert len(bench_data) == 2
        assert all(bench_data['lift'] == "Bench Press")

    def test_get_performance_by_week(self, sample_log):
        """Should filter by week correctly."""
        week1_data = get_performance_by_week(sample_log, 1)
        assert len(week1_data) == 2
        assert all(week1_data['week'] == 1)

        week5_data = get_performance_by_week(sample_log, 5)
        assert len(week5_data) == 2
        assert all(week5_data['week'] == 5)

    def test_get_performance_by_week_invalid(self):
        """Should raise ValueError for invalid week."""
        df = initialize_performance_log()
        with pytest.raises(ValueError, match="week must be between 1 and 13"):
            get_performance_by_week(df, 0)

    def test_get_performance_by_block(self, sample_log):
        """Should filter by block correctly."""
        block1_data = get_performance_by_block(sample_log, 1)
        assert len(block1_data) == 4
        assert all(block1_data['block'] == 1)

        block2_data = get_performance_by_block(sample_log, 2)
        assert len(block2_data) == 2
        assert all(block2_data['block'] == 2)

    def test_get_performance_by_block_invalid(self):
        """Should raise ValueError for invalid block."""
        df = initialize_performance_log()
        with pytest.raises(ValueError, match="block must be 1, 2, or 3"):
            get_performance_by_block(df, 0)

        with pytest.raises(ValueError, match="block must be 1, 2, or 3"):
            get_performance_by_block(df, 4)

    def test_get_latest_1rm_by_lift(self, sample_log):
        """Should return the most recent 1RM for a lift."""
        latest_squat = get_latest_1rm_by_lift(sample_log, "Squat")
        # Week 5 Squat: 7 reps at 255 lbs → effective reps = 14 → 255 * (1 + 14/30) = 374.0
        assert latest_squat == pytest.approx(374.0)

    def test_get_latest_1rm_no_records(self):
        """Should return None when no records exist for lift."""
        df = initialize_performance_log()
        result = get_latest_1rm_by_lift(df, "Squat")
        assert result is None

    def test_filtering_returns_copies(self, sample_log):
        """Filtering functions should return copies, not views."""
        filtered = get_performance_by_lift(sample_log, "Squat")
        # Modify the filtered dataframe
        filtered.loc[filtered.index[0], 'rpe'] = 10
        # Original should be unchanged
        assert sample_log.iloc[0]['rpe'] == 7


class TestIntegration:
    """Integration tests for complete workflows."""

    def test_complete_week_logging_workflow(self):
        """Test logging a complete week of training."""
        df = initialize_performance_log()

        # Week 1 - Day 1: Squat
        df = log_performance(df, week=1, lift="Squat", weight=210, reps=12, total_tut=72, rpe=6)
        df = log_performance(df, week=1, lift="Squat", weight=210, reps=11, total_tut=66, rpe=7)
        df = log_performance(df, week=1, lift="Squat", weight=210, reps=10, total_tut=60, rpe=8)

        # Week 1 - Day 2: Bench Press
        df = log_performance(df, week=1, lift="Bench Press", weight=150, reps=12, total_tut=72, rpe=6)
        df = log_performance(df, week=1, lift="Bench Press", weight=150, reps=12, total_tut=72, rpe=7)
        df = log_performance(df, week=1, lift="Bench Press", weight=150, reps=11, total_tut=66, rpe=8)

        assert len(df) == 6
        assert len(get_performance_by_lift(df, "Squat")) == 3
        assert len(get_performance_by_lift(df, "Bench Press")) == 3

    def test_multi_week_progression_tracking(self):
        """Test tracking progression across multiple weeks."""
        df = initialize_performance_log()

        # Simulate 4 weeks of squat progression
        df = log_performance(df, week=1, lift="Squat", weight=210, reps=10, total_tut=60, rpe=7)
        df = log_performance(df, week=2, lift="Squat", weight=225, reps=10, total_tut=60, rpe=7.5)
        df = log_performance(df, week=3, lift="Squat", weight=240, reps=8, total_tut=48, rpe=8)
        df = log_performance(df, week=4, lift="Squat", weight=217.5, reps=12, total_tut=72, rpe=7)

        squat_data = get_performance_by_lift(df, "Squat")
        assert len(squat_data) == 4
        # Verify 1RM is improving
        assert squat_data.iloc[1]['estimated_1rm'] > squat_data.iloc[0]['estimated_1rm']
