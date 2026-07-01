#!/usr/bin/env python3
"""Per-dimension human-pilot reanalysis (comment 2).

Reads pilot_packets/human_eval_ratings.csv (3 raters x 15 packets) and
pilot_packets/pilot_blind_key.json, and reports:
  - per-dimension Krippendorff's alpha (ordinal)
  - per-dimension mean/SD (restricted-variance evidence)
  - per-rater believable verdicts
  - gap-case certification: verdicts on the 0%-success baseline packets
"""
import csv, json, numpy as np
from collections import defaultdict

RAT = "pilot_packets/human_eval_ratings.csv"
KEY = "pilot_packets/pilot_blind_key.json"
DIMS = ["behavioural_consistency", "memory_coherence",
        "planning_plausibility", "response_naturalness"]

def main():
    rows = [r for r in csv.DictReader(open(RAT)) if r.get("rater_id")]
    key = dict(json.load(open(KEY)))
    raters = sorted(set(r["rater_id"] for r in rows))
    packets = sorted(set(r["packet_id"] for r in rows))
    print(f"raters={raters} packets={len(packets)} rated_rows={len(rows)}")

    try:
        import krippendorff
        print("\nPer-dimension Krippendorff alpha (ordinal):")
        for d in DIMS:
            M = np.full((len(raters), len(packets)), np.nan)
            for r in rows:
                if r[d]:
                    M[raters.index(r["rater_id"]), packets.index(r["packet_id"])] = float(r[d])
            print(f"  {d:24s} alpha={krippendorff.alpha(reliability_data=M, level_of_measurement='ordinal'):+.2f}")
    except ImportError:
        print("(pip install krippendorff for alpha)")

    print("\nPer-dimension mean/SD (restricted-variance check):")
    for d in DIMS:
        v = [float(r[d]) for r in rows if r[d]]
        print(f"  {d:24s} mean={np.mean(v):.2f} sd={np.std(v):.2f}")

    print("\nBelievable verdicts per rater (of 15):")
    for rt in raters:
        yn = [r["believable_yes_no"] for r in rows if r["rater_id"] == rt and r["believable_yes_no"]]
        yes = sum(1 for v in yn if str(v).strip().lower() in ("yes","1","y","true"))
        print(f"  {rt}: {yes}/{len(yn)}")

    base = [p for p, m in key.items() if m["experimental_condition"] == "baseline"]
    print(f"\nGap-case certification (0%-success baseline packets {base}):")
    for rt in raters:
        v = {r["packet_id"]: r["believable_yes_no"] for r in rows if r["rater_id"] == rt}
        print(f"  {rt}: {[v.get(p) for p in base]}")

if __name__ == "__main__":
    main()
