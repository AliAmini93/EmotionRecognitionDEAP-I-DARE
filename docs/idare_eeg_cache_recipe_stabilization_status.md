# I-DARE EEG Cache Recipe Stabilization Status

## Status

Initial cache-based recipe-stabilization smoke tests are complete.

This is not a final LOSO experiment and should not be reported as a final model result.

## Hard Constraints Confirmed

- Training used the validated EEG cache:
  - `.cache/idare_eeg_windows_32x640_float32.npy`
  - `.cache/idare_eeg_cache_index.csv`
- Cache shape observed during runs:
  - `[2016, 32, 640]`
- No raw MATLAB/HDF5 `.mat` files were loaded inside training loops.
- All runs were tiny smoke tests using:
  - `--max-runs 2`
  - `--epochs 1` or `--epochs 2`

## Initial Smoke Findings

### LR 1e-3

With `lr=1e-3`, both `ce_class_weighted` and `ce_no_class_weight` collapsed to one-class predictions.

Observed examples:

- valence / `epochs=1`:
  - both recipes collapsed to class 1
  - balanced accuracy: `0.5000`
- arousal / `epochs=1`:
  - both recipes collapsed to class 0
  - balanced accuracy: `0.5000`
- arousal / `epochs=2`:
  - both recipes still collapsed to class 0
  - balanced accuracy: `0.5000`

### Probability / threshold diagnostics

Probability diagnostics showed that the models were not completely dead, but logits were under-confident or miscalibrated.

For arousal with `lr=1e-3`, `epochs=2`:

- `ce_class_weighted`:
  - argmax predicted only class 0
  - `P(class=1)` mean: `0.4376`
  - best threshold: `0.45`
  - best-threshold macro F1: `0.4419`
  - best-threshold balanced accuracy: `0.5103`
- `ce_no_class_weight`:
  - argmax predicted only class 0
  - `P(class=1)` mean: `0.3933`
  - best threshold: `0.40`
  - best-threshold macro F1: `0.4857`
  - best-threshold balanced accuracy: `0.5005`

## LR 3e-4 Smoke Findings

Lowering LR from `1e-3` to `3e-4` reduced one-class collapse.

### Arousal / midpoint_as_high / fold 1 / seed 11 / epochs 2

| Recipe | Macro F1 | Balanced acc | Accuracy | Pred 0 | Pred 1 | One-class |
|---|---:|---:|---:|---:|---:|---|
| `ce_class_weighted` | `0.4725` | `0.4748` | `0.5142` | `235` | `117` | false |
| `ce_no_class_weight` | `0.4050` | `0.5031` | `0.6108` | `343` | `9` | false |

### Valence / midpoint_as_high / fold 1 / seed 11 / epochs 2

| Recipe | Macro F1 | Balanced acc | Accuracy | Pred 0 | Pred 1 | One-class |
|---|---:|---:|---:|---:|---:|---|
| `ce_class_weighted` | `0.4394` | `0.5133` | `0.4574` | `274` | `78` | false |
| `ce_no_class_weight` | `0.3748` | `0.5000` | `0.5994` | `0` | `352` | true |

## Current Interpretation

The current best anti-collapse candidate is:

```text
recipe = ce_class_weighted
lr = 3e-4
weight_decay = 1e-3
epochs = 2
label_policy = midpoint_as_high
```

This is only a stabilization candidate, not a final recipe.

The main reason to prefer it for the next smoke is that it avoided one-class final predictions for both valence and arousal in fold 1 / seed 11.

## Recommended Next Step

Do not run a full experiment yet.

The next useful step should be another tiny cache-based smoke test that checks whether the current anti-collapse behavior survives slightly more variation.

Recommended next smoke:

- keep `ce_class_weighted`
- keep `lr=3e-4`
- keep `midpoint_as_high`
- use both tasks
- use a tiny cap such as `--max-runs 4`
- keep `--epochs 2`

This should still be treated as a smoke test, not a final or full run.
