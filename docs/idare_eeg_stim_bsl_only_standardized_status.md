# I-DARE EEG STIM-BSL-only Standardized Baseline Status

## Status

Frozen smoke/stabilization closeout for the standardized I-DARE EEG `STIM-BSL`-only baseline comparator.

This is **not** a final LOSO or final performance result.

## Purpose

The purpose of this phase was to close the missing EEG baseline comparator gap before comparing the frozen EEG `STIM-BSL + BSL-stats` sidecar ablation against a fair `STIM-BSL`-only baseline.

The previous local inventory found that a valence baseline-corrected `STIM-BSL`-only report was missing and that existing arousal baseline-corrected reports were not protocol-aligned with the BSL-stats sidecar. This status document records the standardized replacement smoke.

## Evidence

- Commit: `0e9594d` / `0e9594ddd055c70359564c3658171b8e42f100ef`
- Valence report: `docs/idare_eeg_stim_bsl_only_valence_standardized_smoke.md`
- Valence JSON: `docs/idare_eeg_stim_bsl_only_valence_standardized_smoke.json`
- Valence predictions: `docs/idare_eeg_stim_bsl_only_valence_standardized_smoke_predictions.csv`
- Arousal report: `docs/idare_eeg_stim_bsl_only_arousal_standardized_smoke.md`
- Arousal JSON: `docs/idare_eeg_stim_bsl_only_arousal_standardized_smoke.json`
- Arousal predictions: `docs/idare_eeg_stim_bsl_only_arousal_standardized_smoke_predictions.csv`

## Inputs

- cache_npy: `.cache/idare_eeg_windows_32x640_float32_baseline_corrected.npy`
- cache_index: `.cache/idare_eeg_cache_index_baseline_corrected.csv`
- BSL-stats sidecar used: no
- Raw HDF5/MAT loaded in training loop: no

## Protocol Alignment

| Field | Value |
|---|---|
| Target comparison partner | `docs/idare_eeg_bsl_stats_ablation_status.md` |
| Representation | baseline-corrected `STIM-BSL` EEG response cache only |
| Label policy | `midpoint_as_high` |
| Label policy final? | no |
| Tasks | `valence`, `arousal` |
| Recipes | `ce_class_weighted`, `balanced_sampler_ce` |
| Folds | 6 |
| Fold splitter | sidecar-compatible `numpy.default_rng(11)` subject folds |
| Seed | 11 |
| Epochs | 12 |
| Learning rate | 0.001 |
| Batch size | 64 |
| Max runs per task | 4 |

## Aggregate Results

Best final macro-F1 rows only; these are smoke/stabilization results.

| Task | Best recipe | Runs | Final macro F1 | Final balanced acc | Final acc | Threshold macro F1 | Final one-class runs | Threshold one-class runs |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| valence | ce_class_weighted | 2 | 0.5112 | 0.5205 | 0.5511 | 0.5197 | 0 | 0 |
| arousal | ce_class_weighted | 2 | 0.5307 | 0.5323 | 0.5455 | 0.5380 | 0 | 0 |

## Decision

Freeze this standardized EEG `STIM-BSL`-only baseline as the fair baseline-only comparator for the already frozen EEG `STIM-BSL + BSL-stats` sidecar smoke.

This does **not** change the EEG mainline by itself.

## Next Allowed Step

Create direct single-modality comparison documentation for:

- EEG `STIM-BSL`-only standardized baseline vs EEG `STIM-BSL + BSL-stats` sidecar.
- EMG feature-only baseline vs EMG feature + BSL-stats sidecar.

Suggested output:

- `docs/idare_single_modality_bsl_stats_vs_baseline_comparison.md`
- `docs/idare_single_modality_bsl_stats_vs_baseline_comparison.json`

## Intentionally Not Started

- EEG+EMG fusion.
- Full `model(BSL, STIM, STIM-BSL)`.
- Final LOSO / final performance claim.
- Label-policy finalization or locking `midpoint_as_high`.
- Architecture ablations.
- Data augmentation.
- SupCon / VREx / domain generalization.
