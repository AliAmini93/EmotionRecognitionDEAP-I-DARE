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
