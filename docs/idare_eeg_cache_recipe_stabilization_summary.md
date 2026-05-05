# I-DARE EEG Cache Recipe Stabilization Summary

This document summarizes the cache-based I-DARE EEG recipe-stabilization phase.

Latest status checkpoint at the time this summary was prepared:

```text
779ba54 docs: update label smoothing smoke status
```

This summary is documentation only. It does not define or execute a new experiment.

## Scope and Hard Constraints

This phase stayed within the current main project constraints:

- Use EEG cache only.
- Do not load raw MATLAB/HDF5 `.mat` files inside training loops.
- Use the validated cache files:
  - `.cache/idare_eeg_windows_32x640_float32.npy`
  - `.cache/idare_eeg_cache_index.csv`
- Cache shape remains `[2016, 32, 640]`.
- Current main label policy remains `midpoint_as_high`.
- Every new script, training recipe, or experiment runner must be smoke-tested first.
- Do not jump to full LOSO/final/full experiments before smoke results are reviewed.

## Main Script Added/Extended

The main stabilization runner is:

```text
scripts/20_run_idare_eeg_cache_recipe_stabilization.py
```

The script now supports cache-only recipe smoke testing with:

- `ce_class_weighted`
- `ce_no_class_weight`
- `balanced_sampler_ce`
- `ce_label_smoothing_0p05`

It reports:

- macro F1
- balanced accuracy
- accuracy
- confusion counts
- prediction counts
- majority baseline
- one-class prediction/collapse diagnostics
- probability summaries
- threshold sweep diagnostics
- aggregate threshold diagnostics
- train-vs-validation probability diagnostics
- optional validation prediction export CSV

## Documentation Produced

Key docs and outputs produced during this phase include:

```text
docs/idare_eeg_cache_recipe_stabilization_plan.md
docs/idare_eeg_cache_recipe_stabilization_status.md

docs/idare_eeg_cache_recipe_stabilization_arousal_lr3e4_smoke.md
docs/idare_eeg_cache_recipe_stabilization_valence_lr3e4_smoke.md

docs/idare_eeg_cache_recipe_stabilization_arousal_weighted_lr3e4_stability_smoke.md
docs/idare_eeg_cache_recipe_stabilization_valence_weighted_lr3e4_stability_smoke.md

docs/idare_eeg_cache_recipe_stabilization_arousal_balanced_sampler_smoke.md
docs/idare_eeg_cache_recipe_stabilization_valence_balanced_sampler_smoke.md

docs/idare_eeg_cache_recipe_stabilization_arousal_balanced_sampler_stability_smoke.md
docs/idare_eeg_cache_recipe_stabilization_valence_balanced_sampler_stability_smoke.md

docs/idare_eeg_cache_recipe_stabilization_arousal_threshold_aggregate_compare_smoke.md
docs/idare_eeg_cache_recipe_stabilization_valence_threshold_aggregate_compare_smoke.md

docs/idare_valence_fold_bias_diagnostics.md
docs/idare_valence_fold_bias_predictions_smoke.md
docs/idare_valence_train_val_probability_shift_smoke.md
docs/idare_valence_lr1e4_boundary_bias_smoke.md
docs/idare_valence_label_smoothing_smoke.md
```

JSON companions were also written for the smoke outputs.

## Key Findings

### 1. Smoke-first workflow worked

The recipe-stabilization phase successfully prevented a premature full run.

The process caught several important issues early:

- one-class collapse under default recipes
- threshold sensitivity
- fold-specific instability
- train-vs-validation probability behavior
- label-smoothing recipe implementation issues before broader use

This validates the new-chat smoke-test protocol and the cache-only workflow.

### 2. `lr=3e-4` improved over the first default smoke, but did not solve valence

At `lr=3e-4`, `ce_class_weighted` avoided one-class collapse on some valence/arousal fold-1 smoke runs.

However, valence fold 2 remained unstable and drifted strongly toward class 1.

Example valence fold-2 behavior at `lr=3e-4`:

```text
ce_class_weighted:
  val pred_counts = {"0": 3, "1": 349}

balanced_sampler_ce:
  val pred_counts = {"0": 1, "1": 351}
```

This is not acceptable as a stable recipe.

### 3. Arousal is more promising than valence

Arousal showed the strongest signs of useful diagnostic signal.

The best small-scope direction observed for arousal is:

```text
balanced_sampler_ce + threshold diagnostics
```

In the arousal threshold aggregate comparison smoke:

```text
balanced_sampler_ce:
  argmax macro F1 mean      = 0.4428
  argmax balanced acc mean  = 0.5019
  threshold macro F1 mean   = 0.5185
  threshold balanced acc    = 0.5267
  threshold macro F1 gain   = +0.0757
```

This does not justify a final run yet, but it is the most promising path found in this phase.

### 4. Valence fold-2 instability is not just validation-label imbalance

Valence fold-bias diagnostics showed fold 1 and fold 2 had similar train/validation label distributions.

The issue is therefore not explained by a trivial validation class imbalance.

### 5. Valence fold-2 instability is not just validation-only probability shift

Train-vs-validation probability diagnostics showed that fold-2 bias appears on the training set as well.

At `lr=3e-4`:

```text
ce_class_weighted / fold 2:
  train pred_counts = {"0": 109, "1": 1555}
  val pred_counts   = {"0": 3, "1": 349}

balanced_sampler_ce / fold 2:
  train pred_counts = {"0": 29, "1": 1635}
  val pred_counts   = {"0": 1, "1": 351}
```

The train/validation probability shifts were small:

```text
ce_class_weighted / fold 2:
  val_mean - train_mean = +0.0035

balanced_sampler_ce / fold 2:
  val_mean - train_mean = -0.0002
```

This suggests learned boundary bias, not a validation-only shift.

### 6. Lowering LR to `1e-4` did not solve valence

The `lr=1e-4` smoke reversed the fold-2 bias direction rather than stabilizing it.

At `lr=1e-4`:

```text
ce_class_weighted / fold 2:
  train pred_counts = {"0": 1475, "1": 189}
  val pred_counts   = {"0": 326, "1": 26}

balanced_sampler_ce / fold 2:
  train pred_counts = {"0": 1653, "1": 11}
  val pred_counts   = {"0": 351, "1": 1}
```

Interpretation:

```text
lr=3e-4: fold 2 drifts above 0.50 and predicts mostly class 1
lr=1e-4: fold 2 drifts below 0.50 and predicts mostly class 0
```

So the valence problem is not simply “learning rate too high.”

### 7. `ce_label_smoothing_0p05` is not promising

The label-smoothing recipe was added and smoke-tested.

Engineering fixes were required:

- define `train_criterion` and `eval_criterion` for the new recipe
- safely handle `class_weights` metadata for recipes without class weights

After those fixes, the smoke completed successfully.

Result on valence fold 1:

```text
ce_label_smoothing_0p05:
  train pred_counts = {"0": 2, "1": 1662}
  val pred_counts   = {"0": 0, "1": 352}
  val macro F1      = 0.3748
  val balanced acc  = 0.5000
  one_class_pred    = true
```

Label smoothing increased class-1 bias rather than stabilizing valence.

Recommendation:

```text
Do not expand ce_label_smoothing_0p05 to more folds or seeds.
```

## Current Technical Interpretation

### Arousal

Arousal is not solved, but it has a plausible next path:

```text
balanced_sampler_ce + threshold diagnostics
```

Threshold-calibrated diagnostics improved arousal macro F1 in small smoke settings.

However, this remains diagnostic. It is not yet a final evaluation policy.

### Valence

Valence remains unstable.

Current evidence suggests:

```text
- not a cache problem
- not a raw-data loading problem
- not a simple label-count imbalance
- not a validation-only shift
- not solved by lowering LR
- not solved by label smoothing
```

Most likely issue:

```text
fold-sensitive learned boundary instability near 0.50
```

The valence model can flip from class-1-biased to class-0-biased depending on recipe/LR, without becoming consistently useful.

## What Not To Do Next

Do not run a full experiment yet.

Do not start a larger LOSO/full/final run from these recipes.

Do not expand `ce_label_smoothing_0p05`.

Do not return to raw MATLAB/HDF5 `.mat` loading inside training loops.

Do not add many recipe changes at once.

## Recommended Next Step

The next useful step should be diagnostic and small.

Most recommended:

```text
Add per-class train/validation recall aggregates to script 20 reports.
```

Why:

- prediction counts alone show collapse direction
- confusion counts are per-run but not aggregated by class
- per-class recall aggregates would make collapse and minority-class failure easier to compare across recipes/folds
- this is a reporting/diagnostic improvement, not a new training recipe
- it can be smoke-tested with `--max-runs 2 --epochs 2`

Possible smoke after adding the diagnostic:

```text
tasks = valence
recipes = ce_class_weighted, balanced_sampler_ce
lr = 3e-4
epochs = 2
max-runs = 2
```

Only after reviewing that diagnostic should a broader smoke be considered.

## Alternative Next Step

If the team wants to stop recipe experimentation here, another reasonable next step is to close the stabilization phase and update handoff docs:

```text
docs/project_state.md
docs/chat_handoff_latest.md
docs/next_chat_prompt.md
```

These should record:

```text
latest commit = 779ba54
script 20 supports recipe stabilization diagnostics
arousal remains more promising than valence
valence has boundary instability
label smoothing is non-promising
next recommended work = per-class recall aggregate diagnostics or phase closeout
```

## Phase Status

This phase is approximately complete from a recipe-exploration standpoint.

Estimated completion:

```text
85% to 90%
```

Remaining work before closing the phase:

```text
1. Add one final diagnostic summary or per-class recall aggregate, if desired.
2. Update handoff/project-state docs.
3. Explicitly mark no full run should be launched from current valence recipes.
```

## Bottom Line

The cache-based stabilization workflow is working.

The main value of this phase was not finding a final recipe; it was identifying that:

```text
- arousal may benefit from balanced sampling plus threshold diagnostics
- valence is dominated by unstable boundary behavior
- simple recipe tweaks do not solve valence
- smoke-first testing prevents wasting time on bad full runs
```
