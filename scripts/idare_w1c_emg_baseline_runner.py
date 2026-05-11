#!/usr/bin/env python3
from __future__ import annotations

import argparse, csv, json, math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TASKS = ["arousal", "valence"]
POLICY = "midpoint_as_high"
REF = {"arousal": 0.5365, "valence": 0.5202}
CELLS = [
    ("C1", "emg", "none"),
    ("C2", "emg", "per_subject_zscore"),
    ("C3", "emg", "train_fold_standard_scaler"),
    ("C4", "emg_bsl", "none"),
    ("C5", "emg_bsl", "per_subject_zscore"),
    ("C6", "emg_bsl", "train_fold_standard_scaler"),
]

@dataclass(frozen=True)
class Fold:
    fold_id: int
    val_subjects: list[int]
    train_subjects: list[int]

@dataclass(frozen=True)
class Spec:
    run_id: int
    task: str
    cell: str
    input_kind: str
    norm: str
    fold: Fold

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--feature-npy", type=Path, default=ROOT/".cache/idare_emg_features.npy")
    p.add_argument("--feature-index", type=Path, default=ROOT/".cache/idare_emg_feature_cache_index.csv")
    p.add_argument("--bsl-npy", type=Path, default=ROOT/".cache/idare_emg_bsl_stats.npy")
    p.add_argument("--bsl-index", type=Path, default=ROOT/".cache/idare_emg_bsl_stats_index.csv")
    p.add_argument("--out-md", type=Path, required=True)
    p.add_argument("--out-json", type=Path, required=True)
    p.add_argument("--out-predictions-csv", type=Path, required=True)
    p.add_argument("--out-closeout-md", type=Path)
    p.add_argument("--out-closeout-json", type=Path)
    p.add_argument("--tasks", nargs="+", default=TASKS, choices=TASKS)
    p.add_argument("--label-policy", default=POLICY)
    p.add_argument("--folds", type=int, default=6)
    p.add_argument("--fold-seed", type=int, default=20260511)
    p.add_argument("--ridge-alpha", type=float, default=1.0)
    p.add_argument("--max-runs", type=int, default=0)
    p.add_argument("--run-tag", default="first_pass")
    return p.parse_args()

def now(): return datetime.now(timezone.utc).isoformat()
def div(a,b): return float(a/b) if b else 0.0

def counts(y):
    return {"0": int(sum(int(v)==0 for v in y)), "1": int(sum(int(v)==1 for v in y))}

def metrics(y_true, y_pred):
    y_true = [int(x) for x in y_true]; y_pred = [int(x) for x in y_pred]
    conf = {
        "tn": int(sum(t==0 and p==0 for t,p in zip(y_true,y_pred))),
        "fp": int(sum(t==0 and p==1 for t,p in zip(y_true,y_pred))),
        "fn": int(sum(t==1 and p==0 for t,p in zip(y_true,y_pred))),
        "tp": int(sum(t==1 and p==1 for t,p in zip(y_true,y_pred))),
    }
    recalls=[]; f1s=[]; per={}
    for lab in [0,1]:
        tp=sum(t==lab and p==lab for t,p in zip(y_true,y_pred))
        fp=sum(t!=lab and p==lab for t,p in zip(y_true,y_pred))
        fn=sum(t==lab and p!=lab for t,p in zip(y_true,y_pred))
        prec=div(tp,tp+fp); rec=div(tp,tp+fn); f1=div(2*prec*rec,prec+rec)
        recalls.append(rec); f1s.append(f1)
        per[str(lab)]={"precision":prec,"recall":rec,"f1":f1,"support":int(sum(t==lab for t in y_true))}
    pred_unique=sorted(set(y_pred)); true_counts=counts(y_true); pred_counts=counts(y_pred)
    maj=max([0,1], key=lambda k: true_counts[str(k)])
    return {
        "n": len(y_true),
        "accuracy": div(sum(t==p for t,p in zip(y_true,y_pred)), len(y_true)),
        "balanced_accuracy": float(sum(recalls)/2),
        "macro_f1": float(sum(f1s)/2),
        "true_counts": true_counts,
        "pred_counts": pred_counts,
        "confusion": conf,
        "per_class": per,
        "one_class_pred": len(pred_unique)==1,
        "pred_unique_labels": pred_unique,
        "majority_baseline": {"label": int(maj), "accuracy": div(true_counts[str(maj)], len(y_true))},
    }

def summary(vals):
    a=np.asarray(vals,dtype=float)
    if a.size==0: return {"mean": math.nan, "std": math.nan, "min": math.nan, "max": math.nan}
    return {"mean": float(a.mean()), "std": float(a.std(ddof=0)), "min": float(a.min()), "max": float(a.max())}

def load_inputs(a):
    for p in [a.feature_npy,a.feature_index,a.bsl_npy,a.bsl_index]:
        if not p.exists(): raise FileNotFoundError(f"Missing required input: {p}")
    feat=np.load(a.feature_npy,mmap_mode="r"); bsl=np.load(a.bsl_npy,mmap_mode="r")
    fi=pd.read_csv(a.feature_index); bi=pd.read_csv(a.bsl_index)
    if feat.ndim!=2 or bsl.ndim!=2: raise ValueError("Expected 2D EMG feature and BSL arrays")
    if len(fi)!=feat.shape[0] or len(bi)!=bsl.shape[0] or len(fi)!=len(bi): raise ValueError("Index/cache row mismatch")
    for c in ["cache_row","subject_id"]:
        if c not in fi.columns: raise KeyError(f"Missing feature-index column {c}")
    for t in TASKS:
        c=f"{t}_{a.label_policy}"
        if c not in fi.columns: raise KeyError(f"Missing label column {c}")
    common=[c for c in ["subject_id","stimulus_id","trial_id","event_index_0based"] if c in fi.columns and c in bi.columns]
    bad=[]
    for c in common:
        if not np.array_equal(fi[c].astype(str).fillna("").to_numpy(), bi[c].astype(str).fillna("").to_numpy()): bad.append(c)
    if bad: raise ValueError(f"Feature/BSL index alignment mismatch: {bad}")
    fr=fi["cache_row"].astype(int).to_numpy()
    br=bi["cache_row"].astype(int).to_numpy() if "cache_row" in bi.columns else np.arange(len(bi))
    Xf=np.asarray(feat[fr],dtype=float); Xb=np.asarray(bsl[br],dtype=float)
    if not np.isfinite(Xf).all() or not np.isfinite(Xb).all(): raise ValueError("Non-finite cache value")
    return {"feature":Xf,"bsl":Xb,"index":fi.copy(),"alignment_common_cols":common}

def make_folds(subjects, n, seed):
    if n!=6: raise ValueError("W1C requires exactly 6 folds")
    subjects=sorted({int(s) for s in subjects})
    rng=np.random.default_rng(seed); sh=np.asarray(subjects,dtype=int); rng.shuffle(sh)
    chunks=np.array_split(sh,n); all_s=set(subjects); folds=[]
    for i,ch in enumerate(chunks,1):
        val=sorted(int(x) for x in ch.tolist()); train=sorted(all_s-set(val)); folds.append(Fold(i,val,train))
    return folds

def specs(tasks, folds, max_runs):
    out=[]; rid=1
    for t in tasks:
        for f in folds:
            for cell,inp,norm in CELLS:
                out.append(Spec(rid,t,cell,inp,norm,f)); rid+=1
    if max_runs and max_runs>0:
        out=out[:max_runs]
        out=[Spec(i,s.task,s.cell,s.input_kind,s.norm,s.fold) for i,s in enumerate(out,1)]
    return out

def std_train(Xtr,Xva):
    m=Xtr.mean(0); s=Xtr.std(0); s=np.where(s<1e-8,1.0,s)
    return (Xtr-m)/s,(Xva-m)/s,{"type":"train_fold_standard_scaler","std_min":float(s.min()),"std_max":float(s.max())}

def std_subject(X, subs):
    out=np.asarray(X,dtype=float).copy(); mins=[]
    for sub in sorted(set(int(s) for s in subs.tolist())):
        mask=subs==sub; m=out[mask].mean(0); sd=out[mask].std(0); sd=np.where(sd<1e-8,1.0,sd)
        out[mask]=(out[mask]-m)/sd; mins.append(float(sd.min()))
    return out,{"type":"per_subject_zscore","transductive":True,"subjects":len(mins),"min_std_min":float(min(mins))}

def prep(spec, data, valid):
    idx=data["index"]; subs_all=idx["subject_id"].astype(int).to_numpy()
    X = data["feature"] if spec.input_kind=="emg" else np.concatenate([data["feature"],data["bsl"]],axis=1)
    X=X[valid]; subs=subs_all[valid]
    valset=set(spec.fold.val_subjects); va=np.asarray([int(s) in valset for s in subs],dtype=bool); tr=~va
    if spec.norm=="none":
        Xn=X.astype(float,copy=True); return Xn[tr],Xn[va],tr,{"type":"none"}
    if spec.norm=="per_subject_zscore":
        Xn,info=std_subject(X,subs); return Xn[tr],Xn[va],tr,info
    if spec.norm=="train_fold_standard_scaler":
        Xtr,Xva,info=std_train(X[tr],X[va]); return Xtr,Xva,tr,info
    raise ValueError(spec.norm)

def fit_ridge(X,y,alpha):
    yy=np.where(y.astype(int)==1,1.0,-1.0); Xa=np.c_[X,np.ones((X.shape[0],1))]
    reg=np.eye(Xa.shape[1])*alpha; reg[-1,-1]=0.0
    coef=np.linalg.solve(Xa.T@Xa+reg, Xa.T@yy)
    return coef[:-1], float(coef[-1])

def run_one(spec, data, a):
    idx=data["index"]; col=f"{spec.task}_{a.label_policy}"; lab=pd.to_numeric(idx[col], errors="coerce")
    valid=lab.isin([0,1]).to_numpy(); yall=lab[valid].astype(int).to_numpy()
    idxv=idx.loc[valid].reset_index(drop=False).rename(columns={"index":"original_row"})
    Xtr,Xva,tr,info=prep(spec,data,valid); ytr=yall[tr]; yva=yall[~tr]
    w,b=fit_ridge(Xtr,ytr,a.ridge_alpha); sc_tr=Xtr@w+b; sc_va=Xva@w+b
    pr_tr=(sc_tr>=0).astype(int); pr_va=(sc_va>=0).astype(int)
    rows=idxv.loc[~tr].copy().reset_index(drop=True)
    preds=[]
    for i,row in rows.iterrows():
        preds.append({"run_id":spec.run_id,"run_tag":a.run_tag,"task":spec.task,"label_policy":a.label_policy,
                      "cell":spec.cell,"input_kind":spec.input_kind,"normalization":spec.norm,"fold_id":spec.fold.fold_id,
                      "subject_id":int(row["subject_id"]),"cache_row":int(row["cache_row"]),"y_true":int(yva[i]),
                      "y_pred":int(pr_va[i]),"score":float(sc_va[i])})
    res={"run_id":spec.run_id,"run_tag":a.run_tag,"task":spec.task,"label_policy":a.label_policy,
         "cell":spec.cell,"input_kind":spec.input_kind,"normalization":spec.norm,"fold_id":spec.fold.fold_id,
         "val_subjects":spec.fold.val_subjects,"train_subject_count":len(spec.fold.train_subjects),"val_subject_count":len(spec.fold.val_subjects),
         "train_n":int(len(ytr)),"val_n":int(len(yva)),"feature_dim":int(Xtr.shape[1]),"ridge_alpha":float(a.ridge_alpha),
         "normalization_info":info,"train_label_counts":counts(ytr.tolist()),"val_label_counts":counts(yva.tolist()),
         "train":metrics(ytr.tolist(),pr_tr.tolist()),"val":metrics(yva.tolist(),pr_va.tolist())}
    return res,preds

def aggregate(results):
    groups={}
    for r in results: groups.setdefault((r["task"],r["cell"]),[]).append(r)
    out=[]
    for (task,cell),g in sorted(groups.items()):
        bal=[x["val"]["balanced_accuracy"] for x in g]; mf=[x["val"]["macro_f1"] for x in g]; acc=[x["val"]["accuracy"] for x in g]
        one=[x["val"]["one_class_pred"] for x in g]; first=g[0]; mean_bal=float(np.mean(bal)); ref=REF[task]
        out.append({"task":task,"cell":cell,"input_kind":first["input_kind"],"normalization":first["normalization"],"runs":len(g),
                    "balanced_accuracy":summary(bal),"macro_f1":summary(mf),"accuracy":summary(acc),"one_class_runs":int(sum(one)),
                    "reference_balanced_accuracy":float(ref),"delta_vs_reference_balanced_accuracy":float(mean_bal-ref),
                    "moderate_pass":bool(mean_bal>=0.54),"strong_pass":bool(mean_bal>=0.55)})
    return out

def best_by_task(agg):
    out={}
    for t in TASKS:
        rows=[r for r in agg if r["task"]==t]
        if rows: out[t]=max(rows,key=lambda r:(r["balanced_accuracy"]["mean"],r["macro_f1"]["mean"]))
    return out

def write_csv(rows,path):
    path.parent.mkdir(parents=True,exist_ok=True)
    if not rows: path.write_text("",encoding="utf-8"); return
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

def fmt(x):
    try: return f"{float(x):.4f}"
    except Exception: return str(x)

def write_md(rep,path):
    lines=["# W1C I-DARE EMG Independent Ridge Baseline Report","",
           f"- status: `{rep['status']}`",f"- run_tag: `{rep['config']['run_tag']}`",
           f"- registered_runs_executed: `{rep['counts']['registered_runs_executed']}`",f"- model: `closed_form_binary_ridge`",
           f"- ridge_alpha: `{rep['config']['ridge_alpha']}`",f"- label_policy: `{rep['config']['label_policy']}`","",
           "## Aggregate Results","",
           "| Task | Cell | Input | Normalization | Runs | Bal acc mean | Macro F1 mean | Acc mean | Delta vs ref | One-class | Moderate | Strong |",
           "|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---|"]
    for r in rep["aggregate"]:
        lines.append(f"| {r['task']} | {r['cell']} | {r['input_kind']} | {r['normalization']} | {r['runs']} | {fmt(r['balanced_accuracy']['mean'])} | {fmt(r['macro_f1']['mean'])} | {fmt(r['accuracy']['mean'])} | {fmt(r['delta_vs_reference_balanced_accuracy'])} | {r['one_class_runs']} | {str(r['moderate_pass']).lower()} | {str(r['strong_pass']).lower()} |")
    lines += ["","## Best Cells By Task","","| Task | Best cell | Bal acc mean | Reference | Delta | Moderate | Strong |","|---|---|---:|---:|---:|---|---|"]
    for t,r in rep["best_by_task"].items():
        lines.append(f"| {t} | {r['cell']} | {fmt(r['balanced_accuracy']['mean'])} | {fmt(r['reference_balanced_accuracy'])} | {fmt(r['delta_vs_reference_balanced_accuracy'])} | {str(r['moderate_pass']).lower()} | {str(r['strong_pass']).lower()} |")
    lines += ["","## Interpretation","",rep["interpretation"],"","## Not Started",""] + [f"- {x}" for x in rep["not_started"]]
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text("\n".join(lines)+"\n",encoding="utf-8")

def write_closeout(rep, md_path, json_path):
    any_mod=any(v["moderate_pass"] for v in rep["best_by_task"].values()); any_str=any(v["strong_pass"] for v in rep["best_by_task"].values())
    decision = "strong_pass_observed_control_tower_review_required" if any_str else "moderate_pass_observed_control_tower_review_required" if any_mod else "no_pass_observed_keep_emg_as_independent_reference"
    close={"status":"closed","closed_at_utc":now(),"branch":"idare/wave1/emg-baseline-ablation","scope":"W1C EMG independent ridge baseline",
           "registered_runs_executed":rep["counts"]["registered_runs_executed"],"any_moderate_pass":any_mod,"any_strong_pass":any_str,
           "best_by_task":rep["best_by_task"],"decision":decision,"forbidden_not_started":rep["not_started"],
           "next_step":"Control Tower review only. Do not open Wave 2 EMG, pairwise EMG, or fusion from this branch without authorization."}
    json_path.write_text(json.dumps(close,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    lines=["# W1C EMG Independent Baseline Closeout","",f"- status: `{close['status']}`",f"- decision: `{decision}`",f"- registered_runs_executed: `{close['registered_runs_executed']}`",f"- any_moderate_pass: `{str(any_mod).lower()}`",f"- any_strong_pass: `{str(any_str).lower()}`","","## Best By Task","","| Task | Cell | Bal acc mean | Ref | Delta |","|---|---|---:|---:|---:|"]
    for t,r in close["best_by_task"].items(): lines.append(f"| {t} | {r['cell']} | {fmt(r['balanced_accuracy']['mean'])} | {fmt(r['reference_balanced_accuracy'])} | {fmt(r['delta_vs_reference_balanced_accuracy'])} |")
    lines += ["","## Control Tower Note","",close["next_step"],"","## Not Started",""] + [f"- {x}" for x in close["forbidden_not_started"]]
    md_path.write_text("\n".join(lines)+"\n",encoding="utf-8")

def main():
    a=parse_args()
    if a.label_policy!=POLICY: raise ValueError("W1C does not change thresholds; expected midpoint_as_high")
    if a.folds!=6: raise ValueError("W1C requires 6 folds")
    if a.ridge_alpha!=1.0: raise ValueError("W1C ridge alpha fixed at 1.0")
    if a.max_runs and a.max_runs>72: raise ValueError("W1C max registered runs is 72")
    data=load_inputs(a); subjects=sorted(int(s) for s in data["index"]["subject_id"].astype(int).unique().tolist())
    folds=make_folds(subjects,a.folds,a.fold_seed); sp=specs(a.tasks,folds,a.max_runs)
    if len(sp)>72: raise ValueError(f"Too many runs: {len(sp)}")
    results=[]; predrows=[]
    for s in sp:
        r,prs=run_one(s,data,a); results.append(r); predrows.extend(prs)
        print(json.dumps({"run_id":r["run_id"],"task":r["task"],"cell":r["cell"],"fold_id":r["fold_id"],"bal_acc":r["val"]["balanced_accuracy"],"macro_f1":r["val"]["macro_f1"],"one_class_pred":r["val"]["one_class_pred"]},sort_keys=True),flush=True)
    agg=aggregate(results); best=best_by_task(agg); any_mod=any(r["moderate_pass"] for r in agg); any_str=any(r["strong_pass"] for r in agg)
    interp = "Strong pass observed. Stop for Control Tower review before any Wave 2 EMG, pairwise EMG, or fusion-readiness work." if any_str else "Moderate pass observed. Stop for Control Tower review before any Wave 2 EMG, pairwise EMG, or fusion-readiness work." if any_mod else "No moderate pass observed. W1C provides an independent EMG ridge reference but does not justify Wave 2 EMG or fusion-readiness work by itself."
    rep={"status":"complete","generated_at_utc":now(),"branch":"idare/wave1/emg-baseline-ablation",
         "config":{"run_tag":a.run_tag,"feature_npy":str(a.feature_npy),"feature_index":str(a.feature_index),"bsl_npy":str(a.bsl_npy),"bsl_index":str(a.bsl_index),"tasks":a.tasks,"label_policy":a.label_policy,"folds":a.folds,"fold_seed":a.fold_seed,"ridge_alpha":a.ridge_alpha,"max_runs":a.max_runs,"alignment_common_cols":data["alignment_common_cols"]},
         "scope_guardrails":["I-DARE only","EMG only","binary formulation","ridge only","no EEG","no fusion","no DEAP","no neural training","no cache overwrite","no broad hyperparameter search","no push to main"],
         "counts":{"subjects":len(subjects),"registered_runs_executed":len(results),"max_allowed_runs":72,"prediction_rows":len(predrows)},
         "registered_cells":[{"cell":c,"input_kind":i,"normalization":n} for c,i,n in CELLS],"comparison_baselines":REF,"pass_gates":{"moderate_balanced_accuracy":0.54,"strong_balanced_accuracy":0.55},"aggregate":agg,"best_by_task":best,"runs":results,"interpretation":interp,
         "not_started":["EEG","fusion","pairwise EMG retest","neural training","broad hyperparameter search","DEAP","cache overwrite","push to main"]}
    a.out_json.parent.mkdir(parents=True,exist_ok=True); a.out_json.write_text(json.dumps(rep,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    write_md(rep,a.out_md); write_csv(predrows,a.out_predictions_csv)
    if a.out_closeout_md and a.out_closeout_json: write_closeout(rep,a.out_closeout_md,a.out_closeout_json)
    print(f"[DONE] wrote {a.out_md}"); print(f"[DONE] wrote {a.out_json}"); print(f"[DONE] wrote {a.out_predictions_csv}")
    if a.out_closeout_md and a.out_closeout_json: print(f"[DONE] wrote {a.out_closeout_md}"); print(f"[DONE] wrote {a.out_closeout_json}")

if __name__ == "__main__": main()
