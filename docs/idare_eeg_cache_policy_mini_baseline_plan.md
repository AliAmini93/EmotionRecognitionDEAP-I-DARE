# I-DARE Cache-Based Policy Mini-Baseline Plan

## Purpose

The previous full-ish EEG baseline attempt was too slow because it read MATLAB/HDF5 files during training.

The current plan is to use the validated EEG cache:

```text
.cache/idare_eeg_windows_32x640_float32.npy
.cache/idare_eeg_cache_index.csv
```

This should avoid per-batch HDF5 reading and keep training fast.

## Script

```text
scripts/15_run_idare_eeg_cache_policy_mini_baseline.py
```

## What It Tests

Tasks:

```text
valence
arousal
```

Score-5 policies:

```text
discard_midpoint
midpoint_as_low
midpoint_as_high
```

Default split:

```text
train subjects: 5, 6, 7, 8, 9, 10, 11, 12
validation subjects: 1, 2, 3, 13
```

Default training:

```text
epochs: 3
seeds: 11, 13
batch size: 16
loss: class-weighted CrossEntropyLoss
```

## Interpretation

This is not final LOSO.

Use it only to decide whether a score-5 policy is clearly promising. Prefer:

```text
balanced accuracy
macro F1
best macro F1 across epochs
```

over raw accuracy.

If all policies remain weak or unstable, keep all three policies as presets but do not expand ablations yet.
