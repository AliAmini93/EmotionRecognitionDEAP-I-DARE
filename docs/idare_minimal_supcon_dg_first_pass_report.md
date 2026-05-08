# I-DARE Minimal SupCon/DG First-pass Training Report

## Status

Minimal first-pass SupCon/DG diagnostic training complete, pending human review.

Generated UTC: `2026-05-08T09:46:03.236877+00:00`

## Run Matrix

- Design first-pass rows executed: `12`
- Expanded subject-heldout runs completed: `72`
- Prediction rows: `19632`
- Loss trace rows: `864`
- Embedding diagnostic rows: `72`
- Epochs: `12`
- Device: `cuda`

## Aggregate Results

| method | modality | task | n_runs | mean_macro_f1 | mean_balanced_accuracy | mean_accuracy | one_class_pred_count | mean_positive_pair_coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CE_plus_SupCon | EEG | arousal | 6 | 0.4771 | 0.4845 | 0.4875 | 0 | 1.0000 |
| CE_plus_SupCon | EEG | valence | 6 | 0.4784 | 0.4909 | 0.4881 | 0 | 1.0000 |
| CE_plus_SupCon | EMG | arousal | 6 | 0.4817 | 0.5007 | 0.4988 | 0 | 1.0000 |
| CE_plus_SupCon | EMG | valence | 6 | 0.4921 | 0.5059 | 0.5063 | 0 | 1.0000 |
| CE_plus_SupCon_plus_VREx | EEG | arousal | 6 | 0.4871 | 0.4961 | 0.4993 | 0 | 1.0000 |
| CE_plus_SupCon_plus_VREx | EEG | valence | 6 | 0.4738 | 0.4928 | 0.4861 | 0 | 1.0000 |
| CE_plus_SupCon_plus_VREx | EMG | arousal | 6 | 0.4867 | 0.5097 | 0.5036 | 0 | 1.0000 |
| CE_plus_SupCon_plus_VREx | EMG | valence | 6 | 0.4975 | 0.5129 | 0.5124 | 0 | 1.0000 |
| CE_plus_VREx | EEG | arousal | 6 | 0.4987 | 0.5014 | 0.5058 | 0 | 1.0000 |
| CE_plus_VREx | EEG | valence | 6 | 0.4893 | 0.4975 | 0.4933 | 0 | 1.0000 |
| CE_plus_VREx | EMG | arousal | 6 | 0.4995 | 0.5060 | 0.5033 | 0 | 1.0000 |
| CE_plus_VREx | EMG | valence | 6 | 0.5065 | 0.5151 | 0.5185 | 0 | 1.0000 |

## Best Aggregate Cell

- method: `CE_plus_VREx`
- modality: `EMG`
- task: `valence`
- mean macro-F1: `0.5065`
- mean balanced accuracy: `0.5151`

## Method-level Interpretation

```json
{
  "CE_plus_SupCon": "not_sufficient",
  "CE_plus_SupCon_plus_VREx": "not_sufficient",
  "CE_plus_VREx": "not_sufficient"
}
```

## Diagnosis

`minimal_supcon_dg_first_pass_not_sufficient`

## Recommended Next Objective

`supcon_dg_failure_analysis_objective`

## Required Caution

This report does not authorize final claims, fusion, broad hyperparameter search, direct full SupCon/DG training, or mainline replacement.

The result must be reviewed before any second-pass confirmation, targeted ablation, or failure-analysis objective.

## Outputs

- `docs/idare_minimal_supcon_dg_first_pass_runs.csv`
- `docs/idare_minimal_supcon_dg_first_pass_predictions.csv`
- `docs/idare_minimal_supcon_dg_first_pass_embedding_summary.csv`
- `docs/idare_minimal_supcon_dg_first_pass_loss_summary.csv`
- `docs/idare_minimal_supcon_dg_first_pass_report.json`

## Next Allowed Step

Human review / closeout before the recommended next objective.
