"""
Performance Tracking Module

This module provides functions for tracking training performance data throughout
the 13-week program. Uses pandas DataFrame for efficient data storage and analysis.
"""

import pandas as pd
from typing import Optional, Union
from pathlib import Path
from .one_rm import estimate_1rm_from_amrap


def get_block_from_week(week: int) -> int:
    """
    Determine which block a given week belongs to.

    Args:
        week: Week number (1-13)

    Returns:
        Block number (1, 2, or 3)

    Raises:
        ValueError: If week is not in range 1-13

    Example:
        >>> get_block_from_week(1)
        1
        >>> get_block_from_week(5)
        2
        >>> get_block_from_week(9)
        3
    """
    if not 1 <= week <= 13:
        raise ValueError("week must be between 1 and 13")

    if week <= 4:
        return 1
    elif week <= 8:
        return 2
    else:
        return 3


def initialize_performance_log() -> pd.DataFrame:
    """
    Create an empty performance tracking DataFrame with the proper schema.

    Returns:
        Empty pandas DataFrame with columns for tracking training performance:
        - week (int): Week number (1-13)
        - block (int): Block number (1-3)
        - lift (str): Lift name (e.g., "Squat", "Bench Press", "Pull-ups")
        - weight (float): Actual weight used in pounds/kg
        - reps (int): Number of reps completed
        - total_tut (float): Total time under tension for the set in seconds
        - rpe (float): Rate of Perceived Exertion (1-10 scale)
        - estimated_1rm (float): Calculated 1RM from that performance

    Example:
        >>> df = initialize_performance_log()
        >>> df.columns.tolist()
        ['week', 'block', 'lift', 'weight', 'reps', 'total_tut', 'rpe', 'estimated_1rm']
    """
    return pd.DataFrame(columns=[
        'week',
        'block',
        'lift',
        'weight',
        'reps',
        'total_tut',
        'rpe',
        'estimated_1rm'
    ])


def log_performance(
    df: pd.DataFrame,
    week: int,
    lift: str,
    weight: float,
    reps: int,
    total_tut: float,
    rpe: float,
    tut_per_rep: float = 6.0,
    normal_tempo: float = 3.0
) -> pd.DataFrame:
    """
    Add a new performance record to the tracking DataFrame.

    Args:
        df: Existing performance log DataFrame
        week: Week number (1-13)
        lift: Lift name (e.g., "Squat", "Bench Press", "Pull-ups")
        weight: Weight used in pounds/kg
        reps: Number of reps completed
        total_tut: Total time under tension for the set in seconds
        rpe: Rate of Perceived Exertion (1-10 scale)
        tut_per_rep: Time under tension per rep in seconds (default 6s)
        normal_tempo: Baseline tempo in seconds (default 3s)

    Returns:
        Updated DataFrame with the new record appended

    Raises:
        ValueError: If inputs are invalid (negative values, out of range, etc.)

    Example:
        >>> df = initialize_performance_log()
        >>> df = log_performance(df, week=1, lift="Squat", weight=225, reps=10,
        ...                      total_tut=60, rpe=7.5)
        >>> len(df)
        1
    """
    # Validate inputs
    if not 1 <= week <= 13:
        raise ValueError("week must be between 1 and 13")
    if not isinstance(lift, str) or not lift.strip():
        raise ValueError("lift must be a non-empty string")
    if weight <= 0:
        raise ValueError("weight must be positive")
    if reps < 0:
        raise ValueError("reps must be non-negative")
    if total_tut < 0:
        raise ValueError("total_tut must be non-negative")
    if not 1 <= rpe <= 10:
        raise ValueError("rpe must be between 1 and 10")

    # Determine block from week
    block = get_block_from_week(week)

    # Calculate estimated 1RM from performance
    estimated_1rm = estimate_1rm_from_amrap(
        weight=weight,
        actual_reps=reps,
        tut_per_rep=tut_per_rep,
        normal_tempo=normal_tempo
    )

    # Create new record
    new_record = {
        'week': week,
        'block': block,
        'lift': lift,
        'weight': weight,
        'reps': reps,
        'total_tut': total_tut,
        'rpe': rpe,
        'estimated_1rm': estimated_1rm
    }

    # Append to DataFrame using pd.concat for better performance
    new_df = pd.DataFrame([new_record])
    updated_df = pd.concat([df, new_df], ignore_index=True)

    return updated_df


def track_weekly_performance(
    df: pd.DataFrame,
    week: int,
    lift_name: str,
    weight: float,
    reps: int,
    total_tut: float,
    rpe: float,
    tut_per_rep: float = 6.0,
    normal_tempo: float = 3.0
) -> pd.DataFrame:
    """
    Record weekly training data after completing workouts.

    This is the primary function for logging training performance data as specified
    in the program requirements. It validates inputs, calculates block and estimated 1RM,
    and appends the new record to the DataFrame.

    Args:
        df: Existing performance log DataFrame
        week: Current week number (1-13)
        lift_name: Which lift ("Squat", "Bench Press", "Pull-ups")
        weight: Weight used in pounds/kg
        reps: Reps completed
        total_tut: Total time under tension for the set in seconds
        rpe: RPE rating (1-10 scale)
        tut_per_rep: Time under tension per rep in seconds (default 6s)
        normal_tempo: Baseline tempo in seconds (default 3s)

    Returns:
        Updated DataFrame with the new record appended

    Raises:
        ValueError: If inputs are invalid (week out of range, invalid lift name,
                   negative values, RPE out of range)

    Example:
        >>> df = initialize_performance_log()
        >>> df = track_weekly_performance(df, week=1, lift_name="Squat", weight=225,
        ...                               reps=10, total_tut=60, rpe=7.5)
        >>> len(df)
        1

    Notes:
        - Block is automatically calculated from week (1-4=Block 1, 5-8=Block 2, 9-13=Block 3)
        - Estimated 1RM is automatically calculated using TUT-adjusted Epley formula
        - Use save_performance_log() separately if you want to persist to CSV
    """
    # Delegate to log_performance with parameter name mapping
    return log_performance(
        df=df,
        week=week,
        lift=lift_name,
        weight=weight,
        reps=reps,
        total_tut=total_tut,
        rpe=rpe,
        tut_per_rep=tut_per_rep,
        normal_tempo=normal_tempo
    )


def save_performance_log(df: pd.DataFrame, filepath: Union[str, Path]) -> None:
    """
    Save performance log DataFrame to a CSV file.

    Args:
        df: Performance log DataFrame to save
        filepath: Path where to save the CSV file

    Example:
        >>> df = initialize_performance_log()
        >>> df = log_performance(df, week=1, lift="Squat", weight=225, reps=10,
        ...                      total_tut=60, rpe=7.5)
        >>> save_performance_log(df, "data/training_log.csv")
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(filepath, index=False)


def load_performance_log(filepath: Union[str, Path]) -> pd.DataFrame:
    """
    Load performance log DataFrame from a CSV file.

    Args:
        filepath: Path to the CSV file to load

    Returns:
        Performance log DataFrame

    Raises:
        FileNotFoundError: If the file doesn't exist

    Example:
        >>> df = load_performance_log("data/training_log.csv")
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"Performance log not found at {filepath}")

    df = pd.read_csv(filepath)

    # Ensure proper dtypes
    df['week'] = df['week'].astype(int)
    df['block'] = df['block'].astype(int)
    df['lift'] = df['lift'].astype(str)
    df['weight'] = df['weight'].astype(float)
    df['reps'] = df['reps'].astype(int)
    df['total_tut'] = df['total_tut'].astype(float)
    df['rpe'] = df['rpe'].astype(float)
    df['estimated_1rm'] = df['estimated_1rm'].astype(float)

    return df


def get_performance_by_lift(df: pd.DataFrame, lift: str) -> pd.DataFrame:
    """
    Filter performance log to show only records for a specific lift.

    Args:
        df: Performance log DataFrame
        lift: Lift name to filter by

    Returns:
        Filtered DataFrame containing only records for the specified lift

    Example:
        >>> df = load_performance_log("data/training_log.csv")
        >>> squat_data = get_performance_by_lift(df, "Squat")
    """
    return df[df['lift'] == lift].copy()


def get_performance_by_week(df: pd.DataFrame, week: int) -> pd.DataFrame:
    """
    Filter performance log to show only records for a specific week.

    Args:
        df: Performance log DataFrame
        week: Week number to filter by (1-13)

    Returns:
        Filtered DataFrame containing only records for the specified week

    Raises:
        ValueError: If week is not in range 1-13

    Example:
        >>> df = load_performance_log("data/training_log.csv")
        >>> week1_data = get_performance_by_week(df, 1)
    """
    if not 1 <= week <= 13:
        raise ValueError("week must be between 1 and 13")

    return df[df['week'] == week].copy()


def get_performance_by_block(df: pd.DataFrame, block: int) -> pd.DataFrame:
    """
    Filter performance log to show only records for a specific block.

    Args:
        df: Performance log DataFrame
        block: Block number to filter by (1-3)

    Returns:
        Filtered DataFrame containing only records for the specified block

    Raises:
        ValueError: If block is not 1, 2, or 3

    Example:
        >>> df = load_performance_log("data/training_log.csv")
        >>> block1_data = get_performance_by_block(df, 1)
    """
    if block not in [1, 2, 3]:
        raise ValueError("block must be 1, 2, or 3")

    return df[df['block'] == block].copy()


def get_latest_1rm_by_lift(df: pd.DataFrame, lift: str) -> Optional[float]:
    """
    Get the most recent estimated 1RM for a specific lift.

    Args:
        df: Performance log DataFrame
        lift: Lift name to query

    Returns:
        Most recent estimated 1RM for the lift, or None if no records exist

    Example:
        >>> df = load_performance_log("data/training_log.csv")
        >>> latest_squat_1rm = get_latest_1rm_by_lift(df, "Squat")
    """
    lift_data = get_performance_by_lift(df, lift)

    if lift_data.empty:
        return None

    # Get the record with the highest week number (using sort_values for compatibility)
    latest_record = lift_data.sort_values('week', ascending=False).iloc[0]
    return float(latest_record['estimated_1rm'])
