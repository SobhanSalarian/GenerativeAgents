"""
run_persona_panels_43.py — Persona panel robustness, seed 43 only.

Resume-safe: experiment_runner skips trials where a manifest already exists,
so any completed trials from a previous run are preserved.

Usage:
    cd reverie/backend_server
    OPENAI_API_KEY=sk-... python run_persona_panels_43.py
"""

from scenarios.commons_dilemma import CommonsDilemma
from experiment_runner import run_experiment_matrix

print("\n=== Running persona panel seed=43 ===")
run_experiment_matrix(
    fork_sim_code="base_the_ville_n25",
    sim_code_prefix="cd_panel_seed43",
    scenario=CommonsDilemma(),
    experimental_conditions=["baseline", "full"],
    n_steps=100,
    n_trials=5,
    output_dir="experiment_results_cd_panel_seed43",
    persona_sample_size=8,
    selection_seed=43,
    base_seed=20260524,
    export_human_eval=False,
    run_hypothesis_analysis=False,
)
