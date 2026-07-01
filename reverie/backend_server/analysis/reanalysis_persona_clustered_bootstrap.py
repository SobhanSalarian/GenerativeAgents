import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _paths  # noqa: F401  (adds backend_server to sys.path)
_os.chdir(_paths.BACKEND)  # analysis scripts read result dirs relative to backend_server

import json, glob, os, numpy as np
from scipy import stats
rng=np.random.default_rng(42)

def load(root, scenario):
    """agent-level records: (persona, cond, trial, B_agent, V_trial)"""
    rows=[]
    for cond in ["baseline","memory","memory_planning","full"]:
        for td in sorted(glob.glob(f"{root}/{scenario}/{cond}/trial_*")):
            ms=os.path.join(td,"micro_summary.json"); macs=os.path.join(td,"macro_summary.json")
            if not(os.path.exists(ms) and os.path.exists(macs)): continue
            mic=json.load(open(ms)); mac=json.load(open(macs))
            comp=mic.get("composite_believability") or mic.get("composite_believability_final")
            V=mac.get("coordination_score")
            if not comp or V is None: continue
            for persona,b in comp.items():
                rows.append((persona,cond,os.path.basename(td),float(b),float(V)))
    return rows

def trial_level(rows):
    # collapse to trial-level (mean B over personas) -> the paper's unit
    by={}
    for p,c,t,b,v in rows:
        by.setdefault((c,t),[v,[]]); by[(c,t)][1].append(b)
    B=[np.mean(x[1]) for x in by.values()]; V=[x[0] for x in by.values()]
    return np.array(B),np.array(V)

def cluster_boot_trial(rows, nboot=5000):
    """Resample TRIALS with replacement (trial is the independent unit); rho on trial-level."""
    by={}
    for p,c,t,b,v in rows: by.setdefault((c,t),[v,[]]); by[(c,t)][1].append(b)
    keys=list(by.keys()); B=np.array([np.mean(by[k][1]) for k in keys]); V=np.array([by[k][0] for k in keys])
    n=len(keys); rhos=[]
    for _ in range(nboot):
        idx=rng.integers(0,n,n)
        try:
            r,_=stats.spearmanr(B[idx],V[idx])
            if not np.isnan(r): rhos.append(r)
        except: pass
    return np.percentile(rhos,[2.5,97.5])

def persona_cluster_boot(rows, nboot=5000):
    """Resample PERSONAS with replacement (the dependence unit Amin flags),
       carrying all their agent-trial rows; rho computed at agent level (B_agent vs V_trial)."""
    personas=sorted(set(r[0] for r in rows))
    byp={p:[(b,v) for (pp,c,t,b,v) in rows if pp==p] for p in personas}
    rhos=[]
    for _ in range(nboot):
        samp=rng.choice(personas,len(personas),replace=True)
        B=[];V=[]
        for p in samp:
            for b,v in byp[p]: B.append(b);V.append(v)
        try:
            r,_=stats.spearmanr(B,V)
            if not np.isnan(r): rhos.append(r)
        except: pass
    return np.percentile(rhos,[2.5,97.5]), len(personas)

for name,root,scn in [("CD","experiment_results_cd_primary","commons_dilemma"),
                      ("IC","experiment_results_ic_primary","information_consensus")]:
    rows=load(root,scn)
    B,V=trial_level(rows); rho,p=stats.spearmanr(B,V)
    lo,hi=cluster_boot_trial(rows)
    (plo,phi),npers=persona_cluster_boot(rows)
    print(f"{name}: trial-level rho={rho:.3f} (n={len(B)} trials, {npers} personas)")
    print(f"    trial bootstrap 95% CI   = [{lo:.2f}, {hi:.2f}]")
    print(f"    persona-clustered 95% CI = [{plo:.2f}, {phi:.2f}]  (agent-level rho)")
