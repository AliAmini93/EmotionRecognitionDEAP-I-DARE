# I-DARE Subject-variability Intervention-failure Analysis Review Status

## Status

Frozen human-review closeout.

Generated UTC: `2026-05-08T09:24:04.815694+00:00`

## Reviewed Evidence

- Report: `docs/idare_subject_variability_intervention_failure_analysis_report.md`
- JSON: `docs/idare_subject_variability_intervention_failure_analysis_report.json`
- Decision matrix: `docs/idare_subject_variability_intervention_failure_decision_matrix.csv`
- Fold/task summary: `docs/idare_subject_variability_intervention_failure_fold_task_summary.csv`

## Review Decision

Accepted.

The intervention-failure analysis conclusion is accepted:

- `subject_variability_diagnosis_still_supported_intervention_too_weak`

Mainline is unchanged.

Direct SupCon/DG training is not authorized yet.

## Scientific Interpretation

The failed subject-relative + preprocessing intervention does not falsify the subject-variability diagnosis.

It shows that the tested intervention was too weak/incomplete because:

- it relied on preprocessing and CE-only training;
- it did not explicitly align same-affect samples across subjects;
- it did not explicitly penalize subject/environment risk instability;
- it did not lock a positive/negative pair strategy or subject-aware sampler.

## Caution Requirement

The next step must stay diagnostic and staged.

Before any SupCon/DG training, the project must lock:

- explicit assumptions;
- positive/negative/hard-negative pair definitions;
- sampler validity tests;
- hyperparameter candidates and isolation rules;
- smoke tests;
- failure interpretation rules.

## Next Selected Step

Create a cautious SupCon / domain-generalization design objective:

- `docs/idare_subject_variability_supcon_dg_design_objective.md`

This is a design/spec step, not a training step.

## Not Authorized

- SupCon/DG training
- EEG+EMG fusion
- final LOSO / final paper claim
- mainline change
- architecture/augmentation work
- broad hyperparameter search
