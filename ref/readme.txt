```markdown
# Functional Training Program - Scope of Work (Version 1)

## Project Goal
Create a Python-based progressive overload training program inspired by Layne Norton's PH3, adapted for functional training with time-under-tension (TUT) as the primary metric for autoregulation.

## Key Requirements
- 13-week program structure (3 blocks + test week)
- Track 3 main lifts: Squat, Bench Press, Pull-ups/Deadhangs
- 4-5 training days per week
- Weekly adjustments based on AMRAP performance
- TUT-based progression (4-0-2-0 tempo = 6s per rep)
- Target: 40-70 seconds total TUT per set for hypertrophy

## Block Structure
- **Block 1 (Weeks 1-4)**: Strength foundation - percentages [70%, 75%, 80%, 72.5%]
- **Block 2 (Weeks 5-8)**: Hypertrophy focus - percentages [77.5%, 82.5%, 85%, 77.5%]
- **Block 3 (Weeks 9-13)**: Peaking/intensity - percentages [80%, 85%, 87.5%, 90%, 65%]
  - Week 13 is integrated deload at 65%

## AMRAP Weeks & 1RM Progression
- Weeks 2-4, 6-8, 10-12 include AMRAP sets (3 consecutive weeks per block)
- AMRAP is performed at the prescribed percentage of current 1RM for that week
- New 1RM is calculated weekly from AMRAP performance but NOT immediately used
- Instead, percentages are applied to the updated 1RM for prescription
- If a week is failed (unable to complete AMRAP), repeat that week until successful
- Uses effective reps calculation to account for TUT
- PH3 methodology: Accumulate fatigue across 3 AMRAP weeks, then recovery week

## Set/Rep Scheme
- **Progressive volume**: Start at 3 sets, increase by 1 set every 5 weeks (Blocks 2 and 3)
  - Block 1 (Weeks 1-4): 3 sets
  - Block 2 (Weeks 5-8): 4 sets
  - Block 3 (Weeks 9-13): 5 sets
- **Target rep ranges**:
  - Main lifts (Squat, Bench): 9-12 reps per set
  - Pull-ups: 10-15 reps per set
- **Lift selection**: Squat, Bench Press, Pull-ups (bodyweight + added weight)

## Artifacts to Create

### 1. `estimate_1rm_from_amrap()`
**Purpose**: Calculate estimated 1RM from AMRAP performance with TUT adjustment
**Inputs**:
- weight (float): weight lifted during AMRAP
- actual_reps (int): reps completed
- tut_per_rep (float): seconds per rep (default 6)
- normal_tempo (float): baseline tempo (default 3)
**Output**: Estimated 1RM (float)
**Notes**: V2 will add validation flag for unrealistic estimates
**Status**: ✅ Complete

### 2. `build_training_plan()`
**Purpose**: Generate 13-week training plan with progressive overload
**Inputs**:
- start_1rm (float): initial 1RM for the lift
- block_percentages (list of lists): percentages for each block
- amrap_results (dict, optional): actual AMRAP performance data
**Output**: Dictionary mapping week number to prescribed weight
**Status**: 🚧 In progress

### 3. `track_weekly_performance()`
**Purpose**: Record weekly training data
**Inputs**:
- week (int)
- lift_name (str)
- weight, reps, total_tut, rpe
**Output**: Updated performance DataFrame
**Status**: ⏳ Not started

### 4. `suggest_next_week_workout()`
**Purpose**: Generate specific workout prescription based on current plan
**Inputs**:
- current_week (int)
- lift_name (str)
- training_plan (dict)
**Output**: Workout details (sets, reps, weight, rest periods)
**Status**: ⏳ Not started

### 5. Performance tracking data structure
**Purpose**: Store all training data for analysis
**Format**: pandas DataFrame or CSV
**Columns**: week, block, lift, weight, reps, total_tut, rpe, estimated_1rm
**Status**: ⏳ Not started

### 6. `calculate_effective_reps()` (Helper Function)
**Purpose**: Convert actual reps to effective reps based on TUT adjustment
**Inputs**:
- actual_reps (int): reps completed
- tut_per_rep (float): seconds per rep (default 6)
- normal_tempo (float): baseline tempo (default 3)
**Output**: Effective reps (float)
**Status**: ⏳ Not started

### 7. `validate_volume()` (Helper Function)
**Purpose**: Validate that prescribed volume is appropriate and safe
**Inputs**:
- sets (int): number of sets
- reps (int): target reps per set
- weight (float): prescribed weight
- lift_name (str): name of the lift
**Output**: Boolean (valid) + warning message if applicable
**Status**: ⏳ Not started

## Out of Scope (Version 1)
- User interface / web app
- Exercise library beyond 3 main lifts
- Accessory work programming
- Mobile app
- Data visualization
- Export to Excel (can add in V2)

## Design Decisions (V1)
- **Block percentages**:
  - Block 1: [0.7, 0.75, 0.8, 0.725]
  - Block 2: [0.775, 0.825, 0.85, 0.775]
  - Block 3: [0.8, 0.85, 0.875, 0.9, 0.65]
- **AMRAP testing**: 3 consecutive weeks per block (PH3 methodology)
- **1RM updates**: Calculated weekly, percentages applied to updated 1RM
- **Failed weeks**: Repeat until AMRAP is successfully completed
- **Volume progression**: +1 set every 5 weeks (3→4→5 sets)
- **TUT calculation**: Tempo 4-0-2-0 = 6s/rep (4s eccentric, 2s concentric)
- **Main lifts**: Squat, Bench Press, Pull-ups only

## Success Criteria
- Program generates 13-week plan for all 3 lifts
- AMRAP results correctly update 1RM weekly with percentage-based prescription
- Can input weekly performance and get next week's prescription
- All calculations use TUT-adjusted effective reps
- Volume increases appropriately across blocks (3→4→5 sets)
- Unit tests validate 1RM estimation with known values
- Edge case handling (0 reps, extremely high reps)
```