# `analysis/` — reproducible analysis scripts (WISE 2026 paper)

All analysis / reanalysis scripts live here. Runners that *generate* data stay in
`backend_server/` (`run_*.py`); the sim engine (`reverie.py`, `maze.py`, …) is
untouched. Every script is CWD-independent: it imports `_paths` (which puts
`backend_server/` on `sys.path` and resolves result folders there), so you can run
it from anywhere:

```bash
cd reverie/backend_server
python analysis/<script>.py
```

## Canonical script → paper number

| Paper location | Script | Reproduces |
|---|---|---|
| §5.1 headline association | `../experiment_analysis.py` | Spearman ρ = 0.55 (CD), condition means, OLS β = 0.45 |
| §5.1 persona robustness | `reanalysis_persona_clustered_bootstrap.py` | persona-clustered CIs (CD [0.45,0.52], IC [0.75,0.75]) |
| §5.4 C4 reflection repetition | *(in `experiment_analysis.py` / logs)* | 47,040 instances, 3 unique strings, 70.2% dominant |
| §5.4 C5 norm fraction | `reanalysis_c5_norm_fraction.py` | 1,190 unique, 94.9% norm-restating |
| §5.4 C4 vs C5 side-by-side | `compare_reflection_conditions.py` | deterministic vs LLM reflection |
| §5.5 early warning | `analyse_early_warning.py` | **canonical, seed-averaged** (see below) |
| §3.3 / §6 human pilot | `analyse_human_eval_full.py` | α per dim, sanity-check ρ, gap-case certification |

## Reviewer-comment experiments (Amin comments 2–7)

| Comment | Script | Result it reports |
|---|---|---|
| 2 & 3 — placebo reflection | `analyse_p1_placebo.py` | injection 80% vs placebo 60%, **not separable** (MWU p=0.116) |
| 4 — IC counterbalancing | `analyse_ic_counterbalance.py` | baseline fails only when correct = first option (position confound) |
| 5 — no-flag memory | `analyse_ic_noflag.py` | baseline 0%, memory 80% without the flag (genuine aggregation) |
| 7 — persona panels | `analyse_persona_panels.py` | 5 panels + mixed-effects (is_full β=+0.75, ICC≈0) |

## Two resolved number conflicts (best-practice canonical choices)

**Convergent validity (pilot).** Report as a **pilot sanity check, not convergent
validity** (comment 6: no dimension passes the α≥0.67 gate; two are negative).
Canonical number, verified against the raw pilot data: **ρ = 0.82, n = 15**, human
composite vs the **stored LLM-judged composite** — the exact B the paper reports
everywhere else. Per-dimension the agreement is carried almost entirely by planning
(ρ = 0.79); consistency (0.18) and naturalness (0.38) are weak, memory (0.35) middling.

*Correction:* an earlier "ρ = 0.73" was a **bug**, not a real method difference.
`analyse_human_eval_full.py` located trials with `glob("experiment_results_*/*/{cond}/…")`,
which — after the reviewer-comment experiments were added — matches 12 directories and
silently pulled the wrong trial. Fixed with an explicit condition→dir map; the script
now reads the stored micro_summary.json (real instrument, no API) and reproduces 0.82.

**Early-warning classifier (§5.5).** Single-seed AUCs were unstable (0.79/0.77/0.51 at
80 trees/seed 0; 0.82/0.79/0.58 at 200 trees/seed 42). `analyse_early_warning.py`
removes seed cherry-picking by **averaging over 25 RF seeds** (200 trees). Canonical
within-full, K = 20: **combined 0.80, macro-only 0.79, micro-only 0.54**
(seed-range ±0.02–0.03). The run-independent conclusion is unchanged: macro-state
features carry the signal; the micro-only (believability-trace) model is near chance.

## `archive/`
Superseded / duplicate scripts kept for provenance only:
`reanalysis_classifier_battery.py` (→ `analyse_early_warning.py`),
`reanalysis_convergent_validity.py` and `reanalysis_human_pilot_breakout.py`
(→ `analyse_human_eval_full.py`).
The six one-off `run_persona_panels_*.py` variants are in `../archive_runners/`
(→ use `../run_persona_panels.py`, which loops seeds 43–46).
