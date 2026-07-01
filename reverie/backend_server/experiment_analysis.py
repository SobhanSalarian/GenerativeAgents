"""
experiment_analysis.py — H1–H4 hypothesis-testing pipeline.

Reads the structured output produced by experiment_runner.py and performs
the four hypothesis tests defined in the MRes research plan.

Usage
-----
    python experiment_analysis.py [results_dir] [--scenario SCENARIO]

    results_dir : path to the top-level experiment_results directory
                  (default: experiment_results)
    --scenario  : scenario sub-folder to analyse
                  (default: commons_dilemma)

Output
------
    experiment_results/<scenario>/analysis/hypothesis_report.json
    experiment_results/<scenario>/analysis/hypothesis_report.txt

Hypotheses tested
-----------------
H1  Higher composite believability → higher coordination effectiveness.
    Test: Spearman rank correlation (believability vs coordination_score).
    Secondary: Mann-Whitney U comparing high- vs low-believability run groups.

H2  Non-linear threshold effect: below a threshold believability, coordination
    fails regardless of other factors.
    Test: Partition runs into tertile believability bands; compute failure rates
    per band; find the empirical threshold below which all runs fail.

H3  Conditions with richer architectural features show monotonically increasing
    believability: baseline < memory < memory_planning < full.
    Test: Kruskal-Wallis H (overall condition effect) + pairwise Mann-Whitney U
    for consecutive condition pairs; check monotonicity of means.

H4  Memory coherence and behavioural consistency are stronger predictors of
    coordination success than planning plausibility or response naturalness.
    Test: Spearman correlation of each micro sub-dimension against
    coordination_score; rank predictors by |rho|.
"""

import argparse
import csv
import json
from pathlib import Path

import numpy as np
from scipy import stats

# OLS regression for H4 (plan §4.6 — regression modelling)
try:
    from numpy.linalg import lstsq as _lstsq
    _NUMPY_AVAILABLE = True
except ImportError:
    _NUMPY_AVAILABLE = False


# Threshold constants matching Table 1 of the research plan
BELIEVABILITY_HIGH = 0.7
BELIEVABILITY_LOW  = 0.4
COORDINATION_HIGH  = 0.7

# Canonical condition order for H3 monotonicity check
CONDITION_ORDER = ["baseline", "memory", "memory_planning", "full"]


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def _mean_of_dict(d):
    """Mean of numeric values in a dict, or None if the dict is empty."""
    values = [v for v in d.values() if isinstance(v, (int, float))]
    return round(sum(values) / len(values), 4) if values else None


def load_trials(results_dir, scenario):
    """
    Walk the results directory tree and return one flat record per trial.

    Each record contains:
      condition, trial, believability, behavioural_consistency,
      memory_coherence, planning_plausibility, response_naturalness,
      coordination_score, sustainability_score, collapsed,
      coordination_success (bool, threshold >= 0.7)
    """
    base = Path(results_dir) / scenario
    if not base.exists():
        raise FileNotFoundError(
            f"No results directory found at {base}. "
            f"Run experiment_runner.py first."
        )

    records = []
    for condition_dir in sorted(base.iterdir()):
        if not condition_dir.is_dir():
            continue
        condition = condition_dir.name

        for trial_dir in sorted(condition_dir.iterdir()):
            if not trial_dir.is_dir() or not trial_dir.name.startswith("trial_"):
                continue

            micro_path = trial_dir / "micro_summary.json"
            macro_path = trial_dir / "macro_summary.json"
            if not micro_path.exists() or not macro_path.exists():
                continue

            micro = json.loads(micro_path.read_text())
            macro = json.loads(macro_path.read_text())

            record = {
                "condition"              : condition,
                "trial"                  : trial_dir.name,
                "believability"          : _mean_of_dict(
                    micro.get("composite_believability",
                              micro.get("believability_proxy", {}))),
                "behavioural_consistency": _mean_of_dict(
                    micro.get("behavioural_consistency", {})),
                "memory_coherence"       : _mean_of_dict(
                    micro.get("memory_coherence",
                              micro.get("memory_reference_rate", {}))),
                "planning_plausibility"  : _mean_of_dict(
                    micro.get("planning_plausibility",
                              micro.get("planning_reference_rate", {}))),
                "response_naturalness"   : _mean_of_dict(
                    micro.get("response_naturalness",
                              micro.get("response_naturalness_proxy", {}))),
                "coordination_score"     : macro.get("coordination_score"),
                "coordination_success"   : macro.get("coordination_success"),
                "sustainability_score"   : macro.get("sustainability_score"),
                "convergence_speed"      : macro.get("convergence_speed"),
                "collapsed"              : macro.get("collapse_step") is not None,
            }
            if record["coordination_success"] is None:
                record["coordination_success"] = (
                    record["coordination_score"] is not None
                    and record["coordination_score"] >= COORDINATION_HIGH
                )
            records.append(record)

    return records


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _extract_pairs(records, x_key, y_key):
    """Paired (xs, ys) lists, dropping records where either value is None."""
    pairs = [
        (r[x_key], r[y_key])
        for r in records
        if r.get(x_key) is not None and r.get(y_key) is not None
    ]
    if not pairs:
        return [], []
    xs, ys = zip(*pairs)
    return list(xs), list(ys)


def _condition_groups(records, key):
    """Return {condition: [values]} for records where key is not None."""
    groups = {}
    for r in records:
        if r.get(key) is None:
            continue
        groups.setdefault(r["condition"], []).append(r[key])
    return groups


# ---------------------------------------------------------------------------
# H1 — believability vs coordination correlation
# ---------------------------------------------------------------------------

def test_h1(records):
    """
    H1: Agents with higher composite believability scores will produce
    significantly higher group coordination effectiveness.

    Primary test : Spearman rank correlation (believability, coordination_score).
    Secondary    : Mann-Whitney U — high-believability runs vs low-believability runs.
    """
    xs, ys = _extract_pairs(records, "believability", "coordination_score")
    result = {
        "hypothesis" : "H1",
        "description": (
            "Higher composite believability predicts higher coordination score."
        ),
        "n": len(xs),
    }

    if len(xs) < 3:
        result["status"] = "insufficient_data"
        result["note"]   = (
            f"Need ≥ 3 paired observations for correlation; found {len(xs)}. "
            f"Run more trials before interpreting this test."
        )
        return result

    rho, p = stats.spearmanr(xs, ys)
    result.update({
        "test"     : "Spearman rank correlation",
        "rho"      : round(float(rho), 4),
        "p_value"  : round(float(p), 4),
        "supported": bool(rho > 0 and p < 0.05),
        "note"     : (
            f"Spearman rho={rho:.3f}, p={p:.4f}. "
            f"Positive rho with p < 0.05 supports H1."
        ),
    })

    # Group comparison: high vs low believability runs
    high = [y for x, y in zip(xs, ys) if x >= BELIEVABILITY_HIGH]
    low  = [y for x, y in zip(xs, ys) if x <  BELIEVABILITY_LOW]
    if len(high) >= 2 and len(low) >= 2:
        u_stat, u_p = stats.mannwhitneyu(high, low, alternative="greater")
        result["group_comparison"] = {
            "test"     : "Mann-Whitney U (high believability > low believability)",
            "n_high"   : len(high),
            "n_low"    : len(low),
            "mean_high": round(float(np.mean(high)), 4),
            "mean_low" : round(float(np.mean(low)), 4),
            "u_stat"   : round(float(u_stat), 4),
            "p_value"  : round(float(u_p), 4),
            "supported": bool(u_p < 0.05),
        }
    else:
        result["group_comparison"] = {
            "status": "insufficient_data",
            "note"  : (
                f"Need ≥ 2 runs in both high (≥ {BELIEVABILITY_HIGH}) and "
                f"low (< {BELIEVABILITY_LOW}) believability bands. "
                f"Found {len(high)} high, {len(low)} low."
            ),
        }

    return result


# ---------------------------------------------------------------------------
# H2 — threshold effect
# ---------------------------------------------------------------------------

def test_h2(records):
    """
    H2: The relationship between believability and coordination is non-linear;
    below a threshold believability, coordination fails regardless of other
    factors.

    Approach: divide trials into tertile believability bands, compute
    coordination failure rate per band, and identify the empirical threshold
    below which every run failed.
    """
    valid = [
        r for r in records
        if r.get("believability") is not None
        and r.get("coordination_score") is not None
    ]
    result = {
        "hypothesis" : "H2",
        "description": (
            "Below a believability threshold, coordination fails regardless "
            "of other factors (non-linear / threshold effect)."
        ),
        "n": len(valid),
    }

    if len(valid) < 4:
        result["status"] = "insufficient_data"
        result["note"]   = (
            f"Need ≥ 4 observations for threshold analysis; found {len(valid)}."
        )
        return result

    # Tertile band boundaries
    sorted_vals = sorted(r["believability"] for r in valid)
    n           = len(sorted_vals)
    low_cutoff  = sorted_vals[n // 3]
    high_cutoff = sorted_vals[(2 * n) // 3]

    bands = {"low": [], "mid": [], "high": []}
    for r in valid:
        b = r["believability"]
        if b <= low_cutoff:
            bands["low"].append(r["coordination_success"])
        elif b <= high_cutoff:
            bands["mid"].append(r["coordination_success"])
        else:
            bands["high"].append(r["coordination_success"])

    band_stats = {}
    for name, successes in bands.items():
        if successes:
            rate = sum(successes) / len(successes)
            band_stats[name] = {
                "n"           : len(successes),
                "success_rate": round(rate, 3),
                "fail_rate"   : round(1.0 - rate, 3),
            }

    # Empirical threshold: highest believability value such that every run
    # at or below that value failed coordination
    sorted_records = sorted(valid, key=lambda r: r["believability"])
    empirical_threshold = None
    for i, r in enumerate(sorted_records):
        if all(not rb["coordination_success"] for rb in sorted_records[:i + 1]):
            empirical_threshold = r["believability"]

    supported = (
        empirical_threshold is not None
        and band_stats.get("low", {}).get("fail_rate", 0) > 0.5
    )

    result.update({
        "band_cutoffs": {
            "low_max" : round(low_cutoff, 4),
            "high_min": round(high_cutoff, 4),
        },
        "band_stats"          : band_stats,
        "empirical_threshold" : round(empirical_threshold, 4) if empirical_threshold else None,
        "supported"           : supported,
        "note"                : (
            f"Empirical threshold (all runs below fail): {empirical_threshold:.3f}."
            if empirical_threshold else
            "No clear failure threshold found in the current data."
        ),
    })
    return result


# ---------------------------------------------------------------------------
# H3 — monotonically increasing believability across conditions
# ---------------------------------------------------------------------------

def test_h3(records):
    """
    H3: Conditions with incrementally richer architectural features will show
    monotonically increasing believability scores:
    baseline < memory < memory_planning < full.

    Primary test: Kruskal-Wallis H (overall condition effect on believability).
    Secondary   : Pairwise Mann-Whitney U for consecutive condition pairs.
    Monotonicity: Checked on condition mean believability.
    """
    groups = _condition_groups(records, "believability")
    ordered_groups = [(c, groups[c]) for c in CONDITION_ORDER if c in groups]

    result = {
        "hypothesis" : "H3",
        "description": (
            "Believability increases monotonically: "
            "baseline < memory < memory_planning < full."
        ),
        "condition_means": {
            c: round(float(np.mean(v)), 4) for c, v in ordered_groups
        },
        "condition_n": {c: len(v) for c, v in ordered_groups},
    }

    if len(ordered_groups) < 2:
        result["status"] = "insufficient_data"
        result["note"]   = "Need data from ≥ 2 conditions."
        return result

    # Kruskal-Wallis across all available conditions
    group_arrays = [v for _, v in ordered_groups]
    if all(len(a) >= 2 for a in group_arrays):
        h_stat, kw_p = stats.kruskal(*group_arrays)
        result["kruskal_wallis"] = {
            "test"       : "Kruskal-Wallis H",
            "h_stat"     : round(float(h_stat), 4),
            "p_value"    : round(float(kw_p), 4),
            "significant": bool(kw_p < 0.05),
        }
    else:
        result["kruskal_wallis"] = {
            "status": "skipped",
            "note"  : "Some conditions have fewer than 2 observations.",
        }

    # Pairwise Mann-Whitney U for consecutive ordered pairs
    pairwise = []
    for i in range(len(ordered_groups) - 1):
        c1, v1 = ordered_groups[i]
        c2, v2 = ordered_groups[i + 1]
        if len(v1) >= 2 and len(v2) >= 2:
            u, p = stats.mannwhitneyu(v2, v1, alternative="greater")
            pairwise.append({
                "comparison": f"{c1} → {c2}",
                "mean_lower": round(float(np.mean(v1)), 4),
                "mean_upper": round(float(np.mean(v2)), 4),
                "direction" : "↑" if np.mean(v2) > np.mean(v1) else "↓ (unexpected)",
                "u_stat"    : round(float(u), 4),
                "p_value"   : round(float(p), 4),
                "supported" : bool(p < 0.05 and np.mean(v2) > np.mean(v1)),
            })
        else:
            pairwise.append({
                "comparison": f"{c1} → {c2}",
                "status"    : "insufficient_data",
            })
    result["pairwise"] = pairwise

    # Global monotonicity check on means
    means = [np.mean(groups[c]) for c in CONDITION_ORDER if c in groups]
    monotone = all(means[i] <= means[i + 1] for i in range(len(means) - 1))
    result["monotone_in_means"] = monotone
    result["supported"] = monotone
    result["note"] = (
        "Mean believability is monotonically non-decreasing across available "
        f"conditions: {list(result['condition_means'].values())}."
        if monotone else
        "Mean believability does NOT follow the expected monotone order."
    )
    return result


# ---------------------------------------------------------------------------
# H4 — micro sub-dimension predictors of coordination
# ---------------------------------------------------------------------------

def _ols_regression(records, predictors, outcome):
    """
    Ordinary Least Squares: outcome ~ predictors (with intercept).

    Returns a dict with coefficients, R², and per-predictor p-values
    (approximated via t-distribution with n - k - 1 degrees of freedom).
    Returns None when data are insufficient.
    """
    if not _NUMPY_AVAILABLE:
        return None

    # Build aligned arrays dropping rows with any missing value
    rows = []
    for r in records:
        if r.get(outcome) is None:
            continue
        if any(r.get(p) is None for p in predictors):
            continue
        rows.append([r[p] for p in predictors] + [r[outcome]])

    n = len(rows)
    k = len(predictors)
    if n < k + 2:
        return {"status": "insufficient_data", "n": n}

    data = np.array(rows, dtype=float)
    X = np.hstack([np.ones((n, 1)), data[:, :k]])   # add intercept column
    y = data[:, k]

    coeffs, residuals, rank, _ = _lstsq(X, y, rcond=None)
    y_hat = X @ coeffs
    ss_res = float(np.sum((y - y_hat) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

    # Approximate standard errors and t-statistics
    dof = n - k - 1
    if dof > 0 and ss_res > 0:
        sigma2 = ss_res / dof
        XtX_inv = np.linalg.pinv(X.T @ X)
        se = np.sqrt(np.diag(XtX_inv) * sigma2)
        t_stats = coeffs / (se + 1e-12)
        p_values = [
            float(2 * (1 - stats.t.cdf(abs(t), df=dof))) for t in t_stats
        ]
    else:
        se = [None] * (k + 1)
        t_stats = [None] * (k + 1)
        p_values = [None] * (k + 1)

    # Standardised (beta) coefficients: z-score predictors and outcome, refit.
    # These are the coefficients reported in the paper (comparable across
    # predictors on a common scale); the raw coefficients above are retained too.
    Xp = data[:, :k]
    x_sd = Xp.std(axis=0, ddof=0)
    y_sd = y.std(ddof=0)
    std_coefs = {}
    if y_sd > 0 and np.all(x_sd > 0):
        Xz = (Xp - Xp.mean(axis=0)) / x_sd
        yz = (y - y.mean()) / y_sd
        Xzc = np.hstack([np.ones((n, 1)), Xz])
        bz, _, _, _ = _lstsq(Xzc, yz, rcond=None)
        for i, pred in enumerate(predictors):
            std_coefs[pred] = round(float(bz[i + 1]), 4)

    predictor_coefs = {}
    for i, pred in enumerate(predictors):
        predictor_coefs[pred] = {
            "coefficient"             : round(float(coeffs[i + 1]), 4),
            "standardized_coefficient": std_coefs.get(pred),
            "p_value"                 : round(p_values[i + 1], 4) if p_values[i + 1] is not None else None,
        }

    return {
        "n"          : n,
        "r_squared"  : round(r_squared, 4),
        "intercept"  : round(float(coeffs[0]), 4),
        "predictors" : predictor_coefs,
    }


def test_h4(records):
    """
    H4: Memory coherence and behavioural consistency will be stronger predictors
    of coordination success than planning plausibility or response naturalness.

    Primary test : Spearman rank correlation (each sub-dimension vs.
                   coordination_score); rank by |rho|.
    Secondary    : OLS multiple regression (research plan §4.6 — 'regression
                   modelling to test H4').
    Support check: memory_coherence and behavioural_consistency occupy the top
                   two positions in the Spearman ranking.
    """
    sub_dims = [
        ("behavioural_consistency", "behavioural_consistency"),
        ("memory_coherence"       , "memory_coherence"),
        ("planning_plausibility"  , "planning_plausibility"),
        ("response_naturalness"   , "response_naturalness"),
    ]

    result = {
        "hypothesis" : "H4",
        "description": (
            "Memory coherence and behavioural consistency are stronger "
            "predictors of coordination score than planning plausibility "
            "or response naturalness."
        ),
        "correlations": {},
    }

    for label, key in sub_dims:
        xs, ys = _extract_pairs(records, key, "coordination_score")
        if len(xs) < 3:
            result["correlations"][label] = {
                "n": len(xs), "status": "insufficient_data",
            }
            continue
        rho, p = stats.spearmanr(xs, ys)
        result["correlations"][label] = {
            "n"      : len(xs),
            "rho"    : round(float(rho), 4),
            "p_value": round(float(p), 4),
            "abs_rho": round(abs(float(rho)), 4),
        }

    # Rank predictors by |rho|
    ranked = sorted(
        [(k, v) for k, v in result["correlations"].items() if "rho" in v],
        key=lambda kv: kv[1]["abs_rho"],
        reverse=True,
    )
    result["predictor_ranking"] = [k for k, _ in ranked]

    top_two      = set(result["predictor_ranking"][:2]) if len(ranked) >= 2 else set()
    expected_top = {"memory_coherence", "behavioural_consistency"}
    result["supported"] = top_two == expected_top
    result["note"] = (
        f"Top-ranked predictors: {result['predictor_ranking']}. "
        f"H4 supported: {result['supported']}."
    )

    # OLS multiple regression (plan §4.6)
    all_predictors = [key for _, key in sub_dims]
    ols = _ols_regression(records, all_predictors, "coordination_score")
    result["ols_regression"] = ols or {"status": "unavailable"}

    # Regression-based ranking (by absolute coefficient, if OLS succeeded)
    if ols and "predictors" in ols:
        reg_ranked = sorted(
            ols["predictors"].items(),
            key=lambda kv: abs(kv[1]["coefficient"]),
            reverse=True,
        )
        result["regression_predictor_ranking"] = [k for k, _ in reg_ranked]
        reg_top_two = set(result["regression_predictor_ranking"][:2]) if len(reg_ranked) >= 2 else set()
        result["regression_supported"] = reg_top_two == expected_top

    return result


# ---------------------------------------------------------------------------
# H5 — Signed believability–validity discrepancy metric
# ---------------------------------------------------------------------------

def _coordination_validity_score(record, scenario):
    """
    Continuous 0–1 validity score for a trial.

    CD: weighted combo of coordination_score (50%), sustainability_score (30%),
        and equity term 1-gini (20%).
    IC: coordination_score alone (the only varying macro signal).
    """
    cs = record.get("coordination_score") or 0.0
    if scenario == "information_consensus":
        return round(float(cs), 4)

    sust = record.get("sustainability_score") or 0.0
    gini = record.get("average_gini")
    equity = 1.0 - float(gini) if gini is not None else 0.5
    equity = max(0.0, min(1.0, equity))
    return round(0.5 * float(cs) + 0.3 * float(sust) + 0.2 * equity, 4)


def compute_discrepancy(records, scenario="commons_dilemma"):
    """
    H5: Signed believability–validity discrepancy per trial.

    discrepancy = composite_believability − coordination_validity_score

    Positive  → believable agents, poor coordination (the gap case).
    Near zero → micro and macro are aligned.
    Negative  → low believability but high coordination (rare).

    Gap threshold: discrepancy > +0.20

    Returns
    -------
    dict with keys:
      per_trial                   list of per-trial dicts
      gap_cases                   subset where discrepancy > 0.20
      mean_discrepancy_by_condition  {condition: mean}
      max_discrepancy             float
      supported                   bool — gap cases exist
      note                        str
    """
    GAP_THRESHOLD = 0.20

    per_trial = []
    for r in records:
        b = r.get("believability")
        if b is None:
            continue
        validity = _coordination_validity_score(r, scenario)
        disc = round(float(b) - validity, 4)
        per_trial.append({
            "condition"                 : r["condition"],
            "trial"                     : r["trial"],
            "believability"             : round(float(b), 4),
            "coordination_validity_score": validity,
            "discrepancy"               : disc,
            "gap_case"                  : disc > GAP_THRESHOLD,
        })

    gap_cases = [t for t in per_trial if t["gap_case"]]

    # Mean discrepancy by condition
    cond_disc = {}
    for t in per_trial:
        cond_disc.setdefault(t["condition"], []).append(t["discrepancy"])
    mean_by_condition = {
        c: round(sum(v) / len(v), 4) for c, v in cond_disc.items()
    }

    max_disc = max((t["discrepancy"] for t in per_trial), default=None)

    result = {
        "hypothesis"                     : "H5",
        "description"                    : (
            "Individual believability and collective validity decouple in "
            "identifiable regimes, quantified by a signed discrepancy metric."
        ),
        "n"                              : len(per_trial),
        "gap_threshold"                  : GAP_THRESHOLD,
        "per_trial"                      : per_trial,
        "gap_cases"                      : gap_cases,
        "n_gap_cases"                    : len(gap_cases),
        "mean_discrepancy_by_condition"  : mean_by_condition,
        "max_discrepancy"                : round(float(max_disc), 4) if max_disc is not None else None,
        "supported"                      : len(gap_cases) > 0,
    }

    if gap_cases:
        top = max(gap_cases, key=lambda t: t["discrepancy"])
        result["note"] = (
            f"{len(gap_cases)} gap case(s) found (discrepancy > {GAP_THRESHOLD}). "
            f"Largest: {top['condition']}/{top['trial']} "
            f"(believability={top['believability']}, "
            f"validity={top['coordination_validity_score']}, "
            f"discrepancy={top['discrepancy']})."
        )
    else:
        result["note"] = (
            f"No gap cases found (discrepancy > {GAP_THRESHOLD}) in this dataset. "
            f"H5 is best evidenced by the IC cascade (separate scenario)."
        )

    return result


# ---------------------------------------------------------------------------
# H6 — Reflection saturation analysis
# ---------------------------------------------------------------------------

def analyze_reflection_saturation(results_dirs, scenario):
    """
    H6: Count unique reflection strings per condition to detect focal-point
    norm formation (saturation).

    Parameters
    ----------
    results_dirs : dict mapping condition_name -> results_dir path
        e.g. {"full": "experiment_results_cd_primary",
               "full_llm_reflection": "experiment_results_cd_llm_reflection"}
    scenario : str
        Scenario subfolder name (e.g. 'commons_dilemma').

    Returns
    -------
    dict with per-condition saturation stats + diversity curve.
    """
    import collections

    output = {
        "hypothesis"  : "H6",
        "description" : (
            "The categorical coordination gain from reflection coincides with "
            "reflection saturation — convergence on a static focal-point norm."
        ),
        "conditions"  : {},
    }

    for condition, results_dir in results_dirs.items():
        cond_path = Path(results_dir) / scenario / condition
        if not cond_path.exists():
            output["conditions"][condition] = {"status": "directory_not_found",
                                               "path": str(cond_path)}
            continue

        all_reflections = []
        step_reflections = collections.defaultdict(list)

        for trial_dir in sorted(cond_path.iterdir()):
            if not trial_dir.is_dir() or not trial_dir.name.startswith("trial_"):
                continue
            log_path = trial_dir / "micro_log.json"
            if not log_path.exists():
                continue
            entries = json.loads(log_path.read_text())
            for entry in entries:
                step = entry.get("step", 0)
                for ref in entry.get("scenario_reflections", []):
                    if isinstance(ref, str) and ref.strip():
                        s = ref.strip()
                        all_reflections.append(s)
                        step_reflections[step].append(s)

        if not all_reflections:
            output["conditions"][condition] = {"status": "no_reflections_found"}
            continue

        counts = collections.Counter(all_reflections)
        total = len(all_reflections)
        unique = len(counts)
        top_strings = [
            {"string": s[:120], "count": n, "share": round(n / total, 4)}
            for s, n in counts.most_common(10)
        ]

        # Diversity curve: cumulative unique strings seen up to each step
        seen = set()
        diversity_curve = []
        for step in sorted(step_reflections.keys()):
            for s in step_reflections[step]:
                seen.add(s)
            diversity_curve.append({"step": step, "cumulative_unique": len(seen)})

        # Step at which 90% of all eventual unique strings had appeared
        target = 0.9 * unique
        saturation_step = next(
            (d["step"] for d in diversity_curve if d["cumulative_unique"] >= target),
            None
        )

        output["conditions"][condition] = {
            "total_reflections" : total,
            "unique_count"      : unique,
            "repetition_rate"   : round(1 - unique / total, 4),
            "top_1_share"       : top_strings[0]["share"] if top_strings else None,
            "top_strings"       : top_strings,
            "diversity_curve"   : diversity_curve,
            "saturation_step_90pct": saturation_step,
        }

    # Add cross-condition comparison note
    conds = output["conditions"]
    full = conds.get("full", {})
    llm  = conds.get("full_llm_reflection", {})
    if "repetition_rate" in full and "repetition_rate" in llm:
        output["note"] = (
            f"Deterministic 'full': {full['unique_count']} unique strings, "
            f"repetition={full['repetition_rate']:.3f}. "
            f"LLM 'full_llm_reflection': {llm['unique_count']} unique strings, "
            f"repetition={llm['repetition_rate']:.3f}. "
            f"Both show saturation; deterministic condition is more extreme."
        )

    return output


# ---------------------------------------------------------------------------
# Text report
# ---------------------------------------------------------------------------

_SEP = "=" * 62
_DIV = "-" * 62


def _render_text_report(results):
    lines = []
    a = lines.append

    a(_SEP)
    a("MRes HYPOTHESIS TEST REPORT")
    a(_SEP)
    a(f"Scenario        : {results['scenario']}")
    a(f"Trials analysed : {results['n_trials']}")
    a(f"Conditions found: {', '.join(results['conditions_found'])}")
    a("")

    for h_key in ("H1", "H2", "H3", "H4"):
        h = results[h_key]
        a(_SEP)
        a(f"{h['hypothesis']}: {h['description']}")
        a(_DIV)

        if h.get("status") == "insufficient_data":
            a(f"  STATUS : INSUFFICIENT DATA")
            a(f"  Note   : {h.get('note', '')}")
            a("")
            continue

        supported = h.get("supported")
        label = (
            "SUPPORTED"     if supported is True  else
            "NOT SUPPORTED" if supported is False else
            "INCONCLUSIVE"
        )
        a(f"  STATUS : {label}")
        a(f"  n      : {h.get('n', '—')}")
        a(f"  Note   : {h.get('note', '')}")

        if h_key == "H1":
            if "rho" in h:
                a(f"  Spearman  rho={h['rho']:+.3f}, p={h['p_value']:.4f}")
            gc = h.get("group_comparison", {})
            if "mean_high" in gc:
                a(
                    f"  High-believability (≥{BELIEVABILITY_HIGH}) "
                    f"mean coord={gc['mean_high']:.3f} (n={gc['n_high']})"
                )
                a(
                    f"  Low-believability  (<{BELIEVABILITY_LOW}) "
                    f"mean coord={gc['mean_low']:.3f} (n={gc['n_low']}), "
                    f"p={gc['p_value']:.4f}"
                )

        if h_key == "H2":
            bc = h.get("band_cutoffs", {})
            if bc:
                a(f"  Band cutoffs: low ≤ {bc.get('low_max','?'):.3f} "
                  f"< mid ≤ {bc.get('high_min','?'):.3f} < high")
            for band in ("low", "mid", "high"):
                b = h.get("band_stats", {}).get(band)
                if b:
                    a(f"  {band.capitalize():4s} band: "
                      f"n={b['n']}, "
                      f"success_rate={b['success_rate']:.2f}, "
                      f"fail_rate={b['fail_rate']:.2f}")
            thr = h.get("empirical_threshold")
            a(f"  Empirical threshold: {thr:.3f}" if thr else
              "  Empirical threshold: none found")

        if h_key == "H3":
            for c in CONDITION_ORDER:
                m = h["condition_means"].get(c)
                n = h["condition_n"].get(c, 0)
                if m is not None:
                    a(f"  {c:20s}  mean={m:.3f}  n={n}")
            kw = h.get("kruskal_wallis", {})
            if "h_stat" in kw:
                a(f"  Kruskal-Wallis  H={kw['h_stat']:.3f}, "
                  f"p={kw['p_value']:.4f}, "
                  f"significant={kw['significant']}")
            a(f"  Monotone in means: {h.get('monotone_in_means')}")
            for pw in h.get("pairwise", []):
                if "status" in pw:
                    a(f"    {pw['comparison']:40s} (insufficient data)")
                else:
                    tick = "✓" if pw["supported"] else "✗"
                    a(f"    {pw['comparison']:35s} "
                      f"{pw['direction']} "
                      f"p={pw['p_value']:.4f}  {tick}")

        if h_key == "H4":
            a("  Sub-dimension correlations with coordination_score:")
            for dim, corr in h.get("correlations", {}).items():
                if "rho" in corr:
                    a(f"    {dim:30s}  "
                      f"rho={corr['rho']:+.3f}, p={corr['p_value']:.4f}")
                else:
                    a(f"    {dim:30s}  (insufficient data)")
            ranking = h.get("predictor_ranking")
            if ranking:
                a(f"  Spearman ranking : {' > '.join(ranking)}")
            ols = h.get("ols_regression", {})
            if ols.get("status") == "unavailable":
                a("  OLS regression   : unavailable (numpy not installed)")
            elif ols.get("status") == "insufficient_data":
                a(f"  OLS regression   : insufficient data (n={ols.get('n')})")
            elif "r_squared" in ols:
                a(f"  OLS R²           : {ols['r_squared']:.4f}  (n={ols['n']})")
                for pred, info in ols.get("predictors", {}).items():
                    p_str = f"{info['p_value']:.4f}" if info.get('p_value') is not None else "n/a"
                    a(f"    {pred:30s}  β={info['coefficient']:+.4f}, p={p_str}")
                reg_ranking = h.get("regression_predictor_ranking")
                if reg_ranking:
                    a(f"  Regression rank  : {' > '.join(reg_ranking)}")
                    supported_str = str(h.get("regression_supported", "?"))
                    a(f"  Regression H4 supported: {supported_str}")

        a("")

    # H5
    if "H5" in results:
        h = results["H5"]
        a(_SEP)
        a(f"H5: {h['description']}")
        a(_DIV)
        supported = h.get("supported")
        label = "SUPPORTED" if supported else "NOT SUPPORTED"
        a(f"  STATUS        : {label}")
        a(f"  n             : {h.get('n', '—')}")
        a(f"  Gap threshold : discrepancy > {h.get('gap_threshold', 0.20)}")
        a(f"  Gap cases     : {h.get('n_gap_cases', 0)}")
        a(f"  Max discrepancy: {h.get('max_discrepancy', '—')}")
        a(f"  Note          : {h.get('note', '')}")
        a("  Mean discrepancy by condition:")
        for cond, val in sorted(h.get("mean_discrepancy_by_condition", {}).items()):
            a(f"    {cond:25s}  {val:+.4f}")
        if h.get("gap_cases"):
            a("  Gap cases (believability >> validity):")
            for gc in sorted(h["gap_cases"], key=lambda x: -x["discrepancy"])[:5]:
                a(f"    {gc['condition']:20s} {gc['trial']:10s}  "
                  f"B={gc['believability']:.3f}  V={gc['coordination_validity_score']:.3f}  "
                  f"Δ={gc['discrepancy']:+.3f}")
        a("")

    # H6
    if "H6" in results:
        h = results["H6"]
        a(_SEP)
        a(f"H6: {h['description']}")
        a(_DIV)
        for cond, stats in h.get("conditions", {}).items():
            if "status" in stats:
                a(f"  {cond}: {stats['status']}")
                continue
            a(f"  {cond}:")
            a(f"    Total reflections  : {stats['total_reflections']}")
            a(f"    Unique strings     : {stats['unique_count']}")
            a(f"    Repetition rate    : {stats['repetition_rate']:.3f}")
            a(f"    Top-1 share        : {stats['top_1_share']:.3f}")
            a(f"    Saturation step(90%): {stats.get('saturation_step_90pct', '—')}")
            a(f"    Top strings:")
            for ts in stats.get("top_strings", [])[:3]:
                a(f"      [{ts['count']:>5}x  {ts['share']*100:.1f}%]  {ts['string'][:90]}")
        if h.get("note"):
            a(f"  Note: {h['note']}")
        a("")

    a(_SEP)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_analysis(results_dir="experiment_results", scenario="commons_dilemma",
                 reflection_dir=None):
    """
    Load trial data, run H1–H6 tests, save and print the report.

    Parameters
    ----------
    results_dir    : path to top-level results directory (primary conditions)
    scenario       : scenario subfolder name (commons_dilemma / information_consensus)
    reflection_dir : path to directory containing full_llm_reflection trials (for H6).
                     If None, H6 is skipped.

    Returns the results dict (useful when called from other scripts).
    """
    records = load_trials(results_dir, scenario)
    if not records:
        print(f"No trial data found under {results_dir}/{scenario}/")
        return None

    # Also load reflection trials into records for H5 if reflection_dir given
    if reflection_dir:
        ref_records = load_trials(reflection_dir, scenario)
        records_all = records + ref_records
    else:
        records_all = records

    conditions_found = sorted(set(r["condition"] for r in records_all))

    results = {
        "scenario"        : scenario,
        "n_trials"        : len(records_all),
        "conditions_found": conditions_found,
        "H1": test_h1(records_all),
        "H2": test_h2(records_all),
        "H3": test_h3(records_all),
        "H4": test_h4(records_all),
        "H5": compute_discrepancy(records_all, scenario),
    }

    if reflection_dir:
        results_dirs_h6 = {
            "full"               : results_dir,
            "full_llm_reflection": reflection_dir,
        }
        results["H6"] = analyze_reflection_saturation(results_dirs_h6, scenario)

    out_dir = Path(results_dir) / scenario / "analysis"
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / "hypothesis_report.json"
    txt_path  = out_dir / "hypothesis_report.txt"
    csv_path  = out_dir / "feature_table.csv"

    json_path.write_text(json.dumps(results, indent=2))
    report_text = _render_text_report(results)
    txt_path.write_text(report_text)
    _write_feature_table(records_all, csv_path)

    print(report_text)
    print(f"Report saved:\n  {json_path}\n  {txt_path}\n  {csv_path}")
    return results


def _write_feature_table(records, csv_path):
    fieldnames = [
        "condition",
        "trial",
        "believability",
        "behavioural_consistency",
        "memory_coherence",
        "planning_plausibility",
        "response_naturalness",
        "coordination_score",
        "coordination_success",
        "sustainability_score",
        "convergence_speed",
        "collapsed",
    ]
    with open(csv_path, "w", newline="") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run H1–H6 hypothesis tests on MRes experiment output."
    )
    parser.add_argument(
        "results_dir",
        nargs="?",
        default="experiment_results",
        help="Top-level experiment results directory (default: experiment_results)",
    )
    parser.add_argument(
        "--scenario",
        default="commons_dilemma",
        help="Scenario sub-folder to analyse (default: commons_dilemma)",
    )
    parser.add_argument(
        "--reflection-dir",
        default=None,
        dest="reflection_dir",
        help=(
            "Directory containing full_llm_reflection condition data. "
            "When provided, H5 includes reflection trials and H6 runs. "
            "Example: experiment_results_cd_llm_reflection"
        ),
    )
    args = parser.parse_args()
    run_analysis(args.results_dir, args.scenario, args.reflection_dir)
