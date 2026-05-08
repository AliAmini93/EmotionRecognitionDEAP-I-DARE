# I-DARE Targeted SupCon/DG Pair-Sampler Ablation Report

## Status

Status: complete; pending human review.

Runs completed: `120`
Predictions written: `40320`
Runtime seconds: `128.1`

## Executive Diagnosis

Diagnosis: `targeted_pair_sampler_ablation_not_sufficient`

Recommended next objective: `supcon_dg_pair_sampler_failure_analysis_objective`

Best candidate aggregate:

`A5_cross_subject_supcon_vrex` with mean macro-F1 `0.5119` and mean balanced accuracy `0.5164`.

Gain vs CE control by candidate aggregate: `+0.0031` macro-F1.

## Candidate-level Summary

| candidate                         | n  | macro_f1 | bal_acc | gain_vs_ce | over_055 | under_050 |
| --------------------------------- | -- | -------- | ------- | ---------- | -------- | --------- |
| A5_cross_subject_supcon_vrex      | 24 | 0.5119   | 0.5164  | +0.0031    | 2        | 7         |
| A0_CE_control                     | 24 | 0.5088   | 0.5144  | +0.0000    | 1        | 8         |
| A4_rating_distance_guarded_supcon | 24 | 0.5071   | 0.5131  | -0.0017    | 1        | 11        |
| A2_cross_subject_positive_only    | 24 | 0.5061   | 0.5127  | -0.0027    | 3        | 12        |
| A6_vrex_only_recheck              | 24 | 0.5048   | 0.5110  | -0.0040    | 1        | 11        |

## Top Method/Task Cells

| candidate                         | modality | task    | macro_f1 | bal_acc | acc    | over_055 | under_050 |
| --------------------------------- | -------- | ------- | -------- | ------- | ------ | -------- | --------- |
| A4_rating_distance_guarded_supcon | EEG      | arousal | 0.5304   | 0.5323  | 0.5342 | 1        | 1         |
| A2_cross_subject_positive_only    | EEG      | arousal | 0.5285   | 0.5305  | 0.5323 | 1        | 0         |
| A5_cross_subject_supcon_vrex      | EEG      | arousal | 0.5236   | 0.5257  | 0.5267 | 0        | 1         |
| A0_CE_control                     | EEG      | valence | 0.5228   | 0.5283  | 0.5366 | 0        | 0         |
| A5_cross_subject_supcon_vrex      | EMG      | arousal | 0.5197   | 0.5237  | 0.5306 | 1        | 1         |
| A6_vrex_only_recheck              | EMG      | arousal | 0.5164   | 0.5204  | 0.5263 | 1        | 2         |
| A0_CE_control                     | EEG      | arousal | 0.5154   | 0.5194  | 0.5201 | 0        | 1         |
| A6_vrex_only_recheck              | EEG      | arousal | 0.5109   | 0.5134  | 0.5157 | 0        | 3         |
| A4_rating_distance_guarded_supcon | EEG      | valence | 0.5104   | 0.5163  | 0.5185 | 0        | 2         |
| A6_vrex_only_recheck              | EEG      | valence | 0.5096   | 0.5148  | 0.5235 | 0        | 2         |
| A5_cross_subject_supcon_vrex      | EEG      | valence | 0.5092   | 0.5142  | 0.5212 | 1        | 2         |
| A2_cross_subject_positive_only    | EMG      | arousal | 0.5090   | 0.5146  | 0.5183 | 1        | 3         |

## Outputs

- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_runs.csv`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_predictions.csv`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_pair_audit.csv`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_loss_embedding_summary.csv`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_method_task_summary.csv`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_candidate_summary.csv`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_smoke_summary.csv`

## Interpretation Rules

This is a diagnostic ablation only. It does not authorize direct full SupCon/DG training.

A promising candidate must show consistent gains across tasks/folds, not only a single lucky fold.

## Blocked Until Review

- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change

## Next Allowed Step

Human review / closeout before confirmation or failure-analysis objective.
