# I-DARE Subject-relative Task Formulation Review Status

## Status

Frozen human-review closeout.

The subject-relative task formulation report has been reviewed and accepted.

Reviewed report: `docs/idare_subject_relative_task_formulation_report.md`

Reviewed JSON: `docs/idare_subject_relative_task_formulation_report.json`

## Review Decision

The report is accepted.

Selected formulation:

`subject_top_bottom_quantile_q33`

Selected next objective:

`minimal_subject_relative_training_objective`

## Accepted Findings

- Subject-relative top/bottom quantile formulation directly targets the diagnosed label/task subject-dependence blocker.
- It uses only within-subject extremes and discards ambiguous middle trials.
- It is lower coverage than z-score/median candidates, but gives cleaner labels for a first controlled training test.
- The report itself did not authorize training; a separate minimal controlled training objective is required.

## Not Authorized

- EEG+EMG fusion
- final LOSO / final paper claim
- final global label-policy lock
- architecture ablation for improvement
- data augmentation
- SupCon / VREx / domain generalization
- broad hyperparameter search
- mainline change

## Next Allowed Step

Create the minimal subject-relative training objective.

Only that objective may authorize the first small controlled training run.
