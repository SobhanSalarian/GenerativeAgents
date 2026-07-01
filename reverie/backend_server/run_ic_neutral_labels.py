"""
run_ic_neutral_labels.py — IC neutral labels experiment (Comment #4 extension)

Purpose
-------
The IC counterbalancing experiment (run_ic_counterbalance.py) revealed a strong
label-salience effect: baseline agents succeed 5/5 when the correct option is B
or C, but only 1/5 when it is A.  This script tests whether that failure is due
to the alphabetical letter "A" (LLM prior), its display position, or the
semantic content of the description.

Design
------
  - Uses InformationConsensusNeutral, which shows options as X / Y / Z with
    neutral descriptions ("Community development proposal X/Y/Z").
  - Three rotations: the MAJORITY option is internally A (→ X), B (→ Y), or C
    (→ Z).  The display labels are always X/Y/Z in sorted order.
  - If baseline still fails when the majority option displays as "X", the cause
    was not just the letter "A" but something deeper (positional bias or the
    semantic content of the A description).
  - If baseline now SUCCEEDS when the majority option is "X", label salience
    (alphabetical bias) was the driver.

Conditions: baseline + full
Trials per cell: 5
Steps per trial: 30
Total trials: 3 rotations × 2 conditions × 5 trials = 30

Signal distribution: majority 4, minority 2+2 (same as run_ic_counterbalance.py)

Usage
-----
    cd reverie/backend_server
    OPENAI_API_KEY=sk-... python run_ic_neutral_labels.py
"""

from scenarios.information_consensus_neutral import InformationConsensusNeutral
from experiment_runner import run_experiment_matrix

# Each rotation: (true_option, signal_counts, label_suffix)
# true_option is the internal key; it will be displayed as X/Y/Z by the subclass.
ROTATIONS = [
    ("A", {"A": 4, "B": 2, "C": 2}, "correct_A_as_X"),   # correct shown as X
    ("B", {"B": 4, "A": 2, "C": 2}, "correct_B_as_Y"),   # correct shown as Y
    ("C", {"C": 4, "A": 2, "B": 2}, "correct_C_as_Z"),   # correct shown as Z
]

for true_option, signal_counts, label_suffix in ROTATIONS:
    print(f"\n=== IC neutral labels — {label_suffix} ===")
    scenario = InformationConsensusNeutral(
        true_option=true_option,
        signal_counts=signal_counts,
    )
    run_experiment_matrix(
        fork_sim_code="base_the_ville_n25",
        sim_code_prefix=f"ic_neutral_{label_suffix}",
        scenario=scenario,
        experimental_conditions=["baseline", "full"],
        n_steps=30,
        n_trials=5,
        output_dir=f"experiment_results_ic_neutral_{label_suffix}",
        persona_sample_size=8,
        selection_seed=42,
        base_seed=20260630,
        export_human_eval=False,
        run_hypothesis_analysis=False,
    )
    print(f"    Done: {label_suffix}")

print("\n=== All IC neutral label rotations complete ===")
