# I-DARE Target/Protocol Lock Review and Minimal Execution Decision

## Status

`created`

## Scope

Control Tower documentation/review only.

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

## Review Decision

`TARGET_PROTOCOL_LOCK_REVIEW = ACCEPTED`

The project target policy is locked at the governance level as:

- P1 label/task redesign = primary
- P2 protocol target reconciliation = primary
- P0 current held-out binary arousal = comparator only
- P3 subject-relative / within-subject = scoped diagnostic candidate only
- P4 stop/pivot = fallback only

## Minimal Execution Decision

No execution is authorized by this document.

If future execution is later authorized, Control Tower should prefer a compact confirmation of prior best I-DARE single-modality cells rather than rerunning the full prior label-policy matrix.

## Prior Coverage Reuse

The prior I-DARE label-policy ablation already covered:

- 2 tasks: valence and arousal
- 2 modalities: EEG and EMG
- 3 label policies
- 2 recipes
- 6 folds
- 144 total runs

Therefore, the 144-run matrix should be reused as valid controlled prior evidence and should not be rerun by default.

## Minimal Future Confirmation Matrix

Only if future human approval is given, the smallest defensible confirmation matrix is:

| Cell | Dataset | Modality | Task | Policy | Recipe | Prior mean BA | Role |
|---|---|---|---|---|---|---:|---|
| C0 | I-DARE | EEG | arousal | midpoint_as_high | ce_class_weighted | 0.5416 | prior best / moderate |
| C1 | I-DARE | EEG | valence | discard_midpoint | balanced_sampler_ce | 0.5219 | prior best / weaker |
| C2 | I-DARE | EMG | arousal | discard_midpoint | ce_class_weighted | 0.5365 | prior best / moderate |
| C3 | I-DARE | EMG | valence | midpoint_as_high | ce_class_weighted | 0.5202 | prior best / weaker |

Run count if later approved:

`4 cells × 6 folds = 24 confirmation runs`

## Not Recommended

Do not authorize:

- duplicate 144-run I-DARE label-policy rerun,
- DEAP equivalent before unfreeze review,
- fusion before single-modality readiness,
- DG/model-capacity/augmentation before target-policy confirmation,
- representation redesign v2 before label/protocol target is settled.

## Missing But Blocked

| Area | Status |
|---|---|
| DEAP equivalent | missing but frozen |
| EEG+EMG fusion | missing but frozen |
| paper-level final protocol | not yet evidence-locked |
| final LOSO / final claim | not authorized |

## Next State

`REQUEST_IDARE_PRIOR_BEST_CELL_CONFIRMATION_AUTHORIZATION_PACKAGE`
