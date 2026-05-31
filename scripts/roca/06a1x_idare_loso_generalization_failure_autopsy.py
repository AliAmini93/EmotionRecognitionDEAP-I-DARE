#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.linear_model import Ridge
from sklearn.model_selection import KFold, LeaveOneGroupOut
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / ".cache"
ROCA = ROOT / "docs" / "roca"
OUT_PREFIX = "idare_06a1x_loso_generalization_failure_autopsy_current"

EEG_CACHE = CACHE / "idare_eeg_windows_32x640_float32_baseline_corrected.npy"
EEG_INDEX = CACHE / "idare_eeg_cache_index_baseline_corrected.csv"

PREVIOUS_DEEP_DECISION = ROCA / "idare_06a1_previous_model_deep_residual_probe_current_decision_table.csv"
PREVIOUS_DEEP_SUBJECT = ROCA / "idare_06a1_previous_model_deep_residual_probe_current_subject_stats.csv"
REFERENCE_05AJB = ROCA / "idare_high_disagreement_direct_deviation_confirmatory_stats_current_verdict.csv"


def read_csv_optional(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception as exc:
        print(f"[WARN] could not read {path}: {exc}")
        return pd.DataFrame()


def find_col(df: pd.DataFrame, candidates: list[str], required: bool = True) -> str | None:
    lower = {str(c).lower(): c for c in df.columns}
    for c in candidates:
        if c.lower() in lower:
            return lower[c.lower()]
    if required:
        raise SystemExit(f"Could not find any of columns {candidates}. Available columns: {list(df.columns)}")
    return None


def rmse(y: np.ndarray, p: np.ndarray) -> float:
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    m = np.isfinite(y) & np.isfinite(p)
    if m.sum() == 0:
        return float("nan")
    return float(np.sqrt(np.mean((y[m] - p[m]) ** 2)))


def pearson(y: np.ndarray, p: np.ndarray) -> float:
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    m = np.isfinite(y) & np.isfinite(p)
    if m.sum() < 3:
        return float("nan")
    yy = y[m] - np.mean(y[m])
    pp = p[m] - np.mean(p[m])
    den = float(np.sqrt(np.sum(yy ** 2) * np.sum(pp ** 2)))
    if den <= 0:
        return float("nan")
    return float(np.sum(yy * pp) / den)


def sign_acc(y: np.ndarray, p: np.ndarray) -> float:
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    m = np.isfinite(y) & np.isfinite(p) & (y != 0)
    if m.sum() == 0:
        return float("nan")
    return float(np.mean(np.sign(y[m]) == np.sign(p[m])))


def md_table(df: pd.DataFrame, max_rows: int = 40) -> str:
    if df.empty:
        return "(empty)\n"
    x = df.head(max_rows).copy()
    cols = list(x.columns)
    def fmt(v):
        if pd.isna(v):
            return ""
        if isinstance(v, float):
            if abs(v) >= 1000:
                return f"{v:.3f}"
            return f"{v:.6g}"
        return str(v)
    rows = []
    rows.append("| " + " | ".join(cols) + " |")
    rows.append("| " + " | ".join(["---"] * len(cols)) + " |")
    for _, r in x.iterrows():
        rows.append("| " + " | ".join(fmt(r[c]).replace("|", "\\|") for c in cols) + " |")
    return "\n".join(rows) + "\n"


def to_jsonable(obj):
    if isinstance(obj, dict):
        return {str(k): to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_jsonable(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        v = float(obj)
        return None if not math.isfinite(v) else v
    if isinstance(obj, float):
        return None if not math.isfinite(obj) else obj
    if isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    return obj


def compute_leave_subject_out_stimulus_mean(df: pd.DataFrame, y_col: str, stim_col: str) -> np.ndarray:
    sums = df.groupby(stim_col)[y_col].transform("sum").astype(float)
    counts = df.groupby(stim_col)[y_col].transform("count").astype(float)
    y = df[y_col].astype(float)
    return ((sums - y) / np.maximum(counts - 1, 1)).to_numpy(dtype=float)


def build_eeg_summary_features(x: np.ndarray, sample_rate: float = 128.0) -> tuple[np.ndarray, list[str]]:
    # x: [n, channels, time]
    x = np.asarray(x, dtype=np.float32)
    n, ch, t = x.shape

    means = x.mean(axis=2)
    stds = x.std(axis=2)
    rms = np.sqrt(np.mean(x * x, axis=2) + 1e-8)

    feats = [means, stds, rms]
    names = []
    for prefix in ["mean", "std", "rms"]:
        names.extend([f"{prefix}_ch{j:02d}" for j in range(ch)])

    # Cheap spectral summary. This is not intended as a final feature set.
    freqs = np.fft.rfftfreq(t, d=1.0 / sample_rate)
    spec = np.abs(np.fft.rfft(x, axis=2)) ** 2
    bands = [
        ("delta_1_4", 1.0, 4.0),
        ("theta_4_8", 4.0, 8.0),
        ("alpha_8_13", 8.0, 13.0),
        ("beta_13_30", 13.0, 30.0),
        ("gamma_30_45", 30.0, 45.0),
    ]
    for name, lo, hi in bands:
        mask = (freqs >= lo) & (freqs < hi)
        if not np.any(mask):
            bp = np.zeros((n, ch), dtype=np.float32)
        else:
            bp = np.log1p(spec[:, :, mask].mean(axis=2)).astype(np.float32)
        feats.append(bp)
        names.extend([f"{name}_ch{j:02d}" for j in range(ch)])

    out = np.concatenate(feats, axis=1).astype(np.float32)
    return out, names


def split_eval(
    split_name: str,
    splits,
    x_feat: np.ndarray,
    y_dev: np.ndarray,
    high_mask: np.ndarray,
    alpha: float = 100.0,
) -> dict:
    pred = np.full(len(y_dev), np.nan, dtype=float)
    fold_count = 0

    for train_idx, test_idx in splits:
        train_idx = np.asarray(train_idx, dtype=int)
        test_idx = np.asarray(test_idx, dtype=int)
        if len(train_idx) < 10 or len(test_idx) == 0:
            continue
        model = make_pipeline(
            StandardScaler(with_mean=True, with_std=True),
            Ridge(alpha=alpha, random_state=0),
        )
        model.fit(x_feat[train_idx], y_dev[train_idx])
        pred[test_idx] = model.predict(x_feat[test_idx])
        fold_count += 1

    valid = np.isfinite(pred)
    high = valid & high_mask

    out = {
        "split": split_name,
        "folds": fold_count,
        "alpha": alpha,
        "n_all": int(valid.sum()),
        "n_high": int(high.sum()),
        "zero_rmse_all": rmse(y_dev[valid], np.zeros(valid.sum())),
        "model_rmse_all": rmse(y_dev[valid], pred[valid]),
        "lift_vs_zero_all": rmse(y_dev[valid], np.zeros(valid.sum())) - rmse(y_dev[valid], pred[valid]),
        "pearson_all": pearson(y_dev[valid], pred[valid]),
        "sign_acc_all": sign_acc(y_dev[valid], pred[valid]),
        "zero_rmse_high": rmse(y_dev[high], np.zeros(high.sum())),
        "model_rmse_high": rmse(y_dev[high], pred[high]),
        "lift_vs_zero_high": rmse(y_dev[high], np.zeros(high.sum())) - rmse(y_dev[high], pred[high]),
        "pearson_high": pearson(y_dev[high], pred[high]),
        "sign_acc_high": sign_acc(y_dev[high], pred[high]),
    }
    return out


def make_within_subject_folds(subjects: np.ndarray, n_splits: int = 5, seed: int = 11):
    rng = np.random.default_rng(seed)
    subjects = np.asarray(subjects)
    fold_ids = np.full(len(subjects), -1, dtype=int)
    for s in np.unique(subjects):
        idx = np.where(subjects == s)[0]
        rng.shuffle(idx)
        for j, ii in enumerate(idx):
            fold_ids[ii] = j % n_splits

    for f in range(n_splits):
        test = np.where(fold_ids == f)[0]
        train = np.where(fold_ids != f)[0]
        yield train, test


def variance_decomposition(df: pd.DataFrame, y_col: str, dev: np.ndarray, subj_col: str, stim_col: str) -> pd.DataFrame:
    y = df[y_col].to_numpy(dtype=float)
    subj = df[subj_col].to_numpy()
    stim = df[stim_col].to_numpy()

    rows = []

    def add_var(name, values, total):
        v = float(np.nanvar(values))
        rows.append({
            "quantity": name,
            "variance": v,
            "proportion_of_total": v / total if total > 0 else np.nan,
        })

    y_total = float(np.nanvar(y))
    dev_total = float(np.nanvar(dev))

    subj_mean_y = pd.Series(y).groupby(subj).transform("mean").to_numpy(dtype=float)
    stim_mean_y = pd.Series(y).groupby(stim).transform("mean").to_numpy(dtype=float)
    subj_mean_dev = pd.Series(dev).groupby(subj).transform("mean").to_numpy(dtype=float)
    stim_mean_dev = pd.Series(dev).groupby(stim).transform("mean").to_numpy(dtype=float)

    add_var("raw_rating_total", y, y_total)
    add_var("raw_rating_subject_mean_component", subj_mean_y, y_total)
    add_var("raw_rating_stimulus_mean_component", stim_mean_y, y_total)
    add_var("leave_subject_out_deviation_total", dev, dev_total)
    add_var("deviation_subject_mean_component", subj_mean_dev, dev_total)
    add_var("deviation_stimulus_mean_component", stim_mean_dev, dev_total)

    return pd.DataFrame(rows)


def domain_shift_by_subject(x_feat: np.ndarray, subjects: np.ndarray, deep_subject_stats: pd.DataFrame) -> pd.DataFrame:
    z = StandardScaler().fit_transform(x_feat)
    rows = []
    for s in np.unique(subjects):
        m = subjects == s
        other = ~m
        centroid_s = z[m].mean(axis=0)
        centroid_o = z[other].mean(axis=0)
        dist_to_others = float(np.linalg.norm(centroid_s - centroid_o))
        within = float(np.sqrt(np.mean(np.sum((z[m] - centroid_s) ** 2, axis=1)))) if m.sum() > 1 else np.nan
        rows.append({
            "subject_id": s,
            "n_trials": int(m.sum()),
            "centroid_distance_to_other_subjects": dist_to_others,
            "within_subject_dispersion": within,
            "distance_over_within": dist_to_others / within if within and np.isfinite(within) and within > 0 else np.nan,
        })

    out = pd.DataFrame(rows)

    if not deep_subject_stats.empty:
        subj_col = find_col(deep_subject_stats, ["subject_id", "test_subject", "subject"], required=False)
        if subj_col is not None:
            tmp = deep_subject_stats.copy()
            tmp[subj_col] = tmp[subj_col].astype(str)
            out["subject_id_str"] = out["subject_id"].astype(str)
            metric_cols = [c for c in tmp.columns if any(k in c.lower() for k in ["rmse", "lift", "improvement", "delta"])]
            keep = [subj_col] + metric_cols[:12]
            out = out.merge(tmp[keep], left_on="subject_id_str", right_on=subj_col, how="left")
            out = out.drop(columns=["subject_id_str"], errors="ignore")
    return out


def main() -> None:
    ROCA.mkdir(parents=True, exist_ok=True)

    if not EEG_CACHE.exists():
        raise SystemExit(f"Missing EEG cache: {EEG_CACHE}")
    if not EEG_INDEX.exists():
        raise SystemExit(f"Missing EEG index: {EEG_INDEX}")

    print(f"[INFO] loading EEG cache: {EEG_CACHE}")
    eeg = np.load(EEG_CACHE, mmap_mode="r")
    idx = pd.read_csv(EEG_INDEX)
    print(f"[INFO] EEG shape={tuple(eeg.shape)} index_rows={len(idx)}")

    if len(idx) != eeg.shape[0]:
        raise SystemExit(f"EEG/index row mismatch: eeg={eeg.shape[0]} index={len(idx)}")

    subj_col = find_col(idx, ["subject_id", "subject", "participant_id", "participant", "subj", "test_subject"])
    stim_col = find_col(idx, ["stimulus_id", "stimulus", "trial_id", "trial", "video_id"])
    y_col = find_col(idx, ["arousal_score", "arousal", "y_arousal", "label_arousal"])

    idx = idx.copy()
    idx[subj_col] = idx[subj_col].astype(str)
    idx[stim_col] = idx[stim_col].astype(str)
    y = idx[y_col].astype(float).to_numpy()

    train_stim_mean = compute_leave_subject_out_stimulus_mean(idx, y_col, stim_col)
    y_dev = y - train_stim_mean

    ref = read_csv_optional(REFERENCE_05AJB)
    threshold = float(np.nanquantile(np.abs(y_dev), 0.75))
    fixed_reference = {}
    if not ref.empty:
        r = ref[ref.get("target", pd.Series([""] * len(ref))).astype(str).str.lower().eq("arousal")]
        if len(r):
            rr = r.iloc[0].to_dict()
            fixed_reference = rr
            if pd.notna(rr.get("abs_residual_threshold", np.nan)):
                threshold = float(rr.get("abs_residual_threshold"))

    high_mask = np.abs(y_dev) >= threshold
    print(f"[INFO] arousal high-disagreement threshold={threshold:.6f} high_n={int(high_mask.sum())}")

    print("[INFO] building EEG summary features...")
    x_feat, feat_names = build_eeg_summary_features(np.asarray(eeg), sample_rate=128.0)
    print(f"[INFO] summary_feature_shape={x_feat.shape}")

    subjects = idx[subj_col].to_numpy()
    stimuli = idx[stim_col].to_numpy()

    # Split controls. These are intentionally simple Ridge probes, not final models.
    split_rows = []
    rng = np.random.default_rng(11)
    kf = KFold(n_splits=5, shuffle=True, random_state=11)
    split_rows.append(split_eval("random_trial_kfold_subjects_overlap", kf.split(x_feat), x_feat, y_dev, high_mask, alpha=100.0))

    split_rows.append(split_eval(
        "within_subject_trial_kfold_subjects_overlap",
        make_within_subject_folds(subjects, n_splits=5, seed=11),
        x_feat,
        y_dev,
        high_mask,
        alpha=100.0,
    ))

    logo_subj = LeaveOneGroupOut()
    split_rows.append(split_eval(
        "loso_leave_one_subject_out",
        logo_subj.split(x_feat, y_dev, groups=subjects),
        x_feat,
        y_dev,
        high_mask,
        alpha=100.0,
    ))

    logo_stim = LeaveOneGroupOut()
    split_rows.append(split_eval(
        "leave_one_stimulus_out",
        logo_stim.split(x_feat, y_dev, groups=stimuli),
        x_feat,
        y_dev,
        high_mask,
        alpha=100.0,
    ))

    split_df = pd.DataFrame(split_rows)

    deep_decision = read_csv_optional(PREVIOUS_DEEP_DECISION)
    deep_subject_stats = read_csv_optional(PREVIOUS_DEEP_SUBJECT)

    var_df = variance_decomposition(idx, y_col, y_dev, subj_col, stim_col)
    shift_df = domain_shift_by_subject(x_feat, subjects, deep_subject_stats)

    # Diagnosis rules.
    random_high_lift = float(split_df.loc[split_df["split"].eq("random_trial_kfold_subjects_overlap"), "lift_vs_zero_high"].iloc[0])
    within_high_lift = float(split_df.loc[split_df["split"].eq("within_subject_trial_kfold_subjects_overlap"), "lift_vs_zero_high"].iloc[0])
    loso_high_lift = float(split_df.loc[split_df["split"].eq("loso_leave_one_subject_out"), "lift_vs_zero_high"].iloc[0])

    deep_row = {}
    if not deep_decision.empty:
        deep_row = deep_decision.iloc[0].to_dict()
    deep_lift = float(deep_row.get("deep_lift_vs_zero_residual_rmse_high", np.nan)) if deep_row else np.nan
    fixed_lift = float(deep_row.get("fixed_reference_lift_vs_zero", fixed_reference.get("pooled_lift_vs_zero_residual_rmse", np.nan))) if (deep_row or fixed_reference) else np.nan

    subject_component = var_df.loc[var_df["quantity"].eq("deviation_subject_mean_component"), "proportion_of_total"]
    subject_component_value = float(subject_component.iloc[0]) if len(subject_component) else np.nan

    if random_high_lift > 0.02 and loso_high_lift <= 0.02:
        split_diagnosis = "SUBJECT_DOMAIN_SHIFT_OR_SUBJECT_SPECIFIC_MAPPING_BLOCKS_LOSO"
    elif random_high_lift <= 0.02 and within_high_lift <= 0.02 and loso_high_lift <= 0.02:
        split_diagnosis = "CURRENT_EEG_SUMMARY_FEATURES_DO_NOT_PREDICT_RESIDUAL_EVEN_WITH_SUBJECT_OVERLAP"
    else:
        split_diagnosis = "MIXED_SPLIT_CONTROL_RESULT_REQUIRES_REVIEW"

    if np.isfinite(deep_lift) and deep_lift <= 0.02 and np.isfinite(fixed_lift) and fixed_lift > 0.02:
        deep_diagnosis = "PREVIOUS_DEEP_MODEL_UNDERPERFORMS_SIMPLE_FIXED_BANDPOWER_SIGNAL"
    elif np.isfinite(deep_lift) and deep_lift <= 0.02:
        deep_diagnosis = "PREVIOUS_DEEP_MODEL_NO_GO"
    else:
        deep_diagnosis = "PREVIOUS_DEEP_MODEL_NOT_DECISIVE"

    if np.isfinite(subject_component_value) and subject_component_value > 0.20:
        residual_diagnosis = "SUBJECT_STYLE_EXPLAINS_NONTRIVIAL_RESIDUAL_VARIANCE_CALIBRATION_IS_STRUCTURALLY_NEEDED"
    else:
        residual_diagnosis = "RESIDUAL_VARIANCE_NOT_DOMINATED_BY_SIMPLE_SUBJECT_MEAN_COMPONENT"

    decision_rows = [
        {
            "diagnostic_item": "previous_deep_model_result",
            "finding": deep_diagnosis,
            "key_number": deep_lift,
            "interpretation": "The old deep EEGSegmentEncoder residual probe did not beat zero residual or the fixed EEG-bandpower high-disagreement reference.",
            "action": "Do not continue blind architecture search on the same LOSO residual target.",
        },
        {
            "diagnostic_item": "random_vs_loso_split_control",
            "finding": split_diagnosis,
            "key_number": loso_high_lift,
            "interpretation": "This checks whether residual predictability appears only when subjects overlap between train and test.",
            "action": "If subject-overlap works but LOSO fails, prioritize domain adaptation/subject normalization; if both fail, prioritize representation/target audit.",
        },
        {
            "diagnostic_item": "residual_variance_structure",
            "finding": residual_diagnosis,
            "key_number": subject_component_value,
            "interpretation": "A large subject-mean residual component means physiology has to solve a subject-style/calibration problem, not just decode stimulus emotion.",
            "action": "Keep B2 personalization as required baseline; use physiology only if it adds beyond subject calibration.",
        },
        {
            "diagnostic_item": "confirmed_positive_pocket",
            "finding": "AROUSAL_HIGH_DISAGREEMENT_FIXED_EEG_BANDPOWER_SIGNAL_IS_REAL_BUT_WEAK",
            "key_number": fixed_lift,
            "interpretation": "The positive pocket exists, but it has not bridged into global personalization or failure rescue.",
            "action": "Use it as a diagnostic/gating signal, not yet as an additive correction.",
        },
    ]

    decision_df = pd.DataFrame(decision_rows)

    next_steps = pd.DataFrame([
        {
            "priority": 1,
            "step": "06a1y",
            "title": "Split-control learning probe",
            "purpose": "Train the same lightweight model under random/within-subject/LOSO splits to isolate whether the failure is subject shift or weak signal.",
            "success_condition": "Subject-overlap success plus LOSO failure proves generalization/domain shift; failure in all splits points to representation/target weakness.",
        },
        {
            "priority": 2,
            "step": "06a2",
            "title": "Subject-adaptive residual representation",
            "purpose": "If split controls show subject shift, add explicit subject adaptation rather than larger generic CNNs.",
            "success_condition": "Improves beyond B2 locked or matches B2 with fewer calibration samples under paired subject gates.",
        },
        {
            "priority": 3,
            "step": "06a3",
            "title": "Residual identifiability and label-noise bound",
            "purpose": "Quantify whether single-trial subjective residuals have enough repeatable structure to support learning.",
            "success_condition": "A clear upper bound explains whether more model capacity can realistically help.",
        },
    ])

    # Save outputs.
    decision_df.to_csv(ROCA / f"{OUT_PREFIX}_decision_table.csv", index=False)
    split_df.to_csv(ROCA / f"{OUT_PREFIX}_split_control_metrics.csv", index=False)
    var_df.to_csv(ROCA / f"{OUT_PREFIX}_residual_variance_decomposition.csv", index=False)
    shift_df.to_csv(ROCA / f"{OUT_PREFIX}_eeg_domain_shift_by_subject.csv", index=False)
    next_steps.to_csv(ROCA / f"{OUT_PREFIX}_next_steps.csv", index=False)
    if not deep_decision.empty:
        deep_decision.to_csv(ROCA / f"{OUT_PREFIX}_previous_deep_summary.csv", index=False)

    report = {
        "title": "I-DARE LOSO generalization failure autopsy",
        "inputs": {
            "eeg_cache": str(EEG_CACHE.relative_to(ROOT)),
            "eeg_shape": list(map(int, eeg.shape)),
            "index": str(EEG_INDEX.relative_to(ROOT)),
            "previous_deep_decision": str(PREVIOUS_DEEP_DECISION.relative_to(ROOT)),
            "reference_05ajb": str(REFERENCE_05AJB.relative_to(ROOT)),
            "target": "arousal",
            "high_disagreement_threshold": threshold,
            "high_disagreement_n": int(high_mask.sum()),
        },
        "decision_table": decision_df.to_dict(orient="records"),
        "split_control_metrics": split_df.to_dict(orient="records"),
        "residual_variance_decomposition": var_df.to_dict(orient="records"),
        "next_steps": next_steps.to_dict(orient="records"),
    }
    with open(ROCA / f"{OUT_PREFIX}.json", "w", encoding="utf-8") as f:
        json.dump(to_jsonable(report), f, indent=2, ensure_ascii=False)

    lines = []
    lines.append("# I-DARE LOSO generalization failure autopsy\n")
    lines.append("## Purpose\n")
    lines.append("This diagnostic tries to localize why the previous deep residual model failed under LOSO: weak residual signal, subject/domain shift, residual variance structure, or model/training instability.\n")
    lines.append("## Decision table\n")
    lines.append(md_table(decision_df))
    lines.append("\n## Split-control metrics\n")
    lines.append(md_table(split_df))
    lines.append("\n## Residual variance decomposition\n")
    lines.append(md_table(var_df))
    lines.append("\n## Next steps\n")
    lines.append(md_table(next_steps))

    with open(ROCA / f"{OUT_PREFIX}.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("ROCA step 06a1x completed.")
    for suffix in [
        ".md",
        ".json",
        "_decision_table.csv",
        "_split_control_metrics.csv",
        "_residual_variance_decomposition.csv",
        "_eeg_domain_shift_by_subject.csv",
        "_next_steps.csv",
    ]:
        print(f"wrote: {ROCA / (OUT_PREFIX + suffix)}")

    print("\nDecision table:")
    print(decision_df.to_string(index=False))

    print("\nSplit-control metrics:")
    keep_cols = [
        "split",
        "folds",
        "n_high",
        "zero_rmse_high",
        "model_rmse_high",
        "lift_vs_zero_high",
        "pearson_high",
        "sign_acc_high",
    ]
    print(split_df[keep_cols].to_string(index=False))

    print("\nNext steps:")
    print(next_steps.to_string(index=False))


if __name__ == "__main__":
    main()
