# Implementation Plan: H5–H7 Analysis + P1 Design
**Written:** 2026-06-08  
**Purpose:** Self-contained execution reference for completing the analytical pipeline.  
**Status at writing:** Data collection complete. `experiment_analysis.py` covers H1–H4 only.

---

## Codebase state at plan-writing time

### Data directories (all under `reverie/backend_server/`)

| Directory | Scenario | Conditions | Trials | Use |
|-----------|----------|------------|--------|-----|
| `experiment_results_cd_primary/` | CD | baseline, memory, memory_planning, full | 4×20=80 | Primary CD |
| `experiment_results_ic_primary/` | IC | baseline, memory, memory_planning, full | 4×10=40 | Primary IC |
| `experiment_results_ic_llm_reflection/` | IC | full_llm_reflection | 10 | IC LLM reflection |
| `experiment_results_cd_llm_reflection/` | CD | full_llm_reflection | 10 | CD LLM reflection |
| `experiment_results_cd_llm_reflection/` | CD | full_llm_reflection | 10 | FAULTY — reference only |

### Key file structures (per trial directory)

**`micro_summary.json`** — aggregated per-agent scores (dict of dicts)
```json
{
  "composite_believability": {"Abigail Chen": 0.682, ...},
  "behavioural_consistency": {"Abigail Chen": 0.71, ...},
  "memory_coherence":        {"Abigail Chen": 0.64, ...},
  "planning_plausibility":   {"Abigail Chen": 0.69, ...},
  "response_naturalness":    {"Abigail Chen": 0.67, ...}
}
```

**`macro_summary.json`** — group-level outcomes
```json
{
  "coordination_success": true,
  "coordination_score":   0.833,
  "sustainability_score": 0.931,
  "collapse_step":        null,
  "average_gini":         0.026,
  "demand_pressure":      0.998,
  "convergence_step":     3,
  "convergence_speed":    1,
  "total_steps":          100
}
```

**`micro_log.json`** — one entry per agent per step; reflection strings live here
```json
{
  "step": 5,
  "persona": "Abigail Chen",
  "scenario_reflections": ["Requesting at or below fair share helped..."],
  "composite_believability": 0.68,
  ...
}
```

### Key source files

- `experiment_analysis.py` — 776 lines; `load_trials()` reads micro+macro summaries into flat records; `run_analysis()` runs H1–H4 and writes `hypothesis_report.json/txt` + `feature_table.csv`
- `experiment_conditions.py` — defines 5 `ExperimentalCondition` dataclasses in `CONDITIONS` dict; add new ones here for P1
- `scenarios/commons_dilemma.py` — `_generate_llm_reflection()` and `_deterministic_reflection()`
- `scenarios/information_consensus.py` — same

### Known discrepancy to fix first
The thesis reframing documents say **"two unique reflection strings"** for the `full` condition. Actual data: **3 unique strings** (the third appears in ~4% of cases as a corrective when the group overshoots). Must fix in both:
- `reframing my reseach/Abstract_Intro_RQ_Rewrite.md` — abstract paragraph + H6 row in hypothesis table
- `reframing my reseach/Contributions_Section_Draft.md` — C3 paragraph

Correct wording: "three unique reflection strings, of which two account for 95.8% of all instances"

---

## Phase 0 — Text fix (no code, ~5 min)

**Files to edit:**
1. `reframing my reseach/Abstract_Intro_RQ_Rewrite.md`
   - Abstract: change "only two unique reflection strings are generated" → "only three unique reflection strings are generated (two accounting for 95.8% of all instances)"
   - H6 row: change "saturation=2 strings" → "saturation=3 strings (two dominant)"

2. `reframing my reseach/Contributions_Section_Draft.md`
   - C3 paragraph: change "only two unique reflection strings are generated across all 100 steps" → "only three unique reflection strings are generated across all 100 steps, of which two account for 95.8% of all instances"

---

## Phase 1 — Data audit (read-only, no new code)

Two things to verify before writing H5 code. If either fails, the C2 framing needs adjustment.

### 1a — IC cascade: verify believable agents converge on wrong option

**Where to look:** `experiment_results_ic_primary/information_consensus/baseline/`

**What to check in `micro_log.json`:**
- `"correct": false` — agent voted for the wrong option
- `"composite_believability"` or believability sub-scores — should be non-trivially above zero
- `"vote"` — should converge (most agents on same wrong option by final steps)

**Expected finding:** baseline agents have believability ~0.385 (from condition summary) yet converge on the wrong option. This is the IC cascade.

**How to check:**
```python
import json, glob
for trial in range(10):
    micro = json.load(open(f"experiment_results_ic_primary/information_consensus/baseline/trial_{trial}/micro_log.json"))
    last_step = max(e["step"] for e in micro)
    final = [e for e in micro if e["step"] == last_step]
    votes = [e["vote"] for e in final]
    correct = [e["correct"] for e in final]
    print(f"trial_{trial}: votes={votes}, correct={correct}")
```

### 1b — CD collapse cases: find high-believability trials that collapsed

**Where to look:** `experiment_results_cd_primary/commons_dilemma/`

**What to check:** trials where `macro_summary["collapse_step"] is not None` AND `micro_summary["composite_believability"]` mean > 0.5

**Expected finding:** some trials in `memory` or `memory_planning` conditions where agents have reasonable believability (≥0.5) but the commons still collapsed.

**How to check:**
```python
import json, os
BASE = "experiment_results_cd_primary/commons_dilemma"
for cond in ["baseline","memory","memory_planning","full"]:
    for trial in os.listdir(f"{BASE}/{cond}"):
        macro = json.load(open(f"{BASE}/{cond}/{trial}/macro_summary.json"))
        micro = json.load(open(f"{BASE}/{cond}/{trial}/micro_summary.json"))
        if macro.get("collapse_step") is not None:
            cb = micro.get("composite_believability", {})
            mean_b = sum(cb.values())/len(cb) if cb else 0
            print(f"{cond}/{trial}: collapsed at step {macro['collapse_step']}, believability={mean_b:.3f}")
```

---

## Phase 2 — H5: Signed believability–validity discrepancy metric

**File:** `experiment_analysis.py`  
**Insert after:** `test_h4()` function (around line 565)

### What to build

Function `compute_discrepancy(records)` that:
1. Computes a `coordination_validity_score` per trial — a continuous 0–1 score (NOT just binary success)
2. Computes `discrepancy = believability - coordination_validity_score` per trial
3. Returns signed discrepancy table + flags large-positive cases (believable but invalid)

### coordination_validity_score formula

Use a weighted combo of available macro metrics:
```python
# For CD:
coordination_validity_score = (
    0.5 * coordination_score +        # fraction of steps coordinated
    0.3 * sustainability_score +       # resource health
    0.2 * (1 - average_gini)           # equity
)

# For IC: coordination_score alone (sustainability = IC vote convergence)
coordination_validity_score = coordination_score
```

The score is normalised 0–1 so it's directly comparable to believability (also 0–1).

### discrepancy interpretation
- `discrepancy > +0.2` → "gap case": believable agent, poor coordination — C2 evidence
- `discrepancy ≈ 0` → aligned: believability matches validity
- `discrepancy < -0.2` → "anti-gap": low believability but coordinated (rare edge case)

### Function signature
```python
def compute_discrepancy(records, scenario="commons_dilemma"):
    """
    H5: Compute signed believability-validity discrepancy per trial.
    
    Returns dict with:
      - per_trial: list of {condition, trial, believability, 
                            coordination_validity_score, discrepancy, gap_case}
      - gap_cases: subset where discrepancy > 0.2
      - mean_discrepancy_by_condition: {condition: mean_discrepancy}
      - supported: bool (gap cases exist)
    """
```

### Where to add to run_analysis()
After H4, before writing reports:
```python
results["H5"] = compute_discrepancy(records, scenario)
```
And add H5 rendering to `_render_text_report()`.

---

## Phase 3 — H6: Reflection saturation analysis

**File:** `experiment_analysis.py`  
**Insert after:** `compute_discrepancy()`

### What to build

Function `analyze_reflection_saturation(results_dir, scenario, conditions)` that:
1. Reads `micro_log.json` (NOT `micro_summary.json`) for each trial
2. Extracts `scenario_reflections` list from each entry
3. Computes: total count, unique count, repetition rate, diversity curve (unique count vs. step)
4. Reports top-N strings with counts
5. Runs on both `full` (deterministic) and `full_llm_reflection` (LLM) for comparison

### diversity_curve
- For each step s (0 to max_step), count cumulative unique strings seen up to step s across all trials and agents
- This shows when saturation occurs (curve flattens)

### Function signature
```python
def analyze_reflection_saturation(results_dir, scenario, conditions=None):
    """
    H6: Reflection saturation analysis.
    
    Args:
        results_dir: path to top-level results dir
        scenario: 'commons_dilemma' or 'information_consensus'
        conditions: list of condition names to analyse (default: ['full', 'full_llm_reflection'])
    
    Returns dict with per-condition:
        total_reflections, unique_count, repetition_rate, top_strings,
        diversity_curve (list of {step, cumulative_unique})
    """
```

### Important: multi-directory problem

`full` and `full_llm_reflection` live in DIFFERENT result directories:
- `full` → `experiment_results_cd_primary/` (CD) or `experiment_results_ic_primary/` (IC)
- `full_llm_reflection` → `experiment_results_cd_llm_reflection/` or `experiment_results_ic_llm_reflection/`

The function needs to accept a `results_dirs` dict mapping condition → directory, OR accept a list of directories to search across. Simplest: accept a list of directories and auto-detect which conditions are in each.

### Wiring into run_analysis()
Add a separate call since it needs micro_log (not micro_summary):
```python
results["H6"] = analyze_reflection_saturation(
    results_dirs={"full": results_dir, "full_llm_reflection": reflection_dir},
    scenario=scenario
)
```
This means `run_analysis()` needs an optional `reflection_dir` parameter.

---

## Phase 4 — H7/C4: Early-warning classifier + failure taxonomy

**New file:** `reverie/backend_server/early_warning.py`  
**Complexity: HIGH** — most complex phase; do this after Phases 2+3 are working.

### Part A: Early-warning classifier (H7)

**Goal:** Predict coordination collapse from first K micro-trace steps, using trial-level cross-validation (NOT step-level, which would leak future info).

**Features per trial (for first K steps):**
- Mean of each micro sub-dimension over steps 0..K-1: `mean_BC`, `mean_MC`, `mean_PP`, `mean_RN`
- Trend of each sub-dimension: slope of linear fit over steps 0..K-1
- Optional: step_0 values only (earliest signal)

**Label per trial:**
- `collapsed = 1` if `macro_summary["collapse_step"] is not None`
- `collapsed = 0` otherwise

**Data source:** CD primary dataset only (40/80 trials have variance; IC has near-zero variance in non-baseline conditions so is insufficient for within-condition testing)

**Evaluation protocol (CRITICAL — leakage prevention):**
- Split at the TRIAL level (each trial = one observation)
- Leave-one-out CV (LOO-CV) given small N (~80 CD trials total)
- NEVER split within a trial (no step-level train/test — that's leakage)
- Within-condition test: also run classifier trained only on trials from one condition and tested on held-out trials from the SAME condition

**K sweep:** K = 5, 10, 15, 20 steps

**Classifier:** Logistic regression (interpretable, works on small N). Fallback: decision tree depth-2 for taxonomy.

**Output metrics:**
- Precision, recall, F1, AUC-ROC per K value
- Lead time: earliest K with precision+recall both > 0.6
- Within-condition vs. across-condition AUC comparison

**Function signature:**
```python
def run_early_warning(results_dir, scenario="commons_dilemma", k_values=[5,10,15,20]):
    """
    H7: Leakage-safe early-warning classifier.
    Returns dict with results per K value + within-condition test results.
    """
```

**Data loading:** needs `micro_log.json` (step-by-step) + `macro_summary.json` (label). NOT `micro_summary.json` which is already aggregated.

### Part B: Failure taxonomy (C4)

**Goal:** For collapsed CD trials, identify 3–5 recurring micro-failure patterns.

**Approach:**
1. Collect all collapsed trials (from CD primary dataset)
2. For each: extract the sequence of mean believability scores per step and identify which sub-dimension dropped first
3. Cluster by: (a) which sub-dimension drops first, (b) how fast the drop happens, (c) whether all agents fail together or just some
4. Label each cluster as a failure type with a representative trace

**Failure types to look for (hypothesis):**
- Type A: "Rapid believability collapse" — all sub-dims drop together from step 0
- Type B: "Memory erosion" — MC drops first, then cascades
- Type C: "Planning failure" — PP drops while BC stays high (agent seems consistent but plans poorly)
- Type D: "Late coordination failure" — believability stays high but resource depletes anyway (the gap case)

**Function signature:**
```python
def build_failure_taxonomy(results_dir, scenario="commons_dilemma", n_clusters=5):
    """
    C4: Cluster micro-failure patterns from collapsed trials.
    Returns list of failure types: {label, description, n_trials, representative_trace}
    """
```

---

## Phase 5 — P1: Static injection condition design

**File:** `experiment_conditions.py`

### What to add

Two new conditions after `full_llm_reflection`:

```python
"static_reflection_injection": ExperimentalCondition(
    name="static_reflection_injection",
    use_memory=True,
    use_planning=True,
    use_reflection=True,
    use_llm_reflection=False,
    use_static_reflection=True,   # NEW FLAG
    static_reflection_content="Requesting at or below fair share helped keep the group within the replenishment limit.",
    description="memory_planning + the top saturated reflection string from the "
                "full condition injected statically each step. Tests whether the "
                "focal-point gain is driven by content not process (P1).",
),
"static_reflection_placebo": ExperimentalCondition(
    name="static_reflection_placebo",
    use_memory=True,
    use_planning=True,
    use_reflection=True,
    use_llm_reflection=False,
    use_static_reflection=True,   # NEW FLAG
    static_reflection_content="Thinking carefully about each decision helps ensure "
                               "I'm acting thoughtfully in the group context.",
    description="memory_planning + a tone/length-matched placebo string with no "
                "coordination content. Control condition for P1.",
),
```

**What also needs to change:**
- `ExperimentalCondition` dataclass: add `use_static_reflection: bool = False` and `static_reflection_content: str = ""`
- `scenarios/commons_dilemma.py` `_record_scenario_memories()`: check `condition.use_static_reflection` and inject `condition.static_reflection_content` instead of calling `_deterministic_reflection()` or `_generate_llm_reflection()`
- Same in `scenarios/information_consensus.py`

**Placebo string design criteria:**
- Same approximate token length as the injection string (~17 tokens)
- Same first-person register ("I" / "my")
- No resource, fair share, coordination, or group-behaviour content
- Plausible as a reflection on one's own thinking process

---

## Phase 6 — Wire into unified entrypoint

**File:** `experiment_analysis.py` — update `run_analysis()` and `__main__`

### Changes to `run_analysis()`

Add parameters:
```python
def run_analysis(
    results_dir="experiment_results",
    scenario="commons_dilemma",
    reflection_dir=None,       # NEW: dir containing full_llm_reflection data
    run_h5=True,
    run_h6=True,
):
```

Add to results dict:
```python
results["H5"] = compute_discrepancy(records, scenario)
if run_h6 and reflection_dir:
    results["H6"] = analyze_reflection_saturation(
        {"full": results_dir, "full_llm_reflection": reflection_dir}, scenario
    )
```

### Changes to `_render_text_report()`
Add H5 and H6 sections following the same pattern as H1–H4.

### Changes to `__main__`
Add `--reflection-dir` argument:
```python
parser.add_argument("--reflection-dir", default=None,
    help="Directory containing full_llm_reflection condition data (for H6)")
```

### New `__main__` invocation examples (for thesis):
```bash
# CD full analysis
python experiment_analysis.py experiment_results_cd_primary \
    --scenario commons_dilemma \
    --reflection-dir experiment_results_cd_llm_reflection

# IC full analysis  
python experiment_analysis.py experiment_results_ic_primary \
    --scenario information_consensus \
    --reflection-dir experiment_results_ic_llm_reflection
```

---

## Execution order and dependencies

```
Phase 0 (text fix)          — no dependencies, do first
Phase 1 (data audit)        — no dependencies, do before Phase 2
Phase 2 (H5 discrepancy)    — depends on Phase 1 (confirms C2 worked examples)
Phase 3 (H6 saturation)     — independent of Phase 2, can run in parallel
Phase 6 (wire entrypoint)   — depends on Phases 2+3
Phase 4 (H7/C4 classifier)  — depends on Phase 1 (needs collapse labels verified)
Phase 5 (P1 conditions)     — independent, can do any time
```

---

## Acceptance criteria per phase

| Phase | Done when |
|-------|-----------|
| 0 | "two" → "three" corrected in both reframing docs; git committed |
| 1 | IC cascade confirmed (baseline agents vote wrong at final step); ≥1 CD collapse case with believability ≥0.5 identified |
| 2 | `compute_discrepancy()` runs without error on CD primary data; outputs gap_cases with believability > coordination_validity + 0.2; IC cascade trial appears as a gap case |
| 3 | `analyze_reflection_saturation()` reports 3 unique strings for `full` and 1190 unique / 95% repetition for `full_llm_reflection`; diversity curve data produced |
| 4 | `early_warning.py` runs LOO-CV on CD data for K=[5,10,15,20]; produces precision/recall/AUC per K; explicit within-condition AUC reported; failure taxonomy has ≥3 labelled types |
| 5 | Two new conditions in `CONDITIONS` dict; `ExperimentalCondition` dataclass updated; scenarios handle `use_static_reflection` flag without breaking existing conditions |
| 6 | `python experiment_analysis.py experiment_results_cd_primary --scenario commons_dilemma --reflection-dir experiment_results_cd_llm_reflection` produces a unified H1–H6 report |

---

## What remains blocked on external factors

| Item | Blocked on |
|------|-----------|
| Human ratings blend into believability scores | HREC confirmation + 2+ raters recruited |
| `python llm_judge.py --all` (LLM reference ratings) | API budget decision |
| P1 actual experiment run | API budget + Phase 5 condition design done first |
| H7 within-condition statistical power | N is ~20 trials/condition — likely exploratory only; must report as such |
