"""
run_ic_counterbalance.py — IC counterbalancing experiment (Comment #4).

Tests whether the baseline cascade failure and memory-enabled success in the
information consensus scenario depend on label salience (Option A being
inherently appealing) or reflect genuine social-information dynamics.

Design
------
Three rotations of the correct option (A, B, C), each run with two conditions:
  - baseline       : no memory, no planning, no reflection
  - full           : memory + planning + deterministic reflection

If cascade failure and correct convergence occur regardless of which option
holds the majority signal, label salience is ruled out as a confound.

5 trials × 2 conditions × 3 rotations = 30 trials total.
30 steps per trial (IC converges quickly for memory+ conditions).

Requires: OPENAI_API_KEY

Usage:
    cd reverie/backend_server
    OPENAI_API_KEY=sk-... python run_ic_counterbalance.py
"""

from scenarios.information_consensus import InformationConsensus
from experiment_runner import run_experiment_matrix

ROTATIONS = [
    # (true_option, signal_counts, output_suffix)
    ("A", {"A": 4, "B": 2, "C": 2}, "correct_A"),
    ("B", {"B": 4, "A": 2, "C": 2}, "correct_B"),
    ("C", {"C": 4, "A": 2, "B": 2}, "correct_C"),
]

for true_option, signal_counts, suffix in ROTATIONS:
    print(f"\n=== Running rotation: correct={true_option} ===")
    run_experiment_matrix(
        fork_sim_code="base_the_ville_n25",
        sim_code_prefix=f"ic_counterbalance_{suffix}",
        scenario=InformationConsensus(
            true_option=true_option,
            signal_counts=signal_counts,
        ),
        experimental_conditions=["baseline", "full"],
        n_steps=30,
        n_trials=5,
        output_dir=f"experiment_results_ic_counterbalance_{suffix}",
        persona_sample_size=8,
        selection_seed=42,
        base_seed=20260630,
        export_human_eval=False,
        run_hypothesis_analysis=False,
    )
