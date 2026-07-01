"""
run_ic_noflag_332.py — No-flag memory + 3:3:2 signal distribution (Comment #5).

Tests whether memory agents genuinely aggregate distributed information or
whether the prior 4:2:2 design made the correct answer trivially visible
through the public tally (A:4, B:2, C:2 after step 0 = obvious plurality).

Design
------
Signal distribution changed to 3:3:2 (A:3, B:3, C:2).  After step 0 the
public tally shows A:3, B:3, C:2 — a dead tie between A and B.  Agents
must track how the tally evolves across rounds and weight shared evidence
to identify A as the correct option.

The "(majority-signal option)" label has also been removed from memory
strings (applied globally to information_consensus.py) so memory only
provides temporal anchoring through raw tally history, not a direct hint
about which option is correct.

Two conditions:
  - baseline  : no memory — expected to fail (cascade or no convergence)
  - memory    : memory only — key test: does memory still enable correct
                aggregation when the answer is not obvious from the tally?

5 trials × 2 conditions × 30 steps = 10 trials total.

Requires: OPENAI_API_KEY

Usage:
    cd reverie/backend_server
    OPENAI_API_KEY=sk-... python run_ic_noflag_332.py
"""

from scenarios.information_consensus import InformationConsensus
from experiment_runner import run_experiment_matrix

run_experiment_matrix(
    fork_sim_code="base_the_ville_n25",
    sim_code_prefix="ic_noflag_332",
    scenario=InformationConsensus(
        true_option="A",
        signal_counts={"A": 3, "B": 3, "C": 2},
    ),
    experimental_conditions=["baseline", "memory"],
    n_steps=30,
    n_trials=5,
    output_dir="experiment_results_ic_noflag_332",
    persona_sample_size=8,
    selection_seed=42,
    base_seed=20260630,
    export_human_eval=False,
    run_hypothesis_analysis=False,
)
