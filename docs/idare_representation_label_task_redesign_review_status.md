# I-DARE Representation and Label-task Redesign Review Status

## Status

Frozen human-review closeout.

The representation/label-task redesign diagnostic report has been reviewed and accepted.

Reviewed report: `docs/idare_representation_label_task_redesign_report.md`

Reviewed JSON: `docs/idare_representation_label_task_redesign_report.json`

## Review Decision

The report is accepted.

Leading blocker:

`label_task_subject_dependence`

Diagnosis:

`subject_relative_label_task_problem_supported`

Selected next objective:

`subject_relative_task_formulation_objective`

## Accepted Findings

- The leading blocker is label/task subject dependence.
- Global binary labels are likely unstable under subject-heldout evaluation.
- Subject-relative task formulation should be tested before architecture, fusion, augmentation, or domain generalization.
- No new performance-training claim is authorized by this review.

## Not Authorized

- EEG+EMG fusion
- final LOSO / final paper claim
- final global label-policy lock
- new model training
- architecture ablation for improvement
- data augmentation
- SupCon / VREx / domain generalization
- broad hyperparameter search
- mainline change

## Next Allowed Step

Create a subject-relative task formulation objective.

The objective must stay planning/diagnostic-first and must not start broad model training or final claims.
