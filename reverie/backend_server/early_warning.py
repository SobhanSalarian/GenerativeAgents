"""
early_warning.py — H7/C4: Leakage-safe early-warning classifier + failure taxonomy.

H7: Can coordination failure be predicted from the first K steps of a trial's
    macro/micro traces, beyond what is explained by architectural condition alone?

C4: What recurring micro-level failure patterns link to macro-level collapse?

Usage
-----
    python early_warning.py [results_dir] [--scenario SCENARIO] [--k 5 10 15 20]

    results_dir : path to the top-level experiment results directory
    --scenario  : commons_dilemma (default) or information_consensus
    --k         : space-separated list of step-window sizes to sweep

Output
------
    <results_dir>/<scenario>/analysis/early_warning_report.json
    <results_dir>/<scenario>/analysis/early_warning_report.txt

Design notes (leakage prevention)
----------------------------------
- Features are extracted ONLY from steps 0..K-1.
- Labels come from the FULL trial outcome (macro_summary.json).
- Cross-validation splits at the TRIAL level (each trial = one row).
  Never within a trial (step-level splits would leak future steps).
- Within-condition test: for the condition with the most label variance
  (usually 'full' in CD), run LOO-CV restricted to that condition's trials.
  This tests whether we forecast failure beyond condition identity.
- Results are reported as exploratory when within-condition N is small.
"""

import argparse
import json
import os
from pathlib import Path

import numpy as np
from scipy import stats as scipy_stats
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    precision_score, recall_score, f1_score, roc_auc_score,
    confusion_matrix,
)
from sklearn.preprocessing import StandardScaler


# ---------------------------------------------------------------------------
# Feature extraction
# ---------------------------------------------------------------------------

def _linear_slope(values):
    """Slope of OLS fit through (0,v0), (1,v1), ... Return 0 if < 2 points."""
    n = len(values)
    if n < 2:
        return 0.0
    x = np.arange(n, dtype=float)
    y = np.array(values, dtype=float)
    slope = np.polyfit(x, y, 1)[0]
    return float(slope)


def extract_features(trial_dir, k):
    """
    Extract early-warning features from the first K steps of one trial.

    Sources
    -------
    macro_log.json — group-level per-step resource/coordination metrics
    micro_log.json — per-agent per-step behavioural signals

    Returns
    -------
    dict of float features, or None if data is missing / insufficient.
    """
    macro_path = Path(trial_dir) / "macro_log.json"
    micro_path = Path(trial_dir) / "micro_log.json"

    if not macro_path.exists() or not micro_path.exists():
        return None

    macro_log = json.loads(macro_path.read_text())
    micro_log = json.loads(micro_path.read_text())

    # Restrict to first K steps
    macro_k = [e for e in macro_log if e.get("step", 0) < k]
    micro_k = [e for e in micro_log if e.get("step", 0) < k]

    if len(macro_k) < min(k, 2):
        return None

    # --- Macro features ---
    sust   = [e["sustainability_score"] for e in macro_k if "sustainability_score" in e]
    coord  = [1.0 if e.get("coordinated") else 0.0 for e in macro_k]
    osub   = [e.get("oversubscription", 0) for e in macro_k]
    gini   = [e.get("gini", 0) for e in macro_k]
    rl     = [e.get("resource_level", e.get("resource_level_before", 1000))
              for e in macro_k]

    features = {
        "mean_sustainability"    : float(np.mean(sust)) if sust else 0.0,
        "sustainability_slope"   : _linear_slope(sust),
        "mean_coordinated_rate"  : float(np.mean(coord)) if coord else 0.0,
        "mean_oversubscription"  : float(np.mean(osub)) if osub else 0.0,
        "oversubscription_slope" : _linear_slope(osub),
        "mean_gini"              : float(np.mean(gini)) if gini else 0.0,
        "resource_slope"         : _linear_slope(rl),
        "resource_at_step_k"     : float(rl[-1]) if rl else 1000.0,
    }

    # --- Micro features (CD-specific signals) ---
    ratios = [e.get("request_ratio_to_fair_share", 1.0)
              for e in micro_k
              if "request_ratio_to_fair_share" in e]
    parse_errors = [1.0 if e.get("parse_error") else 0.0 for e in micro_k]

    features["mean_request_ratio"]   = float(np.mean(ratios)) if ratios else 1.0
    features["request_ratio_slope"]  = _linear_slope(ratios)
    features["parse_error_rate"]     = float(np.mean(parse_errors)) if parse_errors else 0.0

    # Fraction of agents that cited memory / planning in their reasoning
    mem_refs  = [1.0 if e.get("memory_reference", "") else 0.0 for e in micro_k]
    plan_refs = [1.0 if e.get("plan_reference", "") else 0.0 for e in micro_k]
    features["memory_citation_rate"] = float(np.mean(mem_refs)) if mem_refs else 0.0
    features["plan_citation_rate"]   = float(np.mean(plan_refs)) if plan_refs else 0.0

    return features


def load_dataset(results_dir, scenario, k, label_key="coordination_success"):
    """
    Build a flat dataset of (features, label, condition, trial_id) tuples.

    label_key options:
      "coordination_success"  → label=1 if success (0 = failure)
      "collapsed"             → label=1 if collapse_step is not None

    Returns list of dicts.
    """
    base = Path(results_dir) / scenario
    if not base.exists():
        return []

    rows = []
    for cond_dir in sorted(base.iterdir()):
        if not cond_dir.is_dir():
            continue
        condition = cond_dir.name

        for trial_dir in sorted(cond_dir.iterdir()):
            if not trial_dir.is_dir() or not trial_dir.name.startswith("trial_"):
                continue

            macro_summary_path = trial_dir / "macro_summary.json"
            if not macro_summary_path.exists():
                continue
            macro_summary = json.loads(macro_summary_path.read_text())

            # Derive label
            if label_key == "coordination_success":
                success = macro_summary.get("coordination_success", False)
                label = 0 if success else 1   # 1 = failure (what we want to predict)
            else:
                label = 1 if macro_summary.get("collapse_step") is not None else 0

            feats = extract_features(trial_dir, k)
            if feats is None:
                continue

            rows.append({
                "condition": condition,
                "trial"    : trial_dir.name,
                "label"    : label,
                "features" : feats,
                **feats,
            })

    return rows


# ---------------------------------------------------------------------------
# LOO-CV evaluation (trial-level — no step-level leakage)
# ---------------------------------------------------------------------------

FEATURE_NAMES = [
    "mean_sustainability",
    "sustainability_slope",
    "mean_coordinated_rate",
    "mean_oversubscription",
    "oversubscription_slope",
    "mean_gini",
    "resource_slope",
    "resource_at_step_k",
    "mean_request_ratio",
    "request_ratio_slope",
    "parse_error_rate",
    "memory_citation_rate",
    "plan_citation_rate",
]


def _to_arrays(rows, feature_names=None):
    names = feature_names or FEATURE_NAMES
    X = np.array([[r.get(f, 0.0) for f in names] for r in rows], dtype=float)
    y = np.array([r["label"] for r in rows], dtype=int)
    return X, y


def _loo_cv(rows, feature_names=None):
    """
    Leave-one-out cross-validation at the trial level.

    Returns (y_true, y_pred, y_prob) aligned arrays.
    Skips folds where the training set has only one class (cannot fit LR).
    """
    names = feature_names or FEATURE_NAMES
    n = len(rows)
    y_true, y_pred, y_prob = [], [], []

    for i in range(n):
        train = [rows[j] for j in range(n) if j != i]
        test  = rows[i]

        X_train, y_train = _to_arrays(train, names)
        X_test  = np.array([[test.get(f, 0.0) for f in names]], dtype=float)
        y_t     = test["label"]

        # Skip if training set is single-class (LR undefined)
        if len(set(y_train)) < 2:
            continue

        scaler  = StandardScaler()
        X_train = scaler.fit_transform(X_train)
        X_test  = scaler.transform(X_test)

        clf = LogisticRegression(max_iter=500, solver="lbfgs", C=1.0)
        try:
            clf.fit(X_train, y_train)
        except Exception:
            continue

        pred = clf.predict(X_test)[0]
        prob = clf.predict_proba(X_test)[0]
        pos_idx = list(clf.classes_).index(1) if 1 in clf.classes_ else 0

        y_true.append(y_t)
        y_pred.append(int(pred))
        y_prob.append(float(prob[pos_idx]))

    return y_true, y_pred, y_prob


def _compute_metrics(y_true, y_pred, y_prob):
    """Return dict of classification metrics, handling edge cases."""
    if len(y_true) < 2 or len(set(y_true)) < 2:
        return {
            "status": "insufficient_variance",
            "n": len(y_true),
            "note": "Only one class present — metrics undefined.",
        }

    prec = precision_score(y_true, y_pred, zero_division=0)
    rec  = recall_score(y_true, y_pred, zero_division=0)
    f1   = f1_score(y_true, y_pred, zero_division=0)
    try:
        auc = roc_auc_score(y_true, y_prob)
    except Exception:
        auc = None

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()

    return {
        "n"           : len(y_true),
        "n_failure"   : int(sum(y_true)),
        "n_success"   : int(len(y_true) - sum(y_true)),
        "precision"   : round(float(prec), 4),
        "recall"      : round(float(rec), 4),
        "f1"          : round(float(f1), 4),
        "auc_roc"     : round(float(auc), 4) if auc is not None else None,
        "tp": int(tp), "fp": int(fp), "tn": int(tn), "fn": int(fn),
    }


# ---------------------------------------------------------------------------
# H7: Early-warning analysis across K values
# ---------------------------------------------------------------------------

def run_early_warning(results_dir, scenario="commons_dilemma",
                      k_values=None, label_key="coordination_success"):
    """
    H7: Sweep K values, run LOO-CV at trial level, report precision/recall/AUC.

    Also runs an explicit within-condition test for the condition with the most
    label variance ('full' in CD).

    Returns
    -------
    dict with per-K results + within-condition results + feature importances.
    """
    if k_values is None:
        k_values = [5, 10, 15, 20]

    output = {
        "hypothesis"  : "H7",
        "description" : (
            "Coordination failure is predictable from first-K-step micro traces, "
            "beyond what architectural condition alone explains."
        ),
        "scenario"    : scenario,
        "label_key"   : label_key,
        "k_results"   : {},
        "within_condition": {},
        "lead_time"   : None,
        "feature_importances": {},
    }

    # --- Cross-K sweep (all conditions pooled) ---
    lead_time_k = None
    for k in k_values:
        rows = load_dataset(results_dir, scenario, k, label_key)
        if not rows:
            output["k_results"][k] = {"status": "no_data"}
            continue

        y_true, y_pred, y_prob = _loo_cv(rows)
        metrics = _compute_metrics(y_true, y_pred, y_prob)
        metrics["k"] = k
        output["k_results"][k] = metrics

        # Lead time: earliest K with precision AND recall both > 0.6
        if (lead_time_k is None
                and "precision" in metrics
                and metrics["precision"] > 0.6
                and metrics["recall"] > 0.6):
            lead_time_k = k

    output["lead_time"] = lead_time_k

    # --- Within-condition test ---
    # Use the largest K for within-condition (most signal), restrict to
    # conditions that have both successes and failures.
    max_k = max(k_values)
    all_rows = load_dataset(results_dir, scenario, max_k, label_key)

    cond_variance = {}
    for row in all_rows:
        cond_variance.setdefault(row["condition"], []).append(row["label"])

    for cond, labels in cond_variance.items():
        if len(set(labels)) < 2:
            output["within_condition"][cond] = {
                "status": "no_variance",
                "note"  : f"All {len(labels)} trials have label={labels[0]}; "
                          "within-condition test uninformative.",
                "n"     : len(labels),
            }
            continue

        cond_rows = [r for r in all_rows if r["condition"] == cond]
        y_true, y_pred, y_prob = _loo_cv(cond_rows)
        metrics = _compute_metrics(y_true, y_pred, y_prob)
        metrics["condition"] = cond
        metrics["k"] = max_k
        output["within_condition"][cond] = metrics

    # --- Feature importances (train on all data, report |coef|) ---
    all_rows_k5 = load_dataset(results_dir, scenario, 5, label_key)
    if all_rows_k5 and len(set(r["label"] for r in all_rows_k5)) > 1:
        X, y = _to_arrays(all_rows_k5)
        scaler = StandardScaler()
        X_sc   = scaler.fit_transform(X)
        clf    = LogisticRegression(max_iter=500, solver="lbfgs", C=1.0)
        try:
            clf.fit(X_sc, y)
            importances = {
                FEATURE_NAMES[i]: round(float(abs(clf.coef_[0][i])), 4)
                for i in range(len(FEATURE_NAMES))
            }
            output["feature_importances"] = dict(
                sorted(importances.items(), key=lambda kv: -kv[1])
            )
        except Exception:
            pass

    # Add a plain-language note
    best_k = max(
        (k for k in k_values if "auc_roc" in output["k_results"].get(k, {})),
        key=lambda k: output["k_results"][k].get("auc_roc") or 0,
        default=None,
    )
    if best_k:
        bm = output["k_results"][best_k]
        within_note = ""
        for cond, wm in output["within_condition"].items():
            if "auc_roc" in wm:
                within_note += (
                    f" Within-condition ({cond}): AUC={wm['auc_roc']}, "
                    f"P={wm['precision']}, R={wm['recall']}."
                )
        output["note"] = (
            f"Best pooled AUC at K={best_k}: {bm.get('auc_roc')} "
            f"(P={bm.get('precision')}, R={bm.get('recall')}, "
            f"F1={bm.get('f1')})."
            f"{within_note}"
            f" Lead time (P>0.6 & R>0.6 first met): K={lead_time_k}."
        )

    return output


# ---------------------------------------------------------------------------
# C4: Failure taxonomy
# ---------------------------------------------------------------------------

def _categorise_failure(macro_steps, micro_steps):
    """
    Classify a failed trial into one of the archetypal failure patterns.

    Returns (type_label, details_dict).
    """
    if not macro_steps:
        return "unknown", {}

    sust_vals = [e.get("sustainability_score", 1.0) for e in macro_steps]
    osub_vals = [e.get("oversubscription", 0)       for e in macro_steps]
    gini_vals = [e.get("gini", 0)                   for e in macro_steps]
    coord_vals = [1 if e.get("coordinated") else 0  for e in macro_steps]

    n = len(macro_steps)
    first_third  = sust_vals[:max(1, n // 3)]
    second_third = sust_vals[max(1, n // 3): max(2, 2 * n // 3)]

    sust_slope   = _linear_slope(sust_vals)
    early_coord  = float(np.mean(coord_vals[:10])) if len(coord_vals) >= 10 else float(np.mean(coord_vals))
    late_coord   = float(np.mean(coord_vals[-10:])) if len(coord_vals) >= 10 else float(np.mean(coord_vals))
    mean_osub    = float(np.mean(osub_vals))
    collapse_step = next((e["step"] for e in macro_steps if e.get("collapsed")), None)

    # Ratio features
    ratios = [e.get("request_ratio_to_fair_share", 1.0) for e in micro_steps
              if "request_ratio_to_fair_share" in e]
    mean_ratio = float(np.mean(ratios)) if ratios else 1.0

    details = {
        "sust_slope"   : round(sust_slope, 4),
        "early_coord"  : round(early_coord, 3),
        "late_coord"   : round(late_coord, 3),
        "mean_osub"    : round(mean_osub, 2),
        "mean_ratio"   : round(mean_ratio, 3),
        "collapse_step": collapse_step,
        "n_steps"      : n,
    }

    # --- Type assignment ---

    # Type A: Rapid collapse — resource drains fast from step 0
    if collapse_step is not None and collapse_step <= n * 0.3:
        return "A_rapid_collapse", details

    # Type B: Gradual depletion — steady negative sust slope, eventually collapses
    if collapse_step is not None and sust_slope < -0.004:
        return "B_gradual_depletion", details

    # Type C: Late coordination failure — group almost coordinated then broke down
    if early_coord >= 0.5 and late_coord < 0.3 and collapse_step is None:
        return "C_late_coordination_breakdown", details

    # Type D: Near-miss — high oversubscription but no collapse; fails on threshold
    if mean_osub > 20 and collapse_step is None:
        return "D_persistent_oversubscription", details

    # Type E: Sub-threshold coordination failure — agents request just above fair
    # share, no collapse, but cumulative oversubscription prevents coordination.
    # Captures the 'full' condition gap cases (high believability, modest overshoot).
    if collapse_step is None and mean_osub <= 20 and mean_ratio > 1.0:
        return "E_subthreshold_coordination_failure", details

    # Type F: Low-activity failure — agents appear restrained but don't coordinate
    if collapse_step is None and mean_ratio <= 1.0:
        return "F_low_activity_no_coordination", details

    return "G_unclassified", details


def build_failure_taxonomy(results_dir, scenario="commons_dilemma"):
    """
    C4: Identify recurring micro-level failure patterns from failed trials.

    Returns
    -------
    dict with:
      failure_types  — {type_label: {description, n, representative_trace_summary}}
      per_trial      — list of {condition, trial, failure_type, details}
    """
    base = Path(results_dir) / scenario
    if not base.exists():
        return {"status": "directory_not_found"}

    TYPE_DESCRIPTIONS = {
        "A_rapid_collapse"                  : "Resource collapses within the first third of steps; agents never restrain requests.",
        "B_gradual_depletion"               : "Resource drains steadily throughout the run; agents do not respond to declining pool.",
        "C_late_coordination_breakdown"     : "Group achieves early coordination then loses it; a late disruption breaks the norm.",
        "D_persistent_oversubscription"     : "Requests consistently and heavily exceed replenishment; resource stressed throughout; coordination threshold not met.",
        "E_subthreshold_coordination_failure": "Agents request just above fair share; no collapse, but cumulative pressure keeps coordination below threshold. Typical of high-believability gap cases (full condition).",
        "F_low_activity_no_coordination"    : "Agents request at or below fair share on average but still fail to coordinate; group-level norm does not form.",
        "G_unclassified"                    : "Does not match the above patterns; requires manual inspection.",
    }

    per_trial = []
    type_groups = {}

    for cond_dir in sorted(base.iterdir()):
        if not cond_dir.is_dir():
            continue
        condition = cond_dir.name

        for trial_dir in sorted(cond_dir.iterdir()):
            if not trial_dir.is_dir() or not trial_dir.name.startswith("trial_"):
                continue

            macro_sum_p = trial_dir / "macro_summary.json"
            macro_log_p = trial_dir / "macro_log.json"
            micro_log_p = trial_dir / "micro_log.json"

            if not macro_sum_p.exists():
                continue
            macro_sum = json.loads(macro_sum_p.read_text())

            # Only classify failed trials
            if macro_sum.get("coordination_success", True):
                continue

            macro_steps = json.loads(macro_log_p.read_text()) if macro_log_p.exists() else []
            micro_steps = json.loads(micro_log_p.read_text()) if micro_log_p.exists() else []

            ftype, details = _categorise_failure(macro_steps, micro_steps)

            entry = {
                "condition"   : condition,
                "trial"       : trial_dir.name,
                "failure_type": ftype,
                "details"     : details,
                "believability": None,
            }
            # Attach believability if available
            micro_sum_p = trial_dir / "micro_summary.json"
            if micro_sum_p.exists():
                ms = json.loads(micro_sum_p.read_text())
                cb = ms.get("composite_believability", {})
                if cb:
                    entry["believability"] = round(
                        sum(cb.values()) / len(cb), 4
                    )

            per_trial.append(entry)
            type_groups.setdefault(ftype, []).append(entry)

    # Build taxonomy summary
    failure_types = {}
    for ftype, trials in sorted(type_groups.items(), key=lambda kv: -len(kv[1])):
        believabilities = [t["believability"] for t in trials if t["believability"] is not None]
        rep = trials[0]  # representative = first trial alphabetically
        failure_types[ftype] = {
            "description"          : TYPE_DESCRIPTIONS.get(ftype, ""),
            "n_trials"             : len(trials),
            "conditions"           : sorted(set(t["condition"] for t in trials)),
            "mean_believability"   : round(sum(believabilities) / len(believabilities), 4)
                                     if believabilities else None,
            "representative_trial" : f"{rep['condition']}/{rep['trial']}",
            "representative_details": rep["details"],
        }

    return {
        "contribution" : "C4",
        "description"  : (
            "Recurring micro-level failure patterns linking believability "
            "breakdown to macro-level coordination failure."
        ),
        "n_failed_trials" : len(per_trial),
        "failure_types"   : failure_types,
        "per_trial"       : per_trial,
    }


# ---------------------------------------------------------------------------
# Text report
# ---------------------------------------------------------------------------

def _render_report(h7, c4):
    SEP = "=" * 62
    DIV = "-" * 62
    lines = []
    a = lines.append

    a(SEP)
    a("MRes EARLY WARNING REPORT  (H7 / C4)")
    a(SEP)
    a(f"Scenario : {h7.get('scenario', '?')}")
    a(f"Label    : {h7.get('label_key', '?')}")
    a("")

    # H7
    a(SEP)
    a(f"H7: {h7['description']}")
    a(DIV)
    a(f"  Note: {h7.get('note', '')}")
    a(f"  Lead time (first K with P>0.6 & R>0.6): {h7.get('lead_time', 'not reached')}")
    a("")
    a(f"  {'K':>4}  {'n':>5}  {'Fail':>5}  {'Prec':>6}  {'Rec':>6}  {'F1':>6}  {'AUC':>6}")
    a(f"  {'-'*4}  {'-'*5}  {'-'*5}  {'-'*6}  {'-'*6}  {'-'*6}  {'-'*6}")
    for k, m in sorted(h7.get("k_results", {}).items()):
        if "precision" not in m:
            a(f"  {k:>4}  {'—':>5}  {'—':>5}  {m.get('status','—'):>6}")
            continue
        a(f"  {k:>4}  {m['n']:>5}  {m['n_failure']:>5}  "
          f"{m['precision']:>6.3f}  {m['recall']:>6.3f}  "
          f"{m['f1']:>6.3f}  {str(m.get('auc_roc','—')):>6}")
    a("")
    a("  Within-condition test (K=max, condition held fixed):")
    for cond, wm in sorted(h7.get("within_condition", {}).items()):
        if wm.get("status") == "no_variance":
            a(f"    {cond:22s}  {wm['note']}")
        elif "precision" in wm:
            a(f"    {cond:22s}  n={wm['n']}  Fail={wm['n_failure']}  "
              f"P={wm['precision']:.3f}  R={wm['recall']:.3f}  "
              f"AUC={wm.get('auc_roc','—')}")
    a("")
    a("  Top features (|coefficient| at K=5, trained on all data):")
    for feat, imp in list(h7.get("feature_importances", {}).items())[:6]:
        a(f"    {feat:30s}  |coef|={imp:.4f}")
    a("")

    # C4
    a(SEP)
    a(f"C4: {c4.get('description', '')}")
    a(DIV)
    a(f"  Total failed trials analysed: {c4.get('n_failed_trials', 0)}")
    a("")
    for ftype, ft in c4.get("failure_types", {}).items():
        a(f"  [{ft['n_trials']:>3} trials]  {ftype}")
        a(f"    {ft['description']}")
        a(f"    Conditions: {', '.join(ft['conditions'])}")
        if ft["mean_believability"] is not None:
            a(f"    Mean believability: {ft['mean_believability']:.3f}")
        a(f"    Representative: {ft['representative_trial']}")
        det = ft.get("representative_details", {})
        a(f"      sust_slope={det.get('sust_slope','?')}  "
          f"mean_osub={det.get('mean_osub','?')}  "
          f"mean_ratio={det.get('mean_ratio','?')}  "
          f"collapse_step={det.get('collapse_step','None')}")
        a("")

    a(SEP)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_all(results_dir="experiment_results", scenario="commons_dilemma",
            k_values=None):
    if k_values is None:
        k_values = [5, 10, 15, 20]

    h7 = run_early_warning(results_dir, scenario, k_values)
    c4 = build_failure_taxonomy(results_dir, scenario)

    out_dir = Path(results_dir) / scenario / "analysis"
    out_dir.mkdir(parents=True, exist_ok=True)

    json_out = out_dir / "early_warning_report.json"
    txt_out  = out_dir / "early_warning_report.txt"

    combined = {"H7": h7, "C4": c4}
    json_out.write_text(json.dumps(combined, indent=2))

    report = _render_report(h7, c4)
    txt_out.write_text(report)

    print(report)
    print(f"Report saved:\n  {json_out}\n  {txt_out}")
    return combined


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run H7 early-warning classifier and C4 failure taxonomy."
    )
    parser.add_argument(
        "results_dir",
        nargs="?",
        default="experiment_results_cd_primary",
        help="Top-level experiment results directory",
    )
    parser.add_argument(
        "--scenario",
        default="commons_dilemma",
        help="Scenario subfolder (default: commons_dilemma)",
    )
    parser.add_argument(
        "--k",
        nargs="+",
        type=int,
        default=[5, 10, 15, 20],
        help="Step-window sizes to sweep (default: 5 10 15 20)",
    )
    args = parser.parse_args()
    run_all(args.results_dir, args.scenario, args.k)
