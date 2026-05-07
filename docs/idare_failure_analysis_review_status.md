# I-DARE Failure Analysis Review Status

## Status

Frozen human-review closeout.

The failure-analysis report has been reviewed and accepted as the current diagnostic checkpoint.

Reviewed report: `docs/idare_failure_analysis_report.md`

Reviewed JSON: `docs/idare_failure_analysis_report.json`

## Review Decision

The report confirms that the current problem is not solved by simply switching BSL-stats, label policy, or recipe.

Main decision:

- Do not start new blind training.
- Do not start EEG+EMG fusion.
- Do not start architecture / augmentation / DG work.
- Do not lock a final global label policy.
- Move to a controlled root-cause diagnostic objective.

## Accepted Findings

- Many aggregate rows remain close to chance/majority behavior.
- Failure labels are dominated by weak-signal / near-chance and fold-specific instability.
- Best label policies are mixed by modality/task.
- BSL-stats and label-policy changes do not justify mainline changes or fusion.
- The next work should localize likely root causes before prescribing fixes.

## Next Allowed Step

Create and review `docs/idare_root_cause_diagnostic_objective.md`.

That objective must start with read-only diagnosis from existing predictions and reports.

## Intentionally Not Started

- new performance training
- EEG+EMG fusion
- final LOSO / final paper claim
- final global label-policy lock
- architecture ablation
- data augmentation
- SupCon / VREx / domain generalization
