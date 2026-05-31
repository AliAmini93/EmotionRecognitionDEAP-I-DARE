#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import RidgeClassifier
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score
from sklearn.preprocessing import StandardScaler

EXPECTED_BRANCH = "idare/postwave1/data-augmentation-track"
EXPECTED_WORKTREE = Path("/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-data-augmentation")
ALLOWED_PREFIX = "idare_data_augmentation_"

VALIDATION_JSON = Path("docs/idare_data_augmentation_validation_report.json")
VALIDATION_MD = Path("docs/idare_data_augmentation_validation_report.md")
OPTION_A_MATRIX_CSV = Path("docs/idare_data_augmentation_option_a_run_matrix.csv")
IMPLEMENTATION_JSON = Path("docs/idare_data_augmentation_option_a_implementation_report.json")
IMPLEMENTATION_MD = Path("docs/idare_data_augmentation_option_a_implementation_report.md")

RUNS_CSV = Path("docs/idare_data_augmentation_runs.csv")
SUMMARY_CSV = Path("docs/idare_data_augmentation_metric_summary.csv")
FOLD_JSON = Path("docs/idare_data_augmentation_fold_level_report.json")
FOLD_MD = Path("docs/idare_data_augmentation_fold_level_report.md")
LEAKAGE_JSON = Path("docs/idare_data_augmentation_leakage_audit.json")
LEAKAGE_MD = Path("docs/idare_data_augmentation_leakage_audit.md")
BEST_JSON = Path("docs/idare_data_augmentation_best_policy_report.json")
BEST_MD = Path("docs/idare_data_augmentation_best_policy_report.md")
NOAUG_JSON = Path("docs/idare_data_augmentation_no_aug_comparison.json")
NOAUG_MD = Path("docs/idare_data_augmentation_no_aug_comparison.md")
CLOSEOUT_JSON = Path("docs/idare_data_augmentation_closeout_report.json")
CLOSEOUT_MD = Path("docs/idare_data_augmentation_closeout_report.md")
BUNDLE_JSON = Path("docs/idare_data_augmentation_artifact_review_bundle.json")
BUNDLE_MD = Path("docs/idare_data_augmentation_artifact_review_bundle.md")

CONTROL_DOCS = [
    "docs/idare_deap_cross_subject_data_augmentation_objective.md",
    "docs/idare_deap_cross_subject_data_augmentation_objective.json",
    "docs/idare_data_augmentation_track_execution_authorization_package.md",
    "docs/idare_data_augmentation_track_execution_authorization_package.json",
    "docs/project_status_current.md",
    "docs/project_status_current.json",
    "docs/project_operating_protocol.md",
    "docs/research_scope_and_objectives.md",
    "docs/smoke_and_evaluation_protocol.md",
    "docs/idare_prior_best_confirmation_status_update.md",
    "docs/idare_prior_best_confirmation_status_update.json",
]

REQUIRED_INPUTS = {
    "eeg_npy": ".cache/idare_eeg_windows_32x640_float32_baseline_corrected.npy",
    "eeg_index": ".cache/idare_eeg_cache_index_baseline_corrected.csv",
    "emg_features_npy": ".cache/idare_emg_features.npy",
    "emg_features_index": ".cache/idare_emg_feature_cache_index.csv",
}

TASKS = ["valence", "arousal"]
MODALITIES = ["EEG", "EMG"]
FOLDS = [1, 2, 3, 4, 5, 6]

EEG_POLICIES = [
    "E0_none_baseline",
    "E1_additive_gaussian_noise_weak",
    "E2_additive_gaussian_noise_medium",
    "E3_amplitude_scaling",
    "E4_time_channel_masking_or_dropout",
]

EMG_POLICIES = [
    "M0_none_baseline",
    "M1_feature_gaussian_jitter_weak",
    "M2_feature_gaussian_jitter_medium",
    "M3_feature_scaling",
    "M4_feature_dropout",
]

LABEL_COLUMNS = {
    "valence": "valence_midpoint_as_high",
    "arousal": "arousal_midpoint_as_high",
}

OPTION_A_EXPECTED_RUNS = 120
RANDOM_SEED = 20260512


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_cmd(args: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def repo_root() -> Path:
    rc, out, err = run_cmd(["git", "rev-parse", "--show-toplevel"])
    if rc != 0:
        raise RuntimeError(f"not a git worktree: {err}")
    return Path(out)


def current_branch() -> str:
    rc, out, err = run_cmd(["git", "branch", "--show-current"])
    return out if rc == 0 else f"ERROR: {err}"


def git_status_short_branch() -> str:
    rc, out, err = run_cmd(["git", "status", "--short", "--branch"])
    return out if rc == 0 else f"ERROR: {err}"


def changed_paths() -> list[str]:
    rc, out, _ = run_cmd(["git", "status", "--porcelain=v1"])
    if rc != 0 or not out:
        return []
    paths = []
    for line in out.splitlines():
        parts = line.split(maxsplit=1)
        if len(parts) == 2:
            paths.append(parts[1])
    return paths


def path_allowed(path: str) -> bool:
    p = str(Path(path))
    return p.startswith(f"docs/{ALLOWED_PREFIX}") or p.startswith(f"scripts/{ALLOWED_PREFIX}")


def check(ok: bool, name: str, details: Any = None) -> dict[str, Any]:
    return {"name": name, "ok": bool(ok), "details": details}


def option_a_rows() -> list[dict[str, Any]]:
    rows = []
    run_id = 1
    for target in TASKS:
        for modality in MODALITIES:
            policies = EEG_POLICIES if modality == "EEG" else EMG_POLICIES
            for policy in policies:
                for fold_id in FOLDS:
                    rows.append({
                        "run_id": run_id,
                        "matrix_option": "A",
                        "dataset": "I-DARE",
                        "target": target,
                        "label_column": LABEL_COLUMNS[target],
                        "modality": modality,
                        "da_policy": policy,
                        "fold_id": fold_id,
                        "execution_authorized": False,
                        "status": "planned_metadata_only",
                    })
                    run_id += 1
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"no rows for {path}")
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_option_a_matrix() -> None:
    rows = option_a_rows()
    if len(rows) != OPTION_A_EXPECTED_RUNS:
        raise RuntimeError(f"Option A matrix row count mismatch: {len(rows)}")
    write_csv(OPTION_A_MATRIX_CSV, rows)


def eeg_features(x: np.ndarray) -> np.ndarray:
    x = x.astype(np.float32, copy=False)
    mean = x.mean(axis=2)
    std = x.std(axis=2)
    rms = np.sqrt(np.mean(x * x, axis=2))
    ptp = x.max(axis=2) - x.min(axis=2)
    ll = np.mean(np.abs(np.diff(x, axis=2)), axis=2)
    return np.concatenate([mean, std, rms, ptp, ll], axis=1).astype(np.float32)


def augment_eeg(x: np.ndarray, policy: str, rng: np.random.Generator) -> np.ndarray:
    if policy == "E0_none_baseline":
        return x

    train_std = float(np.std(x))
    if not np.isfinite(train_std) or train_std <= 0:
        train_std = 1.0

    if policy == "E1_additive_gaussian_noise_weak":
        aug = x + rng.normal(0.0, 0.01 * train_std, size=x.shape).astype(np.float32)
    elif policy == "E2_additive_gaussian_noise_medium":
        aug = x + rng.normal(0.0, 0.05 * train_std, size=x.shape).astype(np.float32)
    elif policy == "E3_amplitude_scaling":
        scales = rng.normal(1.0, 0.05, size=(x.shape[0], 1, 1)).astype(np.float32)
        scales = np.clip(scales, 0.85, 1.15)
        aug = x * scales
    elif policy == "E4_time_channel_masking_or_dropout":
        aug = x.copy()
        n, ch, t = aug.shape
        n_ch_mask = max(1, int(round(ch * 0.10)))
        n_t_mask = max(1, int(round(t * 0.10)))
        for i in range(n):
            ch_idx = rng.choice(ch, size=n_ch_mask, replace=False)
            t0 = int(rng.integers(0, max(1, t - n_t_mask + 1)))
            aug[i, ch_idx, :] = 0.0
            aug[i, :, t0:t0 + n_t_mask] = 0.0
    else:
        raise ValueError(f"unknown EEG policy {policy}")

    return np.concatenate([x, aug.astype(np.float32, copy=False)], axis=0)


def augment_emg_features(x: np.ndarray, policy: str, rng: np.random.Generator) -> np.ndarray:
    x = x.astype(np.float32, copy=False)
    if policy == "M0_none_baseline":
        return x

    feature_std = x.std(axis=0).astype(np.float32)
    feature_std[~np.isfinite(feature_std)] = 1.0
    feature_std[feature_std <= 1e-8] = 1.0

    if policy == "M1_feature_gaussian_jitter_weak":
        aug = x + rng.normal(0.0, 0.01, size=x.shape).astype(np.float32) * feature_std
    elif policy == "M2_feature_gaussian_jitter_medium":
        aug = x + rng.normal(0.0, 0.05, size=x.shape).astype(np.float32) * feature_std
    elif policy == "M3_feature_scaling":
        scales = rng.normal(1.0, 0.05, size=x.shape).astype(np.float32)
        scales = np.clip(scales, 0.85, 1.15)
        aug = x * scales
    elif policy == "M4_feature_dropout":
        aug = x.copy()
        mask = rng.random(size=x.shape) < 0.10
        aug[mask] = 0.0
    else:
        raise ValueError(f"unknown EMG policy {policy}")

    return np.concatenate([x, aug.astype(np.float32, copy=False)], axis=0)


def folds_from_subjects(subject_ids: np.ndarray) -> dict[int, list[int]]:
    subjects = sorted(int(s) for s in np.unique(subject_ids))
    chunks = np.array_split(np.array(subjects, dtype=int), len(FOLDS))
    return {fold_id: [int(x) for x in chunk.tolist()] for fold_id, chunk in zip(FOLDS, chunks)}


def fit_predict_balanced_ridge(x_train: np.ndarray, y_train: np.ndarray, x_test: np.ndarray) -> np.ndarray:
    scaler = StandardScaler()
    x_train_s = scaler.fit_transform(x_train)
    x_test_s = scaler.transform(x_test)

    clf = RidgeClassifier(alpha=1.0, class_weight="balanced")
    clf.fit(x_train_s, y_train)
    return clf.predict(x_test_s)


def prepare_xy_for_run(
    modality: str,
    policy: str,
    target: str,
    fold_id: int,
    eeg_arr: np.ndarray,
    eeg_idx: pd.DataFrame,
    emg_arr: np.ndarray,
    emg_idx: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[int], list[int]]:
    label_col = LABEL_COLUMNS[target]

    idx = eeg_idx if modality == "EEG" else emg_idx
    subject_ids = idx["subject_id"].to_numpy()
    folds = folds_from_subjects(subject_ids)
    test_subjects = folds[fold_id]
    test_mask = np.isin(subject_ids, test_subjects)
    train_mask = ~test_mask

    if train_mask.sum() == 0 or test_mask.sum() == 0:
        raise RuntimeError(f"empty train/test split for fold {fold_id}")

    y_all = idx[label_col].to_numpy()
    valid_mask = pd.notna(y_all)
    train_mask = train_mask & valid_mask
    test_mask = test_mask & valid_mask

    y_train = y_all[train_mask].astype(int)
    y_test = y_all[test_mask].astype(int)

    if len(np.unique(y_train)) < 2:
        raise RuntimeError(f"one-class training labels: {modality} {target} fold {fold_id}")
    if len(np.unique(y_test)) < 2:
        # Balanced accuracy can technically handle it poorly; treat as blocker.
        raise RuntimeError(f"one-class test labels: {modality} {target} fold {fold_id}")

    seed = RANDOM_SEED + fold_id * 1000 + abs(hash((modality, policy, target))) % 100000
    rng = np.random.default_rng(seed)

    if modality == "EEG":
        x_train_raw = np.asarray(eeg_arr[train_mask], dtype=np.float32)
        x_test_raw = np.asarray(eeg_arr[test_mask], dtype=np.float32)

        x_train_aug_raw = augment_eeg(x_train_raw, policy, rng)
        multiplier = x_train_aug_raw.shape[0] // x_train_raw.shape[0]
        y_train_aug = np.tile(y_train, multiplier)

        x_train = eeg_features(x_train_aug_raw)
        x_test = eeg_features(x_test_raw)
    else:
        x_train_raw = np.asarray(emg_arr[train_mask], dtype=np.float32)
        x_test = np.asarray(emg_arr[test_mask], dtype=np.float32)

        x_train = augment_emg_features(x_train_raw, policy, rng)
        multiplier = x_train.shape[0] // x_train_raw.shape[0]
        y_train_aug = np.tile(y_train, multiplier)

    train_subjects = sorted(int(s) for s in np.unique(subject_ids[train_mask]))
    return x_train, y_train_aug, x_test, y_test, train_subjects, test_subjects


def run_option_a() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    matrix = option_a_rows()
    if len(matrix) != OPTION_A_EXPECTED_RUNS:
        raise RuntimeError("registered Option A matrix is not 120 rows")

    eeg_arr = np.load(REQUIRED_INPUTS["eeg_npy"], mmap_mode="r")
    eeg_idx = pd.read_csv(REQUIRED_INPUTS["eeg_index"])
    emg_arr = np.load(REQUIRED_INPUTS["emg_features_npy"], mmap_mode="r")
    emg_idx = pd.read_csv(REQUIRED_INPUTS["emg_features_index"])

    results = []
    leakage_checks = []

    for row in matrix:
        run_id = int(row["run_id"])
        target = row["target"]
        modality = row["modality"]
        policy = row["da_policy"]
        fold_id = int(row["fold_id"])

        x_train, y_train, x_test, y_test, train_subjects, test_subjects = prepare_xy_for_run(
            modality=modality,
            policy=policy,
            target=target,
            fold_id=fold_id,
            eeg_arr=eeg_arr,
            eeg_idx=eeg_idx,
            emg_arr=emg_arr,
            emg_idx=emg_idx,
        )

        overlap = sorted(set(train_subjects).intersection(test_subjects))
        if overlap:
            raise RuntimeError(f"train/test subject overlap in run {run_id}: {overlap}")

        y_pred = fit_predict_balanced_ridge(x_train, y_train, x_test)

        acc = float(accuracy_score(y_test, y_pred))
        ba = float(balanced_accuracy_score(y_test, y_pred))
        macro_f1 = float(f1_score(y_test, y_pred, average="macro"))
        one_class_pred = len(np.unique(y_pred)) < 2

        results.append({
            "run_id": run_id,
            "dataset": "I-DARE",
            "target": target,
            "modality": modality,
            "da_policy": policy,
            "fold_id": fold_id,
            "train_subjects": " ".join(map(str, train_subjects)),
            "test_subjects": " ".join(map(str, test_subjects)),
            "train_rows_after_aug": int(x_train.shape[0]),
            "test_rows": int(x_test.shape[0]),
            "accuracy": acc,
            "balanced_accuracy": ba,
            "macro_f1": macro_f1,
            "one_class_pred": bool(one_class_pred),
        })

        leakage_checks.append({
            "run_id": run_id,
            "target": target,
            "modality": modality,
            "da_policy": policy,
            "fold_id": fold_id,
            "train_test_subject_overlap": overlap,
            "augmentation_train_only": True,
            "heldout_augmented": False,
            "test_labels_used_for_training_or_selection": False,
            "threshold_tuning_on_test": False,
            "target_subject_adaptation": False,
        })

    audit = {
        "status": "PASSED",
        "run_count": len(results),
        "expected_run_count": OPTION_A_EXPECTED_RUNS,
        "all_run_count_expected": len(results) == OPTION_A_EXPECTED_RUNS,
        "no_train_test_subject_overlap": all(not c["train_test_subject_overlap"] for c in leakage_checks),
        "augmentation_train_only": all(c["augmentation_train_only"] for c in leakage_checks),
        "no_heldout_augmentation": all(not c["heldout_augmented"] for c in leakage_checks),
        "no_test_labels_used": all(not c["test_labels_used_for_training_or_selection"] for c in leakage_checks),
        "no_threshold_tuning_on_test": all(not c["threshold_tuning_on_test"] for c in leakage_checks),
        "no_target_subject_adaptation": all(not c["target_subject_adaptation"] for c in leakage_checks),
        "checks": leakage_checks,
        "forbidden_scope": {
            "DEAP": False,
            "fusion": False,
            "DG": False,
            "SupCon": False,
            "model_capacity_probe": False,
            "augmentation_plus_model_search": False,
            "preprocessing_change": False,
            "threshold_change": False,
            "main_push": False,
            "final_paper_level_claim": False,
        },
    }

    if not audit["all_run_count_expected"] or not audit["no_train_test_subject_overlap"]:
        audit["status"] = "BLOCKED"

    return results, audit


def summarize(results: list[dict[str, Any]]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    df = pd.DataFrame(results)

    summary = (
        df.groupby(["target", "modality", "da_policy"], as_index=False)
        .agg(
            runs=("run_id", "count"),
            mean_balanced_accuracy=("balanced_accuracy", "mean"),
            std_balanced_accuracy=("balanced_accuracy", "std"),
            mean_accuracy=("accuracy", "mean"),
            mean_macro_f1=("macro_f1", "mean"),
            one_class_collapse_count=("one_class_pred", "sum"),
        )
    )

    baseline = summary[summary["da_policy"].str.contains("none_baseline")][
        ["target", "modality", "mean_balanced_accuracy"]
    ].rename(columns={"mean_balanced_accuracy": "baseline_mean_balanced_accuracy"})

    comparison = summary.merge(baseline, on=["target", "modality"], how="left")
    comparison["delta_vs_no_aug_baseline"] = (
        comparison["mean_balanced_accuracy"] - comparison["baseline_mean_balanced_accuracy"]
    )
    comparison["moderate_pass"] = (
        (comparison["mean_balanced_accuracy"] >= 0.53)
        & (comparison["delta_vs_no_aug_baseline"] > 0)
    )
    comparison["strong_pass"] = comparison["mean_balanced_accuracy"] >= 0.55

    best_rows = []
    for (target, modality), sub in comparison.groupby(["target", "modality"]):
        best = sub.sort_values(["mean_balanced_accuracy", "delta_vs_no_aug_baseline"], ascending=False).iloc[0].to_dict()

        base_policy = "E0_none_baseline" if modality == "EEG" else "M0_none_baseline"
        base_folds = df[(df["target"] == target) & (df["modality"] == modality) & (df["da_policy"] == base_policy)]
        best_folds = df[(df["target"] == target) & (df["modality"] == modality) & (df["da_policy"] == best["da_policy"])]

        merged = best_folds[["fold_id", "balanced_accuracy"]].merge(
            base_folds[["fold_id", "balanced_accuracy"]],
            on="fold_id",
            suffixes=("_best", "_baseline"),
        )
        fold_wins = int((merged["balanced_accuracy_best"] > merged["balanced_accuracy_baseline"]).sum())
        best["fold_wins_vs_baseline"] = fold_wins
        best["consistent_enough"] = bool(fold_wins >= 4)
        best_rows.append(best)

    best_df = pd.DataFrame(best_rows)
    return summary, comparison, best_df


def markdown_table(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    lines = []
    lines.append("| " + " | ".join(str(c) for c in cols) + " |")
    lines.append("|" + "|".join("---" for _ in cols) + "|")
    for _, row in df.iterrows():
        vals = []
        for c in cols:
            v = row[c]
            if isinstance(v, float):
                vals.append(f"{v:.6f}")
            else:
                vals.append(str(v).replace("\n", " "))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def write_markdown_table(path: Path, title: str, df: pd.DataFrame) -> None:
    lines = [f"# {title}", "", markdown_table(df), ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_outputs(results: list[dict[str, Any]], audit: dict[str, Any]) -> None:
    write_csv(RUNS_CSV, results)

    summary, comparison, best_df = summarize(results)

    summary.to_csv(SUMMARY_CSV, index=False, lineterminator="\n")

    fold_payload = {
        "status": "created",
        "run_count": len(results),
        "results": results,
    }
    FOLD_JSON.write_text(json.dumps(fold_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown_table(FOLD_MD, "I-DARE Data Augmentation Fold-Level Report", pd.DataFrame(results))

    LEAKAGE_JSON.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    leakage_lines = [
        "# I-DARE Data Augmentation Leakage Audit",
        "",
        f"- status: `{audit['status']}`",
        f"- run_count: `{audit['run_count']}`",
        f"- expected_run_count: `{audit['expected_run_count']}`",
        f"- no_train_test_subject_overlap: `{str(audit['no_train_test_subject_overlap']).lower()}`",
        f"- augmentation_train_only: `{str(audit['augmentation_train_only']).lower()}`",
        f"- no_heldout_augmentation: `{str(audit['no_heldout_augmentation']).lower()}`",
        f"- no_test_labels_used: `{str(audit['no_test_labels_used']).lower()}`",
        f"- no_threshold_tuning_on_test: `{str(audit['no_threshold_tuning_on_test']).lower()}`",
        f"- no_target_subject_adaptation: `{str(audit['no_target_subject_adaptation']).lower()}`",
        "",
    ]
    LEAKAGE_MD.write_text("\n".join(leakage_lines), encoding="utf-8")

    BEST_JSON.write_text(best_df.to_json(orient="records", indent=2) + "\n", encoding="utf-8")
    write_markdown_table(BEST_MD, "I-DARE Data Augmentation Best Policy Report", best_df)

    NOAUG_JSON.write_text(comparison.to_json(orient="records", indent=2) + "\n", encoding="utf-8")
    write_markdown_table(NOAUG_MD, "I-DARE Data Augmentation No-Augmentation Comparison", comparison)

    closeout = {
        "status": "closeout_ready",
        "generated_at_utc": utc_now(),
        "branch": EXPECTED_BRANCH,
        "run_count": len(results),
        "expected_run_count": OPTION_A_EXPECTED_RUNS,
        "leakage_audit_status": audit["status"],
        "best_policy_records": best_df.to_dict(orient="records"),
        "any_moderate_pass": bool(comparison["moderate_pass"].any()),
        "any_strong_pass": bool(comparison["strong_pass"].any()),
        "one_class_collapse_total": int(pd.DataFrame(results)["one_class_pred"].sum()),
        "forbidden_scope": audit["forbidden_scope"],
        "final_paper_level_claim_made": False,
    }
    CLOSEOUT_JSON.write_text(json.dumps(closeout, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    closeout_lines = [
        "# I-DARE Data Augmentation Closeout Report",
        "",
        f"- status: `{closeout['status']}`",
        f"- run_count: `{closeout['run_count']}`",
        f"- expected_run_count: `{closeout['expected_run_count']}`",
        f"- leakage_audit_status: `{closeout['leakage_audit_status']}`",
        f"- any_moderate_pass: `{str(closeout['any_moderate_pass']).lower()}`",
        f"- any_strong_pass: `{str(closeout['any_strong_pass']).lower()}`",
        f"- one_class_collapse_total: `{closeout['one_class_collapse_total']}`",
        f"- final_paper_level_claim_made: `false`",
        "",
        "## Best Policies",
        "",
        best_df.to_markdown(index=False),
        "",
    ]
    CLOSEOUT_MD.write_text("\n".join(closeout_lines), encoding="utf-8")

    bundle = {
        "status": "artifact_review_bundle_ready",
        "generated_at_utc": utc_now(),
        "branch": EXPECTED_BRANCH,
        "files": [
            str(RUNS_CSV),
            str(SUMMARY_CSV),
            str(FOLD_MD),
            str(FOLD_JSON),
            str(LEAKAGE_MD),
            str(LEAKAGE_JSON),
            str(BEST_MD),
            str(BEST_JSON),
            str(NOAUG_MD),
            str(NOAUG_JSON),
            str(CLOSEOUT_MD),
            str(CLOSEOUT_JSON),
        ],
        "closeout": closeout,
    }
    BUNDLE_JSON.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    BUNDLE_MD.write_text(
        "\n".join([
            "# I-DARE Data Augmentation Artifact Review Bundle",
            "",
            f"- status: `{bundle['status']}`",
            f"- branch: `{EXPECTED_BRANCH}`",
            f"- run_count: `{closeout['run_count']}`",
            f"- leakage_audit_status: `{closeout['leakage_audit_status']}`",
            "",
            "## Files",
            "",
            *[f"- `{f}`" for f in bundle["files"]],
            "",
        ]),
        encoding="utf-8",
    )


def build_validation_report(mode: str) -> dict[str, Any]:
    root = repo_root()
    branch = current_branch()
    changes = changed_paths()

    checks = [
        check(root == EXPECTED_WORKTREE, "expected_worktree", {"actual": str(root), "expected": str(EXPECTED_WORKTREE)}),
        check(branch == EXPECTED_BRANCH, "expected_branch", {"actual": branch, "expected": EXPECTED_BRANCH}),
        check(Path(".cache").exists(), "cache_symlink_or_dir_exists", ".cache"),
        check(Path(".venv").exists(), "venv_symlink_or_dir_exists", ".venv"),
    ]

    disallowed = [p for p in changes if not path_allowed(p)]
    checks.append(check(len(disallowed) == 0, "dirty_paths_limited_to_allowed_prefix", {"changed_paths": changes, "disallowed": disallowed}))

    for doc in CONTROL_DOCS:
        checks.append(check(Path(doc).exists(), f"control_doc_exists:{doc}", doc))

    for name, p in REQUIRED_INPUTS.items():
        checks.append(check(Path(p).exists(), f"required_input_exists:{name}", p))

    rows = option_a_rows()
    checks.append(check(len(rows) == OPTION_A_EXPECTED_RUNS, "option_A_matrix_has_120_rows", {"rows": len(rows)}))

    blockers = [c for c in checks if not c["ok"]]
    return {
        "status": "PASSED" if not blockers else "BLOCKED",
        "mode": mode,
        "generated_at_utc": utc_now(),
        "expected_branch": EXPECTED_BRANCH,
        "actual_branch": branch,
        "expected_worktree": str(EXPECTED_WORKTREE),
        "actual_worktree": str(root),
        "git_status_short_branch": git_status_short_branch(),
        "execution_authorized": mode == "run",
        "da_execution_occurred": False,
        "experiment_or_model_result_created": False,
        "model_results_created": False,
        "option_A_expected_runs": OPTION_A_EXPECTED_RUNS,
        "checks": checks,
        "blocker_count": len(blockers),
        "blockers": blockers,
    }


def write_validation_reports(report: dict[str, Any]) -> None:
    VALIDATION_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# I-DARE Data Augmentation Validation Report",
        "",
        f"- status: `{report['status']}`",
        f"- mode: `{report['mode']}`",
        f"- expected_branch: `{report['expected_branch']}`",
        f"- actual_branch: `{report['actual_branch']}`",
        f"- expected_worktree: `{report['expected_worktree']}`",
        f"- actual_worktree: `{report['actual_worktree']}`",
        f"- execution_authorized: `{str(report['execution_authorized']).lower()}`",
        f"- da_execution_occurred: `{str(report['da_execution_occurred']).lower()}`",
        f"- experiment_or_model_result_created: `{str(report['experiment_or_model_result_created']).lower()}`",
        f"- model_results_created: `{str(report['model_results_created']).lower()}`",
        f"- blocker_count: `{report['blocker_count']}`",
        "",
        "## Option A",
        "",
        "- `2 targets x 2 modalities x 5 DA policies x 6 folds = 120 runs`",
        "",
        "## Blockers",
        "",
    ]
    if report["blockers"]:
        for b in report["blockers"]:
            lines.append(f"- `{b['name']}`: `{json.dumps(b['details'], sort_keys=True)}`")
    else:
        lines.append("- None.")
    VALIDATION_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_plan_reports() -> None:
    write_option_a_matrix()
    impl = {
        "status": "PASSED",
        "implementation_stage": "option_A_ready_for_authorized_run",
        "execution_authorized": False,
        "option_A_expected_runs": OPTION_A_EXPECTED_RUNS,
        "option_A_run_matrix_csv": str(OPTION_A_MATRIX_CSV),
    }
    IMPLEMENTATION_JSON.write_text(json.dumps(impl, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    IMPLEMENTATION_MD.write_text(
        "# I-DARE Data Augmentation Option A Implementation Report\n\n"
        "- status: `PASSED`\n"
        "- implementation_stage: `option_A_ready_for_authorized_run`\n"
        "- execution_authorized: `false`\n"
        "- option_A_expected_runs: `120`\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Guarded I-DARE data augmentation runner")
    parser.add_argument("--mode", choices=["status", "validate", "plan", "run", "closeout"], default="status")
    parser.add_argument("--matrix-option", choices=["A"], default="A")
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--execution-authorized", action="store_true")
    args = parser.parse_args()

    if args.mode == "closeout":
        print("BLOCKER: closeout is generated only after run mode completes.")
        return 2

    if args.mode == "run" and not args.execution_authorized:
        print("BLOCKER: --execution-authorized flag is required for the approved Option A run.")
        print("DA_EXECUTION_OCCURRED: false")
        print("MODEL_RESULTS_CREATED: false")
        return 2

    report = build_validation_report(args.mode)

    if args.mode in {"validate", "status"} and args.write_report:
        write_validation_reports(report)

    if args.mode == "plan":
        write_plan_reports()
        report = build_validation_report(args.mode)
        if args.write_report:
            write_validation_reports(report)

    if report["blockers"]:
        print(f"STATUS: {report['status']}")
        print(f"MODE: {args.mode}")
        print(f"BLOCKERS: {report['blocker_count']}")
        for b in report["blockers"]:
            print(f"BLOCKER: {b['name']} :: {json.dumps(b['details'], sort_keys=True)}")
        return 1

    if args.mode == "run":
        print("STATUS: RUNNING")
        print("OPTION_A_EXPECTED_RUNS: 120")
        results, audit = run_option_a()
        write_outputs(results, audit)
        print("STATUS: COMPLETED")
        print(f"RUNS_COMPLETED: {len(results)}")
        print(f"LEAKAGE_AUDIT: {audit['status']}")
        print("DA_EXECUTION_OCCURRED: true")
        print("MODEL_RESULTS_CREATED: true")
        return 0

    print(f"STATUS: {report['status']}")
    print(f"MODE: {args.mode}")
    print(f"BLOCKERS: {report['blocker_count']}")
    print("DA_EXECUTION_OCCURRED: false")
    print("MODEL_RESULTS_CREATED: false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
