# I-DARE EEG Cache Recipe Stabilization Plan

## Purpose

Run a small cache-based EEG-only training-recipe stabilization check before any fuller experiment.

This is not a final LOSO experiment.

## Hard Rules

- Use only the validated EEG cache:
  - `.cache/idare_eeg_windows_32x640_float32.npy`
  - `.cache/idare_eeg_cache_index.csv`
- Do not load raw MATLAB/HDF5 `.mat` files inside training loops.
- Start with a tiny smoke test:
  - `--max-runs 2`
  - `--epochs 1`
- Do not propose a fuller command until the smoke output has been reviewed.

## Current Main Policy

Use `midpoint_as_high` as the temporary main score-5 policy for both valence and arousal.

Keep `discard_midpoint` available as a secondary sanity / ablation candidate, but do not use it in the first recipe-stabilization smoke.

## Initial Recipes

The first tiny comparison is:

1. `ce_class_weighted`
2. `ce_no_class_weight`

## Diagnostics Required

Each run should report:

- macro F1
- balanced accuracy
- accuracy
- confusion counts
- prediction counts
- one-class-collapse diagnostics
- majority baseline

## Outputs

The script writes:

- `docs/idare_eeg_cache_recipe_stabilization.md`
- `docs/idare_eeg_cache_recipe_stabilization.json`

These outputs should be inspected after the smoke test before any fuller run is considered.


## Added Follow-up Recipe Candidate

After the initial `ce_class_weighted` / `ce_no_class_weight` smoke tests, the next smoke-tested recipe candidate is:

- `balanced_sampler_ce`

This recipe uses a weighted random sampler on the training split and standard CrossEntropyLoss. It must remain cache-based and must be tested first with a tiny smoke command before any fuller run is considered.


## Added Threshold Aggregate Reporting

After threshold-sweep diagnostics showed useful calibration information, script 20 should report aggregate threshold metrics by recipe:

- best-threshold macro F1
- best-threshold balanced accuracy
- mean selected threshold
- macro F1 gain over argmax
- balanced accuracy gain over argmax
- threshold one-class count

This reporting is diagnostic only and does not justify a full experiment by itself.
