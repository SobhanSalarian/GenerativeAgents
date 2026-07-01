"""
rating_ingestion.py — Ingest completed human-evaluation rating sheets and
compute inter-rater reliability (Krippendorff's alpha, ordinal metric).

Research plan §4.5:
  "Human evaluators (3–5 trained raters) will assess micro-level metrics
   using anchored rubrics, with inter-rater reliability measured via
   Krippendorff's alpha (α ≥ 0.67 acceptable)."

Usage
-----
    python rating_ingestion.py <ratings_dir> [--output report.json]

    ratings_dir : directory containing one or more human_eval_ratings.csv
                  files produced by human_evaluation.write_human_evaluation_exports()

Output
------
    JSON reliability report with per-dimension alpha and merged rating table.
    If alpha < 0.67 for any dimension, the report flags low-reliability items.

Standalone function
-------------------
    from rating_ingestion import load_and_analyse_ratings
    report = load_and_analyse_ratings("experiment_results/commons_dilemma")
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from collections import defaultdict


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

RATING_DIMENSIONS = [
    "behavioural_consistency",
    "memory_coherence",
    "planning_plausibility",
    "response_naturalness",
]

ALPHA_ACCEPTABLE = 0.67   # research plan threshold


# ---------------------------------------------------------------------------
# Krippendorff's alpha (ordinal metric, interval difference)
# ---------------------------------------------------------------------------

def _krippendorff_alpha(ratings_matrix: list[list]) -> float | None:
    """
    Compute Krippendorff's alpha for ordinal data.

    Parameters
    ----------
    ratings_matrix : list of lists
        Each inner list is one unit's ratings from all raters.
        None represents a missing value.

    Returns
    -------
    float in [-1, 1] or None when computation is impossible.

    Formula (ordinal / interval metric):
        Alpha = 1 - D_o / D_e
        D_o  = observed disagreement (mean squared difference within units)
        D_e  = expected disagreement (mean squared difference across all pairs)
    """
    # Flatten all non-None values to understand the data
    all_values = [v for row in ratings_matrix for v in row if v is not None]
    if len(all_values) < 2:
        return None

    # Observed disagreement D_o
    do_sum, do_count = 0.0, 0
    for row in ratings_matrix:
        present = [v for v in row if v is not None]
        m_u = len(present)
        if m_u < 2:
            continue
        for i in range(m_u):
            for j in range(i + 1, m_u):
                do_sum += (present[i] - present[j]) ** 2
                do_count += 1

    if do_count == 0:
        return 1.0  # all units have at most one rating — perfect by convention

    D_o = do_sum / do_count

    # Expected disagreement D_e — computed from the pooled value distribution
    n = len(all_values)
    de_sum = 0.0
    for i in range(n):
        for j in range(i + 1, n):
            de_sum += (all_values[i] - all_values[j]) ** 2
    D_e = de_sum / (n * (n - 1) / 2) if n > 1 else 0.0

    if D_e == 0:
        return 1.0  # all values identical

    return round(1.0 - D_o / D_e, 4)


# ---------------------------------------------------------------------------
# CSV loading
# ---------------------------------------------------------------------------

def _parse_rating_value(raw: str):
    """Parse a rating cell; return int if valid, else None."""
    raw = str(raw or "").strip()
    if not raw:
        return None
    try:
        val = int(float(raw))
        return val
    except (ValueError, TypeError):
        return None


def load_ratings_csv(csv_path: Path) -> list[dict]:
    """
    Load a human_eval_ratings.csv file and return a list of row dicts.
    Rows with empty rater_id are skipped (unfilled templates).
    """
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not str(row.get("rater_id", "")).strip():
                continue
            parsed = dict(row)
            for dim in RATING_DIMENSIONS:
                parsed[dim] = _parse_rating_value(row.get(dim))
            rows.append(parsed)
    return rows


def collect_ratings(search_dir: Path) -> list[dict]:
    """
    Recursively find all human_eval_ratings.csv files under search_dir and
    merge them into a single flat list of rating rows.
    """
    all_rows = []
    for csv_path in sorted(search_dir.rglob("human_eval_ratings.csv")):
        try:
            rows = load_ratings_csv(csv_path)
            for row in rows:
                row["_source_file"] = str(csv_path)
            all_rows.extend(rows)
        except Exception as exc:
            print(f"Warning: could not load {csv_path}: {exc}")
    return all_rows


# ---------------------------------------------------------------------------
# Reliability computation
# ---------------------------------------------------------------------------

def _build_ratings_matrix(rows: list[dict], dimension: str) -> list[list]:
    """
    For one dimension, build a units × raters matrix.
    Each unit is identified by packet_id; each column is a unique rater_id.
    """
    by_packet: dict[str, dict[str, int | None]] = defaultdict(dict)
    for row in rows:
        packet_id = str(row.get("packet_id", "")).strip()
        rater_id = str(row.get("rater_id", "")).strip()
        value = row.get(dimension)
        if packet_id and rater_id and value is not None:
            by_packet[packet_id][rater_id] = value

    if not by_packet:
        return []

    raters = sorted({r for packet in by_packet.values() for r in packet})
    matrix = []
    for packet_id, rater_map in by_packet.items():
        matrix.append([rater_map.get(r) for r in raters])
    return matrix


def compute_reliability(rows: list[dict]) -> dict:
    """
    Compute Krippendorff's alpha for every rating dimension.

    Returns
    -------
    dict with per-dimension alpha values and an overall flag.
    """
    report: dict = {
        "n_packets"  : len({r.get("packet_id") for r in rows}),
        "n_raters"   : len({r.get("rater_id")  for r in rows}),
        "n_ratings"  : len(rows),
        "dimensions" : {},
        "acceptable" : True,
    }

    for dim in RATING_DIMENSIONS:
        matrix = _build_ratings_matrix(rows, dim)
        alpha = _krippendorff_alpha(matrix) if matrix else None

        if alpha is None:
            status = "insufficient_data"
            acceptable = None
        elif alpha >= ALPHA_ACCEPTABLE:
            status = "acceptable"
            acceptable = True
        elif alpha >= 0.0:
            status = "marginal"
            acceptable = False
        else:
            status = "poor"
            acceptable = False

        report["dimensions"][dim] = {
            "alpha"      : alpha,
            "status"     : status,
            "acceptable" : acceptable,
            "n_units"    : len(matrix),
        }

        if acceptable is False:
            report["acceptable"] = False

    return report


# ---------------------------------------------------------------------------
# Low-reliability packet flagging
# ---------------------------------------------------------------------------

def flag_low_reliability_packets(rows: list[dict],
                                  threshold: float = 1.5) -> list[dict]:
    """
    Flag packets where any rater's scores deviate from others by more than
    `threshold` points on at least two dimensions.  Returns a list of
    packet_ids that warrant review.
    """
    by_packet: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        pid = str(row.get("packet_id", "")).strip()
        if pid:
            by_packet[pid].append(row)

    flagged = []
    for packet_id, packet_rows in by_packet.items():
        if len(packet_rows) < 2:
            continue
        high_deviation_dims = 0
        for dim in RATING_DIMENSIONS:
            values = [r[dim] for r in packet_rows if r.get(dim) is not None]
            if len(values) < 2:
                continue
            if max(values) - min(values) > threshold:
                high_deviation_dims += 1
        if high_deviation_dims >= 2:
            flagged.append(packet_id)
    return flagged


# ---------------------------------------------------------------------------
# Merged rating export (average ratings per packet)
# ---------------------------------------------------------------------------

def merge_ratings(rows: list[dict]) -> list[dict]:
    """
    Average all raters' scores per packet_id per dimension.
    Returns one row per packet.
    """
    by_packet: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        pid = str(row.get("packet_id", "")).strip()
        if pid:
            by_packet[pid].append(row)

    merged = []
    for packet_id, packet_rows in by_packet.items():
        base = {
            "packet_id"         : packet_id,
            "blinded_agent_id"  : packet_rows[0].get("blinded_agent_id", ""),
            "scenario"          : packet_rows[0].get("scenario", ""),
            "trial"             : packet_rows[0].get("trial", ""),
            "step"              : packet_rows[0].get("step", ""),
            "phase"             : packet_rows[0].get("phase", ""),
            "n_raters"          : len(packet_rows),
        }
        for dim in RATING_DIMENSIONS:
            values = [r[dim] for r in packet_rows if r.get(dim) is not None]
            base[f"{dim}_mean"] = round(sum(values) / len(values), 3) if values else None
            base[f"{dim}_range"] = (max(values) - min(values)) if len(values) >= 2 else None

        # believable_yes_no consensus (majority vote)
        yn_values = [
            str(r.get("believable_yes_no", "")).strip().lower()
            for r in packet_rows
        ]
        yes_count = yn_values.count("yes")
        base["believable_consensus"] = (
            "yes" if yes_count > len(yn_values) / 2 else "no"
        )
        merged.append(base)
    return merged


# ---------------------------------------------------------------------------
# Main analysis entry point
# ---------------------------------------------------------------------------

def load_and_analyse_ratings(search_dir: str | Path,
                              output_path: str | Path | None = None) -> dict:
    """
    Collect all rating CSVs under search_dir, compute reliability, merge
    ratings, and optionally save a JSON report.

    Returns the full report dict.
    """
    search_dir = Path(search_dir)
    rows = collect_ratings(search_dir)

    if not rows:
        print(f"No completed ratings found under {search_dir}.")
        return {"error": "no_ratings_found", "search_dir": str(search_dir)}

    reliability = compute_reliability(rows)
    merged = merge_ratings(rows)
    flagged = flag_low_reliability_packets(rows)

    report = {
        "search_dir"         : str(search_dir),
        "reliability"        : reliability,
        "flagged_packets"    : flagged,
        "merged_ratings"     : merged,
        "alpha_threshold"    : ALPHA_ACCEPTABLE,
    }

    _print_reliability_report(reliability, flagged)

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2))
        print(f"\nReport saved to {output_path}")

    return report


def _print_reliability_report(reliability: dict, flagged: list):
    sep = "=" * 62
    div = "-" * 62
    print(sep)
    print("INTER-RATER RELIABILITY REPORT (Krippendorff's alpha)")
    print(sep)
    print(f"Packets  : {reliability['n_packets']}")
    print(f"Raters   : {reliability['n_raters']}")
    print(f"Ratings  : {reliability['n_ratings']}")
    print(f"Threshold: α ≥ {ALPHA_ACCEPTABLE} (research plan §4.5)")
    print(div)
    for dim, info in reliability["dimensions"].items():
        alpha_str = f"{info['alpha']:.4f}" if info["alpha"] is not None else "N/A"
        status = info["status"].upper()
        print(f"  {dim:30s}  α={alpha_str}  [{status}]")
    print(div)
    overall = "ACCEPTABLE" if reliability["acceptable"] else "NEEDS ATTENTION"
    print(f"Overall reliability: {overall}")
    if flagged:
        print(f"\nFlagged packets (high rater disagreement): {len(flagged)}")
        for pid in flagged[:10]:
            print(f"  {pid}")
        if len(flagged) > 10:
            print(f"  ... and {len(flagged) - 10} more")
    print(sep)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ingest human ratings and compute inter-rater reliability."
    )
    parser.add_argument(
        "ratings_dir",
        nargs="?",
        default="experiment_results",
        help="Directory to search for human_eval_ratings.csv files "
             "(default: experiment_results)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Path for the JSON reliability report (optional)",
    )
    args = parser.parse_args()
    load_and_analyse_ratings(args.ratings_dir, output_path=args.output)
