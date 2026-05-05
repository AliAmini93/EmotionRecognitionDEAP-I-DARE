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

## Arousal Aggregate Threshold Comparison Smoke

After adding aggregate threshold diagnostics to `scripts/20_run_idare_eeg_cache_recipe_stabilization.py`, a tiny arousal smoke was rerun to verify the new report-level aggregate table.

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

This remained cache-only and did not use raw MATLAB/HDF5 `.mat` loading inside training loops.

### Argmax aggregate

| Recipe | Runs | Argmax macro F1 | Argmax balanced acc | Argmax accuracy | One-class final runs |
|---|---:|---:|---:|---:|---:|
| `balanced_sampler_ce` | 2 | `0.4428` | `0.5019` | `0.4716` | `0/2` |
| `ce_class_weighted` | 2 | `0.4379` | `0.4834` | `0.4716` | `0/2` |

### Aggregate threshold diagnostics

| Recipe | Runs | Threshold macro F1 | Threshold balanced acc | Mean threshold | Macro F1 gain | Balanced acc gain | Threshold one-class runs |
|---|---:|---:|---:|---:|---:|---:|---:|
| `balanced_sampler_ce` | 2 | `0.5185` | `0.5267` | `0.5250` | `+0.0757` | `+0.0248` | `0/2` |
| `ce_class_weighted` | 2 | `0.4898` | `0.4952` | `0.5250` | `+0.0519` | `+0.0118` | `0/2` |

### Interpretation

The aggregate threshold diagnostics table is working and makes the arousal calibration effect easier to inspect.

Current smoke-level conclusion:

- `balanced_sampler_ce` has the better threshold-calibrated aggregate result for arousal.
- `balanced_sampler_ce` improved from argmax macro F1 `0.4428` to threshold macro F1 `0.5185`.
- `balanced_sampler_ce` improved from argmax balanced accuracy `0.5019` to threshold balanced accuracy `0.5267`.
- `ce_class_weighted` also improved with threshold adjustment, but less strongly.
- No threshold-selected run became one-class.

This is still diagnostic only. The thresholds were selected on the validation split, so these numbers should not be reported as final model performance.

### Updated Recommendation

Do not run a full experiment yet.

The next technical step should remain smoke-first. A reasonable next smoke is to test whether the same aggregate threshold pattern appears for valence, using the same small scope:

```text
task = valence
recipes = ce_class_weighted, balanced_sampler_ce
lr = 3e-4
epochs = 2
max-runs = 4
```

Only after reviewing that smoke should any broader stabilization run be considered.

## Valence Aggregate Threshold Comparison Smoke

After the arousal aggregate threshold comparison, a matching tiny valence smoke was run to check whether threshold calibration shows the same pattern.

Configuration:

```text
task = valence
label_policy = midpoint_as_high
recipes = ce_class_weighted, balanced_sampler_ce
lr = 3e-4
weight_decay = 1e-3
epochs = 2
folds = 6
seed = 11
max_runs = 4
```

This remained cache-only and did not use raw MATLAB/HDF5 `.mat` loading inside training loops.

### Argmax aggregate

| Recipe | Runs | Argmax macro F1 | Argmax balanced acc | Argmax accuracy | One-class final runs |
|---|---:|---:|---:|---:|---:|
| `balanced_sampler_ce` | 2 | `0.4404` | `0.5040` | `0.5739` | `0/2` |
| `ce_class_weighted` | 2 | `0.4142` | `0.5090` | `0.5298` | `0/2` |

### Aggregate threshold diagnostics

| Recipe | Runs | Threshold macro F1 | Threshold balanced acc | Mean threshold | Macro F1 gain | Balanced acc gain | Threshold one-class runs |
|---|---:|---:|---:|---:|---:|---:|---:|
| `balanced_sampler_ce` | 2 | `0.4404` | `0.5040` | `0.5000` | `0.0000` | `0.0000` | `0/2` |
| `ce_class_weighted` | 2 | `0.4142` | `0.5090` | `0.5000` | `0.0000` | `0.0000` | `0/2` |

### Interpretation

Unlike arousal, threshold calibration did not improve valence in this smoke.

Current smoke-level conclusion:

- For valence, best thresholds remained at `0.50` for both recipes.
- Threshold macro F1 and threshold balanced accuracy were identical to argmax metrics.
- The main remaining issue is not threshold calibration; it is fold/class-bias instability.
- Fold 2 remains near-collapse toward class 1:
  - `ce_class_weighted`: pred_counts = `{"0": 3, "1": 349}`
  - `balanced_sampler_ce`: pred_counts = `{"0": 1, "1": 351}`

This is still diagnostic only and should not be reported as final model performance.

### Updated Recommendation

Do not run a full experiment yet.

The next technical step for valence should focus on fold/class-bias diagnostics rather than threshold calibration.

A reasonable next smoke direction is to keep the same cache-based path and inspect whether the near-collapse behavior is driven by:

```text
fold-specific label distribution
subject composition
training prediction distribution
validation probability compression
sampler-induced class bias
```

Any such follow-up must remain smoke-first, for example using `--max-runs 2` or `--max-runs 4`, before any broader stabilization run is considered.

## Valence Fold-Bias Diagnostic

A cache-index and smoke-JSON diagnostic was added:

```text
scripts/21_analyze_idare_valence_fold_bias_diagnostics.py
```

Outputs:

```text
docs/idare_valence_fold_bias_diagnostics.md
docs/idare_valence_fold_bias_diagnostics.json
```

This diagnostic does not train a model and does not load raw MATLAB/HDF5 `.mat` files. It reads only:

```text
.cache/idare_eeg_cache_index.csv
docs/idare_eeg_cache_recipe_stabilization_valence_threshold_aggregate_compare_smoke.json
```

### Key finding

Valence fold 1 and fold 2 have identical aggregate label counts in the smoke:

```text
train counts = {"0": 671, "1": 993}
val counts   = {"0": 141, "1": 211}
```

Therefore, the fold 2 near-collapse toward class 1 is not explained by simple train/validation label imbalance.

### Fold behavior

| Fold | Recipe | Pred 0 | Pred 1 | P1 mean | P1 median | Macro F1 | Balanced acc |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | `ce_class_weighted` | `274` | `78` | `0.4909` | `0.4911` | `0.4394` | `0.5133` |
| 1 | `balanced_sampler_ce` | `103` | `249` | `0.5146` | `0.5194` | `0.4982` | `0.5044` |
| 2 | `ce_class_weighted` | `3` | `349` | `0.5235` | `0.5234` | `0.3889` | `0.5047` |
| 2 | `balanced_sampler_ce` | `1` | `351` | `0.5294` | `0.5300` | `0.3825` | `0.5035` |

### Interpretation

The valence fold 2 issue is more likely related to:

```text
subject composition
fold-specific learned boundary
probability/logit bias
sampler-induced class bias
validation probability compression
```

rather than a trivial label-count imbalance.

### Updated Recommendation

Do not run a full experiment yet.

The next technical step should remain diagnostic and smoke-first. A reasonable next step is to add optional per-sample validation prediction export to script 20, then run a tiny smoke to inspect which subjects/stimuli drive fold 2 class-1 bias.

## Valence Per-Sample Prediction Export Diagnostic

Script 20 was extended with optional final-validation per-sample prediction export:

```text
--out-predictions-csv
```

This is intended for diagnostics only. It should be used with tiny smoke runs, not full experiments.

A valence fold-bias prediction smoke was run with:

```text
task = valence
label_policy = midpoint_as_high
recipes = ce_class_weighted, balanced_sampler_ce
lr = 3e-4
weight_decay = 1e-3
epochs = 2
folds = 6
seed = 11
max_runs = 4
```

Outputs:

```text
docs/idare_valence_fold_bias_predictions_smoke.md
docs/idare_valence_fold_bias_predictions_smoke.json
docs/idare_valence_fold_bias_predictions_smoke.csv
```

The CSV contains per-sample validation predictions and probabilities:

```text
run_id
task
policy
recipe
sampler
fold_id
seed
cache_row
subject_id
stimulus_id
y_true
y_pred
prob1
logit_margin
```

### Key finding

The per-sample export confirmed that valence fold 2 near-collapse is a fold-level probability/logit offset, not a single-subject issue.

In fold 2, nearly all validation subjects had `prob1_mean` above `0.51`, so the default `0.50` threshold pushed almost all predictions to class 1.

### Fold 2 subject-level behavior

For `ce_class_weighted` / fold 2:

```text
subject 8:  pred_counts = {"0": 1, "1": 31}, prob1_mean = 0.5132
subject 10: pred_counts = {"0": 0, "1": 32}, prob1_mean = 0.5217
subject 18: pred_counts = {"0": 0, "1": 32}, prob1_mean = 0.5332
subject 24: pred_counts = {"0": 0, "1": 32}, prob1_mean = 0.5208
subject 29: pred_counts = {"0": 0, "1": 32}, prob1_mean = 0.5238
subject 31: pred_counts = {"0": 1, "1": 31}, prob1_mean = 0.5185
subject 34: pred_counts = {"0": 0, "1": 32}, prob1_mean = 0.5265
subject 41: pred_counts = {"0": 1, "1": 31}, prob1_mean = 0.5208
subject 43: pred_counts = {"0": 0, "1": 32}, prob1_mean = 0.5362
subject 46: pred_counts = {"0": 0, "1": 32}, prob1_mean = 0.5214
subject 53: pred_counts = {"0": 0, "1": 32}, prob1_mean = 0.5226
```

For `balanced_sampler_ce` / fold 2:

```text
subject 8:  pred_counts = {"0": 0, "1": 32}, prob1_mean = 0.5297
subject 10: pred_counts = {"0": 0, "1": 32}, prob1_mean = 0.5307
subject 18: pred_counts = {"0": 0, "1": 32}, prob1_mean = 0.5297
subject 24: pred_counts = {"0": 0, "1": 32}, prob1_mean = 0.5293
subject 29: pred_counts = {"0": 0, "1": 32}, prob1_mean = 0.5283
subject 31: pred_counts = {"0": 1, "1": 31}, prob1_mean = 0.5289
subject 34: pred_counts = {"0": 0, "1": 32}, prob1_mean = 0.5252
subject 41: pred_counts = {"0": 0, "1": 32}, prob1_mean = 0.5264
subject 43: pred_counts = {"0": 0, "1": 32}, prob1_mean = 0.5315
subject 46: pred_counts = {"0": 0, "1": 32}, prob1_mean = 0.5307
subject 53: pred_counts = {"0": 0, "1": 32}, prob1_mean = 0.5330
```

### Interpretation

The fold 2 behavior is not driven by one outlier subject.

It is better described as a fold-level probability shift where validation probabilities are compressed slightly above `0.50`.

This explains why threshold calibration did not help valence in the earlier aggregate threshold smoke: the best threshold stayed at `0.50`, and the probabilities were not sufficiently separable.

### Updated Recommendation

Do not run a full experiment yet.

The next technical step should remain smoke-first and should target fold-level probability offset mitigation or diagnostics.

Reasonable next smoke directions include:

```text
1. Add train/validation probability summaries to compare calibration shift directly.
2. Add per-subject aggregate diagnostics to the script report.
3. Test one mild regularization/calibration change at a time.
4. Keep max-runs small, such as --max-runs 2 or --max-runs 4.
```

The strongest current distinction remains:

```text
arousal:
  threshold calibration appears useful.

valence:
  fold-level probability offset/class-bias is the main issue.

## Valence Train-vs-Validation Probability Shift Diagnostic

Script 20 was extended to record final train-set probability diagnostics alongside validation diagnostics.

A tiny valence smoke was run with:

```text
task = valence
label_policy = midpoint_as_high
recipes = ce_class_weighted, balanced_sampler_ce
lr = 3e-4
weight_decay = 1e-3
epochs = 2
folds = 6
seed = 11
max_runs = 4
```

Outputs:

```text
docs/idare_valence_train_val_probability_shift_smoke.md
docs/idare_valence_train_val_probability_shift_smoke.json
```

This remained cache-only and did not use raw MATLAB/HDF5 `.mat` loading inside training loops.

### Train-vs-validation probability summary

| Run | Recipe | Fold | Train pred 0 | Train pred 1 | Val pred 0 | Val pred 1 | Train P1 mean | Val P1 mean | Mean shift | Train P1 median | Val P1 median | Median shift |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `ce_class_weighted` | 1 | `1309` | `355` | `274` | `78` | `0.4901` | `0.4909` | `+0.0008` | `0.4910` | `0.4911` | `+0.0001` |
| 2 | `balanced_sampler_ce` | 1 | `420` | `1244` | `103` | `249` | `0.5174` | `0.5146` | `-0.0028` | `0.5236` | `0.5194` | `-0.0042` |
| 3 | `ce_class_weighted` | 2 | `109` | `1555` | `3` | `349` | `0.5200` | `0.5235` | `+0.0035` | `0.5205` | `0.5234` | `+0.0028` |
| 4 | `balanced_sampler_ce` | 2 | `29` | `1635` | `1` | `351` | `0.5296` | `0.5294` | `-0.0002` | `0.5308` | `0.5300` | `-0.0008` |

### Key finding

The valence fold 2 near-collapse is not a validation-only shift.

For fold 2, both recipes are already strongly biased toward class 1 on the training set:

```text
ce_class_weighted / fold 2:
  train pred_counts = {"0": 109, "1": 1555}
  val pred_counts   = {"0": 3, "1": 349}

balanced_sampler_ce / fold 2:
  train pred_counts = {"0": 29, "1": 1635}
  val pred_counts   = {"0": 1, "1": 351}
```

The train/validation probability shifts are small:

```text
ce_class_weighted / fold 2:
  val_mean - train_mean = +0.0035

balanced_sampler_ce / fold 2:
  val_mean - train_mean = -0.0002
```

### Interpretation

The current evidence suggests that valence fold 2 near-collapse is a learned boundary / recipe bias toward class 1, not:

```text
simple label imbalance
a single-subject issue
validation-only probability shift
```

This makes threshold calibration less useful for valence, because the probability distribution is already compressed close to and above `0.50` on both train and validation.

### Updated Recommendation

Do not run a full experiment yet.

The next technical step should remain smoke-first and should test one small mitigation at a time against this learned class-1 boundary bias.

Reasonable next smoke directions:

```text
1. Reduce class-1 bias with a stronger or different class-balancing mechanism.
2. Compare class-weighted CE against balanced sampler using train-vs-val diagnostics.
3. Try one mild regularization/calibration change at a time.
4. Add a small diagnostic for train-set per-class recall / prediction collapse.
```

Any next run should stay tiny first, for example:

```text
--max-runs 2
--epochs 2
```

or at most the existing diagnostic scope:

```text
--max-runs 4
--epochs 2
```
