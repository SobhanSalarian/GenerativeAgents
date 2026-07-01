from scenarios.information_consensus import InformationConsensus
from scenarios.commons_dilemma import CommonsDilemma
from experiment_runner import run_experiment_matrix

# --- IC v3 full_llm_reflection ---
run_experiment_matrix(
    fork_sim_code="base_the_ville_n25",
    sim_code_prefix="ic_experiment_llm_reflection",
    scenario=InformationConsensus(),
    experimental_conditions=["full_llm_reflection"],
    n_steps=30,
    n_trials=10,
    output_dir="experiment_results_ic_llm_reflection",
    persona_sample_size=8,
    selection_seed=42,
    base_seed=20260524,
    export_human_eval=True,
    run_hypothesis_analysis=False,
)

# --- CD full_llm_reflection v2 ---
run_experiment_matrix(
    fork_sim_code="base_the_ville_n25",
    sim_code_prefix="cd_experiment_llm_reflection",
    scenario=CommonsDilemma(),
    experimental_conditions=["full_llm_reflection"],
    n_steps=100,
    n_trials=10,
    output_dir="experiment_results_cd_llm_reflection",
    persona_sample_size=8,
    selection_seed=42,
    base_seed=20260524,
    export_human_eval=True,
    run_hypothesis_analysis=False,
)
