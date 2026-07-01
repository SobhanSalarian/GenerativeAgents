#!/usr/bin/env python3
"""
analyse_ic_counterbalance.py  --  IC option counterbalancing (Amin comment 4).

The primary Information-Consensus result (baseline converges unanimously on a
WRONG option) fixed the option set, order, and correct option.  Comment 4: a
reviewer can argue the failure is label/position salience, not social-information
lock-in.  We ran counterbalanced arms:

  experiment_results_ic_counterbalance_correct_{A,B,C}  (meaningful labels)
  experiment_results_ic_neutral_correct_{A_as_X,B_as_Y} (neutral labels)

each with baseline + full conditions.  This script reports baseline and full
coordination success as a function of which option is correct.

Key diagnostic: if baseline fails ONLY when the correct option is the
first-listed one (A / X) and succeeds otherwise, the unanimous-wrong convergence
is confounded with option POSITION and cannot be cleanly attributed to pure
signal-discounting lock-in.  The paper must report this honestly.

Usage:
    cd reverie/backend_server
    python analysis/analyse_ic_counterbalance.py
"""
import glob
import json

import numpy as np

from _paths import rpath

MEANINGFUL = [
    ("correct=A (1st)", "experiment_results_ic_counterbalance_correct_A", "information_consensus"),
    ("correct=B (2nd)", "experiment_results_ic_counterbalance_correct_B", "information_consensus"),
    ("correct=C (3rd)", "experiment_results_ic_counterbalance_correct_C", "information_consensus"),
]
NEUTRAL = [
    ("correct=X (1st)", "experiment_results_ic_neutral_correct_A_as_X", "information_consensus_neutral"),
    ("correct=Y (2nd)", "experiment_results_ic_neutral_correct_B_as_Y", "information_consensus_neutral"),
]


def cell(root, scenario, cond):
    files = sorted(glob.glob(rpath(root, scenario, cond, "trial_*", "macro_summary.json")))
    succ = sum(1 for f in files if json.load(open(f)).get("coordination_success"))
    coord = [json.load(open(f)).get("coordination_score", float("nan")) for f in files]
    return len(files), succ, (np.nanmean(coord) if coord else float("nan"))


def block(title, arms):
    print(f"\n{title}")
    print(f"  {'correct option':16s} {'baseline':>22s} {'full':>22s}")
    for label, root, scen in arms:
        nb, sb, cb = cell(root, scen, "baseline")
        nf, sf, cf = cell(root, scen, "full")
        bstr = f"{sb}/{nb} ({100*sb/nb:.0f}%) c={cb:.2f}" if nb else "n/a"
        fstr = f"{sf}/{nf} ({100*sf/nf:.0f}%) c={cf:.2f}" if nf else "n/a"
        print(f"  {label:16s} {bstr:>22s} {fstr:>22s}")


def main():
    print("=" * 70)
    print("IC OPTION COUNTERBALANCING (comment 4): success by correct option")
    print("=" * 70)
    block("Meaningful labels (A/B/C):", MEANINGFUL)
    block("Neutral labels (X/Y):", NEUTRAL)
    print("\nRead-out: baseline success depends on WHICH option is correct — it")
    print("fails when the correct option is the first-listed one and succeeds")
    print("otherwise, and the pattern persists under neutral labels.  This is an")
    print("option-POSITION effect: the unanimous-wrong convergence cannot be")
    print("cleanly separated from label/position salience, so the IC result must")
    print("be framed as cascade-like with an acknowledged salience confound, not")
    print("as pure social-information lock-in.")


if __name__ == "__main__":
    main()
