# Discussion Notes — 2026-05-29

**Project:** Validation of Generative Agents in Agent-Based Models — Linking Individual Believability to Emergent Group Coordination
**Author:** Sayedali Mohseni (MRes, Macquarie University)
**Topic of session:** Empirical validity of the code, the memory module design, the deterministic reflection problem, the generative-agent framing, and the decision to add an LLM-reflection condition.

---

## 1. Is the empirical part academically valid?

Verdict from direct code inspection: **largely yes.** The experiment is real, not cosmetic.

- The four conditions genuinely change the LLM input. The `use_memory` / `use_planning` / `use_reflection` toggles in `experiment_conditions.py` are actually consumed: `persona.py` exposes them via `uses_memory()` etc., and `commons_dilemma._ask_agent` rebuilds the prompt per condition. Baseline agents are explicitly told not to draw on memory or plans; memory conditions get injected episodic context. So C1–C4 receive structurally different prompts — the ablation is genuine.
- The statistics are legitimate. `experiment_analysis.py` uses real `scipy.stats` (`spearmanr`, `mannwhitneyu`, `kruskal`) plus a hand-rolled OLS with computed p-values. Nothing is hardcoded or faked.
- The measurement formulas match the documentation. `memory_coherence_per_agent` implements exactly `opportunity × (0.4·mention + 0.6·embedding_relevance)`; behavioural consistency, planning alignment, and naturalness use real cosine-embedding similarity.

**Conclusion:** the pipeline, ablation, and statistical analysis are sound. The existing 120 trials (80 CD + 40 IC) are valid data.

---

## 2. What was actually changed vs. stock Park et al.

It is **not** just the memory module. Changes fall into three categories:

1. **A large new experimental layer built on top of Park (the real contribution).**
   New files that did not exist in Park's codebase: `experiment_runner.py`, `experiment_conditions.py`, `experiment_analysis.py`, the whole `scenarios/` folder (commons_dilemma, information_consensus, …), the whole `measurement/` folder (micro.py, macro.py), `llm_judge.py`, `human_evaluation.py`, `rating_ingestion.py`, `preflight.py`. Thousands of lines. This is a research harness, not a memory edit.

2. **Robustness / bug-fix edits to Park's core cognitive modules — behaviour-preserving.**
   The diffs to `plan.py`, `perceive.py`, `execute.py` are almost entirely defensive null guards (`run_gpt_prompt_x(...)[0]` → `result[0] if result else <fallback>`). These fix crashes; they do not change the cognitive algorithm. The one deliberate semantic change: `perceive.py` gained a `store_to_memory` flag so the baseline condition does not silently accumulate episodic traces — a legitimate ablation hook.

3. **`converse.py` switched from `agent_chat_v1` to `agent_chat_v2`** — this is Park's own v1/v2 and is largely irrelevant to the scenarios, which bypass Smallville conversation and answer the scenario prompt directly.

**Important nuance about "memory":** Park's associative-memory stream (`a_mem`, `retrieve.py`) was *not* rewritten — it was essentially untouched (a one-line comment in `retrieve.py`). In the scenarios it is **bypassed**, and a parallel, bespoke `scenario_memories` dict is used instead.

---

## 3. How the scenario memory works — and is it academically defensible?

### How it works (commons_dilemma.py)
- `scenario_memories` is a per-persona Python dict, initialised in `setup()`.
- After each round, `_record_scenario_memories()` writes **templated** episodic strings per agent: group demand vs. replenishment, pool change, coordination status, the agent's own request vs. fair share, and peer behaviour (who was above/below fair share).
- It keeps only the last 20 strings per agent (`[-20:]`); `_get_scenario_memories()` returns the last 5 into the prompt.
- It is **scenario-local** (within a single trial), **templated** (fixed sentence formats), and has **no importance weighting, no embedding retrieval, no decay** — unlike Park's retrieval (recency × importance × relevance).

### Is this correct and academic? **Yes — as a deliberate experimental-control choice, not as a flaw.**
This is the key reframing. A controlled experiment *wants* to strip away uncontrolled variables. Park's full memory stream would inject importance-weighted autobiographical recall, world events, and retrieval noise — all confounds for a clean micro→macro test. Using a controlled, task-relevant episodic memory:
- **isolates** the variable of interest (does memory *context* affect coordination?),
- **improves internal validity** (every agent in a condition sees memory built the same deterministic way),
- and was also chosen for practical **resource/cost control** (a legitimate and common constraint).

This is a standard and accepted move in agent-based modelling and in controlled LLM-agent studies. It must simply be **described accurately**: state that the study uses a *controlled scenario-level episodic memory* in place of Park's full associative stream, and explain why (isolation + internal validity + cost). Framed this way it is the *stronger* methodological choice for the research question, not a weakness.

**Action:** do **not** revert memory and do **not** rerun for the memory module. The only fix needed is one honest sentence in the methods chapter.

---

## 4. The reflection problem (the one genuine mismatch)

- In the original `full` (C4) condition, "reflection" is **three hardcoded if/else strings** in `_record_scenario_memories` — a deterministic rule, not an LLM operation.
- Park's reflection is, by definition, an **LLM synthesis** of memories into higher-order insight.
- This creates a **claim-vs-mechanism mismatch**: the headline finding "the reflection module is the critical component (10% → 70% jump)" describes a mechanism the code does not implement. A code-reading reviewer will flag this.
- This is also why the data showed "only ~2 unique reflection strings across 100 steps" — by construction there are only three possible strings.

### Two ways to resolve (neither requires touching memory)
- **Low-effort / no rerun — relabel.** Call the C3→C4 module what it is: a *"reflective feedback cue"* or *"normative feedback signal."* The finding becomes "injecting a deterministic reflective cue produces a categorical coordination jump." True to the code; costs a few sentences.
- **Higher-effort / targeted rerun — make reflection a real LLM call** and rerun only the affected condition. Keeps the strong "reflection matters" claim with a faithful, generative mechanism. **This is the option we chose to build (see §6).**

---

## 5. Are these still "generative agents"? (framing for the micro–macro claim)

Honest position: the agents are a **reduced / partial instantiation** of the Park generative-agent architecture.

- **Still generative at the core:** every decision is an LLM generation conditioned on injected episodic memory + persona identity. The planning module is genuinely LLM-generative. So the root claim is not false.
- **Memory is simplified** (controlled episodic recall, not the full associative stream) — a substitution within the architecture.
- **Reflection (original C4) was not generative** — it was a rule. This is the one part that breaks the strict Park definition.

**Does the micro–macro coordination claim survive? Yes**, provided two framing moves:
1. Describe the agents as a **configurable generative-agent architecture based on Park et al.**, with memory and reflection operationalised as controlled, scenario-level modules to enable a clean ablation. Disclose the simplifications.
2. Name the conditions for what they *are*. Either relabel the deterministic reflection honestly, or make it genuinely generative (chosen). The GABM literature (e.g. the Gao et al. LLM-ABM survey) covers LLM-driven agents broadly, not only exact Park replicas, so the work sits inside the accepted GABM umbrella.

The strongest finding — **planning plausibility predicts coordination (β = 0.645, p = 0.001)** — rests on a genuinely LLM-generative module and does not depend on any of these caveats.

---

## 6. Decision: add an LLM-reflection condition and rerun (targeted)

**Decision:** add a new condition where reflection is produced by a real LLM call, and rerun **only that condition** for the **Commons Dilemma** (where the fine-grained statistics live), keeping everything else frozen.

### Why it is worth doing
- Converts the most attackable result into a defensible one.
- Makes C4-equivalent a faithful generative-agent condition.
- Removes the "are these even generative agents?" objection at its root.

### Scope and guardrails (decided in session)
- Rerun **only the new condition**, CD only (not all 120 trials).
- **Freeze everything else**: same generator model, same prompts, same scoring code, same seeds. The new condition must differ from the original `full` **only** in the reflection function.
- **Commit to whatever the rerun shows.** Genuine reflection may make the jump larger, smaller, or noisier. If it is weaker, that is a *more* honest and still-interesting finding — but the headline sentence gets rewritten. Do not rerun if attached to the 70% number; relabel instead.
- Timeline is comfortable: project is ~6–8 weeks ahead, so the ~1 week + API cost is affordable.

### Open items to confirm before treating the cheap rerun as clean
- Is the rest of the pipeline frozen (same model, prompts, seeds, scoring) as when C1–C3 were run?
- Are the original per-trial random seeds recorded, so the new condition differs from the old `full` **only** in the reflection function?
  - If both yes → the targeted rerun is a clean comparison.
  - If either no → reruns of the compared conditions are also needed to keep the comparison fair.

---

## 7. What was implemented this session

- New condition `full_llm_reflection` added to `experiment_conditions.py` (new field `use_llm_reflection`, default `False` so all existing conditions are byte-for-byte unchanged).
- `persona.uses_llm_reflection()` accessor added.
- `commons_dilemma.py`: reflection generation now branches — `full` keeps the deterministic rule (`_deterministic_reflection`, original strings preserved); `full_llm_reflection` calls `_generate_llm_reflection`, an LLM synthesis over the agent's last 5 episodic memories, with automatic fallback to the deterministic rule on any failure.
- Verified: `full` output is unchanged; `full_llm_reflection` uses the LLM output; LLM failure falls back correctly.

See `docs/RUNNING_LLM_REFLECTION_CONDITION.md` for how to run it.

---

## 8. Outstanding writing tasks (no code needed)

- Methods paragraph: frame scenario memory as deliberate controlled episodic memory (isolation + internal validity + cost), not a limitation.
- Methods paragraph: describe agents as a controlled/simplified instantiation of the Park architecture; disclose the two simplifications.
- After the rerun: rewrite the reflection finding to reflect the LLM-reflection results (whatever they are), and report `full` (deterministic) vs `full_llm_reflection` (generative) as a comparison.
- Reconcile the H1 statistic discrepancy across docs (ρ=0.41 in CONTRIBUTION_ASSESSMENT vs ρ=0.549 CD / 0.750 IC in the summary).

---

## 9. Hypothesis results vs. documentation — verification (this session)

Read the actual `experiment_analysis.py` output (`hypothesis_report.txt`) for the 80-trial CD set and the 40-trial IC v3 set and compared against the documentation. **Every headline number matches.** The documentation is an accurate report of the results, not an embellishment.

| Hypothesis | CD (n=80) | IC v3 (n=40) | Matches docs? |
|---|---|---|---|
| H1 believability→coordination | SUPPORTED ρ=+0.549, p<0.0001 | SUPPORTED ρ=+0.750, p<0.0001 | Yes |
| H2 believability threshold | SUPPORTED, threshold=0.363 | SUPPORTED, threshold=0.389 | Yes |
| H3 monotone C1<C2<C3<C4 | SUPPORTED (KW H=68.9; C3→C4 p=0.0015) | NOT supported (C3→C4 ↓, p=0.647) | Yes ("partially supported") |
| H4 memory+consistency top predictors | NOT supported (planning_plausibility β=+0.645, p=0.0012) | SUPPORTED (memory_coherence β=+1.22, p<0.0001) | Yes ("cross-scenario divergence") |

Caveats made visible by the reports (carry into the writing):
- CD OLS **R²=0.264** — believability sub-dimensions explain ~26% of coordination variance. Real but modest; do not oversell.
- IC OLS **R²=0.9998** — too perfect; reflects the near-zero-variance / effective-n=1 problem (C2–C4 converge identically). Treat IC's H4 "support" as weak binary evidence only.
- The "reflection is the critical module" line is an *interpretation* of the C3→C4 jump; the jump is real (p=0.0015) but the code's reflection is deterministic — hence the `full_llm_reflection` rerun.
- Data-fix: the `ρ=0.41` figure in `CONTRIBUTION_ASSESSMENT.md` is stale/incorrect; the real H1 value is ρ=0.549 (CD). Correct it.

---

## 10. Pilot rating exercise (LLM-as-rater dry run) — this session

Rated a reproducible random sample of 12 full-condition CD packets (4 each early/middle/late, seed 20260529) against `HUMAN_RATER_TRAINING_GUIDE.md`. Output saved to `experiment_results_cd_primary/commons_dilemma/full/_pilot_ai_ratings/pilot_ai_ratings.csv` with `rater_id = ai_pilot_rater`.

**This is NOT human evaluation** and cannot be reported as such — an LLM rating LLM-generated text shares the system's blind spots and is not the independent human judgment the thesis needs. It is a *pilot/instrument check* only.

Findings:
- Composite (thesis weights) ≈ **0.632**, close to the documented automated 0.682 — consistent, slightly lower as the limitation note predicts.
- **Confabulation confirmed:** 3 of 4 step-0 packets cited a memory with an empty memory tab → scored 1 per rubric. Directly confirms documented limitation #4.
- **Planning plausibility did not discriminate** — flat 3 across all 12 (every plan_reference generic "this aligns with my goal of…"). Yellow flag: human raters may also fail to discriminate this dimension, which could weaken the human-validated version of the H4 (planning) claim.
- **Self-consistency check (re-rated cold):** 46/48 dimension-scores identical; MC and PP 12/12 identical; believable y/n 12/12. The two drifts were both ±1 on the subjective dimensions (BC, RN). Interpretation: the rubric is highly *reliable* on rule-based dimensions, but high reliability ≠ validity — an LLM can be consistently biased. Reinforces that independent human raters are still required.

---

## 11. Dual-level validation framework — assessment (this session)

**Verdict: good, academic, and publishable — as a methodological vehicle inside an empirical paper, not as a standalone "novel framework" paper.** (Consistent with CONTRIBUTION_ASSESSMENT and THESIS_METRICS_ASSESSMENT.)

Strengths:
- Theoretically principled micro/macro split — operationalises the micro–macro problem in ABM (Windrum et al. 2007) with scenario theory (Hardin, Ostrom; Condorcet, Bikhchandani).
- Clean extensible design (`BaseScenario`), separated levels, full raw+summary export.
- Rigorous measurement hygiene: blinded human-eval pipeline, Krippendorff's α, reliability gating, judge–generator independence (GPT generates, Claude judges).
- Works empirically — produced significant, interpretable, and surprising (H4-reversing) results.

What stops it being a standalone framework paper:
- Extension of existing theory to GABMs, not a new theory.
- Validated on one platform only (Park et al.); "architecture-agnostic" is asserted, not demonstrated.
- Micro metrics are automated proxies; human eval pending.
- No comparative framework baseline; one scenario (CD) carries the fine-grained statistics.

**Framing tension to fix:** `README-research-scenarios.md` says "The full Park et al. (2023) memory and reflection architecture is preserved." This overstates fidelity (scenarios bypass Park's associative memory; reflection is deterministic) and will be contradicted by anyone reading the code. Replace with: "built on the Park et al. architecture, with memory and reflection operationalised as controlled scenario-level modules." This is the single most important credibility fix.

Path to a standalone framework paper (post-MRes): (a) validate on a second platform (AutoGen/CAMEL); (b) complete the human evaluation establishing that proxies track human judgment.

### Draft "scope and contribution" paragraph (framework section)

> We present a dual-level validation framework for generative agent-based models (GABMs) that jointly measures individual-agent believability (micro) and emergent group coordination (macro), and tests whether the former predicts the latter. The framework is not a new agent architecture; it is an evaluation methodology that operationalises the micro–macro problem in agent-based modelling (Windrum et al., 2007) for LLM-driven agents. It comprises four automated micro-level proxy metrics (behavioural consistency, memory coherence, planning plausibility, response naturalness) combined into a composite believability score, a suite of macro-level coordination metrics derived directly from simulation state (sustainability, coordination success, demand pressure, inequality, convergence, role differentiation), a blinded human-evaluation protocol with inter-rater reliability gating, and a pre-registered set of hypotheses (H1–H4) tested with non-parametric statistics and OLS regression. The framework is architecture-agnostic by design and is instantiated here on the Park et al. (2023) generative-agent platform — the canonical and most widely used open GABM — across two structurally distinct coordination scenarios (a commons dilemma and an information-consensus task). Within this instantiation, memory and reflection are realised as controlled, scenario-level modules rather than the platform's full associative-memory stream, a deliberate choice that isolates the cognitive variable under test and strengthens internal validity. We position the framework as the methodological vehicle for the empirical contributions of this work rather than as a standalone proposal: its value is demonstrated by the interpretable and partly counter-hypothesised findings it produces, and its generalisation to additional platforms and full human-grounded validation are identified as future work.

---

## 12. Fixing the five gaps that stop it being a standalone framework paper

Each gap from §11 is fixable; they differ greatly in cost. "Fixable" ≠ "worth doing now." Split by timeline below.

| # | Gap | Fix | Cost | When |
|---|---|---|---|---|
| 1 | Extension, not new theory | Don't chase new theory (PhD-scale). Instead **formalise one falsifiable proposition** out of the synthesis — e.g. "micro believability is necessary-but-not-sufficient for macro coordination, with an empirical threshold" (H2, 0.363). Turns measurement into a small theoretical claim. | Writing only | Now (partial) |
| 2 | One platform; "architecture-agnostic" asserted not shown | **Instantiate the framework on a second GABM platform** (AutoGen / CAMEL / AgentVerse), same commons-dilemma scenario. Even a reduced replication converts "agnostic by design" → "agnostic, demonstrated." **Highest-leverage fix; the real gate.** | Weeks of engineering | Post-MRes |
| 3 | Micro metrics unvalidated proxies; human eval not done | The planned **human evaluation**: show automated believability correlates with human ratings (Krippendorff α + blend). Converts proxies → validated proxies. | Planned Jul–Aug study + HREC | Now (thesis-critical) |
| 4 | No comparative baseline | (a) **Reframe:** no prior dual-level GABM framework exists → position this as the *first* baseline others compare against (absence becomes a contribution). (b) Optional: build a naive baseline (random / single-dimension scorer) and show yours discriminates better. | (a) a paragraph; (b) ~1 day | (a) now; (b) if pushed |
| 5 | One scenario (CD) carries the stats; IC only binary | Implement a **third scenario with graded within-condition variance** (`task_assignment` stub exists). IC's zero variance is by-design, so a graded scenario is needed to spread the fine-grained statistics beyond CD. | Moderate engineering | Post-MRes / stretch |

### Prioritisation
- **For the thesis + AAMAS/JASSS paper (now):** do #3 (human eval, already planned) and #4a (reframe missing baseline as "first-of-kind"). Optionally sharpen #1 (formalise the threshold proposition). Enough to make the framework defensible as the *method* behind a strong empirical paper.
- **For a standalone framework paper (post-MRes):** do #2 (second platform) and #5 (third high-variance scenario). These are the genuine gate — no shortcut; a framework paper must *demonstrate* generality, not assert it.

### Zero-cost reframe (do immediately)
Stop trying to clear the "novel framework" bar for the current paper. Present the framework as the rigorous method that produced counter-hypothesised findings; then the five gaps become a clean, credible **future-work** section rather than weaknesses. Reviewers reward honest scoping more than they punish "extension rather than invention."

### Two writing fixes available now (no new experiments)
- **Formalised H2 threshold proposition** (fix #1 partial) — to draft.
- **"First-of-kind / no comparative baseline exists" paragraph** (fix #4a) — to draft.

---

## 13. LLM-reflection rerun — trial 0 results (this session)

First trial of `full_llm_reflection` finished (trial 1 running). **n=1 — read as a signal, not a result; need all 20 trials for success-rate comparison vs original `full` (70%).**

Macro (trial 0):
- coordination_success = **True**, convergence at **step 1**, coordination_score **0.99**
- sustainability **0.976** (vs ~0.931 documented deterministic full)
- demand_pressure **0.98**, Gini **0.003**

Mechanism check (the point of the rerun):
- **77 unique LLM-generated reflections, 0 fallbacks** — vs only 2–3 unique strings in the deterministic `full`. Reflection is now genuinely generative.
- **Caveat — semantic convergence:** the 77 are lexically varied but nearly all express one insight ("keep aligning requests with fair share to maintain group harmony/sustainability"). Mechanism is fixed; content converges once coordination is stable. Describe accurately: generative and lexically varied, NOT semantically diverse. The convergence is partly caused by the heavy task-scoping in our prompt (see §14).

Micro (trial 0, within-trial noise): composite 0.650; planning_plausibility low at 0.432 — wait for full set.

---

## 14. How our reflection relates to Park et al. — NOT identical (this session)

Our new reflection is a **simplified, single-stage realization of Park-style reflection**, not Park's mechanism. Captures the core idea (LLM synthesises recent experience into a higher-order, forward-looking insight that feeds back into behaviour) but omits several Park components.

### Prompt comparison

**Park (two prompts, run as a pipeline):**
1. `generate_focal_pt_v1.txt`: "Given only the information above, what are [N] most salient high-level questions we can answer about the subjects grounded in the statements?"
2. `insight_and_evidence_v1.txt`: "What high-level insights can you infer from the above statements? (example format: insight (because of 1, 5, 3))"

**Ours (one prompt, `commons_dilemma._generate_llm_reflection`):**
> "You are [name], reflecting privately after a round… Your recent observations: [last 5 episodic memories]. This round you requested X credits (fair share Y), and [stayed within / exceeded the limit]. In ONE short first-person sentence, state the single most useful lesson you draw from these observations to guide how much you should request next round. Do not restate the numbers; express an insight about your own behaviour or the group's coordination."

### Concrete differences

| Aspect | Park et al. | Ours |
|---|---|---|
| LLM calls | Two-stage (questions → insights) | Single stage (memories → insight) |
| Focal-question step | Yes | No |
| Evidence grounding | Each insight must cite source memories "(because of 1,5,3)" | Not required |
| Voice / scope | Third-person, open-ended (any salient subject) | First-person, task-scoped to the resource decision |
| Output size | N insights (default 5) | One sentence |
| Trigger | Fires only when accumulated memory importance crosses threshold | Every round, unconditionally |
| Input memory | Full associative stream (importance×recency×relevance retrieval) | Controlled templated `scenario_memories` (last 5) |
| Write-back | Insights become new retrievable memory nodes → recursive reflection | Stored in separate list, not re-embedded; no recursion |

### Recommendation (decided): KEEP the controlled single-stage version

Do **not** chase Park-identical reflection. Reasons:
- Park's trigger + focal-question + recursive write-back reintroduce exactly the confounds (variable reflection timing, extra stochastic call, compounding recursion) the controlled ablation was built to exclude — adopting them *weakens* internal validity here.
- It would also break the clean comparison against existing `full` data and roughly double reflection API cost.
- Full Park reflection is a **post-MRes** research direction, not a thesis fix.

Middle fallback (only if a supervisor pushes on reflection *diversity*): one surgical prompt change — add Park's evidence-citation requirement and loosen the task-scoping — keeps it a single call but yields more evidence-grounded, varied insights. Requires one more rerun of this condition.

### Ready-to-use methods sentences (no rerun needed)

> Reflection was implemented as a single LLM call that synthesises each agent's recent episodic observations into one forward-looking, first-person insight, which is then provided as context for subsequent decisions. This is a simplified, controlled realisation of the reflection mechanism of Park et al. (2023): it preserves the essential idea of LLM-generated synthesis of experience feeding back into behaviour, but omits their focal-question stage, importance-based triggering, explicit evidence citation, and recursive write-back of insights into the retrievable memory stream. The simplification is deliberate — it holds reflection timing and structure constant across agents and trials, isolating the contribution of reflective synthesis for the ablation rather than confounding it with variable trigger dynamics and recursive memory growth.

---

## 15. Over-steering / trivial-convergence check (this session)

Checked whether the LLM reflection trivializes the task by leaking the answer. Traced trial 0 step-by-step (group request totals + per-agent reasoning + reflections seen).

**No answer-leakage (good).** Reflections express a *principle* ("align my requests closely with the fair share / the group's capacity to avoid oversubscribing"), never the *number* (6). Agents infer the specific amount themselves from the situation context (which legitimately states fair share ≈ 6.25). So the mechanism is honest — reflection is not handing agents the solution.

**But: trivial, rigid convergence (caveat).** Trajectory in trial 0:
- Step 0 (no reflection yet): chaotic — total=146, individual requests [20,10,50,20,20,10,10,6].
- Step 1 onward (after one reflection round): every agent locks to exactly **6**, total=**48**, and it **never changes for the remaining 99 steps** (dead-flat 6/6/6/6…).

Implications:
- **Strengthens** the headline "reflection enables coordination" — the step-0 chaos → step-1 lockstep contrast is stark and directly attributable to the reflection signal. Cleaner than the deterministic version.
- **Weakens** any claim of *rich / emergent* coordination dynamics. This is closer to **parallel individual compliance** (every agent independently receives the same normative nudge and complies instantly) than to emergent group negotiation. A reviewer will notice the dead-flat trace and ask whether anything emergent is happening after step 1.
- **Statistical consequence:** near-zero within-trial variance in this condition from step 1 (identical decisions) → micro believability sub-scores nearly constant → limited regression signal from this condition, same limitation that hampered IC (effective n≈1 within a trial).

Recommended framing: *"LLM reflection produced rapid, near-deterministic convergence to fair-share compliance,"* NOT "gradual emergent coordination." Do not oversell as rich emergent behaviour.

Open check for the full run: does the lockstep hold across all 20 trials, or do some show messier dynamics? The messier trials are scientifically more valuable (real coordination process to study). Quantified by the new rigidity metric in `compare_reflection_conditions.py` (§ below).

Added to `compare_reflection_conditions.py`: `flat_from_step` (first step after which the group total never changes) and `ever_perturbed_after_flat` per trial, aggregated per condition.

---

## 16. What to do when the rerun finishes (one command)

The `full_llm_reflection` experiment runs on its own. **No action needed until it finishes** (20 trials).

Check progress anytime:
```bash
ls experiment_results_cd_llm_reflection/commons_dilemma/full_llm_reflection/ | grep trial | wc -l
```
When it prints **20**, the run is done.

Then run **one command** (from `reverie/backend_server`):
```bash
python finalize_llm_reflection.py
```
This: (1) checks the trial count and warns if < 20, (2) prints the deterministic-vs-LLM comparison incl. rigidity metrics, (3) runs the H1–H4 analysis on the new results dir.

**Caveat about the analysis step:** H1/H3/H4 compare *across* conditions. The `experiment_results_cd_llm_reflection/` dir contains only `full_llm_reflection`, so `run_analysis` on it alone cannot do a real cross-condition test. Two options:
- If you only want the **deterministic-vs-LLM-reflection contrast** (the actual question this rerun answers) → the comparison output is enough; no further action.
- If you want the new condition **folded into full H1–H4** → run a five-condition matrix (baseline, memory, memory_planning, full, full_llm_reflection) into one fresh `output_dir`, then `run_analysis` on that dir. This means re-running the other four conditions too (cost + must freeze model/seeds), so only do it if a supervisor wants the unified hypothesis tests.

Scripts created this session (in `reverie/backend_server/`): `compare_reflection_conditions.py`, `finalize_llm_reflection.py`.

---

## 17. Justification for the experiment numbers (this session)

### Human-eval packets: why 24 per trial
Not an arbitrary target — it falls out of the sampling design in `human_evaluation.py`:

- `_sample_entries_for_persona` samples **3 time points per agent**: first step, middle step, last step (`indices = {0, len//2, len-1}`).
- The study uses **8 agents** (`persona_sample_size=8`).
- 3 × 8 = **24 packets per trial.**
- If a trial has a traceable failure, a 4th "critical-step" packet may be added for the affected agent, so some trials carry a couple extra; baseline design is 24.

**Why 3 time points (early/middle/late):** agent behaviour changes over a run — early steps have no accumulated memory (where confabulation lives), middle steps are where coordination forms, late steps show whether it stabilised. Rating only one phase would bias the believability estimate (e.g. miss early confabulation, over-state memory coherence). Three points capture the trajectory cheaply; rating all 100 steps would be 800 packets/trial — infeasible for humans. The protocol explicitly requires sampling "across early, middle, and late steps."

**Why 8 agents:** deterministic sub-sample of 8 from the 25-agent Smallville world (seed 42). Sits in the documented "5–10 agent study" range — large enough for genuine group dynamics and a meaningful commons dilemma (fair share = 50/8 ≈ 6.25), small enough to keep per-trial LLM cost and rating burden manageable.

**How it scales to the human-eval scope:** plan is ~96 CD packets ≈ 24 × 4 conditions (or a few representative trials). The 24-per-trial structure is what lets the protocol's four coverage requirements all be met in a small, human-feasible sample: across conditions (C1–C4), across successful AND failed runs, across early/middle/late steps, across multiple personas.

**Honest caveat for the thesis:** 3 points/agent is a *coarse* trajectory sample. Defensible as a deliberate feasibility trade-off, but state it as such — you sample the trajectory, not exhaustively rate it; the early/middle/late split is the justification that 3 points still cover the behaviourally distinct phases.

### Other key experiment numbers (for completeness)
- **20 trials × 4 conditions = 80 CD trials; 10 × 4 = 40 IC trials.** Independent replications per condition; 20 gives enough spread to compute non-parametric tests and a success *rate* rather than a single outcome. IC uses 10 because its conditions converge near-identically (low variance → fewer replications needed; the limitation is the near-zero variance itself, not the count).
- **100 steps per CD trial / 30 per IC trial.** CD needs a long horizon for sustained depletion/restraint dynamics and the ≥5-consecutive-step success window; IC converges by step 5–6 in memory+ conditions, so 30 is ample.
- **Fair share = replenishment / n_agents = 50/8 ≈ 6.25.** Defines the cooperation benchmark used throughout micro/macro metrics.
- **Success criteria:** CD = ≥5 consecutive steps with total requests ≤ replenishment at pool ≥70%; IC = ≥6/8 agents on correct option for 5 consecutive steps. Both encode "sustained" coordination, not a one-off lucky step.

### Draft methods sentence (sampling design)
> For human evaluation, decision packets were sampled at three behaviourally distinct points in each trial — the first, middle, and final step — for each of the eight agents, yielding 24 packets per trial (with an additional packet at the failure-critical step where applicable). The three-point scheme was chosen as a feasibility-constrained trajectory sample: it captures the early phase (before episodic memory accumulates, where memory confabulation is observable), the middle phase (during which coordination forms), and the late phase (in which coordination either stabilises or breaks down), while keeping the per-trial rating burden tractable relative to the 100-step run. Packets were sampled across all four architecture conditions and across both successful and failed runs, consistent with the human-evaluation protocol's coverage requirements.

---

## 18. Interim snapshot — 5 of 20 LLM-reflection trials complete (this session)

Run was interrupted (internet drop) and resumed successfully — the runner skips trials that have a `run_manifest.json` (written last), so completed trials are not re-run and interrupted ones are cleanly redone. trial_5 was mid-run at time of snapshot.

**Comparison at n=5 (LLM) vs n=20 (deterministic):**

| metric | full (determ.) | full_llm_reflection |
|---|---|---|
| trials | 20 | 5 |
| success rate | 70% (14/20) | 100% (5/5) |
| mean sustainability | 0.931 | 0.985 |
| mean demand pressure | 0.998 | 0.976 |
| mean coordination score | 0.709 | 0.984 |
| mean Gini | 0.026 | 0.004 |
| mean convergence step | 11.7 | 1.6 |
| unique reflections/trial | 2.9 | 83.2 |
| of which LLM-generated | 0.0 | 83.2 |
| trials with fallback | 20 | 0 |
| mean flat-from step | 25.7 | 5.2 |
| perturbed after flat | 2/20 | 0/5 |

Per-trial (complete): all 5 success; flat-from steps = 1, 6, 5, 5, 9; all settle at total=48 (= 8 × fair-share 6); none perturb after flat.

**Both findings are strengthening, not softening, as n grows:**
- Headline holds — genuine LLM reflection → near-perfect coordination with a faithful mechanism (83 unique reflections/trial, 0 fallbacks across all 5).
- Caveat holds — rigid, rapid *compliance*, not emergent negotiation: every trial locks to a constant 48 within ~5 steps and never perturbs. Near-zero within-trial variance → will flatten micro believability sub-scores and limit regression signal (same effective-n≈1 issue as IC).

**Cautions before quoting:** still only 5 trials — wait for 20 before reporting a success rate vs the documented 70%. The uniform, very fast convergence deserves one honest line: a strong reflective "stick to fair share" signal makes the coordination problem easy, which is itself a finding about signal strength, not just agent capability.

**Next:** when `ls …/full_llm_reflection/*/run_manifest.json | wc -l` = 20, run `python finalize_llm_reflection.py`.

---

## 19. Net status after this session

- Empirical pipeline, statistics, and ablation: **valid**; documentation **accurately reports** the results.
- Memory module: **sound controlled-design choice**, not a bug — no rerun needed; describe accurately.
- Reflection: deterministic in original `full`; new `full_llm_reflection` condition implemented and verified for a targeted rerun.
- Framework: **publishable as method-in-service-of-findings**; one fidelity overstatement to correct in the README.
- Human evaluation: still required for the thesis (believability is the central construct); pilot done as instrument check only; real raters + HREC outstanding.
