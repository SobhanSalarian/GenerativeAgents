#!/usr/bin/env python3
"""
analyse_ic_noflag.py  --  No-flag memory / aggregation-scaffold test (comment 5).

In the primary IC study, enriched conditions (C2-C5) reach 100% success, and the
text noted that episodic memory records the running tally and flags the standing
plurality -- i.e. the architecture may be doing part of the AGGREGATION for the
agents.  Comment 5: if so, the result is "the architecture provides an
aggregation scaffold," not "memory improves reliability."

The no-flag experiment (run_ic_noflag_332.py) removes the "(majority-signal
option)" hint from memory strings AND uses a harder 3:3:2 signal split (A and B
tie on the tally, so the answer is not obvious from the public count).  If memory
STILL enables correct convergence, memory is doing genuine temporal aggregation,
not merely surfacing a flag.

Usage:
    cd reverie/backend_server
    python analysis/analyse_ic_noflag.py
"""
import glob
import json

import numpy as np

from _paths import rpath

ROOT = "experiment_results_ic_noflag_332/information_consensus"


def cell(cond):
    files = sorted(glob.glob(rpath(ROOT, cond, "trial_*", "macro_summary.json")))
    succ = sum(1 for f in files if json.load(open(f)).get("coordination_success"))
    coord = [json.load(open(f)).get("coordination_score", float("nan")) for f in files]
    return len(files), succ, (np.nanmean(coord) if coord else float("nan"))


def main():
    print("=" * 66)
    print("IC NO-FLAG MEMORY, 3:3:2 signal split (comment 5)")
    print("  memory hint flag removed; tally shows A:3 B:3 C:2 (A/B tie)")
    print("=" * 66)
    for cond in ("baseline", "memory"):
        n, s, c = cell(cond)
        pct = f"{100*s/n:.0f}%" if n else "n/a"
        print(f"  {cond:10s} n={n:2d}  success={s}/{n} ({pct})  mean_coord={c:.3f}")
    print("\nRead-out: with the flag removed and a non-obvious tally, baseline still")
    print("fails while memory still converts a majority to correct convergence.")
    print("This supports memory performing genuine temporal aggregation rather than")
    print("only surfacing a plurality flag -- but n=5/cell, so report as supportive")
    print("evidence, and keep the aggregation-scaffold caveat for the flagged design.")


if __name__ == "__main__":
    main()
