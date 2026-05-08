# I-DARE SupCon/DG Failure Analysis Report

## Status

Read-only SupCon/DG failure analysis is complete and pending human review.

- Created at: `2026-05-08T09:59:59+00:00`
- Objective: `docs/idare_supcon_dg_failure_analysis_objective.md`
- Runs analyzed: `72`
- Prediction rows analyzed: `19632`
- Diagnosis: `supcon_dg_first_pass_failed_despite_valid_smokes`
- Recommended next objective: `targeted_supcon_dg_pair_sampler_objective_ablation_design`

## Executive Diagnosis

The minimal SupCon/DG first pass failed to provide robust evidence that SupCon/DG, as currently specified, solves the subject-heldout generalization problem.

This is not interpreted as a basic plumbing failure, because the prior smoke tests passed and the first-pass runs produced non-degenerate predictions. The more likely issue is that the current objective and pair/domain formulation is too weak or misaligned for the subject-variability problem.

## Best Aggregate Cell

```json
{
  "method": "CE_plus_VREx",
  "modality": "EMG",
  "task": "valence",
  "n_runs": 6,
  "mean_macro_f1": 0.5064987409626325,
  "std_macro_f1": 0.04144051165063541,
  "min_macro_f1": 0.4376097222411236,
  "max_macro_f1": 0.5563108336859924,
  "mean_balanced_accuracy": 0.5151315622001712,
  "mean_accuracy": 0.5185094553335976,
  "folds_over_055_macro_f1": 2,
  "folds_under_050_macro_f1": 3,
  "one_class_pred_count": 0
}
```

## Overall Method Ranking

| method | n_runs | mean_macro_f1 | mean_balanced_accuracy | std_macro_f1 | folds_over_055_macro_f1 | folds_under_050_macro_f1 |
| --- | --- | --- | --- | --- | --- | --- |
| CE_plus_VREx | 24 | 0.4985 | 0.5050 | 0.0347 | 3 | 14 |
| CE_plus_SupCon_plus_VREx | 24 | 0.4863 | 0.5029 | 0.0321 | 0 | 12 |
| CE_plus_SupCon | 24 | 0.4823 | 0.4955 | 0.0352 | 0 | 14 |

## Top Method / Modality / Task Cells

| method | modality | task | n_runs | mean_macro_f1 | std_macro_f1 | mean_balanced_accuracy | folds_over_055_macro_f1 | folds_under_050_macro_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CE_plus_VREx | EMG | valence | 6 | 0.5065 | 0.0414 | 0.5151 | 2 | 3 |
| CE_plus_VREx | EMG | arousal | 6 | 0.4995 | 0.0382 | 0.5060 | 1 | 3 |
| CE_plus_VREx | EEG | arousal | 6 | 0.4987 | 0.0283 | 0.5014 | 0 | 4 |
| CE_plus_SupCon_plus_VREx | EMG | valence | 6 | 0.4975 | 0.0216 | 0.5129 | 0 | 2 |
| CE_plus_SupCon | EMG | valence | 6 | 0.4921 | 0.0476 | 0.5059 | 0 | 1 |
| CE_plus_VREx | EEG | valence | 6 | 0.4893 | 0.0260 | 0.4975 | 0 | 4 |
| CE_plus_SupCon_plus_VREx | EEG | arousal | 6 | 0.4871 | 0.0253 | 0.4961 | 0 | 4 |
| CE_plus_SupCon_plus_VREx | EMG | arousal | 6 | 0.4867 | 0.0418 | 0.5097 | 0 | 2 |
| CE_plus_SupCon | EMG | arousal | 6 | 0.4817 | 0.0373 | 0.5007 | 0 | 4 |
| CE_plus_SupCon | EEG | valence | 6 | 0.4784 | 0.0173 | 0.4909 | 0 | 5 |
| CE_plus_SupCon | EEG | arousal | 6 | 0.4771 | 0.0294 | 0.4845 | 0 | 4 |
| CE_plus_SupCon_plus_VREx | EEG | valence | 6 | 0.4738 | 0.0315 | 0.4928 | 0 | 4 |

## Weakest Method / Modality / Task Cells

| method | modality | task | n_runs | mean_macro_f1 | std_macro_f1 | mean_balanced_accuracy | folds_over_055_macro_f1 | folds_under_050_macro_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CE_plus_SupCon_plus_VREx | EEG | valence | 6 | 0.4738 | 0.0315 | 0.4928 | 0 | 4 |
| CE_plus_SupCon | EEG | arousal | 6 | 0.4771 | 0.0294 | 0.4845 | 0 | 4 |
| CE_plus_SupCon | EEG | valence | 6 | 0.4784 | 0.0173 | 0.4909 | 0 | 5 |
| CE_plus_SupCon | EMG | arousal | 6 | 0.4817 | 0.0373 | 0.5007 | 0 | 4 |
| CE_plus_SupCon_plus_VREx | EMG | arousal | 6 | 0.4867 | 0.0418 | 0.5097 | 0 | 2 |
| CE_plus_SupCon_plus_VREx | EEG | arousal | 6 | 0.4871 | 0.0253 | 0.4961 | 0 | 4 |
| CE_plus_VREx | EEG | valence | 6 | 0.4893 | 0.0260 | 0.4975 | 0 | 4 |
| CE_plus_SupCon | EMG | valence | 6 | 0.4921 | 0.0476 | 0.5059 | 0 | 1 |

## Loss / Embedding Alignment

The generated alignment table is written to:

- `docs/idare_supcon_dg_failure_loss_embedding_alignment.csv`

The strongest simple diagnostic correlations with validation macro-F1 are:

| diagnostic_metric | corr_with_macro_f1 | corr_with_balanced_accuracy | n_nonmissing |
| --- | --- | --- | --- |
| active_lambda_supcon_end | -0.1925 | -0.0962 | 72 |
| active_lambda_supcon_delta | -0.1925 | -0.0962 | 72 |
| supcon_loss_end | -0.1922 | -0.0957 | 72 |
| total_loss_relative_delta | -0.1908 | -0.0925 | 72 |
| total_loss_delta | -0.1906 | -0.0917 | 72 |
| total_loss_end | -0.1898 | -0.0904 | 72 |
| supcon_loss_start | -0.1887 | -0.0898 | 72 |
| supcon_loss_relative_delta | -0.1531 | -0.2699 | 48 |
| vrex_environment_count_start | 0.1408 | 0.1451 | 72 |
| vrex_environment_count_end | 0.1408 | 0.1451 | 72 |

If loss terms decrease but these correlations are weak, then optimization is happening without reliable subject-heldout transfer.

## Prediction Error Notes

```json
{
  "overall_error_rate": 0.5,
  "top_subject_error_rates": [
    {
      "subject": "49",
      "error_rate": 0.5807291666666666
    },
    {
      "subject": "34",
      "error_rate": 0.564327485380117
    },
    {
      "subject": "22",
      "error_rate": 0.5614035087719298
    },
    {
      "subject": "52",
      "error_rate": 0.5544871794871795
    },
    {
      "subject": "46",
      "error_rate": 0.5533333333333333
    },
    {
      "subject": "12",
      "error_rate": 0.546875
    },
    {
      "subject": "63",
      "error_rate": 0.5390070921985816
    },
    {
      "subject": "60",
      "error_rate": 0.5374149659863946
    },
    {
      "subject": "3",
      "error_rate": 0.5352564102564102
    },
    {
      "subject": "58",
      "error_rate": 0.5289855072463768
    }
  ]
}
```

## Decision Matrix

| hypothesis | support | decision |
| --- | --- | --- |
| implementation_or_sampler_bug | low | do_not_debug_basic_plumbing_unless_future smoke fails |
| SupCon/DG objective not aligned with subject-heldout performance | high | analyze objective/pair design before more training |
| pair_sampler_or_positive_definition_too_weak | medium_high | targeted pair/sampler ablation is more justified than broad hyperparameter search |
| VREx/domain_regularization_insufficient | high | do not launch full DG training without a narrower failure hypothesis |
| representation_or_label_task_remains_primary_bottleneck | medium_high | targeted_supcon_dg_pair_sampler_objective_ablation_design |

## Interpretation

The failed first pass suggests that the current SupCon/DG setup is not yet targeting the actual blocker strongly enough.

Most likely explanations:

1. positive pairs are label-compatible but not necessarily subject-invariant,
2. negative pairs may be semantically noisy under affect labels,
3. VREx may be regularizing loss without learning useful invariant structure,
4. representation features may still encode subject/fold artifacts more strongly than affect state,
5. subject-heldout validation remains the core bottleneck.

## Recommendation

Do **not** start direct full SupCon/DG training or broad hyperparameter search.

The next scientific step should be a targeted objective around pair/sampler and domain-objective ablation, constrained by this failure analysis. The goal should be to test a small number of explicit failure hypotheses rather than expanding the search space.

Recommended next objective:

- `targeted_supcon_dg_pair_sampler_objective_ablation_design`

## Next Allowed Step

Human review / closeout of this failure analysis before any new SupCon/DG training, targeted ablation, broad search, fusion, or mainline change.
