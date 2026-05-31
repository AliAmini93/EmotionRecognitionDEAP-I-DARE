# I-DARE Post-Wave1 Synthesis and Next Decision Objective

## Status

`created`

## Objective ID

`idare_post_wave1_synthesis_and_next_decision_objective`

## Scope

This is a Control Tower documentation/decision objective only.

Allowed:
- synthesize accepted Wave 1 closeouts.
- prepare a decision matrix for next possible directions.
- prepare for `REQUEST_POST_WAVE1_NEXT_DIRECTION_REVIEW`.

Forbidden:
- no experiments.
- no Wave 2 execution.
- no DEAP.
- no fusion.
- no preprocessing changes.
- no threshold changes.
- no branch-owned W1A/W1B/W1C/W1D file edits.
- no push to main.

## Official Wave 1 State

- `WAVE_1_FORMAL_STATUS = CLOSED_ACCEPTED`
- `WAVE_1_PERFORMANCE_GATE = FAIL`
- `WAVE_1_DIAGNOSTIC_GATE = PARTIAL_PASS`
- `WAVE_2_AUTHORIZATION = NO`

## Wave 1 Synthesis Inputs

| Branch | Finding | Interpretation |
|---|---|---|
| W1A | Tested EEG input definitions did not rescue pairwise arousal performance. | Input-definition variants alone are not enough. |
| W1B | Transductive rank transform reduced heterogeneity, but no strict non-transductive pass. | Normalization matters diagnostically, but strict evidence is missing. |
| W1C | EMG ridge aggregate no-pass. | Keep EMG as an independent reference, not a next-step driver. |
| W1D | Within-subject signal exists but cross-subject signal collapses due to subject-dominated geometry. | The core bottleneck is subject/domain shift, not total absence of affect signal. |

## Decision Target

Decide whether the next authorized step should be:

A. documentation-only W2E interaction-grid design.  
B. strict non-transductive normalization/domain-generalization design.  
C. defer model-capacity probe until a better operating point exists.  
D. defer augmentation.  
E. stop/pivot toward representation redesign.  
F. keep DEAP/fusion frozen.

## Next Control State

After this objective is committed to `idare/control-tower`, the next requested state is:

`REQUEST_POST_WAVE1_NEXT_DIRECTION_REVIEW`
