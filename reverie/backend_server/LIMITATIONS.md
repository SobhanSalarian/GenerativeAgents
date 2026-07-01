# Limitations (detailed record)

Detailed limitations of the believability–reliability study, for the MRes thesis and
reviewer/defence preparation. Each item: what it is, why it matters, how the current
paper handles it, and the residual risk. Grouped by severity. Items marked "in WISE
§6" are already acknowledged in the conference paper's threats/limitations text.

---

## Tier 1 — Fundamental scope

### L1. No external validity / no real-world grounding
- **What:** V measures task success *within the simulation*, not correspondence to any
  real human system.
- **Why it matters:** caps the claim to "believable ≠ reliable in simulation"; cannot
  be read as a statement about real online communities.
- **Current handling:** explicit "no external-fidelity claim" (WISE §6, Construct).
- **Residual risk:** low for honesty, but limits impact; the strongest reviewer ask is
  to calibrate at least one task against real platform data.

### L2. Narrow empirical base: two synthetic tasks, one architecture, one model
- **What:** commons dilemma + information consensus; Park et al. generative-agent
  architecture; GPT-4o-mini only.
- **Why it matters:** generality (across tasks/architectures/models) is unestablished.
- **Current handling:** named as future work (WISE §6, Generality and drift).
- **Residual risk:** high — a reviewer may want at least one cross-model or cross-task
  replication before believing the effect generalises.

### L3. The believability instrument is itself not fully validated
- **What:** composite weights are hand-set (judgement, not optimised); human validation
  is a 15-packet, 3-rater pilot whose inter-rater Krippendorff's alpha fails the 0.67
  gate on two of four dimensions (consistency -0.33, naturalness -0.31; memory +0.52,
  planning +0.42). Pilot sanity-check agreement rho = 0.82 (n=15; human composite vs
  the stored LLM-judged composite, verified against raw data), carried almost entirely
  by planning (0.79); consistency/memory/naturalness are weak. Report as a pilot sanity
  check, NOT convergent validity (comment 6). [An earlier 0.78/0.73 figure was a
  stale-glob bug, now fixed; see ANALYSIS_NOTES.md.]
- **Why it matters:** B is a *proposed* measure; conclusions about B inherit its
  measurement uncertainty.
- **Current handling:** WISE §6 says "automated proxies pending complete multi-rater
  validation"; the pilot's small size and failed gate are reported in §3 but UNDERSTATED
  in §6. (Amin's comment 2 is exactly this.)
- **Residual risk:** high — the single most-pressed item. Mitigation = the full
  multi-rater study (120-packet set already generated; see HUMAN_EVAL_README.md).

---

## Tier 2 — Statistical / inferential

### L4. Persona non-independence (only 8 personas)
- **What:** all trials reuse one fixed 8-persona panel (selection seed 42).
- **Why it matters:** trials are not independent; effective n < nominal; p-values
  optimistic. A persona-clustered bootstrap with only 8 clusters is itself unstable.
- **Current handling:** WISE §6 (Persona dependence); persona-clustered bootstrap
  (association stays positive: CD CI [0.45,0.52], IC [0.75,0.75]). NOW ADDRESSED
  (comment 7): 4 additional independent panels (seeds 43-46) run on baseline+full;
  mixed-effects `coord ~ is_full + (1|panel)` gives is_full beta=+0.75, p<1e-40,
  ICC~0. Baseline robustly 0% across all 5 panels; full high but variable (seed 43 20%).
  Script: `analysis/analyse_persona_panels.py`.
- **Residual risk:** low-moderate — 5 panels + mixed-effects done; more panels (>=10)
  and cross-task panels would further strengthen it.

### L5. Small within-condition samples
- **What:** 20 trials/condition (CD), 10 (IC). Within-condition correlations and the
  within-condition early-warning AUC rest on very small n.
- **Why it matters:** low power; null within-condition results are inconclusive, not
  evidence of no effect.
- **Current handling:** WISE §6 (Confounding / Statistics): "nulls reflect low power."
- **Residual risk:** moderate; more trials per condition would resolve it.

### L6. Δ = B − V presumes scale comparability
- **What:** subtracting two differently-constructed [0,1] scores is not automatically
  meaningful.
- **Why it matters:** gap-case *counts* depend on a possibly non-comparable difference.
- **Current handling:** (B,V) plane treated as primary, Δ as convenience (§3.5). NOT in
  §6 threats.
- **Residual risk:** low — qualitative conclusion does not depend on Δ's exact scale.

### L7. The 0.20 gap threshold and the weights are conventions
- **What:** δ = 0.20 and the weights w, γ, ω are judgement-set, not calibrated.
- **Why it matters:** gap counts move with δ and ω (30–59 across weightings; 56/41/37
  across δ = 0.15/0.20/0.25); headline "41" is a point estimate in a range.
- **Current handling:** sensitivity reported (§3.5, §5.2); "a-priori weighting" noted
  in §6. Threshold-convention point not in §6.
- **Residual risk:** low — robustness range is reported.

---

## Tier 3 — Design confounds

### L8. Believability confounded with architecture by construction
- **What:** absent modules score 0, so the pooled B–V association is partly mechanical.
- **Why it matters:** the headline rho = 0.55 is presence-driven, not a clean
  believability effect (it falls to -0.24 under not-applicable scoring).
- **Current handling:** WISE §6 (Confounding); N/A reanalysis exposes it directly.
- **Residual risk:** low — this is reported as a finding, not hidden.

### L9. Cumulative conditions, not a clean ablation
- **What:** C1→C4 add modules cumulatively, so memory/planning/reflection effects are
  not separately identified.
- **Why it matters:** cannot attribute an outcome change to a single module.
- **Current handling:** stated in §3/§4 as "cumulative, not ablation"; NOT in §6.
- **Residual risk:** moderate — planning-only and reflection-control conditions are the
  fix (named as follow-up).

### L10. IC option-semantic / order confound
- **What:** fixed correct option and option set; 8/10 baseline trials converge on the
  same wrong option.
- **Why it matters:** convergence could reflect semantic preference or order bias rather
  than pure social-information lock-in.
- **Current handling:** WISE §6 (Task evidence). NOW RUN (comment 4) and it CONFIRMS the
  threat: counterbalancing the correct option (A/B/C) and neutral labels (X/Y) shows
  baseline fails ONLY when the correct option is first-listed (A: 20%, X: 0%) and
  succeeds otherwise (B/C/Y: ~100%). This is an option-POSITION effect; the unanimous-
  wrong convergence cannot be cleanly separated from salience. Script:
  `analysis/analyse_ic_counterbalance.py`.
- **Residual risk:** HIGH for the strong claim — the paper must reframe the IC result as
  cascade-like with an acknowledged position/salience confound, not pure lock-in.
  Hidden-tally and vote-only controls still un-run.

### L11. Reflection effect is not causally identified
- **What:** the C4 deterministic reflection rule states the fair-share solution, so the
  coordination gain conflates "reflection/focal-point" with "being given the answer."
- **Why it matters:** cannot claim reflection *caused* the gain.
- **Current handling:** described as "associated with," "consistent with a focal point."
  NOW RUN (comments 2 & 3): a matched placebo (tone/length/register-matched string with
  no coordination content) vs the fair-share injection. Injection 8/10 vs placebo 6/10;
  Mann-Whitney p=0.116, Cliff's delta=+0.42 -> NOT separable, and the content-free
  placebo alone lifts far above C3's 10%. So the fair-share CONTENT is not the
  demonstrable driver; the reflection STEP carries most of the gain. Script:
  `analysis/analyse_p1_placebo.py`.
- **Residual risk:** moderate — use the safer wording ("injects a shared coordination
  norm; focal-point vs instruction vs leakage unresolved"); do NOT keep a focal-point
  causal claim. A larger placebo n and a within-experiment C3 anchor would sharpen it.

### L12. Memory condition doubles as an aggregation aid (IC)
- **What:** in IC, episodic memory also flags the standing plurality, so "memory helps"
  is confounded with "aggregation help."
- **Why it matters:** the memory effect in IC is not pure memory.
- **Current handling:** noted in §5.2 results. NOW RUN (comment 5): a no-flag memory
  condition (plurality hint removed) on a harder 3:3:2 signal split (A/B tie on the
  tally). Baseline 0/5, memory 4/5 (80%) -> memory still enables correct aggregation
  without the flag, supporting genuine temporal aggregation over a mere scaffold.
  Script: `analysis/analyse_ic_noflag.py`.
- **Residual risk:** low-moderate — supportive but n=5/cell; a direct aggregation-aid
  condition would fully separate memory from scaffold.

---

## Tier 4 — Measurement / instrument internals

### L13. LLM-as-judge dependence
- **What:** planning and naturalness use a Claude judge.
- **Why it matters:** judge drift, prompt sensitivity, and judge–generator interaction
  can move sub-scores even with cross-provider separation.
- **Current handling:** cross-provider judge (Claude vs GPT-4o-mini); WISE §6 notes judge
  drift.
- **Residual risk:** low–moderate; multi-judge agreement would strengthen it.

### L14. Cooperation-rate overlaps the macro outcome
- **What:** one behavioural-consistency sub-component (cooperation rate, 6% of the
  composite: w1=0.30 × γ3=0.20) mechanically correlates with success.
- **Why it matters:** mild circularity between B and V.
- **Current handling:** association re-reported with it removed (CD rho = 0.44,
  unchanged conclusion); WISE §6, Measurement.
- **Residual risk:** low — quantified and shown not to drive the result.

### L15. API/model drift and seed non-determinism limit strict reproducibility
- **What:** two related issues: (a) GPT-4o-mini is a closed, versioned, changeable model;
  (b) OpenAI's `seed` parameter provides best-effort, not guaranteed, determinism —
  minor response variation across replications cannot be fully excluded even with a
  fixed `trial_seed = base_seed + trial_index`.
- **Why it matters:** (a) exact regeneration across model updates is not guaranteed;
  (b) if a trial is interrupted and re-run with the same seed, the replayed LLM
  responses (plans, decisions, reflections) may differ slightly from the original,
  introducing non-systematic per-trial variance.
- **Current handling:** fixed snapshot id (`gpt-4o-mini-2024-07-18`); all raw
  `cognitive_process_log.jsonl` and `run_manifest.json` files released so the
  original outputs are preserved regardless of future model changes. Resume logic
  operates at the whole-trial level (manifest-based), so completed trials are never
  re-run.
- **Residual risk:** moderate for (a) — inherent to closed models. Low for (b) — seed
  variation is non-systematic and negligible relative to across-trial variance; results
  are aggregated over 10–20 trials per condition.

---

## Tier 5 — Exploratory components

### L16. Early-warning classifier is exploratory
- **What:** small, imbalanced within-condition data; pooled AUC partly reflects
  architecture identity.
- **Why it matters:** predictive claims are preliminary.
- **Current handling:** labelled exploratory; pooled AUC not headlined. Single-seed AUCs
  were seed/tree-sensitive (0.79/0.77/0.51 vs 0.82/0.79/0.58), so the canonical script
  now reports **seed-averaged** AUCs (25 seeds, 200 trees): within-full K=20 combined
  0.80, macro-only 0.79, micro-only 0.54 (seed-range ±0.02-0.03). Micro-only near chance.
  Script: `analysis/analyse_early_warning.py`.
- **Residual risk:** low — clearly scoped as exploratory; consider shortening §5.5 or
  moving to an appendix (comment 8).

### L17. Type E is partly circular
- **What:** Type E (sub-threshold failure / gap case) is defined via the discrepancy
  criterion it is then used to illustrate.
- **Why it matters:** Type E is descriptive, not independent evidence.
- **Current handling:** stated in §3.4; NOT in §6.
- **Residual risk:** low — already framed as descriptive.

---

## Summary: §6 coverage status (WISE paper)
- **Fully in §6:** L1, L2, L4, L5, L8, L10, L11, L13, L14, L15, L16.
- **Partial / understated in §6:** L3 (pilot size + failed gate), L6, L7 (threshold).
- **Missing from §6:** L9 (cumulative-not-ablation), L12 (memory-as-aggregation-aid),
  L17 (Type E circularity).

## Update — reviewer-comment controls now RUN (were future work)
- **L4 (comment 7):** 5 persona panels + mixed-effects — DONE.
- **L10 (comment 4):** IC counterbalancing — DONE, and it CONFIRMS a position/salience
  confound (baseline fails only when correct = first option). Reframe the IC claim.
- **L11 (comments 2 & 3):** placebo reflection — DONE; injection not separable from a
  content-free placebo. Drop the focal-point causal claim; use the safer wording.
- **L12 (comment 5):** no-flag memory — DONE; memory still aggregates without the flag.
- **Classifier (comment 8):** seed-averaged canonical numbers (0.80/0.79/0.54).
- **Convergent validity (comment 6):** corrected to rho=0.82, n=15; frame as pilot
  sanity check. All new analysis scripts live in `analysis/` (see `analysis/README.md`).
- **Highest-priority residual (reviewer/examiner):** L3 (full multi-rater validation),
  L2 (cross-model/cross-task), and reframing the two claims the new controls weakened
  (IC lock-in -> position confound; reflection focal-point -> reflection step).
- **Still un-run:** hidden-tally and vote-only IC controls; direct aggregation-aid
  condition; planning-only / reflection-only ablations.
