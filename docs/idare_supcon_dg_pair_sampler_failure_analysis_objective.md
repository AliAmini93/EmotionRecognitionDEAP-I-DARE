# I-DARE SupCon/DG Pair-Sampler Failure Analysis Objective

## Status

Status: objective created; read-only analysis only.

Created UTC: `2026-05-08T10:30:45+00:00`

No new training is authorized by this document.

## Scientific Question

Why did the targeted SupCon/DG pair-sampler ablation fail to produce a stable subject-heldout improvement, despite passing smoke tests, leakage guards, and positive-pair coverage checks?

## Immediate Context

The targeted ablation completed `120` runs and `40320` prediction rows.

The report diagnosis was:

`targeted_pair_sampler_ablation_not_sufficient`

The best aggregate candidate was `A5_cross_subject_supcon_vrex` with mean macro-F1 `0.5119` and mean balanced accuracy `0.5164`.

This means the pair/sampler direction was not obviously broken, but also not sufficient.

## Authorized Scope

This objective is read-only. It may use only committed evidence files.

Allowed inputs:

- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_report.md`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_report.json`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_runs.csv`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_predictions.csv`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_pair_audit.csv`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_loss_embedding_summary.csv`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_method_task_summary.csv`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_candidate_summary.csv`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_smoke_summary.csv`
- `docs/idare_supcon_dg_failure_analysis_report.md`
- `docs/idare_supcon_dg_failure_analysis_report.json`

## Required Analysis Questions

1. Did pair/sampler variants improve any modality/task/fold pattern consistently, or only isolated cells?
2. Was A5 better because of cross-subject SupCon, VREx, or their interaction?
3. Did positive-pair coverage hide semantic label noise, subject-specific label meaning, or rating-distance mismatch?
4. Did SupCon lower contrastive loss without improving class-separable validation embeddings?
5. Did VREx reduce fold variance or suppress weak useful signal?
6. Are improvements concentrated in EMG/arousal, EEG/arousal, or particular folds/subjects?
7. Do prediction errors overlap with earlier subject-variability hard-subject patterns?
8. Which failure mode is most supported now:
   - pair design failure
   - label/task semantic mismatch
   - representation weakness
   - optimization/hyperparameter issue
   - DG regularizer mismatch
   - insufficient data per subject/fold

## Expected Outputs

- `docs/idare_supcon_dg_pair_sampler_failure_analysis_report.md`
- `docs/idare_supcon_dg_pair_sampler_failure_analysis_report.json`
- `docs/idare_supcon_dg_pair_sampler_failure_candidate_deltas.csv`
- `docs/idare_supcon_dg_pair_sampler_failure_fold_subject_summary.csv`
- `docs/idare_supcon_dg_pair_sampler_failure_loss_alignment.csv`
- `docs/idare_supcon_dg_pair_sampler_failure_decision_matrix.csv`

## Pass Criteria

- No new training is run.
- The report explains why `A5_cross_subject_supcon_vrex` was best but insufficient.
- The report distinguishes implementation failure from scientific/assumption failure.
- The report recommends exactly one next objective or a stop/rollback decision.
- Full SupCon/DG training remains blocked unless a later reviewed analysis explicitly justifies it.

## Blocked

- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change
- new training before failure-analysis review

## Next Allowed Step

Prepare a reviewed read-only command/script for this failure analysis.
