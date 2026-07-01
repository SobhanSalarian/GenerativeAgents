# Table 1 Implementation Checklist

This document maps **Table 1** from the MRes research plan to the current
`Mres_demo` codebase.

Its purpose is to answer, metric by metric:

- what Table 1 requires
- what the repository currently implements
- whether that implementation is complete, proxy-only, or missing
- what must still be built to make the implementation thesis-faithful

## Status Legend

- `Implemented`
  The repo already provides a materially aligned implementation.
- `Proxy`
  The repo provides a lightweight automated approximation, but not the full
  Table 1 design.
- `Missing`
  The metric is not yet implemented in a meaningful form.

## Coverage Snapshot

### Micro-level metrics

| Table 1 metric | Current status | Notes |
|---|---|---|
| Behavioural consistency | `Proxy` | Now uses cosine embedding similarity for profile alignment (replaces Jaccard). Request consistency + cooperation + embedding profile-alignment composite. Human rating still required for the Likert dimension. |
| Memory coherence | `Proxy` | Commons-dilemma memory is now scenario-specific episodic memory from prior resource-allocation rounds. Cosine embedding relevance scores whether cited memories match available task memory. Human accuracy check still required. |
| Planning plausibility | `Partial` | Now blends an LLM-assisted 1–5 rubric judge (sampled per persona) with embedding alignment; this matches the "Human (LLM-assisted)" Table 1 method. The full rubric is now automated via `_llm_planning_plausibility_score()`. |
| Response naturalness | `Partial` | Now blends an LLM-as-judge distinction test (`_llm_response_naturalness_score()`) with the heuristic fallback. Directly implements the Table 1 "Distinction test (human vs. AI)" method at the automated level. |
| Composite believability | `Proxy` | Now built from upgraded sub-scores including LLM judge components and cosine embedding similarity. Still a proxy until human ratings are ingested via `rating_ingestion.py`. |

### Macro-level metrics

| Table 1 metric | Current status | Notes |
|---|---|---|
| Coordination success | `Proxy` | Explicit run-level `coordination_success` with configurable threshold. Still commons-dilemma-specific. |
| Convergence speed | `Implemented` | Sustained-streak convergence with timeout. |
| Emergent role differentiation | `Proxy` | Role entropy from observed request strategies. Network analysis component still missing. |
| Outcome variance | `Implemented` | CV across replications with `robust/unstable` banding. |
| Failure traceability | `Proxy` | Structured automated failure bundles exported per trial. Qualitative human coding still required. |

## Metric-by-Metric Checklist

## Micro-level (Individual Agent)

### 1. Behavioural consistency

Table 1 requirement:
- **Measurement method:** cosine similarity of action embeddings vs. profile
  plus human rating
- **Type:** Auto + Human
- **Scale:** `0–1` and `1–5 Likert`
- **Thresholds:** `>= 0.7 high; < 0.4 low`

Current repo coverage:
- [micro.py](../reverie/backend_server/measurement/micro.py)
  contains:
  - `request_consistency_per_agent(...)` — 1 − CV over requests
  - `profile_alignment_per_agent(...)` — **cosine embedding similarity** of
    action text vs. persona profile (upgraded from Jaccard; falls back to
    Jaccard when embedding client is unavailable)
  - `cooperation_rate_per_agent(...)`
  - `behavioural_consistency_per_agent(...)` — weighted composite
    (0.45 × request consistency + 0.35 × embedding profile alignment + 0.20
    × cooperation rate)
  - threshold banding via `_label_dict(..., "behavioural_consistency")`

Status:
- `Proxy`

What is still missing:
- human Likert rating (1–5 rater sheet column exists in
  `human_eval_ratings.csv` but ratings not yet ingested back into scores)
- final blended Auto+Human score once `rating_ingestion.py` produces
  per-agent averages

Implementation tasks:
- collect human ratings using the exported `human_eval_ratings.csv`
- run `rating_ingestion.load_and_analyse_ratings()` to obtain per-packet
  average scores
- blend human behavioural_consistency ratings into the composite

Priority:
- Medium (automated embedding layer is now complete)

### 2. Memory coherence

Table 1 requirement:
- **Measurement method:** prior-context references divided by opportunities
  plus human accuracy check
- **Type:** Auto + Human
- **Scale:** `0–1 ratio` and `1–5 Likert`
- **Thresholds:** `>= 0.6 high; < 0.3 low`

Current repo coverage:
- [commons_dilemma.py](../reverie/backend_server/scenarios/commons_dilemma.py)
  logs: `memory_reference`, `recent_memories`, `memory_scope`,
  `memory_context_available`
  - `recent_memories` are now scenario-specific episodic memories from prior
    resource-allocation rounds, not generic Smallville object-state memories
  - `memory_scope` is `scenario_episodic` when memory is enabled and `none`
    in baseline
- [micro.py](../reverie/backend_server/measurement/micro.py) contains:
  - `memory_reference_rate(...)` — binary mention rate
  - `memory_relevance_per_agent(...)` — **cosine embedding similarity** of
    cited memory reference vs. available recent memories (upgraded from
    Jaccard)
  - `memory_coherence_per_agent(...)` — opportunity-weighted score:
    `0.4 × mention + 0.6 × embedding relevance` (only scored when
    `memory_context_available` is True)
  - threshold banding via `_label_dict(..., "memory_coherence")`

Status:
- `Proxy`

What is still missing:
- human accuracy check (the `memory_coherence` column in
  `human_eval_ratings.csv` captures this; not yet ingested)
- final blended Auto+Human score

Construct-validity note:
- The original scenario-context implementation used
  `persona.get_recent_memories(limit=5)`, which often surfaced memories such
  as `bed is idle`, `desk is idle`, and `<persona> is sleeping`. Those are
  valid world memories, but they are weak evidence for memory coherence in a
  commons-dilemma task.
- The current implementation operationalises memory coherence as appropriate
  use of prior **task interactions**: group demand, pool change, fair-share
  deviation, oversubscription, and which agents requested above or below fair
  share.
- This makes the metric better aligned with the research plan's phrase
  "prior-context references divided by opportunities plus human accuracy
  check."
- This does not award believability merely because relevant memory is present.
  The score still depends on whether the agent cites and uses the available
  task memory accurately. An agent can receive a low memory-coherence score if
  it ignores prior commons outcomes, cites them inaccurately, or reasons in a
  direction inconsistent with them.

Implementation tasks:
- collect and ingest human memory-coherence ratings via `rating_ingestion.py`
- blend human ratings into `memory_coherence_per_agent`

Priority:
- Medium (embedding relevance now implemented; awaits human ratings)

### 3. Planning plausibility

Table 1 requirement:
- **Measurement method:** human rubric, LLM-assisted
- **Type:** Human (LLM-assisted)
- **Scale:** `1–5 rubric`
- **Thresholds:** `>= 4 high; < 2 low`

Current repo coverage:
- [commons_dilemma.py](../reverie/backend_server/scenarios/commons_dilemma.py)
  logs: `plan_reference`, `daily_goals`, `current_activity`,
  `planning_context_available`
- [micro.py](../reverie/backend_server/measurement/micro.py) contains:
  - `planning_plausibility_llm_per_agent(...)` — **LLM-assisted 1–5 rubric**
    judge, sampled at 4 representative entries per persona; normalises score
    to 0–1 (`_llm_planning_plausibility_score`); directly implements the
    Table 1 "Human (LLM-assisted)" method
  - `planning_alignment_per_agent(...)` — cosine embedding alignment of plan
    reference vs. daily goals + current activity (embedding fallback)
  - `planning_plausibility_per_agent(...)` — blends LLM judge (0.5) and
    embedding alignment (0.5) when LLM scores are available
  - `planning_plausibility_rubric(...)` — maps blended 0–1 score → 1–5
  - threshold banding via `_label_dict(..., "planning_plausibility")`

Status:
- `Partial`

What is still missing:
- supplementary human rater ratings (the `planning_plausibility` column in
  `human_eval_ratings.csv` supports this)
- ingestion via `rating_ingestion.py` to produce final blended score

Implementation tasks:
- collect human planning-plausibility ratings from raters
- ingest and blend with the LLM judge scores

Priority:
- Low (LLM judge is the primary automated instrument and is now implemented)

### 4. Response naturalness

Table 1 requirement:
- **Measurement method:** distinction test (human vs. AI) + perplexity
- **Type:** Human + Auto
- **Scale:** binary and continuous `0–1`
- **Threshold:** `> 50% fooled = high`

Current repo coverage:
- [micro.py](../reverie/backend_server/measurement/micro.py) contains:
  - `response_naturalness_llm_per_agent(...)` — **LLM-as-judge distinction
    test** (`_llm_response_naturalness_score`): asks the model to score
    0–1 whether text is indistinguishable from human writing and whether a
    naive reader would be fooled; directly implements the Table 1 method
  - `_heuristic_naturalness(...)` — word-count/sentence/unique-ratio
    heuristic, used as fallback when LLM unavailable
  - `response_naturalness_per_agent(...)` — blends LLM judge (0.6) and
    heuristic (0.4) when LLM scores are available
  - blinded reasoning text exported in `human_eval_packets.jsonl` for human
    rater distinction test
  - threshold banding via `_label_dict(..., "response_naturalness")`

Status:
- `Partial`

What is still missing:
- human rater distinction test results (the `response_naturalness` and
  `believable_yes_no` columns in `human_eval_ratings.csv` support this)
- ingestion via `rating_ingestion.py` to produce final "fooling rate"
- perplexity via LLM log-probs (not implemented; LLM-as-judge is the
  current automated substitute)

Implementation tasks:
- collect human believability/distinction ratings from raters
- compute fooling rate from `believable_yes_no` column
- ingest and blend with the LLM judge score

Priority:
- Low (LLM distinction test is the primary automated instrument and is now
  implemented)

### 5. Composite believability

Table 1 requirement:
- **Measurement method:** weighted average of the four micro sub-scores
- **Type:** Computed
- **Scale:** `0–1 normalised`
- **Thresholds:** `>= 0.7 high; < 0.4 low`

Current repo coverage:
- [micro.py](../reverie/backend_server/measurement/micro.py) contains:
  - `composite_believability_per_agent(...)` — automated weighted composite:
    - 0.30 × behavioural consistency (embedding-based)
    - 0.25 × memory coherence (embedding-based)
    - 0.25 × planning plausibility (LLM judge blended with embedding)
    - 0.20 × response naturalness (LLM judge blended with heuristic)
  - `blend_human_ratings_into_summary(...)` — **final mixed-method blend**:
    - ingests per-agent averaged human ratings (1–5 normalised to 0–1)
    - applies reliability gating (Krippendorff's α < 0.67 → auto-only)
    - produces `composite_believability_final` from blended sub-scores
  - `compute_micro_summary(...)` now accepts `human_ratings`,
    `agent_deblind_map`, `reliability` to trigger the blend inline
  - `_build_agent_deblind_map(trial_dir)` — de-blinds packet IDs back to
    persona names for linkage
  - threshold banding via `_label_dict(..., "composite_believability")`
  - `believability_proxy` backward-compatible alias preserved

Status:
- `Partial`

Scenario-memory impact:
- The scenario-memory fix primarily affects the `memory_coherence`
  sub-score, which contributes 0.25 of the automated composite believability
  score.
- It may indirectly affect `planning_plausibility` because memory and goals
  now refer to the same resource-allocation task, but the composite formula
  itself is unchanged.
- Baseline remains comparable because `memory_context_available` is false and
  `memory_scope` is `none`; memory-enabled conditions are evaluated on whether
  they use prior commons-round memory coherently.
- Therefore, post-fix composite scores should be interpreted as believability
  under a task-relevant episodic-memory operationalisation, not as a test of
  open-ended retrieval from the full Smallville memory stream.

What is still missing:
- actual human ratings: the blend code is complete and waiting on data;
  set `trial_scenario.human_ratings_path` once rating files are returned
- final weighting policy confirmed with supervisors (current weights
  are provisional: 0.50/0.50 auto/human per dimension except response
  naturalness at 0.60/0.40)

Implementation tasks:
- collect human ratings and run `rating_ingestion.load_and_analyse_ratings()`
- verify Krippendorff's α ≥ 0.67 per dimension before using ratings
- set `human_ratings_path` on scenario and re-run to produce final scores
- confirm composite weights with supervisors

Priority:
- High (code complete; blocked only on data collection)

## Macro-level (System)

### 6. Coordination success

Table 1 requirement:
- **Measurement method:** proportion of runs achieving consensus or near-optimal allocation
- **Type:** Auto
- **Scale:** `0–1 proportion`
- **Thresholds:** `>= 0.7 high; < 0.3 low`

Current repo coverage:
- [macro.py](/mnt/shared/Sayedali/Mres_demo/reverie/backend_server/measurement/macro.py:1)
  contains:
  - `coordination_score(...)`
- [experiment_runner.py](/mnt/shared/Sayedali/Mres_demo/reverie/backend_server/experiment_runner.py:1)
  contains:
  - `aggregate_macro_summaries(...)` integration
  - `coordination_success_rate` in condition summaries

Current interpretation:
- the repo now computes both `coordination_score` and boolean
  `coordination_success`
- the current success definition is still scenario-specific and heuristic, so
  it remains a proxy rather than a final cross-scenario standard

Status:
- `Proxy`

What is missing:
- final cross-scenario success definitions
- stronger domain-grounded criteria for "near-optimal" outcomes

Implementation tasks:
- define explicit success criteria per scenario
- compute proportion of successful runs across replications
- add threshold labels

Priority:
- High

### 7. Convergence speed

Table 1 requirement:
- **Measurement method:** rounds to reach coordination or timeout
- **Type:** Auto
- **Scale:** count
- **Threshold:** `<= median = fast`

Current repo coverage:
- [macro.py](/mnt/shared/Sayedali/Mres_demo/reverie/backend_server/measurement/macro.py:1)
  now computes:
  - `convergence_step(...)`
  - `convergence_speed(...)`

Status:
- `Implemented`

What is missing:
- more scenario-specific convergence definitions once additional scenarios are
  implemented

Implementation tasks:
- define “converged” state for each scenario
- log first step meeting convergence criteria
- aggregate across runs

Priority:
- Medium-high

### 8. Emergent role differentiation

Table 1 requirement:
- **Measurement method:** entropy of role distribution plus network analysis
- **Type:** Auto
- **Scale:** continuous vs. random baseline

Current repo coverage:
- [macro.py](/mnt/shared/Sayedali/Mres_demo/reverie/backend_server/measurement/macro.py:1)
  now computes:
  - per-persona role labels
  - role-count distributions
  - entropy-based differentiation summaries

Status:
- `Proxy`

What is missing:
- network-based interaction analysis
- scenario-specific role semantics beyond request strategy

Implementation tasks:
- define observable role categories
- infer role frequencies over time
- compute entropy or differentiation scores

Priority:
- Medium

### 9. Outcome variance

Table 1 requirement:
- **Measurement method:** coefficient of variation across replications
- **Type:** Auto
- **Scale:** `CV ratio`
- **Thresholds:** `<0.2 robust; >0.5 unstable`

Current repo coverage:
- [macro.py](/mnt/shared/Sayedali/Mres_demo/reverie/backend_server/measurement/macro.py:1)
  contains:
  - `aggregate_macro_summaries(...)`
  - coefficient-of-variation style outputs in `outcome_variance`
- [experiment_runner.py](/mnt/shared/Sayedali/Mres_demo/reverie/backend_server/experiment_runner.py:1)
  writes:
  - `condition_summary.json`

Status:
- `Implemented`

What is still worth improving:
- add threshold labels
- expose variance summaries more explicitly in reports/tables

Implementation tasks:
- attach robust/unstable classification bands
- add convenience CSV export

Priority:
- Medium

### 10. Failure traceability

Table 1 requirement:
- **Measurement method:** qualitative coding of coordination breakdowns to
  micro-level causes
- **Type:** Human
- **Scale:** categorical
- **Threshold:** descriptive only

Current repo coverage:
- [macro.py](/mnt/shared/Sayedali/Mres_demo/reverie/backend_server/measurement/macro.py:1)
  now computes:
  - `failure_traceability(...)`
- [experiment_runner.py](/mnt/shared/Sayedali/Mres_demo/reverie/backend_server/experiment_runner.py:1)
  now writes:
  - `failure_traceability.json`
  - human-evaluation bundles for analyst review

Status:
- `Proxy`

What is missing:
- completed qualitative coding by human analysts
- final mapping from coded failures into thesis reporting

Implementation tasks:
- export failure-focused transcript bundles
- capture local context around collapse or coordination failure
- add analyst notes or coding templates

Priority:
- High

## Supplemental Metrics Already Present But Not In Table 1

The current branch also computes several useful supporting metrics that are
not identical to Table 1 but remain valuable:

- `sustainability_score`
- `collapse_step`
- `average_gini`
- `demand_pressure`
- `final_resource_level`

These are especially relevant for the commons dilemma scenario and can support
the macro analysis chapter even if they are not the primary Table 1 metrics.

## Recommended Build Order (Next Steps)

Steps 1–3 are the critical path for thesis data collection.
Steps 4–6 are code improvements that can proceed in parallel.

### Study execution steps (data-dependent)

1. **Collect human ratings** — distribute the exported `human_eval_ratings.csv`
   files to 3–5 raters; the blend code is complete and waiting on this data
2. **Ingest ratings and verify reliability** — run
   `rating_ingestion.load_and_analyse_ratings()` once ratings are returned;
   verify α ≥ 0.67 per dimension; dimensions below threshold are automatically
   gated in the blend step
3. **Trigger blend and produce final scores** — set `human_ratings_path` on
   the scenario object and re-run (or call `blend_human_ratings_into_summary`
   directly); `composite_believability_final` is then the thesis metric
4. **Run full experiment matrix** — 4 conditions × 20 trials ×
   `persona_sample_size=8` on `base_the_ville_n25`; costs ~80 LLM-judge
   calls per trial

### Code improvements (can start immediately)

5. **Implement `information_consensus` scenario** — second coordination
   scenario; maps to the consensus-building framing in §4.4; enables
   cross-scenario generalisability claims
6. **Network analysis for role differentiation** — add interaction-graph
   topology (adjacency matrix, degree centrality, clustering coefficient)
   to `macro.py` alongside the existing entropy component; this is the only
   remaining Table 1 code gap
7. **Refine coordination success criteria** — define scenario-specific
   "near-optimal" thresholds beyond the commons-dilemma heuristic once a
   second scenario is live
8. **Qualitative failure coding** — analyst coding of exported
   `failure_traceability.json` bundles; no further code changes required

## Bottom-Line Assessment

If judged strictly against Table 1 as of 2026-04-30 (post mixed-method blend pass):

- `Implemented`: 2 out of 10 (convergence speed, outcome variance)
- `Partial`: 3 out of 10 (planning plausibility — LLM judge done; response
  naturalness — LLM distinction test done; composite believability — blend
  code complete, awaiting data)
- `Proxy`: 5 out of 10 (automated components upgraded; human data pending)
- `Missing`: 0 out of 10

The repo now implements the **full mixed-method pipeline** end to end. The
only remaining gap is human-data collection and execution of the experiment
matrix.
