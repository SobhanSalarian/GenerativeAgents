"""
run_persona_panels_44_46.py — Persona panel robustness, seeds 44–46 only.

Companion to run_persona_panels.py. Run this in a separate terminal with a
different API key while run_persona_panels.py handles seed 43, to parallelise
the most time-consuming part of the panel robustness check.

Seeds 44, 45, 46 × 2 conditions (baseline + full) × 5 trials × 100 steps
= 30 trials total.

Usage:
    cd reverie/backend_server
    OPENAI_API_KEY=sk-... python run_persona_panels_44_46.py
"""

from scenarios.commons_dilemma import CommonsDilemma
from experiment_runner import run_experiment_matrix

PANEL_SEEDS = [44, 45, 46]

for seed in PANEL_SEEDS:
    print(f"\n=== Running persona panel seed={seed} ===")
    run_experiment_matrix(
        fork_sim_code="base_the_ville_n25",
        sim_code_prefix=f"cd_panel_seed{seed}",
        scenario=CommonsDilemma(),
        experimental_conditions=["baseline", "full"],
        n_steps=100,
        n_trials=5,
        output_dir=f"experiment_results_cd_panel_seed{seed}",
        persona_sample_size=8,
        selection_seed=seed,
        base_seed=20260524,
        export_human_eval=False,
        run_hypothesis_analysis=False,
    )
