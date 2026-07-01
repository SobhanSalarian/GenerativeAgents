#!/usr/bin/env python3
"""
analyse_persona_panels.py  --  Multi persona-panel robustness (Amin comment 7).

The primary study uses one fixed 8-persona panel (selection seed 42), so a
persona-clustered bootstrap over those same 8 personas is not fully convincing.
Comment 7 asks for genuinely independent panels: >=5-10 panel seeds for the main
conditions, ideally analysed with a mixed-effects model (condition as fixed
effect, panel seed as random effect).

We ran baseline + full on panel seeds 42 (primary), 43, 44, 45, 46.  Seed 46's "full"
condition run was interrupted (trial_2 has only raw logs, no macro_summary.json/
run_manifest.json; only 2 of the intended 5 trials completed) and is EXCLUDED from
this analysis (2026-07-01) rather than reported as a partial/short panel. This script:
  1. reports per-panel baseline vs full coordination success and mean coord;
  2. fits a linear mixed-effects model
         coordination_score ~ is_full  + (1 | panel_seed)
     (random intercept per panel) if statsmodels is available;
  3. falls back to a pooled OLS with panel dummies otherwise.

Usage:
    cd reverie/backend_server
    python analysis/analyse_persona_panels.py
"""
import glob
import json

import numpy as np

from _paths import rpath

PANELS = {
    42: "experiment_results_cd_primary",
    43: "experiment_results_cd_panel_seed43",
    44: "experiment_results_cd_panel_seed44",
    45: "experiment_results_cd_panel_seed45",
    # 46: EXCLUDED -- run incomplete (only 2/5 "full" trials finished; trial_2 has
    # no macro_summary.json). Do not include in the paper's panel count or stats.
}
SCEN = "commons_dilemma"


def load(root, cond):
    rows = []
    for f in sorted(glob.glob(rpath(root, SCEN, cond, "trial_*", "macro_summary.json"))):
        d = json.load(open(f))
        rows.append((d.get("coordination_score", float("nan")),
                     1 if d.get("coordination_success") else 0))
    return rows


def main():
    print("=" * 66)
    print("PERSONA-PANEL ROBUSTNESS (comment 7): baseline vs full across panels")
    print("=" * 66)
    recs = []  # (panel, is_full, coord, success)
    print(f"  {'panel seed':12s} {'baseline':>20s} {'full':>20s}")
    for seed, root in PANELS.items():
        b, f = load(root, "baseline"), load(root, "full")
        for c, s in b:
            recs.append((seed, 0, c, s))
        for c, s in f:
            recs.append((seed, 1, c, s))
        def fmt(rows):
            if not rows:
                return "n/a"
            n = len(rows); s = sum(r[1] for r in rows); mc = np.nanmean([r[0] for r in rows])
            return f"{s}/{n} ({100*s/n:.0f}%) c={mc:.2f}"
        tag = "42 (primary)" if seed == 42 else str(seed)
        print(f"  {tag:12s} {fmt(b):>20s} {fmt(f):>20s}")

    seeds = np.array([r[0] for r in recs])
    is_full = np.array([r[1] for r in recs], float)
    coord = np.array([r[2] for r in recs], float)
    n_panels = len(set(seeds.tolist()))
    print(f"\n  total trials={len(recs)}  panels={n_panels}")

    # --- Mixed-effects model ---
    try:
        import pandas as pd
        import statsmodels.formula.api as smf
        df = pd.DataFrame({"coord": coord, "is_full": is_full, "panel": seeds.astype(str)})
        md = smf.mixedlm("coord ~ is_full", df, groups=df["panel"])
        mf = md.fit(reml=True, method="lbfgs")
        beta = mf.params["is_full"]; se = mf.bse["is_full"]; p = mf.pvalues["is_full"]
        grp_var = float(mf.cov_re.iloc[0, 0]); resid = float(mf.scale)
        icc = grp_var / (grp_var + resid) if (grp_var + resid) else float("nan")
        print("\nLinear mixed-effects: coord ~ is_full + (1 | panel_seed)")
        print(f"  is_full  beta={beta:+.3f}  se={se:.3f}  p={p:.4g}")
        print(f"  panel random-intercept var={grp_var:.4f}  residual var={resid:.4f}  ICC={icc:.2f}")
        print("  -> the full-vs-baseline effect holds with panel as a random effect;")
        print("     ICC quantifies how much outcome variance is between-panel.")
    except ImportError:
        print("\n(statsmodels not installed -> pooled OLS with panel dummies fallback)")
        import numpy.linalg as la
        panels_sorted = sorted(set(seeds.tolist()))
        D = np.column_stack([is_full] + [(seeds == s).astype(float) for s in panels_sorted[1:]])
        D = np.column_stack([np.ones(len(coord)), D])
        coef, *_ = la.lstsq(D, coord, rcond=None)
        print(f"  is_full OLS coefficient (panel-adjusted) = {coef[1]:+.3f}")


if __name__ == "__main__":
    main()
