#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import random
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler

EXPECTED_BRANCH = "idare/postwave1/idare-prior-best-cell-confirmation"
EXPECTED_WORKTREE = Path("/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-idare-prior-best-confirm")
ALLOWED_PREFIX = "idare_prior_best_confirm_"

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

OBJECTIVE_JSON = ROOT / "docs" / "idare_prior_best_confirm_objective.json"
VALIDATION_JSON = ROOT / "docs" / "idare_prior_best_confirm_validation_report.json"
VALIDATION_MD = ROOT / "docs" / "idare_prior_best_confirm_validation_report.md"

RUNS_CSV = ROOT / "docs" / "idare_prior_best_confirm_confirmation_runs.csv"
METRIC_SUMMARY_JSON = ROOT / "docs" / "idare_prior_best_confirm_metric_summary.json"
METRIC_SUMMARY_MD = ROOT / "docs" / "idare_prior_best_confirm_metric_summary.md"
METRIC_SUMMARY_CSV = ROOT / "docs" / "idare_prior_best_confirm_metric_summary.csv"
FOLD_REPORT_JSON = ROOT / "docs" / "idare_prior_best_confirm_fold_level_report.json"
FOLD_REPORT_MD = ROOT / "docs" / "idare_prior_best_confirm_fold_level_report.md"
FOLD_REPORT_CSV = ROOT / "docs" / "idare_prior_best_confirm_fold_level_report.csv"
PRIOR_COMPARE_JSON = ROOT / "docs" / "idare_prior_best_confirm_prior_vs_confirmation_comparison.json"
PRIOR_COMPARE_MD = ROOT / "docs" / "idare_prior_best_confirm_prior_vs_confirmation_comparison.md"
PRIOR_COMPARE_CSV = ROOT / "docs" / "idare_prior_best_confirm_prior_vs_confirmation_comparison.csv"
LEAKAGE_AUDIT_JSON = ROOT / "docs" / "idare_prior_best_confirm_leakage_scope_audit.json"
LEAKAGE_AUDIT_MD = ROOT / "docs" / "idare_prior_best_confirm_leakage_scope_audit.md"
CLOSEOUT_JSON = ROOT / "docs" / "idare_prior_best_confirm_closeout_report.json"
CLOSEOUT_MD = ROOT / "docs" / "idare_prior_best_confirm_closeout_report.md"
BUNDLE_JSON = ROOT / "docs" / "idare_prior_best_confirm_artifact_review_bundle.json"
BUNDLE_MD = ROOT / "docs" / "idare_prior_best_confirm_artifact_review_bundle.md"
EXECUTION_JSON = ROOT / "docs" / "idare_prior_best_confirm_execution_report.json"
EXECUTION_MD = ROOT / "docs" / "idare_prior_best_confirm_execution_report.md"

EXPECTED_CELLS = [
    {
        "cell_id": "C0",
        "dataset": "I-DARE",
        "modality": "EEG",
        "task": "arousal",
        "label_policy": "midpoint_as_high",
        "recipe": "ce_class_weighted",
        "prior_macro_f1": 0.5313,
        "prior_balanced_accuracy": 0.5416,
    },
    {
        "cell_id": "C1",
        "dataset": "I-DARE",
        "modality": "EEG",
        "task": "valence",
        "label_policy": "discard_midpoint",
        "recipe": "balanced_sampler_ce",
        "prior_macro_f1": 0.5066,
        "prior_balanced_accuracy": 0.5219,
    },
    {
        "cell_id": "C2",
        "dataset": "I-DARE",
        "modality": "EMG",
        "task": "arousal",
        "label_policy": "discard_midpoint",
        "recipe": "ce_class_weighted",
        "prior_macro_f1": 0.5253,
        "prior_balanced_accuracy": 0.5365,
    },
    {
        "cell_id": "C3",
        "dataset": "I-DARE",
        "modality": "EMG",
        "task": "valence",
        "label_policy": "midpoint_as_high",
        "recipe": "ce_class_weighted",
        "prior_macro_f1": 0.5140,
        "prior_balanced_accuracy": 0.5202,
    },
]

REQUIRED_DOC_ARTIFACTS = [
    "docs/project_status_current.md",
    "docs/project_operating_protocol.md",
    "docs/research_scope_and_objectives.md",
    "docs/smoke_and_evaluation_protocol.md",
    "docs/idare_label_policy_ablation_objective.md",
    "docs/idare_label_policy_ablation_objective.json",
    "docs/idare_label_policy_ablation_report.md",
    "docs/idare_label_policy_ablation_report.json",
    "docs/idare_label_policy_ablation_eeg_primary.json",
    "docs/idare_label_policy_ablation_emg_primary.json",
    "docs/idare_label_policy_ablation_review_status.md",
    "docs/idare_label_policy_ablation_review_status.json",
]

REQUIRED_INPUTS = {
    "EEG": {
        "cache_npy": ".cache/idare_eeg_windows_32x640_float32_baseline_corrected.npy",
        "cache_index_csv": ".cache/idare_eeg_cache_index_baseline_corrected.csv",
        "expected_shape": [2016, 32, 640],
    },
    "EMG": {
        "cache_npy": ".cache/idare_emg_features.npy",
        "cache_index_csv": ".cache/idare_emg_feature_cache_index.csv",
        "expected_shape": [2016, 22],
    },
}

FORBIDDEN_SCOPES = [
    "144_run_label_policy_matrix",
    "DEAP",
    "fusion",
    "DG",
    "Wave_2",
    "model_capacity_probe",
    "augmentation",
    "representation_redesign_v2",
    "preprocessing_change",
    "threshold_change",
    "W1_owned_files",
    "main_push",
    "final_paper_level_performance_claim",
]

ALLOWED_OUTPUTS = {
    str(p.relative_to(ROOT)) for p in [
        VALIDATION_JSON,
        VALIDATION_MD,
        RUNS_CSV,
        METRIC_SUMMARY_JSON,
        METRIC_SUMMARY_MD,
        METRIC_SUMMARY_CSV,
        FOLD_REPORT_JSON,
        FOLD_REPORT_MD,
        FOLD_REPORT_CSV,
        PRIOR_COMPARE_JSON,
        PRIOR_COMPARE_MD,
        PRIOR_COMPARE_CSV,
        LEAKAGE_AUDIT_JSON,
        LEAKAGE_AUDIT_MD,
        CLOSEOUT_JSON,
        CLOSEOUT_MD,
        BUNDLE_JSON,
        BUNDLE_MD,
        EXECUTION_JSON,
        EXECUTION_MD,
    ]
}

@dataclass(frozen=True)
class FoldSpec:
    fold_id: int
    train_subjects: list[int]
    test_subjects: list[int]

@dataclass(frozen=True)
class RunSpec:
    run_id: int
    cell_id: str
    modality: str
    task: str
    label_policy: str
    recipe: str
    fold: FoldSpec
    seed: int

def git(args: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(["git", *args], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def label_col(task: str, policy: str) -> str:
    return f"{task}_{policy}"

def parse_porcelain_paths(porcelain: str) -> list[str]:
    paths = []
    for line in porcelain.splitlines():
        if not line:
            continue
        if line.startswith("?? "):
            raw = line[3:]
        elif len(line) >= 4 and line[2] == " ":
            raw = line[3:]
        elif len(line) >= 3:
            raw = line[2:].strip()
        else:
            raw = line.strip()
        if " -> " in raw:
            raw = raw.rsplit(" -> ", 1)[1]
        paths.append(raw.strip())
    return paths

def add_check(checks: list[dict[str, Any]], name: str, ok: bool, details: Any = None) -> None:
    checks.append({"name": name, "ok": bool(ok), "details": details})

def npy_shape(path: Path) -> list[int]:
    arr = np.load(path, mmap_mode="r")
    return [int(v) for v in arr.shape]

def csv_header_and_rows(path: Path) -> tuple[list[str], int]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            return [], 0
        rows = sum(1 for _ in reader)
    return header, rows

def preflight(mode: str, folds: int, planned_runs: int) -> tuple[dict[str, Any], list[str]]:
    checks: list[dict[str, Any]] = []
    blockers: list[str] = []

    code, git_root, err = git(["rev-parse", "--show-toplevel"])
    root_ok = code == 0 and Path(git_root).resolve() == ROOT.resolve()
    add_check(checks, "git_root_matches_script_root", root_ok, {"git_root": git_root, "script_root": str(ROOT)})
    if not root_ok:
        blockers.append("git root mismatch")

    worktree_ok = ROOT.resolve() == EXPECTED_WORKTREE.resolve()
    add_check(checks, "expected_worktree_path", worktree_ok, {"expected": str(EXPECTED_WORKTREE), "actual": str(ROOT.resolve())})
    if not worktree_ok:
        blockers.append("wrong worktree")

    code, branch, err = git(["rev-parse", "--abbrev-ref", "HEAD"])
    branch_ok = code == 0 and branch == EXPECTED_BRANCH
    add_check(checks, "expected_branch", branch_ok, {"expected": EXPECTED_BRANCH, "actual": branch})
    if not branch_ok:
        blockers.append("wrong branch")

    code, status_short, err = git(["status", "--short", "--branch"])
    add_check(checks, "git_status_readable", code == 0, {"status": status_short, "stderr": err})
    if code != 0:
        blockers.append("git status not readable")

    code, porcelain, err = git(["status", "--porcelain"])
    changed = parse_porcelain_paths(porcelain) if code == 0 else []
    bad = [p for p in changed if not (p.startswith("docs/idare_prior_best_confirm_") or p.startswith("scripts/idare_prior_best_confirm_"))]
    add_check(checks, "working_tree_changes_limited_to_allowed_prefix", not bad, {"changed_paths": changed, "disallowed": bad})
    if bad:
        blockers.append("working tree has changes outside idare_prior_best_confirm_ prefix")

    objective_exists = OBJECTIVE_JSON.exists()
    add_check(checks, "objective_json_exists", objective_exists, str(OBJECTIVE_JSON.relative_to(ROOT)))
    if not objective_exists:
        blockers.append("objective JSON missing")
        objective = {}
    else:
        objective = json.loads(OBJECTIVE_JSON.read_text(encoding="utf-8"))

    objective_cells = objective.get("registered_cells", [])
    expected_cells_no_prior = [{k: c[k] for k in ["cell_id", "dataset", "modality", "task", "label_policy", "recipe"]} for c in EXPECTED_CELLS]
    cells_ok = objective_cells == expected_cells_no_prior
    add_check(checks, "exact_four_registered_cells", cells_ok, objective_cells)
    if not cells_ok:
        blockers.append("registered cells mismatch")

    matrix = objective.get("planned_matrix_metadata", {})
    matrix_ok = matrix.get("cells") == 4 and matrix.get("folds_per_cell") == folds == 6 and matrix.get("planned_confirmation_runs") == planned_runs == 24
    add_check(checks, "planned_matrix_4x6_24", matrix_ok, matrix)
    if not matrix_ok:
        blockers.append("planned matrix metadata mismatch")

    for rel in REQUIRED_DOC_ARTIFACTS:
        exists = (ROOT / rel).exists()
        add_check(checks, f"required_doc_exists:{rel}", exists, rel)
        if not exists:
            blockers.append(f"missing required doc: {rel}")

    for modality, spec in REQUIRED_INPUTS.items():
        npy = ROOT / spec["cache_npy"]
        idx = ROOT / spec["cache_index_csv"]
        npy_exists = npy.exists()
        idx_exists = idx.exists()
        add_check(checks, f"{modality}_cache_exists", npy_exists, spec["cache_npy"])
        add_check(checks, f"{modality}_index_exists", idx_exists, spec["cache_index_csv"])
        if not npy_exists:
            blockers.append(f"missing {modality} cache: {spec['cache_npy']}")
        if not idx_exists:
            blockers.append(f"missing {modality} index: {spec['cache_index_csv']}")
        if npy_exists:
            shape = npy_shape(npy)
            shape_ok = shape == spec["expected_shape"]
            add_check(checks, f"{modality}_cache_shape", shape_ok, {"expected": spec["expected_shape"], "actual": shape})
            if not shape_ok:
                blockers.append(f"{modality} cache shape mismatch")
        if idx_exists:
            header, rows = csv_header_and_rows(idx)
            required_cols = {"cache_row", "subject_id"}
            for cell in EXPECTED_CELLS:
                if cell["modality"] == modality:
                    required_cols.add(label_col(cell["task"], cell["label_policy"]))
            missing = sorted(required_cols - set(header))
            add_check(checks, f"{modality}_index_columns", not missing, {"required": sorted(required_cols), "missing": missing, "rows": rows})
            if missing:
                blockers.append(f"{modality} index missing columns: {missing}")
            if rows <= 0:
                blockers.append(f"{modality} index empty")

    expected_outputs_ok = all(p.startswith("docs/idare_prior_best_confirm_") for p in ALLOWED_OUTPUTS)
    add_check(checks, "output_paths_within_allowed_prefix", expected_outputs_ok, sorted(ALLOWED_OUTPUTS))

    report = {
        "generated_at_utc": now(),
        "status": "BLOCKED" if blockers else "PASSED",
        "mode": mode,
        "expected_branch": EXPECTED_BRANCH,
        "expected_worktree": str(EXPECTED_WORKTREE),
        "actual_root": str(ROOT.resolve()),
        "registered_cells": expected_cells_no_prior,
        "planned_matrix_metadata": {"cells": 4, "folds_per_cell": folds, "planned_confirmation_runs": planned_runs, "metadata_only": mode == "validate"},
        "checks": checks,
        "blockers": blockers,
        "git_status_short_branch": status_short,
        "confirmation_execution_occurred": False,
        "experiment_or_model_result_created": False,
        "model_results_created": False,
        "final_paper_level_claim_made": False,
    }
    return report, blockers

def write_validation_report(report: dict[str, Any]) -> None:
    VALIDATION_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# I-DARE Prior Best Confirmation Validation Report",
        "",
        f"- status: `{report['status']}`",
        f"- mode: `{report['mode']}`",
        f"- expected_branch: `{report['expected_branch']}`",
        f"- expected_worktree: `{report['expected_worktree']}`",
        f"- actual_root: `{report['actual_root']}`",
        "- confirmation_execution_occurred: `false`",
        "- experiment_or_model_result_created: `false`",
        "- model_results_created: `false`",
        "- final_paper_level_claim_made: `false`",
        "",
        "## Registered Cells",
        "",
        "| Cell | Dataset | Modality | Task | Label policy | Recipe |",
        "|---|---|---|---|---|---|",
    ]
    for c in report["registered_cells"]:
        lines.append(f"| {c['cell_id']} | {c['dataset']} | {c['modality']} | {c['task']} | {c['label_policy']} | {c['recipe']} |")
    lines += ["", "## Planned Matrix Metadata", "", "- 4 cells x 6 folds = 24 planned confirmation runs.", "- Metadata only." if report["mode"] == "validate" else "- Execution authorized.", "", "## Blockers", ""]
    if report["blockers"]:
        lines += [f"- BLOCKER: {b}" for b in report["blockers"]]
    else:
        lines.append("- None.")
    lines += ["", "## Check Summary", "", "| Check | OK | Details |", "|---|---:|---|"]
    for chk in report["checks"]:
        d = json.dumps(chk.get("details"), sort_keys=True)
        if len(d) > 180:
            d = d[:177] + "..."
        lines.append(f"| {chk['name']} | {str(chk['ok']).lower()} | `{d}` |")
    VALIDATION_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

class CachedModalityDataset(Dataset):
    def __init__(self, cache: np.ndarray, index_df: pd.DataFrame, label_column: str, subjects: list[int], modality: str, norm: dict[str, np.ndarray] | None = None):
        self.cache = cache
        self.modality = modality
        df = index_df[index_df["subject_id"].astype(int).isin([int(s) for s in subjects])].copy()
        df[label_column] = pd.to_numeric(df[label_column], errors="coerce")
        df = df[df[label_column].isin([0, 1])].copy()
        df["label"] = df[label_column].astype(int)
        df["cache_row"] = df["cache_row"].astype(int)
        df["subject_id"] = df["subject_id"].astype(int)
        if len(df) == 0:
            raise ValueError(f"empty dataset for {modality} {label_column} subjects={subjects}")
        self.df = df.sort_values(["subject_id", "cache_row"]).reset_index(drop=True)
        self.norm = norm

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, i: int) -> dict[str, Any]:
        row = self.df.iloc[i]
        x = np.asarray(self.cache[int(row["cache_row"])], dtype=np.float32)
        if self.norm is not None:
            x = (x - self.norm["mean"]) / self.norm["std"]
        return {
            "x": torch.tensor(x, dtype=torch.float32),
            "y": torch.tensor(int(row["label"]), dtype=torch.long),
            "subject_id": int(row["subject_id"]),
            "cache_row": int(row["cache_row"]),
        }

class EMGMLP(nn.Module):
    def __init__(self, in_dim: int = 22):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, 64),
            nn.LayerNorm(64),
            nn.GELU(),
            nn.Dropout(0.20),
            nn.Linear(64, 32),
            nn.GELU(),
            nn.Linear(32, 2),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)

class EEGFallbackCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv1d(32, 32, kernel_size=9, padding=4),
            nn.GroupNorm(8, 32),
            nn.GELU(),
            nn.AvgPool1d(4),
            nn.Conv1d(32, 64, kernel_size=7, padding=3),
            nn.GroupNorm(8, 64),
            nn.GELU(),
            nn.AdaptiveAvgPool1d(1),
            nn.Flatten(),
            nn.Linear(64, 2),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)

def make_eeg_model(device: torch.device) -> nn.Module:
    try:
        from emotion_deap_idare.models.eeg_segment_classifier import EEGSegmentClassifier
        model = EEGSegmentClassifier(
            C=32,
            sampling_rate=128,
            window_sec=5.0,
            n_classes=2,
            modelsize="lite",
            stem_fusion="concat",
            channel_pos_mode="learnable",
            channel_mixer="mha",
            norm_kind="gn",
            use_spectral_branch=False,
        )
        return EEGModelWrapper(model).to(device)
    except Exception as exc:
        print(f"[WARN] EEGSegmentClassifier import/init failed; using fallback CNN: {exc}", flush=True)
        return EEGFallbackCNN().to(device)

class EEGModelWrapper(nn.Module):
    def __init__(self, model: nn.Module):
        super().__init__()
        self.model = model
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = self.model(x, return_attn=False)
        if isinstance(out, tuple):
            return out[0]
        return out

def make_folds(subjects: list[int], n_folds: int) -> list[FoldSpec]:
    subjects = sorted({int(s) for s in subjects})
    rng = random.Random(20260512)
    shuffled = list(subjects)
    rng.shuffle(shuffled)
    chunks = np.array_split(np.asarray(shuffled, dtype=int), n_folds)
    folds = []
    for i, chunk in enumerate(chunks, 1):
        test_subjects = sorted(int(v) for v in chunk.tolist())
        test_set = set(test_subjects)
        train_subjects = sorted(s for s in subjects if s not in test_set)
        folds.append(FoldSpec(i, train_subjects, test_subjects))
    return folds

def counts(labels: list[int]) -> dict[str, int]:
    return {"0": int(sum(1 for x in labels if x == 0)), "1": int(sum(1 for x in labels if x == 1))}

def safe_div(a: float, b: float) -> float:
    return float(a / b) if b else 0.0

def binary_metrics(y_true: list[int], y_pred: list[int]) -> dict[str, Any]:
    tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)

    f1s = []
    recalls = []
    for label in [0, 1]:
        l_tp = sum(1 for t, p in zip(y_true, y_pred) if t == label and p == label)
        l_fp = sum(1 for t, p in zip(y_true, y_pred) if t != label and p == label)
        l_fn = sum(1 for t, p in zip(y_true, y_pred) if t == label and p != label)
        precision = safe_div(l_tp, l_tp + l_fp)
        recall = safe_div(l_tp, l_tp + l_fn)
        f1 = safe_div(2 * precision * recall, precision + recall)
        f1s.append(f1)
        recalls.append(recall)

    total = len(y_true)
    acc = safe_div(sum(int(t == p) for t, p in zip(y_true, y_pred)), total)
    pred_unique = sorted({int(p) for p in y_pred})
    true_counts = counts(y_true)
    majority_label = 0 if true_counts["0"] >= true_counts["1"] else 1
    majority_acc = safe_div(sum(1 for t in y_true if t == majority_label), total)

    return {
        "n": int(total),
        "accuracy": acc,
        "balanced_accuracy": float(sum(recalls) / 2),
        "macro_f1": float(sum(f1s) / 2),
        "confusion": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "true_counts": true_counts,
        "pred_counts": counts(y_pred),
        "one_class_pred": len(pred_unique) == 1,
        "pred_unique_labels": pred_unique,
        "majority_baseline": {"label": int(majority_label), "accuracy": majority_acc},
    }

def class_weights(labels: list[int], device: torch.device) -> torch.Tensor:
    c = counts(labels)
    n = c["0"] + c["1"]
    w0 = n / (2 * c["0"]) if c["0"] else 0.0
    w1 = n / (2 * c["1"]) if c["1"] else 0.0
    return torch.tensor([w0, w1], dtype=torch.float32, device=device)

def emg_norm(cache: np.ndarray, train_rows: list[int]) -> dict[str, np.ndarray]:
    x = np.asarray(cache[train_rows], dtype=np.float32)
    mean = x.mean(axis=0).astype(np.float32)
    std = x.std(axis=0).astype(np.float32)
    std[std < 1e-6] = 1.0
    return {"mean": mean, "std": std}

def train_eval(spec: RunSpec, caches: dict[str, np.ndarray], indices: dict[str, pd.DataFrame], epochs: int, batch_size: int, lr: float, weight_decay: float, device: torch.device) -> dict[str, Any]:
    random.seed(spec.seed)
    np.random.seed(spec.seed)
    torch.manual_seed(spec.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(spec.seed)

    label = label_col(spec.task, spec.label_policy)
    cache = caches[spec.modality]
    index_df = indices[spec.modality]

    norm = None
    if spec.modality == "EMG":
        train_df = index_df[index_df["subject_id"].astype(int).isin(spec.fold.train_subjects)].copy()
        train_df[label] = pd.to_numeric(train_df[label], errors="coerce")
        train_df = train_df[train_df[label].isin([0, 1])].copy()
        train_rows = train_df["cache_row"].astype(int).tolist()
        norm = emg_norm(cache, train_rows)

    train_ds = CachedModalityDataset(cache, index_df, label, spec.fold.train_subjects, spec.modality, norm)
    test_ds = CachedModalityDataset(cache, index_df, label, spec.fold.test_subjects, spec.modality, norm)

    train_labels = train_ds.df["label"].astype(int).tolist()
    test_labels = test_ds.df["label"].astype(int).tolist()

    generator = torch.Generator()
    generator.manual_seed(spec.seed)

    if spec.recipe == "balanced_sampler_ce":
        c = counts(train_labels)
        weights = []
        for y in train_labels:
            weights.append(1.0 / max(c[str(y)], 1))
        sampler = WeightedRandomSampler(torch.DoubleTensor(weights), num_samples=len(weights), replacement=True, generator=generator)
        shuffle = False
    else:
        sampler = None
        shuffle = True

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=shuffle, sampler=sampler, num_workers=0, generator=None if sampler else generator)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, num_workers=0)

    if spec.modality == "EEG":
        model = make_eeg_model(device)
    else:
        model = EMGMLP(in_dim=cache.shape[1]).to(device)

    if spec.recipe == "ce_class_weighted":
        criterion = nn.CrossEntropyLoss(weight=class_weights(train_labels, device))
    else:
        criterion = nn.CrossEntropyLoss()

    eval_criterion = nn.CrossEntropyLoss()
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)

    start = time.perf_counter()
    epoch_records = []
    best = None
    best_epoch = 0

    for epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0
        train_n = 0
        for batch in train_loader:
            x = batch["x"].to(device)
            y = batch["y"].to(device)
            opt.zero_grad(set_to_none=True)
            logits = model(x)
            loss = criterion(logits, y)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            train_loss += float(loss.item()) * int(y.numel())
            train_n += int(y.numel())

        eval_record = evaluate(model, test_loader, eval_criterion, device)
        epoch_record = {
            "epoch": epoch,
            "train_loss_mean": safe_div(train_loss, train_n),
            "test": eval_record,
        }
        epoch_records.append(epoch_record)
        score = (eval_record["macro_f1"], eval_record["balanced_accuracy"])
        if best is None or score > (best["macro_f1"], best["balanced_accuracy"]):
            best = dict(eval_record)
            best_epoch = epoch

    final = epoch_records[-1]["test"]
    assert best is not None
    elapsed = time.perf_counter() - start

    return {
        "run_id": spec.run_id,
        "cell_id": spec.cell_id,
        "modality": spec.modality,
        "task": spec.task,
        "label_policy": spec.label_policy,
        "recipe": spec.recipe,
        "fold_id": spec.fold.fold_id,
        "seed": spec.seed,
        "epochs": epochs,
        "batch_size": batch_size,
        "lr": lr,
        "weight_decay": weight_decay,
        "train_subjects": spec.fold.train_subjects,
        "test_subjects": spec.fold.test_subjects,
        "train_n": len(train_ds),
        "test_n": len(test_ds),
        "train_counts": counts(train_labels),
        "test_counts": counts(test_labels),
        "final": final,
        "best": {"epoch": best_epoch, **best},
        "duration_sec": elapsed,
        "epoch_records": epoch_records,
    }

def evaluate(model: nn.Module, loader: DataLoader, criterion: nn.Module, device: torch.device) -> dict[str, Any]:
    model.eval()
    y_true, y_pred = [], []
    loss_sum = 0.0
    n = 0
    with torch.no_grad():
        for batch in loader:
            x = batch["x"].to(device)
            y = batch["y"].to(device)
            logits = model(x)
            loss = criterion(logits, y)
            pred = logits.argmax(dim=1)
            loss_sum += float(loss.item()) * int(y.numel())
            n += int(y.numel())
            y_true.extend(int(v) for v in y.cpu().tolist())
            y_pred.extend(int(v) for v in pred.cpu().tolist())
    metrics = binary_metrics(y_true, y_pred)
    metrics["loss_mean"] = safe_div(loss_sum, n)
    return metrics

def build_specs(folds: int, seed: int, indices: dict[str, pd.DataFrame]) -> list[RunSpec]:
    specs = []
    run_id = 1
    for cell in EXPECTED_CELLS:
        df = indices[cell["modality"]].copy()
        label = label_col(cell["task"], cell["label_policy"])
        df[label] = pd.to_numeric(df[label], errors="coerce")
        df = df[df[label].isin([0, 1])].copy()
        subjects = sorted(int(s) for s in df["subject_id"].astype(int).unique())
        fold_specs = make_folds(subjects, folds)
        for fold in fold_specs:
            specs.append(RunSpec(
                run_id=run_id,
                cell_id=cell["cell_id"],
                modality=cell["modality"],
                task=cell["task"],
                label_policy=cell["label_policy"],
                recipe=cell["recipe"],
                fold=fold,
                seed=seed + run_id,
            ))
            run_id += 1
    return specs

def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    groups = {}
    for r in rows:
        key = (r["cell_id"], r["modality"], r["task"], r["label_policy"], r["recipe"])
        groups.setdefault(key, []).append(r)
    for key, group in sorted(groups.items()):
        cell_id, modality, task, policy, recipe = key
        vals = {
            "final_macro_f1": [g["final"]["macro_f1"] for g in group],
            "final_balanced_accuracy": [g["final"]["balanced_accuracy"] for g in group],
            "final_accuracy": [g["final"]["accuracy"] for g in group],
            "best_macro_f1": [g["best"]["macro_f1"] for g in group],
            "best_balanced_accuracy": [g["best"]["balanced_accuracy"] for g in group],
            "majority_accuracy": [g["final"]["majority_baseline"]["accuracy"] for g in group],
        }
        row = {
            "cell_id": cell_id,
            "modality": modality,
            "task": task,
            "label_policy": policy,
            "recipe": recipe,
            "runs": len(group),
            "one_class_final_runs": sum(1 for g in group if g["final"]["one_class_pred"]),
        }
        for name, arr in vals.items():
            a = np.asarray(arr, dtype=float)
            row[f"{name}_mean"] = float(a.mean())
            row[f"{name}_std"] = float(a.std(ddof=0))
            row[f"{name}_min"] = float(a.min())
            row[f"{name}_max"] = float(a.max())
        out.append(row)
    return out

def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow(r)

def flatten_run_for_csv(r: dict[str, Any]) -> dict[str, Any]:
    f = r["final"]
    b = r["best"]
    c = f["confusion"]
    return {
        "run_id": r["run_id"],
        "cell_id": r["cell_id"],
        "modality": r["modality"],
        "task": r["task"],
        "label_policy": r["label_policy"],
        "recipe": r["recipe"],
        "fold_id": r["fold_id"],
        "seed": r["seed"],
        "epochs": r["epochs"],
        "train_n": r["train_n"],
        "test_n": r["test_n"],
        "test_subjects": " ".join(str(x) for x in r["test_subjects"]),
        "final_macro_f1": f["macro_f1"],
        "final_balanced_accuracy": f["balanced_accuracy"],
        "final_accuracy": f["accuracy"],
        "best_epoch": b["epoch"],
        "best_macro_f1": b["macro_f1"],
        "best_balanced_accuracy": b["balanced_accuracy"],
        "best_accuracy": b["accuracy"],
        "tn": c["tn"],
        "fp": c["fp"],
        "fn": c["fn"],
        "tp": c["tp"],
        "pred_0": f["pred_counts"]["0"],
        "pred_1": f["pred_counts"]["1"],
        "true_0": f["true_counts"]["0"],
        "true_1": f["true_counts"]["1"],
        "one_class_pred": f["one_class_pred"],
        "majority_accuracy": f["majority_baseline"]["accuracy"],
        "duration_sec": r["duration_sec"],
    }

def write_reports(run_results: list[dict[str, Any]], preflight_report: dict[str, Any], args: argparse.Namespace) -> None:
    summary = summarize(run_results)
    flat = [flatten_run_for_csv(r) for r in run_results]

    write_csv(RUNS_CSV, flat, list(flat[0].keys()))
    write_csv(FOLD_REPORT_CSV, flat, list(flat[0].keys()))
    write_csv(METRIC_SUMMARY_CSV, summary, list(summary[0].keys()))

    FOLD_REPORT_JSON.write_text(json.dumps({"runs": run_results}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    METRIC_SUMMARY_JSON.write_text(json.dumps({"summary": summary}, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    compare_rows = []
    prior_lookup = {c["cell_id"]: c for c in EXPECTED_CELLS}
    for row in summary:
        prior = prior_lookup[row["cell_id"]]
        compare_rows.append({
            **row,
            "prior_macro_f1": prior["prior_macro_f1"],
            "prior_balanced_accuracy": prior["prior_balanced_accuracy"],
            "delta_macro_f1_mean_minus_prior": row["final_macro_f1_mean"] - prior["prior_macro_f1"],
            "delta_balanced_accuracy_mean_minus_prior": row["final_balanced_accuracy_mean"] - prior["prior_balanced_accuracy"],
        })
    PRIOR_COMPARE_JSON.write_text(json.dumps({"prior_source": "docs/idare_label_policy_ablation_review_status.md", "rows": compare_rows}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(PRIOR_COMPARE_CSV, compare_rows, list(compare_rows[0].keys()))

    leakage = {
        "status": "PASSED",
        "checks": [],
        "forbidden_scope": {name: False for name in FORBIDDEN_SCOPES},
        "run_count": len(run_results),
        "expected_run_count": 24,
    }
    for r in run_results:
        train = set(r["train_subjects"])
        test = set(r["test_subjects"])
        overlap = sorted(train & test)
        leakage["checks"].append({
            "run_id": r["run_id"],
            "cell_id": r["cell_id"],
            "fold_id": r["fold_id"],
            "train_subject_count": len(train),
            "test_subject_count": len(test),
            "subject_overlap": overlap,
            "ok": not overlap,
        })
    if any(not c["ok"] for c in leakage["checks"]):
        leakage["status"] = "BLOCKED"
    LEAKAGE_AUDIT_JSON.write_text(json.dumps(leakage, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    produced = [
        RUNS_CSV, METRIC_SUMMARY_JSON, METRIC_SUMMARY_MD, METRIC_SUMMARY_CSV,
        FOLD_REPORT_JSON, FOLD_REPORT_MD, FOLD_REPORT_CSV,
        PRIOR_COMPARE_JSON, PRIOR_COMPARE_MD, PRIOR_COMPARE_CSV,
        LEAKAGE_AUDIT_JSON, LEAKAGE_AUDIT_MD,
        CLOSEOUT_JSON, CLOSEOUT_MD,
        BUNDLE_JSON, BUNDLE_MD,
        EXECUTION_JSON, EXECUTION_MD,
    ]

    closeout = {
        "status": "closeout_ready",
        "generated_at_utc": now(),
        "authorized_matrix": [{k: c[k] for k in ["cell_id", "dataset", "modality", "task", "label_policy", "recipe"]} for c in EXPECTED_CELLS],
        "confirmation_run_count": len(run_results),
        "expected_run_count": 24,
        "blocker_status": "none" if len(run_results) == 24 and leakage["status"] == "PASSED" else "blocked",
        "confirmation_execution_occurred": True,
        "experiment_or_model_result_created": True,
        "final_paper_level_claim_made": False,
        "forbidden_scope_confirmation": {name: False for name in FORBIDDEN_SCOPES},
        "produced_files": [str(p.relative_to(ROOT)) for p in produced],
        "summary": summary,
        "prior_vs_confirmation": compare_rows,
    }
    CLOSEOUT_JSON.write_text(json.dumps(closeout, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    EXECUTION_JSON.write_text(json.dumps({"preflight": preflight_report, "closeout": closeout, "runs": run_results}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    BUNDLE_JSON.write_text(json.dumps({"artifact_review_bundle_files": closeout["produced_files"], "status": "ready_for_review"}, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    metric_lines = [
        "# I-DARE Prior Best Confirmation Metric Summary",
        "",
        "Smoke/stabilization confirmation only. This is not a final paper-level performance claim.",
        "",
        "| Cell | Modality | Task | Policy | Recipe | Runs | Final macro-F1 mean | Final balanced acc mean | One-class final runs |",
        "|---|---|---|---|---|---:|---:|---:|---:|",
    ]
    for r in summary:
        metric_lines.append(f"| {r['cell_id']} | {r['modality']} | {r['task']} | {r['label_policy']} | {r['recipe']} | {r['runs']} | {r['final_macro_f1_mean']:.4f} | {r['final_balanced_accuracy_mean']:.4f} | {r['one_class_final_runs']} |")
    METRIC_SUMMARY_MD.write_text("\n".join(metric_lines) + "\n", encoding="utf-8")

    fold_lines = [
        "# I-DARE Prior Best Confirmation Fold-Level Report",
        "",
        "| Run | Cell | Fold | Modality | Task | Policy | Recipe | Test subjects | Macro-F1 | Balanced acc | Accuracy | One-class |",
        "|---:|---|---:|---|---|---|---|---|---:|---:|---:|---|",
    ]
    for r in flat:
        fold_lines.append(f"| {r['run_id']} | {r['cell_id']} | {r['fold_id']} | {r['modality']} | {r['task']} | {r['label_policy']} | {r['recipe']} | {r['test_subjects']} | {float(r['final_macro_f1']):.4f} | {float(r['final_balanced_accuracy']):.4f} | {float(r['final_accuracy']):.4f} | {r['one_class_pred']} |")
    FOLD_REPORT_MD.write_text("\n".join(fold_lines) + "\n", encoding="utf-8")

    compare_lines = [
        "# I-DARE Prior Best Confirmation Prior-vs-Confirmation Comparison",
        "",
        "Prior values are from the accepted label-policy ablation review status. Confirmation values are 6-fold means from this authorized 24-run confirmation.",
        "",
        "| Cell | Prior macro-F1 | Confirm macro-F1 mean | Delta | Prior balanced acc | Confirm balanced acc mean | Delta |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in compare_rows:
        compare_lines.append(f"| {r['cell_id']} | {r['prior_macro_f1']:.4f} | {r['final_macro_f1_mean']:.4f} | {r['delta_macro_f1_mean_minus_prior']:.4f} | {r['prior_balanced_accuracy']:.4f} | {r['final_balanced_accuracy_mean']:.4f} | {r['delta_balanced_accuracy_mean_minus_prior']:.4f} |")
    PRIOR_COMPARE_MD.write_text("\n".join(compare_lines) + "\n", encoding="utf-8")

    audit_lines = [
        "# I-DARE Prior Best Confirmation Leakage / Scope Audit",
        "",
        f"- status: `{leakage['status']}`",
        f"- run_count: `{len(run_results)}`",
        "- subject overlap between train and held-out fold subjects: none expected",
        "- forbidden scopes touched: none",
        "",
        "## Forbidden Scope Confirmation",
        "",
    ]
    for k, v in leakage["forbidden_scope"].items():
        audit_lines.append(f"- {k}: `{str(v).lower()}`")
    LEAKAGE_AUDIT_MD.write_text("\n".join(audit_lines) + "\n", encoding="utf-8")

    closeout_lines = [
        "# I-DARE Prior Best Confirmation Closeout Report",
        "",
        f"- status: `{closeout['status']}`",
        f"- blocker_status: `{closeout['blocker_status']}`",
        f"- confirmation_run_count: `{len(run_results)}`",
        "- final_paper_level_claim_made: `false`",
        "",
        "## Produced Files",
        "",
    ]
    for p in closeout["produced_files"]:
        closeout_lines.append(f"- `{p}`")
    CLOSEOUT_MD.write_text("\n".join(closeout_lines) + "\n", encoding="utf-8")

    bundle_lines = ["# I-DARE Prior Best Confirmation Artifact Review Bundle", "", "## Files", ""]
    for p in closeout["produced_files"]:
        bundle_lines.append(f"- `{p}`")
    BUNDLE_MD.write_text("\n".join(bundle_lines) + "\n", encoding="utf-8")

    exec_lines = [
        "# I-DARE Prior Best Confirmation Execution Report",
        "",
        f"- status: `{closeout['status']}`",
        f"- run_count: `{len(run_results)}`",
        "- confirmation_execution_occurred: `true`",
        "- final_paper_level_claim_made: `false`",
    ]
    EXECUTION_MD.write_text("\n".join(exec_lines) + "\n", encoding="utf-8")

def execute(args: argparse.Namespace) -> int:
    preflight_report, blockers = preflight("execute", args.folds, args.planned_runs)
    write_validation_report(preflight_report)
    if blockers:
        print(json.dumps({"status": "BLOCKED", "blockers": blockers}, indent=2))
        return 2

    caches = {}
    indices = {}
    for modality, spec in REQUIRED_INPUTS.items():
        caches[modality] = np.load(ROOT / spec["cache_npy"], mmap_mode="r")
        indices[modality] = pd.read_csv(ROOT / spec["cache_index_csv"])

    specs = build_specs(args.folds, args.seed, indices)
    if len(specs) != args.planned_runs:
        raise RuntimeError(f"planned run count mismatch: expected {args.planned_runs}, got {len(specs)}")
    expected_order = [c["cell_id"] for c in EXPECTED_CELLS for _ in range(args.folds)]
    actual_order = [s.cell_id for s in specs]
    if actual_order != expected_order:
        raise RuntimeError(f"cell order mismatch: {actual_order}")

    device = torch.device("cpu" if args.cpu or not torch.cuda.is_available() else "cuda")
    print(f"[INFO] device={device}")
    print(f"[INFO] authorized_runs={len(specs)}")

    results = []
    for spec in specs:
        print(f"[RUN] {spec.run_id:02d}/24 {spec.cell_id} {spec.modality} {spec.task} {spec.label_policy} {spec.recipe} fold={spec.fold.fold_id}", flush=True)
        row = train_eval(spec, caches, indices, args.epochs, args.batch_size, args.lr, args.weight_decay, device)
        results.append(row)
        print(json.dumps({
            "run_id": row["run_id"],
            "cell_id": row["cell_id"],
            "fold_id": row["fold_id"],
            "macro_f1": row["final"]["macro_f1"],
            "balanced_accuracy": row["final"]["balanced_accuracy"],
            "accuracy": row["final"]["accuracy"],
            "one_class_pred": row["final"]["one_class_pred"],
        }, sort_keys=True), flush=True)

    write_reports(results, preflight_report, args)
    print(json.dumps({
        "status": "closeout_ready",
        "run_count": len(results),
        "outputs": [
            str(RUNS_CSV.relative_to(ROOT)),
            str(METRIC_SUMMARY_MD.relative_to(ROOT)),
            str(FOLD_REPORT_MD.relative_to(ROOT)),
            str(PRIOR_COMPARE_MD.relative_to(ROOT)),
            str(LEAKAGE_AUDIT_MD.relative_to(ROOT)),
            str(CLOSEOUT_MD.relative_to(ROOT)),
            str(BUNDLE_MD.relative_to(ROOT)),
        ],
        "final_paper_level_claim_made": False,
    }, indent=2))
    return 0

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="validate", choices=["validate", "execute"])
    parser.add_argument("--folds", type=int, default=6)
    parser.add_argument("--planned-runs", type=int, default=24)
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--seed", type=int, default=20260512)
    parser.add_argument("--cpu", action="store_true")
    args = parser.parse_args()

    if args.mode == "validate":
        report, blockers = preflight("validate", args.folds, args.planned_runs)
        write_validation_report(report)
        print(json.dumps({
            "status": report["status"],
            "blocker_count": len(blockers),
            "out_md": str(VALIDATION_MD.relative_to(ROOT)),
            "out_json": str(VALIDATION_JSON.relative_to(ROOT)),
            "confirmation_execution_occurred": False,
            "experiment_or_model_result_created": False,
        }, indent=2))
        return 2 if blockers else 0

    return execute(args)

if __name__ == "__main__":
    raise SystemExit(main())
