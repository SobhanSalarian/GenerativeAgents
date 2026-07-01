"""
Creates a blinded pilot packet subset for human-evaluation dry-run.

Samples 1 packet per condition × per phase (early/middle/late) from trial_0
of the CD primary dataset → 12 packets total, shuffled.

Output: pilot_packets/pilot_human_eval_packets.jsonl
        pilot_packets/pilot_blind_key.json

Usage:
    cd reverie/backend_server
    python create_pilot_subset.py
"""
from __future__ import annotations

import hashlib
import json
import os
import random

CONDITIONS = [
    ("experiment_results_cd_primary/commons_dilemma", "baseline"),
    ("experiment_results_cd_primary/commons_dilemma", "memory"),
    ("experiment_results_cd_primary/commons_dilemma", "memory_planning"),
    ("experiment_results_cd_primary/commons_dilemma", "full"),
    ("experiment_results_cd_llm_reflection/commons_dilemma", "full_llm_reflection"),
]
PHASES = ["early", "middle", "late"]
TRIAL = "trial_0"
OUT_DIR = "pilot_packets"
SEED = 42


def main():
    rng = random.Random(SEED)

    # Collect (packet_dict, bk_entry) without condition in any packet field
    pool: list[tuple[dict, dict]] = []

    for base, condition in CONDITIONS:
        path = os.path.join(base, condition, TRIAL, "human_eval_packets.jsonl")
        packets = [json.loads(line) for line in open(path)]

        bk_path = os.path.join(base, condition, TRIAL, "human_eval_blind_key.json")
        bk = json.load(open(bk_path))

        by_phase: dict[str, list[dict]] = {}
        for p in packets:
            by_phase.setdefault(p["phase"], []).append(p)

        for phase in PHASES:
            phase_pool = by_phase.get(phase, [])
            if not phase_pool:
                print(f"  WARNING: no {phase} packets in {condition}/{TRIAL}")
                continue
            chosen = rng.choice(phase_pool)
            pool.append((dict(chosen), bk[chosen["packet_id"]]))

    rng.shuffle(pool)

    # Assign opaque sequential IDs — condition must not appear in packet content
    selected: list[dict] = []
    blind_key: dict[str, dict] = {}

    for i, (packet, bk_entry) in enumerate(pool):
        pilot_pid = f"pilot_{i+1:02d}"
        packet["packet_id"] = pilot_pid
        selected.append(packet)
        blind_key[pilot_pid] = {**bk_entry, "orig_packet_id": bk_entry.get("orig_packet_id", pilot_pid)}

    os.makedirs(OUT_DIR, exist_ok=True)
    packets_path = os.path.join(OUT_DIR, "pilot_human_eval_packets.jsonl")
    bk_out_path = os.path.join(OUT_DIR, "pilot_blind_key.json")

    with open(packets_path, "w") as f:
        for p in selected:
            f.write(json.dumps(p) + "\n")

    with open(bk_out_path, "w") as f:
        json.dump(blind_key, f, indent=2)

    print(f"Pilot subset: {len(selected)} packets → {packets_path}")
    print(f"Blind key   : {bk_out_path}")
    print()
    print("Condition × phase breakdown (blinded during rating):")
    rows = sorted(
        [(blind_key[p["packet_id"]]["experimental_condition"], p["phase"], p["packet_id"]) for p in selected],
        key=lambda r: (r[0], r[1]),
    )
    for cond, phase, pid in rows:
        print(f"  {phase:8s}  {cond:20s}  {pid}")


if __name__ == "__main__":
    main()
