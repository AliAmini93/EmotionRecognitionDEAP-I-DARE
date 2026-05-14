#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ROCA_DIR = ROOT / "docs" / "roca"
BASE_SCRIPT_05H = ROOT / "scripts" / "roca" / "05h_eeg_augmentation_matrix_smoke.py"


def load_aug_module():
    if not BASE_SCRIPT_05H.exists():
        raise FileNotFoundError(BASE_SCRIPT_05H)

    spec = importlib.util.spec_from_file_location("roca_05h_aug_full_loso", BASE_SCRIPT_05H)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module spec for {BASE_SCRIPT_05H}")

    module = importlib.util.module_from_spec(spec)
    sys.modules["roca_05h_aug_full_loso"] = module
    spec.loader.exec_module(module)
    return module


def main():
    aug = load_aug_module()

    # Redirect outputs so full LOSO does not overwrite smoke runs.
    aug.OUT_MD = ROCA_DIR / "eeg_gaussian10_full_loso_current.md"
    aug.OUT_JSON = ROCA_DIR / "eeg_gaussian10_full_loso_current.json"
    aug.OUT_PRED_CSV = ROCA_DIR / "eeg_gaussian10_full_loso_predictions_current.csv"
    aug.OUT_MAIN_CSV = ROCA_DIR / "eeg_gaussian10_full_loso_main_metrics_current.csv"
    aug.OUT_SUBSET_CSV = ROCA_DIR / "eeg_gaussian10_full_loso_subset_metrics_current.csv"
    aug.OUT_FOLD_CSV = ROCA_DIR / "eeg_gaussian10_full_loso_fold_summary_current.csv"
    aug.OUT_HISTORY_CSV = ROCA_DIR / "eeg_gaussian10_full_loso_history_current.csv"

    aug.MODEL_NAME = "eeg_bc_residual_huber_norm_gaussian10_full_loso"

    aug.main()


if __name__ == "__main__":
    main()
