"""
Training Plan Generation Module

This module provides functions for generating weekly training plans with
progressive overload and 1RM adjustments based on AMRAP performance.
"""

from typing import Dict, List, Optional
from .one_rm import estimate_1rm_from_amrap


def build_training_plan(
    start_1rm: float,
    block_percentages: Optional[List[List[float]]] = None,
    amrap_results: Optional[Dict[int, Dict[str, float]]] = None
) -> Dict[int, Dict[str, float]]:
    """
    Generate 13-week training plan with progressive overload.

    Creates a complete training program with weekly prescriptions based on
    percentage-based programming. Updates 1RM weekly based on AMRAP performance
    and applies progressive volume increases across blocks.

    Args:
        start_1rm: Initial 1RM for the lift in pounds/kg
        block_percentages: List of lists containing percentages for each block.
                          Default:
                            Block 1 (Weeks 1-4): [0.7, 0.75, 0.8, 0.725]
                            Block 2 (Weeks 5-8): [0.775, 0.825, 0.85, 0.775]
                            Block 3 (Weeks 9-13): [0.8, 0.85, 0.875, 0.9, 0.65]
        amrap_results: Optional dict mapping week number to AMRAP data.
                      Format: {week: {'weight': float, 'actual_reps': int,
                                     'tut_per_rep': float, 'normal_tempo': float}}
                      If not provided, assumes no AMRAP data available yet.

    Returns:
        Dictionary with weekly prescription data:
        {
            week_number: {
                'prescribed_weight': float,  # Weight to use for training
                'percentage': float,          # Percentage of current 1RM
                'current_1rm': float,         # 1RM at start of this week
                'sets': int,                  # Number of sets to perform
                'is_amrap_week': bool         # Whether to perform AMRAP this week
            }
        }

    Example:
        >>> plan = build_training_plan(300.0)
        >>> plan[1]
        {'prescribed_weight': 210.0, 'percentage': 0.7, 'current_1rm': 300.0,
         'sets': 3, 'is_amrap_week': False}

    Notes:
        - AMRAP weeks are weeks 2-4, 6-8, and 10-12 (3 consecutive weeks per block)
        - Week 1, 5, 9 are orientation weeks without AMRAP
        - Week 13 is integrated deload at 65%
        - Progressive volume: 3 sets (Block 1) → 4 sets (Block 2) → 5 sets (Block 3)
        - 1RM updates from AMRAP are applied starting the following week
    """
    if start_1rm <= 0:
        raise ValueError("start_1rm must be positive")

    # Default block percentages if not provided
    if block_percentages is None:
        block_percentages = [
            [0.7, 0.75, 0.8, 0.725],      # Block 1 (Weeks 1-4)
            [0.775, 0.825, 0.85, 0.775],  # Block 2 (Weeks 5-8)
            [0.8, 0.85, 0.875, 0.9, 0.65] # Block 3 (Weeks 9-13)
        ]

    # Validate block percentages structure
    if len(block_percentages) != 3:
        raise ValueError("block_percentages must contain exactly 3 blocks")
    if len(block_percentages[0]) != 4 or len(block_percentages[1]) != 4 or len(block_percentages[2]) != 5:
        raise ValueError("block_percentages must have 4, 4, and 5 weeks respectively")

    # Initialize amrap_results if not provided
    if amrap_results is None:
        amrap_results = {}

    # AMRAP weeks: weeks 2-4, 6-8, 10-12
    amrap_weeks = {2, 3, 4, 6, 7, 8, 10, 11, 12}

    # Progressive volume: 3 sets (weeks 1-4), 4 sets (weeks 5-8), 5 sets (weeks 9-13)
    def get_sets_for_week(week: int) -> int:
        if week <= 4:
            return 3
        elif week <= 8:
            return 4
        else:
            return 5

    # Build the training plan week by week
    training_plan = {}
    current_1rm = start_1rm

    for week in range(1, 14):  # Weeks 1-13
        # Determine which block and week within block
        if week <= 4:
            block_idx = 0
            week_in_block = week - 1
        elif week <= 8:
            block_idx = 1
            week_in_block = week - 5
        else:
            block_idx = 2
            week_in_block = week - 9

        # Get percentage for this week
        percentage = block_percentages[block_idx][week_in_block]

        # Calculate prescribed weight
        prescribed_weight = current_1rm * percentage

        # Get sets for this week
        sets = get_sets_for_week(week)

        # Check if this is an AMRAP week
        is_amrap_week = week in amrap_weeks

        # Store weekly prescription
        training_plan[week] = {
            'prescribed_weight': prescribed_weight,
            'percentage': percentage,
            'current_1rm': current_1rm,
            'sets': sets,
            'is_amrap_week': is_amrap_week
        }

        # Update 1RM based on AMRAP results from this week (applied to next week)
        if week in amrap_results:
            amrap_data = amrap_results[week]

            # Validate AMRAP data format
            required_keys = {'weight', 'actual_reps'}
            if not required_keys.issubset(amrap_data.keys()):
                raise ValueError(f"AMRAP data for week {week} must contain 'weight' and 'actual_reps'")

            # Extract AMRAP parameters
            weight = amrap_data['weight']
            actual_reps = amrap_data['actual_reps']
            tut_per_rep = amrap_data.get('tut_per_rep', 6.0)
            normal_tempo = amrap_data.get('normal_tempo', 3.0)

            # Calculate new 1RM from AMRAP performance
            new_1rm = estimate_1rm_from_amrap(
                weight=weight,
                actual_reps=actual_reps,
                tut_per_rep=tut_per_rep,
                normal_tempo=normal_tempo
            )

            # Update current 1RM for subsequent weeks
            current_1rm = new_1rm

    return training_plan
