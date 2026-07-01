# Analysis Notes — Reproducing the Paper's Numbers

This documents how the reported figures map to the analysis code, including two
points that previously caused apparent mismatches (both now reconciled).

## Main results pipeline

```
cd reverie/backend_server
python experiment_analysis.py experiment_results_cd_primary --scenario commons_dilemma
```
Outputs to `experiment_results_cd_primary/commons_dilemma/analysis/`:
`hypothesis_report.json`, `hypothesis_report.txt`, `feature_table.csv`.

Reproduces:
- Headline association: Spearman rho = 0.549 (-> paper 0.55), n = 80.
- Condition believability means: baseline 0.347, memory 0.543, memory+planning
  0.669, full 0.682 (Table 2).
- Monotonic increase across conditions; C3->C4 pairwise p = 0.0015.
- Sub-dimension correlations (memory 0.544, planning 0.501, consistency 0.248,
  naturalness -0.109) and the OLS predictor model.

## Point 1 — OLS coefficient is the STANDARDISED beta (paper: 0.45)

The paper reports a **standardised** regression coefficient for planning
plausibility (beta = 0.45). `_ols_regression` now returns both:
- `coefficient`              — raw (unstandardised) OLS coefficient (planning = 0.645);
- `standardized_coefficient` — z-scored predictors and outcome (planning = 0.449 -> 0.45).

The paper's 0.45 = the standardised value. Verified: standardising the four
sub-dimensions and the outcome over the 80 CD primary trials gives planning
beta = 0.449. Use `standardized_coefficient` when checking against the paper.

## Point 2 — Gap-case count is threshold-sensitive at the baseline cluster

The paper reports ~41 CD gap cases at Delta > 0.20, within a sensitivity range
(30-59 across V-weightings; 56/41/37 across Delta > 0.15/0.20/0.25; bootstrap
CI [32,50]). The pipeline's point count at Delta > 0.20 is 54. The difference is
entirely in the **baseline** condition:

- Enriched conditions are robust and reproduce exactly: memory 18 +
  memory_planning 18 + full 3 = **39** gap cases (their Delta is far from the cut).
- All 20 **baseline** trials sit in a razor-thin band Delta = 0.191-0.223,
  straddling the 0.20 cutoff, so the baseline count swings from ~2 to ~15 with
  tiny differences in how composite believability is computed/rounded.

This is the "presence artifact" the paper discusses: baseline believability is
mechanically depressed (structural zeros for memory/planning), so its trials
pile up at the threshold. The headline count is therefore reported as a range,
not a hard point estimate; the **robust core is the 39 enriched-condition gap
cases**. Both 41 (paper) and 54 (pipeline default) fall inside the stated range.

## Convergent validity (human eval) — RESOLVED: report as pilot sanity check

Canonical script: `analysis/analyse_human_eval_full.py` (recompute-from-source).
Per Amin comment 6 this is a **pilot sanity check, NOT convergent validity**: no
dimension passes the alpha>=0.67 gate and two are negative (consistency -0.33,
naturalness -0.31; memory +0.52, planning +0.42).

Canonical (verified against raw pilot data): **rho = 0.82, n = 15**, human composite
vs the STORED LLM-judged composite (the exact B the paper reports elsewhere).
Per-dimension, agreement is carried almost entirely by planning (rho = 0.79);
consistency (0.18), memory (0.35), naturalness (0.38) are weak.

CORRECTION: an earlier "rho = 0.73" was a BUG, not a method difference. The trial
locator globbed `experiment_results_*/*/{cond}/...`, which now matches 12 dirs (panel
seeds, counterbalance, no-flag, IC) and pulled the wrong trial. Fixed with an explicit
condition->dir map in `analysis/analyse_human_eval_full.py` (reads stored
micro_summary.json; reproduces 0.82). Gap-case certification:
raters certify all three 0%-success baseline packets as believable (3/3 by majority)
— direct human evidence for the believability-reliability gap. Superseded scripts
moved to `analysis/archive/` (reanalysis_convergent_validity.py,
reanalysis_human_pilot_breakout.py).

## Point 3 — C5 "94.9% restate the fair-share norm" (§5.4)

The C5 (LLM-generated reflection) figure is a *semantic* measure, not exact-string
dedup: free reflections paraphrase the same fair-share norm, so exact dedup gives
1,190 unique strings while the repetition is in the meaning. An instance is counted
as norm-restating if its text contains any fair-share-norm keyword
('fair', 'replenish', 'sustainab').

Reproduced by `reanalysis_c5_norm_fraction.py`:
- unique strings (exact)     = 1,190   (matches paper)
- norm-restating share       = 94.9%   (matches paper)

The deterministic C4 figures (47,040 instances, 3 unique strings, top-2 = 95.8%,
dominant = 70.2%) are exact-string and reproduce directly from the C4 micro logs.

## Point 4 — Early-warning classifier (§5.5) — RESOLVED: seed-averaged canonical

Canonical script: `analysis/analyse_early_warning.py` (feature extraction + failure
taxonomy reused from `early_warning.py`; the old `ew_fast.py` and
`reanalysis_classifier_battery.py` are superseded — battery archived).

Single-seed AUCs were unstable and cherry-pickable (0.79/0.77/0.51 at 80 trees/seed 0;
0.82/0.79/0.58 at 200 trees/seed 42). The canonical script removes this by **averaging
LOO ROC-AUC over 25 RF seeds** (n_estimators=200).

Seed-averaged, within full condition, K = 20 (n=20, 6 failures):
- combined   AUC = 0.80   (seed-range ~[0.78, 0.83])
- macro-only AUC = 0.79   (seed-range ~[0.77, 0.81])
- micro-only AUC = 0.54   (seed-range ~[0.52, 0.58])

Report the within-condition trio as **0.80 / 0.79 / 0.54** (seed-averaged). Pooled
figures (~0.84 at K=5, ~0.94 at K=20) are condition-confounded and are NOT headlined
(Amin comment 8). Run-independent conclusion unchanged: macro-state features carry the
within-condition signal; the micro-only (believability-trace) model is near chance.

Failure taxonomy (deterministic, via build_failure_taxonomy in early_warning.py):
63 failed CD trials -> 38 Type D (mean believability 0.459), 25 Type E (0.641). Exact.

## Point 5 — Reviewer-comment experiments (Amin comments 2-7)

Each experiment now has a dedicated analysis script under `analysis/` (see
`analysis/README.md`). Runners stay at top level (`run_*.py`).

- Comment 2 & 3 (placebo reflection): `analysis/analyse_p1_placebo.py`.
  injection 8/10 (coord 0.772) vs placebo 6/10 (coord 0.585); Mann-Whitney U=71,
  p=0.116, Cliff's delta=+0.42 -> NOT separable. A content-free placebo already lifts
  coordination far above C3's 10%, so the fair-share CONTENT is not the demonstrable
  driver; use the cautious "injects a shared coordination norm" wording.
- Comment 4 (IC counterbalancing): `analysis/analyse_ic_counterbalance.py`.
  Baseline fails only when the correct option is first-listed (A: 20%, X: 0%) and
  succeeds otherwise (B/C/Y: ~100%). Position/salience confound -> IC failure is
  cascade-like with an acknowledged salience confound, not pure lock-in.
- Comment 5 (no-flag memory, 3:3:2): `analysis/analyse_ic_noflag.py`.
  baseline 0/5, memory 4/5 (80%) with the flag removed and a tied tally -> supports
  genuine temporal aggregation (n=5/cell, supportive not definitive).
- Comment 7 (persona panels): `analysis/analyse_persona_panels.py`.
  5 panel seeds (42 primary + 43-46), baseline vs full. Mixed-effects
  coord ~ is_full + (1|panel): is_full beta=+0.75, p<1e-40, ICC~0. Baseline robustly
  0% across all panels; full high but variable (seed 43 only 20%).
