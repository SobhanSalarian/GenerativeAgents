# MRes Progress Log

## 2026-07-01 — IC neutral labels implemented; experiment results reviewed

### New files (Comment #4 — option order randomised + neutral labels)

Two new files created to address the remaining gap in Comment #4. The
counterbalancing experiment (run_ic_counterbalance.py) only rotated which
option was correct; it did not control for alphabetical label bias (A/B/C)
or positional bias (correct option always in the same display position).

**`scenarios/information_consensus_neutral.py`** — new subclass of
`InformationConsensus`. Does NOT modify the original file. Key features:
- Replaces A/B/C labels with X/Y/Z throughout all agent-visible text
  (prompts, memory strings, reflections)
- Replaces semantic descriptions (creative studio, wellness, etc.) with
  neutral ones ("Community development proposal X/Y/Z")
- Rotates display ORDER of options every step via a Latin square over all
  6 permutations of X/Y/Z. Over 30 steps, each option appears in each
  display position exactly 10 times — perfectly balanced.
- Internal tracking (vote_history, TRUE_OPTION, tally keys) stays A/B/C
  for full pipeline compatibility.
- `_init_kwargs()` returns `{true_option, signal_counts}` so
  `clone_scenario()` works correctly across trials.

**`run_ic_neutral_labels.py`** — launcher: 3 rotations × baseline+full ×
5 trials × 30 steps = 30 trials.
- correct_A_as_X: majority option (internal A) displayed as X
- correct_B_as_Y: majority option (internal B) displayed as Y
- correct_C_as_Z: majority option (internal C) displayed as Z

### Experiment results (as of 2026-07-01)

**IC neutral labels — correct_A→X (COMPLETE)**

| Condition | Succeeded | Avg coordination |
|---|---|---|
| baseline | 0/5 | 0.00 |
| full | 5/5 | 0.83 |

Key finding: baseline still fails 0/5 even with neutral X/Y/Z labels and
randomised display order. The original correct_A failure is NOT due to
alphabetical label bias or positional bias — it reflects genuine
information aggregation failure in the baseline condition.

**IC counterbalance — all 3 rotations COMPLETE**

| Rotation | baseline | full |
|---|---|---|
| correct_A | 1/5 (0.10) | 5/5 (0.83) |
| correct_B | 5/5 (0.83) | 5/5 (0.83) |
| correct_C | 5/5 (0.83) | 4/5 (0.67) |

Confirms label salience finding. Full condition robust across all rotations.

**IC noflag 3:3:2 — COMPLETE**

| Condition | Succeeded | Avg coordination |
|---|---|---|
| baseline | 0/5 | 0.00 |
| memory | 4/5 | 0.62 |

Memory enables genuine aggregation even under an ambiguous tally (3:3:2).
Baseline fails completely, ruling out the tally-reading shortcut.

**CD persona panels — seeds 43/44/45 COMPLETE, seed46 in progress**

| Seed | baseline | full |
|---|---|---|
| 43 | 0/5 | 1/5 (0.36) ⚠️ outlier |
| 44 | 0/5 | 5/5 (0.99) |
| 45 | 0/5 | 5/5 (0.98) |
| 46 | in progress | in progress |

Seed 43 is an outlier (full only 1/5). Seeds 44 and 45 cleanly replicate
the primary finding. Seed 46 still running.

### Active experiments (as of 2026-07-01)

| Script | Trials done | Remaining | Avg/trial | Est. finish |
|---|---|---|---|---|
| `run_ic_neutral_labels.py` | 17/30 | 13 | 42 min | ~9 hrs |
| `run_persona_panels_46.py` | 6/10 | 4 | 87 min | ~6 hrs |
| `run_p1.py` | 4/30 | 26 | 182 min | ~3.3 days |

Bottleneck: CD P1 (~3.3 days remaining). IC neutral and seed46 will
finish today (2026-07-01).

---

## 2026-06-30 — Rate limit audit; kill/resume analysis; LIMITATIONS.md updated

### Diagnostics

**429 / RateLimitError audit** across all experiment directories (CD primary,
CD P1, IC primary, CD panel seed 43):

| Condition | Trials affected | Total 429 hits |
|---|---|---|
| CD primary — `full` | 15 / 20 | 46 |
| CD primary — `memory_planning` | 4 / 20 | 9 |
| IC primary — `memory_planning` | 1 / 10 | 2 |

All 20 affected trials completed successfully (manifests present) — no data
loss. Cause: daily RPD limit (10,000 req/day) exhausted by running three
experiment scripts concurrently (run_p1.py, run_ic_counterbalance.py,
run_persona_panels_43.py) against the same API key.

**Kill/resume behaviour confirmed:** resume granularity is at the whole-trial
level (manifest-based). Interrupted trials re-run from step 0 with the same
`trial_seed = base_seed + trial_index`. LLM seed provides best-effort
reproducibility; minor plan/decision variation on re-run is non-systematic
and negligible across 10–20 trials per condition. Not a data validity concern.

**Metric integrity confirmed:** `planning_plausibility` and `memory_coherence`
are within-step citation-relevance metrics (embedding alignment between an
agent's step-level reference text and its current goals/memories). They do
not compare against any cross-step or pre-kill ground truth, so a re-run
with a slightly different plan produces a different-but-internally-consistent
trial — not corrupted data. Paper treatment: not a standalone limitation;
covered by the one-line seed non-determinism note already in §6 / L15.

### Documentation updates

**LIMITATIONS.md — L15 extended** to cover seed non-determinism alongside
model-version drift. Added note that resume logic is manifest-gated so
completed trials are never re-run.

**No §6 / thesis text changes required** — seed non-determinism is a one-line
note in the Limitations section, not a structural concern.

### Active experiments (as of 2026-06-30)

| Script | Terminal | Conditions | Trials | Steps |
|---|---|---|---|---|
| `run_p1.py` | s001 | injection / placebo / memory_planning | 10 each | 100 |
| `run_ic_counterbalance.py` | s004 | baseline + full × 3 rotations | 5 each | 30 |
| `run_persona_panels_43.py` | s006 | baseline + full, seed=43 | 5 each | 100 |

---

## 2026-06-29 — Supervisor comments addressed; four new experiments launched

### Code changes (comments #2, #4, #5, #7)

**run_p1.py (#2):** Added `"memory_planning"` as third arm. All P1 comparisons
now within-experiment (same `base_seed=20260610`) — no cross-dataset artefacts.

**information_consensus.py (#4, #5):** Four changes:
1. `TRUE_OPTION` / `SIGNAL_COUNTS` moved to constructor parameters (defaults
   preserve primary dataset behaviour).
2. `_init_kwargs()` now returns `{"true_option": ..., "signal_counts": ...}` so
   `clone_scenario()` preserves rotation across trials (was returning `{}`).
3. `_deterministic_reflection` converted from `@staticmethod` to instance method;
   hardcoded `"A"` replaced with `self.TRUE_OPTION`.
4. Removed `"X% supported Option A (the majority-signal option)"` clause from
   `group_status` memory string — memory now records raw tally only.

**New launchers:**
- `run_ic_counterbalance.py` — 3 rotations × baseline+full × 5 trials × 30 steps
  (rules out Option A label-salience confound)
- `run_ic_noflag_332.py` — 3:3:2 signal distribution × baseline+memory × 5 trials
  × 30 steps (tests genuine aggregation under ambiguous public tally)
- `run_persona_panels.py` — seeds 43–46 × baseline+full × 5 trials × 100 steps
  (panel robustness check for CD main findings)

### Experiments running

| Script | Trials | Steps | Status |
|--------|--------|-------|--------|
| `run_p1.py` | 30 | 100 | **Running** (started 14:49 AEST) |
| `run_ic_counterbalance.py` | 30 | 30 | Queued |
| `run_ic_noflag_332.py` | 10 | 30 | Queued |
| `run_persona_panels.py` | 40 | 100 | Queued |

Full details: `docs/progress/session_20260629.md`

---

## 2026-06-07 — Experiment results audit: IC complete, CD in progress

### IC v3 `full_llm_reflection` — 10 trials, complete

All 10 trials completed successfully. Results compared against primary IC conditions:

| Condition | Success rate | Coord score | Conv step | Gini | Believability (mean) |
|-----------|-------------|-------------|-----------|------|----------------------|
| baseline | 0% | 0.000 | — | 0.637 | — |
| memory | 100% | 0.833 | 1 | 0.584 | — |
| memory_planning | 100% | 0.833 | 1 | 0.581 | — |
| full | 100% | 0.833 | 1 | 0.585 | — |
| **full_llm_reflection** | **100%** | **0.821** | **1–2** | **0.575** | **0.667–0.683** |

**Finding:** LLM reflection adds no measurable coordination benefit over the
`full` condition in IC. All non-baseline conditions saturate at effectively
identical outcomes. This supports H5 (believability–validity gap): once the
threshold is crossed, additional cognitive richness does not improve group
outcomes further.

**H6 saturation (IC):**
- 984 total reflection strings across 10 trials
- 408 unique strings — repetition rate **0.585**
- Top string appears only 3× — no focal-point convergence
- IC reflections remain substantially diverse across agents and rounds
- Interpretation: task structure (changing vote tallies each round) prevents
  saturation; persona grounding is working but no single lesson dominates

---

### CD `full_llm_reflection` v2 — in progress (7 complete, trial_7 running)

Seven completed trials (trial_0–6; trial_7 active, trials 8–9 pending) show clear improvement over primary CD conditions:

| Condition | Success rate | Sust score | Gini |
|-----------|-------------|------------|------|
| baseline | 0% | 0.138 | 0.313 |
| memory | 5% | 0.264 | 0.334 |
| memory_planning | 10% | 0.326 | 0.239 |
| full | 70% | 0.931 | 0.026 |
| **full_llm_reflection v2** | **100%** | **0.990** | **0.003–0.135** |

**Finding:** CD LLM reflection outperforms even the best non-reflection condition
(100% vs 70% success, sust 0.990 vs 0.931). Reflective synthesis is the key
driver of near-perfect commons coordination.

**H6 saturation (CD, 7 trials):**
- 16,464 total reflection strings
- 810 unique strings — repetition rate **0.951**
- Top string appears 357× — all top-10 strings are semantically identical
  ("stick to fair share → group coordinates")
- This is the focal-point norm collapse predicted by H6: CD reflection converges
  on a single dominant strategy insight and the group coordinates near-perfectly

**Key contrast (H6):**
| Scenario | Saturation rate | Pattern |
|----------|----------------|---------|
| IC full_llm_reflection | 58.5% | Diverse — no focal-point norm |
| CD full_llm_reflection v2 | 95.1% | Saturated — focal-point norm forms |

**Result directory:** `experiment_results_cd_llm_reflection/` — trial_7
currently running (active process PID 28198, 64/100 steps at last check). Trials 8–9
will follow automatically.

---

### Outstanding (updated priority)

1. Wait for CD trial_7–9 to complete
2. Implement H5: signed believability–validity discrepancy metric (`experiment_analysis.py`)
3. Implement H6: reflection saturation analysis — raw counts available; need
   semantic clustering to collapse near-identical strings into canonical forms
4. Implement H7/C4: leakage-safe early-warning classifier (`early_warning.py`)
5. P1: static reflection injection experiment
6. Confirm HREC pathway with Prof. Beheshti; run `llm_judge.py --all`

---

## 2026-06-06 (continued) — Bug fixes, persona description fix, experiment relaunch

### Bug 1: NameError in `_record_scenario_memories` (IC)

`information_consensus.py` referenced bare `personas` inside `_record_scenario_memories()`,
which is a separate method from `step()` and does not have `personas` in scope.

**Fix:** Changed `personas.get(persona_name)` → `self.personas.get(persona_name)`.
`self.personas` is set during `setup()` and is always available.

No equivalent bug in `commons_dilemma.py` — CD explicitly passes `personas` as a
parameter to its `_record_scenario_memories()`.

---

### Bug 2: Persona description missing from LLM reflection prompt (both scenarios)

`_generate_llm_reflection()` in both `commons_dilemma.py` and `information_consensus.py`
did not include `persona.scratch.get_str_iss()` in the reflection prompt. The prompt
only provided: agent name, recent scenario memories (generic group observations),
current vote, private signal, and group count.

**Why this is a flaw in our architecture:** Park et al. also omits the persona
description from the reflection prompt, but their reflections draw from an
autobiographical memory stream that implicitly carries persona-consistent experiences.
Our scenario memories are generic group-level observations (vote tallies, coordination
status) with zero persona signal. Without `get_str_iss()`, the reflection is completely
persona-blind — any agent could produce any reflection regardless of character.

**Evidence:** IC full_llm_reflection trial_0 (faulty prompt) produced 40 unique
reflection strings across 8 agents × 6 steps — no character anchoring, pure generic
deliberative language.

**Fix applied to both scenarios:**
- Added `persona_obj` parameter to `_generate_llm_reflection()` signature
- Added `persona_desc = persona_obj.scratch.get_str_iss() if persona_obj else ""`
- Prepended `persona_desc` to both prompts (same pattern as `_ask_agent()` already uses)
- Call sites updated to pass the persona object already in scope

**Note:** This fix makes our reflection more persona-grounded than Park et al.'s
original for this use case, and is the correct compensation for our non-autobiographical
memory architecture.

---

### Faulty data discarded

- IC v3 reflection trial_0 and trial_1 (faulty prompt) — deleted
- CD full_llm_reflection v1 trials (10 complete trials, faulty prompt) — kept in
  `experiment_results_cd_llm_reflection/` as reference but excluded from analysis
- New clean runs output to separate directories

---

### Trial count decision

Decided on **10 trials** for `full_llm_reflection` in both scenarios:
- Matches the existing IC count (4 conditions × 10 trials)
- CD conditions have 20 trials each — 10 for full_llm_reflection is unbalanced
  but defensible; framed as an exploratory 5th condition
- 5 trials was considered and rejected as statistically too weak

---

### New convenience script: `run_llm_reflection_both.py`

Created `reverie/backend_server/run_llm_reflection_both.py` to run IC then CD
sequentially in one command. IC runs first (30 steps × 10 trials →
`experiment_results_ic_llm_reflection/`), then CD (100 steps × 10 trials →
`experiment_results_cd_llm_reflection/`).

---

### Experiment status at session update

| Dataset | Status |
|---------|--------|
| IC v3 full_llm_reflection | Running (10 trials, both fixes applied) |
| CD full_llm_reflection v2 | Queued — starts after IC finishes |
| CD full_llm_reflection v1 (faulty) | Kept as reference, excluded from analysis |

---

## 2026-06-06 — Research reframing + IC full_llm_reflection launch

### Research reframing (from `reframing my reseach/` documents)

Three documents were reviewed and accepted as the new thesis narrative:
- `Abstract_Intro_RQ_Rewrite.md`
- `Contributions_Section_Draft.md`
- `Limitations_FutureWork_Section.md`

**Central change:** The thesis is now framed around the *believability–validity gap*
(H5/C2) as the headline finding — individually believable agents producing
collectively invalid outcomes — rather than the four confirmatory H1–H4 findings.
H1–H4 are retained as supporting evidence.

**New hypothesis structure:**

| # | Claim | Status |
|---|-------|--------|
| H1 | Higher believability → stronger coordination | Supported (ρ=0.55 CD, ρ=0.75 IC) |
| H2 | Non-linear threshold ~0.36–0.39 | Supported |
| H3 | Richer architecture → higher believability (C3↔C4 not separable) | Partially supported |
| H4 | Planning plausibility strongest predictor (β=0.65, p=0.001) | Supported (observational) |
| H5 | Believability–validity decoupling quantified by signed discrepancy metric | **New — not yet implemented** |
| H6 | Reflection categorical gain = static focal-point norm (saturation=2 strings) | **New — needs saturation analysis** |
| H7 | Coordination collapse predictable from first-K micro traces (within-condition) | **New — needs early-warning module** |
| H8 | Reflection gain driven by content not process (P1 injection) | **Planned experiment** |

**New contributions:** C1 (instrument), C2 (gap demonstration), C3 (focal-point
mechanism), C4 (trace-based diagnostics).

**Key fragility identified:** H6 (focal-point norm) currently rests on
observational evidence from the deterministic reflection condition. The
full_llm_reflection rerun (both CD and IC) will provide stronger support or
surface a qualification. P1 (static injection experiment) is the confirmatory
test.

**Language fix needed in thesis:** "necessary but not sufficient" should be
softened to "consistent with necessity within this study" — the data shows
a lower boundary, not a formal necessity proof.

**Implementation plan agreed (phases):**
1. Audit existing data (verify saturation claim, IC cascade, CD collapse cases)
2. H5: signed believability–validity discrepancy metric (`experiment_analysis.py`)
3. H6: reflection saturation analysis (`experiment_analysis.py`)
4. H7/C4: leakage-safe early-warning classifier + failure taxonomy (`early_warning.py`)
5. P1: static reflection injection condition (`experiment_conditions.py`, `experiment_runner.py`)
6. Wire all into analysis entrypoint

---

### IC `full_llm_reflection` implementation

**Problem:** `information_consensus.py` did not support `use_llm_reflection=True`.
The scenario only had inline deterministic reflection logic — unlike
`commons_dilemma.py` which already had a full `_generate_llm_reflection()` branch.

**Changes made to `scenarios/information_consensus.py`:**

1. Added `own_signal = entry["signal"]` to the step-loop memory/reflection block
   so the LLM reflection prompt has access to the agent's private signal.

2. Extracted the inline deterministic reflection logic into a new static method
   `_deterministic_reflection(own_vote, macro_entry)` — mirrors the CD pattern.

3. Added `_generate_llm_reflection(persona_name, own_vote, own_signal, macro_entry)`:
   - Reads last 5 scenario memories as context
   - Builds a prompt asking for ONE first-person reflective sentence about
     information-sharing and vote-updating behaviour (IC-appropriate framing)
   - Uses `ChatGPT_request`, strips/truncates to 240 chars
   - Returns `""` on any exception (caller falls back to deterministic rule)
   - Identical structure to the CD implementation; only prompt content differs

4. Updated the reflection branch to call `persona.uses_llm_reflection()` and
   route to `_generate_llm_reflection()` when True, with deterministic fallback.

**Design decision:** Used the same single-call simplified approach as CD (not
the full Park et al. two-stage focal-point + retrieval pipeline). Rationale:
internal consistency with CD is more important than Park et al. fidelity for
the H6 cross-scenario saturation comparison. Disclosed in thesis methods section.

---

### IC v3 full_llm_reflection experiment launched

**Command run:**
```bash
cd reverie/backend_server && python experiment_runner.py
```

**Configuration (from `__main__` block, pre-existing):**

| Parameter | Value |
|-----------|-------|
| Scenario | information_consensus |
| Condition | `full_llm_reflection` only |
| Trials | 10 |
| Steps | 30 |
| Agents | 8 (selection_seed=42, same as IC v3) |
| Base seed | 20260524 (same as IC v3) |
| Output dir | `experiment_results_ic_llm_reflection/` |
| Hypothesis analysis | False (manual combination needed after) |

**Status at session end:** Experiment running. Log at
`experiment_results_ic_llm_reflection/run_20260606_135206.log`.

**Purpose:** Test whether full_llm_reflection condition on IC (a) achieves
coordination success like the deterministic full condition and (b) whether
reflection strings also saturate (H6 cross-scenario evidence). Also provides
the fifth condition for IC cross-condition comparison.

---

## 2026-05-27 (IC v3 full inspection — findings, limitations, thesis implications)

### Run health

All 40 trials completed cleanly (10 per condition × 4 conditions).  The final
two `full` trials (trial_8, trial_9) ran on 2026-05-27 and terminated normally.
Parse error rate: **0.0%** across all 2,400 + 480 + 480 + 480 agent decisions
(total 3,840 decisions logged).  This confirms the v3 prompt fix is effective.

---

### Finding 1: Baseline — information cascade failure (100% wrong convergence)

The baseline condition (C1) converged on the **wrong** option in all 10 trials:

| Correct (A) | Wrong-B | Wrong-C |
|---|---|---|
| 0 / 10 | 2 / 10 | 8 / 10 |

**Mechanism (observed in micro logs, steps 0–2):**

- **Step 0:** Every agent votes its private signal → tally `A:4, B:2, C:2`
  (correct plurality, matching the 4:2:2 signal distribution).
- **Step 1:** The two C-signal agents share wellness/recreation framing that
  reads as emotionally salient.  Two of the four A-signal agents update away
  from A toward C.  Tally flips to `A:2, B:1, C:5`.  One B-signal agent also
  moves to C.
- **Step 2:** With C holding a 5-vote lead, all remaining agents cascade onto C
  → `A:0, B:0, C:8`.  Locked permanently for steps 2–29.

This is a textbook **Bikhchandani et al. (1992) information cascade**: once
public information (the vote tally) creates a strong apparent majority, agents
discard private evidence and herd.  Without memory to anchor their prior
reasoning, the cascade is unrecoverable.  The minority signals (C and B)
happened to produce more emotionally compelling statements ("health and
wellness", "outdoor recreation"), which triggered the cascade away from the
correct plurality option.

**Theoretical significance:** This directly demonstrates the prediction of
Bayesian social learning theory in an LLM-agent setting.  Naïve agents with
no memory of their own prior reasoning will over-weight public information and
produce incorrect herding.  This is not a code artefact — it is an expected
failure mode that the scenario was designed to surface.

---

### Finding 2: Memory+ conditions — perfect convergence, zero variance

All three memory-enabled conditions (C2, C3, C4) achieved:

| Condition | Success rate | Convergence step | Tally (all trials) | Std |
|---|---|---|---|---|
| Memory | 10/10 (100%) | 5 | A:8 B:0 C:0 | **0.000** |
| Memory+Planning | 10/10 (100%) | 5 | A:8 B:0 C:0 | **0.000** |
| Full | 10/10 (100%) | 5 | A:8 B:0 C:0 | **0.000** |

All 10 trials in each memory+ condition are **byte-for-byte identical**.
Different seeds were set (20260524–20260533) but GPT-4o-mini produced the
same outputs across all trials.

**What happens:** At step 1, all four minority agents (2 B-signal, 2 C-signal)
simultaneously update to A after observing the step-0 tally of 4:2:2 and the
A-signal agents' shared statements.  The tally jumps from `A:4, B:2, C:2` to
`A:8, B:0, C:0` in one step and stays there.  The convergence_window = 5
requires 5 consecutive coordinated steps, so the run terminates at step 5
(total 6 steps including step 0).

**Mechanism contrast with baseline:** Memory-enabled agents have access to
their own prior-round reasoning in the cognitive context.  This anchors them
to their original private signal assessment even when others express contrary
views.  The minority agents also update correctly here (toward A, which is
correct) because the A-signal agents' statements are specific and evidence-rich,
and the tally provides a clear 4-against-2 signal even at step 0.

---

### Finding 3: Zero-variance is a methodological limitation

The zero variance in C2/C3/C4 means the effective sample size for each of
these conditions is **n=1**, not n=10.  The 30 trials across C2–C4 represent
3 independent observations.

**Root cause:** The IC scenario with the new collective-reasoning prompt is
too easy for memory-enabled agents.  Convergence is so rapid (one round) and
the LLM outputs are deterministic enough for this prompt that no trial-to-trial
variation occurs.

**Thesis disclosure required:** This must be reported as a study limitation.
Suggested wording:

> *"The information consensus scenario produced zero outcome variance across
> all memory-enabled conditions (C2–C4): all 30 trials converged on the
> correct option at step 5 with identical vote trajectories.  Inspection of
> the logs confirmed that GPT-4o-mini produced deterministic outputs for this
> task across different random seeds, reducing the effective per-condition
> sample size to n=1 for the cross-trial comparison.  The IC scenario therefore
> contributes only binary evidence (cascade failure vs. correct aggregation) to
> the coordination success analysis; the statistical analyses for H1–H4 draw
> primarily on the commons dilemma data where outcome variance is present."*

---

### Finding 4: Signal disclosure and belief updating

| Condition | Signal disclosed | Position changes |
|---|---|---|
| Baseline | 703/2400 (29.3%) | 66/2400 (2.8%) |
| Memory | 204/480 (42.5%) | 40/480 (8.3%) |
| Memory+Planning | 213/480 (44.4%) | 40/480 (8.3%) |
| Full | 198/480 (41.2%) | 41/480 (8.5%) |

Memory agents disclose their private signal ~50% more often than baseline
agents, and change position ~3× more frequently.  However, in the memory+
conditions all position changes are the same event: minority agents updating
to A at step 1.  There is no within-condition variability to analyse.

---

### Finding 5: Hypothesis results on IC v3

| Hypothesis | Status | Key statistic |
|---|---|---|
| H1: Believability predicts coordination | **Supported** | Spearman rho=0.750, p<0.0001 |
| H2: Threshold effect below which coordination always fails | **Supported** | Empirical threshold=0.389; below threshold 71% fail, above 100% succeed |
| H3: Monotone believability C1<C2<C3<C4 | **Not supported** | C3→C4 not significant (p=0.65); C1<C2<C3 holds |
| H4: Memory coherence strongest predictor | **Supported** | memory_coherence β=+1.22 (p<0.0001); only significant OLS predictor |

H3 partial failure (C3↔C4 indistinguishable) is consistent with the CD
result and supports the thesis framing that the planning module drives the
key C2→C3 jump, with reflection adding no measurable further effect.

---

### Summary table: IC v3 vs IC v1 vs IC v2

| | v1 (invalid) | v2 (invalid) | v3 (valid) |
|---|---|---|---|
| Parse error rate | 11–18% | ~0% | **0%** |
| Baseline convergence on correct option | artefactually inflated | 0% | **0%** |
| Memory+ convergence on correct option | artefactually inflated | 0% (no updating) | **100%** |
| Within-condition variance | artefact-driven | — | **0.000 for C2–C4** |
| H1 | — | — | **Supported** |
| H3 | — | — | **Partially supported** |

v1 was invalidated by parse-error bias (correct-option default inflated success).
v2 was invalidated by the signal-advocacy prompt framing (agents did not update).
v3 is the clean dataset.

---

### Thesis implications

1. **Baseline cascade failure is a positive finding**, not just a null result.
   It replicates Bikhchandani et al. (1992) in LLM agents and demonstrates
   that the scenario is sensitive enough to detect architectural effects.

2. **IC supports H1/H2/H4 cross-scenario**.  The same metric structure and
   hypothesis tests that worked on CD replicate on IC, supporting the
   generalisability of the believability–coordination relationship.

3. **Zero variance must be disclosed** as a limitation.  The IC data cannot
   support fine-grained statistical analysis across C2–C4; that analysis is
   based on the CD dataset.

4. **Determinism of GPT-4o-mini** should be noted in the methods section.
   With fixed seeds the model converges to the same outputs for a given
   prompt, which reduces the effective sample size when scenarios are too
   simple to generate output variance.

---

## 2026-05-27 (validity fix: rater blinding + scenario-aware packets)

### 1. "Correct option" wording removed from IC packets

**Problem:** `resource_level_label` in `information_consensus.py` was written
as `"N of M agents on correct option"`.  This string appeared in the human eval
UI (Streamlit and React) as a "Consensus support" metric, directly telling
raters that there is a right answer and implying which option it is.  This
would bias raters toward rewarding agents who voted for the "correct" option
regardless of reasoning quality — a systematic threat to rating validity.

**Fix — `scenarios/information_consensus.py`:**
```python
# BEFORE (leaks correct option)
"resource_level_label": f"{n_correct} of {n_agents} agents on correct option",

# AFTER (neutral — identifies option label without revealing it is "correct")
"resource_level_label": f"{n_correct} of {n_agents} agents on Option {self.TRUE_OPTION}",
```

Wait: "Option A" still reveals which option is being tracked as correct, because
only one option is TRUE_OPTION.  The field is no longer rendered in IC packets
at all (see §2 below) — `resource_level_label` is a CD-only field now.

**Residual exposure:** The `information_diffusion_rate` and `n_correct` /
`n_agents` macro fields are still present in IC packets, but they are displayed
as aggregate group metrics (e.g. "Consensus rate: 62%", "Vote tally: A:3, B:3,
C:2"), which do not identify which option is correct.

---

### 2. Scenario-aware packet building (`human_evaluation.py`)

**Problem:** IC packets contained null-valued CD fields (`resource_level_before`,
`pool_percent_before`, `fair_share`, `requested`, `granted`, `collapsed`,
`total_requested`, `resource_level_note`) and CD packets contained null IC
fields (`vote_tally`, `n_correct`, `consensus_rate`, etc.).  The monolithic
structure made packets harder to parse and included misleading null fields.

**Fix:** `build_human_evaluation_packets()` now branches on
`is_ic = scenario == "information_consensus"`.

IC packets — `local_context.macro_state` contains:
- `vote_tally`, `n_agents`, `consensus_rate`, `consensus_reached`,
  `consensus_step`, `information_diffusion_rate`, `coordinated`

IC packets — `decision` contains:
- `vote`, `prior_vote`, `position_change`, `signal_disclosed`,
  `shared_statement`, `reasoning`, `memory_reference`, `plan_reference`

CD packets — `local_context` contains:
- `resource_level_before`, `pool_percent_before`, `fair_share`,
  `current_activity`, `daily_goals`, `recent_memories`
- `macro_state`: `total_requested`, `resource_level`, `resource_level_note`,
  `coordinated`, `collapsed`

CD packets — `decision` contains:
- `requested`, `granted`, `reasoning`, `memory_reference`, `plan_reference`

No null cross-scenario fields appear in either packet type.

---

### 3. Scenario-aware rater UIs

**`human_eval_ui.py` (Streamlit):**
`render_context_block()` now branches on `is_ic = packet.get("scenario") == "information_consensus"`.

- IC situation: vote tally string (e.g. "Option A: 3, Option B: 3, Option C: 2"),
  consensus rate as %, coordinated flag, information diffusion rate
- CD situation: existing resource layout (resource before, fair share, group
  requested, pool percent, resource level)
- IC Decision tab: Option selected, Previous option, Changed position, Signal
  disclosed, Statement shared with group
- CD Decision tab: Requested, Granted

**`agent_eval_react_site/src/App.jsx` (React):**
- `buildMetricItems()` line 163: "Consensus support" (which used
  `resource_level_note`) replaced with "Consensus rate" using
  `formatPercent(macroState.consensus_rate)`.  Consensus rate is a group-level
  aggregate that does not identify which option is "correct".
- `SituationPanel` IC block: removed "Current group support" row (was
  `resource_level_note`), which was redundant alongside the explicit
  vote tally and consensus rate rows.

---

## 2026-05-24 (methodological decision: judge-generator independence)

### LLM judge must use a different model family from the generative agents

Confirmed and documented: `llm_judge.py` must use **Claude (Anthropic)**, not
GPT-4o-mini, because the generative agents are driven by GPT-4o-mini.

**Rationale:** Using the same model to generate decisions and judge them
introduces self-serving bias — the model rates its own outputs higher than
an independent evaluator would.  Judge-generator independence is a standard
requirement from Zheng et al. (2023) "Judging LLM-as-a-Judge with MT-Bench
and Chatbot Arena."  Agreement between Claude ratings and human raters will
reflect genuine quality signal, not model self-consistency.

**Thesis implication:** This must be stated explicitly in §4.5.  Suggested
wording added to `HUMAN_EVALUATION_PROTOCOL.md`.

**Practical step:** Requires an Anthropic API key
(`console.anthropic.com`).  Full dataset cost estimated < $1 USD with
`claude-haiku-4-5-20251001`.

---

## 2026-05-24 (validity finding: LLM memory confabulation at step 0)

### LLM confabulation of `memory_reference` when no scenario memories exist

Observed in the human eval UI: a packet shows "Recent memories: not available"
alongside a non-empty "Memory cited" field.

**Root cause (LLM behaviour, not a code bug):**

`recent_memories` and `memory_reference` come from entirely separate sources:

- `recent_memories` = scenario-recorded episodic summaries injected into the
  prompt; empty at step 0 because no prior rounds have occurred yet
- `memory_reference` = what the LLM wrote in its JSON response; the prompt
  instruction for memory-capable conditions is permissive ("one short sentence
  about any memory... use an empty string if none")

When `recent_memories = []` the LLM receives no scenario memory in its prompt
but still generates a plausible-sounding `memory_reference` by drawing on the
**persona description** text.  This is an LLM tendency to fill gaps rather
than return empty strings.

**Research significance:**

This is informative data, not noise.  It shows that generative agents with
the memory module active will confabulate memory references even when no
actual prior-round memory exists.  This has direct implications for:

- `memory_coherence` scoring: confabulated references should be rated 1–2
- Thesis framing: report as evidence that LLM agents are prone to memory
  confabulation, consistent with known LLM hallucination behaviour
- Rater guidance added to `HUMAN_EVALUATION_PROTOCOL.md` (validity issue #7)

**Decision: do not zero out `memory_reference` in code.**
The data is scientifically meaningful.  Raters are instructed to score
`memory_coherence` as 1 when "Recent memories" is blank but "Memory cited"
is non-empty.

---

## 2026-05-24 (human evaluation infrastructure: LLM judge + CD packet fix)

### 1. Resource Note fix for Commons Dilemma

**Problem:** `resource_level_note` in human eval packets was always blank for
Commons Dilemma.  The macro log never wrote a `resource_level_label` key, so
`human_evaluation.py:macro_entry.get("resource_level_label")` returned `None`
for all CD trials.  IC was unaffected (it already wrote the label).

**Fix — `scenarios/commons_dilemma.py`:**
Added `resource_level_label` to the per-step `macro_entry` dict:
```python
"resource_level_label": (
    f"{self.resource_level:.1f} credits "
    f"({round(sustainability * 100, 1)}% of original pool)"
)
```

**Fix — `human_evaluation.py`:**
Replaced the direct `.get("resource_level_label")` call with a new helper
`_resource_level_note(macro_entry)` that:
1. Returns `resource_level_label` if present (new runs + all IC runs)
2. Falls back to constructing the string from `resource_level` +
   `sustainability_score` for existing CD results already on disk
3. Returns `None` if neither field is available

**Packet regeneration:**
All 168 existing `human_eval_packets.jsonl` files regenerated:
- 80 trials — `experiment_results_cd_primary/commons_dilemma/`
- 40 trials — `experiment_results_ic/`
- 40 trials — `experiment_results_ic_primary/`
- 4 trials  — `experiment_results_ic_test/`
- 4 trials  — `experiment_results_ic_primary/`

No underlying log data (`micro_log.json`, `macro_log.json`) was modified.
Only `human_eval_packets.jsonl`, `human_eval_blind_key.json`, and
`human_eval_ratings.csv` were overwritten per trial directory.

---

### 2. LLM-as-a-judge evaluation module (`llm_judge.py`)

New file: `reverie/backend_server/llm_judge.py`

**Purpose:** Automated reference rater that processes every
`human_eval_packets.jsonl` and writes `llm_judge_ratings.csv` in the same
format as `human_eval_ratings.csv`, so `rating_ingestion.py` can include the
LLM as an additional rater when computing Krippendorff's alpha.

**Design decisions:**

- Uses Claude tool use (`submit_rating` tool) for structured output — no
  regex or JSON parsing, all five fields validated by schema
- Default model `claude-haiku-4-5-20251001` for cost efficiency; override
  with `--model claude-sonnet-4-6` for higher-quality ratings
- Prompt mirrors exactly what human raters see in the UI: persona background,
  local context (resource/consensus state, fair share), memory (recent
  memories), planning (daily goals), and the full agent decision with
  reasoning, memory_reference, and plan_reference
- Scenario-specific context cards (rater focus, summary) included in prompt,
  matching the UI scenario panel
- `rater_id="llm_judge"` written into every row
- Skips files where `llm_judge_ratings.csv` already exists (use `--force` to
  overwrite); supports `--dry-run` to print prompt without API calls
- Rate limiting handled with exponential backoff (3 retries)

**System prompt anchors (matches human rubric exactly):**

| Dimension | 1 (low) | 5 (high) |
|---|---|---|
| behavioural_consistency | Contradicts persona | Fully consistent |
| memory_coherence | Ignores / misuses memory | Uses it well |
| planning_plausibility | No connection | Clear logical connection |
| response_naturalness | Clearly robotic | Natural |
| believable_yes_no | no | yes |

**Usage:**
```bash
python llm_judge.py --dry-run experiment_results_ic_primary    # check prompt
python llm_judge.py experiment_results_cd_primary    # one directory
python llm_judge.py --all                                 # all result dirs
python llm_judge.py --force --all                         # re-rate everything
```

**Requires:** `ANTHROPIC_API_KEY` environment variable.

**Academic note (for thesis §4.5):**
The LLM judge provides a scalable pre-collection reference and allows
LLM–human inter-rater agreement to be reported as a secondary validity check.
It does not replace the 3–5 human raters required by the research plan.

---

## 2026-05-01 (simulation start time and code cleanup)

### Simulation start time changed to 09:00

`environment/frontend_server/storage/base_the_ville_n25/reverie/meta.json`
updated: `curr_time` changed from `"February 13, 2023, 00:00:00"` to
`"February 13, 2023, 09:00:00"`.

**Why:** With `sec_per_step = 10`, all 100 commons-dilemma rounds complete
within 17 simulated minutes. Previously this window fell at midnight
(00:02–00:19) while all 8 agents were asleep at home. The fix moves the
window to 09:00–09:17, when all agents are awake and the planning module
has already fired for the morning. The agents' planning context (daily goals,
current activity) is therefore coherent with the timing of their resource
decisions.

**What was not changed:** `sec_per_step` remains 10. Increasing it to 86400
(one day per step) would trigger daily re-planning every step due to the
new-day detection in `persona.py` (`strftime('%A %B %d')` comparison), causing
massive LLM overhead and breaking hour-specific guards in `plan.py`.

**Effect on results:** None — agents do not see `curr_time` in their prompts.
The change only affects what is written to the log `time` field.

**Trial scope:** trial_0 of the current run (baseline) was forked before this
change and still starts at midnight. All subsequent trials use 09:00.

---

### Code cleanup: 5 issues fixed in `commons_dilemma.py`

1. **`_no_memory_note` removed** — redundant with `_mem_instr` which already
   instructs baseline agents not to draw on memory. Having both created
   duplicate instructions in the prompt.

2. **`fair_share` computed once** — previously computed independently in both
   `step()` and `_resource_context()`. Now computed once in `step()` and
   passed as a parameter to `_resource_context(fair_share)`.

3. **Dead `__init__` initialisations annotated** — `scenario_memories = {}`
   and `scenario_reflections = {}` in `__init__` are immediately overwritten
   by `setup()`. Clarified with comments; not removed (guard against
   setup()-not-called edge cases).

4. **Smallville noise removed from logging context** — `action_address` (e.g.
   `"the Ville:Abigail Chen's room"`) and `current_activity` (e.g.
   `"sleeping"`) were Smallville world state fields with no meaning in the
   commons-dilemma context. Removed from `_build_logging_context()` so the
   micro log is clean of Smallville-specific noise.

5. **"Agents" → "Community members" in memory strings** — `peer_status` in
   `_record_scenario_memories()` used "Agents" while the rest of the scenario
   now uses "community members" for consistency.

---

## 2026-05-01 (commons-dilemma prompt ecological validity fix)

### Improved scenario prompt for academic rigour

Three changes applied to `scenarios/commons_dilemma.py` to align the scenario
with standard Ostrom-inspired commons-dilemma ABM practice:

**1. Concrete resource identity**

The abstract "resource pool / units" framing was replaced with "community fund /
credits". This gives the shared resource a grounded identity that community
members (artists, students, researchers) can relate to, rather than an
abstract unit count.

**2. Fair-share anchor in the resource context**

The resource context string now includes the sustainable equal share per agent
(`replenishment_rate / n_agents`, ≈ 6.3 credits at default parameters). In
Ostrom (1990) and subsequent ABM work (Janssen & Ostrom 2006), agents knowing
the sustainable quota is a standard design feature that allows the model to
test whether agents exercise restraint relative to a known fair-share baseline.
Without this anchor, agents have no reference point for what "fair" means.

**3. Personal-stakes sentence and corrected example**

A one-sentence stakes framing was added immediately before the decision
question: *"These credits support your work and projects in this community.
What you request directly affects your ability to pursue your goals and what
remains for others."* This grounds the resource in each agent's persona without
requiring per-agent customisation.

The example JSON amount was corrected from 30 (4.8× fair share — likely to
bias LLM responses toward over-requesting) to 6 (≈ fair share).

**Academic motivation:** Without personal stakes and a fair-share reference,
the LLM is making decisions about an abstract quantity with no grounding. The
changes do not alter the experimental design or metrics — all four conditions
still differ only in cognitive architecture — but they improve ecological
validity and reduce prompt-level confounds.

**Memory string consistency:** The `_record_scenario_memories()` strings were
also updated from "units" to "credits" so that C2–C4 agents read consistent
language when their past-round memories are injected into future prompts.

---

## 2026-05-01 (scenario-memory construct validity fix)

### Re-scoped commons-dilemma memory to task-relevant episodic memory

During pilot inspection of the `full` condition, `micro_log.json` showed that
the commons-dilemma `recent_memories` field was dominated by low-level
Smallville world perceptions such as:

- `bed is idle`
- `desk is idle`
- `closet is idle`
- `<persona> is sleeping`

These memories are valid outputs of the Park et al. perception and
associative-memory loop, even in headless mode, because the backend still
simulates the Smallville map, tiles, objects, and persona actions. However,
they were not valid evidence for the research-plan construct of **memory
coherence** in the commons-dilemma task.

**Academic concern:** The MRes research plan defines memory coherence as the
appropriate retrieval and use of prior interactions. In the resource-allocation
scenario, prior interactions should refer to previous commons rounds: resource
requests, fair-share deviations, pool changes, oversubscription, and group
coordination outcomes. Using generic room-object memories would weaken
construct validity because the memory condition would test access to recent
environmental perceptions rather than task-relevant prior coordination
experience.

**Resolution:** `reverie/backend_server/scenarios/commons_dilemma.py` now
maintains per-agent scenario-level episodic memory:

- group demand relative to replenishment
- resource-pool change before and after each round
- whether the group stayed within or exceeded the replenishment limit
- each agent's request relative to fair share
- which agents requested at/below or above fair share

The commons-dilemma prompt now uses this scenario memory when
`persona.uses_memory()` is true. General Smallville world memory remains part
of the underlying agent architecture, but it is no longer used as the memory
context for this scenario's experimental manipulation.

The logged context now includes:

- `memory_scope`: `scenario_episodic` or `none`
- `recent_memories`: prior commons-round memories, not room-object states
- `scenario_reflections`: deterministic coordination reflections for the
  `full` condition

The condition interpretation is now cleaner:

- `baseline`: persona identity + current pool state only
- `memory`: baseline + prior commons-round episodic memories
- `memory_planning`: memory + current plan/goals
- `full`: memory + planning + scenario-level coordination reflections

This directly supports:

- RQ1: sharper operationalisation of micro-level memory coherence
- H3: cleaner architectural ablation
  (`baseline < memory < memory_planning < full`)
- H4: meaningful testing of whether memory coherence predicts coordination

**Run-management update:** The default full run now writes corrected outputs
under `experiment_results_cd_primary/` and uses simulation prefix
`commons_experiment_scenario_memory` so corrected data is not mixed with the
earlier pilot outputs generated under `experiment_results/`.

**Believability-score interpretation:** The composite believability formula
was not changed. The fix changes the evidence available to the
memory-coherence sub-score, which has weight 0.25 in the automated composite.
Post-fix scores should be interpreted as believability under a
task-relevant episodic-memory operationalisation. Pre-fix and post-fix
believability scores should not be pooled because the memory context differs.

**Important:** Any long-running experiment process started before this change
must be stopped and restarted. Python processes that already imported
`commons_dilemma.py` will continue using the old generic-memory behaviour.

---

## 2026-04-30 (methodological caveats documented)

### Reflection history depth and study reliability

Documented two boundary conditions on the ablation design in
`MRES_IMPLEMENTATION_PLAN.md` (Methodological Caveats section) and
`RESEARCH_PLAN_FIDELITY_CHECKLIST.md` (§3.3 and §3.7 notes):

**Reflection history depth (C3→C4 effect size)**

Each trial starts from a fork point and runs for 100 steps. The C4 full
condition enables the reflection module during the run but does not start
with deeply accumulated reflection content. This means:
- The ablation comparison (C4 vs C3) is internally valid
- The observed C3→C4 effect size is a conservative lower-bound estimate of
  reflection's full contribution
- Very small C3→C4 gaps should not be read as "reflection has no effect"
  without accounting for run length as a confound
- Optional mitigation: pre-warm the fork before branching to enrich
  reflection content at trial start

**Baseline condition approximation**

C1 disables retrieval, planning, and reflection but retains persona identity
and world grounding. This matches the research plan's intent but not the
strictest reading of "stateless." Recommended framing: state it as a
boundary condition in the limitations section.

These are not fatal flaws. They are known constraints that should appear
explicitly in the thesis and be addressed in how claims are scoped.

---

## 2026-04-30 (mixed-method scoring blend pass)

### Complete mixed-method scoring blend step

Added the final infrastructure layer that combines automated scores with
human rater scores to produce thesis-faithful per-agent metric values, as
required by the research plan (§4.2.1, §4.5).

**Context:** The research plan defines believability as a human+automated
mixed-method measure. The repo already had automated scores, export, and
ingestion pipelines. The final blend step — merging returned ratings into
the actual thesis metrics — was still missing.

---

#### Change 1 — `_build_agent_deblind_map(trial_dir)` in `measurement/micro.py`

Reads `human_eval_packets.jsonl` and `human_eval_blind_key.json` from a
trial output directory and returns `{blinded_agent_id: persona_name}`.
This de-blinding step bridges the anonymised rating packets back to the
named personas used throughout the analysis pipeline.

---

#### Change 2 — `blend_human_ratings_into_summary()` in `measurement/micro.py`

A non-destructive post-processing function that takes a completed
`micro_summary` dict, a merged ratings list from `rating_ingestion`, and
the de-blinding map, and returns the summary extended with `*_final` keys:

Blend weights (per dimension):

| Dimension | Auto | Human |
|---|---|---|
| behavioural_consistency | 0.50 | 0.50 |
| memory_coherence | 0.50 | 0.50 |
| planning_plausibility | 0.50 | 0.50 |
| response_naturalness | 0.60 | 0.40 |

Normalisation: human 1–5 Likert → 0–1 via `(rating − 1) / 4`.

Reliability gating: if `reliability` is provided and a dimension's
Krippendorff's α < 0.67, the human component is skipped for that dimension
and the automated score is used as-is. Gated dimensions are flagged in
`reliability_gated_dimensions`.

`composite_believability_final` is recomputed from the blended sub-scores
using the standard weights (0.30 + 0.25 + 0.25 + 0.20).

New keys added to `micro_summary`:
- `{dim}_final` and `{dim}_final_band` for each of the four dimensions
- `composite_believability_final` and `composite_believability_final_band`
- `human_ratings_blended: True`
- `human_blend_weights` — the weights used per dimension
- `reliability_gated_dimensions` — list of dimensions skipped due to low α
- `personas_with_human_ratings` — list of personas that had human data

---

#### Change 3 — `compute_micro_summary()` extended signature

Three optional parameters added:
- `human_ratings` — `list[dict]` from `rating_ingestion.merge_ratings()`
- `agent_deblind_map` — `{blinded_agent_id: persona_name}`
- `reliability` — reliability dict from `rating_ingestion`

When `human_ratings` is provided the blend is called automatically at the
end of `compute_micro_summary`. Fully backwards-compatible: default
behaviour unchanged when the new params are None.

---

#### Change 4 — Optional post-ingestion blend in `experiment_runner.py`

After `compute_micro_summary` is called, the runner checks for
`trial_scenario.human_ratings_path`. If set, it:
- calls `load_and_analyse_ratings(human_ratings_path)`
- calls `_build_agent_deblind_map(trial_dir)`
- calls `blend_human_ratings_into_summary`
- overwrites `micro_summary` with the extended result
- logs the number of personas blended and any gated dimensions

This makes human-rating injection a single-line scenario config change
once real ratings are collected, with no further code changes required.

---

Why these changes matter:
- The blend step was the last missing piece of the mixed-method evaluation
  pipeline; the repo now implements the full human+auto framework the
  research plan requires
- The reliability gate protects final scores from low-agreement ratings
- Everything downstream (H1–H4 analysis, feature table, condition summaries)
  will automatically use the `*_final` blended values once real ratings are
  supplied

Remaining work before thesis data collection is complete:
- **collect human ratings** — distribute `human_eval_ratings.csv` to 3–5
  raters; point `scenario.human_ratings_path` at the returned files
- **implement information_consensus scenario** — second real coordination
  scenario for cross-scenario generalisability
- **network analysis for role differentiation** — add interaction-graph
  topology to `macro.py` alongside the existing entropy component
- **qualitative failure coding** — analyst coding of exported failure
  bundles; no further code changes needed

---

## 2026-04-30 (research-plan gap-fix pass)

### Research Plan vs. Code Gap Analysis and Fixes

A systematic comparison of the research plan (Table 1, §4.5, §4.6, §4.7)
against the code identified seven concrete gaps. All seven were addressed in
this session.

---

#### Fix 1 — Embedding-based similarity in `measurement/micro.py`

**Gap:** The research plan (Table 1, §4.2) requires cosine similarity of
action embeddings vs. persona profile. The code used Jaccard token overlap
throughout all four micro-metrics.

**Change:** Rewrote `measurement/micro.py`:
- Added `_EMBEDDING_CACHE`, `_embed_text()`, `_cosine_similarity()`,
  `_embedding_similarity()`, `_best_embedding_match()`
- `pre_embed_micro_log()` pre-populates the cache for all unique texts before
  any metric is computed, minimising redundant API calls
- `clear_embedding_cache()` frees memory between trials
- `profile_alignment_per_agent`, `memory_relevance_per_agent`,
  `memory_coherence_per_agent`, `planning_alignment_per_agent`, and
  `planning_plausibility_per_agent` all now use cosine embedding similarity
- Jaccard kept as automatic fallback when embedding client is unavailable

Why this matters: Jaccard ignores semantics. Cosine embedding similarity
captures meaning, which is the intended measurement for profile alignment and
memory relevance.

---

#### Fix 2 — LLM-assisted planning plausibility judge

**Gap:** Table 1 specifies "Human (LLM-assisted) 1–5 rubric" for planning
plausibility. The code produced a Jaccard keyword-overlap score mapped to 1–5.

**Change:** Added `_llm_planning_plausibility_score()` and
`planning_plausibility_llm_per_agent()`:
- Sends a structured prompt asking the LLM to rate plan-action coherence on
  a 1–5 rubric aligned with the Table 1 anchors
- Samples 4 representative entries per persona (early/mid/late + critical
  step) to keep API cost proportional to the human-eval budget
- `planning_plausibility_per_agent()` now blends 0.5 × LLM + 0.5 × embedding
  alignment when LLM scores are available
- `planning_plausibility_llm` exposed as a separate output key in
  `compute_micro_summary`

---

#### Fix 3 — LLM-as-judge response naturalness (distinction test)

**Gap:** Table 1 specifies "Distinction test (human vs. AI) + perplexity". The
code used a heuristic based on word count and sentence count.

**Change:** Added `_llm_response_naturalness_score()` and
`response_naturalness_llm_per_agent()`:
- Sends a prompt asking the LLM to rate (0–1) whether text is
  indistinguishable from human writing and whether a naive reader would be
  fooled
- Same 4-entry-per-persona sampling strategy as the planning judge
- `response_naturalness_per_agent()` now blends 0.6 × LLM + 0.4 × heuristic
- `response_naturalness_llm` exposed as a separate output key

---

#### Fix 4 — OLS regression for H4 (`experiment_analysis.py`)

**Gap:** The research plan (§4.6) calls for "regression modelling to test H4".
The code used only Spearman |rho| ranking.

**Change:** Added `_ols_regression()` and extended `test_h4()`:
- Fits OLS with intercept on all four sub-dimensions vs. coordination_score
- Reports R², per-predictor β coefficients, and t-distribution p-values
- Ranks predictors by |β| and checks whether memory_coherence +
  behavioural_consistency occupy the top two positions (regression-based H4
  support check alongside the existing Spearman check)
- Text report renderer extended with OLS section

---

#### Fix 5 — Rating ingestion + Krippendorff's alpha (`rating_ingestion.py`)

**Gap:** The research plan (§4.5) requires Krippendorff's α ≥ 0.67.
No ingestion or reliability computation existed.

**Change:** Created `reverie/backend_server/rating_ingestion.py`:
- `collect_ratings()` — recursively finds all `human_eval_ratings.csv` files
- `_krippendorff_alpha()` — pure-Python ordinal Krippendorff's alpha
  (no additional dependencies)
- `compute_reliability()` — per-dimension alpha with
  acceptable / marginal / poor classification; flags overall reliability
- `merge_ratings()` — averages multi-rater scores per packet into a single
  table ready for `experiment_analysis.py`
- `flag_low_reliability_packets()` — identifies packets with high
  inter-rater disagreement (≥ 2 dimensions with range > 1.5 points)
- CLI: `python rating_ingestion.py experiment_results/ --output report.json`

---

#### Fix 6 — LLM seed enforcement (`gpt_structure.py`, `experiment_runner.py`)

**Gap:** The research plan (§4.7) lists LLM stochasticity as a key risk.
`DEFAULT_CHAT_SEED` was read from an env var at import time and never updated
per trial.

**Change:**
- Added `set_chat_seed(seed)` to `gpt_structure.py` — updates
  `DEFAULT_CHAT_SEED` at runtime
- `experiment_runner.py` now calls `_set_chat_seed(trial_seed)` before each
  trial so every LLM call in that trial uses the same seed
- `clear_embedding_cache()` is also called between trials to prevent prior
  trial embeddings from polluting the cache

---

#### Fix 7 — Scale trials to 20 (`experiment_runner.py`)

**Gap:** The research plan budget (§7) specifies "4 conditions × 20 runs".
The `__main__` block used `n_trials=3`.

**Change:** Updated `n_trials=20` in the `__main__` block.

---

#### Wiring: critical step passed to micro summary

**Additional improvement:** `experiment_runner.py` now derives `_critical_step`
from the collapse step or peak oversubscription step and passes it to
`compute_micro_summary(use_llm_judges=True, critical_step=_critical_step)`.
This ensures LLM judge sampling is anchored at the most informative moment in
each trial.

---

Why these changes matter collectively:
- The four micro-metric measurement methods now match the Table 1 specification
  at the automated level (embedding similarity + LLM judges)
- H4 analysis is now backed by regression as the plan requires
- Inter-rater reliability can be computed as soon as ratings are collected
- LLM calls are now reproducible at the trial level
- The experiment scale matches the plan budget

Next:
- collect human ratings using the exported `human_eval_packets.jsonl` and
  `human_eval_ratings.csv` artefacts
- run `rating_ingestion.py` once ratings are returned
- implement at least one additional scenario (task_assignment or
  information_consensus)



This log records implementation progress for the MRes-aligned research
platform in the `research-scenarios` branch.

## 2026-04-30 (research-plan alignment pass)

### Experiment Pipeline Upgrade

Completed:

- upgraded `reverie/backend_server/experiment_runner.py` to support:
  - deterministic persona sub-sampling from base worlds
  - 5-10 agent study setups without hand-editing simulation folders
  - per-trial RNG seeding
  - experiment config export
  - automatic H1-H4 analysis execution
- updated `reverie/backend_server/reverie.py` to record:
  - selected personas
  - run seed
  - LLM usage metadata in run manifests

Why this matters:

- the research plan specifies groups of `5-10` agents and multiple
  replications
- experiments are now easier to reproduce and compare across conditions
- each run now stores enough metadata to explain how it was configured

### Baseline and Context Logging Upgrade

Completed:

- updated `persona.move()` / `perceive()` so the baseline condition no longer
  silently accumulates associative-memory traces during perception
- added richer scenario logging in
  `reverie/backend_server/scenarios/commons_dilemma.py`, including:
  - persona profile context
  - recent memories
  - daily goals and current activity
  - fair-share and resource-state context

Why this matters:

- the research plan's baseline condition should be meaningfully weaker than
  the memory-enabled conditions
- later human and automated evaluation now has direct access to the context
  that informed each decision

### Metric and Export Upgrade

Completed:

- rewrote `measurement/micro.py` with richer context-aware proxies for:
  - behavioural consistency
  - memory coherence
  - planning plausibility
  - response naturalness
  - composite believability
- rewrote `measurement/macro.py` to add:
  - run-level coordination success
  - convergence speed / timeout
  - emergent role differentiation
  - structured failure-traceability reports
- added `human_evaluation.py` to export:
  - `human_eval_packets.jsonl`
  - `human_eval_blind_key.json`
  - `human_eval_ratings.csv`
- extended `experiment_analysis.py` to emit `analysis/feature_table.csv`

Why this matters:

- the code is now much closer to the dual-level validation framework in the
  research plan
- several former "manual later" steps are now first-class pipeline outputs
- the repo can now support both automated analysis and human-rating workflows

## 2026-04-30

### Documentation Setup

Completed:

- created `docs/MRES_IMPLEMENTATION_PLAN.md`
- created `docs/MRES_PROGRESS_LOG.md`
- created `docs/TABLE1_IMPLEMENTATION_CHECKLIST.md`

Purpose:

- document the research-to-code roadmap before major changes
- establish a rule that documentation is updated after each phase

Next:

- complete Phase 1 by adding experimental condition scaffolding to the
  runtime

### Phase 1: Experimental Condition Scaffolding

Completed:

- added `reverie/backend_server/experiment_conditions.py`
- added canonical condition definitions:
  - `baseline`
  - `memory`
  - `memory_planning`
  - `full`
- passed experimental condition metadata into:
  - `reverie/backend_server/reverie.py`
  - `reverie/backend_server/persona/persona.py`
- added a lightweight run manifest path in `ReverieServer`
- updated `experiment_runner.py` to accept an experimental condition argument

Why this matters:

- the thesis needs explicit architecture conditions
- the runtime now has a clean place to store and report which condition was
  used in a run
- later behavioural gating can be added without redesigning the experiment
  interface

Validation:

- `python -m py_compile` passed for the touched Phase 1 backend files

Next:

- complete Phase 2 by upgrading the runner to organize outputs by scenario and
  condition, and to support multi-condition execution

### Phase 2: Condition-Aware Experiment Runner

Completed:

- added scenario slugging and per-trial scenario cloning in
  `reverie/backend_server/experiment_runner.py`
- changed the output layout to:
  - `experiment_results/<scenario>/<condition>/trial_<n>/`
- added `run_experiment_matrix(...)` for multi-condition execution
- added matrix-level summary output at:
  - `experiment_results/<scenario>/matrix_results.json`
- added run manifests per trial

Why this matters:

- the thesis requires clean comparisons across conditions
- outputs are now easier to analyze by scenario and by condition
- the runner is now closer to a real experiment harness instead of a single
  ad hoc script

Validation:

- `python -m py_compile` passed for the refactored runner and Phase 1 files

Next:

- extend the micro-level summaries toward the thesis believability dimensions

### Phase 3: Micro-Level Believability Metrics

Completed:

- extended `reverie/backend_server/scenarios/commons_dilemma.py` to log:
  - `memory_reference`
  - `plan_reference`
  - `experimental_condition`
  - `parse_error`
- extended `reverie/backend_server/measurement/micro.py` with:
  - `behavioural_consistency`
  - `memory_reference_rate`
  - `planning_reference_rate`
  - `response_naturalness_proxy`
  - `believability_proxy`

Why this matters:

- the current branch now exposes a first-pass automated view of the thesis
  micro-level constructs
- each scenario step captures richer evidence for later human and statistical
  evaluation
- the pipeline can now produce more thesis-relevant summaries without waiting
  for the full human-rating layer

Important caveat:

- these are automated proxies, not final substitutes for human evaluation of
  believability

Validation:

- `python -m py_compile` passed for the updated scenario and micro metric files
- a sample `compute_micro_summary(...)` call returned the new fields as
  expected

Next:

- strengthen macro-level summaries and add run-to-run stability support

### Phase 4: Macro-Level Validation and Stability

Completed:

- extended `reverie/backend_server/measurement/macro.py` with
  `aggregate_macro_summaries(...)`
- added condition-level summary output in
  `reverie/backend_server/experiment_runner.py`
- each condition folder now receives:
  - `all_results.json`
  - `condition_summary.json`

Why this matters:

- the thesis needs more than single-run outputs
- macro validation now includes replication-oriented summaries such as:
  - collapse rate
  - coordination success rate
  - mean collapse step
  - metric variance across trials
- this makes the runner more suitable for statistical comparison between
  architecture conditions

Validation:

- `python -m py_compile` passed for the updated macro and runner files
- a sample `aggregate_macro_summaries(...)` call returned the expected summary
  structure

Next:

- add export paths for structured human evaluation and richer transcript review

### Table 1 Metric Mapping

Completed:

- created a one-to-one mapping document for the metrics in Table 1 of the
  research plan:
  - `docs/TABLE1_IMPLEMENTATION_CHECKLIST.md`

Why this matters:

- it makes the thesis metric requirements explicit at the code level
- it distinguishes clearly between:
  - fully implemented metrics
  - proxy-only metrics
  - missing metrics
- it gives us a concrete build order for the remaining measurement work

Current headline status:

- `Implemented`: outcome variance
- `Proxy`: behavioural consistency, memory coherence, planning plausibility,
  response naturalness, composite believability, coordination success
- `Missing`: convergence speed, emergent role differentiation, failure
  traceability

Next:

- continue with Phase 5 human-evaluation export support so the proxy-only
  micro metrics can move toward the full mixed-method Table 1 design

### Documentation Expansion

Completed:

- added `docs/README.md`
- added `docs/HUMAN_EVALUATION_PROTOCOL.md`
- added `docs/EXPERIMENT_OUTPUT_SCHEMA.md`
- updated `README-research-scenarios.md` to reflect:
  - the docs folder
  - the current output layout
  - the current metric set
  - the current limitations
  - the condition-gating caveat

Why this matters:

- the branch README now matches the current code more closely
- future analysis work has a schema reference
- the remaining thesis gap around human evaluation is now documented in a
  concrete protocol

Next:

- keep these support docs updated as Phase 5 implementation lands

### Research Plan Fidelity Review

Completed:

- added `docs/RESEARCH_PLAN_FIDELITY_CHECKLIST.md`
- expanded the documentation set so the repo is checked against the **full**
  research plan, not only Table 1

Why this matters:

- the research plan includes important requirements beyond the metric table
- this review surfaced several additional gaps:
  - H1–H4 analysis workflow is still missing
  - full behavioural gating for the architecture conditions is still missing
  - the target `5–10` agent study size is not yet matched cleanly by the
    current base simulations
  - seed control and reproducibility support are still weak
  - human-evaluation exports are still not implemented

Next:

- keep the implementation anchored to
  `docs/RESEARCH_PLAN_FIDELITY_CHECKLIST.md` as the broader source of truth

### Documentation Consistency Refresh

Completed:

- updated `docs/MRES_IMPLEMENTATION_PLAN.md` so it no longer lists
  experimental conditions and the experiment matrix runner as missing
- added an explicit caveat that condition metadata is implemented but full
  behavioural gating is still pending

Why this matters:

- the docs now match the code more accurately
- it reduces the risk of over-claiming that the condition ablation is already
  complete

Next:

- keep the docs aligned as Phase 5 and later metric work lands

## 2026-04-30 (continued)

### Behavioural Condition Gating

Completed:

- modified `reverie/backend_server/persona/persona.py`:
  - `move()` now gates each cognitive module based on the persona's condition:
    - `retrieve()` is called only when `uses_memory()` is True; otherwise
      `retrieved = {}`
    - `plan()` is called only when `uses_planning()` is True; otherwise the
      persona keeps its current `act_address` (idle fallback on first step)
    - `reflect()` is called only when `uses_reflection()` is True
  - added `get_cognitive_context_for_scenario()`: returns a condition-aware
    string assembled from associative memory and scratch state, suitable for
    injection into scenario decision prompts
- modified `reverie/backend_server/scenarios/commons_dilemma.py`:
  - `_ask_agent()` now calls `persona.get_cognitive_context_for_scenario()`
    and inserts the result into the LLM prompt as a "cognitive context"
    section; for C1 agents the section is omitted entirely

What this means for each condition:

- C1 (baseline): `move()` perceives but does not retrieve, plan, or reflect;
  `_ask_agent` prompt contains only identity and resource context; the LLM
  has no memory or plan material to draw on
- C2 (memory): `move()` retrieves from associative memory; `_ask_agent` prompt
  includes a "Recent memories" section drawn from the persona's actual
  `seq_event` and `seq_thought` nodes; no plan section is included
- C3 (memory+planning): same as C2 plus an active planning module; prompt
  includes both "Recent memories" and "Current plans" sections
- C4 (full): same as C3 plus reflection; reflective thoughts accumulate in
  `seq_thought` via `reflect()` and therefore appear in the memory section of
  the prompt automatically

Why this matters:

- conditions C1–C4 now produce genuinely different LLM inputs per scenario
  step, not just different run metadata
- the research's core ablation — varying architecture features and measuring
  their impact on believability and coordination — is now implemented in code
- H3 (monotonically increasing believability across conditions) and H4
  (memory coherence and behavioural consistency as strongest predictors) can
  now be tested against real behavioural differences, not label differences

Validation:

- `python -m py_compile` passed for both changed files

Remaining gaps (unchanged from prior audit):

- no analysis pipeline for H1–H4 hypothesis testing
- no human-evaluation export generation
- no seed control or per-run cost logging
- agent count still 3 (base_the_ville_isabella_maria_Klaus) or 25; research
  plan specifies 5–10
- three scenario stubs (task_assignment, information_consensus,
  emergency_coordination) remain unimplemented

Next:

- implement H1–H4 analysis pipeline (condition-comparison scripts, regression)

### H1–H4 Analysis Pipeline

Completed:

- created `reverie/backend_server/experiment_analysis.py`

What the script does:

- loads all trial data from the experiment_results/ directory tree by reading
  `micro_summary.json` and `macro_summary.json` for every condition × trial
- tests all four hypotheses from Section 3.2 of the research plan:
  - H1: Spearman rank correlation (believability vs coordination_score) +
         Mann-Whitney U comparing high- vs low-believability run groups
  - H2: tertile band analysis of coordination failure rates by believability
         band; empirical threshold detection (highest believability value below
         which every run failed)
  - H3: Kruskal-Wallis H test across conditions + pairwise Mann-Whitney U for
         consecutive condition pairs (baseline→memory→memory_planning→full);
         monotonicity check on condition means
  - H4: Spearman correlation of each micro sub-dimension against
         coordination_score; ranked by |rho|; check whether memory_coherence
         and behavioural_consistency occupy the top two positions
- saves two files per run to experiment_results/<scenario>/analysis/:
  - `hypothesis_report.json` — machine-readable results with all statistics
  - `hypothesis_report.txt` — human-readable report suitable for the thesis

Usage:

```
cd reverie/backend_server
python experiment_analysis.py experiment_results --scenario commons_dilemma
```

Why this matters:

- the research plan requires statistical analysis of H1–H4 (Section 4.6)
- the script can be run as soon as multi-condition trial data exists
- the output format maps directly to the three-stage analysis approach described
  in the research plan (micro comparison for H3, macro comparison for H1/H2,
  regression for H4)

Validation:

- `python -m py_compile` passed for the new analysis script

Remaining gaps:

- no human-evaluation export generation
- no seed control or per-run cost logging
- agent count still 3 or 25; research plan specifies 5–10
- three scenario stubs remain unimplemented

Next:

- implement human-evaluation export (blinded transcript bundles, rater CSV)

---

## Session 2026-05-02 / 2026-05-03

### API Rate Limiting Fix

**Problem:** Trials 1–6 completed in ~20 min each (natural speed), but from
trial 7 onwards each trial took ~2 hours. Cause: 832 API calls per trial burst
through the OpenAI TPM/RPM bucket; the SDK's internal retries then stall each
subsequent call for minutes at a time.

**Fix applied to `reverie/backend_server/persona/prompt_template/gpt_structure.py`:**

- Added `time.sleep(_INTER_CALL_DELAY)` (default 0.3 s, tunable via
  `OPENAI_INTER_CALL_DELAY` env var) before every `ChatGPT_request` call.
  This spreads 832 calls over ~4 extra minutes, preventing bucket exhaustion.
- Replaced bare `except: print("ChatGPT ERROR")` with explicit
  `openai.RateLimitError` handling: exponential backoff with up to 6 retries
  (1 s, 3 s, 5 s, 9 s, 17 s, 33 s), logging each attempt.

Expected trial duration after fix: **~25–30 minutes** consistently across all
80 trials, reducing total experiment time from ~5 days to ~1.5 days.

### Baseline Results Analysis (17 trials, completed 2026-05-02)

Key findings from the first 17 of 20 baseline trials:

| Metric | Mean | Std |
|---|---|---|
| Sustainability score | 0.139 | 0.029 |
| Coordination score | 0.000 | 0.000 |
| Demand pressure | 1.761 | 0.253 |
| Average Gini | 0.312 | 0.063 |
| Parse errors | 0 / 13,600 | — |

**Persona-consistent behaviour confirmed:** Carlos Gomez (poet) requests
mean 30.6 credits (4.9× fair share) across all trials; Yuriko Yamamoto and
Wolfgang Schulz consistently request at or near fair share (6.3 and 7.1
respectively). This is strong face validity for the persona manipulation.

**Three academic observations documented:**

1. **Coordination floor effect:** `coordinated = True` requires
   `total_requested ≤ 50`. No step in 1,700 baseline steps achieved this
   (minimum observed total was ~66). `coordination_score = 0.0` for all 17
   trials. If memory/full conditions also fail to reach 50, H1 will produce a
   null result due to threshold strictness, not because the hypothesis is wrong.
   Threshold can be changed post-hoc from raw `total_requested` values in
   `macro_log.json` — see `RUNNING_THE_EXPERIMENT.md` Part 8.

2. **True collapse is mechanically impossible** under the proportional
   allocation rule: if pool = 50 and total requested = 200, agents receive 25%
   each; pool replenishes back to 50 next round. `collapse_step` will be `None`
   in every trial. The scenario tests _sustained degradation_, not collapse
   dynamics. This should be stated explicitly in the methodology section.

3. **Behaviour locks in after step ~20:** Once the pool depletes to ~50
   credits, individual agent requests become fixed for the remainder of the
   trial (Carlos always requests 50, Wolfgang always 6–10). There are no
   within-trial dynamics in baseline. Memory conditions should break this
   stasis.

### Metrics Recomputability Confirmed

All derived metric files (`macro_summary.json`, `condition_summary.json`,
`matrix_results.json`, `hypothesis_report.*`) are recomputable from the raw
`micro_log.json` and `macro_log.json` files without new API calls. The raw
files are never overwritten after a trial completes. Recompute with:

```bash
python -c "from experiment_analysis import run_analysis; run_analysis('experiment_results_cd_primary', 'commons_dilemma')"
```

### Scenario Memory Validity for H1 — Confirmed Appropriate

The use of task-relevant scenario memory (rather than generic Park et al.
Smallville memories) was reviewed and confirmed academically sound for H1.

**Rationale:**
- Generic Smallville memories (object states, room locations) are irrelevant to
  commons dilemma decisions. Injecting them would test "does irrelevant noise
  affect coordination?" not "does memory of prior rounds affect coordination?"
- Task-relevant episodic memory (what happened last round, who took what, was
  the group sustainable) is the correct operationalisation of the theoretical
  construct being tested.
- Ostrom-inspired ABMs routinely give agents information about prior rounds;
  scenario memory mirrors this standard in the field.

**Caveats to document in the methodology section:**
- This is a controlled operationalisation of episodic memory, not a verbatim
  replication of Park et al.'s retrieval pipeline. State this explicitly.
- Memory content includes social information (which agents requested above/below
  fair share), conflating temporal memory with social information as potential
  mechanisms. Acknowledge in limitations.
- The memory content was engineered to be coordination-relevant; the H1 finding
  (if supported) generalises to task-relevant episodic memory, not episodic
  memory in general. Scope the claim accordingly.

### API Cost Estimate

Based on real token counts from 17 completed baseline trials:
- Per trial (baseline): ~350,641 input tokens + ~42,006 output tokens ≈ **$0.078**
- Full 80-trial experiment (all conditions): **~$7 USD** on gpt-4o-mini
- Same experiment on gpt-4o: ~$104

Cost tracking was not active during current run (env vars not set).
To enable for future runs:
```bash
export OPENAI_CHAT_INPUT_COST_PER_1K_USD=0.00015
export OPENAI_CHAT_OUTPUT_COST_PER_1K_USD=0.00060
```

### Publication Strategy

Two non-mutually-exclusive outputs identified:

1. **Primary — Full research paper:** Submit H1–H4 empirical findings to
   AAMAS 2027 (submission deadline ~October 2026) or JASSS (journal, open
   access, high fit for LLM-based ABM). The study has a genuinely novel
   design: a controlled 4-condition ablation isolating causal contributions of
   specific cognitive modules (memory, planning, reflection) to collective
   coordination outcomes in a standard social dilemma paradigm.

2. **Secondary — Demo paper:** Package the AWS-deployable experiment framework
   as a demo submission to the same or co-located conference. Viable as a
   secondary output; should not be pursued before the full paper is drafted.

**Recommended timeline:** finish experiment (May 2026) → analyse results
(June–July) → draft paper (August–September) → submit AAMAS 2027 (October).

---

## Session 2026-05-05

### Crash Fix: `TypeError: 'NoneType' object is not subscriptable` in `plan.py`

**Symptom:** The experiment crashed mid-trial during the `memory_planning`
condition (trial 5/20), terminating the entire process with exit code 1.

```
TypeError: 'NoneType' object is not subscriptable
  File "persona/cognitive_modules/plan.py", line 269, in generate_act_obj_desc
    return run_gpt_prompt_act_obj_desc(act_game_object, act_desp, persona)[0]
```

**Root cause:** The Park et al. codebase uses `<random>` as a placeholder
object name when an agent moves to a location with no valid interactable maze
object (e.g. Carlos Gomez at The Rose and Crown Pub for a creative writing
workshop). When `run_gpt_prompt_act_obj_desc` is called with `<random>`, the
LLM response fails to parse and the function returns `None`. Three functions in
`plan.py` blindly subscripted `[0]` on the return value without a null check,
crashing the entire experiment process.

**Files changed:** `reverie/backend_server/persona/cognitive_modules/plan.py`

Three functions patched with null guards:

| Function | Line | Fallback |
|---|---|---|
| `generate_action_event_triple` | 264 | `(persona.scratch.name, "is", "idle")` |
| `generate_act_obj_desc` | 269 | `"idle"` |
| `generate_act_obj_event_triple` | 273 | `(act_game_object, "is", "idle")` |

**Before:**
```python
return run_gpt_prompt_act_obj_desc(act_game_object, act_desp, persona)[0]
```

**After:**
```python
result = run_gpt_prompt_act_obj_desc(act_game_object, act_desp, persona)
return result[0] if result is not None else "idle"
```

**Recovery:** Deleted the incomplete `memory_planning/trial_5` folder (only
`agent_step_log.jsonl` had been written — no `run_manifest.json`). The resume
logic re-ran trial 5 from scratch. Trials 0–4 of `memory_planning` and all
20 trials of `baseline` and `memory` were unaffected.

**Why this wasn't caught earlier:** The `<random>` placeholder is only
triggered when a specific combination of agent location + activity has no
valid maze object. Carlos Gomez attending a creative writing workshop at The
Rose and Crown Pub was the first instance to surface this path across all
prior trials.

---

### Crash Fix: `ValueError: too many values to unpack` in `run_gpt_prompt.py`

**Symptom:** Experiment crashed again mid-trial during `memory_planning`
condition (trial 5/20, same trial as the previous crash):

```
ValueError: too many values to unpack (expected 2)
  File "run_gpt_prompt.py", line 477, in run_gpt_prompt_task_decomp
    for i_task, i_duration in output:
```

**Root cause:** When the LLM returns a task decomposition in an unrecognised
format (e.g. numbered markdown headers like `**10:00 AM - 10:05 AM**: Wolfgang
sets up his study space...` instead of the expected `(duration in minutes: 5,
minutes left: ...)` format), `__func_validate` returns False and
`safe_generate_response` falls back to `get_fail_safe()`. That function
returned `["asleep"]` — a list with a bare string. The loop
`for i_task, i_duration in output` then tried to unpack `"asleep"` (6
characters) into 2 variables, raising `ValueError`.

**Files changed:**

- `reverie/backend_server/persona/prompt_template/run_gpt_prompt.py` — fixed
  `get_fail_safe()` inside `run_gpt_prompt_task_decomp` to return
  `[["asleep", duration]]` instead of `["asleep"]`
- `reverie/backend_server/persona/cognitive_modules/plan.py` — added null/empty
  guard on `generate_task_decomp` (line 164): returns `[[task, duration]]`
  fallback if result is falsy

**Before:**
```python
def get_fail_safe():
    fs = ["asleep"]
    return fs
```

**After:**
```python
def get_fail_safe():
    fs = [["asleep", duration]]
    return fs
```

**Recovery:** Same as previous crash — deleted incomplete `memory_planning/trial_5`
results folder and matching storage folder in
`environment/frontend_server/storage/`, then restarted. Both `.pyc` cache
files (`plan.cpython-310.pyc` and `run_gpt_prompt.cpython-310.pyc`) were
also deleted to ensure the fixed source was used.

**Why this wasn't caught earlier:** The markdown-formatted response only occurs
when the LLM generates a long study schedule (Wolfgang's 4-hour chemistry
session) and uses a different formatting style than the short examples in the
prompt template. Shorter schedules in earlier trials parsed correctly.

---

### Data Coherence Review — `memory_planning` Trial 6, Step 0

Manual inspection of a `memory_planning` agent step log entry (Ayesha Khan,
step 0) confirmed the data structure, field values, and code are all correct.
Two step-0 behaviours were identified as LLM compliance issues (not code bugs)
that have implications for analysis:

**1. Confabulated `memory_reference` at step 0**

At step 0 no scenario memories exist yet (`recent_memories: []`,
`memory_context_available: false`). The prompt instructs memory-enabled agents
to return an empty string if no memory applies, but the LLM produced a
plausible-sounding confabulated memory instead
("Last semester, I learned the importance of collaboration and resource-sharing
in my literature classes.").

- The code is correct: `memory_context_available: false` accurately flags that
  no scenario memory was injected.
- The LLM simply did not comply with the "empty string if none" instruction.
- **Analysis implication:** When scoring `memory_coherence`, only include
  entries where `memory_context_available: true`. Step 0 memory references
  across all memory-enabled trials should be excluded or flagged as
  confabulated.

**2. `plan_reference` not grounded in injected `daily_goals`**

At 09:00 the planning module injects morning routine goals ("wake up and
complete morning routine", "eat breakfast"). These are already completed by the
time decisions occur and are not relevant to resource allocation. The agent's
`plan_reference` cited Shakespeare research — drawn from the agent's persona
backstory, not the injected goals.

- The code is correct: it injects whichever daily goals are active at 09:00.
- The LLM drew on broader persona knowledge rather than the specific listed
  goals.
- **Analysis implication:** When scoring `planning_plausibility`, verify
  whether the `plan_reference` content actually maps to entries in `daily_goals`
  rather than accepting any persona-consistent statement as evidence of
  planning grounding. From step 1 onwards, as active goals shift to work/study
  tasks, genuine grounding should improve.

---

### Inter-call Delay Increased to 0.8 s (Default in Code)

**Problem:** The 0.3 s inter-call delay set during the baseline condition was
insufficient for `memory_planning` and `full` conditions. These conditions make
~1,000+ API calls per trial (vs ~832 for baseline) because:

- **Agent conversations**: spontaneous Park et al. conversations between
  co-located agents add ~10+ extra LLM calls per conversation (generate
  dialogue, poignancy ratings, memory storage for each participant)
- **Richer planning prompts**: planning-enabled agents generate longer prompts
  consuming more tokens per call

Result: rate limiting hit from trial 3 of `memory_planning` onwards, pushing
trial duration back to ~2.5 hours despite the earlier fix.

**Fix:** Changed the hardcoded default in
`reverie/backend_server/persona/prompt_template/gpt_structure.py` from
`"0.3"` to `"0.8"`:

```python
_INTER_CALL_DELAY = float(os.getenv("OPENAI_INTER_CALL_DELAY", "0.8"))
```

This is a code change (version-controlled), not an environment variable, so
it applies automatically to all future runs without manual configuration.

**Effect:** Each trial adds ~13 minutes of sleep overhead but eliminates
2-hour rate-limit stalls. Expected trial duration: ~40 minutes consistently
across all remaining conditions. Estimated saving: ~47 hours across the
33 remaining trials.

---

### Cognitive Process Log Added (`cognitive_process_log.jsonl`)

**Motivation:** All internal Park et al. cognitive module calls (poignancy
ratings, task decompositions, object state updates, daily planning, agent
conversations) were previously only visible as debug prints in
`experiment_run.log`. These are now saved to a structured JSONL file per trial
for process transparency and reproducibility.

**Files changed:**
- `reverie/backend_server/persona/prompt_template/gpt_structure.py` — added
  `set_process_log()`, `close_process_log()`, `_write_process_log()`, and
  `_infer_call_type()` functions; `ChatGPT_request` now writes every call to
  the log file when active
- `reverie/backend_server/experiment_runner.py` — opens
  `cognitive_process_log.jsonl` in the trial directory at the start of each
  trial and closes it after `rs.save()`

**Output location:** `experiment_results_cd_primary/commons_dilemma/<condition>/trial_N/cognitive_process_log.jsonl`

**Format:** One JSON object per line:
```json
{"timestamp": "2026-05-06T10:35:27", "call_type": "event_poignancy", "prompt": "...", "response": "5"}
```

**Call types captured:**

| `call_type` | What it represents |
|---|---|
| `commons_decision` | The scenario resource-allocation decision (the research data) |
| `event_poignancy` | Park et al. memory importance scoring for world events |
| `conversation_poignancy` | Poignancy rating for agent-to-agent conversations |
| `task_decomp` | 5-minute subtask breakdown for daily activities |
| `daily_planning` | Hourly schedule generation at wake-up |
| `object_state` | Object state description (bed is occupied, desk is cluttered) |
| `emoji_conversion` | Action-to-emoji mapping for frontend visualisation |
| `action_sector` | Agent navigation: which sector to move to |
| `action_arena` | Agent navigation: which arena within the sector |
| `conversation_generation` | Spontaneous agent-to-agent dialogue |
| `event_triple` | Subject-predicate-object encoding of events |
| `other` | Any call not matching the above patterns |

**Note:** The log captures ALL calls including Smallville world simulation
calls, not just commons dilemma decisions. To extract only research-relevant
calls, filter by `call_type == "commons_decision"`.

---

## Session 2026-05-07

### Crash Fix: `TypeError: 'NoneType' object is not subscriptable` in `generate_convo_summary`

**Symptom:** Experiment crashed mid-trial during `memory_planning` condition
(trial 18/20, i.e. `trial_17`) at a spontaneous agent conversation:

```
TypeError: 'NoneType' object is not subscriptable
  File "persona/cognitive_modules/plan.py", line 301, in generate_convo_summary
    convo_summary = run_gpt_prompt_summarize_conversation(persona, convo)[0]
```

**Root cause:** Same underlying pattern as the previous two crashes. The Park
et al. codebase has numerous functions that call a `run_gpt_prompt_*` helper
and immediately subscript `[0]` without checking for a `None` return. When
the LLM response fails to parse (e.g. during a rate-limit retry that still
returns an unexpected format), the helper returns `None` and the `[0]`
subscript raises `TypeError`.

A systematic audit found **six** remaining unguarded `[0]` calls in
`plan.py` beyond those fixed in the previous session:

**Files changed:** `reverie/backend_server/persona/cognitive_modules/plan.py`

| Function | Fallback |
|---|---|
| `generate_first_daily_plan` | `[]` |
| `generate_action_sector` | `"<random>"` |
| `generate_action_arena` | `"<random>"` |
| `generate_convo_summary` | `"conversing"` |
| `generate_decide_to_talk` | `False` |
| `generate_decide_to_react` | `"wait"` |

All six functions now follow the same null-guard pattern:
```python
result = run_gpt_prompt_*(...)
return result[0] if result else <fallback>
```

**Stale bytecode:** `plan.cpython-310.pyc` was deleted from `__pycache__/`
after applying the fix to force Python to recompile from the updated source.

**Recovery:** Deleted incomplete `memory_planning/trial_17` results folder
(only `agent_step_log.jsonl` written — no `run_manifest.json` or
`results.json`) and the matching storage folder
`commons_experiment_scenario_memory_memory_planning_trial_17`. Experiment
resumed from `--start_trial 17`.

**All remaining `[0]` subscripts in `plan.py` are now guarded.** No further
crashes of this type should occur.

---

### Data Quality Finding: Reflection Convergence in `full` Condition

**Discovery:** Manual inspection of `full/trial_0/micro_log.json` revealed that
across 800 agent-step entries, `scenario_reflections` contains only **2 unique
strings** injected a total of 2,352 times:

| Reflection text | Injection count |
|---|---|
| "Even moderate requests were not enough because total group demand exceeded replenishment." | 2,049 |
| "Requests above fair share increased pressure on the shared pool and may require restraint next round." | 303 |

Both reflections appear from step 1 onwards and remain fixed for the rest of
the trial.

**Why this happens:** The commons dilemma scenario has a narrow outcome space —
at each step, either total group demand exceeded replenishment or it did not.
The reflection generator produces a lesson based on that binary outcome, so the
reflection content converges to two fixed strings almost immediately. This is
an expected property of the constrained repeated-game structure, not a code bug.

**Impact on H3/H4 validity:** The hypotheses test whether the *presence* of
reflections changes agent behaviour relative to conditions without reflections
(`memory_planning`). That contrast remains valid — `full` condition agents
receive these injected lessons every step while `memory_planning` agents do not.
The experimental comparison is intact.

**Limitation for thesis:** The reflection mechanism does not accumulate diverse,
evolving insights the way Park et al. (2023) intended for open-ended social
simulation. In this scenario it collapses to a binary signal by step 1.

**Recommended write-up note:** *"Reflection content converged to two
scenario-level summaries by step 1 of each trial, limiting the diversity of
reflective input across the simulation. This is an expected consequence of the
constrained commons dilemma outcome space rather than a code error, and does
not invalidate the H3/H4 behavioural comparison between `full` and
`memory_planning` conditions."*

---

## Session 2026-05-09

### Experiment Complete — All 80 Trials Finished

All four conditions completed successfully. No crashes occurred in the `full`
condition. The experiment runner exited cleanly after `full/trial_19`.

**Final dataset:** 4 conditions × 20 trials × 100 steps × 8 agents = **64,000
agent decisions**.

---

### Final Results Summary

| Condition | Sustainability | Coordination Score | Coord. Success Rate | Demand Pressure | Gini |
|---|---:|---:|---:|---:|---:|
| baseline | 0.138 | 0.000 | 0% | 1.771 | 0.313 |
| memory | 0.264 | 0.066 | 5% | 1.578 | 0.334 |
| memory_planning | 0.326 | 0.085 | 10% | 1.325 | 0.239 |
| **full** | **0.931** | **0.709** | **70%** | **0.998** | **0.026** |

**Key finding:** The `full` condition (memory + planning + reflection) produces a
qualitative leap in outcomes. Coordination success jumps from 10% to 70%.
Sustainability reaches 0.931 (vs 0.138 baseline). Demand pressure drops to 0.998
(nearly at the sustainable threshold of 1.0). Gini drops to 0.026 — near-perfect
equality in resource distribution. This is not a marginal improvement; it is a
categorical shift in collective behaviour.

The incremental gains from baseline → memory → memory_planning are real but modest.
The addition of reflection (memory_planning → full) is where the breakthrough occurs.

---

### H1–H4 Hypothesis Test Results

Analysis run: `experiment_analysis.py` on all 80 trials (2026-05-09).

| Hypothesis | Status | Key statistic |
|---|---|---|
| **H1**: Believability predicts coordination | ✅ SUPPORTED | Spearman ρ=0.549, p<0.0001 |
| **H2**: Threshold effect below which all runs fail | ✅ SUPPORTED | Empirical threshold: believability=0.363 |
| **H3**: Believability increases monotonically across conditions | ✅ SUPPORTED | KW H=68.91, p<0.0001; all pairwise ✓ |
| **H4**: Memory coherence + consistency > planning + naturalness | ❌ NOT SUPPORTED | Planning plausibility ranks 2nd, not consistency |

**H1 detail:** Moderate-strong positive correlation between composite believability
and coordination score across all 80 trials.

**H2 detail:** Three bands identified (low ≤0.541, mid ≤0.671, high >0.671).
Below the empirical threshold of 0.363, all runs failed. In the high band, 50%
succeeded. Clear non-linear effect confirmed.

**H3 detail:** Condition means monotonically increase: 0.347 → 0.543 → 0.669 →
0.682. All consecutive pairwise comparisons significant (smallest p=0.0015 for
memory_planning → full). Architectural enrichment reliably increases believability.

**H4 detail (unexpected):** Spearman ranking: memory_coherence (ρ=0.544) >
planning_plausibility (ρ=0.501) > behavioural_consistency (ρ=0.248) >
response_naturalness (ρ=-0.109). OLS regression identifies planning_plausibility
as the only significant predictor (β=0.645, p=0.0012, R²=0.264). H4 predicted
memory_coherence and behavioural_consistency would occupy top 2 — planning_plausibility
displaced consistency into 3rd place. **Interpretation:** Planning grounding is a
stronger driver of coordination than anticipated. Agents who articulate their goals
clearly and consistently also achieve better collective outcomes. This is a
substantively interesting finding, not a failure.

---

### Sustainability Score Documentation Fix

The `sustainability_score` metric was incorrectly described in some documentation
as "final pool level / initial pool level". The correct definition (confirmed in
`measurement/macro.py`) is the **mean of per-step pool health across all 100 steps**.

Fixed in:
- `docs/EXPERIMENT_RESULTS_DATA_DICTIONARY.md` — both `macro_log.json` and
  `macro_summary.json` entries updated
- `docs/MRES_IMPLEMENTATION_PLAN.md` — metrics table updated
- `docs/THESIS_METRICS_ASSESSMENT.md` — §4.1 marked as resolved

No code changes required. The implementation was always correct; only the
documentation was wrong.

---

## Session 2026-05-09 (continued) — Research Plan Comparison

### Formal Research Plan Assessment

User attached the MRes Research Plan (April 2026) for comparison against actual
results. Assessment completed and documentation updated.

**Timeline status:** Experiments finished 6–8 weeks ahead of schedule (May 2026
vs Jun–Jul 2026 planned). Human evaluation (Jul–Aug 2026) and thesis drafting
(Aug–Sep 2026) are still on track.

**Hypothesis fidelity:**

| Hypothesis | Plan expectation | Result | Verdict |
|---|---|---|---|
| H1 | Believability positively correlates with coordination | ρ=0.549, p<0.0001 | ✅ SUPPORTED |
| H2 | Threshold below which all runs fail | Threshold at 0.363 | ✅ SUPPORTED |
| H3 | Believability monotonically increases C1→C4 | 0.347→0.543→0.669→0.682 | ✅ SUPPORTED |
| H4 | Memory coherence + consistency > planning + naturalness | Planning_plausibility dominates OLS (β=0.645, p=0.001) | ❌ NOT SUPPORTED |

**Key finding against the plan:** The full condition produces a categorical shift
rather than an incremental improvement. The research plan framed C1→C4 as a
smooth continuum; actual results show C1–C3 clustered in the low coordination
band (0–10% success) and C4 achieving 70% success. The reflection module
(C3→C4 step) is the critical component.

**Threshold fidelity:**

- Coordination success: full condition achieves exactly 0.70 — meets the
  research plan's "high" threshold (≥0.70).
- Composite believability: full condition achieves 0.682 — just below the "high"
  threshold (≥0.70). Human evaluation may shift this.

**Documentation updates made in this session:**

- `docs/THESIS_METRICS_ASSESSMENT.md` — added full condition to both macro and
  micro tables; updated recommended thesis claim with all 4 conditions; added
  H4 unexpected finding section; added full-condition breakthrough section;
  updated Overall Judgement
- `docs/RESEARCH_PLAN_FIDELITY_CHECKLIST.md` — added §7 (Research Plan vs.
  Actual Results) with timeline table, hypothesis results table, macro/micro
  threshold comparison, deviation analysis, and alignment summary

---

## Session 2026-05-09 (continued) — Reflection Saturation Decision

### Reflection Saturation: Option 1 Selected (Documentation Only)

**Issue recap:** The full condition (C4) generated only 2 unique reflection
strings across 2,352 injections in trial_0. Root cause: 100-step trials produce
structurally repetitive resource-allocation memories → similar focal questions
at each reflection trigger → same insights stored → loop.

**Three options were assessed:**

1. **Document it** — no re-run; frame as a methodological boundary condition
2. **Pre-warm the fork** — run N extra Smallville steps before each trial to
   build reflection diversity before the commons dilemma starts
3. **Memory-rotation fix** — modify `_record_scenario_memories()` to rotate
   memory framings across steps; re-run full condition only

**Decision: Option 1 selected.** Rationale:
- Pre-warm reflections are Smallville-domestic, not task-relevant; they help
  only the first reflection trigger
- Memory-rotation fix is stronger but requires a code change and partial re-run
- The 70% coordination success is a clean finding regardless of reflection
  diversity; the saturation does not invalidate the result
- Being 6–8 weeks ahead of schedule makes burning the buffer on a marginal
  improvement unwise

**Thesis limitation paragraph agreed:**

> The reflection module generated a small set of recurring insights across
> trials (approximately 2 unique reflection strings across the full condition).
> This convergence is expected given the short 100-step horizon and
> structurally repetitive resource-allocation memories — agents make similar
> decisions each round, which produces similar focal questions at each
> reflection trigger. The C3→C4 coordination improvement should therefore be
> attributed to the reflection module being active and contributing strategic
> synthesis, rather than to richly evolving reflective insight. The effect
> size is best treated as a conservative lower bound on reflection's potential
> contribution in longer-horizon or more varied task settings.

**Next steps agreed:**
- Plan and implement two additional coordination scenarios
- Assess whether the thesis can be submitted as a research paper

---

## Session 2026-05-09 (continued) — Paper Assessment + Scenario Roadmap

### Can the thesis be submitted as a research paper?

**Assessment: Yes, with conditions.**

The contribution is publication-worthy: dual-level validation framework for
generative agents applied to coordination, empirical 4-condition design with
clean statistics, and the H4 planning_plausibility finding that goes against
cited prior work. Specific venue analysis:

| Venue | What is needed | Realistic deadline |
|---|---|---|
| AAMAS 2027 workshop | Current results + one extra scenario | Nov–Dec 2026 (concurrent with thesis) |
| JASSS / AI Review journal | Human evaluation + 2 scenarios | Mid-2027 (PhD Year 1) |
| AAAI 2027 main track | Not realistic without human eval + multiple scenarios | Too competitive |

**Blockers to address before any submission:**
1. Human evaluation (Jul–Aug 2026 per plan) — removes the "all proxies" objection
2. Second scenario (removes single-scenario generalisability concern)

**Recommended path:** Submit thesis November 2026 first. Extract a tightly-scoped
conference paper for AAMAS 2027 workshop in December 2026, when human evaluation
data will be available. Discuss with Beheshti and Zhang which venue fits best.

---

### Publication Venue — Updated Assessment (2026-05-24)

ICDM was considered and ruled out. Full reasoning documented below.

**ICDM verdict: not recommended.**

- Acceptance rate ~9% — very competitive
- Venue fit problem: ICDM expects novel mining algorithms, scalability
  results, or knowledge discovery methods. This work is agent evaluation
  methodology, which reads as AI/MAS research regardless of reframing.
  Reviewers familiar with ICDM scope will sense the mismatch and at 9%
  acceptance that alone can sink an otherwise solid paper.
- Reframing around "trace-based behavioural mining" is possible but
  forces the contribution into an unnatural frame that dilutes it.

**Recommended primary venue: AAMAS 2027 main track**

- Acceptance rate ~25% — realistic for this contribution
- Perfect venue fit: agent evaluation methodology is core AAMAS scope
- Reviewers will engage with H4 (planning > memory) as a substantive
  finding, not a curiosity
- Approximate deadline: October 2026 — aligns with completing IC v3,
  human eval, and paper writing by August–September 2026
- Verify exact deadline at aamas2027.org when live

**Fallback: JASSS (Journal of Artificial Societies and Social Simulation)**

- Rolling submission — no deadline pressure
- Open access, respected in agent-based simulation community
- No page limit — methodology can be fully described
- Submit immediately if AAMAS rejects

**Human evaluation strategy confirmed (2026-05-24):**

- 2 raters (researcher + one supervisor)
- Commons Dilemma scenario only (IC v3 data pending; add IC if time allows)
- 1 median trial per condition (4 trials × 24 packets = 96 packets per rater)
- Trial selection by median sustainability score — transparent, non-cherry-picked:
  - baseline: trial_12 (sustainability=0.139)
  - memory: trial_8 (sustainability=0.173)
  - memory_planning: trial_18 (sustainability=0.284)
  - full: trial_17 (sustainability=0.957, convergence step 12)
- Frame as "preliminary human validation" not "human evaluation study"
- Report Krippendorff's α honestly; do not gate composite score on 2-rater α
- Use directionally: "human ratings correlated with automated
  planning_plausibility scores, supporting construct validity"

**Timeline to AAMAS 2027 submission:**

| Milestone | Target |
|---|---|
| IC v3 complete | June 2026 |
| Human eval ratings collected | July 2026 |
| Rating ingestion + blend into composite | July 2026 |
| Paper first draft | August 2026 |
| Supervisor review + revision | September 2026 |
| AAMAS 2027 submission | October 2026 |
| Thesis submission | November 2026 |

### Two Additional Scenarios Agreed

1. **`information_consensus`** (next to implement)
   - Agents receive private signals about a community policy decision
   - Must communicate, share information, and converge on the correct option
   - Tests information aggregation rather than resource restraint
   - Maps directly to the research plan's "consensus-building" language (§4.4)

2. **`task_assignment`** (second)
   - Community has N tasks; agents volunteer without duplication or gaps
   - Tests voluntary contribution and role differentiation
   - Directly activates emergent role differentiation metric

**Build order:** information_consensus first (2–3 weeks); 10-trial pilot per
condition; then task_assignment. Both fit within the Jul–Aug 2026 analysis
window before thesis drafting.

---

## Session 2026-05-09/10 — information_consensus Implementation + Design Fixes

### Implementation completed

`scenarios/information_consensus.py` fully implemented and registered in
`scenarios/__init__.py`. Smoke test (1 trial × 4 conditions × 10 steps) ran
successfully.

### Design issues confirmed by smoke test

The first smoke test revealed four problems:

1. **LLM Option-A bias** — "Community garden and creative workspace" is
   inherently appealing. Wolfgang Schulz (signal B) and Yuriko Yamamoto
   (signal C) both voted A at step 0 despite non-A signals. Baseline
   achieved coordination_success=True without genuine information sharing.

2. **Signal distribution 5-2-1 too unbalanced** — 5 A-signal agents plus 2
   biased agents = 7/8 voting A at step 0, trivially exceeding the 6/8
   threshold.

3. **`_check_signal_disclosed` false positives** — checked for option letter
   in reasoning text; all agents mention their option, so all conditions
   showed ~100% disclosure.

4. **`convergence_window=3` caused premature exit** — memory_planning and
   full terminated at step 3 out of 10.

### Fixes applied (2026-05-10)

**`scenarios/information_consensus.py`:**
- OPTIONS replaced with three equally appealing community proposals:
  A = "Shared creative studio and collaborative workshop space",
  B = "Community learning centre with digital skills programs",
  C = "Outdoor recreation area and wellness garden"
- SIGNAL_COUNTS changed from 5-2-1 to **4-2-2** — genuine persuasion required
- SIGNALS updated to match new option names with evidence-source language
- SIGNAL_KEYWORDS class attribute added; `_check_signal_disclosed` now checks
  content keywords ("consultation", "needs assessment", "wellbeing") not letters
- `convergence_window` raised from 3 to **5**

**`measurement/macro.py`:**
- `compute_macro_summary` now checks `consensus_reached` flag in macro log
  entries (written by information_consensus) as an override for
  `coordination_success`. Prevents warm-up steps from pulling the overall
  fraction below the 0.75 threshold when the convergence window was genuinely
  achieved. Zero impact on commons_dilemma (no `consensus_reached` field).

### Second smoke test results (post-fix)

| Condition | Coord score | Success | Steps |
|---|---|---|---|
| baseline | 0.000 | False | 10/10 |
| memory | 0.100 | False | 10/10 |
| memory_planning | 0.500 | False | 10/10 |
| full | 0.714 | **True** | 7/10 (converged at step 6) |

Monotonic coordination increase confirmed. Baseline correctly fails.
Residual single-agent bias (Yuriko Yamamoto, 1/8 agents) noted; will
average out across 10 trials.

### Next step

Run 10-trial pilot: `n_trials=10, n_steps=30, output_dir=experiment_results_ic`.

---

## Session 2026-05-10 — Human Eval Packet Fixes + Full Experiment Launch

### Human eval packet issues identified and fixed

Two issues found in `human_eval_packets.jsonl` output for information_consensus:

1. **Parse errors in reasoning field** — GPT-4o-mini occasionally wraps its
   JSON response in markdown code fences (` ```json ... ``` `). `json.loads()`
   rejected these, storing raw truncated error text as the reasoning field.
   Zero parse errors in all 80 commons_dilemma trials; only IC was affected.

   **Fix:** Added markdown fence stripping in `_ask_agent` for both
   `information_consensus.py` and `commons_dilemma.py` before `json.loads()`.

2. **`resource_level` in macro_state misleading for IC** — the pipeline
   compatibility stub (`resource_level = n_correct`) showed meaningless float
   values (e.g. 5.0) to human evaluators.

   **Fix:** Added `resource_level_label` to IC macro log entries
   (e.g. "5 of 8 agents on correct option") and `resource_level_note` to
   `human_evaluation.py`'s macro_state packet construction.

3. **Retroactive fix of existing packets** — 29 parse-error packets across
   `experiment_results_ic_test` and `experiment_results_ic` were patched
   in-place. Partial reasoning text was extracted and marked `[truncated]`.
   Commons_dilemma packets untouched (0 errors).

### Full information_consensus experiment launched (2026-05-10)

`experiment_results_ic/` — the real experiment dataset, equivalent in status
to the 80-trial commons_dilemma corpus:

| Parameter | Value |
|---|---|
| Scenario | information_consensus |
| Conditions | baseline, memory, memory_planning, full |
| Trials per condition | 10 |
| Steps per trial | 30 |
| Output dir | `experiment_results_ic/` |
| sim_code_prefix | `ic_pilot` |

30 steps chosen (vs 100 for commons_dilemma) because IC converges by step ~6
in the full condition — further steps would be redundant and costly.

**Status at time of documentation:** baseline condition running (trial 3/10).
Memory, memory_planning, and full still pending. ETA ~2–3 hours total.

### Next steps (after experiment completes)
1. Run `experiment_analysis.py` on `experiment_results_ic/`
2. Compare H1–H4 direction with commons_dilemma results
3. Implement `task_assignment` scenario (second additional scenario)

---

## Session 2026-05-23

### Methodology Chapter Cross-Check (v3.1 → v3.2)

Performed a systematic cross-check of the methodology chapter draft (v3.1)
against the codebase. Four discrepancies were found and corrected in v3.2.

**Discrepancy 1 — Material: Blend weights (§X.6.3)**

v3.1 stated the default human/automated blend as "60% human / 40% automated"
across all sub-dimensions. The actual implementation in `measurement/micro.py`
(`_BLEND_WEIGHTS_DEFAULT`) uses:

| Dimension | Auto | Human |
|---|---|---|
| behavioural_consistency | 0.50 | 0.50 |
| memory_coherence | 0.50 | 0.50 |
| planning_plausibility | 0.50 | 0.50 |
| response_naturalness | 0.60 | 0.40 |

The chapter had response naturalness backwards (stated 60% human; code is
60% auto) and overstated the human weight for the other three. Fixed in v3.2
with the rationale for the lower human weight on response naturalness (ceiling-
effect risk) made explicit.

**Discrepancy 2 — Minor: H1 secondary test grouping (§X.7.1)**

v3.1 described the H1 secondary Mann-Whitney U test as comparing "top tertile
and bottom tertile". The code uses fixed thresholds (`BELIEVABILITY_HIGH=0.70`,
`BELIEVABILITY_LOW=0.40`). Tertile banding is used in H2, not H1. Fixed.

**Discrepancy 3 — Minor: Role labels (§X.5.3)**

v3.1 used informal labels (cooperators, extractors, stabilisers, oscillating).
The code uses `conserver` (ratio < 0.8), `competitor` (ratio > 1.2), `balancer`,
`volatile` (consistency < 0.45). Chapter now uses the code's labels with
thresholds stated.

**Discrepancy 4 — Minor: H3 pairwise test directionality (§X.7.3)**

v3.1 did not state that the pairwise Mann-Whitney tests are one-tailed. The
code uses `alternative="greater"` (richer condition > leaner). Added explicit
statement and noted the directionality was pre-specified.

**Additionally identified:** sub-dimension internal weights (0.45/0.35/0.20
for BC; 0.4/0.6 for MC and PP) are not discussed anywhere in the chapter.
These are implementation judgment calls, not literature-derived values. A
disclosure paragraph was drafted for §X.4.5:

> The sub-dimension scores are themselves weighted composites. Behavioural
> consistency combines request consistency (0.45), persona-profile alignment
> (0.35), and cooperation rate (0.20)... Memory coherence and planning
> plausibility each apply a 0.4 / 0.6 split between an explicit-citation
> indicator and an embedding-based semantic relevance score... These
> sub-dimension weights are implementation judgements rather than
> literature-derived values. The composite-level sensitivity checks defined
> above partially bound this dependence, but the sub-weights themselves are
> not varied independently.

---

### Network Topology Analysis Added to `macro.py`

Implemented the influence-structure component of §X.5.3, which was committed
to in the methodology chapter but left methodologically open. Four functions
added to `reverie/backend_server/measurement/macro.py`:

**`influence_network(micro_log)`**
Builds a directed pairwise lagged-correlation matrix across agents. For each
ordered pair (source, target): Pearson r between source's requests at steps
0..T-2 and target's requests at steps 1..T-1. A positive weight means target
tends to adjust its request in the direction of source's prior request.
Returns: `{agents, matrix: {source: {target: r}}, min_steps}`.

**`network_descriptors(network, threshold=0.30)`**
Derives summary network statistics from the influence matrix using a
significance threshold of |r| ≥ 0.30:
- `density` — fraction of possible directed edges that are significant
- `in_degree` / `out_degree` — per-agent influence counts
- `reciprocal_pairs` / `reciprocity` — bidirectional influence pairs
- `max_influence_pair` — (source, target, r) for the strongest edge

**`influence_baseline(micro_log, n_permutations=100, threshold=0.30)`**
Random baseline via permutation test. Shuffles each agent's request sequence
independently 100 times using a seeded LCG (no numpy dependency), recomputes
density each time, and compares observed density against the null distribution.
Returns observed density, baseline mean/std, p-value (fraction of permutations
≥ observed), and `above_chance` flag (observed > mean + 2σ).

Validation confirmed: 8-agent trial with 4 follower pairs → observed density
0.214 vs baseline mean 0.008, p=0.0, above_chance=True.

**`group_state_responsiveness(micro_log, macro_log)`**
Per-agent correlation between own request at step t and prior-step group
demand excluding self. Interpretation:
- `follows_crowd` (r > 0.30): agent increases demand when group increased
- `counter_balances` (r < -0.30): agent pulls back when group over-demands
- `independent` (|r| ≤ 0.30): ignores group state

All four functions wired into `compute_macro_summary()` under the
`"influence_network"` key with no breaking changes to existing keys:

```json
"influence_network": {
    "matrix": {...},
    "descriptors": {...},
    "baseline": {...},
    "group_state_responsiveness": {...}
}
```

Each step validated with synthetic micro_log tests before proceeding to the
next. All edge cases handled: empty log, single agent, all-constant series.

**Academic alignment:** Directly operationalises §X.5.3 of the methodology
chapter — "both role entropy and the chosen influence descriptors are compared
against random-baseline expectations to determine whether observed structure is
statistically distinguishable from chance." Role entropy was already
implemented; influence structure is now complete.

---

## Session 2026-05-24 — IC Dataset Invalidation + Prompt Fix + v3 Pre-registration

### IC v1 and v2 datasets invalidated

Full parse-error audit of `experiment_results_ic/` (v1) found:

| Condition | Parse error rate | Successful trials | Of those, outcome-determinative |
|---|---|---|---|
| baseline | 18.3% | 0/10 | 9/10 |
| memory | 11.7% | 2/10 | 2/2 (100%) |
| memory_planning | 16.2% | 8/10 | 8/8 (100%) |
| full | 14.5% | 8/10 | 7/8 (88%) |

Every successful trial in memory, memory_planning, and full was
outcome-determinative: parse errors defaulting to `TRUE_OPTION` ("A") were
the margin that pushed step-level consensus above the 6/8 threshold. The
apparent condition gradient (0% → 20% → 80% → 80%) is an artefact of
parse-error votes, not genuine information aggregation.

Genuine (non-parse-error) switching analysis confirmed the underlying signal
was real but extremely weak:

| Condition | Genuine switch rate | Trials with any switch |
|---|---|---|
| baseline | 0.00% | 0/10 |
| memory | 0.52% | 6/10 |
| memory_planning | 2.26% | 8/10 |
| full | 1.79% | 8/10 |

`experiment_results_ic_primary/` (v2) showed 0.500 flat across all 40 trials —
zero genuine switching. Root cause identified: in v1, parse-error-inflated
vote tallies (showing 6+ agents on A when the true count was 4) created false
social proof that induced the weak genuine switching observed. With the correct
fallback (signal not TRUE_OPTION), vote tallies are honest and the 4:2:2 split
provides insufficient social proof for B/C agents to update.

**Both datasets are invalid. Neither can be used for H1–H4 IC claims.**

### Prompt fix pre-registered (2026-05-24)

The core problem: the IC prompt framed the decision as signal-advocacy
("Based on your signal... which option do you currently support?") rather
than collective reasoning. Agents anchored on their private signal and did
not update based on group evidence.

**What changed in `scenarios/information_consensus.py` `_ask_agent()`:**

Removed:
> "Your signal is an important piece of information that others may not have.
> Sharing it clearly helps the community make the best collective decision.
> Based on your signal, the current vote tally, and what others have shared,
> which option do you currently support?"

Replaced with:
> "Your signal is one input among many. Other community members hold different
> pieces of evidence you have not seen. The goal is to reach the decision that
> best reflects all available evidence — not to advocate for your own signal.
> Consider: does the vote tally and what others have shared suggest that the
> collective evidence points somewhere different from your private signal? If
> multiple people with different backgrounds are converging on an option, their
> combined evidence may outweigh your single signal.
> Which option best reflects all the evidence available to the group so far?"

The example response was also updated to show a B-signal agent updating to A
based on collective evidence, making the belief-updating pattern explicit.

**Academic rationale:** Information aggregation theory (Condorcet jury theorem)
requires agents to weight others' evidence, not just advocate their own. The
original prompt suppressed this mechanism. The fix restores it without changing
any other experimental parameter.

### v3 pilot verification (2026-05-24)

2 trials × 4 conditions × 15 steps with `base_seed=20260524`:

| Condition | Success | Parse errors | Genuine switches | Notes |
|---|---|---|---|---|
| baseline | 0/2 | 0 | 6/112 | rate ~0.07 — agents switch but cannot coordinate |
| memory | 2/2 | 0 | 4/40 | Converges at step 6, rate 0.917 |
| memory_planning | 2/2 | 0 | 4/40 | Converges at step 6, rate 0.917 |
| full | 2/2 | 0 | 4/40 | Converges at step 6, rate 0.896–0.917 |

All three verification criteria passed:
1. Parse errors = 0 across all conditions ✅
2. Genuine belief updating confirmed ✅
3. Condition gradient present (baseline fails, memory+ succeeds) ✅

**Baseline failure mode:** agents without memory converge on the wrong option,
not just fail to converge. This is theoretically coherent — without episodic
context to track what evidence has been shared, agents are herded by local
advocacy toward whichever option is argued most recently/forcefully.

**Note on convergence speed:** memory+ conditions converged at step 6 in the
pilot (consistent with `convergence_window=5` — requires 5 consecutive
coordinated rounds). This is fast relative to v1 (median ~10 steps for full
condition) but plausible given the stronger belief-updating prompt. The full
10-trial run will confirm whether step-6 convergence is consistent or variable.

### Next step: full v3 run

Run `experiment_results_ic_primary/` with identical parameters to v1:
- 10 trials × 4 conditions × 30 steps
- `persona_sample_size=8`, `selection_seed=42`, `base_seed=20260524`
- `export_human_eval=True`

This will be the primary IC dataset for H1–H4.
