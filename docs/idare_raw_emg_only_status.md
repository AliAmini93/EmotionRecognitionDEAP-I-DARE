# I-DARE Raw EMG-Only Smoke Status

## Status

Frozen after successful I-DARE raw EMG cache build and raw EMG-only training smokes.

This document records the raw EMG-only ablation status. The raw-vs-feature comparison has since been completed, and current next steps are governed by `docs/project_status_current.md`.

## Inputs

- Raw EMG cache: `.cache/idare_raw_emg_windows_2x10000_float32.npy`
- Raw EMG index: `.cache/idare_raw_emg_cache_index.csv`
- Cache build report:
  - `docs/idare_raw_emg_cache_build_report.md`
  - `docs/idare_raw_emg_cache_build_report.json`

## Raw EMG Cache

The full I-DARE raw EMG cache was built from raw I-DARE EMG HDF5/MAT files using the trial index.

- rows: `2016`
- subjects: `63`
- shape: `[2016, 2, 10000]`
- channels: `emg_ch1`, `emg_ch2`
- source sampling rate: `2000 Hz`
- window length: `5s`
- baseline source: preceding BSL event inferred from `event_index_0based - 1`
- baseline correction: subtract preceding BSL per-channel mean
- normalization: per-window global z-score after baseline correction
- NaN count: `0`
- Inf count: `0`

## Raw EMG-Only Training Smokes

Training script:

- `scripts/32_run_idare_raw_emg_smoke.py`

Reports:

- Valence:
  - `docs/idare_raw_emg_valence_training_smoke.md`
  - `docs/idare_raw_emg_valence_training_smoke.json`
  - `docs/idare_raw_emg_valence_training_smoke_predictions.csv`
- Arousal:
  - `docs/idare_raw_emg_arousal_training_smoke.md`
  - `docs/idare_raw_emg_arousal_training_smoke.json`
  - `docs/idare_raw_emg_arousal_training_smoke_predictions.csv`

## Valence Smoke Summary

Policy: `midpoint_as_high`

| Recipe | Runs | Final macro F1 | Final bal acc | Final acc | Threshold macro F1 | Threshold bal acc | Majority acc | One-class runs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ce_class_weighted | 2 | 0.4863 | 0.5000 | 0.5085 | 0.4945 | 0.5005 | 0.5753 | 0 |
| balanced_sampler_ce | 2 | 0.4607 | 0.5318 | 0.5199 | 0.5067 | 0.5290 | 0.5753 | 0 |

Interpretation:

- Raw valence did not clearly beat majority accuracy in these smokes.
- Balanced sampler improved balanced accuracy but had unstable prediction bias across folds.
- Threshold sweep helped macro F1 for `balanced_sampler_ce`, but this should be treated as diagnostic only.

## Arousal Smoke Summary

Policy: `midpoint_as_high`

| Recipe | Runs | Final macro F1 | Final bal acc | Final acc | Threshold macro F1 | Threshold bal acc | Majority acc | One-class runs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ce_class_weighted | 2 | 0.4131 | 0.5006 | 0.5170 | 0.4761 | 0.5086 | 0.5625 | 0 |
| balanced_sampler_ce | 2 | 0.4464 | 0.4969 | 0.4787 | 0.5187 | 0.5294 | 0.5625 | 0 |

Interpretation:

- Raw arousal is weaker than feature-level arousal in the first smoke.
- Balanced sampler has better threshold-swept macro F1, but the needed thresholds are high and indicate calibration instability.
- No one-class collapse occurred, but prediction bias is still visible.

## Current Raw-vs-Feature Direction

Compared with the frozen I-DARE EMG feature-only smoke:

- Feature-level valence:
  - ce_class_weighted final macro F1: `0.5004`
  - balanced_sampler_ce final macro F1: `0.4776`
- Raw valence:
  - ce_class_weighted final macro F1: `0.4863`
  - balanced_sampler_ce final macro F1: `0.4607`

Feature-level valence is slightly ahead in macro F1.

- Feature-level arousal:
  - ce_class_weighted final macro F1: `0.5223`
  - balanced_sampler_ce final macro F1: `0.5065`
- Raw arousal:
  - ce_class_weighted final macro F1: `0.4131`
  - balanced_sampler_ce final macro F1: `0.4464`

Feature-level arousal is clearly ahead in these smokes.

## Decision

For the paper mainline, keep I-DARE EMG as feature-level EMG first.

Raw EMG-only remains useful as an ablation, but current smoke evidence does not justify making raw EMG the main EMG representation.

## Next Step / Current Roadmap Note

The compact raw-vs-feature EMG-only comparison report has since been created.

Current roadmap:

1. Keep raw EMG-only as an ablation, not the main EMG path.
2. Keep feature-level EMG as the current I-DARE EMG mainline.
3. Do not move directly to EEG+EMG fusion from this status document.
4. Before fusion, directly compare the EEG/EMG single-modality baselines and BSL-stats ablations, then update the central roadmap if the next allowed step changes.
