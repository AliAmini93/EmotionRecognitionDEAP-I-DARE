# I-DARE EEG Cache Plan

## Purpose

The previous baseline training attempt was stopped because it appeared to hang while repeatedly reading I-DARE MATLAB v7.3 / HDF5 files during training.

The next step is to build a cache of fixed-size EEG windows before training.

## Cache Design

Input:

```text
.cache/idare_trial_index.csv
/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/*.mat
```

Output:

```text
.cache/idare_eeg_windows_32x640_float32.npy
.cache/idare_eeg_cache_index.csv
docs/idare_eeg_cache_build_report.md
docs/idare_eeg_cache_build_report.json
docs/idare_eeg_cache_validation.md
docs/idare_eeg_cache_validation.json
```

The `.npy` cache is intentionally stored under `.cache` and should not be committed.

## Signal Convention

For each I-DARE trial:

```text
start = int(eeg_begin_raw)
window = data[start:start + 2560, first_32_channels]
downsampled = window[::4]
output shape = [32, 640]
```

Rationale:

- I-DARE EEG sampling rate is 512Hz.
- The model expects 128Hz.
- Five seconds at 512Hz is 2560 samples.
- Downsampling by 4 gives 640 samples.
- This matches the existing `IDARETrialDataset` validation.

## Normalization

Each cached EEG trial is normalized independently:

```text
x = (x - mean(x)) / std(x)
```

This matches the current loader-smoke behavior where each returned EEG window has approximately zero mean and unit variance.

## Scope

This is still a pre-training infrastructure step.

It does not run full LOSO training.
It does not save model checkpoints.
It only prepares and validates a fast cache for the next baseline run.
