# I-DARE EEG Main Baseline Status

This status note records the current cache-based I-DARE EEG main baseline.

## Decision

- Temporary main score-5 policy: `midpoint_as_high` for both valence and arousal.
- This is **not** a final LOSO result.
- This is a cache-based subject-fold baseline used to stabilize the training/evaluation path.
- `discard_midpoint` remains a secondary sanity / ablation candidate.

## Main Baseline Results

| Task | Policy | Final macro F1 | Final balanced acc | Best macro F1 | One-class final runs |
|---|---|---:|---:|---:|---:|
| valence | midpoint_as_high | 0.3953 | 0.4995 | 0.4566 | 4/12 |
| arousal | midpoint_as_high | 0.4825 | 0.5159 | 0.4918 | 1/12 |

## Interpretation

- Arousal is currently more promising than valence.
- Valence still shows notable one-class-collapse risk.
- The next technical priority is not a bigger final experiment yet; it is a controlled sanity run for `discard_midpoint` and then small training-recipe stabilization.

## Source Report

- `docs/idare_eeg_cache_main_baseline.md`
- `docs/idare_eeg_cache_main_baseline.json`

## Status

Accepted as the current working baseline status, not as a final experimental claim.
