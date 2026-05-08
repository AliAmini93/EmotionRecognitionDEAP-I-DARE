# I-DARE Alternative Pairwise Failure-or-Metric-Debug Objective

## Status

Status: objective created; read-only failure/metric-debug only; no training is authorized.

Created UTC: `2026-05-08T19:06:50+00:00`

## Scientific Question

Why did the alternative within-subject pairwise minimal first pass produce only a weak mixed signal, and what is the next defensible decision?

## Triggering Evidence

Accepted first-pass diagnosis: `alternative_pairwise_minimal_first_pass_weak_mixed_signal`

Best learned cell:

```json
{
  "model": "ridge_classifier_pairwise_summary_diff",
  "training_category": "minimal_classical_pairwise_baseline",
  "modality": "EEG",
  "task": "arousal",
  "n_runs": 6,
  "mean_balanced_accuracy": 0.5216709095350218,
  "std_balanced_accuracy": 0.018748839652001463,
  "min_balanced_accuracy": 0.5053943898345721,
  "max_balanced_accuracy": 0.5497501135847342,
  "mean_macro_f1": 0.5216709095350218,
  "mean_accuracy": 0.5216709095350218,
  "mean_pred_positive_rate": 0.5,
  "one_class_pred_count": 0,
  "folds_over_055_bal_acc": 0,
  "folds_under_045_bal_acc": 0,
  "mean_majority_baseline_bal_acc": 0.5,
  "delta_vs_majority_baseline_bal_acc": 0.02167090953502182,
  "mean_random_baseline_bal_acc": 0.501244141659629,
  "delta_vs_random_baseline_bal_acc": 0.02042676787539277
}
```

Key trigger: best mean balanced accuracy was `0.521671`, with delta vs majority baseline `0.021671`, folds over 0.55 = `0`, and max fold balanced accuracy `0.549750`.

## Authorized Work

- Read existing pairwise first-pass outputs.
- Compute control-adjusted lift, fold stability, subject concentration, and metric conflict.
- Produce a read-only failure/metric-debug report.
- Recommend one next decision path.

## Not Authorized

- running additional training before read-only failure/metric-debug review
- broad hyperparameter search
- direct full SupCon/DG training
- EEG+EMG fusion
- final LOSO claim
- training outside a reviewed objective

## Required Analysis Questions

See: `docs/idare_label_semantics_alternative_pairwise_failure_or_metric_debug_questions.csv`

## Input Map

See: `docs/idare_label_semantics_alternative_pairwise_failure_or_metric_debug_input_map.csv`

## Decision Tree

See: `docs/idare_label_semantics_alternative_pairwise_failure_or_metric_debug_decision_tree.csv`

## Pass Criteria

- No new training is run.
- All conclusions are derived from committed first-pass outputs.
- Best-cell lift is compared against no-training controls.
- Fold and subject concentration are explicitly audited.
- Next step is one of: narrow confirmation, narrow patch/debug, archive, or representation/feature-summary objective.

## Next Allowed Step

`prepare_reviewed_label_semantics_alternative_pairwise_failure_or_metric_debug_command`
