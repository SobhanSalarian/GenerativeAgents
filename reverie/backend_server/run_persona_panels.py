"""
run_persona_panels.py — Multiple persona-panel robustness check (Comment #7).

The primary CD dataset used a single persona panel (selection_seed=42, the
same 8 agents in every trial).  Bootstrapping within those 8 personas does
not create genuinely independent panels.  This script runs 4 additional
panel seeds to test whether the main findings (baseline fails, full succeeds)
hold across different persona compositions.

Design
------
4 additional selection seeds (43–46) × 2 conditions (baseline + full) × 5
trials × 100 steps = 40 trials total.  Baseline and full are the most
contrasting conditions and are sufficient to assess panel robustness.

Combined with seed=42 (20 trials each) this gives 5 panel seeds × 2
conditions for a mixed-effects robustness analysis.

Requires: OPENAI_API_KEY

Usage:
    cd reverie/backend_server
    OPENAI_API_KEY=sk-... python run_persona_panels.py
"""

from scenarios.commons_dilemma import CommonsDilemma
from experiment_runner import run_experiment_matrix

PANEL_SEEDS = [43, 44, 45, 46]

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
