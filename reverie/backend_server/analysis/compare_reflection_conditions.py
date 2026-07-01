import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _paths  # noqa: F401  (adds backend_server to sys.path)
_os.chdir(_paths.BACKEND)  # analysis scripts read result dirs relative to backend_server

"""
Compare the original deterministic-reflection condition (`full`) against the
new LLM-reflection condition (`full_llm_reflection`) for the Commons Dilemma.

Reports, side by side:
  - n trials found (handles partial runs gracefully)
  - coordination success rate
  - mean sustainability_score
  - mean demand_pressure
  - mean coordination_score
  - mean Gini
  - mean convergence step (successful trials)
  - unique reflection count per trial (deterministic should be ~2-3; LLM ~tens)

Usage (run from reverie/backend_server):
    python compare_reflection_conditions.py

Optionally override the two result directories:
    python compare_reflection_conditions.py \
        --full_dir experiment_results_cd_primary \
        --llm_dir  experiment_results_cd_llm_reflection

The script reads each trial's macro_summary.json and, for the reflection-count
check, the per-trial micro_log.json (scenario_reflections field). It works on
however many trials currently exist, so it can be run while the experiment is
still in progress.
"""

import argparse
import glob
import json
import os
import statistics as st

SCENARIO = "commons_dilemma"

DETERMINISTIC_REFLECTION_STRINGS = {
    "Requesting at or below fair share helped keep the group within the replenishment limit.",
    "Even moderate requests were not enough because total group demand exceeded replenishment.",
    "Requests above fair share increased pressure on the shared pool and may require restraint next round.",
}


def _trial_dirs(base_dir, condition):
    path = os.path.join(base_dir, SCENARIO, condition)
    return sorted(glob.glob(os.path.join(path, "trial_*")))


def _load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


def _rigidity_in_trial(trial_dir):
    """Measure how quickly/rigidly the group locks to a constant total request.

    Returns:
      flat_from_step          : first step S such that total_requested is identical
                                for every step >= S (i.e. the group went flat and
                                stayed flat). None if it never stabilises.
      ever_perturbed_after_flat: True if, after first reaching its eventual constant
                                value, the total ever deviated and returned (i.e. not
                                perfectly monotone-into-flat). Indicates richer dynamics.
      final_total             : the constant total it settled on (or last total).
    """
    macro = _load_json(os.path.join(trial_dir, "macro_log.json"))
    if not macro:
        return None
    totals = [m.get("total_requested") for m in macro if m.get("total_requested") is not None]
    if not totals:
        return None
    final = totals[-1]
    # flat_from_step: earliest index from which all subsequent totals equal `final`
    flat_from = None
    for i in range(len(totals)):
        if all(t == final for t in totals[i:]):
            flat_from = i
            break
    # perturbation: once it first hit `final`, did it ever leave that value again?
    ever_perturbed = False
    if final in totals:
        first_hit = totals.index(final)
        after = totals[first_hit:]
        if any(t != final for t in after):
            ever_perturbed = True
    return {
        "flat_from_step": flat_from,
        "ever_perturbed_after_flat": ever_perturbed,
        "final_total": final,
    }


def _unique_reflections_in_trial(trial_dir):
    """Count unique scenario_reflections in a trial's micro_log, split LLM vs fallback."""
    micro = _load_json(os.path.join(trial_dir, "micro_log.json"))
    if not micro:
        return None
    refs = set()
    for entry in micro:
        for r in (entry.get("scenario_reflections") or []):
            refs.add(r)
    llm = [r for r in refs if r not in DETERMINISTIC_REFLECTION_STRINGS]
    fb = [r for r in refs if r in DETERMINISTIC_REFLECTION_STRINGS]
    return {"unique_total": len(refs), "unique_llm": len(llm), "fallback_present": len(fb)}


def summarize_condition(base_dir, condition):
    trials = _trial_dirs(base_dir, condition)
    rows = []
    refl_counts = []
    rigidity = []
    for td in trials:
        ms = _load_json(os.path.join(td, "macro_summary.json"))
        if not ms:
            continue
        rows.append({
            "trial": os.path.basename(td),
            "success": bool(ms.get("coordination_success")),
            "sustainability": ms.get("sustainability_score"),
            "demand_pressure": ms.get("demand_pressure"),
            "coordination_score": ms.get("coordination_score"),
            "gini": ms.get("average_gini"),
            "convergence_step": ms.get("convergence_step"),
        })
        rc = _unique_reflections_in_trial(td)
        if rc:
            refl_counts.append(rc)
        rg = _rigidity_in_trial(td)
        if rg:
            rigidity.append(rg)
    return rows, refl_counts, rigidity


def _mean(vals):
    vals = [v for v in vals if isinstance(v, (int, float))]
    return st.mean(vals) if vals else float("nan")


def _fmt(x, nd=3):
    return f"{x:.{nd}f}" if isinstance(x, (int, float)) and x == x else "—"


def report(base_full, cond_full, base_llm, cond_llm):
    results = {}
    for label, base, cond in [
        ("full (deterministic)", base_full, cond_full),
        ("full_llm_reflection", base_llm, cond_llm),
    ]:
        rows, refl, rigidity = summarize_condition(base, cond)
        n = len(rows)
        succ = sum(1 for r in rows if r["success"])
        conv = [r["convergence_step"] for r in rows if r["success"] and isinstance(r["convergence_step"], (int, float))]
        flats = [rg["flat_from_step"] for rg in rigidity if rg["flat_from_step"] is not None]
        results[label] = {
            "n": n,
            "success_rate": (succ / n) if n else float("nan"),
            "success_n": succ,
            "mean_sustainability": _mean([r["sustainability"] for r in rows]),
            "mean_demand_pressure": _mean([r["demand_pressure"] for r in rows]),
            "mean_coordination_score": _mean([r["coordination_score"] for r in rows]),
            "mean_gini": _mean([r["gini"] for r in rows]),
            "mean_convergence_step": _mean(conv),
            "mean_unique_reflections": _mean([rc["unique_total"] for rc in refl]),
            "mean_unique_llm_reflections": _mean([rc["unique_llm"] for rc in refl]),
            "trials_with_fallback": sum(1 for rc in refl if rc["fallback_present"] > 0),
            "mean_flat_from_step": _mean(flats),
            "trials_that_went_flat": len(flats),
            "trials_perturbed_after_flat": sum(1 for rg in rigidity if rg["ever_perturbed_after_flat"]),
        }

    a = results["full (deterministic)"]
    b = results["full_llm_reflection"]
    w = 26
    print("=" * 78)
    print(f"COMMONS DILEMMA — deterministic vs LLM reflection")
    print("=" * 78)
    print(f"{'metric':<{w}}{'full (determ.)':>22}{'full_llm_reflection':>26}")
    print("-" * 78)

    def line(name, ka, kb, nd=3, pct=False):
        va = a.get(ka)
        vb = b.get(ka) if kb is None else b.get(kb)
        if pct:
            sa = f"{va*100:.0f}%" if isinstance(va, (int, float)) and va == va else "—"
            sb = f"{vb*100:.0f}%" if isinstance(vb, (int, float)) and vb == vb else "—"
        else:
            sa, sb = _fmt(va, nd), _fmt(vb, nd)
        print(f"{name:<{w}}{sa:>22}{sb:>26}")

    print(f"{'trials found':<{w}}{a['n']:>22}{b['n']:>26}")
    print(f"{'coordination success':<{w}}{str(a['success_n'])+'/'+str(a['n']):>22}{str(b['success_n'])+'/'+str(b['n']):>26}")
    line("  success rate", "success_rate", "success_rate", pct=True)
    line("mean sustainability", "mean_sustainability", None)
    line("mean demand pressure", "mean_demand_pressure", None)
    line("mean coordination score", "mean_coordination_score", None)
    line("mean Gini", "mean_gini", None)
    line("mean convergence step", "mean_convergence_step", None, nd=1)
    print("-" * 78)
    line("unique reflections/trial", "mean_unique_reflections", None, nd=1)
    line("  of which LLM-generated", "mean_unique_llm_reflections", None, nd=1)
    print(f"{'trials with fallback':<{w}}{a['trials_with_fallback']:>22}{b['trials_with_fallback']:>26}")
    print("-" * 78)
    print("CONVERGENCE RIGIDITY (lower flat-step = locks faster; perturbed = richer dynamics)")
    line("mean flat-from step", "mean_flat_from_step", None, nd=1)
    print(f"{'trials that went flat':<{w}}{a['trials_that_went_flat']:>22}{b['trials_that_went_flat']:>26}")
    print(f"{'  perturbed after flat':<{w}}{a['trials_perturbed_after_flat']:>22}{b['trials_perturbed_after_flat']:>26}")
    print("=" * 78)
    print("Notes:")
    print("  - Refloration-count check: deterministic should be ~2-3 unique strings;")
    print("    LLM condition should be tens of unique strings with 0 fallbacks.")
    print("  - Compare success rate vs the documented full=70% only when n=20 for both.")
    print("  - This script tolerates partial runs; re-run as more trials complete.")

    return results


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--full_dir", default="experiment_results_cd_primary",
                    help="results dir containing the original deterministic 'full' condition")
    ap.add_argument("--full_cond", default="full")
    ap.add_argument("--llm_dir", default="experiment_results_cd_llm_reflection",
                    help="results dir containing the new 'full_llm_reflection' condition")
    ap.add_argument("--llm_cond", default="full_llm_reflection")
    args = ap.parse_args()
    report(args.full_dir, args.full_cond, args.llm_dir, args.llm_cond)
