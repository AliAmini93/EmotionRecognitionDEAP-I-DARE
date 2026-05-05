"""
I-DARE dataset loader.

This module loads the I-DARE trial index produced by:

    scripts/06_build_idare_trial_index.py

and extracts fixed-size EEG/EMG windows for model validation and later training.

Design decisions:
- Main protocol subjects: 63 common EEG+EMG subjects.
- Main trial unit: one emotional STIM_* event.
- Signal slicing: start at event_begin and extract exactly 5.0 seconds.
- EEG source sampling rate: 512 Hz.
- EEG model sampling rate: 128 Hz.
- EEG output shape: (32, 640).
- EMG source sampling rate: 2000 Hz.
- EMG output shape: (2, 10000).
- Label policies are configurable:
  - discard_midpoint: score < 5 -> 0, score > 5 -> 1, score == 5 dropped.
  - midpoint_as_low: score <= 5 -> 0, score > 5 -> 1.
  - midpoint_as_high: score < 5 -> 0, score >= 5 -> 1.

No training code is included here.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal
import warnings

import h5py
import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset


TaskName = Literal["valence", "arousal"]
ReturnMode = Literal["eeg", "emg", "both"]
LabelPolicy = Literal["discard_midpoint", "midpoint_as_low", "midpoint_as_high"]


@dataclass(frozen=True)
class IDAREPaths:
    """Filesystem paths used by the I-DARE loader."""

    project_root: Path = Path("/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE")
    idare_root: Path = Path("/mnt/HDD/AliWorks/I-DARE")

    @property
    def trial_index_csv(self) -> Path:
        return self.project_root / ".cache" / "idare_trial_index.csv"


def _ensure_path(path: Path, description: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"{description} not found: {path}")


def normalize_label_policy(
    label_policy: LabelPolicy = "discard_midpoint",
    *,
    keep_score5: bool | None = None,
) -> LabelPolicy:
    """Normalize label policy while preserving backward compatibility.

    Previous code exposed `keep_score5`, but the cached trial-index labels made
    score==5 effectively dropped anyway. New code should use `label_policy`.

    Mapping for legacy calls:
    - keep_score5=False -> discard_midpoint
    - keep_score5=True  -> midpoint_as_low
    """
    valid = {"discard_midpoint", "midpoint_as_low", "midpoint_as_high"}
    if label_policy not in valid:
        raise ValueError(f"Unsupported label_policy={label_policy!r}; expected one of {sorted(valid)}")

    if keep_score5 is None:
        return label_policy

    warnings.warn(
        "`keep_score5` is deprecated. Use `label_policy` instead. "
        "keep_score5=False maps to discard_midpoint; keep_score5=True maps to midpoint_as_low.",
        DeprecationWarning,
        stacklevel=2,
    )

    if keep_score5 is False:
        return "discard_midpoint"
    return "midpoint_as_low"


def labels_from_scores(scores: pd.Series, *, label_policy: LabelPolicy) -> pd.Series:
    """Convert numeric SAM scores to binary labels under a selected policy."""
    score_values = pd.to_numeric(scores, errors="coerce")

    if label_policy == "discard_midpoint":
        labels = pd.Series(np.nan, index=score_values.index, dtype="float64")
        labels.loc[score_values < 5] = 0
        labels.loc[score_values > 5] = 1
        return labels

    if label_policy == "midpoint_as_low":
        labels = pd.Series(np.nan, index=score_values.index, dtype="float64")
        labels.loc[score_values <= 5] = 0
        labels.loc[score_values > 5] = 1
        return labels

    if label_policy == "midpoint_as_high":
        labels = pd.Series(np.nan, index=score_values.index, dtype="float64")
        labels.loc[score_values < 5] = 0
        labels.loc[score_values >= 5] = 1
        return labels

    raise ValueError(f"Unsupported label_policy: {label_policy!r}")


def build_idare_dataframe(
    *,
    task: TaskName,
    paths: IDAREPaths | None = None,
    include_subjects: list[int] | None = None,
    label_policy: LabelPolicy = "discard_midpoint",
    keep_score5: bool | None = None,
) -> pd.DataFrame:
    """Load and filter the cached I-DARE trial index."""
    if task not in {"valence", "arousal"}:
        raise ValueError(f"Unsupported task: {task!r}")

    label_policy = normalize_label_policy(label_policy, keep_score5=keep_score5)

    paths = paths or IDAREPaths()
    _ensure_path(paths.trial_index_csv, "I-DARE trial index CSV")

    df = pd.read_csv(paths.trial_index_csv)

    score_col = f"{task}_score"
    discard_col = f"{task}_is_discard_score5"

    required_cols = [
        "subject_id",
        "stimulus_id",
        "eeg_file",
        "emg_file",
        "eeg_begin_raw",
        "emg_begin_raw",
        "eeg_fs",
        "emg_fs",
        score_col,
    ]

    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise KeyError(f"Trial index is missing required columns: {missing}")

    if include_subjects is not None:
        subject_set = set(int(s) for s in include_subjects)
        df = df[df["subject_id"].astype(int).isin(subject_set)].copy()

    df["score"] = pd.to_numeric(df[score_col], errors="coerce")
    df["label"] = labels_from_scores(df["score"], label_policy=label_policy)
    df["label_policy"] = label_policy

    if discard_col in df.columns:
        df["is_score5"] = df[discard_col].astype(bool)
    else:
        df["is_score5"] = df["score"] == 5

    df = df[df["label"].notna()].copy()
    df["label"] = df["label"].astype(int)

    df = df.sort_values(["subject_id", "event_index_1based"]).reset_index(drop=True)
    return df


@lru_cache(maxsize=8)
def _load_hdf5_data_array(file_path: str) -> tuple[np.ndarray, float]:
    """Load a single I-DARE HDF5 .mat data array.

    The raw h5py orientation observed in audit/probe reports is time x channels.
    The returned array keeps that orientation: shape (time, channels).
    """
    path = Path(file_path)
    _ensure_path(path, "I-DARE .mat file")

    with h5py.File(path, "r") as handle:
        top_keys = [k for k in handle.keys() if not k.startswith("#")]
        if len(top_keys) != 1:
            raise ValueError(f"Expected exactly one subject group in {path}, got: {top_keys}")

        group = handle[top_keys[0]]
        data = np.asarray(group["data"], dtype=np.float32)
        fs = float(np.asarray(group["Fs"]).squeeze())

    if data.ndim != 2:
        raise ValueError(f"Expected 2D data in {path}, got shape {data.shape}")

    return data, fs


def _slice_fixed_seconds(
    data_time_x_channels: np.ndarray,
    *,
    begin_raw: float,
    fs: float,
    seconds: float,
) -> np.ndarray:
    """Slice exactly `seconds` from `begin_raw` using Python half-open indexing."""
    start = int(round(float(begin_raw)))
    n_samples = int(round(float(fs) * float(seconds)))
    stop = start + n_samples

    if start < 0:
        raise ValueError(f"Negative start index: {start}")
    if stop > data_time_x_channels.shape[0]:
        raise ValueError(
            f"Slice exceeds data length: start={start}, stop={stop}, "
            f"data_len={data_time_x_channels.shape[0]}"
        )

    window = data_time_x_channels[start:stop, :]
    if window.shape[0] != n_samples:
        raise ValueError(f"Expected {n_samples} samples, got {window.shape[0]}")

    return window


def _downsample_eeg_512_to_128(eeg_time_x_channels: np.ndarray) -> np.ndarray:
    """Downsample EEG from 512 Hz to 128 Hz by taking every 4th sample."""
    if eeg_time_x_channels.shape[0] != 2560:
        raise ValueError(
            f"Expected 2560 EEG samples before downsampling, "
            f"got {eeg_time_x_channels.shape[0]}"
        )

    return eeg_time_x_channels[::4, :]


def _standardize_per_channel(x_channels_x_time: np.ndarray, eps: float = 1e-6) -> np.ndarray:
    """Per-window, per-channel z-normalization."""
    x = x_channels_x_time.astype(np.float32, copy=False)
    mean = x.mean(axis=1, keepdims=True)
    std = x.std(axis=1, keepdims=True)
    return (x - mean) / np.maximum(std, eps)


class IDARETrialDataset(Dataset):
    """PyTorch dataset for I-DARE 5-second STIM trials."""

    def __init__(
        self,
        *,
        task: TaskName,
        paths: IDAREPaths | None = None,
        return_mode: ReturnMode = "both",
        include_subjects: list[int] | None = None,
        label_policy: LabelPolicy = "discard_midpoint",
        keep_score5: bool | None = None,
        seconds: float = 5.0,
        eeg_channels: int = 32,
        standardize_eeg: bool = True,
        standardize_emg: bool = True,
        cache_files: bool = True,
    ) -> None:
        if return_mode not in {"eeg", "emg", "both"}:
            raise ValueError(f"Unsupported return_mode: {return_mode!r}")

        self.paths = paths or IDAREPaths()
        self.task = task
        self.label_policy = normalize_label_policy(label_policy, keep_score5=keep_score5)
        self.return_mode = return_mode
        self.seconds = float(seconds)
        self.eeg_channels = int(eeg_channels)
        self.standardize_eeg = bool(standardize_eeg)
        self.standardize_emg = bool(standardize_emg)
        self.cache_files = bool(cache_files)

        self.df = build_idare_dataframe(
            task=task,
            paths=self.paths,
            include_subjects=include_subjects,
            label_policy=self.label_policy,
        )

        if self.df.empty:
            raise ValueError("Filtered I-DARE dataframe is empty.")

    def __len__(self) -> int:
        return len(self.df)

    def _load_data(self, file_path: str) -> tuple[np.ndarray, float]:
        if self.cache_files:
            return _load_hdf5_data_array(str(file_path))

        _load_hdf5_data_array.cache_clear()
        return _load_hdf5_data_array(str(file_path))

    def _extract_eeg(self, row: pd.Series) -> np.ndarray:
        data, fs = self._load_data(str(row["eeg_file"]))

        if abs(fs - 512.0) > 1e-6:
            raise ValueError(f"Expected I-DARE EEG fs=512Hz, got {fs}")

        window_time_x_channels = _slice_fixed_seconds(
            data,
            begin_raw=float(row["eeg_begin_raw"]),
            fs=fs,
            seconds=self.seconds,
        )

        if window_time_x_channels.shape[1] < self.eeg_channels:
            raise ValueError(
                f"Requested {self.eeg_channels} EEG channels but file only has "
                f"{window_time_x_channels.shape[1]}"
            )

        window_time_x_channels = window_time_x_channels[:, : self.eeg_channels]
        window_time_x_channels = _downsample_eeg_512_to_128(window_time_x_channels)

        eeg = window_time_x_channels.T.astype(np.float32, copy=False)

        if eeg.shape != (self.eeg_channels, 640):
            raise ValueError(f"Expected EEG shape {(self.eeg_channels, 640)}, got {eeg.shape}")

        if self.standardize_eeg:
            eeg = _standardize_per_channel(eeg)

        return eeg

    def _extract_emg(self, row: pd.Series) -> np.ndarray:
        data, fs = self._load_data(str(row["emg_file"]))

        if abs(fs - 2000.0) > 1e-6:
            raise ValueError(f"Expected I-DARE EMG fs=2000Hz, got {fs}")

        window_time_x_channels = _slice_fixed_seconds(
            data,
            begin_raw=float(row["emg_begin_raw"]),
            fs=fs,
            seconds=self.seconds,
        )

        emg = window_time_x_channels.T.astype(np.float32, copy=False)

        if emg.shape != (2, 10000):
            raise ValueError(f"Expected EMG shape {(2, 10000)}, got {emg.shape}")

        if self.standardize_emg:
            emg = _standardize_per_channel(emg)

        return emg

    def __getitem__(self, index: int) -> dict[str, Any]:
        row = self.df.iloc[int(index)]

        item: dict[str, Any] = {
            "label": torch.tensor(int(row["label"]), dtype=torch.long),
            "score": float(row["score"]),
            "label_policy": self.label_policy,
            "subject_id": int(row["subject_id"]),
            "stimulus_id": str(row["stimulus_id"]),
            "event_index_1based": int(row["event_index_1based"]),
            "task": self.task,
        }

        if self.return_mode in {"eeg", "both"}:
            item["eeg"] = torch.from_numpy(self._extract_eeg(row))

        if self.return_mode in {"emg", "both"}:
            item["emg"] = torch.from_numpy(self._extract_emg(row))

        return item


def summarize_dataset(dataset: IDARETrialDataset, *, n_items_to_check: int = 8) -> dict[str, Any]:
    """Return a lightweight validation summary for a dataset instance."""
    n_items = min(int(n_items_to_check), len(dataset))
    checked: list[dict[str, Any]] = []

    for idx in range(n_items):
        item = dataset[idx]
        row_summary: dict[str, Any] = {
            "index": idx,
            "subject_id": item["subject_id"],
            "stimulus_id": item["stimulus_id"],
            "score": float(item["score"]),
            "label": int(item["label"].item()),
            "label_policy": item["label_policy"],
        }

        if "eeg" in item:
            eeg = item["eeg"]
            row_summary["eeg_shape"] = list(eeg.shape)
            row_summary["eeg_isfinite"] = bool(torch.isfinite(eeg).all().item())
            row_summary["eeg_mean"] = float(eeg.mean().item())
            row_summary["eeg_std"] = float(eeg.std().item())

        if "emg" in item:
            emg = item["emg"]
            row_summary["emg_shape"] = list(emg.shape)
            row_summary["emg_isfinite"] = bool(torch.isfinite(emg).all().item())
            row_summary["emg_mean"] = float(emg.mean().item())
            row_summary["emg_std"] = float(emg.std().item())

        checked.append(row_summary)

    label_counts = dataset.df["label"].value_counts(dropna=False).sort_index().to_dict()
    subject_count = int(dataset.df["subject_id"].nunique())

    return {
        "task": dataset.task,
        "label_policy": dataset.label_policy,
        "return_mode": dataset.return_mode,
        "n_rows": len(dataset),
        "n_subjects": subject_count,
        "label_counts": {str(k): int(v) for k, v in label_counts.items()},
        "checked_items": checked,
    }
