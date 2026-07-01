"""
Human-evaluation analysis aligned with Amin's comment 2.

Design (Option 2): the 120-packet balanced set (full_eval_packets/) is the PRIMARY
study; the 15-packet pilot (pilot_packets/) is reported SEPARATELY as the initial
calibration round. Same three blinded raters (R1, R2, R3) throughout.

Amin comment 2 requires, and this script reports:
  (1) multiple blinded raters                         -> design (3 raters)
  (2) inter-rater reliability                          -> per-dimension Krippendorff alpha (ordinal)
  (3) rating rubric and anchors                        -> documented (see RUBRIC below / paper)
  (4) human-automated agreement for EACH dimension     -> per-dimension Spearman rho
                                                          (human mean rating vs automated sub-score)
  (5) ask raters whether gap cases are believable      -> gap-case certification on
                                                          baseline / 0%-success packets

Supporting (DOCX): per-dimension mean/SD (restricted-variance diagnostic); the
alpha>=0.67 blending gate applied honestly (reports which dimensions pass); all
language to be reported as PRELIMINARY convergent validity, not construct validity.

Automated sub-scores are RECOMPUTED from measurement/micro.py via compute_micro_summary
on the FULL trial micro_log (so a persona's score matches how the instrument scores it
over the whole trial, not a single packet in isolation). LLM judges are OFF by default
(heuristic/proxy scores, no API calls); pass --llm to use the LLM-judged sub-scores.

Usage:
    cd reverie/backend_server
    python analyse_human_eval_full.py                 # primary (120) + pilot (15)
    python analyse_human_eval_full.py --llm           # use LLM judges (needs API key, costs)
"""
from __future__ import annotations
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _paths  # noqa: F401  (adds backend_server to sys.path)
_os.chdir(_paths.BACKEND)  # analysis scripts read result dirs relative to backend_server
import argparse, csv, json, os, glob
from collections import defaultdict
import numpy as np
from scipy import stats

DIMS = ["behavioural_consistency", "memory_coherence",
        "planning_plausibility", "response_naturalness"]
ALPHA_GATE = 0.67          # Krippendorff threshold (conventional minimum tentative reliability)

# ---- (3) Rubric anchors (1-5), documented here and in the paper ---------------
RUBRIC = {
    1: "clearly implausible / inconsistent with persona, memory, or goals",
    2: "mostly implausible",
    3: "mixed / borderline",
    4: "mostly plausible",
    5: "clearly plausible and consistent",
}

# ---- automated sub-scores for the rated persona ------------------------------
# Explicit condition -> trial directory map. IMPORTANT: do NOT glob
# `experiment_results_*/*/{cond}/...` — after the reviewer-comment experiments
# were added, that pattern matches 12+ directories (panel seeds, counterbalance,
# no-flag, IC) and silently pulls the WRONG trial. That ambiguity produced a
# spurious pilot rho of 0.73; the correct value against the stored LLM-judged
# composite (the instrument the paper actually reports) is rho = 0.82.
COND_DIRS = {
    "baseline":            "experiment_results_cd_primary/commons_dilemma/baseline",
    "memory":              "experiment_results_cd_primary/commons_dilemma/memory",
    "memory_planning":     "experiment_results_cd_primary/commons_dilemma/memory_planning",
    "full":                "experiment_results_cd_primary/commons_dilemma/full",
    "full_llm_reflection": "experiment_results_cd_llm_reflection/commons_dilemma/full_llm_reflection",
}

def automated_subscores(blind_entry, use_llm):
    """Sub-scores for the rated persona, faithful to the instrument.

    Default (use_llm=False): read the STORED sub-scores from micro_summary.json,
    i.e. the actual LLM-judged instrument output computed at experiment time
    (no API needed, fully reproducible). This is the composite the paper uses.
    With --llm: recompute from the full micro_log via measurement.micro.
    """
    cond = blind_entry["experimental_condition"]; trial = blind_entry["trial"]
    persona = blind_entry["persona_name"]
    d = COND_DIRS.get(cond)
    if not d:
        return None
    tdir = f"{d}/trial_{trial}"
    if use_llm:
        try:
            micro_log = json.load(open(f"{tdir}/micro_log.json"))
        except FileNotFoundError:
            return None
        import measurement.micro as micro
        summ = micro.compute_micro_summary(micro_log, use_llm_judges=True)
    else:
        try:
            summ = json.load(open(f"{tdir}/micro_summary.json"))
        except FileNotFoundError:
            return None
    out = {}
    for dim in DIMS:
        col = summ.get(dim, {})
        if persona in col:
            out[dim] = float(col[persona])
    return out or None

def krippendorff_ordinal(matrix):
    try:
        import krippendorff
        return krippendorff.alpha(reliability_data=matrix, level_of_measurement="ordinal")
    except Exception:
        return None

def analyse(ratings_csv, blind_key, label, use_llm):
    if not os.path.exists(ratings_csv):
        print(f"\n[{label}] ratings file not found yet ({ratings_csv}). Skipping until raters submit.")
        return
    rows = [r for r in csv.DictReader(open(ratings_csv)) if r.get("rater_id")]
    if not rows:
        print(f"\n[{label}] no ratings yet ({ratings_csv}). Skipping.")
        return
    key = dict(json.load(open(blind_key)))
    raters = sorted(set(r["rater_id"] for r in rows))
    packets = sorted(set(r["packet_id"] for r in rows))
    print(f"\n{'='*64}\n{label}: {len(packets)} packets x {len(raters)} raters = {len(rows)} ratings\n{'='*64}")

    # (2) inter-rater reliability + restricted-variance diagnostic
    print("\n(2) Inter-rater reliability (Krippendorff alpha, ordinal) + mean/SD:")
    passed = []
    for d in DIMS:
        M = np.full((len(raters), len(packets)), np.nan)
        vals = []
        for r in rows:
            if r.get(d):
                M[raters.index(r["rater_id"]), packets.index(r["packet_id"])] = float(r[d]); vals.append(float(r[d]))
        a = krippendorff_ordinal(M)
        astr = f"{a:+.2f}" if a is not None else "n/a"
        if a is not None and a >= ALPHA_GATE: passed.append(d)
        print(f"  {d:24s} alpha={astr}  mean={np.mean(vals):.2f} sd={np.std(vals):.2f}")
    print(f"  -> dimensions passing alpha>={ALPHA_GATE} gate (blended): {passed or 'none'}")

    # (4) human-automated agreement PER DIMENSION
    print("\n(4) Human vs automated agreement, per dimension (Spearman):")
    # human mean rating per packet,dim (scaled 1-5 -> 0-1 to match automated 0-1)
    hum = {d: {} for d in DIMS}
    for p in packets:
        pr = [r for r in rows if r["packet_id"] == p]
        for d in DIMS:
            v = [float(r[d]) for r in pr if r.get(d)]
            if v: hum[d][p] = (np.mean(v) - 1) / 4.0
    auto = {}  # packet -> {dim: score}
    for p in packets:
        be = key.get(p)
        if be:
            s = automated_subscores(be, use_llm)
            if s: auto[p] = s
    for d in DIMS:
        common = [p for p in packets if p in hum[d] and p in auto and d in auto[p]]
        if len(common) >= 3:
            h = [hum[d][p] for p in common]; a = [auto[p][d] for p in common]
            rho, pv = stats.spearmanr(h, a)
            print(f"  {d:24s} rho={rho:+.2f}  p={pv:.3f}  n={len(common)}")
        else:
            print(f"  {d:24s} insufficient paired data (n={len(common)})")
    # overall composite agreement (weighted human composite vs automated composite)
    W = {"behavioural_consistency":0.30,"memory_coherence":0.25,"planning_plausibility":0.25,"response_naturalness":0.20}
    common = [p for p in packets if p in auto and all(p in hum[d] for d in DIMS)]
    if len(common) >= 3:
        hc = [sum(W[d]*hum[d][p] for d in DIMS) for p in common]
        ac = [sum(W[d]*auto[p][d] for d in DIMS) for p in common]
        rho, pv = stats.spearmanr(hc, ac)
        print(f"  {'OVERALL composite':24s} rho={rho:+.2f}  p={pv:.3f}  n={len(common)} (preliminary convergent validity)")

    # (5) gap-case certification: believable verdicts on baseline / 0%-success packets
    print("\n(5) Gap-case certification (Amin item 5):")
    base = [p for p in packets if key.get(p, {}).get("experimental_condition") == "baseline"]
    print(f"  baseline packets rated: {len(base)}")
    def yes(v): return str(v).strip().lower() in ("yes","1","y","true")
    certified = 0
    for p in base:
        verdicts = [r["believable_yes_no"] for r in rows if r["packet_id"] == p and r.get("believable_yes_no")]
        if verdicts and sum(yes(v) for v in verdicts) > len(verdicts)/2:  # majority
            certified += 1
    if base:
        print(f"  certified believable by a MAJORITY of raters: {certified}/{len(base)}")
        print("  -> individually believable yet from 0%-success (collectively unreliable) trials")
    # per-rater overall verdict counts
    print("  believable verdicts per rater (all packets):")
    for rt in raters:
        v = [r["believable_yes_no"] for r in rows if r["rater_id"] == rt and r.get("believable_yes_no")]
        print(f"    {rt}: {sum(yes(x) for x in v)}/{len(v)}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--llm", action="store_true", help="use LLM judges (API key + cost)")
    args = ap.parse_args()
    print("Rubric anchors (1-5):")
    for k, v in RUBRIC.items(): print(f"  {k} = {v}")
    # PRIMARY study (Option 2)
    analyse("full_eval_packets/human_eval_ratings.csv",   # the UI writes this name
            "full_eval_packets/full_blind_key.json",
            "PRIMARY STUDY (120 packets)", args.llm)
    # PILOT, reported separately
    analyse("pilot_packets/human_eval_ratings.csv",
            "pilot_packets/pilot_blind_key.json",
            "PILOT (15 packets, reported separately)", args.llm)

if __name__ == "__main__":
    main()
