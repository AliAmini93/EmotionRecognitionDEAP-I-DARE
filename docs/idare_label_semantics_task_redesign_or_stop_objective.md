# I-DARE Label-Semantics Task-Redesign-or-Stop Objective

## Status

Status: objective created; read-only decision analysis only.

Created UTC: `2026-05-08T10:59:14+00:00`

## Scientific Question

Given the diagnosis `label_semantics_and_representation_transfer_joint_bottleneck`, should the current I-DARE binary affect-recognition task be redesigned, narrowed, paused, or stopped before any further training?

## Core Principle

No more model-side fixes should be tried until the task-level assumptions are explicitly reviewed.

The problem may not be "SupCon not strong enough." The problem may be that the current labels, subject variability, and LOSO claim do not define a stable enough supervised target.

## Authorized Work

This objective authorizes only read-only decision analysis:

1. Review existing reports and committed output tables.
2. Compare task-level alternatives.
3. Identify evidence gaps.
4. Recommend one next objective only after a task-level decision.

## Candidate Decisions to Evaluate

| Candidate | Meaning |
|---|---|
| Stop/archive current path | Conclude current task is not scientifically defensible enough for continued training. |
| Pause and redesign labels | Keep data and pipeline, but redefine the target before new training. |
| Subject-relative binary task | Use per-subject top/bottom affect labels only if evidence supports semantic validity. |
| Ordinal/regression task | Preserve rating information instead of binary discretization. |
| Restricted high-confidence cohort/task | Use only subjects/items with sufficient rating spread and label confidence, with anti-cherry-picking guardrails. |
| Personalization/few-shot adaptation | Treat subject variability as the central scientific problem rather than a nuisance. |

## Required Analysis Questions

- Does the current global binary task have enough cross-subject semantic consistency?
- Did subject-relative labels fail because the idea is wrong, or because the representation/training setup was too weak?
- Is LOSO-only final performance still a valid scientific target?
- Would ordinal/regression labels better match the DEAP-style affect scores?
- Is there a defensible restricted-cohort task that avoids cherry-picking?
- What condition would make us stop this experimental branch?

## Expected Outputs

- `docs/idare_label_semantics_task_redesign_or_stop_report.md`
- `docs/idare_label_semantics_task_redesign_or_stop_report.json`
- `docs/idare_label_semantics_task_redesign_or_stop_decision_matrix.csv`
- `docs/idare_label_semantics_task_candidate_matrix.csv`
- `docs/idare_label_semantics_evidence_gap_audit.csv`

## Pass Criteria

- No new training is run.
- The report clearly distinguishes stop, pause, redesign, and narrow-validation options.
- Any recommended continuation must explain exactly what assumption it tests.
- direct full SupCon/DG training remains blocked.
- Broad hyperparameter search remains blocked.
- EEG+EMG fusion and final LOSO claim remain blocked.

## Next Allowed Step

Prepare reviewed read-only label-semantics task-redesign-or-stop report command.

- broad hyperparameter search remains blocked.
