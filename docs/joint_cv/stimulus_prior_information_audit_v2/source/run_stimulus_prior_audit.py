#!/usr/bin/env python3
"""Stimulus-Associated Prior Information Audit (candidate v1).

Quantifies how much information about a held-out participant's binary
Valence/Arousal label is available from the *identity of the eliciting
stimulus alone*, when the stimulus-conditioned label tendency is estimated
from source participants only.

Datasets: DEAP, I-DARE (Primary), DEJA-VU (external validation).

This is a metadata / label analysis. No EEG or EMG signal values are read,
transformed, windowed, or used. (The DEAP official pickle stores labels and
signals in one object, so deserialising it necessarily materialises the signal
array in memory; the array is never read, transformed or persisted.)

Read-only with respect to every dataset and every authority repository.

Root audit seed: 20260822
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Sequence

import numpy as np
import pandas as pd
from scipy.stats import rankdata, spearmanr, pearsonr

# --------------------------------------------------------------------------
# Constants / authorities
# --------------------------------------------------------------------------

ROOT_SEED = 20260822

MAIN_REPO = Path("/mnt/HDD/AliWorks/MM-SAGE-DG-PARALLEL-UNIVERSE")
DEJAVU_SHARED_REPO = Path("/mnt/HDD/AliWorks/DEJA-VU-Emotion-Recognition")
DEJAVU_INTEGRATION_REPO = Path("/mnt/HDD/AliWorks/MM-SAGE-DG-dejavu-paper2")

DEJAVU_PINNED_COMMIT = "01351073683eaa6c4469bf8b8728227a184b1ac4"

DEAP_ROOT = Path("/mnt/HDD/AliWorks/DEAP")
IDARE_ROOT = Path("/mnt/HDD/AliWorks/I-DARE")

DEAP_SUBJECT_FOLDS = MAIN_REPO / "configs/cv/folds/deap_subject_folds.csv"
IDARE_SUBJECT_FOLDS = MAIN_REPO / "configs/cv/folds/idare_subject_folds.csv"
DEJAVU_LABELS = DEJAVU_SHARED_REPO / "manifests/dejavu_cohort_b_primary_labels.csv"
DEJAVU_FOLDS = DEJAVU_SHARED_REPO / "folds/dejavu_joint_cv_repeated_assignments.csv"

MIDPOINT = 5.0
JEFFREYS_A = 0.5
JEFFREYS_N = 1.0

TASKS = ("valence", "arousal")
DATASETS = ("DEAP", "IDARE", "DEJAVU")
PRIMARY_DATASETS = ("DEAP", "IDARE")

N_BOOTSTRAP = 10_000
N_PERMUTATION = 10_000

# DEJA-VU frozen expectations (verified, never assumed).
DEJAVU_EXPECTED = {
    "emotional_physical_trials": 90,
    "exact_videos": 16,
    "participants": 24,
    "participant_sessions": 30,
    "valence": {"low": 53, "high": 22, "drop": 15, "retained": 75},
    "arousal": {"low": 33, "high": 38, "drop": 19, "retained": 71},
}


# --------------------------------------------------------------------------
# Utilities
# --------------------------------------------------------------------------

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_frame(frame: pd.DataFrame) -> str:
    """Content hash of a DataFrame, independent of file compression metadata."""
    return sha256_text(frame.to_csv(index=False, lineterminator="\n"))


def git_info(repo: Path) -> dict:
    def run(args: list[str]) -> str | None:
        try:
            out = subprocess.run(
                ["git", "-C", str(repo), *args],
                capture_output=True, text=True, check=True, timeout=60,
            )
            return out.stdout.strip()
        except Exception:
            return None

    return {
        "path": str(repo),
        "head": run(["rev-parse", "HEAD"]),
        "branch": run(["rev-parse", "--abbrev-ref", "HEAD"]),
        "dirty_tracked_files": run(["status", "--porcelain", "--untracked-files=no"]),
    }


def derived_seed(*parts: object) -> int:
    """Deterministic child seed derived from the root audit seed."""
    payload = f"MM-SAGE-DG|stimulus-prior-audit-v1|root={ROOT_SEED}|" + "|".join(
        str(p) for p in parts
    )
    return int.from_bytes(hashlib.sha256(payload.encode("utf-8")).digest()[:8], "big") % (2**32)


def binary_from_score(score: float) -> float:
    """Paper-2 cross-dataset rule: <5 -> LOW(0), >5 -> HIGH(1), ==5 -> DROP."""
    value = float(score)
    if not math.isfinite(value):
        return np.nan
    if value == MIDPOINT:
        return np.nan
    return 1.0 if value > MIDPOINT else 0.0


# --------------------------------------------------------------------------
# Canonical trial tables
# --------------------------------------------------------------------------

CORE_COLUMNS = [
    "dataset",
    "participant_id",
    "session_id",
    "physical_trial_id",
    "canonical_stimulus_id",
    "valence_score",
    "arousal_score",
    "valence_binary",
    "arousal_binary",
    "valence_retained",
    "arousal_retained",
]


def _finalise(frame: pd.DataFrame) -> pd.DataFrame:
    for task in TASKS:
        frame[f"{task}_binary"] = frame[f"{task}_score"].map(binary_from_score)
        frame[f"{task}_retained"] = frame[f"{task}_binary"].notna()
    extra = [c for c in frame.columns if c not in CORE_COLUMNS]
    return frame[CORE_COLUMNS + extra].reset_index(drop=True)


def build_deap_table() -> pd.DataFrame:
    """DEAP from the active MM-SAGE-DG authority loader."""
    sys.path.insert(0, str(MAIN_REPO / "src"))
    from mm_sage_dg.data import build_deap_inventory  # noqa: PLC0415

    inv = build_deap_inventory(DEAP_ROOT)
    order = pd.read_csv(MAIN_REPO / "configs/data/deap_subject_presentation_order.csv")
    order_key = order.set_index(["subject_id", "source_trial_index_0based"])

    frame = pd.DataFrame(
        {
            "dataset": "DEAP",
            "participant_id": inv["subject_id"],
            "session_id": "",  # single-session design
            "physical_trial_id": inv["trial_id"],
            "canonical_stimulus_id": inv["stimulus_id"],
            "valence_score": inv["valence_score"].astype(float),
            "arousal_score": inv["arousal_score"].astype(float),
            "source_trial_index_0based": inv["source_trial_index"].astype(int),
            "source_container_file": inv["eeg_file"],
        }
    )
    idx = pd.MultiIndex.from_arrays(
        [frame["participant_id"], frame["source_trial_index_0based"]]
    )
    frame["subject_presentation_order"] = order_key["presentation_order"].reindex(idx).to_numpy()
    frame["verified_order_hypothesis"] = order_key["verified_order_hypothesis"].reindex(idx).to_numpy()
    # Cross-check the two DEAP stimulus authorities agree row by row.
    order_stim = order_key["verified_stimulus_id"].reindex(idx).to_numpy()
    if not (order_stim == frame["canonical_stimulus_id"].to_numpy()).all():
        raise RuntimeError("DEAP verified mapping vs subject presentation order disagree")
    frame["session_structure_present"] = False
    frame["stimulus_identity_scheme"] = "experiment_order_alignment"
    frame["label_source"] = "official_preprocessed_python:labels[:,0..1]"
    return _finalise(frame)


def build_idare_table() -> pd.DataFrame:
    """I-DARE from the active MM-SAGE-DG authority loader."""
    sys.path.insert(0, str(MAIN_REPO / "src"))
    from mm_sage_dg.data import build_idare_inventory  # noqa: PLC0415

    inv = build_idare_inventory(IDARE_ROOT)
    pairing = pd.read_csv(MAIN_REPO / "configs/data/idare_event_pairing.csv")
    pair_key = pairing.set_index("stimulus_event_index_0based")

    frame = pd.DataFrame(
        {
            "dataset": "IDARE",
            "participant_id": inv["subject_id"],
            "session_id": "",  # single-session design
            "physical_trial_id": inv["trial_id"],
            "canonical_stimulus_id": inv["stimulus_id"],
            "valence_score": inv["valence_score"].astype(float),
            "arousal_score": inv["arousal_score"].astype(float),
            "source_event_index_0based": inv["source_trial_index"].astype(int),
            "source_eeg_file": inv["eeg_file"],
            "source_emg_file": inv["emg_file"],
        }
    )
    ev = frame["source_event_index_0based"]
    frame["raw_stimulus_name"] = pair_key["raw_stimulus_name"].reindex(ev).to_numpy()
    frame["presentation_order"] = pair_key["presentation_order"].reindex(ev).to_numpy()
    pair_stim = pair_key["canonical_stimulus_id"].reindex(ev).to_numpy()
    if not (pair_stim == frame["canonical_stimulus_id"].to_numpy()).all():
        raise RuntimeError("I-DARE event pairing vs inventory canonical stimulus disagree")
    frame["session_structure_present"] = False
    frame["stimulus_identity_scheme"] = "nearest_preceding_baseline_event_pairing"
    frame["label_source"] = "labels/Valence_SAM.csv;labels/Arousal_SAM.csv"
    return _finalise(frame)


def build_dejavu_table() -> pd.DataFrame:
    """DEJA-VU from the pinned read-only shared authority."""
    raw = pd.read_csv(DEJAVU_LABELS)

    if not bool(raw["is_emotional_stimulus"].all()):
        raise RuntimeError("DEJA-VU cohort contains non-emotional presentations")
    if bool(raw["is_baseline"].any()):
        raise RuntimeError("DEJA-VU cohort contains baseline presentations")

    frame = pd.DataFrame(
        {
            "dataset": "DEJAVU",
            "participant_id": raw["participant_id"],
            "session_id": raw["session_id"],
            "physical_trial_id": raw["presentation_id"],
            "canonical_stimulus_id": raw["content_id"],
            # Paper-2 DEJA-VU label authority: post-stimulus `after` rating.
            "valence_score": pd.to_numeric(raw["after_valence"], errors="coerce").astype(float),
            "arousal_score": pd.to_numeric(raw["after_arousal"], errors="coerce").astype(float),
            "video_id": raw["video_id"],
            "video_name": raw["video_name"],
            "canonical_quadrant": raw["canonical_quadrant"],
            "emotion_name": raw["emotion_name"],
            "chronological_position": raw["chronological_position"],
            "video_order": raw["video_order"],
            "participant_session_key": raw["participant_session_key"],
        }
    )
    frame["session_structure_present"] = True
    frame["stimulus_identity_scheme"] = "shared_authority_cohort_b_content_id"
    frame["label_source"] = "manifests/dejavu_cohort_b_primary_labels.csv:after_valence|after_arousal"
    out = _finalise(frame)

    # Independently re-derive the frozen support and cross-check the manifest's
    # own precomputed primary labels.
    for task, col in (("valence", "primary_valence_label"), ("arousal", "primary_arousal_label")):
        ours = out[f"{task}_binary"]
        theirs = pd.to_numeric(raw[col], errors="coerce")
        if not ours.isna().equals(theirs.isna()):
            raise RuntimeError(f"DEJA-VU {task} retention disagrees with manifest primary label")
        mask = ours.notna()
        if not np.array_equal(ours[mask].to_numpy(), theirs[mask].to_numpy()):
            raise RuntimeError(f"DEJA-VU {task} binary disagrees with manifest primary label")
    return out


# --------------------------------------------------------------------------
# Fold views
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class View:
    name: str            # "A_LOPO" or "B_SUBJECT_FOLD"
    dataset: str
    repetition: int      # 0 for View A and non-repeated View B
    group_of_participant: dict     # participant_id -> held-out group label
    provenance: str


def build_views(dataset: str, table: pd.DataFrame) -> list[View]:
    participants = sorted(table["participant_id"].unique())
    views = [
        View(
            name="A_LOPO",
            dataset=dataset,
            repetition=0,
            group_of_participant={p: p for p in participants},
            provenance="leave_one_participant_out",
        )
    ]

    if dataset == "DEAP":
        folds = pd.read_csv(DEAP_SUBJECT_FOLDS)
        mapping = dict(zip(folds["entity_id"], folds["fold_index"].astype(int)))
        _require_cover(mapping, participants, "DEAP subject folds")
        views.append(View("B_SUBJECT_FOLD", dataset, 0, mapping,
                          f"configs/cv/folds/deap_subject_folds.csv"))
    elif dataset == "IDARE":
        folds = pd.read_csv(IDARE_SUBJECT_FOLDS)
        mapping = dict(zip(folds["entity_id"], folds["fold_index"].astype(int)))
        _require_cover(mapping, participants, "I-DARE subject folds")
        views.append(View("B_SUBJECT_FOLD", dataset, 0, mapping,
                          f"configs/cv/folds/idare_subject_folds.csv"))
    elif dataset == "DEJAVU":
        folds = pd.read_csv(DEJAVU_FOLDS)
        part = folds[folds["entity_type"] == "participant"]
        for rep in sorted(part["repetition"].unique()):
            sub = part[part["repetition"] == rep]
            mapping = dict(zip(sub["entity_id"], sub["fold"].astype(int)))
            _require_cover(mapping, participants, f"DEJA-VU participant folds rep{rep}")
            views.append(View("B_SUBJECT_FOLD", dataset, int(rep), mapping,
                              f"shared:{DEJAVU_PINNED_COMMIT}:folds/"
                              f"dejavu_joint_cv_repeated_assignments.csv (participant, rep={rep})"))
    return views


def _require_cover(mapping: dict, participants: Sequence[str], label: str) -> None:
    missing = sorted(set(participants) - set(mapping))
    extra = sorted(set(mapping) - set(participants))
    if missing or extra:
        raise RuntimeError(f"{label}: participant mismatch missing={missing} extra={extra}")


# --------------------------------------------------------------------------
# Source-only stimulus-ID prior predictor
# --------------------------------------------------------------------------
#
# Two independent implementations:
#   * `predict_reference` never indexes target-row labels at all. It is the
#     implementation used for every reported result. It is, by construction,
#     source-only.
#   * `predict_fast` computes the same quantity as (global aggregate - own
#     group's contribution) and is used only inside the permutation loop.
# Their equality on real and permuted data is asserted by the test suite.


def _jeffreys(n_high: np.ndarray | float, n_total: np.ndarray | float) -> np.ndarray | float:
    return (n_high + JEFFREYS_A) / (n_total + JEFFREYS_N)


def predict_reference(
    group: np.ndarray, stim: np.ndarray, label: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Out-of-fold source-only prediction. Loops over held-out groups.

    Returns (p_stimulus, p_global, fallback_mask).
    """
    n = len(label)
    p_stim = np.full(n, np.nan)
    p_glob = np.full(n, np.nan)
    fallback = np.zeros(n, dtype=bool)

    for g in np.unique(group):
        tgt = group == g
        src = ~tgt
        if not src.any():
            raise RuntimeError("Empty source set for a held-out group")

        src_label = label[src]           # only source labels are ever read
        src_stim = stim[src]
        p_global_g = _jeffreys(src_label.sum(), src_label.size)

        # Stimulus-conditioned source prior.
        n_by = np.bincount(src_stim, minlength=int(stim.max()) + 1).astype(float)
        h_by = np.bincount(src_stim, weights=src_label, minlength=int(stim.max()) + 1)

        tgt_stim = stim[tgt]             # target *stimulus identity* only
        seen = n_by[tgt_stim] > 0
        vals = np.where(seen, _jeffreys(h_by[tgt_stim], n_by[tgt_stim]), p_global_g)

        p_stim[tgt] = vals
        p_glob[tgt] = p_global_g
        fallback[tgt] = ~seen

    if not np.isfinite(p_stim).all() or not np.isfinite(p_glob).all():
        raise RuntimeError("Non-finite out-of-fold probability")
    if not ((p_stim > 0).all() and (p_stim < 1).all()):
        raise RuntimeError("Jeffreys smoothing failed to bound probabilities")
    return p_stim, p_glob, fallback


def predict_fast(
    group_idx: np.ndarray, stim: np.ndarray, label: np.ndarray, n_groups: int, n_stim: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Vectorised equivalent of `predict_reference` (aggregate minus own group)."""
    flat = group_idx * n_stim + stim
    n_gv = np.bincount(flat, minlength=n_groups * n_stim).astype(float)
    h_gv = np.bincount(flat, weights=label, minlength=n_groups * n_stim)
    n_v = n_gv.reshape(n_groups, n_stim).sum(axis=0)
    h_v = h_gv.reshape(n_groups, n_stim).sum(axis=0)
    n_g = np.bincount(group_idx, minlength=n_groups).astype(float)
    h_g = np.bincount(group_idx, weights=label, minlength=n_groups)

    src_n = n_v[stim] - n_gv[flat]
    src_h = h_v[stim] - h_gv[flat]
    src_N = label.size - n_g[group_idx]
    src_H = label.sum() - h_g[group_idx]

    p_glob = _jeffreys(src_H, src_N)
    seen = src_n > 0
    p_stim = np.where(seen, _jeffreys(src_h, src_n), p_glob)
    return p_stim, p_glob, ~seen


# --------------------------------------------------------------------------
# Metrics
# --------------------------------------------------------------------------

def hard_predict(p: np.ndarray, p_global: np.ndarray) -> tuple[np.ndarray, int]:
    """p>0.5 -> HIGH, p<0.5 -> LOW, p==0.5 -> source global majority (LOW if 0.5)."""
    tie = p == 0.5
    yhat = (p > 0.5).astype(int)
    yhat[tie] = (p_global[tie] > 0.5).astype(int)
    return yhat, int(tie.sum())


def auc_score(y: np.ndarray, p: np.ndarray) -> float:
    n1 = float(y.sum())
    n0 = float(y.size - n1)
    if n1 == 0 or n0 == 0:
        return np.nan
    r = rankdata(p)
    return float((r[y == 1].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n0))


def classification_metrics(y: np.ndarray, p: np.ndarray, p_global: np.ndarray) -> dict:
    yhat, ties = hard_predict(p, p_global)
    out: dict[str, float] = {"n": int(y.size), "n_ties": ties}
    out["accuracy"] = float((yhat == y).mean())

    recalls, f1s = [], []
    for c in (0, 1):
        pos = y == c
        pred = yhat == c
        recalls.append(float(pred[pos].mean()) if pos.any() else np.nan)
        tp = float((pos & pred).sum())
        denom = float(pos.sum() + pred.sum())
        f1s.append((2.0 * tp / denom) if denom > 0 else 0.0)
    out["balanced_accuracy"] = float(np.mean(recalls)) if not any(np.isnan(recalls)) else np.nan
    out["macro_f1"] = float(np.mean(f1s))
    out["auc"] = auc_score(y, p)
    out["log_loss"] = float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))
    out["brier"] = float(np.mean((p - y) ** 2))
    return out


def metric_pair(y: np.ndarray, p_stim: np.ndarray, p_glob: np.ndarray) -> dict:
    s = classification_metrics(y, p_stim, p_glob)
    g = classification_metrics(y, p_glob, p_glob)
    row = {f"stim_{k}": v for k, v in s.items()}
    row.update({f"glob_{k}": v for k, v in g.items()})
    row["delta_ba_pp"] = 100.0 * (s["balanced_accuracy"] - g["balanced_accuracy"])
    row["delta_accuracy_pp"] = 100.0 * (s["accuracy"] - g["accuracy"])
    row["delta_macro_f1"] = s["macro_f1"] - g["macro_f1"]
    row["delta_auc"] = s["auc"] - g["auc"]
    row["logloss_gain"] = g["log_loss"] - s["log_loss"]
    row["brier_gain"] = g["brier"] - s["brier"]
    row["bits_per_trial"] = (g["log_loss"] - s["log_loss"]) / math.log(2.0)
    row["n"] = s["n"]
    return row


# --------------------------------------------------------------------------
# Task-level data container
# --------------------------------------------------------------------------

@dataclass
class TaskData:
    dataset: str
    task: str
    view: View
    participant: np.ndarray      # participant id (string)
    group: np.ndarray            # held-out group label (string)
    group_idx: np.ndarray
    n_groups: int
    stim: np.ndarray             # stimulus code
    stim_names: np.ndarray
    n_stim: int
    label: np.ndarray            # 0/1 float
    trial_id: np.ndarray
    score: np.ndarray            # raw continuous rating (retained rows)


def make_task_data(dataset: str, table: pd.DataFrame, task: str, view: View) -> TaskData:
    sub = table[table[f"{task}_retained"]].copy()
    sub = sub.sort_values("physical_trial_id", kind="mergesort").reset_index(drop=True)

    grp = sub["participant_id"].map(view.group_of_participant)
    if grp.isna().any():
        raise RuntimeError("Participant without a held-out group assignment")
    grp = grp.astype(str)

    stim_names, stim_codes = np.unique(sub["canonical_stimulus_id"].to_numpy(), return_inverse=True)
    grp_names, grp_codes = np.unique(grp.to_numpy(), return_inverse=True)

    return TaskData(
        dataset=dataset,
        task=task,
        view=view,
        participant=sub["participant_id"].to_numpy(),
        group=grp.to_numpy(),
        group_idx=grp_codes,
        n_groups=len(grp_names),
        stim=stim_codes,
        stim_names=stim_names,
        n_stim=len(stim_names),
        label=sub[f"{task}_binary"].to_numpy(dtype=float),
        trial_id=sub["physical_trial_id"].to_numpy(),
        score=sub[f"{task}_score"].to_numpy(dtype=float),
    )


# --------------------------------------------------------------------------
# Analysis A - structural overlap
# --------------------------------------------------------------------------

def structural_overlap(td: TaskData) -> pd.DataFrame:
    rows = []
    for g in np.unique(td.group):
        tgt = td.group == g
        src = ~tgt
        src_stim = td.stim[src]
        tgt_stim = td.stim[tgt]
        n_by = np.bincount(src_stim, minlength=td.n_stim)
        # source participants supporting each stimulus
        part_by: dict[int, set] = {}
        for s, p in zip(src_stim, td.participant[src]):
            part_by.setdefault(int(s), set()).add(p)

        seen_trial = n_by[tgt_stim] > 0
        uniq = np.unique(tgt_stim)
        seen_uniq = n_by[uniq] > 0
        support_trials = n_by[uniq].astype(float)
        support_parts = np.array([len(part_by.get(int(s), ())) for s in uniq], dtype=float)

        rows.append(
            {
                "dataset": td.dataset,
                "task": td.task,
                "view": td.view.name,
                "repetition": td.view.repetition,
                "held_out_group": g,
                "n_target_trials": int(tgt.sum()),
                "n_target_unique_stimuli": int(uniq.size),
                "trial_weighted_overlap_fraction": float(seen_trial.mean()),
                "unique_stimulus_overlap_fraction": float(seen_uniq.mean()),
                "n_fallback_trials": int((~seen_trial).sum()),
                "fallback_trial_fraction": float((~seen_trial).mean()),
                "source_participants_per_target_stimulus_min": float(support_parts.min()),
                "source_participants_per_target_stimulus_median": float(np.median(support_parts)),
                "source_participants_per_target_stimulus_mean": float(support_parts.mean()),
                "source_participants_per_target_stimulus_max": float(support_parts.max()),
                "source_trials_per_target_stimulus_min": float(support_trials.min()),
                "source_trials_per_target_stimulus_median": float(np.median(support_trials)),
                "source_trials_per_target_stimulus_mean": float(support_trials.mean()),
                "source_trials_per_target_stimulus_max": float(support_trials.max()),
            }
        )
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# Analysis C - stimulus label consistency / entropy
# --------------------------------------------------------------------------

def binary_entropy(p: float) -> float:
    if p <= 0.0 or p >= 1.0:
        return 0.0
    return float(-(p * math.log2(p) + (1 - p) * math.log2(1 - p)))


def label_consistency(td: TaskData) -> pd.DataFrame:
    rows = []
    for s in range(td.n_stim):
        m = td.stim == s
        y = td.label[m]
        n = int(y.size)
        high = int(y.sum())
        low = n - high
        emp = high / n
        p_smooth = float(_jeffreys(high, n))
        rows.append(
            {
                "dataset": td.dataset,
                "task": td.task,
                "canonical_stimulus_id": td.stim_names[s],
                "retained_n": n,
                "n_unique_participants": int(len(set(td.participant[m]))),
                "low_count": low,
                "high_count": high,
                "empirical_high_probability": emp,
                "smoothed_high_probability": p_smooth,
                "majority_agreement_fraction": max(emp, 1 - emp),
                "conditional_entropy_bits": binary_entropy(emp),
                "abs_distance_from_half": abs(emp - 0.5),
            }
        )
    return pd.DataFrame(rows)


def consistency_summary(td: TaskData, cons: pd.DataFrame) -> dict:
    p_marg = float(td.label.mean())
    h_y = binary_entropy(p_marg)
    w = cons["retained_n"].to_numpy(dtype=float)
    h_cond = cons["conditional_entropy_bits"].to_numpy(dtype=float)
    h_given = float(np.average(h_cond, weights=w))
    return {
        "dataset": td.dataset,
        "task": td.task,
        "n_retained": int(td.label.size),
        "n_stimuli": int(td.n_stim),
        "marginal_high_probability": p_marg,
        "H_Y_bits": h_y,
        "H_Y_given_stimulus_bits_trial_weighted": h_given,
        "plug_in_mutual_information_bits_DESCRIPTIVE_BIASED": h_y - h_given,
        "macro_mean_conditional_entropy_bits": float(h_cond.mean()),
        "macro_median_conditional_entropy_bits": float(np.median(h_cond)),
        "macro_mean_majority_agreement": float(cons["majority_agreement_fraction"].mean()),
        "trial_weighted_majority_agreement": float(
            np.average(cons["majority_agreement_fraction"].to_numpy(dtype=float), weights=w)
        ),
        "q10_conditional_entropy_bits": float(np.quantile(h_cond, 0.10)),
        "q25_conditional_entropy_bits": float(np.quantile(h_cond, 0.25)),
        "q75_conditional_entropy_bits": float(np.quantile(h_cond, 0.75)),
        "q90_conditional_entropy_bits": float(np.quantile(h_cond, 0.90)),
    }


# --------------------------------------------------------------------------
# Analysis D - continuous rating prior
# --------------------------------------------------------------------------

def continuous_prior(dataset: str, table: pd.DataFrame, task: str) -> dict:
    sub = table[table[f"{task}_score"].notna()].copy()
    sub = sub.sort_values("physical_trial_id", kind="mergesort").reset_index(drop=True)
    y = sub[f"{task}_score"].to_numpy(dtype=float)
    part = sub["participant_id"].to_numpy()
    stim_names, stim = np.unique(sub["canonical_stimulus_id"].to_numpy(), return_inverse=True)
    n_stim = len(stim_names)

    pred_s = np.full(y.size, np.nan)
    pred_g = np.full(y.size, np.nan)
    fallback = np.zeros(y.size, dtype=bool)
    for p in np.unique(part):
        tgt = part == p
        src = ~tgt
        sy, ss = y[src], stim[src]
        gmean = float(sy.mean())
        n_by = np.bincount(ss, minlength=n_stim).astype(float)
        s_by = np.bincount(ss, weights=sy, minlength=n_stim)
        ts = stim[tgt]
        seen = n_by[ts] > 0
        pred_s[tgt] = np.where(seen, np.divide(s_by[ts], np.where(n_by[ts] > 0, n_by[ts], 1.0)), gmean)
        pred_g[tgt] = gmean
        fallback[tgt] = ~seen

    def stats(pred: np.ndarray, prefix: str) -> dict:
        res = y - pred
        ss_res = float((res**2).sum())
        ss_tot = float(((y - y.mean()) ** 2).sum())
        d = {
            f"{prefix}_mae": float(np.abs(res).mean()),
            f"{prefix}_rmse": float(np.sqrt((res**2).mean())),
            f"{prefix}_r2": float(1.0 - ss_res / ss_tot) if ss_tot > 0 else np.nan,
        }
        if np.std(pred) > 0 and np.std(y) > 0:
            d[f"{prefix}_pearson_r"] = float(pearsonr(y, pred)[0])
            d[f"{prefix}_spearman_r"] = float(spearmanr(y, pred)[0])
        else:
            d[f"{prefix}_pearson_r"] = np.nan
            d[f"{prefix}_spearman_r"] = np.nan
        return d

    out = {
        "dataset": dataset,
        "task": task,
        "view": "A_LOPO",
        "n_trials_all_scores": int(y.size),
        "n_fallback_trials": int(fallback.sum()),
        "rating_scale_note": "raw SAM rating before binary midpoint removal",
    }
    out.update(stats(pred_s, "stimulus"))
    out.update(stats(pred_g, "global"))
    out["mae_improvement"] = out["global_mae"] - out["stimulus_mae"]
    out["rmse_improvement"] = out["global_rmse"] - out["stimulus_rmse"]
    out["r2_improvement"] = out["stimulus_r2"] - out["global_r2"]
    return out


# --------------------------------------------------------------------------
# Uncertainty
# --------------------------------------------------------------------------

def cluster_bootstrap(td: TaskData, p_stim: np.ndarray, p_glob: np.ndarray,
                      n_rep: int = N_BOOTSTRAP) -> pd.DataFrame:
    """PRIMARY interval. Resample held-out participants; keep all their trials.

    IMPORTANT LIMITATION: the out-of-fold probabilities are held FIXED while the
    participants that produced them are resampled. The interval is therefore
    conditional on the stimulus->label tendencies realised in this participant
    sample: it propagates evaluation-set sampling variability but NOT the
    estimation variability of the source-side prior, and so UNDERSTATES total
    uncertainty. `cluster_bootstrap_refit` recomputes the prior inside each
    resample and is reported alongside as a conservative upper bound.
    """
    parts = np.unique(td.participant)
    idx_by_part = [np.flatnonzero(td.participant == p) for p in parts]
    rng = np.random.default_rng(derived_seed("bootstrap", td.dataset, td.task, td.view.name,
                                             td.view.repetition))
    keys = ["stim_balanced_accuracy", "stim_accuracy", "stim_macro_f1", "stim_auc",
            "stim_log_loss", "stim_brier", "glob_balanced_accuracy", "glob_accuracy",
            "glob_macro_f1", "glob_auc", "glob_log_loss", "glob_brier",
            "delta_ba_pp", "delta_accuracy_pp", "delta_macro_f1", "delta_auc",
            "logloss_gain", "brier_gain", "bits_per_trial"]
    acc = {k: np.full(n_rep, np.nan) for k in keys}
    invalid = 0

    for r in range(n_rep):
        pick = rng.integers(0, len(parts), size=len(parts))
        sel = np.concatenate([idx_by_part[i] for i in pick])
        y = td.label[sel]
        if y.min() == y.max():
            invalid += 1
            continue
        row = metric_pair(y, p_stim[sel], p_glob[sel])
        for k in keys:
            acc[k][r] = row[k]

    rows = []
    for k in keys:
        v = acc[k]
        ok = v[np.isfinite(v)]
        rows.append({
            "dataset": td.dataset, "task": td.task, "view": td.view.name,
            "repetition": td.view.repetition, "metric": k,
            "n_replicates_requested": n_rep,
            "n_replicates_valid": int(ok.size),
            "n_replicates_invalid": int(n_rep - ok.size),
            "ci95_low": float(np.percentile(ok, 2.5)) if ok.size else np.nan,
            "ci95_high": float(np.percentile(ok, 97.5)) if ok.size else np.nan,
            "bootstrap_mean": float(ok.mean()) if ok.size else np.nan,
        })
    out = pd.DataFrame(rows)
    out["n_all_class_degenerate_resamples"] = invalid
    out["bootstrap_variant"] = "primary_fixed_predictions"
    return out


def cluster_bootstrap_refit(td: TaskData, n_rep: int = N_BOOTSTRAP) -> pd.DataFrame:
    """SENSITIVITY interval: recompute the source-only prior inside each resample.

    Participants are resampled with replacement; the leave-one-participant-out
    prior is then refitted *within* the resample, with all duplicate copies of the
    same original participant held out together so that no copy can ever appear in
    its own source set. This propagates the estimation variability of the prior
    that the primary interval conditions away.

    It is a CONSERVATIVE UPPER BOUND, not the truth: a bootstrap resample contains
    only ~63% distinct participants, so the refitted prior is estimated from fewer
    effective source participants than the real analysis and the interval carries
    its own inflation.
    """
    parts = np.unique(td.participant)
    idx_by_part = [np.flatnonzero(td.participant == p) for p in parts]
    rng = np.random.default_rng(derived_seed("bootstrap-refit", td.dataset, td.task,
                                             td.view.name, td.view.repetition))
    keys = ["stim_balanced_accuracy", "delta_ba_pp", "bits_per_trial",
            "logloss_gain", "brier_gain", "stim_auc"]
    acc = {k: np.full(n_rep, np.nan) for k in keys}
    invalid = 0

    for r in range(n_rep):
        pick = rng.integers(0, len(parts), size=len(parts))
        sel = np.concatenate([idx_by_part[i] for i in pick])
        # Group by the ORIGINAL participant index `i`, never by the copy position:
        # every duplicate copy of one original participant must share a single
        # held-out group, otherwise one copy sits in another copy's source set and
        # the participant predicts itself. (Groups for unpicked participants are
        # simply empty; predict_fast tolerates that.)
        grp = np.concatenate([np.full(idx_by_part[i].size, i) for i in pick])
        y = td.label[sel]
        if y.min() == y.max() or len(np.unique(grp)) < 2:
            invalid += 1
            continue
        p_s, p_g, _ = predict_fast(grp, td.stim[sel], y, len(parts), td.n_stim)
        row = metric_pair(y, p_s, p_g)
        for k in keys:
            acc[k][r] = row[k]

    rows = []
    for k in keys:
        v = acc[k]
        ok = v[np.isfinite(v)]
        rows.append({
            "dataset": td.dataset, "task": td.task, "view": td.view.name,
            "repetition": td.view.repetition, "metric": k,
            "n_replicates_requested": n_rep,
            "n_replicates_valid": int(ok.size),
            "n_replicates_invalid": int(n_rep - ok.size),
            "ci95_low": float(np.percentile(ok, 2.5)) if ok.size else np.nan,
            "ci95_high": float(np.percentile(ok, 97.5)) if ok.size else np.nan,
            "bootstrap_mean": float(ok.mean()) if ok.size else np.nan,
        })
    out = pd.DataFrame(rows)
    out["n_all_class_degenerate_resamples"] = invalid
    out["bootstrap_variant"] = "sensitivity_refit_within_resample"
    return out


def permutation_null(td: TaskData, observed: dict, n_rep: int = N_PERMUTATION) -> dict:
    """Matched null: permute canonical-stimulus identity WITHIN each participant.

    Preserves every participant's trial count, label multiset and stimulus
    multiset exactly; destroys only the participant-internal pairing between
    stimulus identity and label, and hence the cross-subject alignment.
    The global-prior predictor is invariant under this null (it never uses
    stimulus identity), so its metrics are constant and recomputed once.
    """
    rng = np.random.default_rng(derived_seed("permutation", td.dataset, td.task,
                                             td.view.name, td.view.repetition))
    order = np.argsort(td.participant, kind="mergesort")
    part_sorted = td.participant[order]
    # group boundaries in the participant-sorted ordering
    part_codes = np.unique(part_sorted, return_inverse=True)[1]

    null_bits = np.full(n_rep, np.nan)
    null_gain = np.full(n_rep, np.nan)
    null_dba = np.full(n_rep, np.nan)

    # The global-prior predictor never uses stimulus identity, so it is invariant
    # under this null and is computed once.
    p_glob_fixed = predict_reference(td.group, td.stim, td.label)[1]
    glob = classification_metrics(td.label, p_glob_fixed, p_glob_fixed)
    ll_glob = glob["log_loss"]
    ba_glob = glob["balanced_accuracy"]

    for r in range(n_rep):
        keys = rng.random(part_codes.size)
        shuffled_positions = order[np.lexsort((keys, part_codes))]
        stim_perm = np.empty_like(td.stim)
        stim_perm[order] = td.stim[shuffled_positions]

        p_s, p_g, _ = predict_fast(td.group_idx, stim_perm, td.label, td.n_groups, td.n_stim)
        ll = float(-np.mean(td.label * np.log(p_s) + (1 - td.label) * np.log(1 - p_s)))
        yhat, _ = hard_predict(p_s, p_g)
        rec = []
        for c in (0, 1):
            pos = td.label == c
            rec.append(float((yhat[pos] == c).mean()) if pos.any() else np.nan)
        null_gain[r] = ll_glob - ll
        null_bits[r] = (ll_glob - ll) / math.log(2.0)
        null_dba[r] = 100.0 * (float(np.mean(rec)) - ba_glob)

    obs_bits = observed["bits_per_trial"]
    obs_dba = observed["delta_ba_pp"]
    return {
        "dataset": td.dataset, "task": td.task, "view": td.view.name,
        "repetition": td.view.repetition,
        "null_design": "within_participant_stimulus_identity_permutation",
        "n_permutations": n_rep,
        "observed_bits_per_trial": obs_bits,
        "observed_logloss_gain": observed["logloss_gain"],
        "observed_delta_ba_pp": obs_dba,
        "null_bits_per_trial_mean": float(np.nanmean(null_bits)),
        "null_bits_per_trial_sd": float(np.nanstd(null_bits, ddof=1)),
        "null_bits_per_trial_q95": float(np.nanpercentile(null_bits, 95)),
        "null_delta_ba_pp_mean": float(np.nanmean(null_dba)),
        "null_delta_ba_pp_sd": float(np.nanstd(null_dba, ddof=1)),
        "null_delta_ba_pp_q95": float(np.nanpercentile(null_dba, 95)),
        # one-sided empirical p-value, (#{null >= obs} + 1) / (n + 1)
        "p_one_sided_bits_per_trial": float((np.sum(null_bits >= obs_bits) + 1) / (n_rep + 1)),
        "p_one_sided_delta_ba_pp": float((np.sum(null_dba >= obs_dba) + 1) / (n_rep + 1)),
        "note": "Permutation test of association, NOT a causal test.",
    }, null_bits, null_dba


# --------------------------------------------------------------------------
# Subject-macro metrics
# --------------------------------------------------------------------------

def subject_macro(td: TaskData, p_stim: np.ndarray, p_glob: np.ndarray) -> dict:
    parts = np.unique(td.participant)
    ba_s, ba_g, acc_s, acc_g = [], [], [], []
    undefined = 0
    for p in parts:
        m = td.participant == p
        y = td.label[m]
        s = classification_metrics(y, p_stim[m], p_glob[m])
        g = classification_metrics(y, p_glob[m], p_glob[m])
        acc_s.append(s["accuracy"])
        acc_g.append(g["accuracy"])
        if np.isnan(s["balanced_accuracy"]):
            undefined += 1
        else:
            ba_s.append(s["balanced_accuracy"])
            ba_g.append(g["balanced_accuracy"])
    return {
        "subject_macro_ba_stimulus": float(np.mean(ba_s)) if ba_s else np.nan,
        "subject_macro_ba_global": float(np.mean(ba_g)) if ba_g else np.nan,
        "subject_macro_ba_valid_denominator": len(ba_s),
        "subject_macro_ba_undefined_participants": undefined,
        "subject_macro_accuracy_stimulus": float(np.mean(acc_s)),
        "subject_macro_accuracy_global": float(np.mean(acc_g)),
        "subject_macro_accuracy_denominator": len(acc_s),
        "n_participants": len(parts),
    }


# --------------------------------------------------------------------------
# Leakage / sanity tests
# --------------------------------------------------------------------------

def run_leakage_tests(tables: dict, task_data: dict, oof: pd.DataFrame) -> list[dict]:
    """Machine-readable PASS/FAIL suite.

    Each record carries `kind`:
      * `computed`        - an independent computation
      * `derived_from`    - a restatement of another record's computation
      * `code_inspection` - a structural assertion about the source, not a test
    Only `computed` records should be counted as independent evidence.
    """
    T: list[dict] = []

    def record(tid: str, name: str, passed: bool, detail: str,
               kind: str = "computed", derives_from: str | None = None) -> None:
        T.append({"test_id": tid, "name": name,
                  "result": "PASS" if passed else "FAIL",
                  "kind": kind, "derives_from": derives_from, "detail": detail})

    # 1 - source/target participant disjointness
    ok, det = True, []
    for key, td in task_data.items():
        for g in np.unique(td.group):
            tgt = set(td.participant[td.group == g])
            src = set(td.participant[td.group != g])
            if tgt & src:
                ok = False
                det.append(f"{key}:{g}")
    record("T01", "Source and target participant IDs disjoint in every fold", ok,
           f"checked {len(task_data)} dataset-task-views; violations={det or 'none'}")

    # 2/4/5/6 - target labels cannot influence predictions
    ok, det = True, []
    for key, td in task_data.items():
        base = predict_reference(td.group, td.stim, td.label)[0]
        rng = np.random.default_rng(derived_seed("labelcorrupt", key))
        for trial in range(3):
            corrupted = td.label.copy()
            for g in np.unique(td.group):
                m = td.group == g
                # replace this fold's target labels with pure noise
                corrupted_g = rng.integers(0, 2, size=int(m.sum())).astype(float)
                probe = td.label.copy()
                probe[m] = corrupted_g
                got = predict_reference(td.group, td.stim, probe)[0][m]
                if not np.allclose(got, base[m], rtol=0, atol=0):
                    ok = False
                    det.append(f"{key}:{g}:rep{trial}")
    record("T02", "Target labels are not accessed when fitting the predictor", ok,
           "per-fold target labels replaced with noise (3 independent draws per fold); "
           "out-of-fold probabilities bitwise unchanged")
    record("T04", "Post-hoc target-label changes do not change any predicted probability", ok,
           "RESTATEMENT of the T02 computation, read per held-out fold",
           kind="derived_from", derives_from="T02")
    record("T05", "No target-derived class prior is used", ok,
           "RESTATEMENT of T02: the global prior is invariant to target-label corruption",
           kind="derived_from", derives_from="T02")
    record("T06", "No target-derived stimulus statistics are used", ok,
           "RESTATEMENT of T02: the stimulus-conditioned prior is invariant to "
           "target-label corruption", kind="derived_from", derives_from="T02")

    # 3 - target labels only joined at evaluation (structural, not a computation)
    record("T03", "Target labels joined only at the evaluation stage", True,
           "STRUCTURAL ASSERTION, not a computation: predict_reference() reads label[] "
           "only through the boolean source mask `src = ~tgt`; target rows enter solely "
           "via stim[tgt]. The empirical evidence for this property is T02.",
           kind="code_inspection", derives_from="T02")

    # 7 - midpoint exclusions applied before any fold metric
    ok, det = True, []
    for name, tbl in tables.items():
        for task in TASKS:
            ret = tbl[tbl[f"{task}_retained"]]
            if (ret[f"{task}_score"] == MIDPOINT).any():
                ok = False
                det.append(f"{name}:{task}")
            if ret[f"{task}_binary"].isna().any():
                ok = False
                det.append(f"{name}:{task}:nan")
    record("T07", "Task-specific midpoint exclusion applied before fold metrics", ok,
           f"violations={det or 'none'}")

    # 8 / 9 - OOF coverage, checked on the EMITTED prediction frame
    def _coverage(view_name: str) -> tuple[bool, list[str], int]:
        good, bad, n_checked = True, [], 0
        sub = oof[oof["view"] == view_name]
        for (ds, task, rep), grp in sub.groupby(["dataset", "task", "repetition"]):
            n_checked += 1
            expected = int(tables[ds][f"{task}_retained"].sum())
            if grp["physical_trial_id"].duplicated().any():
                good = False
                bad.append(f"{ds}|{task}|rep{rep}:duplicate_prediction")
            if len(grp) != expected:
                good = False
                bad.append(f"{ds}|{task}|rep{rep}:{len(grp)}!={expected}")
            # each trial assigned to exactly one held-out group
            if grp.groupby("physical_trial_id")["held_out_group"].nunique().max() != 1:
                good = False
                bad.append(f"{ds}|{task}|rep{rep}:trial_in_two_folds")
            if grp["held_out_group"].nunique() < 2:
                good = False
                bad.append(f"{ds}|{task}|rep{rep}:degenerate_folds")
            # fallback rows must equal the global prior exactly
            fb = grp[grp["unseen_stimulus_fallback"]]
            if len(fb) and not np.array_equal(fb["p_stimulus_prior"].to_numpy(),
                                              fb["p_global_prior"].to_numpy()):
                good = False
                bad.append(f"{ds}|{task}|rep{rep}:fallback_not_global")
        return good, bad, n_checked

    ok, det, n_a = _coverage("A_LOPO")
    record("T08", "Each retained physical trial appears exactly once in the emitted "
                  "LOPO OOF frame", ok,
           f"checked {n_a} dataset-task conditions on "
           f"STIMULUS_PRIOR_OOF_PREDICTIONS; verified no duplicate prediction, exact "
           f"retained-count match, one held-out group per trial, and fallback rows "
           f"equal to the global prior; violations={det or 'none'}")

    ok, det, n_b = _coverage("B_SUBJECT_FOLD")
    record("T09", "View-B subject-fold OOF coverage exact in the emitted frame, no "
                  "duplicate predictions", ok,
           f"checked {n_b} dataset-task-repetition conditions; "
           f"violations={det or 'none'}")

    # 10 - DEJA-VU SESSIONS never split across source/target (session-level test)
    dv = tables["DEJAVU"]
    sess_of_trial = dv.set_index("physical_trial_id")["session_id"].to_dict()
    part_of_trial = dv.set_index("physical_trial_id")["participant_id"].to_dict()
    ok, det = True, []
    n_multi_checked = 0
    for key, td in task_data.items():
        if td.dataset != "DEJAVU":
            continue
        # full session key = participant + session, since session ids repeat across people
        skey = np.array([f"{part_of_trial[t]}/{sess_of_trial[t]}" for t in td.trial_id])
        for g in np.unique(td.group):
            tgt = set(skey[td.group == g])
            src = set(skey[td.group != g])
            crossing = tgt & src
            if crossing:
                ok = False
                det.append(f"{key}:{g}:{sorted(crossing)}")
    multi = dv.groupby("participant_id")["session_id"].nunique()
    multi_parts = sorted(multi[multi > 1].index)
    # confirm every multi-session participant's sessions land in one group together
    for key, td in task_data.items():
        if td.dataset != "DEJAVU":
            continue
        for p in multi_parts:
            m = td.participant == p
            if m.any():
                n_multi_checked += 1
                if len(np.unique(td.group[m])) != 1:
                    ok = False
                    det.append(f"{key}:{p}:sessions_in_different_groups")
    record("T10", "DEJA-VU participant sessions never cross source/target", ok,
           f"session-level test on participant/session keys: no session appears on both "
           f"sides of any fold; additionally verified that all sessions of each of the "
           f"{len(multi_parts)} multi-session participants {multi_parts} share one "
           f"held-out group ({n_multi_checked} participant-condition checks); "
           f"violations={det or 'none'}")

    # 11 - canonical stimulus stability / traceability
    ok, det = True, []
    for name, tbl in tables.items():
        if tbl["canonical_stimulus_id"].isna().any() or (tbl["canonical_stimulus_id"] == "").any():
            ok = False
            det.append(f"{name}:empty")
        if tbl.groupby("physical_trial_id")["canonical_stimulus_id"].nunique().max() != 1:
            ok = False
            det.append(f"{name}:unstable")
        if tbl["physical_trial_id"].duplicated().any():
            ok = False
            det.append(f"{name}:dup_trial")
    record("T11", "Canonical stimulus IDs stable and provenance-traceable", ok,
           f"violations={det or 'none'}")

    # 12 - determinism across two full recomputations
    ok, det = True, []
    for key, td in task_data.items():
        a = predict_reference(td.group, td.stim, td.label)
        b = predict_reference(td.group, td.stim, td.label)
        if not (np.array_equal(a[0], b[0]) and np.array_equal(a[1], b[1])
                and np.array_equal(a[2], b[2])):
            ok = False
            det.append(key)
    record("T12", "Predictions bitwise deterministic across two recomputations", ok,
           f"violations={det or 'none'}")

    # 12b - reference vs fast implementations agree
    ok, det = True, []
    for key, td in task_data.items():
        ra, rg, rf = predict_reference(td.group, td.stim, td.label)
        fa, fg, ff = predict_fast(td.group_idx, td.stim, td.label, td.n_groups, td.n_stim)
        if not (np.allclose(ra, fa, rtol=0, atol=1e-12)
                and np.allclose(rg, fg, rtol=0, atol=1e-12)
                and np.array_equal(rf, ff)):
            ok = False
            det.append(key)
        # also on permuted data, which is what the null actually uses
        rng = np.random.default_rng(derived_seed("impl-equiv", key))
        for _ in range(5):
            perm = td.stim.copy()
            for p in np.unique(td.participant):
                m = td.participant == p
                perm[m] = rng.permutation(perm[m])
            ra2 = predict_reference(td.group, perm, td.label)[0]
            fa2 = predict_fast(td.group_idx, perm, td.label, td.n_groups, td.n_stim)[0]
            if not np.allclose(ra2, fa2, rtol=0, atol=1e-12):
                ok = False
                det.append(f"{key}:perm")
    record("T13", "Reference (source-only loop) and fast (aggregate-minus-own) agree", ok,
           f"real + 5 permuted draws per dataset-task-view; violations={det or 'none'}")

    # 13 - toy unit tests
    toy = _toy_tests()
    for t in toy:
        T.append(t)
    return T


def _toy_tests() -> list[dict]:
    out = []

    # (a) label independent of stimulus -> no information.
    # Under this null the stimulus prior emits one blocked decision per stimulus,
    # so balanced accuracy has SD ~ 0.5/sqrt(n_stimuli), not 0.5/sqrt(n_trials).
    # n_stim=200 gives SD ~3.5 pp, making a 10 pp bound a genuine 3-sigma test.
    rng = np.random.default_rng(derived_seed("toy", "independent"))
    n_p, n_s = 40, 200
    part = np.repeat(np.arange(n_p), n_s)
    stim = np.tile(np.arange(n_s), n_p)
    label = rng.integers(0, 2, size=part.size).astype(float)
    ps, pg, _ = predict_reference(part.astype(str), stim, label)
    m = metric_pair(label, ps, pg)
    ba_tol_pp = 100.0 * 3.0 * 0.5 / math.sqrt(n_s)
    ok = abs(m["bits_per_trial"]) < 0.05 and abs(m["delta_ba_pp"]) < ba_tol_pp
    out.append({"test_id": "T14a", "name": "Toy: labels independent of stimulus -> ~zero information",
                "result": "PASS" if ok else "FAIL",
                "kind": "computed", "derives_from": None,
                "detail": f"bits_per_trial={m['bits_per_trial']:.4f} (|.|<0.05), "
                          f"delta_BA_pp={m['delta_ba_pp']:.2f} "
                          f"(|.|<{ba_tol_pp:.2f} = 3 sigma of the blocked null)"})

    # (b) stimulus perfectly determines label -> strong information
    truth = (np.arange(n_s) >= n_s // 2).astype(float)
    label = truth[stim]
    ps, pg, _ = predict_reference(part.astype(str), stim, label)
    m = metric_pair(label, ps, pg)
    ok = m["bits_per_trial"] > 0.7 and m["delta_ba_pp"] > 45.0 and m["stim_balanced_accuracy"] == 1.0
    out.append({"test_id": "T14b", "name": "Toy: stimulus perfectly determines label -> strong information",
                "result": "PASS" if ok else "FAIL",
                "kind": "computed", "derives_from": None,
                "detail": f"bits_per_trial={m['bits_per_trial']:.4f}, "
                          f"delta_BA_pp={m['delta_ba_pp']:.2f}, "
                          f"stim_BA={m['stim_balanced_accuracy']:.4f}"})

    # (c) unseen-stimulus fallback
    part2 = np.array(["p1", "p1", "p2", "p2", "p3", "p3"])
    stim2 = np.array([0, 1, 0, 1, 0, 2])          # stimulus 2 only ever seen by p3
    label2 = np.array([1.0, 1.0, 1.0, 0.0, 1.0, 0.0])
    ps, pg, fb = predict_reference(part2, stim2, label2)
    expect_fb = np.array([False, False, False, False, False, True])
    ok = np.array_equal(fb, expect_fb) and ps[5] == pg[5]
    out.append({"test_id": "T14c", "name": "Toy: unseen-stimulus fallback to source global prior",
                "result": "PASS" if ok else "FAIL",
                "kind": "computed", "derives_from": None,
                "detail": f"fallback_mask={fb.tolist()}, expected={expect_fb.tolist()}, "
                          f"p_stim[5]={ps[5]:.6f} p_global[5]={pg[5]:.6f}"})
    return out


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-root", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--bootstrap", type=int, default=N_BOOTSTRAP)
    ap.add_argument("--permutations", type=int, default=N_PERMUTATION)
    ap.add_argument("--verify-against", type=Path, default=None,
                    help="Output root of an independent full run; its derived-artefact "
                         "content hashes are compared against this run's and the result "
                         "is written into REPRODUCIBILITY_VALIDATION.json.")
    args = ap.parse_args()

    out = args.output_root
    (out / "derived").mkdir(parents=True, exist_ok=True)
    (out / "validation").mkdir(parents=True, exist_ok=True)
    (out / "provenance").mkdir(parents=True, exist_ok=True)

    print("[1/9] Reconstructing canonical trial tables ...", flush=True)
    tables = {
        "DEAP": build_deap_table(),
        "IDARE": build_idare_table(),
        "DEJAVU": build_dejavu_table(),
    }

    # ---------------- data authority validation ----------------
    validation = {"root_seed": ROOT_SEED, "datasets": {}}
    for name, tbl in tables.items():
        d = {
            "n_physical_trials": int(len(tbl)),
            "n_participants": int(tbl["participant_id"].nunique()),
            "n_sessions": int(tbl[["participant_id", "session_id"]].drop_duplicates().shape[0])
            if tbl["session_structure_present"].iloc[0] else None,
            "n_canonical_stimuli": int(tbl["canonical_stimulus_id"].nunique()),
            "physical_trial_id_unique": bool(not tbl["physical_trial_id"].duplicated().any()),
            "duplicate_participant_stimulus_pairs": int(
                tbl.duplicated(["participant_id", "canonical_stimulus_id"]).sum()
            ),
        }
        for task in TASKS:
            ret = tbl[f"{task}_retained"]
            d[task] = {
                "retained": int(ret.sum()),
                "dropped_midpoint": int((tbl[f"{task}_score"] == MIDPOINT).sum()),
                "missing_score": int(tbl[f"{task}_score"].isna().sum()),
                "low": int((tbl.loc[ret, f"{task}_binary"] == 0).sum()),
                "high": int((tbl.loc[ret, f"{task}_binary"] == 1).sum()),
                "n_stimuli_with_retained_trials": int(
                    tbl.loc[ret, "canonical_stimulus_id"].nunique()
                ),
                "n_participants_with_retained_trials": int(
                    tbl.loc[ret, "participant_id"].nunique()
                ),
            }
        validation["datasets"][name] = d

    # DEJA-VU cross-check against the frozen authority expectations
    dv = validation["datasets"]["DEJAVU"]
    dejavu_check = {
        "emotional_physical_trials": (dv["n_physical_trials"], DEJAVU_EXPECTED["emotional_physical_trials"]),
        "exact_videos": (dv["n_canonical_stimuli"], DEJAVU_EXPECTED["exact_videos"]),
        "participants": (dv["n_participants"], DEJAVU_EXPECTED["participants"]),
        "participant_sessions": (dv["n_sessions"], DEJAVU_EXPECTED["participant_sessions"]),
    }
    for task in TASKS:
        exp = DEJAVU_EXPECTED[task]
        for k in ("low", "high", "retained"):
            dejavu_check[f"{task}_{k}"] = (dv[task][k], exp[k])
        dejavu_check[f"{task}_drop"] = (dv[task]["dropped_midpoint"], exp["drop"])
    validation["dejavu_authority_crosscheck"] = {
        k: {"observed": o, "expected": e, "match": bool(o == e)}
        for k, (o, e) in dejavu_check.items()
    }
    validation["dejavu_authority_crosscheck_all_match"] = all(
        v["match"] for v in validation["dejavu_authority_crosscheck"].values()
    )
    # DEAP / I-DARE design facts (verified, not assumed)
    validation["deap_design_facts"] = {
        "subjects_is_32": tables["DEAP"]["participant_id"].nunique() == 32,
        "trials_per_subject_all_40": bool(
            (tables["DEAP"].groupby("participant_id").size() == 40).all()
        ),
        "canonical_stimuli_is_40": tables["DEAP"]["canonical_stimulus_id"].nunique() == 40,
        "fully_crossed_subject_by_stimulus": bool(
            len(tables["DEAP"]) == 32 * 40
            and tables["DEAP"].duplicated(["participant_id", "canonical_stimulus_id"]).sum() == 0
        ),
    }
    validation["idare_design_facts"] = {
        "subjects": int(tables["IDARE"]["participant_id"].nunique()),
        "canonical_stimuli": int(tables["IDARE"]["canonical_stimulus_id"].nunique()),
        "fully_crossed_subject_by_stimulus": bool(
            len(tables["IDARE"]) == tables["IDARE"]["participant_id"].nunique() * 32
            and tables["IDARE"].duplicated(["participant_id", "canonical_stimulus_id"]).sum() == 0
        ),
    }
    validation["dejavu_design_facts"] = {
        "fully_crossed_participant_by_stimulus": bool(
            len(tables["DEJAVU"])
            == tables["DEJAVU"]["participant_id"].nunique()
            * tables["DEJAVU"]["canonical_stimulus_id"].nunique()
        ),
        "trials_per_session": tables["DEJAVU"].groupby(
            ["participant_id", "session_id"]).size().value_counts().to_dict(),
        "sessions_per_participant": tables["DEJAVU"].groupby(
            "participant_id")["session_id"].nunique().value_counts().to_dict(),
    }

    # ---------------- build views and task data ----------------
    print("[2/9] Building evaluation views ...", flush=True)
    task_data: dict[str, TaskData] = {}
    for ds, tbl in tables.items():
        for view in build_views(ds, tbl):
            for task in TASKS:
                key = f"{ds}|{task}|{view.name}|rep{view.repetition}"
                task_data[key] = make_task_data(ds, tbl, task, view)

    # ---------------- Analyses A, B, C ----------------
    print("[3/9] Structural overlap, prior predictor, consistency ...", flush=True)
    overlap_rows, fold_rows, summary_rows, oof_rows, cons_rows, cons_sum_rows = [], [], [], [], [], []

    for key, td in sorted(task_data.items()):
        ov = structural_overlap(td)
        overlap_rows.append(ov)

        p_stim, p_glob, fallback = predict_reference(td.group, td.stim, td.label)
        yhat, n_ties = hard_predict(p_stim, p_glob)

        oof_rows.append(pd.DataFrame({
            "dataset": td.dataset, "task": td.task, "view": td.view.name,
            "repetition": td.view.repetition, "held_out_group": td.group,
            "participant_id": td.participant, "physical_trial_id": td.trial_id,
            "canonical_stimulus_id": td.stim_names[td.stim],
            "y_true": td.label.astype(int),
            "p_stimulus_prior": p_stim, "p_global_prior": p_glob,
            "yhat_stimulus_prior": yhat,
            "yhat_global_prior": hard_predict(p_glob, p_glob)[0],
            "unseen_stimulus_fallback": fallback,
        }))

        # per-fold metrics
        for g in np.unique(td.group):
            m = td.group == g
            row = {"dataset": td.dataset, "task": td.task, "view": td.view.name,
                   "repetition": td.view.repetition, "held_out_group": g}
            row.update(metric_pair(td.label[m], p_stim[m], p_glob[m]))
            row["n_fallback_trials"] = int(fallback[m].sum())
            fold_rows.append(row)

        # pooled OOF summary
        pooled = metric_pair(td.label, p_stim, p_glob)
        srow = {"dataset": td.dataset, "task": td.task, "view": td.view.name,
                "repetition": td.view.repetition}
        srow.update(pooled)
        srow.update(subject_macro(td, p_stim, p_glob))
        srow["n_fallback_trials"] = int(fallback.sum())
        srow["fallback_trial_fraction"] = float(fallback.mean())
        srow["trial_weighted_overlap_fraction_pooled"] = float(1.0 - fallback.mean())
        srow["unique_stimulus_overlap_fraction_mean_over_folds"] = float(
            ov["unique_stimulus_overlap_fraction"].mean())
        srow["n_participants"] = int(len(np.unique(td.participant)))
        srow["n_stimuli"] = int(td.n_stim)
        srow["class_balance_high_fraction"] = float(td.label.mean())
        srow["fold_provenance"] = td.view.provenance
        summary_rows.append(srow)

        if td.view.name == "A_LOPO":
            c = label_consistency(td)
            cons_rows.append(c)
            cons_sum_rows.append(consistency_summary(td, c))

    overlap = pd.concat(overlap_rows, ignore_index=True)
    folds_df = pd.DataFrame(fold_rows)
    summary = pd.DataFrame(summary_rows)
    oof = pd.concat(oof_rows, ignore_index=True)
    consistency = pd.concat(cons_rows, ignore_index=True)
    consistency_sum = pd.DataFrame(cons_sum_rows)

    # Primary-4 macro row (DEAP+I-DARE only; DEJA-VU deliberately excluded)
    p4 = summary[(summary["view"] == "A_LOPO") & (summary["dataset"].isin(PRIMARY_DATASETS))]
    if len(p4) == 4:
        macro = {"dataset": "PRIMARY4_MACRO_DEAP_IDARE_ONLY", "task": "both",
                 "view": "A_LOPO", "repetition": 0}
        for c in ("stim_balanced_accuracy", "glob_balanced_accuracy", "delta_ba_pp",
                  "stim_macro_f1", "stim_auc", "stim_log_loss", "glob_log_loss",
                  "logloss_gain", "bits_per_trial", "brier_gain",
                  "trial_weighted_overlap_fraction_pooled"):
            macro[c] = float(p4[c].mean())
        summary = pd.concat([summary, pd.DataFrame([macro])], ignore_index=True)

    # ---------------- Analysis D ----------------
    print("[4/9] Continuous rating prior ...", flush=True)
    cont = pd.DataFrame([continuous_prior(ds, tbl, task)
                         for ds, tbl in tables.items() for task in TASKS])

    # ---------------- Bootstrap ----------------
    print(f"[5/9] Cluster bootstrap ({args.bootstrap} replicates, primary + refit "
          f"sensitivity) ...", flush=True)
    boot_rows = []
    for key, td in sorted(task_data.items()):
        p_stim, p_glob, _ = predict_reference(td.group, td.stim, td.label)
        boot_rows.append(cluster_bootstrap(td, p_stim, p_glob, n_rep=args.bootstrap))
        if td.view.name == "A_LOPO":
            boot_rows.append(cluster_bootstrap_refit(td, n_rep=args.bootstrap))
    bootstrap = pd.concat(boot_rows, ignore_index=True)

    # ---------------- Permutation ----------------
    print(f"[6/9] Permutation null ({args.permutations} permutations) ...", flush=True)
    perm_rows = []
    for key, td in sorted(task_data.items()):
        p_stim, p_glob, _ = predict_reference(td.group, td.stim, td.label)
        observed = metric_pair(td.label, p_stim, p_glob)
        row, _, _ = permutation_null(td, observed, n_rep=args.permutations)
        perm_rows.append(row)
    permutation = pd.DataFrame(perm_rows)

    # ---------------- Leakage tests ----------------
    print("[7/9] Leakage and sanity tests ...", flush=True)
    tests = run_leakage_tests(tables, task_data, oof)
    n_fail = sum(1 for t in tests if t["result"] != "PASS")
    n_computed = sum(1 for t in tests if t["kind"] == "computed")
    n_derived = sum(1 for t in tests if t["kind"] == "derived_from")
    n_inspect = sum(1 for t in tests if t["kind"] == "code_inspection")

    # ---------------- Write outputs ----------------
    print("[8/9] Writing derived artefacts ...", flush=True)
    D = out / "derived"
    for name, tbl in tables.items():
        tbl.to_csv(D / f"CANONICAL_TRIAL_TABLE_{name}.csv.gz", index=False, compression="gzip")
    overlap.to_csv(D / "STIMULUS_OVERLAP_BY_FOLD.csv", index=False)
    oof.to_csv(D / "STIMULUS_PRIOR_OOF_PREDICTIONS.csv.gz", index=False, compression="gzip")
    folds_df.to_csv(D / "STIMULUS_PRIOR_METRICS_BY_FOLD.csv", index=False)
    summary.to_csv(D / "STIMULUS_PRIOR_SUMMARY.csv", index=False)
    consistency.to_csv(D / "STIMULUS_LABEL_CONSISTENCY.csv", index=False)
    consistency_sum.to_csv(D / "STIMULUS_LABEL_CONSISTENCY_SUMMARY.csv", index=False)
    bootstrap.to_csv(D / "STIMULUS_PRIOR_BOOTSTRAP_CI.csv", index=False)
    permutation.to_csv(D / "STIMULUS_PRIOR_PERMUTATION_SUMMARY.csv", index=False)
    cont.to_csv(D / "CONTINUOUS_RATING_PRIOR_SUMMARY.csv", index=False)

    # ---------------- Provenance / validation ----------------
    print("[9/9] Writing provenance and validation ...", flush=True)
    env = {
        "python_executable": sys.executable,
        "python_version": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": __import__("scipy").__version__,
        "h5py": __import__("h5py").__version__,
        "root_audit_seed": ROOT_SEED,
        "bootstrap_replicates": args.bootstrap,
        "permutation_replicates": args.permutations,
        "sklearn": "not used (metrics implemented in-module)",
        "repositories": {
            "main": git_info(MAIN_REPO),
            "dejavu_shared_authority": git_info(DEJAVU_SHARED_REPO),
            "dejavu_paper2_integration": git_info(DEJAVU_INTEGRATION_REPO),
        },
    }
    (out / "provenance" / "ENVIRONMENT.json").write_text(json.dumps(env, indent=2) + "\n")

    authority_files = {
        "deap_yaml": MAIN_REPO / "configs/data/deap.yaml",
        "deap_verified_stimulus_mapping": MAIN_REPO / "configs/data/deap_verified_stimulus_mapping.csv",
        "deap_subject_presentation_order": MAIN_REPO / "configs/data/deap_subject_presentation_order.csv",
        "deap_subject_folds": DEAP_SUBJECT_FOLDS,
        "idare_yaml": MAIN_REPO / "configs/data/idare.yaml",
        "idare_event_pairing": MAIN_REPO / "configs/data/idare_event_pairing.csv",
        "idare_valence_labels": IDARE_ROOT / "labels/Valence_SAM.csv",
        "idare_arousal_labels": IDARE_ROOT / "labels/Arousal_SAM.csv",
        "idare_stimuli_specifications": IDARE_ROOT / "metadata/Stimuli_Specifications.csv",
        "idare_subject_folds": IDARE_SUBJECT_FOLDS,
        "dejavu_primary_labels": DEJAVU_LABELS,
        "dejavu_fold_assignments": DEJAVU_FOLDS,
        "dejavu_label_active_pointer": DEJAVU_INTEGRATION_REPO / "docs/dejavu/PAPER2_DEJAVU_LABEL_ACTIVE_VERSION.md",
        "dejavu_label_state_v3": DEJAVU_INTEGRATION_REPO / "docs/dejavu/paper2-label-v3/DEJAVU_PAPER2_LABEL_STATE_v3.json",
        "dejavu_folds_state_v2": DEJAVU_INTEGRATION_REPO / "docs/dejavu/paper2-folds-v2/DEJAVU_PAPER2_FOLD_STATE_v2.json",
        "dejavu_content_state_v2": DEJAVU_INTEGRATION_REPO / "docs/dejavu/paper2-content-v2/DEJAVU_PAPER2_CONTENT_STATE_v2.json",
        "dejavu_admission_state_v3": DEJAVU_INTEGRATION_REPO / "docs/dejavu/paper2-admission-v3/DEJAVU_PAPER2_ADMISSION_STATE_v3.json",
        "loader_deap_inventory": MAIN_REPO / "src/mm_sage_dg/data/deap_inventory.py",
        "loader_idare_inventory": MAIN_REPO / "src/mm_sage_dg/data/idare_inventory.py",
        "loader_schemas": MAIN_REPO / "src/mm_sage_dg/data/schemas.py",
    }
    inputs = {
        "dataset_roots": {
            "DEAP": str(DEAP_ROOT), "IDARE": str(IDARE_ROOT),
            "DEJAVU": str(DEJAVU_SHARED_REPO),
        },
        "dejavu_pinned_commit_expected": DEJAVU_PINNED_COMMIT,
        "dejavu_pinned_commit_observed": git_info(DEJAVU_SHARED_REPO)["head"],
        "dejavu_pinned_commit_match":
            git_info(DEJAVU_SHARED_REPO)["head"] == DEJAVU_PINNED_COMMIT,
        "authority_files": {
            k: {"path": str(v), "exists": v.exists(),
                "sha256": sha256_file(v) if v.exists() else None}
            for k, v in authority_files.items()
        },
        "label_rule": "score < 5 -> LOW(0); score > 5 -> HIGH(1); score == 5 -> DROP (task-specific)",
        "smoothing": "Jeffreys/Beta(0.5,0.5): p = (n_HIGH + 0.5) / (n_total + 1.0)",
        "tie_policy": "p>0.5 HIGH; p<0.5 LOW; p==0.5 -> source global majority; "
                      "global also 0.5 -> LOW",
        "notes": [
            "configs/paths/local.yaml is absent from the working tree; only "
            "configs/paths/local.example.yaml (placeholder paths) exists. Dataset roots "
            "were resolved from the on-disk dataset locations used by the repository's "
            "own loaders and recorded explicitly here.",
            "DEJA-VU Paper-2 authority pointer documents live in the integration "
            "repository MM-SAGE-DG-dejavu-paper2, not under docs/dejavu/ of the "
            "parallel-universe worktree.",
        ],
    }
    (out / "provenance" / "INPUT_AUTHORITY.json").write_text(json.dumps(inputs, indent=2) + "\n")
    (out / "validation" / "DATA_AUTHORITY_VALIDATION.json").write_text(
        json.dumps(validation, indent=2, default=str) + "\n")
    (out / "validation" / "SOURCE_ONLY_LEAKAGE_TESTS.json").write_text(
        json.dumps({"n_assertions": len(tests),
                    "n_independent_computations": n_computed,
                    "n_restatements_of_another_computation": n_derived,
                    "n_code_inspection_assertions": n_inspect,
                    "counting_note": "Quote n_independent_computations, not n_assertions. "
                                     "T04/T05/T06 restate the single T02 computation and "
                                     "T03 is a structural assertion about the source whose "
                                     "empirical evidence is T02.",
                    "n_pass": len(tests) - n_fail,
                    "n_fail": n_fail,
                    "overall": "PASS" if n_fail == 0 else "FAIL",
                    "tests": tests}, indent=2) + "\n")

    # deterministic content hashes of every derived artefact
    repro = {
        "determinism_note": "All stochastic steps seeded from root seed 20260822 via "
                            "SHA-256 derived child seeds; predictions contain no stochastic step.",
        "content_sha256": {
            "CANONICAL_TRIAL_TABLE_DEAP": sha256_frame(tables["DEAP"]),
            "CANONICAL_TRIAL_TABLE_IDARE": sha256_frame(tables["IDARE"]),
            "CANONICAL_TRIAL_TABLE_DEJAVU": sha256_frame(tables["DEJAVU"]),
            "STIMULUS_OVERLAP_BY_FOLD": sha256_frame(overlap),
            "STIMULUS_PRIOR_OOF_PREDICTIONS": sha256_frame(oof),
            "STIMULUS_PRIOR_METRICS_BY_FOLD": sha256_frame(folds_df),
            "STIMULUS_PRIOR_SUMMARY": sha256_frame(summary),
            "STIMULUS_LABEL_CONSISTENCY": sha256_frame(consistency),
            "STIMULUS_LABEL_CONSISTENCY_SUMMARY": sha256_frame(consistency_sum),
            "STIMULUS_PRIOR_BOOTSTRAP_CI": sha256_frame(bootstrap),
            "STIMULUS_PRIOR_PERMUTATION_SUMMARY": sha256_frame(permutation),
            "CONTINUOUS_RATING_PRIOR_SUMMARY": sha256_frame(cont),
        },
    }
    # Machine-generated cross-process comparison. Run the whole pipeline into a
    # second output directory, then re-run with --verify-against <that dir>.
    if args.verify_against is not None:
        ref_path = Path(args.verify_against) / "validation" / "REPRODUCIBILITY_VALIDATION.json"
        ref = json.load(open(ref_path))["content_sha256"]
        mine = repro["content_sha256"]
        mismatched = sorted(k for k in mine if mine[k] != ref.get(k))
        missing = sorted(set(mine) - set(ref))
        repro["cross_process_rerun"] = {
            "description": "Content hashes of every derived artefact compared against an "
                           "independent full run of this same script in a separate Python "
                           "process writing to a different output directory.",
            "reference_run": str(Path(args.verify_against).resolve()),
            "reference_file": str(ref_path),
            "n_artefacts_compared": len(mine),
            "n_identical": len(mine) - len(mismatched),
            "mismatched_artefacts": mismatched,
            "artefacts_absent_from_reference": missing,
            "result": "PASS" if not (mismatched or missing) else "FAIL",
            "generated_by": "run_stimulus_prior_audit.py --verify-against",
        }
        repro["determinism_result"] = repro["cross_process_rerun"]["result"]
    else:
        repro["cross_process_rerun"] = None
        repro["determinism_result"] = "NOT_CHECKED_THIS_RUN"

    (out / "validation" / "REPRODUCIBILITY_VALIDATION.json").write_text(
        json.dumps(repro, indent=2) + "\n")

    final = {
        "audit_status": "PASS" if (n_fail == 0
                                   and validation["dejavu_authority_crosscheck_all_match"]
                                   and inputs["dejavu_pinned_commit_match"]) else "FAIL",
        "leakage_assertions_total": len(tests),
        "leakage_independent_computations": n_computed,
        "leakage_tests_failed": n_fail,
        "dejavu_authority_crosscheck_all_match": validation["dejavu_authority_crosscheck_all_match"],
        "dejavu_pinned_commit_match": inputs["dejavu_pinned_commit_match"],
        "bootstrap_replicates": args.bootstrap,
        "permutation_replicates": args.permutations,
        "dataset_task_conditions": 6,
        "views": ["A_LOPO", "B_SUBJECT_FOLD"],
    }
    (out / "validation" / "FINAL_AUDIT_VALIDATION.json").write_text(
        json.dumps(final, indent=2) + "\n")

    # ---------------- console headline ----------------
    print("\n=== HEADLINE (View A: leave-one-participant-out, pooled OOF) ===")
    head = summary[(summary["view"] == "A_LOPO")]
    cols = ["dataset", "task", "n", "stim_balanced_accuracy", "glob_balanced_accuracy",
            "delta_ba_pp", "stim_auc", "logloss_gain", "bits_per_trial", "brier_gain",
            "trial_weighted_overlap_fraction_pooled"]
    with pd.option_context("display.width", 200, "display.max_columns", 50):
        print(head[cols].to_string(index=False))
    print(f"\nleakage suite: {len(tests) - n_fail}/{len(tests)} assertions PASS "
          f"({n_computed} independent computations, {n_derived} restatements, "
          f"{n_inspect} code-inspection)")
    print(f"reproducibility: {repro['determinism_result']}")
    print(f"AUDIT_STATUS={final['audit_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
