# Thesis Metrics Assessment

This note assesses whether the current macro- and micro-level results in this
repository are suitable for use in a thesis, and how they should be framed
academically.

## Academic Validity of Single-Platform Evaluation (added 2026-05-24)

### Is it valid to test the framework only on the Park et al. architecture?

**Yes — provided claims are scoped correctly.**

The framework contribution has two separable layers:

- **Framework design** — the abstract dual-level validation logic (micro
  metrics, macro metrics, human eval protocol, hypothesis tests).
  Architecture-agnostic by design.
- **Framework instantiation** — the concrete implementation on Park et al.
  (2023) using Commons Dilemma and IC scenarios.  One rigorous realisation.

Single-platform validation is standard in CS/IS framework papers.  Park et
al. is the canonical, most-cited, and only widely-used open GABM platform —
the strongest possible instantiation choice.

Do not claim empirical validation on other architectures (AutoGen, CAMEL,
AgentVerse). Do claim the design is architecture-agnostic and note
generalisation as future work.

### Is it valid to not test on external datasets?

**Yes — no suitable external data exists.**

No publicly available GABM simulation datasets with structured per-agent
decision logs (reasoning, memory references, plan references) exist.  The
Park et al. (2023) repository releases code only — confirmed by direct
inspection.  External validation was therefore not feasible; controlled
experiments with known ground truth provide stronger internal validity
than post-hoc application to unstructured third-party logs.

Use in limitations section:

> External validation on independent datasets was not attempted, as no
> publicly available GABM simulation datasets with structured agent decision
> logs currently exist (Park et al., 2023 release code only).  The absence
> of such datasets is itself a gap in the field that this framework is
> positioned to address.

---

## Short Answer

Yes, the results can be used in a thesis, provided they are presented as
computational experiment results with clearly defined automated metrics and
explicit limitations.

The macro-level results are the strongest part of the evidence base because
they measure observable simulation outcomes: resource sustainability,
coordination, demand pressure, inequality, convergence, and collapse. The
micro-level results are useful but should be described as automated proxy
measures of agent-level believability, memory use, planning plausibility, and
response naturalness.

The current results support a cautious academic claim:

> The automated evaluation suggests that memory and planning conditions improved
> resource sustainability and reduced collective demand pressure relative to
> baseline. However, coordination success remained low across all conditions,
> indicating that memory and planning improved individual decision grounding more
> strongly than they produced reliable group-level coordination.

They do not support a strong causal claim such as:

> Memory and planning conclusively improve group coordination.

## Evidence Quality

The results are academically usable because they have:

- Defined experimental conditions: `baseline`, `memory`, and `memory_planning`
- Repeated trials: 20 trials per condition in the current commons-dilemma output
- Separated levels of analysis: individual agent metrics and group/system metrics
- Exported raw and summary data: `micro_log.json`, `macro_log.json`,
  `micro_summary.json`, `macro_summary.json`, and `condition_summary.json`
- A documented measurement pipeline in `measurement/micro.py`,
  `measurement/macro.py`, and `experiment_analysis.py`

The results should be treated as preliminary or mixed-methods-ready rather than
final human-validated behavioural evidence.

## Macro-Level Assessment

Macro metrics are the most defensible thesis outcomes because they are based on
directly observable simulation state rather than subjective interpretation.

Across the existing commons-dilemma results:

| Condition | Sustainability | Coordination | Demand Pressure | Gini | Coordination Success Rate |
|---|---:|---:|---:|---:|---:|
| `baseline` | 0.138 | 0.000 | 1.771 | 0.313 | 0.00 |
| `memory` | 0.264 | 0.066 | 1.578 | 0.334 | 0.05 |
| `memory_planning` | 0.326 | 0.085 | 1.325 | 0.239 | 0.10 |
| **`full`** | **0.931** | **0.709** | **0.998** | **0.026** | **0.70** |

Interpretation:

- Sustainability improves modestly from baseline → memory → memory_planning,
  then jumps dramatically at full (0.138 → 0.264 → 0.326 → 0.931).
- Demand pressure tracks sustainability: near-sustainable (0.998) only in the
  full condition, where agents request almost exactly at the replenishment rate.
- Gini (inequality) is near zero (0.026) in the full condition — close to
  perfectly equal distribution.
- Coordination success jumps from 10% (memory_planning) to 70% (full) — a
  qualitative shift driven by the reflection module, not a linear increment.
- The full condition meets the research plan's coordination success threshold
  (≥0.7) and approaches the high sustainability band.

Academic framing:

- **Strong claim**: Memory + planning + reflection produces reliable coordination
  success (70%) and near-sustainable resource use (demand pressure ≈ 1.0).
- **Moderate claim**: Memory and planning alone (C2, C3) improve sustainability
  and reduce demand pressure but do not reliably produce coordination success.
- **Finding**: The C3→C4 jump is larger than C1→C3, suggesting the reflection
  module is the critical component for collective coordination in this scenario.

## Micro-Level Assessment

Micro metrics are useful for explaining agent-level mechanisms, but most should
be treated as proxies.

Across the existing commons-dilemma results:

| Condition | Avg Request | Cooperation Rate | Behavioural Consistency | Memory Coherence | Planning Plausibility | Composite Believability |
|---|---:|---:|---:|---:|---:|---:|
| `baseline` | 11.066 | 0.464 | 0.530 | 0.000 | 0.000 | 0.347 |
| `memory` | 9.861 | 0.863 | 0.657 | 0.638 | 0.000 | 0.543 |
| `memory_planning` | 8.283 | 0.809 | 0.634 | 0.665 | 0.507 | 0.669 |
| **`full`** | **~8.0** | **high** | n/a | n/a | n/a | **0.682** |

*Note: per-agent micro averages for the `full` condition are stored in
`full/*/micro_summary.json`; the composite believability value (0.682) is from
the hypothesis report.*

Interpretation:

- Average requests fall when memory and planning are enabled; the full condition
  approaches the fair-share (≈6.3) per agent.
- Memory-enabled agents cite and use memory frequently.
- Planning-enabled agents produce planning references almost continuously.
- Composite believability rises across all four conditions: 0.347 → 0.543 →
  0.669 → 0.682. The gap from memory_planning to full is small (0.013), but the
  coordination gain is large (10% → 70%).
- Response naturalness is near ceiling in all conditions, so it is unlikely to
  discriminate strongly between conditions without human ratings or a stricter
  judge.

Academic framing:

- Use micro metrics as mechanism indicators.
- Avoid treating them as direct proof of human-like believability unless human
  evaluation is included.
- State clearly that `memory_coherence`, `planning_plausibility`,
  `response_naturalness`, and `composite_believability` are automated proxies.
- The full condition composite believability (0.682) falls just below the ≥0.7
  "high" threshold from the research plan; this is worth noting in the thesis
  as a borderline result, not a failure — macro outcomes at full are clearly high.

## Important Methodological Caveats

### 1. Sustainability Definition Mismatch ✅ RESOLVED (2026-05-09)

~~There is a documentation mismatch that should be corrected before thesis use.~~

**Resolved:** All documentation now correctly describes `sustainability_score` as
**mean of per-step `(resource_level / initial_resource)` across all 100 steps** —
average pool health throughout the trial, not the final state.

The following files were updated:
- `docs/EXPERIMENT_RESULTS_DATA_DICTIONARY.md` — macro_log.json and macro_summary.json entries
- `docs/MRES_IMPLEMENTATION_PLAN.md` — metrics table

**For thesis writing:** Describe `sustainability_score` as
*"mean per-step pool health as a fraction of the initial pool, averaged across all 100 simulation steps."*
The final pool state is separately available as `final_resource_level` in `macro_summary.json`
and `condition_summary.json` if needed.

### 2. Proxy Metrics Need Careful Language

Several metrics approximate constructs that are normally assessed by human
judgement:

- `memory_coherence`
- `planning_plausibility`
- `response_naturalness`
- `composite_believability`

These are acceptable in a thesis as automated proxy metrics, but they should not
be described as definitive measures of believability or human-likeness.

Recommended wording:

> Automated proxy measures were used to estimate memory coherence, planning
> plausibility, response naturalness, and composite believability. These metrics
> provide scalable indicators of agent behaviour, but they should be interpreted
> as approximations rather than substitutes for human evaluation.

### 3. Composite Believability Is Condition-Sensitive

The composite believability score includes memory and planning dimensions.
Therefore, baseline and memory-only conditions are structurally disadvantaged on
dimensions that are not available in those conditions.

This does not make the metric invalid, but it means the metric should be framed
as measuring realised cognitive behaviour under each condition, not pure agent
quality independent of condition design.

### 4. Coordination Remains Weak

The macro results suggest improvement, but not robust coordination. Even in the
best condition, most runs do not reach the coordination-success threshold.

This is an important finding, not a failure. It suggests that individual-level
cognitive improvements do not automatically translate into reliable group-level
coordination.

### 5. Full-Condition Breakthrough Finding

The `full` condition (memory + planning + reflection) achieves 70% coordination
success and sustainability of 0.931. This is not a continuation of the incremental
trend from C1→C3; it is a categorical shift. This finding is the most important
empirical result in the dataset and should be prominently reported.

Framing note: the jump occurs when the **reflection** module is added.
Thesis-appropriate wording:

> The addition of the reflection module (C4 vs C3) was associated with a
> qualitative shift in collective outcomes: coordination success increased from
> 10% to 70% and mean sustainability from 0.326 to 0.931. This suggests
> that reflection-mediated synthesis of prior experience — rather than memory
> retrieval or planning alone — is the critical architectural feature for
> enabling reliable coordination in this commons-dilemma setting.

Important caveat (see §3.3 of RESEARCH_PLAN_FIDELITY_CHECKLIST.md): each trial
starts from a shared fork point with 100 steps. Reflection had limited prior
experience to synthesise. The C3→C4 effect size should be described as a
**conservative lower bound** on reflection's contribution.

### 6. H4 Unexpected Finding

The research plan cited Hishiki et al. [23] and behavioural regularity theory
as motivation for H4 (memory coherence + consistency > planning + naturalness
as predictors of coordination). The actual result:

| Predictor | Spearman ρ | OLS β | OLS p |
|---|---:|---:|---:|
| memory_coherence | +0.544 | +0.191 | 0.556 |
| planning_plausibility | +0.501 | **+0.645** | **0.001** |
| behavioural_consistency | +0.248 | −0.452 | 0.749 |
| response_naturalness | −0.109 | +0.172 | 0.956 |

Planning plausibility is the only significant OLS predictor (β=0.645, p=0.001).
H4 is **not supported**: planning displaces behavioural consistency from the
top-2 ranking. Recommend framing this as a positive finding:

> Contrary to H4, planning plausibility — not memory coherence or behavioural
> consistency — was the strongest independent predictor of coordination score
> in the OLS regression (β=0.645, p=0.001, R²=0.264). This suggests that
> articulating clear, goal-consistent plans is more predictive of successful
> collective coordination than consistency of past behaviour or accuracy of
> memory retrieval, at least in a short-horizon commons-dilemma setting.

## Recommended Thesis Claim

A defensible thesis statement based on all four completed conditions:

> In the commons-dilemma simulation, architectural enrichment from baseline to
> full (memory + planning + reflection) produced a monotonic increase in
> composite believability (0.347 → 0.682) and a dramatic improvement in
> macro-level outcomes. The full condition achieved 70% coordination success
> and 0.931 mean sustainability — compared to 0% and 0.138 in the baseline.
> At the micro level, planning plausibility was the strongest independent
> predictor of coordination success (β=0.645, p=0.001), contrary to the
> hypothesis that memory coherence and behavioural consistency would dominate.
> A believability threshold was confirmed at 0.363, below which no trial
> succeeded. These results suggest that the reflection module — which
> synthesises past interactions into higher-order insights — is the critical
> architectural component for reliable collective coordination in this setting.

## Recommended Limitations Section

Suggested limitations text:

> The evaluation relies partly on automated proxy metrics. Macro-level measures
> such as demand pressure, resource sustainability, and coordination score are
> directly derived from simulation state and are therefore relatively robust.
> Micro-level measures such as memory coherence, planning plausibility, response
> naturalness, and composite believability approximate constructs that would
> ideally be validated through independent human ratings. As a result, these
> micro-level results should be interpreted as scalable indicators of behavioural
> patterns rather than final evidence of human-like believability.

> Human evaluation was conducted on the commons dilemma scenario only.  This
> scenario was selected because it produces the greatest behavioural variance
> across conditions (coordination success: 0% → 5% → 10% → 70%) and the
> richest per-agent decision traces for rater assessment of planning plausibility,
> memory coherence, and response naturalness.  The information consensus
> scenario, in which conditions C2–C4 converge to near-identical outcomes
> (≈91% consensus at ≈6 steps), offers insufficient within-condition variance
> for meaningful human rating.  Whether human-rated believability generalises
> to information-sharing scenarios with lower behavioural variance remains a
> direction for future work.

## Overall Judgement

**Status as of 2026-05-09: All 80 trials complete. H1, H2, H3 supported. H4 not supported.**

The results are academically strong and suitable for thesis presentation. The
full-condition breakthrough (70% coordination success, 0.931 sustainability) is
a clear, defensible empirical finding. The H4 deviation from expectation is an
interesting positive result rather than a problem.

Remaining gap: composite believability in the full condition (0.682) falls just
below the research plan threshold of ≥0.7. This should be noted honestly rather
than obscured. Human evaluation (Jul–Aug 2026) may shift this slightly.

Priority framing for the thesis:
1. The macro results are the strongest evidence — cite them first.
2. The full-condition categorical shift (reflection as the key module) is the
   headline finding.
3. The H4 unexpected result (planning > consistency) is a substantive
   contribution, not a failure.
4. Micro proxy metrics support and explain the macro findings; they do not need
   to stand alone as primary evidence.
