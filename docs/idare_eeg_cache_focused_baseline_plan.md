# I-DARE EEG Cache-Based Focused Baseline Plan

## Purpose

Run a short, cache-based EEG-only baseline after the score-5 multi-fold policy-selection pilot.

The previous pilot narrowed the useful policy set to:

```text
midpoint_as_low
midpoint_as_high
```

`discard_midpoint` remains implemented, but it is deprioritized for this focused baseline.

## Why This Step

The cache is now validated and avoids slow MATLAB/HDF5 reads during training.

This step should test whether the EEG-only model shows any stable signal under the two surviving score-5 policies before committing to heavier LOSO or multimodal experiments.

## Default Configuration

```text
tasks: valence, arousal
policies: midpoint_as_low, midpoint_as_high
seeds: 11, 13
folds: 6 subject-held-out folds over all cached subjects
epochs: 5
batch size: 32
loss: class-weighted CrossEntropyLoss
model: EEGSegmentClassifier-v1 lite
input: cached EEG tensor [32, 640]
```

## Outputs

```text
docs/idare_eeg_cache_focused_baseline.md
docs/idare_eeg_cache_focused_baseline.json
```

## Interpretation Rule

Use macro F1 and balanced accuracy as primary indicators.

Raw accuracy is secondary because class imbalance can make majority-class predictions look deceptively good.

Watch for:

```text
one-class final predictions
near-chance balanced accuracy
failure to beat majority-class macro F1
```

## Expected Runtime

The previous cache-based multi-fold selection took about 74 seconds for a broader policy pilot.

This focused run has fewer policies but more folds/epochs, so it should still be practical on the RTX 5090.
