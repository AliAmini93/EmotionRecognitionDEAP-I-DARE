# I-DARE Representation or Label-Semantics Failure Analysis Objective

## Status

Status: objective created; read-only analysis only.

Created UTC: `2026-05-08T10:44:24+00:00`

No new training is authorized by this document.

## Scientific Question

After valid SupCon/DG smoke tests and targeted pair/sampler ablations failed to deliver stable held-out subject gains, is the remaining blocker primarily:

1. label semantics,
2. representation transfer,
3. task formulation,
4. objective/metric mismatch?

## Core Rationale

The pair/sampler failure analysis accepted this diagnosis:

`pair_sampler_valid_but_not_primary_failure_mode`

The strongest targeted candidate was `A5_cross_subject_supcon_vrex`, but it remained insufficient.

This means the next analysis must move one level deeper. The question is no longer "did the pair sampler work?" but "why did valid pairs and valid regularization not produce generalizable affect recognition?"

## Authorized Scope

Authorized:

- read-only analysis of committed predictions, run summaries, label audits, representation diagnostics, and cache indices
- cross-subject label-semantics audit
- representation transfer audit
- task formulation audit
- objective/metric alignment audit

Not authorized:

- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change
- new model training
- new feature-engineering training

## Required Analysis Questions

The report must answer:

1. Do same binary valence/arousal labels represent comparable affective semantics across subjects?
2. Do subject-relative labels improve semantic consistency, or do they remove between-subject transfer signal?
3. Do EEG/EMG representations separate class labels in ways that are stable across held-out subjects?
4. Are hard folds/hard subjects explained by label distribution, representation shift, or model objective mismatch?
5. Do SupCon/DG loss or embedding diagnostics correlate with held-out macro-F1 after controlling for modality/task/fold?
6. Is the current task formulation scientifically defensible for LOSO-style claims?
7. Which next step is justified: label/task redesign, representation redesign, objective redesign, or stopping this path?

## Required Inputs

Use the following evidence where available:

- `docs/idare_supcon_dg_pair_sampler_failure_analysis_report.json`
- `docs/idare_supcon_dg_pair_sampler_failure_candidate_deltas.csv`
- `docs/idare_supcon_dg_pair_sampler_failure_fold_subject_summary.csv`
- `docs/idare_supcon_dg_pair_sampler_failure_loss_alignment.csv`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_predictions.csv`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_runs.csv`
- `docs/idare_label_noise_subject_balance_summary.csv`
- `docs/idare_representation_signal_diagnostic_summary.csv`
- `docs/idare_subject_relative_label_balance_summary.csv`
- `docs/idare_subject_relative_candidate_matrix.csv`
- `.cache/idare_eeg_cache_index_baseline_corrected.csv`
- `.cache/idare_emg_feature_cache_index.csv`

## Expected Outputs

The next command/script should create:

- `docs/idare_representation_or_label_semantics_failure_analysis_report.md`
- `docs/idare_representation_or_label_semantics_failure_analysis_report.json`
- `docs/idare_label_semantics_cross_subject_audit.csv`
- `docs/idare_representation_transfer_failure_summary.csv`
- `docs/idare_task_formulation_failure_decision_matrix.csv`
- `docs/idare_objective_metric_alignment_summary.csv`

## Pass Criteria

The objective passes only if:

1. analysis is read-only and uses committed outputs/caches,
2. label semantics, representation transfer, task formulation, and objective/metric mismatch are separated,
3. the report explains why valid pair/sampler and SupCon/DG interventions were insufficient,
4. exactly one next objective is recommended, or the path is explicitly stopped/parked,
5. no new training, fusion, or broad hyperparameter search is authorized.

## Next Allowed Step

Prepare a reviewed read-only representation or label-semantics failure-analysis command/script.

## Blocked Steps

- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change
- new training before representation/label-semantics failure analysis review
