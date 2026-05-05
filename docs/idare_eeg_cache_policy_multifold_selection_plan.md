# I-DARE EEG Cache-Based Multi-Fold Policy Selection Plan

## Purpose

The previous cache-based mini-baseline showed that cache training is fast and that no score-5 policy is a universal winner from one validation split.

This next step runs a small multi-fold subject-held-out policy-selection pilot.

## Why this is not full LOSO

This is still a pilot. It uses a few validation folds and a capped number of training subjects by default to keep runtime short. Its goal is to decide which score-5 policies deserve the next real baseline pass.

## Compared policies

- `discard_midpoint`
- `midpoint_as_low`
- `midpoint_as_high`

## Tasks

- `valence`
- `arousal`

## Default folds

- Fold 1 validation subjects: `1, 2, 3, 13`
- Fold 2 validation subjects: `14, 15, 16, 17`
- Fold 3 validation subjects: `18, 19, 20, 21`
- Fold 4 validation subjects: `22, 23, 24, 25`

## Default runtime controls

- Seeds: `11, 13`
- Epochs: `3`
- Batch size: `32`
- Max training subjects per fold: `24`
- Data source: `.cache/idare_eeg_windows_32x640_float32.npy`

## Outputs

- `docs/idare_eeg_cache_policy_multifold_selection.md`
- `docs/idare_eeg_cache_policy_multifold_selection.json`

## Interpretation rule

Prefer macro F1 and balanced accuracy over raw accuracy. Penalize policies that often collapse to one-class predictions. Promote a task-specific policy only if it is clearly better across folds and seeds.
