# I-DARE Alternative Pairwise Minimal First-Pass Review Status

## Status

Status: human review accepted.

Created UTC: `2026-05-08T19:06:50+00:00`

## Review Decision

The alternative pairwise minimal first-pass report is accepted for closeout.

Accepted diagnosis: `alternative_pairwise_minimal_first_pass_weak_mixed_signal`

Accepted recommended next objective: `label_semantics_alternative_pairwise_failure_or_metric_debug_objective`

## Accepted Key Evidence

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

Interpretation: the pairwise formulation shows a weak mixed signal, not an actionable confirmation.

## Consequence

This review authorizes creating a read-only failure/metric-debug objective.

This review does not authorize additional training, broad search, SupCon/DG, EEG+EMG fusion, or final LOSO claims.

## Next Allowed Step

`prepare_reviewed_label_semantics_alternative_pairwise_failure_or_metric_debug_command`
