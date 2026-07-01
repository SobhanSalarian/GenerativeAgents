"""
run_persona_panels_44.py — Persona panel robustness, seed 44 only.

Usage:
    cd reverie/backend_server
    OPENAI_API_KEY=sk-... python run_persona_panels_44.py
"""

from scenarios.commons_dilemma import CommonsDilemma
from experiment_runner import run_experiment_matrix

print("\n=== Running persona panel seed=44 ===")
run_experiment_matrix(
    fork_sim_code="base_the_ville_n25",
    sim_code_prefix="cd_panel_seed44",
    scenario=CommonsDilemma(),
    experimental_conditions=["baseline", "full"],
    n_steps=100,
    n_trials=5,
    output_dir="experiment_results_cd_panel_seed44",
    persona_sample_size=8,
    selection_seed=44,
    base_seed=20260524,
    export_human_eval=False,
    run_hypothesis_analysis=False,
)
