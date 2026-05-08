# I-DARE Minimal SupCon/DG First-pass Training Objective

## Status

Short-term diagnostic training objective created.

Created UTC: `2026-05-08T09:39:01.179380+00:00`

Preceded by:

- smoke-test objective: `docs/idare_subject_variability_supcon_dg_smoke_tests_objective.md`
- smoke-test report: `docs/idare_subject_variability_supcon_dg_smoke_tests_report.md`
- smoke-test review: `docs/idare_subject_variability_supcon_dg_smoke_tests_review_status.md`
- design spec: `docs/idare_subject_variability_supcon_dg_design_spec.md`

## Scientific Question

Does the cautious SupCon/DG design improve subject-heldout generalization over the current subject-relative/preprocessed diagnostic baselines, without relying on leakage, broad tuning, or post-hoc threshold selection?

## Authorized Scope

This objective authorizes a **minimal first-pass** SupCon/DG training run only.

Authorized:

- use the reviewed pair/sampler design;
- use the reviewed hyperparameter registry;
- use the first-pass run matrix from `docs/idare_subject_variability_supcon_dg_first_pass_run_matrix.csv`;
- log CE loss, SupCon loss, total loss, embedding diagnostics, prediction counts, and per-fold metrics;
- compare only against already committed subject-relative and preprocessed first-pass baselines;
- commit raw outputs and a combined report.

Not authorized:

- broad hyperparameter search;
- direct full SupCon/DG training;
- changing the selected pair/sampler semantics during the run;
- adding EEG+EMG fusion;
- final LOSO or paper-level claims;
- replacing project mainline/default model.

## Required First-pass Matrix

Use the reviewed first-pass run matrix:

- file: `docs/idare_subject_variability_supcon_dg_first_pass_run_matrix.csv`
- planned rows: `16`

The implementation command may reduce only if a technical smoke failure occurs. Otherwise, all planned rows should run.

## Hyperparameter Handling

Use the reviewed registry:

- file: `docs/idare_subject_variability_supcon_dg_hyperparameter_registry.csv`
- registry rows: `8`

For every run, the output must record:

- modality;
- task;
- fold;
- seed;
- label formulation;
- encoder/feature path;
- SupCon temperature;
- SupCon loss weight;
- batch sampler type;
- CE/class weighting choice;
- epochs;
- learning rate;
- batch size.

## Required Safety Checks Before Training

The run script must fail before training if:

- repo is dirty;
- required cache/index/design/report files are missing;
- smoke-test review is missing;
- first-pass run matrix is empty;
- subject-heldout fold construction deviates from the reviewed seed/fold policy;
- a batch has no positive cross-subject pair availability;
- any train/validation row overlap or subject overlap is detected.

## Required Outputs

Expected output files:

- `docs/idare_minimal_supcon_dg_first_pass_report.md`
- `docs/idare_minimal_supcon_dg_first_pass_report.json`
- `docs/idare_minimal_supcon_dg_first_pass_runs.csv`
- `docs/idare_minimal_supcon_dg_first_pass_predictions.csv`
- `docs/idare_minimal_supcon_dg_first_pass_embedding_summary.csv`
- `docs/idare_minimal_supcon_dg_first_pass_loss_summary.csv`

## Pass Criteria

The objective passes execution if:

1. all authorized runs complete or any skipped run is explicitly justified;
2. every run has valid finite metrics;
3. no one-class prediction collapse occurs without being flagged;
4. no leakage guard fails;
5. per-run hyperparameters are recorded;
6. a report states whether SupCon/DG is better, mixed, or not useful versus the prior diagnostic baselines.

Scientific success is stricter than execution success.

A positive scientific signal requires consistent improvement over prior subject-relative/preprocessed baselines, not just one isolated fold.

## Decision Tree After Report

If improved consistently:

- create a second-pass confirmation objective with a narrow hyperparameter expansion.

If mixed:

- inspect which modality/task/fold benefits, then create a targeted ablation objective.

If not improved:

- do not continue SupCon/DG blindly; diagnose whether pair definition, representation backbone, label formulation, or DG regularizer is the limiting factor.

## Next Allowed Step

Prepare a reviewed implementation/run command for the minimal SupCon/DG first-pass matrix.
