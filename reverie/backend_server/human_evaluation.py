"""
Exports blinded packets and rating sheets for the MRes human-evaluation stage.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os


def _sanitize_text(text, persona_name, blinded_agent_id):
    text = str(text or "")
    parts = [persona_name] + persona_name.split()
    for part in sorted({p for p in parts if p}, key=len, reverse=True):
        text = text.replace(part, blinded_agent_id)
    return text


def _blinded_agent_id(persona_name, scenario, trial):
    digest = hashlib.sha1(f"{scenario}:{trial}:{persona_name}".encode()).hexdigest()
    return f"agent_{digest[:8]}"


def _packet_id(scenario, trial, persona_name, step, kind="decision"):
    digest = hashlib.sha1(
        f"{scenario}:{trial}:{persona_name}:{step}:{kind}".encode()
    ).hexdigest()
    return f"{kind}_{digest[:10]}"


def _resource_level_note(macro_entry):
    label = macro_entry.get("resource_level_label")
    if label:
        return label
    level = macro_entry.get("resource_level")
    if level is None:
        return None
    sustainability = macro_entry.get("sustainability_score")
    if sustainability is not None:
        return f"{level:.1f} credits ({round(sustainability * 100, 1)}% of original pool)"
    return f"{level:.1f} credits"


def _phase_label(step, max_step):
    if max_step <= 0:
        return "early"
    progress = step / max_step
    if progress < 0.34:
        return "early"
    if progress < 0.67:
        return "middle"
    return "late"


def _sample_entries_for_persona(entries, critical_step=None):
    if not entries:
        return []

    chosen = []
    indices = sorted({0, len(entries) // 2, len(entries) - 1})
    for index in indices:
        chosen.append(entries[index])

    if critical_step is not None:
        nearest = min(entries, key=lambda entry: abs(entry["step"] - critical_step))
        if nearest not in chosen:
            chosen.append(nearest)

    deduped = []
    seen = set()
    for entry in sorted(chosen, key=lambda entry: entry["step"]):
        key = (entry["persona"], entry["step"])
        if key not in seen:
            deduped.append(entry)
            seen.add(key)
    return deduped


def build_human_evaluation_packets(
    micro_log,
    macro_log,
    run_manifest,
    failure_traceability=None,
):
    scenario = run_manifest.get("scenario", "unknown_scenario")
    trial = run_manifest.get("trial", 0)
    critical_step = None
    if failure_traceability:
        critical_step = failure_traceability.get("critical_step")

    by_persona = {}
    for entry in micro_log:
        by_persona.setdefault(entry["persona"], []).append(entry)

    max_step = max((entry["step"] for entry in micro_log), default=0)
    packets = []
    blind_key = {}
    rating_rows = []

    for persona_name, entries in sorted(by_persona.items()):
        blinded_agent_id = _blinded_agent_id(persona_name, scenario, trial)
        sampled_entries = _sample_entries_for_persona(entries, critical_step=critical_step)

        for entry in sampled_entries:
            packet_id = _packet_id(scenario, trial, persona_name, entry["step"])
            macro_entry = next(
                (row for row in macro_log if row.get("step") == entry.get("step")),
                {},
            )
            is_ic = scenario == "information_consensus"

            shared_context = {
                "daily_goals": [
                    _sanitize_text(goal, persona_name, blinded_agent_id)
                    for goal in entry.get("daily_goals", [])
                ],
                "recent_memories": [
                    _sanitize_text(memory, persona_name, blinded_agent_id)
                    for memory in entry.get("recent_memories", [])
                ],
            }
            shared_decision = {
                "reasoning": _sanitize_text(
                    entry.get("reasoning", ""),
                    persona_name,
                    blinded_agent_id,
                ),
                "memory_reference": _sanitize_text(
                    entry.get("memory_reference", ""),
                    persona_name,
                    blinded_agent_id,
                ),
                "plan_reference": _sanitize_text(
                    entry.get("plan_reference", ""),
                    persona_name,
                    blinded_agent_id,
                ),
            }

            if is_ic:
                local_context = {
                    **shared_context,
                    "macro_state": {
                        "vote_tally": macro_entry.get("vote_tally"),
                        "n_agents": macro_entry.get("n_agents"),
                        "consensus_rate": macro_entry.get("consensus_rate"),
                        "consensus_reached": macro_entry.get("consensus_reached"),
                        "consensus_step": macro_entry.get("consensus_step"),
                        "information_diffusion_rate": macro_entry.get(
                            "information_diffusion_rate"
                        ),
                        "coordinated": macro_entry.get("coordinated"),
                    },
                }
                decision = {
                    "vote": entry.get("vote"),
                    "prior_vote": entry.get("prior_vote"),
                    "position_change": entry.get("position_change"),
                    "signal_disclosed": entry.get("signal_disclosed"),
                    "shared_statement": _sanitize_text(
                        entry.get("shared_statement", ""),
                        persona_name,
                        blinded_agent_id,
                    ),
                    **shared_decision,
                }
            else:
                local_context = {
                    "resource_level_before": entry.get("resource_level_before"),
                    "pool_percent_before": entry.get("pool_percent_before"),
                    "fair_share": entry.get("fair_share"),
                    "current_activity": _sanitize_text(
                        entry.get("current_activity", ""),
                        persona_name,
                        blinded_agent_id,
                    ),
                    **shared_context,
                    "macro_state": {
                        "total_requested": macro_entry.get("total_requested"),
                        "resource_level": macro_entry.get("resource_level"),
                        "resource_level_note": _resource_level_note(macro_entry),
                        "coordinated": macro_entry.get("coordinated"),
                        "collapsed": macro_entry.get("collapsed"),
                    },
                }
                decision = {
                    "requested": entry.get("requested"),
                    "granted": entry.get("granted"),
                    **shared_decision,
                }

            packet = {
                "packet_id": packet_id,
                "packet_type": "decision_review",
                "scenario": scenario,
                "trial": trial,
                "step": entry["step"],
                "phase": _phase_label(entry["step"], max_step),
                "time": entry.get("time"),
                "blinded_agent_id": blinded_agent_id,
                "persona_background": _sanitize_text(
                    entry.get("persona_profile", ""),
                    persona_name,
                    blinded_agent_id,
                ),
                "local_context": local_context,
                "decision": decision,
            }
            packets.append(packet)

            blind_key[packet_id] = {
                "scenario": scenario,
                "trial": trial,
                "persona_name": persona_name,
                "experimental_condition": run_manifest.get("experimental_condition"),
                "sim_code": run_manifest.get("sim_code"),
            }

            rating_rows.append({
                "packet_id": packet_id,
                "blinded_agent_id": blinded_agent_id,
                "scenario": scenario,
                "trial": trial,
                "step": entry["step"],
                "phase": packet["phase"],
                "rater_id": "",
                "behavioural_consistency": "",
                "memory_coherence": "",
                "planning_plausibility": "",
                "response_naturalness": "",
                "believable_yes_no": "",
                "notes": "",
            })

    return packets, blind_key, rating_rows


def write_human_evaluation_exports(
    output_path,
    micro_log,
    macro_log,
    run_manifest,
    failure_traceability=None,
):
    packets, blind_key, rating_rows = build_human_evaluation_packets(
        micro_log,
        macro_log,
        run_manifest,
        failure_traceability=failure_traceability,
    )

    os.makedirs(output_path, exist_ok=True)
    packets_path = f"{output_path}/human_eval_packets.jsonl"
    blind_key_path = f"{output_path}/human_eval_blind_key.json"
    ratings_path = f"{output_path}/human_eval_ratings.csv"

    with open(packets_path, "w") as outfile:
        for packet in packets:
            outfile.write(json.dumps(packet) + "\n")

    with open(blind_key_path, "w") as outfile:
        json.dump(blind_key, outfile, indent=2)

    fieldnames = [
        "packet_id",
        "blinded_agent_id",
        "scenario",
        "trial",
        "step",
        "phase",
        "rater_id",
        "behavioural_consistency",
        "memory_coherence",
        "planning_plausibility",
        "response_naturalness",
        "believable_yes_no",
        "notes",
    ]
    with open(ratings_path, "w", newline="") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rating_rows)

    return {
        "packets_path": packets_path,
        "blind_key_path": blind_key_path,
        "ratings_path": ratings_path,
        "packet_count": len(packets),
    }
