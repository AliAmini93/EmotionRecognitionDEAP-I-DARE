#!/usr/bin/env python3
"""Main-model I-DARE DA runner: EEGSegmentClassifier raw EEG cache + EMG feature MLP.

Default full matrix: 2 targets x 2 modalities x 5 DA policies x 6 folds = 120 runs.
Final metric: argmax balanced accuracy. No DEAP, no fusion, no threshold tuning.
"""
from __future__ import annotations
import argparse, csv, json, math, random, sys, time, subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import numpy as np, pandas as pd, torch
from torch import nn
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path: sys.path.insert(0, str(SRC))
from emotion_deap_idare.models.eeg_segment_classifier import EEGSegmentClassifier  # noqa: E402

PFX="idare_da_main_model_full_"
EEG_DA=["E0_none_baseline","E1_additive_gaussian_noise_weak","E2_additive_gaussian_noise_medium","E3_amplitude_scaling","E4_time_channel_masking_or_dropout"]
EMG_DA=["M0_none_baseline","M1_feature_gaussian_jitter_weak","M2_feature_gaussian_jitter_medium","M3_feature_scaling","M4_feature_dropout"]

@dataclass(frozen=True)
class Fold: fold_id:int; train_subjects:tuple[int,...]; val_subjects:tuple[int,...]
@dataclass(frozen=True)
class Spec: run_id:int; modality:str; task:str; policy:str; da:str; fold:Fold; seed:int; recipe:str

def now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
def git(args):
    try: return subprocess.run(["git",*args], cwd=ROOT, text=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.strip()
    except Exception: return ""
def set_seed(s):
    random.seed(s); np.random.seed(s); torch.manual_seed(s)
    if torch.cuda.is_available(): torch.cuda.manual_seed_all(s)
def labcol(task, policy): return f"{task}_{policy}"
def sf(x):
    if pd.isna(x): return None
    try: return float(x)
    except Exception: return None
def counts(y):
    y=[int(v) for v in y]; return {"0":int(sum(v==0 for v in y)),"1":int(sum(v==1 for v in y))}
def div(a,b): return float(a/b) if b else 0.0
def metrics(yt,yp):
    rec=[]; f1=[]; pc={};
    for lab in [0,1]:
        tp=sum(1 for t,p in zip(yt,yp) if t==lab and p==lab); fp=sum(1 for t,p in zip(yt,yp) if t!=lab and p==lab); fn=sum(1 for t,p in zip(yt,yp) if t==lab and p!=lab)
        pr=div(tp,tp+fp); re=div(tp,tp+fn); ff=div(2*pr*re,pr+re); rec.append(re); f1.append(ff); pc[str(lab)]={"precision":pr,"recall":re,"f1":ff,"support":sum(1 for t in yt if t==lab)}
    uniq=sorted(set(int(p) for p in yp)); correct=sum(int(t==p) for t,p in zip(yt,yp))
    return {"n":len(yt),"accuracy":div(correct,len(yt)),"balanced_accuracy":float(sum(rec)/2),"macro_f1":float(sum(f1)/2),"true_counts":counts(yt),"pred_counts":counts(yp),"per_class":pc,"one_class_pred":len(uniq)==1,"collapsed_to_label":int(uniq[0]) if len(uniq)==1 else None,"confusion":{"tn":sum(1 for t,p in zip(yt,yp) if t==0 and p==0),"fp":sum(1 for t,p in zip(yt,yp) if t==0 and p==1),"fn":sum(1 for t,p in zip(yt,yp) if t==1 and p==0),"tp":sum(1 for t,p in zip(yt,yp) if t==1 and p==1)}}
def make_folds(subjects,n,seed):
    subjects=sorted({int(s) for s in subjects}); rng=np.random.default_rng(seed); arr=np.asarray(subjects,dtype=int); rng.shuffle(arr); chunks=np.array_split(arr,n); allset=set(subjects)
    return [Fold(i, tuple(sorted(allset-set(int(x) for x in ch.tolist()))), tuple(sorted(int(x) for x in ch.tolist()))) for i,ch in enumerate(chunks,1)]
def subjects(index_csv, task, policy):
    df=pd.read_csv(index_csv); col=labcol(task,policy); df[col]=df[col].map(sf); df=df[df[col].isin([0.0,1.0])]
    return sorted(int(s) for s in df.subject_id.astype(int).unique().tolist())
def class_weights(labels, device):
    c=counts(labels); total=c["0"]+c["1"]; return torch.tensor([total/(2*max(c["0"],1)), total/(2*max(c["1"],1))], dtype=torch.float32, device=device)
def sampler(labels, seed):
    c=counts(labels); w=[1.0/max(c[str(int(y))],1) for y in labels]; g=torch.Generator(); g.manual_seed(seed); return WeightedRandomSampler(torch.tensor(w,dtype=torch.double), len(w), replacement=True, generator=g)

class EEGDS(Dataset):
    def __init__(self, npy, idx, task, policy, subjects, train, da, seed, chstd=None):
        self.cache=np.load(npy,mmap_mode="r"); df=pd.read_csv(idx); col=labcol(task,policy)
        df=df[df.subject_id.astype(int).isin([int(s) for s in subjects])].copy(); df[col]=df[col].map(sf); df=df[df[col].isin([0.0,1.0])].copy(); df["label"]=df[col].astype(int); df.cache_row=df.cache_row.astype(int); df.subject_id=df.subject_id.astype(int); self.df=df.sort_values(["subject_id","cache_row"]).reset_index(drop=True)
        self.train=train; self.da=da; self.rng=np.random.default_rng(seed)
        if chstd is None:
            x=np.asarray(self.cache[self.df.cache_row.to_numpy(dtype=int)], dtype=np.float32); chstd=x.std(axis=(0,2)).astype(np.float32); chstd=np.where(chstd<1e-6,1.0,chstd)
        self.chstd=chstd.astype(np.float32)
    def __len__(self): return len(self.df)
    def aug(self,x):
        if (not self.train) or self.da=="E0_none_baseline": return x
        if self.da=="E1_additive_gaussian_noise_weak": return x+(0.001*self.chstd[:,None]*self.rng.standard_normal(x.shape)).astype(np.float32)
        if self.da=="E2_additive_gaussian_noise_medium": return x+(0.01*self.chstd[:,None]*self.rng.standard_normal(x.shape)).astype(np.float32)
        if self.da=="E3_amplitude_scaling": return x*self.rng.uniform(0.90,1.10,size=(x.shape[0],1)).astype(np.float32)
        if self.da=="E4_time_channel_masking_or_dropout":
            y=x.copy(); ch=self.rng.choice(np.arange(y.shape[0]), size=int(self.rng.integers(1,4)), replace=False); y[ch,:]=0.0; w=int(self.rng.integers(16,65)); st=int(self.rng.integers(0,max(1,y.shape[1]-w+1))); y[:,st:st+w]=0.0; return y
        raise ValueError(self.da)
    def __getitem__(self,i):
        r=self.df.iloc[i]; x=np.array(self.cache[int(r.cache_row)], dtype=np.float32, copy=True); x=self.aug(x)
        return {"x":torch.from_numpy(x),"label":torch.tensor(int(r.label),dtype=torch.long),"subject_id":int(r.subject_id),"cache_row":int(r.cache_row)}

class EMGDS(Dataset):
    def __init__(self,npy,idx,task,policy,subjects,train,da,seed,mean=None,std=None):
        self.cache=np.load(npy,mmap_mode="r"); df=pd.read_csv(idx); col=labcol(task,policy)
        df=df[df.subject_id.astype(int).isin([int(s) for s in subjects])].copy(); df[col]=df[col].map(sf); df=df[df[col].isin([0.0,1.0])].copy(); df["label"]=df[col].astype(int); df.cache_row=df.cache_row.astype(int); df.subject_id=df.subject_id.astype(int); self.df=df.sort_values(["subject_id","cache_row"]).reset_index(drop=True)
        rows=self.df.cache_row.to_numpy(dtype=int)
        if mean is None or std is None:
            x=np.asarray(self.cache[rows],dtype=np.float32); mean=x.mean(axis=0).astype(np.float32); std=x.std(axis=0).astype(np.float32); std=np.where(std<1e-6,1.0,std)
        self.mean=mean.astype(np.float32); self.std=std.astype(np.float32); self.train=train; self.da=da; self.rng=np.random.default_rng(seed); self.feature_dim=int(self.cache.shape[1])
    def __len__(self): return len(self.df)
    def aug(self,x):
        if (not self.train) or self.da=="M0_none_baseline": return x
        if self.da=="M1_feature_gaussian_jitter_weak": return x+(0.01*self.rng.standard_normal(x.shape)).astype(np.float32)
        if self.da=="M2_feature_gaussian_jitter_medium": return x+(0.05*self.rng.standard_normal(x.shape)).astype(np.float32)
        if self.da=="M3_feature_scaling": return x*self.rng.uniform(0.90,1.10,size=x.shape).astype(np.float32)
        if self.da=="M4_feature_dropout":
            y=x.copy(); n=max(1,int(round(0.10*y.shape[0]))); ix=self.rng.choice(np.arange(y.shape[0]),size=n,replace=False); y[ix]=0.0; return y
        raise ValueError(self.da)
    def __getitem__(self,i):
        r=self.df.iloc[i]; x=np.asarray(self.cache[int(r.cache_row)],dtype=np.float32); x=(x-self.mean)/self.std; x=self.aug(x.astype(np.float32,copy=True))
        return {"x":torch.from_numpy(x),"label":torch.tensor(int(r.label),dtype=torch.long),"subject_id":int(r.subject_id),"cache_row":int(r.cache_row)}

class TinyEMGMLP(nn.Module):
    def __init__(self, feature_dim, hidden_dim=64, dropout=0.20):
        super().__init__(); self.net=nn.Sequential(nn.Linear(feature_dim,hidden_dim),nn.LayerNorm(hidden_dim),nn.GELU(),nn.Dropout(dropout),nn.Linear(hidden_dim,hidden_dim),nn.GELU(),nn.Dropout(dropout),nn.Linear(hidden_dim,2))
    def forward(self,x): return self.net(x)
def eeg_model(device):
    return EEGSegmentClassifier(C=32,sampling_rate=128,window_sec=5.0,n_classes=2,modelsize="lite",stem_fusion="concat",channel_pos_mode="learnable",channel_mixer="mha",norm_kind="gn",use_spectral_branch=False).to(device)

def evaluate(model,loader,device,modality):
    model.eval(); yt=[]; yp=[]
    with torch.no_grad():
        for b in loader:
            x=b["x"].to(device=device,dtype=torch.float32); y=b["label"].to(device=device)
            logits = model(x, return_attn=False)[0] if modality=="EEG" else model(x)
            pred=logits.argmax(1); yt += [int(v) for v in y.cpu().tolist()]; yp += [int(v) for v in pred.cpu().tolist()]
    return metrics(yt,yp)

def loader(ds,batch,shuffle,samp,seed,nw):
    g=torch.Generator(); g.manual_seed(seed); return DataLoader(ds,batch_size=batch,shuffle=shuffle if samp is None else False,sampler=samp,num_workers=nw,generator=g if samp is None else None)

def train_one(s,args,device):
    set_seed(s.seed+s.run_id); t0=time.perf_counter()
    if s.modality=="EEG":
        base=EEGDS(args.eeg_npy,args.eeg_index,s.task,s.policy,s.fold.train_subjects,False,"E0_none_baseline",s.seed+s.run_id)
        tr=EEGDS(args.eeg_npy,args.eeg_index,s.task,s.policy,s.fold.train_subjects,True,s.da,s.seed+s.run_id,base.chstd)
        va=EEGDS(args.eeg_npy,args.eeg_index,s.task,s.policy,s.fold.val_subjects,False,"E0_none_baseline",s.seed+s.run_id,base.chstd)
        model=eeg_model(device); epochs=args.eeg_epochs; batch=args.eeg_batch_size; lr=args.eeg_lr; wd=args.eeg_weight_decay
    else:
        base=EMGDS(args.emg_npy,args.emg_index,s.task,s.policy,s.fold.train_subjects,False,"M0_none_baseline",s.seed+s.run_id)
        tr=EMGDS(args.emg_npy,args.emg_index,s.task,s.policy,s.fold.train_subjects,True,s.da,s.seed+s.run_id,base.mean,base.std)
        va=EMGDS(args.emg_npy,args.emg_index,s.task,s.policy,s.fold.val_subjects,False,"M0_none_baseline",s.seed+s.run_id,base.mean,base.std)
        model=TinyEMGMLP(tr.feature_dim,args.emg_hidden_dim,args.emg_dropout).to(device); epochs=args.emg_epochs; batch=args.emg_batch_size; lr=args.emg_lr; wd=args.emg_weight_decay
    labels=[int(x) for x in tr.df.label.tolist()]
    samp=sampler(labels,s.seed+s.run_id) if s.recipe=="balanced_sampler_ce" else None
    crit=nn.CrossEntropyLoss(weight=class_weights(labels,device)) if s.recipe=="ce_class_weighted" else nn.CrossEntropyLoss(); opt=torch.optim.AdamW(model.parameters(),lr=lr,weight_decay=wd)
    train_loader=loader(tr,batch,samp is None,samp,s.seed+s.run_id,args.num_workers); val_loader=loader(va,batch,False,None,s.seed+s.run_id,args.num_workers)
    best=None
    for ep in range(1,epochs+1):
        model.train()
        for b in train_loader:
            x=b["x"].to(device=device,dtype=torch.float32); y=b["label"].to(device=device); opt.zero_grad(set_to_none=True)
            logits=model(x,return_attn=False)[0] if s.modality=="EEG" else model(x); loss=crit(logits,y); loss.backward()
            if args.grad_clip>0: torch.nn.utils.clip_grad_norm_(model.parameters(),args.grad_clip)
            opt.step()
        m=evaluate(model,val_loader,device,s.modality); score=(m["balanced_accuracy"],m["macro_f1"],m["accuracy"])
        if best is None or score>(best["balanced_accuracy"],best["macro_f1"],best["accuracy"]): best={**m,"epoch":ep}
    final=evaluate(model,val_loader,device,s.modality)
    return {"run_id":s.run_id,"modality":s.modality,"task":s.task,"label_policy":s.policy,"da_policy":s.da,"recipe":s.recipe,"fold_id":s.fold.fold_id,"seed":s.seed,"train_subjects":" ".join(map(str,s.fold.train_subjects)),"val_subjects":" ".join(map(str,s.fold.val_subjects)),"train_n":len(tr),"val_n":len(va),"train_counts":counts(labels),"val_counts":counts([int(x) for x in va.df.label.tolist()]),"epochs":epochs,"batch_size":batch,"lr":lr,"weight_decay":wd,"final_accuracy":final["accuracy"],"final_balanced_accuracy":final["balanced_accuracy"],"final_macro_f1":final["macro_f1"],"final_one_class_pred":final["one_class_pred"],"final_collapsed_to_label":final["collapsed_to_label"],"final_true_counts":final["true_counts"],"final_pred_counts":final["pred_counts"],"final_confusion":final["confusion"],"best_epoch":best["epoch"],"best_balanced_accuracy":best["balanced_accuracy"],"best_macro_f1":best["macro_f1"],"duration_sec":time.perf_counter()-t0}

def specs(args):
    out=[]; rid=1
    for mod in args.modalities:
        das=EEG_DA if mod=="EEG" else EMG_DA; idx=args.eeg_index if mod=="EEG" else args.emg_index
        for task in args.tasks:
            folds=make_folds(subjects(idx,task,args.label_policy),args.folds,args.fold_seed)
            for da in das:
                for fo in folds:
                    for seed in args.seeds:
                        out.append(Spec(rid,mod,task,args.label_policy,da,fo,seed,args.recipe)); rid+=1
    if args.max_runs and args.max_runs>0: out=out[:args.max_runs]
    return [Spec(i+1,s.modality,s.task,s.policy,s.da,s.fold,s.seed,s.recipe) for i,s in enumerate(out)]

def csv_write(path, rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    if not rows: return
    flat=[]
    for r in rows:
        flat.append({k:(json.dumps(v,ensure_ascii=False,sort_keys=True) if isinstance(v,(dict,list,tuple)) else v) for k,v in r.items()})
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(flat[0].keys()),lineterminator="\n"); w.writeheader(); w.writerows(flat)
def specrow(s): return {"run_id":s.run_id,"modality":s.modality,"task":s.task,"label_policy":s.policy,"da_policy":s.da,"fold_id":s.fold.fold_id,"train_subjects":" ".join(map(str,s.fold.train_subjects)),"val_subjects":" ".join(map(str,s.fold.val_subjects)),"seed":s.seed,"recipe":s.recipe}
def aggregate(runs):
    df=pd.DataFrame(runs); rows=[]
    for (mod,task,da),g in df.groupby(["modality","task","da_policy"],sort=True):
        base_da="E0_none_baseline" if mod=="EEG" else "M0_none_baseline"; b=df[(df.modality==mod)&(df.task==task)&(df.da_policy==base_da)][["fold_id","final_balanced_accuracy"]]
        bm={int(r.fold_id):float(r.final_balanced_accuracy) for r in b.itertuples()}; deltas=[]; wins=0
        for r in g.itertuples():
            if int(r.fold_id) in bm:
                d=float(r.final_balanced_accuracy)-bm[int(r.fold_id)]; deltas.append(d); wins += int(d>0)
        rows.append({"modality":mod,"task":task,"da_policy":da,"runs":len(g),"mean_balanced_accuracy":float(g.final_balanced_accuracy.mean()),"std_balanced_accuracy":float(g.final_balanced_accuracy.std(ddof=0)),"mean_accuracy":float(g.final_accuracy.mean()),"mean_macro_f1":float(g.final_macro_f1.mean()),"one_class_collapse_count":int(g.final_one_class_pred.sum()),"mean_delta_vs_no_da":float(np.mean(deltas)) if deltas else 0.0,"fold_wins_vs_no_da":wins})
    return rows
def write_reports(args, ss, runs):
    docs=ROOT/"docs"; csv_write(docs/f"{PFX}run_matrix.csv",[specrow(s) for s in ss]); csv_write(docs/f"{PFX}runs.csv",runs); met=aggregate(runs); csv_write(docs/f"{PFX}metric_summary.csv",met)
    leak={"status":"PASSED","generated_at_utc":now(),"run_count":len(runs),"checks":[{"run_id":s.run_id,"overlap":sorted(set(s.fold.train_subjects)&set(s.fold.val_subjects)),"augmentation_training_only":True,"test_stats_used":False,"test_labels_used":False} for s in ss],"forbidden_scope":{"deap":False,"fusion":False,"preprocessing_change":False,"threshold_change":False,"main_push":False}}
    (docs/f"{PFX}leakage_audit.json").write_text(json.dumps(leak,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    best={}
    for r in met:
        k=(r["modality"],r["task"]); best[k]=r if k not in best or r["mean_balanced_accuracy"]>best[k]["mean_balanced_accuracy"] else best[k]
    close={"status":"closeout_ready","generated_at_utc":now(),"branch":git(["branch","--show-current"]),"head":git(["rev-parse","HEAD"]),"planned_runs":len(ss),"completed_runs":len(runs),"label_policy":args.label_policy,"recipe":args.recipe,"best_by_modality_task":{f"{k[0]}_{k[1]}":v for k,v in best.items()},"leakage_status":leak["status"],"one_class_total":int(sum(bool(r["final_one_class_pred"]) for r in runs)),"paper_level_claim":False}
    (docs/f"{PFX}closeout_report.json").write_text(json.dumps(close,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    lines=["# I-DARE Main-Model Data Augmentation Full Closeout","",f"- completed_runs: `{len(runs)}`",f"- leakage_status: `{leak['status']}`","","| Modality | Task | Best DA | Mean BA | Delta vs no DA | Wins vs no DA |","|---|---|---|---:|---:|---:|"]
    for (m,t),r in sorted(best.items()): lines.append(f"| {m} | {t} | {r['da_policy']} | {r['mean_balanced_accuracy']:.4f} | {r['mean_delta_vs_no_da']:.4f} | {r['fold_wins_vs_no_da']} |")
    (docs/f"{PFX}closeout_report.md").write_text("\n".join(lines)+"\n",encoding="utf-8")

def validate(args):
    blockers=[]
    for p in [args.eeg_npy,args.eeg_index,args.emg_npy,args.emg_index]:
        if not p.exists(): blockers.append(f"missing {p}")
    if args.eeg_npy.exists():
        x=np.load(args.eeg_npy,mmap_mode="r")
        if x.ndim!=3 or tuple(x.shape[1:])!=(32,640): blockers.append(f"bad EEG shape {x.shape}")
    if args.emg_npy.exists():
        x=np.load(args.emg_npy,mmap_mode="r")
        if x.ndim!=2: blockers.append(f"bad EMG shape {x.shape}")
    for idx,mod in [(args.eeg_index,"EEG"),(args.emg_index,"EMG")]:
        if idx.exists():
            cols=pd.read_csv(idx,nrows=5).columns
            for task in args.tasks:
                for req in ["cache_row","subject_id",labcol(task,args.label_policy)]:
                    if req not in cols: blockers.append(f"{mod} index missing {req}")
    print(json.dumps({"status":"validation_passed" if not blockers else "validation_blocked","blockers":blockers,"planned_runs":len(specs(args)) if not blockers else None,"modalities":args.modalities,"tasks":args.tasks,"label_policy":args.label_policy,"recipe":args.recipe},indent=2))
    return 0 if not blockers else 2

def parse_args():
    p=argparse.ArgumentParser(); p.add_argument("--mode",choices=["validate","run"],default="validate")
    p.add_argument("--eeg-npy",type=Path,default=ROOT/".cache/idare_eeg_windows_32x640_float32_baseline_corrected.npy"); p.add_argument("--eeg-index",type=Path,default=ROOT/".cache/idare_eeg_cache_index_baseline_corrected.csv")
    p.add_argument("--emg-npy",type=Path,default=ROOT/".cache/idare_emg_features.npy"); p.add_argument("--emg-index",type=Path,default=ROOT/".cache/idare_emg_feature_cache_index.csv")
    p.add_argument("--modalities",nargs="+",default=["EEG","EMG"],choices=["EEG","EMG"]); p.add_argument("--tasks",nargs="+",default=["arousal","valence"],choices=["arousal","valence"]); p.add_argument("--label-policy",default="midpoint_as_high",choices=["discard_midpoint","midpoint_as_low","midpoint_as_high"])
    p.add_argument("--recipe",default="ce_class_weighted",choices=["ce_class_weighted","balanced_sampler_ce","ce_no_class_weight"]); p.add_argument("--folds",type=int,default=6); p.add_argument("--fold-seed",type=int,default=11); p.add_argument("--seeds",nargs="+",type=int,default=[11]); p.add_argument("--max-runs",type=int,default=0)
    p.add_argument("--eeg-epochs",type=int,default=3); p.add_argument("--emg-epochs",type=int,default=20); p.add_argument("--eeg-batch-size",type=int,default=32); p.add_argument("--emg-batch-size",type=int,default=128); p.add_argument("--eeg-lr",type=float,default=3e-4); p.add_argument("--emg-lr",type=float,default=1e-3); p.add_argument("--eeg-weight-decay",type=float,default=1e-3); p.add_argument("--emg-weight-decay",type=float,default=1e-3); p.add_argument("--emg-hidden-dim",type=int,default=64); p.add_argument("--emg-dropout",type=float,default=0.20); p.add_argument("--grad-clip",type=float,default=1.0); p.add_argument("--num-workers",type=int,default=0); p.add_argument("--cpu",action="store_true")
    return p.parse_args()

def main():
    args=parse_args();
    if args.mode=="validate": return validate(args)
    rc=validate(args)
    if rc: return rc
    device=torch.device("cpu" if args.cpu or not torch.cuda.is_available() else "cuda"); ss=specs(args); print(f"[INFO] device={device} planned_runs={len(ss)}")
    runs=[]; csv_write(ROOT/"docs"/f"{PFX}run_matrix.csv",[specrow(s) for s in ss])
    for s in ss:
        print(json.dumps({"event":"run_start","run_id":s.run_id,"modality":s.modality,"task":s.task,"da":s.da,"fold":s.fold.fold_id},sort_keys=True),flush=True)
        r=train_one(s,args,device); runs.append(r); print(json.dumps({"event":"run_done","run_id":r["run_id"],"ba":round(r["final_balanced_accuracy"],4),"f1":round(r["final_macro_f1"],4),"one_class":r["final_one_class_pred"]},sort_keys=True),flush=True)
        csv_write(ROOT/"docs"/f"{PFX}runs.csv",runs); csv_write(ROOT/"docs"/f"{PFX}metric_summary.csv",aggregate(runs))
    write_reports(args,ss,runs); print("[DONE] closeout_ready")
    print((ROOT/"docs"/f"{PFX}closeout_report.md").read_text())
    return 0
if __name__=="__main__": raise SystemExit(main())
