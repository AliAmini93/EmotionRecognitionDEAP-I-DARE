# I-DARE SupCon/DG Failure Analysis Objective

## Status

Short-term read-only objective created.

- Created at: `2026-05-08T09:55:30+00:00`
- Objective id: `supcon_dg_failure_analysis_objective`
- Previous report: `docs/idare_minimal_supcon_dg_first_pass_report.md`
- Previous diagnosis: `minimal_supcon_dg_first_pass_not_sufficient`

## Scientific Question

Why did the minimal SupCon/DG first-pass fail to produce a robust improvement, and what does that imply for the next scientifically valid intervention?

## Motivation

The minimal first-pass did not justify full SupCon/DG training.

That does **not** mean SupCon/DG is invalid. It means we must determine whether the failure came from:

1. objective mismatch,
2. positive/negative pair design,
3. subject-domain grouping or VREx formulation,
4. representation weakness,
5. label/task ambiguity,
6. fold/task instability,
7. insufficient first-pass training evidence,
8. or a combination of the above.

## Authorized Scope

Allowed: read-only analysis of committed outputs.

Primary inputs:

- `docs/idare_minimal_supcon_dg_first_pass_runs.csv`
- `docs/idare_minimal_supcon_dg_first_pass_predictions.csv`
- `docs/idare_minimal_supcon_dg_first_pass_embedding_summary.csv`
- `docs/idare_minimal_supcon_dg_first_pass_loss_summary.csv`
- `docs/idare_subject_variability_supcon_dg_design_spec.md`
- `docs/idare_subject_variability_supcon_dg_pair_sampler_spec.csv`
- `docs/idare_subject_variability_supcon_dg_hyperparameter_registry.csv`
- `docs/idare_subject_variability_supcon_dg_smoke_tests_report.json`
- prior diagnostic reports under `docs/`

Forbidden until review:

- new model training,
- direct full SupCon/DG training,
- broad hyperparameter search,
- EEG+EMG fusion,
- final LOSO claim,
- mainline change.

## Required Analysis Questions

The failure-analysis report must answer:

1. Did SupCon loss decrease while validation macro-F1 / balanced accuracy stayed near chance?
2. Did embedding diagnostics improve within train but fail under subject-heldout validation?
3. Were positive pairs too easy, too local, too subject-specific, or too sparse for cross-subject generalization?
4. Were negative pairs semantically noisy because affect labels are subject-relative and ambiguous?
5. Did VREx reduce variance across subject groups or merely regularize without improving signal?
6. Were failures modality/task-specific, fold-specific, or method-specific?
7. Did any method improve consistency even if mean performance stayed low?
8. Is the next rational step pair/sampler redesign, subject-aware DG, label/task redesign, representation change, or stop condition?

## Expected Outputs

The next script should create:

- `docs/idare_supcon_dg_failure_analysis_report.md`
- `docs/idare_supcon_dg_failure_analysis_report.json`
- `docs/idare_supcon_dg_failure_method_task_summary.csv`
- `docs/idare_supcon_dg_failure_fold_summary.csv`
- `docs/idare_supcon_dg_failure_loss_embedding_alignment.csv`
- `docs/idare_supcon_dg_failure_decision_matrix.csv`

## Pass Criteria

A passing report must:

- use committed outputs only,
- explain whether failure is due to objective mismatch, pair/sampler design, representation weakness, fold/task instability, or insufficient evidence,
- produce a decision matrix with one selected next objective or stop condition,
- block broad hyperparameter search unless a specific targeted ablation is justified.

## Next Allowed Step

Prepare a reviewed read-only command/script for the SupCon/DG failure analysis report.
