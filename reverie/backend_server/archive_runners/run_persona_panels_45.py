"""
run_persona_panels_45.py — Persona panel robustness, seed 45 only.

Usage:
    cd reverie/backend_server
    OPENAI_API_KEY=sk-... python run_persona_panels_45.py
"""

from scenarios.commons_dilemma import CommonsDilemma
from experiment_runner import run_experiment_matrix

print("\n=== Running persona panel seed=45 ===")
run_experiment_matrix(
    fork_sim_code="base_the_ville_n25",
    sim_code_prefix="cd_panel_seed45",
    scenario=CommonsDilemma(),
    experimental_conditions=["baseline", "full"],
    n_steps=100,
    n_trials=5,
    output_dir="experiment_results_cd_panel_seed45",
    persona_sample_size=8,
    selection_seed=45,
    base_seed=20260524,
    export_human_eval=False,
    run_hypothesis_analysis=False,
)
