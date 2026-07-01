import json,glob,os,numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import LeaveOneOut
from sklearn.metrics import roc_auc_score
import importlib.util,sys
rng=np.random.default_rng(42)
spec=importlib.util.spec_from_file_location("ew","early_warning.py")
ew=importlib.util.module_from_spec(spec); sys.argv=["ew"]
try: spec.loader.exec_module(ew)
except SystemExit: pass
MACRO=["mean_sustainability","sustainability_slope","mean_coordinated_rate","mean_oversubscription","oversubscription_slope","mean_gini","resource_slope","resource_at_step_k"]
MICRO=["mean_request_ratio","request_ratio_slope","parse_error_rate","memory_citation_rate","plan_citation_rate"]
def dataset(cond,k=20):
    X=[];y=[]
    for td in sorted(glob.glob(f"experiment_results_cd_primary/commons_dilemma/{cond}/trial_*")):
        f=ew.extract_features(td,k)
        if f is None: continue
        mac=json.load(open(os.path.join(td,"macro_summary.json")))
        s=mac.get("coordination_success")
        if s is None: continue
        X.append(f);y.append(0 if s else 1)
    return X,np.array(y)
def loo(X,y,feats):
    Xm=np.array([[x[f] for f in feats] for x in X]);n=len(y);pr=np.zeros(n)
    for tr,te in LeaveOneOut().split(Xm):
        sc=StandardScaler().fit(Xm[tr]);clf=RandomForestClassifier(n_estimators=200,random_state=42)
        clf.fit(sc.transform(Xm[tr]),y[tr])
        cls=list(clf.classes_);pr[te]=clf.predict_proba(sc.transform(Xm[te]))[0][cls.index(1)] if 1 in cls else 0.0
    return roc_auc_score(y,pr),pr
def ci(y,pr,nb=1500):
    n=len(y);a=[]
    for _ in range(nb):
        i=rng.integers(0,n,n)
        if len(set(y[i]))>1: a.append(roc_auc_score(y[i],pr[i]))
    return np.percentile(a,[2.5,97.5])
X,y=dataset("full")
print(f"full K=20: n={len(y)} fail={int(y.sum())} base={y.mean():.2f}")
res={}
for nm,ft in [("combined",MACRO+MICRO),("macro-only",MACRO),("micro-only",MICRO)]:
    a,pr=loo(X,y,ft);lo,hi=ci(y,pr);res[nm]=(a,lo,hi,pr)
    print(f"  {nm:11s} AUC={a:.2f} CI[{lo:.2f},{hi:.2f}]")
np.save("/tmp/probs.npy",{k:v[3] for k,v in res.items()},allow_pickle=True)
np.save("/tmp/y.npy",y)
