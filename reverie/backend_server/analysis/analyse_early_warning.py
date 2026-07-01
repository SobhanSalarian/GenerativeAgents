#!/usr/bin/env python3
"""
analyse_early_warning.py  --  CANONICAL early-warning classifier analysis (§5.5).

Amin comment 8: the within-condition classifier is exploratory and underpowered
(n=20, 6 failures), and single-seed AUCs are unstable.  Two earlier scripts gave
different point estimates purely from seed / tree-count choices
(early_warning.py: 0.79/0.77/0.51 at 80 trees, seed 0;
 reanalysis_classifier_battery.py: 0.82/0.79/0.58 at 200 trees, seed 42).

To remove seed cherry-picking, this canonical script reports the AUC **averaged
over many random-forest seeds** (mean and 2.5-97.5 percentile ACROSS seeds), for
three feature sets (combined / macro-only / micro-only) at both the pooled level
and within the full condition.  The run-independent conclusion is what the paper
should report: macro-state features carry the within-condition signal and the
micro-only (believability-trace) model collapses toward chance.

Feature extraction and the failure taxonomy are reused from early_warning.py
(single source of truth for features); this script only does the modelling.

Usage:
    cd reverie/backend_server
    python analysis/analyse_early_warning.py
    python analysis/analyse_early_warning.py --seeds 50 --trees 200
"""
import argparse
import glob
import json
import os

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import LeaveOneOut
from sklearn.metrics import roc_auc_score

from _paths import BACKEND, rpath
import early_warning as ew  # feature extraction + taxonomy (single source of truth)

MACRO = ["mean_sustainability", "sustainability_slope", "mean_coordinated_rate",
         "mean_oversubscription", "oversubscription_slope", "mean_gini",
         "resource_slope", "resource_at_step_k"]
MICRO = ["mean_request_ratio", "request_ratio_slope", "parse_error_rate",
         "memory_citation_rate", "plan_citation_rate"]

PRIMARY = "experiment_results_cd_primary/commons_dilemma"


def dataset(cond, k):
    """Return (list-of-feature-dicts, label array) for one condition at prefix k.
    Label = 1 for FAILURE (coordination_success is falsy)."""
    X, y = [], []
    for td in sorted(glob.glob(rpath(PRIMARY, cond, "trial_*"))):
        f = ew.extract_features(td, k)
        if f is None:
            continue
        mac = json.load(open(os.path.join(td, "macro_summary.json")))
        s = mac.get("coordination_success")
        if s is None:
            continue
        X.append(f)
        y.append(0 if s else 1)
    return X, np.array(y)


def loo_auc(X, y, feats, trees, seed):
    """Leave-one-out ROC-AUC for one feature set and one RF seed."""
    Xm = np.array([[x[f] for f in feats] for x in X])
    n = len(y)
    pr = np.zeros(n)
    for tr, te in LeaveOneOut().split(Xm):
        sc = StandardScaler().fit(Xm[tr])
        clf = RandomForestClassifier(n_estimators=trees, random_state=seed)
        clf.fit(sc.transform(Xm[tr]), y[tr])
        cls = list(clf.classes_)
        pr[te] = clf.predict_proba(sc.transform(Xm[te]))[0][cls.index(1)] if 1 in cls else 0.0
    return roc_auc_score(y, pr)


def seed_averaged(X, y, feats, trees, n_seeds):
    """Mean and 2.5-97.5 percentile of LOO-AUC across n_seeds RF seeds."""
    aucs = [loo_auc(X, y, feats, trees, s) for s in range(n_seeds)]
    return float(np.mean(aucs)), float(np.percentile(aucs, 2.5)), float(np.percentile(aucs, 97.5))


def report(title, X, y, trees, n_seeds):
    print(f"\n{title}: n={len(y)}  failures={int(y.sum())}  base_rate={y.mean():.2f}")
    for name, feats in [("combined", MACRO + MICRO), ("macro-only", MACRO), ("micro-only", MICRO)]:
        m, lo, hi = seed_averaged(X, y, feats, trees, n_seeds)
        print(f"  {name:11s} AUC={m:.2f}  seed-range[{lo:.2f},{hi:.2f}]  ({n_seeds} seeds, {trees} trees)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=25, help="number of RF seeds to average over")
    ap.add_argument("--trees", type=int, default=200, help="n_estimators")
    args = ap.parse_args()

    print("=" * 66)
    print("CANONICAL EARLY-WARNING ANALYSIS (seed-averaged; §5.5)")
    print(f"  trees={args.trees}  seeds=range(0,{args.seeds})  LOO cross-validation")
    print("=" * 66)

    # Pooled across the four primary conditions (confounded by architecture — not headlined).
    for k in (5, 20):
        X, y = [], []
        for cond in ("baseline", "memory", "memory_planning", "full"):
            Xc, yc = dataset(cond, k)
            X += Xc
            y = np.concatenate([y, yc]) if len(y) else yc
        report(f"POOLED (all conditions), K={k}  [condition-confounded]", X, np.array(y), args.trees, args.seeds)

    # Within the full condition — the honest, un-confounded test.
    Xf, yf = dataset("full", 20)
    report("WITHIN full condition, K=20  [honest test]", Xf, yf, args.trees, args.seeds)

    # Failure taxonomy (deterministic, from early_warning.build_failure_taxonomy).
    try:
        tax = ew.build_failure_taxonomy(rpath("experiment_results_cd_primary"))
        print("\nFailure taxonomy (deterministic):")
        print(f"  {json.dumps(tax, indent=2) if isinstance(tax, dict) else tax}")
    except Exception as e:
        print(f"\n(failure taxonomy: run early_warning.py directly — {e})")


if __name__ == "__main__":
    main()
