"""
run_p1.py — P1 confirmatory experiment: static reflection injection vs. placebo.

Tests whether the C3→C4 coordination gain (10%→70% in the commons dilemma) is
driven by the *content* of the dominant reflection string or by the *process* of
generating it.

Three arms (CD only; IC has zero condition variance and is not informative here):
  - static_reflection_injection : memory + planning + top saturation string verbatim
  - static_reflection_placebo   : same architecture + matched string with no coordination content
  - memory_planning             : within-experiment baseline (same base_seed) for clean comparison

Including memory_planning as a third arm allows all comparisons to be made
within a single experiment (same base_seed=20260610, same personas), avoiding
cross-dataset comparison artefacts.

Expected result if content account holds (H6 confirmed):
  injection  coordination ≈ full condition (70%)
  placebo    coordination ≈ memory_planning (10%)
  injection  vs placebo   : statistically separable

Requires: OPENAI_API_KEY (for GPT-4o-mini agent decisions).
No Anthropic key needed — reflection is injected statically, no LLM call.

Usage:
    cd reverie/backend_server
    OPENAI_API_KEY=sk-... python run_p1.py
"""

from scenarios.commons_dilemma import CommonsDilemma
from experiment_runner import run_experiment_matrix

run_experiment_matrix(
    fork_sim_code="base_the_ville_n25",
    sim_code_prefix="cd_experiment_p1",
    scenario=CommonsDilemma(),
    experimental_conditions=[
        "static_reflection_injection",
        "static_reflection_placebo",
        "memory_planning",
    ],
    n_steps=100,
    n_trials=10,
    output_dir="experiment_results_cd_p1",
    persona_sample_size=8,
    selection_seed=42,
    base_seed=20260610,
    export_human_eval=True,
    run_hypothesis_analysis=False,
)
