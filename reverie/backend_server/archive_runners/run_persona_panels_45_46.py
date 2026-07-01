"""
run_persona_panels_45_46.py — Persona panel robustness, seeds 45–46 only.

Usage:
    cd reverie/backend_server
    OPENAI_API_KEY=sk-... python run_persona_panels_45_46.py
"""

from scenarios.commons_dilemma import CommonsDilemma
from experiment_runner import run_experiment_matrix

PANEL_SEEDS = [45, 46]

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
