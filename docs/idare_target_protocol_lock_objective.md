# I-DARE Target/Protocol Lock Objective

## Status

`created`

## Objective ID

`idare_target_protocol_lock_objective`

## Scope

Control Tower documentation/target-protocol lock only.

Forbidden:
- no execution
- no runner creation
- no new audit
- no experiments
- no model results
- no Wave 2 execution
- no DG execution
- no model-capacity probe
- no augmentation
- no representation redesign v2
- no DEAP execution
- no fusion execution
- no preprocessing changes
- no threshold changes
- no main push

## Human Target Policy Decision

The approved lock direction is:

- `P1_LABEL_TASK_REDESIGN = PRIMARY`
- `P2_PROTOCOL_TARGET_RECONCILIATION = PRIMARY`
- `P0_CURRENT_HELD_OUT_BINARY_AROUSAL = COMPARATOR_ONLY`
- `P3_SUBJECT_RELATIVE_WITHIN_SUBJECT = SCOPED_DIAGNOSTIC_CANDIDATE_ONLY`
- `P4_STOP_PIVOT = FALLBACK_ONLY`

## Project-Level Target

The long-range project target remains:

- datasets: I-DARE and DEAP
- tasks: valence and arousal
- modalities: EEG and EMG single-modality first
- later: EEG+EMG fusion only after single-modality readiness
- evaluation: cross-subject / held-out-subject target, unless protocol reconciliation proves a different target is needed

## Current Ruling

The current I-DARE held-out-subject binary arousal target is retained only as a comparator/continuity reference.

It is not the final target for new modeling.

## Label/Task Policy Candidates

Future policy lock must explicitly choose among:

| Candidate | Meaning | Current status |
|---|---|---|
| L0 current binary midpoint-as-high | existing continuity comparator | comparator only |
| L1 discard midpoint | prior label-policy ablation candidate | reuse prior I-DARE evidence |
| L2 midpoint-as-low | prior label-policy ablation candidate | reuse prior I-DARE evidence |
| L3 subject-relative label/task | diagnostic candidate | not auto-mainline |
| L4 within-subject preference/ranking | diagnostic candidate | scoped only |
| L5 dataset-specific policy by task/modality | reviewable | requires explicit lock |

## Evaluation Protocol Candidates

Future protocol lock must explicitly choose among:

| Candidate | Meaning | Current status |
|---|---|---|
| E0 current held-out-subject / cross-subject | strict target | comparator/reference until reconciled |
| E1 paper-aligned protocol if different | protocol reconciliation target | must be documented before claims |
| E2 subject-relative / within-subject evaluation | alternate scientific question | diagnostic candidate only |
| E3 final paper-level protocol | not locked | requires separate final protocol decision |

## Prior I-DARE Evidence To Reuse

The prior I-DARE label-policy ablation is reused as valid controlled evidence, not final LOSO/paper evidence:

- 2 tasks: valence and arousal
- 2 modalities: EEG and EMG
- 3 label policies
- 2 recipes
- 6 folds
- 144 total runs

Best prior I-DARE label-policy cells:

| Modality | Task | Best policy | Best recipe | Mean BA | Reuse decision |
|---|---|---|---|---:|---|
| EEG | valence | discard_midpoint | balanced_sampler_ce | 0.5219 | reuse; no rerun by default |
| EEG | arousal | midpoint_as_high | ce_class_weighted | 0.5416 | reuse; moderate evidence, candidate for confirmation only |
| EMG | valence | midpoint_as_high | ce_class_weighted | 0.5202 | reuse; no rerun by default |
| EMG | arousal | discard_midpoint | ce_class_weighted | 0.5365 | reuse; moderate evidence, candidate for confirmation only |

The broader standardized single-modality evaluation is reused as additional single-modality context, not a final claim.

## Missing / Not Yet Locked

| Area | Status |
|---|---|
| DEAP equivalent target-policy coverage | missing / not authorized |
| EEG+EMG fusion target-policy coverage | missing / frozen |
| final paper-level protocol | not locked |
| subject-relative/within-subject target | candidate only |
| final label policy | not locked |
| final cross-dataset claim | not authorized |

## Minimal Future Execution Matrix After Lock

No execution is authorized here.

If future execution is later authorized, the minimal matrix should avoid duplicate runs and should be selected from:

1. confirmation of existing best I-DARE cells,
2. missing DEAP equivalent after protocol lock,
3. fusion readiness only after single-modality target is locked,
4. inductive-bias comparison only after target/policy lock,
5. learning-curve/data-size diagnosis only if target is defensible.

The default recommendation is:

- do not rerun the 144-run I-DARE label-policy matrix,
- reuse it as prior evidence,
- confirm only selected best cells if needed,
- prioritize missing target/protocol coverage, not duplicate ablation.

## Comparator / Diagnostic / Paper-Level Distinction

| Class | Meaning |
|---|---|
| Comparator | Existing target retained only for continuity and comparison |
| Diagnostic candidate | Allowed for interpretation, not paper-level target |
| Paper-level target | Requires explicit final protocol/label-policy lock and later evidence |

## Next State

`REQUEST_TARGET_PROTOCOL_LOCK_REVIEW_AND_MINIMAL_EXECUTION_DECISION`
