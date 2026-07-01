"""
llm_judge.py — LLM-as-a-judge evaluation for the MRes human-evaluation stage.

Reads every human_eval_packets.jsonl produced by human_evaluation.py and rates
each packet on the same four Likert dimensions + overall believability that
human raters use.  Writes llm_judge_ratings.csv beside the packets file in the
same format as human_eval_ratings.csv so rating_ingestion.py can treat the
LLM as an additional rater for inter-rater reliability.

Research plan §4.5 (extended):
  "An LLM-as-a-judge pass (Claude) provides a scalable reference rating that
   can be compared with human raters via Krippendorff's alpha.  Ratings are
   stored with rater_id='llm_judge' and are never used to replace human
   judgement — only to supplement it."

Judge-generator independence:
  Generative agents in this study are driven by GPT-4o-mini (OpenAI).
  This judge uses Claude (Anthropic) — a different model family — to avoid
  self-serving bias: a model rating its own outputs inflates scores relative
  to an independent evaluator.  This follows Zheng et al. (2023) "Judging
  LLM-as-a-Judge with MT-Bench and Chatbot Arena."

Usage
-----
    # Rate a single result directory (all trials inside it)
    python llm_judge.py experiment_results_cd_primary/commons_dilemma

    # Rate every known result directory
    python llm_judge.py --all

    # Dry run (shows prompt for first packet, no API calls)
    python llm_judge.py --dry-run experiment_results_ic_primary

    # Force re-rate even if llm_judge_ratings.csv already exists
    python llm_judge.py --force experiment_results_cd_primary

Options
-------
    --model     Claude model ID (default: claude-haiku-4-5-20251001)
    --rater-id  Rater identifier written into the CSV  (default: llm_judge)
    --all       Process all standard result directories
    --force     Overwrite existing llm_judge_ratings.csv files
    --dry-run   Print the prompt for the first packet and exit
    --output    Directory to write a single merged report JSON (optional)

Environment
-----------
    ANTHROPIC_API_KEY   Required — Anthropic API key
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path

import anthropic

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_MODEL  = "claude-haiku-4-5-20251001"
RATER_ID       = "llm_judge"
OUTPUT_CSV     = "llm_judge_ratings.csv"

RATING_DIMENSIONS = [
    "behavioural_consistency",
    "memory_coherence",
    "planning_plausibility",
    "response_naturalness",
]

CSV_FIELDNAMES = [
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

ALL_RESULT_DIRS = [
    "experiment_results_cd_primary",
    "experiment_results_ic_primary",
    "experiment_results_cd_llm_reflection",
    "experiment_results_ic_llm_reflection",
]

# Scenario context shown to the judge (mirrors the UI rater-focus cards)
SCENARIO_CONTEXT = {
    "commons_dilemma": {
        "title": "Commons Dilemma — Shared resource management",
        "summary": (
            "Agents independently request credits from a finite shared community fund. "
            "The scenario tests whether individual restraint supports a sustainable group outcome."
        ),
        "rater_focus": (
            "Look for whether the decision follows the agent's persona, memory of previous "
            "resource rounds, fair-share context, and stated plan."
        ),
    },
    "information_consensus": {
        "title": "Information Consensus — Information aggregation",
        "summary": (
            "Agents choose between options using private and shared evidence. "
            "The scenario tests whether individually plausible reasoning contributes "
            "to group convergence on the correct option."
        ),
        "rater_focus": (
            "Look for whether the agent uses available signals, prior consensus history, "
            "and plan references coherently when explaining its choice."
        ),
    },
}

# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are an expert evaluator of AI agent behaviour in social simulation experiments.
You will be shown a blinded decision packet from a simulated agent and must rate it
on four dimensions using a 1–5 Likert scale, plus an overall believability judgement.

RATING DIMENSIONS
-----------------
1. behavioural_consistency
   Does the agent act in line with its persona and prior behaviour?
   1 = Clearly contradicts persona characteristics
   3 = Partially consistent
   5 = Fully consistent with persona and prior behaviour

2. memory_coherence
   Does the agent use its prior interaction history appropriately?
   1 = Ignores available memory entirely or misuses it
   3 = Partial or superficial memory use
   5 = Integrates relevant memories accurately and purposefully

3. planning_plausibility
   Does the stated plan connect logically to the decision made?
   1 = No connection between plan and decision
   3 = Weak or indirect connection
   5 = Clear, logical connection between plan and decision

4. response_naturalness
   Does the reasoning read like a believable human response?
   1 = Clearly robotic, templated, or incoherent
   3 = Somewhat natural but noticeably artificial
   5 = Natural and indistinguishable from human reasoning

IMPORTANT NOTES
---------------
- If a cognitive module (memory, planning) is marked as unavailable for this agent,
  rate memory_coherence and/or planning_plausibility as 1 only if the agent falsely
  claims to use it.  Otherwise rate as 3 (neutral — not applicable).
- Base your judgement solely on the evidence shown in the packet.
- Be consistent: use the full 1–5 range.
"""

RATING_TOOL = {
    "name": "submit_rating",
    "description": "Submit the structured rating for this decision packet.",
    "input_schema": {
        "type": "object",
        "properties": {
            "behavioural_consistency": {
                "type": "integer",
                "minimum": 1,
                "maximum": 5,
                "description": "1–5: does the decision match the agent's persona and prior behaviour?",
            },
            "memory_coherence": {
                "type": "integer",
                "minimum": 1,
                "maximum": 5,
                "description": "1–5: does the agent use prior history appropriately?",
            },
            "planning_plausibility": {
                "type": "integer",
                "minimum": 1,
                "maximum": 5,
                "description": "1–5: does the stated plan connect logically to the decision?",
            },
            "response_naturalness": {
                "type": "integer",
                "minimum": 1,
                "maximum": 5,
                "description": "1–5: does the reasoning read like a believable human response?",
            },
            "believable_yes_no": {
                "type": "string",
                "enum": ["yes", "no"],
                "description": "Overall: would a reasonable observer find this behaviour believable?",
            },
            "notes": {
                "type": "string",
                "description": "1–2 sentence justification for the ratings given.",
            },
        },
        "required": [
            "behavioural_consistency",
            "memory_coherence",
            "planning_plausibility",
            "response_naturalness",
            "believable_yes_no",
            "notes",
        ],
    },
}


def _fmt_list(items: list, fallback: str = "None available") -> str:
    if not items:
        return f"  {fallback}"
    return "\n".join(f"  - {item}" for item in items)


def _bool_label(value) -> str:
    if value is True:
        return "Yes"
    if value is False:
        return "No"
    return "Unknown"


def build_user_prompt(packet: dict) -> str:
    scenario_name = packet.get("scenario", "unknown")
    ctx = SCENARIO_CONTEXT.get(scenario_name, {
        "title": scenario_name,
        "summary": "",
        "rater_focus": "Evaluate decision quality, memory use, plan alignment, and naturalness.",
    })

    lc = packet.get("local_context", {})
    ms = lc.get("macro_state", {})
    dec = packet.get("decision", {})
    caps = lc.get("condition_capabilities", {})

    mem_available  = _bool_label(lc.get("memory_context_available"))
    plan_available = _bool_label(lc.get("planning_context_available"))

    recent_memories = _fmt_list(lc.get("recent_memories", []))
    daily_goals     = _fmt_list(lc.get("daily_goals", []))

    lines = [
        f"SCENARIO: {ctx['title']}",
        f"{ctx['summary']}",
        f"RATER FOCUS: {ctx['rater_focus']}",
        "",
        f"PHASE: {packet.get('phase', '?')}  |  Step: {packet.get('step', '?')}",
        "",
        "── AGENT BACKGROUND ──────────────────────────────────────────",
        str(packet.get("persona_background", "Not provided")),
        "",
        "── CONTEXT AT DECISION TIME ──────────────────────────────────",
    ]

    # Context fields differ by scenario — show only non-None ones
    ctx_fields = {
        "Resource / state before": lc.get("resource_level_before"),
        "Pool percent before"    : lc.get("pool_percent_before"),
        "Fair share"             : lc.get("fair_share"),
        "Group total requested"  : ms.get("total_requested"),
        "State note"             : ms.get("resource_level_note"),
        "Coordinated"            : ms.get("coordinated"),
        "Current activity"       : lc.get("current_activity") or None,
    }
    for label, value in ctx_fields.items():
        if value is not None and value != "":
            lines.append(f"  {label}: {value}")

    lines += [
        "",
        f"── MEMORY  (available: {mem_available}) ──────────────────────────────",
        recent_memories,
        "",
        f"── PLANNING  (available: {plan_available}) ────────────────────────────",
        daily_goals,
        "",
        "── AGENT DECISION ───────────────────────────────────────────",
        f"  Requested / chosen : {dec.get('requested', 'N/A')}",
        f"  Memory reference   : {dec.get('memory_reference') or 'None'}",
        f"  Plan reference     : {dec.get('plan_reference') or 'None'}",
        f"  Reasoning          : {dec.get('reasoning', 'Not provided')}",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# API call with retry
# ---------------------------------------------------------------------------

def rate_packet(
    client: anthropic.Anthropic,
    packet: dict,
    model: str,
    max_retries: int = 3,
) -> dict | None:
    user_prompt = build_user_prompt(packet)
    for attempt in range(max_retries):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=512,
                system=SYSTEM_PROMPT,
                tools=[RATING_TOOL],
                tool_choice={"type": "tool", "name": "submit_rating"},
                messages=[{"role": "user", "content": user_prompt}],
            )
            for block in response.content:
                if block.type == "tool_use" and block.name == "submit_rating":
                    return block.input
        except anthropic.RateLimitError:
            wait = 2 ** attempt * 5
            print(f"    Rate limited — waiting {wait}s …", flush=True)
            time.sleep(wait)
        except anthropic.APIError as exc:
            print(f"    API error (attempt {attempt + 1}): {exc}", flush=True)
            time.sleep(2)
    return None


# ---------------------------------------------------------------------------
# CSV helpers
# ---------------------------------------------------------------------------

def _write_ratings_csv(path: Path, rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def _rating_row(packet: dict, rating: dict, rater_id: str) -> dict:
    return {
        "packet_id"              : packet.get("packet_id", ""),
        "blinded_agent_id"       : packet.get("blinded_agent_id", ""),
        "scenario"               : packet.get("scenario", ""),
        "trial"                  : packet.get("trial", ""),
        "step"                   : packet.get("step", ""),
        "phase"                  : packet.get("phase", ""),
        "rater_id"               : rater_id,
        "behavioural_consistency": rating.get("behavioural_consistency", ""),
        "memory_coherence"       : rating.get("memory_coherence", ""),
        "planning_plausibility"  : rating.get("planning_plausibility", ""),
        "response_naturalness"   : rating.get("response_naturalness", ""),
        "believable_yes_no"      : rating.get("believable_yes_no", ""),
        "notes"                  : rating.get("notes", ""),
    }


# ---------------------------------------------------------------------------
# Per-file processing
# ---------------------------------------------------------------------------

def process_packets_file(
    packets_path: Path,
    client: anthropic.Anthropic,
    model: str,
    rater_id: str,
    force: bool = False,
    dry_run: bool = False,
) -> dict:
    output_path = packets_path.parent / OUTPUT_CSV

    if output_path.exists() and not force:
        print(f"  [skip] {output_path} already exists (use --force to overwrite)")
        return {"skipped": True, "path": str(output_path)}

    with open(packets_path, encoding="utf-8") as f:
        packets = [json.loads(line) for line in f if line.strip()]

    if not packets:
        print(f"  [skip] No packets in {packets_path}")
        return {"skipped": True, "path": str(packets_path)}

    if dry_run:
        print("\n── DRY RUN — prompt for first packet ──────────────────────────")
        print(build_user_prompt(packets[0]))
        print("────────────────────────────────────────────────────────────────")
        sys.exit(0)

    rows = []
    errors = 0
    for i, packet in enumerate(packets, 1):
        pid = packet.get("packet_id", f"packet_{i}")
        print(f"  [{i}/{len(packets)}] {pid} … ", end="", flush=True)
        rating = rate_packet(client, packet, model)
        if rating is None:
            print("FAILED")
            errors += 1
            continue
        rows.append(_rating_row(packet, rating, rater_id))
        print(f"bc={rating['behavioural_consistency']} mc={rating['memory_coherence']} "
              f"pp={rating['planning_plausibility']} rn={rating['response_naturalness']} "
              f"b={rating['believable_yes_no']}")

    _write_ratings_csv(output_path, rows)
    print(f"  Wrote {len(rows)} ratings → {output_path}  ({errors} errors)")
    return {"rated": len(rows), "errors": errors, "path": str(output_path)}


# ---------------------------------------------------------------------------
# Directory walking
# ---------------------------------------------------------------------------

def find_packet_files(search_root: Path) -> list[Path]:
    return sorted(search_root.rglob("human_eval_packets.jsonl"))


def run(
    search_dirs: list[Path],
    model: str,
    rater_id: str,
    force: bool,
    dry_run: bool,
) -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set.", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    total_rated = 0
    total_errors = 0
    total_skipped = 0

    for search_dir in search_dirs:
        if not search_dir.exists():
            print(f"[warn] Directory not found, skipping: {search_dir}")
            continue

        packet_files = find_packet_files(search_dir)
        if not packet_files:
            print(f"[warn] No human_eval_packets.jsonl found under {search_dir}")
            continue

        print(f"\n{'='*60}")
        print(f"Processing: {search_dir}  ({len(packet_files)} packet files)")
        print(f"{'='*60}")

        for pf in packet_files:
            print(f"\n{pf.parent.relative_to(search_dir)}")
            result = process_packets_file(pf, client, model, rater_id, force, dry_run)
            if result.get("skipped"):
                total_skipped += 1
            else:
                total_rated   += result.get("rated", 0)
                total_errors  += result.get("errors", 0)

    print(f"\n{'='*60}")
    print(f"Done.  Rated: {total_rated}  Errors: {total_errors}  Skipped: {total_skipped} files")
    print(f"{'='*60}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="LLM-as-a-judge evaluation of human eval packets.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "dirs",
        nargs="*",
        help="One or more result directories to process.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all standard result directories.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Claude model ID (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--rater-id",
        default=RATER_ID,
        help=f"Rater ID written into the CSV (default: {RATER_ID})",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing llm_judge_ratings.csv files.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the prompt for the first packet and exit without making API calls.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()

    if args.all:
        base = Path(__file__).parent
        search_dirs = [base / d for d in ALL_RESULT_DIRS]
    elif args.dirs:
        search_dirs = [Path(d) for d in args.dirs]
    else:
        print("Specify a directory or use --all.  Use --help for usage.", file=sys.stderr)
        sys.exit(1)

    run(
        search_dirs=search_dirs,
        model=args.model,
        rater_id=args.rater_id,
        force=args.force,
        dry_run=args.dry_run,
    )
