# ICDM 2026 Applied Track — Submission Feasibility Assessment
**Date assessed:** 2026-05-27  
**Submission deadline:** June 6, 2026 — 10 days away  
**Venue:** ICDM 2026, Shenyang, China — Applied Track

---

## 🚦 Overall Verdict: NOT RECOMMENDED — too many blockers

Short version: the Applied Track is a meaningfully better fit than the Research Track, but **the 10-day deadline makes a quality submission almost impossible given the current project state**, and several substantive issues would likely cause rejection regardless.

---

## 1. Deadline Reality Check

| Task required to submit | Time needed | Available |
|---|---|---|
| Write full 10-page IEEE 2-col paper | 5–7 days minimum | ✅ barely |
| Supervisor review + sign-off | 2–3 days | ❌ almost none |
| Human evaluation results | Not done | ❌ missing |
| Ethics clearance for human raters | Unknown pathway | ❌ unconfirmed |
| Reproducibility checklist | Required at submission | ⚠️ needs work |
| Revisions after supervisor feedback | 1–2 days | ❌ no time |

**10 calendar days are available. A realistic complete draft needs at minimum 7, leaving 3 for supervisor feedback — which is not enough for a first submission anywhere.**

---

## 2. Applied Track Fit Assessment

The Applied Track is better than the Research Track for this work. Honest breakdown:

### ✅ What fits

| Applied Track criterion | This project |
|---|---|
| "Comprehensive experimental analysis… providing new fundamental insights" | ✅ Strong match — 4-condition ablation × 80 trials × full statistical analysis (Spearman, KW, OLS) |
| "Interdisciplinary and novel applications" | ✅ Social science (commons dilemma, Condorcet jury theorem) + LLM agents |
| "New benchmarks that promote research and evaluation in new problems" | ✅ Dual-level validation framework + benchmark design for GABMs |

### ❌ What doesn't fit

| Problem | Detail |
|---|---|
| **Venue identity mismatch** | ICDM reviewers expect novel *mining algorithms*, scalability results, or KDD-style pattern discovery. The core contribution is agent evaluation methodology — that reads as AI/MAS research, not data mining, regardless of reframing. Project notes (2026-05-24) already concluded: *"Venue fit problem… this work is agent evaluation methodology, which reads as AI/MAS research regardless of reframing."* |
| **No deployed system** | The Applied Track's top criterion is "deployed systems." This platform is a research prototype, not deployed software. |
| **Acceptance rate ~9%** | At this rate, venue mismatch alone is typically fatal. ICDM reviewers familiar with the scope will flag it immediately. |
| **Human evaluation missing** | Applied Track expects end-to-end results. Submitting with automated proxies only and noting "human eval pending July–August" signals incomplete work. |

---

## 3. What Would Need to Be True to Submit

For this to be a viable submission, **all** of the following must be in place by June 6:

1. **A complete polished paper** — 10 pages, IEEE 2-column format, introduction through conclusion
2. **Human evaluation results** — at minimum the LLM judge ratings from `python llm_judge.py --all` (not yet run); ideally real human ratings
3. **Ethics confirmation** — Prof. Beheshti must confirm the HREC pathway before human evaluation data enters any publication
4. **Supervisor approval** — Beheshti and Zhang need to review and approve before submission
5. **Reproducibility checklist** — code and (ideally) data must be publicly available or described precisely

**None of these are currently in place.**

---

## 4. What the Project's Own Documents Say About ICDM

From [MRES_PROGRESS_LOG.md](MRES_PROGRESS_LOG.md) (recorded 2026-05-24):

> **ICDM verdict: not recommended.**
> - Acceptance rate ~9% — very competitive
> - Venue fit problem: ICDM expects novel mining algorithms, scalability results, or knowledge discovery methods. This work is agent evaluation methodology, which reads as AI/MAS research regardless of reframing.
> - Reframing around "trace-based behavioural mining" is possible but forces the contribution into an unnatural frame that dilutes it.

That assessment was for the main Research Track. The Applied Track is a partial improvement, but the core objections — venue identity mismatch, ~9% acceptance rate, missing human evaluation — still apply.

---

## 5. ICDM Alternative Tracks Worth Checking

From the ICDM discussion summary (docs/todays_discussion_summary_icdm_ethics_framework.md):

| ICDM Target | Suitability |
|---|---|
| ICDM 2026 Research Track (main) | ❌ Not recommended |
| ICDM 2026 Applied Track | ⚠️ Possible but hard — this assessment |
| **ICDM 2026 Workshop** | ✅ Stronger and more realistic |
| **ICDM 2026 PhD Forum** | ✅ Very suitable for work-in-progress |
| ICDM 2027 main track | ✅ Realistic with full human eval + polished results |

**Action:** Check the ICDM 2026 website for workshop and PhD Forum deadlines — these are explicitly designed for research-in-progress and typically have later submission windows with lower bars.

---

## 6. Venue Comparison

| Option | Effort | Deadline | Fit | Recommended? |
|---|---|---|---|---|
| ICDM 2026 Applied Track | Very high (10 days) | Jun 6, 2026 | Weak–medium | ❌ No |
| ICDM 2026 Workshop / PhD Forum | Medium | Check website | Good | ✅ Check immediately |
| **AAMAS 2027 main track** | Normal | ~Oct 2026 | **Perfect** | ✅ **Primary plan** |
| JASSS journal | Low (rolling) | None | Very good | ✅ Fallback |

### Why AAMAS 2027 is the right primary target

- Acceptance rate ~25% — realistic for this contribution
- **Perfect venue fit:** agent evaluation methodology is core AAMAS scope
- Reviewers will engage with H4 (planning > memory) as a substantive finding, not a curiosity
- Approximate deadline: October 2026 — aligns with completing human evaluation (Jul–Aug) and paper drafting (Aug–Sep)
- Full timeline: IC v3 ✅ → human eval (Jul) → rating blend (Jul) → paper draft (Aug) → supervisor review (Sep) → submit (Oct) → thesis (Nov)

---

## 7. Reproducibility Checklist (ICDM Requirement)

If a future ICDM submission is considered, the reproducibility checklist requires:

- [ ] Code publicly available (GitHub repository)
- [ ] Data publicly available or clearly described
- [ ] Detailed algorithm pseudocode
- [ ] Comprehensive experimental methodology
- [ ] Results on publicly available datasets (currently: all data is self-generated)

The self-generated nature of the experimental data is a known limitation. It is justified academically (no public GABM datasets exist — confirmed by direct repository inspection), but must be stated explicitly. See `RESEARCH_PLAN_FIDELITY_CHECKLIST.md` §3.7 for the recommended thesis framing.

---

## 8. Bottom Line

**Do not rush to submit to ICDM 2026 Applied Track.**

- The deadline is 10 days away
- The venue fit is weak-to-medium at best
- Human evaluation is not done and ethics clearance is unconfirmed
- The project is already 6–8 weeks ahead of the thesis timeline

Spending 10 days producing a rushed paper for a ~9% acceptance venue when **AAMAS 2027 is a perfect fit with 4 months to prepare** is not a good trade. The risk is: exhaustion, rejection, and loss of 10 days that should go toward human evaluation (July deadline) and the methodology chapter.

**The one action worth taking immediately:** check whether ICDM 2026 has a **Workshop or PhD Forum** with an open deadline — those tracks are genuinely well-suited and far more achievable.

---

*Assessment prepared 2026-05-27 based on full reading of all project documentation.*
