import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _paths  # noqa: F401  (adds backend_server to sys.path)
_os.chdir(_paths.BACKEND)  # analysis scripts read result dirs relative to backend_server

#!/usr/bin/env python3
"""
reanalysis_c5_norm_fraction.py

Reproduces the paper's §5.4 figure for the exploratory C5 (LLM-generated
reflection) condition: "1,190 unique strings, yet 94.9% of instances repeat a
small set restating the fair-share norm."

The 94.9% is a *semantic* measure: free LLM reflections paraphrase the same
fair-share norm in varied wording, so exact-string deduplication understates the
repetition. We classify a reflection instance as "norm-restating" if its text
contains any of a small set of fair-share-norm keywords. Exact-string dedup is
also reported for the 1,190 unique-string count.

Norm keywords: 'fair', 'replenish', 'sustainab'  (covers "fair share",
"replenishment limit / rate", "sustainable / sustainability").

Usage:
    cd reverie/backend_server
    python reanalysis_c5_norm_fraction.py
"""
import json, glob, os
from collections import Counter

C5_GLOB = "experiment_results_cd_llm_reflection/commons_dilemma/*/trial_*"
NORM_KEYWORDS = ("fair", "replenish", "sustainab")


def collect_c5_reflections():
    refs = []
    for td in glob.glob(C5_GLOB):
        ml = os.path.join(td, "micro_log.json")
        if not os.path.exists(ml):
            continue
        for e in json.load(open(ml)):
            for r in (e.get("scenario_reflections") or []):
                txt = r if isinstance(r, str) else (
                    r.get("text") or r.get("content") or json.dumps(r))
                refs.append(txt.strip())
    return refs


def is_norm_restating(text):
    t = text.lower()
    return any(k in t for k in NORM_KEYWORDS)


def main():
    refs = collect_c5_reflections()
    n = len(refs)
    unique = len(Counter(refs))
    norm = sum(1 for r in refs if is_norm_restating(r))
    print(f"C5 (LLM-generated reflection), CD:")
    print(f"  total instances        : {n}")
    print(f"  unique strings (exact) : {unique}   (paper: 1,190)")
    print(f"  norm-restating share   : {100*norm/n:.1f}%   (paper: 94.9%)")
    print(f"  (keywords: {NORM_KEYWORDS})")


if __name__ == "__main__":
    main()
