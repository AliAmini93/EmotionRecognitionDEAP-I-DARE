# I-DARE Post Strict NTD Smoke Synthesis and Pivot Decision

## Status

`created`

## Scope

Control Tower documentation/decision only.

Forbidden:
- no experiments
- no runner creation
- no Wave 2 execution
- no W2E execution
- no DG execution
- no model-capacity probe
- no augmentation
- no DEAP
- no fusion
- no preprocessing changes
- no threshold changes
- no main push

## Current Official State

- `WAVE_1 = CLOSED_ACCEPTED`
- `STRICT_NTD_NORM_SMOKE = ACCEPTED_CLEAN_WEAK_EFFECT`
- `STRICT_NTD_NORM_SMOKE_GATE = NO_PASS`
- `FOLLOWUP_EXECUTION = NOT_AUTHORIZED`

## Evidence Summary

| Evidence | Finding | Interpretation |
|---|---|---|
| Wave 1 performance gate | failed | No tested branch produced aggregate performance pass. |
| W1D | within-subject signal exists; cross-subject signal collapses | The problem is not total signal absence; subject identity dominates cross-subject geometry. |
| W1B | transductive rank transform reduced heterogeneity | Useful diagnostic, but not strict non-transductive evidence. |
| W1A | input-definition variants did not rescue pairwise performance | Simple tested EEG input alternatives are not enough. |
| W1C | EMG aggregate no-pass | EMG remains an independent reference, not next driver. |
| Strict NTD smoke | clean but weak; best S3 BA about 0.5142 | Simple strict normalization is technically feasible but not sufficient. |

## Decision Matrix

| Option | Direction | Decision | Rationale |
|---|---|---|---|
| A | Representation redesign | primary next design candidate | Since simple input-definition and strict normalization did not materially reduce cross-subject collapse, redesigning the representation is the cleanest next design path. |
| B | DG design | secondary next design candidate | W1D supports subject/domain shift, but DG execution should wait until representation assumptions are defined. |
| C | W2E interaction-grid design | deprioritized design-only | Input-definition x normalization interaction may be documented later, but weak components make it lower priority. |
| D | Model-capacity probe | deferred | Without a better representation/operating point, capacity probing risks noise chasing. |
| E | Augmentation | deferred | Augmentation before representation and leakage design is premature. |
| F | Stop/pivot/rethink | reviewable fallback | If representation redesign design is judged too broad or weak, a controlled project rethink is appropriate. |

## Control Decision

Representation redesign is the primary next documentation-only design candidate.

DG design remains secondary.

No execution is authorized by this decision.

## Next State

`REQUEST_REPRESENTATION_REDESIGN_DESIGN_OBJECTIVE`
