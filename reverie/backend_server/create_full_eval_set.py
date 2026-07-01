"""
Create the FULL human-evaluation packet set (expansion of the 15-packet pilot).

Design
------
The pilot sampled 1 packet per condition x phase from trial_0 (15 packets, since
the 5th condition `full_llm_reflection` was added). This script builds the full
balanced set: ALL 24 packets (8 early / 8 middle / 8 late) from ONE trial per
condition, across the five conditions -> 120 packets.

To guarantee NO overlap with the already-rated pilot (which used trial_0), the
full set is drawn from trial_1 of each condition. The 15 pilot ratings remain
valid as additional trial_0 data and can be pooled at analysis time.

Output (in full_eval_packets/):
    full_human_eval_packets.jsonl   (blinded packets the raters see)
    full_blind_key.json             (packet_id -> condition/trial/persona; for analysis only)

Usage:
    cd reverie/backend_server
    python create_full_eval_set.py
"""
from __future__ import annotations
import json, os, random

# (base_dir, condition, source_trial)  -- source_trial != pilot's trial_0
CONDITIONS = [
    ("experiment_results_cd_primary/commons_dilemma",        "baseline",            "trial_1"),
    ("experiment_results_cd_primary/commons_dilemma",        "memory",              "trial_1"),
    ("experiment_results_cd_primary/commons_dilemma",        "memory_planning",     "trial_1"),
    ("experiment_results_cd_primary/commons_dilemma",        "full",                "trial_1"),
    ("experiment_results_cd_llm_reflection/commons_dilemma", "full_llm_reflection", "trial_1"),
]
OUT_DIR = "full_eval_packets"
PILOT_KEY = "pilot_packets/pilot_blind_key.json"
SEED = 4242


def main():
    rng = random.Random(SEED)

    # IDs already rated in the pilot, to guarantee no packet is rated twice
    pilot_orig_ids = set()
    if os.path.exists(PILOT_KEY):
        for m in json.load(open(PILOT_KEY)).values():
            if m.get("orig_packet_id"):
                pilot_orig_ids.add(m["orig_packet_id"])

    pool = []  # (packet_dict, blind_key_entry)
    for base, condition, src_trial in CONDITIONS:
        ppath = os.path.join(base, condition, src_trial, "human_eval_packets.jsonl")
        bkpath = os.path.join(base, condition, src_trial, "human_eval_blind_key.json")
        packets = [json.loads(l) for l in open(ppath)]
        bk = json.load(open(bkpath))
        for p in packets:
            if p["packet_id"] in pilot_orig_ids:
                continue  # safety: skip anything already rated
            pool.append((dict(p), bk[p["packet_id"]]))

    rng.shuffle(pool)

    selected, blind_key = [], {}
    for i, (packet, bk_entry) in enumerate(pool):
        pid = f"eval_{i+1:03d}"
        orig = packet["packet_id"]
        packet["packet_id"] = pid                      # opaque id; condition hidden
        selected.append(packet)
        blind_key[pid] = {**bk_entry, "orig_packet_id": orig}

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "full_human_eval_packets.jsonl"), "w") as f:
        for p in selected:
            f.write(json.dumps(p) + "\n")
    with open(os.path.join(OUT_DIR, "full_blind_key.json"), "w") as f:
        json.dump(blind_key, f, indent=2)

    # report (blinded breakdown for our records, NOT shown to raters)
    from collections import Counter
    by_cond = Counter(blind_key[p["packet_id"]]["experimental_condition"] for p in selected)
    by_phase = Counter(p["phase"] for p in selected)
    print(f"Full eval set: {len(selected)} packets -> {OUT_DIR}/full_human_eval_packets.jsonl")
    print(f"Excluded {len(pilot_orig_ids)} pilot-rated ids (no overlap).")
    print("By condition:", dict(by_cond))
    print("By phase:    ", dict(by_phase))


if __name__ == "__main__":
    main()
