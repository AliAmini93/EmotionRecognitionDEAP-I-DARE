# I-DARE Root-Cause Triage Runner Plan

## Status

`created`

## Plan ID

`idare_root_cause_triage_runner_plan`

## Boundary

Documentation only.

No script is created by this plan.

No triage, audit, experiment, or runner execution is authorized by this plan.

## Future Runner Purpose

If Control Tower later authorizes script creation and then separately authorizes execution, a guarded mode-based runner may collect compact diagnostic evidence across the five approved categories.

## Future Modes

Default future mode must be:

`status`

Potential future modes, only if separately authorized:

- `status`
- `inventory`
- `validate`
- `audit_label_task`
- `audit_subject_domain`
- `audit_protocol_alignment`
- `audit_representation_failure`
- `audit_null_permutation`
- `decision_matrix`
- `closeout`

## Future Guard Checks

A future runner must check:

1. branch is `idare/postwave1/root-cause-triage`
2. working tree is clean unless Control approves otherwise
3. `.cache` symlink exists
4. `.venv` symlink exists
5. output paths stay under allowed prefixes
6. no forbidden scope is requested
7. required artifacts are discoverable

Missing inputs must stop with:

`BLOCKER: <specific reason>`

## Future Report Contracts

Future reports, if execution is later authorized:

- `docs/idare_root_cause_triage_label_task_sanity_report.md/json`
- `docs/idare_root_cause_triage_subject_domain_shift_report.md/json`
- `docs/idare_root_cause_triage_protocol_alignment_report.md/json`
- `docs/idare_root_cause_triage_representation_failure_report.md/json`
- `docs/idare_root_cause_triage_null_permutation_sanity_report.md/json`
- `docs/idare_root_cause_triage_decision_matrix.md/json`

## Current Non-Execution Confirmation

This plan creates no runner.

This plan runs no audit.

This plan runs no experiment.

This plan does not modify `scripts/`.

## Next State

`AWAITING_CONTROL_REVIEW_FOR_SCRIPT_CREATION_OR_FURTHER_DOC_REFINEMENT`
