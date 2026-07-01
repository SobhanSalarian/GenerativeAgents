# Human Evaluation — Pipeline and Reproduction

This document describes the human-evaluation pipeline for the believability
instrument (WISE 2026 paper, §3.1). It covers the data layout, how packets are
generated, how raters score them, and how the reported numbers are computed.

## Design (Option 2)

- **Primary study:** a balanced 120-packet set — 24 packets per condition
  (8 per phase: early / middle / late) across the five conditions
  (`baseline`, `memory`, `memory_planning`, `full`, `full_llm_reflection`),
  drawn from `trial_1` of each condition. Rated by three blinded raters (R1–R3).
- **Pilot (reported separately):** the original 15-packet set (1 per
  condition × phase, from `trial_0`), rated by the same three raters. This is
  the initial calibration round, reported alongside but not pooled with the
  primary study.
- The two sets are drawn from **different trials** (trial_0 vs trial_1), so no
  packet is rated twice.

## Files

Generation
- `create_pilot_subset.py`   — builds the 15-packet pilot (trial_0). Output: `pilot_packets/`.
- `create_full_eval_set.py`  — builds the 120-packet primary set (trial_1), excluding
  any pilot-rated packet id. Output: `full_eval_packets/`. Seeded (SEED=4242).

Rating interface
- `human_eval_ui.py` — Streamlit app. Raters select their code (R1–R5), load a
  packet file, and score four 1–5 rubric dimensions plus a believable yes/no
  verdict. Ratings are written next to the packet file as `human_eval_ratings.csv`.

Data layout
```
pilot_packets/
  pilot_human_eval_packets.jsonl   # 15 blinded packets
  pilot_blind_key.json             # packet_id -> condition/trial/persona (analysis only)
  human_eval_ratings.csv           # 15 packets x 3 raters = 45 rows  (DO NOT overwrite)
full_eval_packets/
  full_human_eval_packets.jsonl    # 120 blinded packets
  full_blind_key.json              # unblinding key (analysis only)
  human_eval_ratings.csv           # written by the UI as raters submit (120 x 3 target)
```

Ratings CSV columns: `packet_id, blinded_agent_id, scenario, trial, step, phase,
rater_id, behavioural_consistency, memory_coherence, planning_plausibility,
response_naturalness, believable_yes_no, notes`.

## Rubric anchors (1–5)

| Dimension | 1 (low) | 5 (high) |
|---|---|---|
| Behavioural consistency | Contradicts persona | Fully consistent |
| Memory coherence | Ignores / misuses memory | Uses it well |
| Planning plausibility | No connection to decision | Clear logical connection |
| Response naturalness | Clearly robotic / templated | Natural |

`believable_yes_no` is the rater's overall verdict for the packet.

Rater instruction (important): **use the whole 1–5 scale.** In the pilot, most
ratings clustered at 4–5, which depressed inter-rater Krippendorff's alpha through
restricted variance rather than genuine disagreement.

## Running data collection

```
cd reverie/backend_server
streamlit run human_eval_ui.py
```
In the sidebar, each rater: (1) selects their code, (2) enters the packet path
`full_eval_packets/full_human_eval_packets.jsonl`, (3) loads and rates. The app
resumes each rater at their first unrated packet and appends to
`full_eval_packets/human_eval_ratings.csv`.

## Analysis (aligned with reviewer comment 2)

```
cd reverie/backend_server
python analysis/analyse_human_eval_full.py          # alpha, per-dim agreement, composite, gap-case
python analysis/analyse_human_eval_full.py --llm     # recompute sub-scores via the LLM judge (API key)
```
Reports, for the primary study (and the pilot separately):
1. inter-rater reliability — per-dimension Krippendorff's alpha (ordinal);
2. per-dimension mean / SD (restricted-variance diagnostic);
3. per-dimension human-vs-automated agreement (Spearman) + overall composite;
4. blending gate — dimensions passing alpha >= 0.67;
5. gap-case certification — believable verdicts on the 0%-success baseline packets.

By default the automated sub-scores are read from the **stored** `micro_summary.json`
(the actual LLM-judged instrument output computed at experiment time — no API needed,
fully reproducible). `--llm` recomputes them from the full `micro_log` via
`measurement/micro.py`. The trial for each packet is resolved with an explicit
condition->directory map (NOT a `experiment_results_*` wildcard — see below).

## Pilot convergent-validity — report as a PILOT SANITY CHECK (comment 6)

Canonical script: `analysis/analyse_human_eval_full.py`. Verified against the raw
pilot data, the overall agreement is **rho = 0.82, n = 15** (human composite vs the
stored LLM-judged composite — the exact B the paper reports elsewhere), carried almost
entirely by planning (rho = 0.79); consistency (0.18), memory (0.35), naturalness
(0.38) are weak. Because no dimension passes the alpha >= 0.67 gate (two are negative),
this is reported as a **pilot sanity check, not convergent validity.**

Correction: an earlier "rho = 0.73" was a BUG — the trial locator globbed
`experiment_results_*/*/{cond}/...`, which now matches 12 directories (panel seeds,
counterbalance, no-flag, IC) and pulled the wrong trial. Fixed with the explicit
condition->dir map. The archived `analysis/archive/reanalysis_convergent_validity.py`
(stored-composite, n=12/15) is retained for provenance only.

## Other analysis scripts (see `analysis/README.md` for the full map)

- `analysis/reanalysis_persona_clustered_bootstrap.py` — comment 7 (persona-clustered CIs).
- `analysis/analyse_persona_panels.py` — comment 7 (5 panel seeds + mixed-effects model).
- `analysis/analyse_early_warning.py` — comment 8 (seed-averaged micro/macro/combined AUCs).
- `analysis/analyse_p1_placebo.py` — comments 2 & 3 (reflection injection vs placebo).
- `analysis/analyse_ic_counterbalance.py` — comment 4 (IC option/position counterbalancing).
- `analysis/analyse_ic_noflag.py` — comment 5 (no-flag memory / aggregation-scaffold test).
- Archived (superseded): `analysis/archive/reanalysis_classifier_battery.py`,
  `reanalysis_convergent_validity.py`, `reanalysis_human_pilot_breakout.py`.
