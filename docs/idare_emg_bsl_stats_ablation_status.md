# I-DARE EMG Response + BSL Stats Ablation Status

## Status

Frozen after successful smoke runs for both valence and arousal.

This document closes the current EMG-only BSL-stats phase. It does not start EEG+EMG fusion and does not introduce a full paired BSL/STIM neural model.

## What Was Tested

- Main EMG input: existing baseline-corrected `STIM-BSL` EMG feature cache.
- Sidecar input: compact preceding-BSL EMG summary stats.
- Model: `TinyEMGBSLStatsMLP(input_dim=44, hidden_dim=64)`.
- Label policy: `midpoint_as_high`.
- Runs: 4 per task, 2 recipes x 2 folds.
- Recipes: `ce_class_weighted`, `balanced_sampler_ce`.

## Sources

- valence: `docs/idare_emg_bsl_stats_valence_ablation_smoke.json`
- arousal: `docs/idare_emg_bsl_stats_arousal_ablation_smoke.json`

## Aggregate Results

| Task | Recipe | Runs | Final macro F1 | Final bal acc | Final acc | Threshold macro F1 | Threshold bal acc | Threshold | Majority acc | One-class runs |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| valence | balanced_sampler_ce | 2 | 0.5069 | 0.5169 | 0.5085 | 0.5069 | 0.5169 | 0.5000 | 0.5753 | 0 |
| valence | ce_class_weighted | 2 | 0.5073 | 0.5136 | 0.5085 | 0.5073 | 0.5136 | 0.5000 | 0.5753 | 0 |
| arousal | balanced_sampler_ce | 2 | 0.5227 | 0.5270 | 0.5270 | 0.5333 | 0.5500 | 0.5250 | 0.5625 | 0 |
| arousal | ce_class_weighted | 2 | 0.5319 | 0.5344 | 0.5384 | 0.5319 | 0.5344 | 0.5000 | 0.5625 | 0 |

## Best Rows

| Task | Metric | Recipe | Value |
|---|---|---|---:|
| valence | best_final_macro_f1 | ce_class_weighted | 0.5073 |
| valence | best_final_balanced_accuracy | balanced_sampler_ce | 0.5169 |
| valence | best_threshold_macro_f1 | ce_class_weighted | 0.5073 |
| valence | best_threshold_balanced_accuracy | balanced_sampler_ce | 0.5169 |
| arousal | best_final_macro_f1 | ce_class_weighted | 0.5319 |
| arousal | best_final_balanced_accuracy | ce_class_weighted | 0.5344 |
| arousal | best_threshold_macro_f1 | balanced_sampler_ce | 0.5333 |
| arousal | best_threshold_balanced_accuracy | balanced_sampler_ce | 0.5500 |

## Interpretation

- The EMG BSL-stats sidecar path ran successfully for both valence and arousal.
- No final one-class collapse was observed in the aggregate rows.
- Valence improved modestly over the earlier EMG feature-only smoke in final macro F1, but the gain is small and should be treated as smoke-level evidence.
- Arousal is the cleaner result: `ce_class_weighted` reached the best final macro F1 and final balanced accuracy, while `balanced_sampler_ce` reached the best threshold balanced accuracy.
- Threshold behavior is stable enough for smoke work, but this should not automatically replace the current EMG mainline without direct comparison to the prior `STIM-BSL`-only EMG feature baseline.

## Phase Decision

- Current EMG BSL-stats phase: complete and frozen.
- Do not start fusion in this chat.
- Do not implement full `model(BSL, STIM, STIM-BSL)` yet.
- Before any future architecture decision, compare this sidecar ablation against the existing `STIM-BSL`-only EMG feature baseline.
- EEG and EMG BSL-stats sidecar ablations are now both available as controlled I-DARE-aware ablations.
