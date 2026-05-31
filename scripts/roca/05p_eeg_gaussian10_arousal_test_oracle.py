#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ROCA_DIR = ROOT / "docs" / "roca"
BASE_SCRIPT = ROOT / "scripts" / "roca" / "05o_eeg_oracle_checkpoint_base.py"


def load_oracle_base():
    if not BASE_SCRIPT.exists():
        raise FileNotFoundError(BASE_SCRIPT)

    spec = importlib.util.spec_from_file_location("roca_05o_oracle_base_arousal", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module spec for {BASE_SCRIPT}")

    module = importlib.util.module_from_spec(spec)
    sys.modules["roca_05o_oracle_base_arousal"] = module
    spec.loader.exec_module(module)
    return module


def remove_arg_with_value(argv: list[str], option: str) -> list[str]:
    out = []
    skip_next = False
    for item in argv:
        if skip_next:
            skip_next = False
            continue
        if item == option:
            skip_next = True
            continue
        if item.startswith(option + "="):
            continue
        out.append(item)
    return out


def main():
    oracle = load_oracle_base()

    oracle.OUT_MD = ROCA_DIR / "eeg_gaussian10_arousal_test_oracle_current.md"
    oracle.OUT_JSON = ROCA_DIR / "eeg_gaussian10_arousal_test_oracle_current.json"
    oracle.OUT_PRED_CSV = ROCA_DIR / "eeg_gaussian10_arousal_test_oracle_predictions_current.csv"
    oracle.OUT_MAIN_CSV = ROCA_DIR / "eeg_gaussian10_arousal_test_oracle_main_metrics_current.csv"
    oracle.OUT_SUBSET_CSV = ROCA_DIR / "eeg_gaussian10_arousal_test_oracle_subset_metrics_current.csv"
    oracle.OUT_FOLD_CSV = ROCA_DIR / "eeg_gaussian10_arousal_test_oracle_fold_summary_current.csv"
    oracle.OUT_HISTORY_CSV = ROCA_DIR / "eeg_gaussian10_arousal_test_oracle_history_current.csv"

    oracle.MODEL_NAME = "eeg_bc_residual_huber_norm_gaussian10_arousal_test_oracle"

    argv = sys.argv[1:]

    argv = remove_arg_with_value(argv, "--target")
    argv = remove_arg_with_value(argv, "--configs")

    argv = ["--target", "arousal"] + argv
    argv += ["--configs", "gaussian_0p10"]

    if "--oracle-test-checkpoint-selection" not in argv:
        argv += ["--oracle-test-checkpoint-selection"]

    sys.argv = [sys.argv[0]] + argv
    oracle.main()


if __name__ == "__main__":
    main()
