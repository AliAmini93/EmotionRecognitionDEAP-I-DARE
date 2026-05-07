# I-DARE Single-Modality BSL-stats vs Baseline Comparison

## Status

Frozen documentation comparison.

This report compares BSL-stats sidecar smokes against corresponding single-modality baselines for I-DARE EEG and EMG.

This is **not** a final LOSO result and does **not** authorize EEG+EMG fusion by itself.

## Purpose

The purpose is to close the current roadmap comparison step before any future architecture or fusion decision:

- EEG `STIM-BSL`-only standardized baseline vs EEG `STIM-BSL + BSL-stats` sidecar.
- EMG feature-only baseline vs EMG feature + BSL-stats sidecar.

## Sources

| Role | Source |
|---|---|
| EEG baseline valence | `docs/idare_eeg_stim_bsl_only_valence_standardized_smoke.json` |
| EEG baseline arousal | `docs/idare_eeg_stim_bsl_only_arousal_standardized_smoke.json` |
| EEG BSL-stats valence | `docs/idare_eeg_bsl_stats_valence_ablation_smoke.json` |
| EEG BSL-stats arousal | `docs/idare_eeg_bsl_stats_arousal_ablation_smoke.json` |
| EMG baseline valence | `docs/idare_emg_feature_valence_training_smoke.md` |
| EMG baseline arousal | `docs/idare_emg_feature_arousal_training_smoke.md` |
| EMG BSL-stats valence | `docs/idare_emg_bsl_stats_valence_ablation_smoke.json` |
| EMG BSL-stats arousal | `docs/idare_emg_bsl_stats_arousal_ablation_smoke.json` |

## Protocol Gates

| Gate | Status |
|---|---|
| EEG STIM-BSL-only comparator present | pass |
| EEG comparator uses sidecar-compatible folds | pass |
| EMG feature-only comparator present | pass |
| BSL-stats sidecar reports present | pass |
| Label policy | `midpoint_as_high`, not final/locked |
| Evidence boundary | smoke/stabilization only |

## EEG Comparison

| Task | Baseline recipe | Baseline final macro F1 | Sidecar recipe | Sidecar final macro F1 | Delta macro F1 | Baseline final bal acc | Sidecar final bal acc | Delta bal acc | Baseline threshold macro F1 | Sidecar threshold macro F1 | Delta threshold macro F1 | Interpretation |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| valence | ce_class_weighted | 0.5112 | ce_class_weighted | 0.4801 | -0.0311 | 0.5205 | 0.5191 | -0.0014 | 0.5197 | 0.5187 | -0.0010 | baseline_better_smoke_level |
| arousal | ce_class_weighted | 0.5307 | ce_class_weighted | 0.4943 | -0.0364 | 0.5323 | 0.5344 | 0.0022 | 0.5380 | 0.5565 | 0.0186 | baseline_better_smoke_level |

### EEG Interpretation

Keep EEG STIM-BSL-only as practical mainline for now; EEG BSL-stats sidecar does not consistently beat the standardized baseline on final macro-F1.

The EEG sidecar should remain a controlled ablation unless broader standardized evidence changes this conclusion.

## EMG Comparison

| Task | Baseline recipe | Baseline final macro F1 | Sidecar recipe | Sidecar final macro F1 | Delta macro F1 | Baseline final bal acc | Sidecar final bal acc | Delta bal acc | Baseline threshold macro F1 | Sidecar threshold macro F1 | Delta threshold macro F1 | Interpretation |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| valence | ce_class_weighted | 0.5004 | ce_class_weighted | 0.5073 | 0.0069 | 0.5083 | 0.5136 | 0.0053 | 0.5004 | 0.5073 | 0.0069 | roughly_neutral_or_mixed |
| arousal | ce_class_weighted | 0.5223 | ce_class_weighted | 0.5319 | 0.0096 | 0.5319 | 0.5344 | 0.0025 | 0.5223 | 0.5319 | 0.0096 | roughly_neutral_or_mixed |

### EMG Interpretation

EMG BSL-stats sidecar is smoke-level promising/marginal where it improves over feature-only baseline, but this does not automatically replace the EMG feature mainline.

The EMG sidecar evidence is useful, but it is still smoke-level evidence and should not trigger fusion or a final mainline change by itself.

## Decision

- Mainline changed: no.
- EEG practical representation remains baseline-corrected `STIM-BSL` for now.
- EMG practical representation remains feature-level EMG for now.
- BSL-stats sidecars remain controlled I-DARE-aware ablations.
- Next allowed step is human review of this comparison and, if needed, a broader standardized single-modality evaluation decision.
- EEG+EMG fusion is **not** started by this comparison.

## Intentionally Not Started

- EEG+EMG fusion.
- Full `model(BSL, STIM, STIM-BSL)`.
- Final LOSO / final performance claim.
- Locking `midpoint_as_high`.
- Raw EMG mainline.
- Architecture ablations.
- Data augmentation.
- SupCon / VREx / domain generalization.
