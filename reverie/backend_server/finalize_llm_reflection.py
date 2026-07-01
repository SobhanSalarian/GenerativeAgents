"""
One-step finalizer for the full_llm_reflection rerun.

Run this ONCE the 20-trial run has finished. It:
  1. Checks how many trials completed and warns if < expected (default 20).
  2. Prints the deterministic-vs-LLM comparison (compare_reflection_conditions).
  3. Runs the H1–H4 hypothesis analysis on the new condition's results dir.

Usage (from reverie/backend_server):
    python finalize_llm_reflection.py
    python finalize_llm_reflection.py --expected 20
    python finalize_llm_reflection.py --llm_dir experiment_results_cd_llm_reflection

Safe to run while the experiment is still going — it will just tell you how
many trials are present and proceed on whatever exists.
"""

import argparse
import glob
import os
import sys

SCENARIO = "commons_dilemma"


def count_trials(llm_dir, condition):
    path = os.path.join(llm_dir, SCENARIO, condition, "trial_*")
    # count only trials that actually have a macro_summary (i.e. finished)
    done = [d for d in glob.glob(path)
            if os.path.exists(os.path.join(d, "macro_summary.json"))]
    return len(done), len(glob.glob(path))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--full_dir", default="experiment_results_cd_primary")
    ap.add_argument("--full_cond", default="full")
    ap.add_argument("--llm_dir", default="experiment_results_cd_llm_reflection")
    ap.add_argument("--llm_cond", default="full_llm_reflection")
    ap.add_argument("--expected", type=int, default=20)
    args = ap.parse_args()

    done, started = count_trials(args.llm_dir, args.llm_cond)
    print("=" * 78)
    print(f"FINALIZE — full_llm_reflection")
    print(f"Trials finished (have macro_summary): {done} / expected {args.expected}"
          f"   (started dirs: {started})")
    if done < args.expected:
        print(f"WARNING: only {done} of {args.expected} trials finished. "
              f"Numbers below are PARTIAL — do not report success-rate comparisons "
              f"until all {args.expected} are in.")
    print("=" * 78)

    # 1. Comparison
    print("\n[1/2] Deterministic vs LLM reflection comparison\n")
    try:
        import compare_reflection_conditions as cmp
        cmp.report(args.full_dir, args.full_cond, args.llm_dir, args.llm_cond)
    except Exception as e:
        print(f"  comparison failed: {e}")

    # 2. Hypothesis analysis on the new condition's results dir
    print("\n[2/2] H1–H4 hypothesis analysis on new results dir\n")
    try:
        from experiment_analysis import run_analysis
        run_analysis(args.llm_dir, SCENARIO)
        print(f"  -> reports written under "
              f"{os.path.join(args.llm_dir, SCENARIO, 'analysis')}/")
        print("  NOTE: H1/H3/H4 compare ACROSS conditions. This results dir contains")
        print("  only full_llm_reflection, so cross-condition tests will be limited.")
        print("  For a full H1–H4 contrast, run a matrix that includes all five")
        print("  conditions (baseline, memory, memory_planning, full, full_llm_reflection)")
        print("  in one output_dir, then run_analysis on that dir.")
    except Exception as e:
        print(f"  analysis failed: {e}")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
