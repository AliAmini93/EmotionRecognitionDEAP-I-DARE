# I-DARE EEG Response + BSL Stats Ablation Status

## Status

Frozen after successful smoke runs for both valence and arousal.

This document closes the current EEG-only BSL-stats phase. It does not start EEG+EMG fusion and does not introduce a full paired BSL/STIM neural model.

Important scope note: this status document covers the EEG-only BSL-stats phase. The EMG BSL-stats counterpart was completed and frozen later as a separate EMG-only phase in `docs/idare_emg_bsl_stats_ablation_status.md`.

## What Was Tested

- Main EEG input: existing baseline-corrected `STIM-BSL` EEG response cache.
- Sidecar input: compact preceding-BSL EEG summary stats.
- Model: `TinyEEGBSLStatsNet(eeg=[32,640], bsl_stats_dim=229)`.
- Label policy: `midpoint_as_high`.
- Runs: 4 per task, 2 recipes x 2 folds.
- Recipes: `ce_class_weighted`, `balanced_sampler_ce`.

## Sources

- valence: `docs/idare_eeg_bsl_stats_valence_ablation_smoke.json`
- arousal: `docs/idare_eeg_bsl_stats_arousal_ablation_smoke.json`

## Aggregate Results

| Task | Recipe | Runs | Final macro F1 | Final bal acc | Final acc | Threshold macro F1 | Threshold bal acc | Threshold | Majority acc | One-class runs |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| valence | balanced_sampler_ce | 2 | 0.4395 | 0.5231 | 0.5412 | 0.5380 | 0.5402 | 0.5000 | 0.5753 | 0 |
| valence | ce_class_weighted | 2 | 0.4801 | 0.5191 | 0.5526 | 0.5187 | 0.5244 | 0.5750 | 0.5753 | 0 |
| arousal | balanced_sampler_ce | 2 | 0.4880 | 0.5099 | 0.4915 | 0.5238 | 0.5244 | 0.6750 | 0.5625 | 0 |
| arousal | ce_class_weighted | 2 | 0.4943 | 0.5344 | 0.5369 | 0.5565 | 0.5575 | 0.5250 | 0.5625 | 0 |

## Best Rows

| Task | Metric | Recipe | Value |
|---|---|---|---:|
| valence | best_final_macro_f1 | ce_class_weighted | 0.4801 |
| valence | best_final_balanced_accuracy | balanced_sampler_ce | 0.5231 |
| valence | best_threshold_macro_f1 | balanced_sampler_ce | 0.5380 |
| valence | best_threshold_balanced_accuracy | balanced_sampler_ce | 0.5402 |
| arousal | best_final_macro_f1 | ce_class_weighted | 0.4943 |
| arousal | best_final_balanced_accuracy | ce_class_weighted | 0.5344 |
| arousal | best_threshold_macro_f1 | ce_class_weighted | 0.5565 |
| arousal | best_threshold_balanced_accuracy | ce_class_weighted | 0.5575 |

## Interpretation

- The BSL-stats sidecar path ran successfully for both valence and arousal.
- No final one-class collapse was observed in the aggregate rows.
- Valence shows useful threshold-sweep gains, especially for `balanced_sampler_ce`, but final macro F1 remains modest.
- Arousal shows the strongest threshold result with `ce_class_weighted`.
- Threshold gains suggest calibration sensitivity, so this should not automatically replace the current EEG mainline without direct comparison to the prior `STIM-BSL`-only EEG smoke.

## Phase Decision

- Current EEG BSL-stats phase: complete and frozen.
- Do not start fusion in this chat.
- Do not implement full `model(BSL, STIM, STIM-BSL)` yet.
- Before any future architecture decision, compare this sidecar ablation against the existing `STIM-BSL`-only EEG baseline.
- The EMG BSL-stats counterpart has since been completed and frozen separately; both EEG and EMG BSL-stats ablations should be compared against their own `STIM-BSL`-only baselines before fusion.
