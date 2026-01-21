"""
1RM Estimation and Effective Reps Calculation Module

This module provides functions for calculating estimated 1RM from AMRAP performance
with time-under-tension (TUT) adjustments.
"""


def calculate_effective_reps(
    actual_reps: int,
    tut_per_rep: float = 6.0,
    normal_tempo: float = 3.0
) -> float:
    """
    Convert actual reps to effective reps based on TUT adjustment.

    When using slower tempo (higher TUT), fewer reps represent more work.
    This function adjusts rep count to reflect the increased difficulty.

    Args:
        actual_reps: Number of reps completed
        tut_per_rep: Time under tension per rep in seconds (default 6s for 4-0-2-0 tempo)
        normal_tempo: Baseline tempo in seconds (default 3s)

    Returns:
        Effective reps as a float

    Example:
        >>> calculate_effective_reps(10, tut_per_rep=6, normal_tempo=3)
        20.0  # 10 reps at 6s TUT = 20 effective reps at normal tempo
    """
    if actual_reps < 0:
        raise ValueError("actual_reps must be non-negative")
    if tut_per_rep <= 0:
        raise ValueError("tut_per_rep must be positive")
    if normal_tempo <= 0:
        raise ValueError("normal_tempo must be positive")

    # Calculate effective reps by scaling based on TUT ratio
    effective_reps = actual_reps * (tut_per_rep / normal_tempo)

    return effective_reps


def estimate_1rm_from_amrap(
    weight: float,
    actual_reps: int,
    tut_per_rep: float = 6.0,
    normal_tempo: float = 3.0
) -> float:
    """
    Calculate estimated 1RM from AMRAP performance with TUT adjustment.

    Uses the Epley formula with TUT-adjusted effective reps:
    1RM = weight × (1 + effective_reps / 30)

    Args:
        weight: Weight lifted during AMRAP set
        actual_reps: Number of reps completed
        tut_per_rep: Time under tension per rep in seconds (default 6s)
        normal_tempo: Baseline tempo in seconds (default 3s)

    Returns:
        Estimated 1RM as a float

    Example:
        >>> estimate_1rm_from_amrap(225, 10, tut_per_rep=6, normal_tempo=3)
        375.0  # 10 reps at 225lbs with 6s TUT = 20 effective reps = 375lbs 1RM

    Notes:
        - V2 will add validation flag for unrealistic estimates
        - Edge cases: 0 reps returns the weight itself
    """
    if weight <= 0:
        raise ValueError("weight must be positive")
    if actual_reps < 0:
        raise ValueError("actual_reps must be non-negative")

    # Handle edge case: 0 reps means the weight is at or above 1RM
    if actual_reps == 0:
        return weight

    # Convert to effective reps based on TUT
    effective_reps = calculate_effective_reps(actual_reps, tut_per_rep, normal_tempo)

    # Epley formula: 1RM = weight × (1 + reps / 30)
    estimated_1rm = weight * (1 + effective_reps / 30)

    return estimated_1rm
