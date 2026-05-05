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

## Two-Fold Stability Smoke - ce_class_weighted / lr 3e-4

A tiny two-fold stability smoke was run after the initial fold-1 recipe check.

Configuration:

```text
recipe = ce_class_weighted
lr = 3e-4
weight_decay = 1e-3
epochs = 2
label_policy = midpoint_as_high
folds = 6
seeds = 11
max_runs = 2 per task
```

This remained cache-only and did not use raw MATLAB/HDF5 `.mat` loading inside training loops.

### Valence result

| Fold | Macro F1 | Balanced acc | Accuracy | Pred 0 | Pred 1 | One-class |
|---:|---:|---:|---:|---:|---:|---|
| 1 | `0.4394` | `0.5133` | `0.4574` | `274` | `78` | false |
| 2 | `0.3889` | `0.5047` | `0.6023` | `3` | `349` | false |

Aggregate:

```text
macro F1 = 0.4142
balanced accuracy = 0.5090
one-class final runs = 0/2
```

### Arousal result

| Fold | Macro F1 | Balanced acc | Accuracy | Pred 0 | Pred 1 | One-class |
|---:|---:|---:|---:|---:|---:|---|
| 1 | `0.4725` | `0.4748` | `0.5142` | `235` | `117` | false |
| 2 | `0.4033` | `0.4920` | `0.4290` | `67` | `285` | false |

Aggregate:

```text
macro F1 = 0.4379
balanced accuracy = 0.4834
one-class final runs = 0/2
```

### Interpretation

`ce_class_weighted + lr=3e-4` is a better anti-collapse candidate than the earlier `lr=1e-3` setting because it avoided strict one-class final predictions in both tasks across the first two folds.

However, this is still not stable enough for a full experiment:

- Valence fold 2 is technically not one-class, but it is almost fully biased toward class 1.
- Arousal fold 2 is also strongly biased toward class 1.
- Balanced accuracy remains close to chance.
- Threshold diagnostics suggest calibration/class-bias remains an issue.

### Updated Recommendation

Do not run a full experiment yet.

The next useful step should be another tiny smoke test that changes only one thing. The strongest next candidate is to add and smoke-test a `balanced_sampler_ce` recipe against `ce_class_weighted`, still cache-only and still with a tiny smoke cap.

## Balanced Sampler CE Smoke

A new recipe candidate was added to `scripts/20_run_idare_eeg_cache_recipe_stabilization.py`:

```text
balanced_sampler_ce
```

Implementation summary:

- Uses `WeightedRandomSampler` on the training split.
- Uses standard `CrossEntropyLoss`.
- Remains fully cache-based.
- Does not load raw MATLAB/HDF5 `.mat` files inside training loops.
- Records sampler mode in JSON:
  - `shuffle`
  - `weighted_random_sampler`

### Smoke Configuration

```text
label_policy = midpoint_as_high
lr = 3e-4
weight_decay = 1e-3
epochs = 2
folds = 6
seed = 11
max_runs = 2
```

This is still a smoke test, not a full experiment.

### Arousal / fold 1

| Recipe | Sampler | Macro F1 | Balanced acc | Accuracy | Pred 0 | Pred 1 | One-class |
|---|---|---:|---:|---:|---:|---:|---|
| `ce_class_weighted` | `shuffle` | `0.4725` | `0.4748` | `0.5142` | `235` | `117` | false |
| `balanced_sampler_ce` | `weighted_random_sampler` | `0.3897` | `0.5079` | `0.4261` | `50` | `302` | false |

Threshold diagnostic for `balanced_sampler_ce`:

```text
best threshold = 0.60
best threshold macro F1 = 0.5291
best threshold balanced accuracy = 0.5306
best threshold pred_counts = {"0": 241, "1": 111}
```

### Valence / fold 1

| Recipe | Sampler | Macro F1 | Balanced acc | Accuracy | Pred 0 | Pred 1 | One-class |
|---|---|---:|---:|---:|---:|---:|---|
| `ce_class_weighted` | `shuffle` | `0.4394` | `0.5133` | `0.4574` | `274` | `78` | false |
| `balanced_sampler_ce` | `weighted_random_sampler` | `0.4982` | `0.5044` | `0.5455` | `103` | `249` | false |

Threshold diagnostic for `balanced_sampler_ce`:

```text
best threshold = 0.50
best threshold macro F1 = 0.4982
best threshold balanced accuracy = 0.5044
best threshold pred_counts = {"0": 103, "1": 249}
```

### Interpretation

`balanced_sampler_ce` avoided strict one-class collapse in both task smoke tests.

It may be useful as an anti-collapse / calibration candidate, but it is not yet clearly better than `ce_class_weighted`:

- For valence fold 1, it improved macro F1 but not balanced accuracy.
- For arousal fold 1, argmax macro F1 dropped, but threshold sweep improved both macro F1 and balanced accuracy.
- It can push predictions strongly toward class 1.

### Updated Recommendation

Do not run a full experiment yet.

The next useful step should be a tiny two-fold stability smoke for `balanced_sampler_ce`, analogous to the previous `ce_class_weighted + lr=3e-4` stability smoke.

Use:

```text
recipes = balanced_sampler_ce
lr = 3e-4
epochs = 2
max_runs = 2
```

Run separately for valence and arousal with task-specific output files.

## Balanced Sampler CE Two-Fold Stability Smoke

A two-fold stability smoke was run for `balanced_sampler_ce`.

Configuration:

```text
recipe = balanced_sampler_ce
sampler = weighted_random_sampler
lr = 3e-4
weight_decay = 1e-3
epochs = 2
label_policy = midpoint_as_high
folds = 6
seed = 11
max_runs = 2 per task
```

This remained cache-only and did not use raw MATLAB/HDF5 `.mat` loading inside training loops.

### Valence result

| Fold | Macro F1 | Balanced acc | Accuracy | Pred 0 | Pred 1 | One-class |
|---:|---:|---:|---:|---:|---:|---|
| 1 | `0.4982` | `0.5044` | `0.5455` | `103` | `249` | false |
| 2 | `0.3825` | `0.5035` | `0.6023` | `1` | `351` | false |

Aggregate:

```text
macro F1 = 0.4404
balanced accuracy = 0.5040
one-class final runs = 0/2
```

Interpretation:

- `balanced_sampler_ce` avoided strict one-class collapse for valence.
- However, fold 2 is effectively near-collapse toward class 1.
- This is not stable enough for a full experiment.

### Arousal result

| Fold | Macro F1 | Balanced acc | Accuracy | Pred 0 | Pred 1 | One-class |
|---:|---:|---:|---:|---:|---:|---|
| 1 | `0.3897` | `0.5079` | `0.4261` | `50` | `302` | false |
| 2 | `0.4960` | `0.4960` | `0.5170` | `212` | `140` | false |

Aggregate:

```text
macro F1 = 0.4428
balanced accuracy = 0.5019
one-class final runs = 0/2
```

Threshold diagnostics:

```text
fold 1 best threshold = 0.60
fold 1 best threshold macro F1 = 0.5291
fold 1 best threshold balanced accuracy = 0.5306

fold 2 best threshold = 0.45
fold 2 best threshold macro F1 = 0.5079
fold 2 best threshold balanced accuracy = 0.5228
```

Interpretation:

- `balanced_sampler_ce` avoided strict one-class collapse for arousal.
- Threshold sweep suggests useful calibration signal for arousal.
- Arousal is currently the stronger candidate for threshold-calibrated follow-up smoke.

### Updated Recommendation

Do not run a full experiment yet.

The next useful step should be a tiny threshold-calibration smoke, still cache-only, using the existing probability/threshold diagnostics.

Recommended next smoke direction:

```text
recipe candidates:
  ce_class_weighted
  balanced_sampler_ce

lr:
  3e-4

epochs:
  2

scope:
  max-runs 2 or 4 only
```

The goal should be to compare argmax metrics against threshold-calibrated metrics, not to claim final performance.

## Arousal Threshold-Comparison Smoke

A tiny threshold-comparison smoke was run for arousal after the balanced-sampler stability checks.

Configuration:

```text
task = arousal
label_policy = midpoint_as_high
recipes = ce_class_weighted, balanced_sampler_ce
lr = 3e-4
weight_decay = 1e-3
epochs = 2
folds = 6
seed = 11
max_runs = 4
```

This smoke covered:

```text
fold 1 / ce_class_weighted
fold 1 / balanced_sampler_ce
fold 2 / ce_class_weighted
fold 2 / balanced_sampler_ce
```

It remained cache-only and did not use raw MATLAB/HDF5 `.mat` loading inside training loops.

### Argmax aggregate

| Recipe | Runs | Final macro F1 | Final balanced acc | Final accuracy | One-class final runs |
|---|---:|---:|---:|---:|---:|
| `balanced_sampler_ce` | 2 | `0.4428` | `0.5019` | `0.4716` | `0/2` |
| `ce_class_weighted` | 2 | `0.4379` | `0.4834` | `0.4716` | `0/2` |

### Per-run threshold observations

| Run | Recipe | Fold | Argmax macro F1 | Argmax bal acc | Best threshold | Threshold macro F1 | Threshold bal acc |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | `ce_class_weighted` | 1 | `0.4725` | `0.4748` | `0.50` | `0.4725` | `0.4748` |
| 2 | `balanced_sampler_ce` | 1 | `0.3897` | `0.5079` | `0.60` | `0.5291` | `0.5306` |
| 3 | `ce_class_weighted` | 2 | `0.4033` | `0.4920` | `0.55` | `0.5071` | `0.5155` |
| 4 | `balanced_sampler_ce` | 2 | `0.4960` | `0.4960` | `0.45` | `0.5079` | `0.5228` |

### Interpretation

Threshold-calibrated evaluation appears more informative than raw argmax for arousal.

The strongest observation is that `balanced_sampler_ce` improved after threshold adjustment in both folds:

```text
fold 1: macro F1 0.3897 -> 0.5291, balanced acc 0.5079 -> 0.5306
fold 2: macro F1 0.4960 -> 0.5079, balanced acc 0.4960 -> 0.5228
```

`ce_class_weighted` also benefited from threshold adjustment in fold 2.

This supports adding report-level aggregate threshold metrics before any broader experiment.

### Updated Recommendation

Do not run a full experiment yet.

Next step should be a small script/report patch that aggregates threshold-sweep best metrics by recipe, so future smoke reports directly compare:

```text
argmax macro F1
argmax balanced accuracy
best-threshold macro F1
best-threshold balanced accuracy
best threshold distribution
one-class counts
```

After that patch, run only a tiny smoke test again.
