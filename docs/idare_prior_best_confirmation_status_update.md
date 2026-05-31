# I-DARE Prior Best Confirmation Status Update

## Status

`created`

## Scope

Control Tower documentation/status update only.

Forbidden:
- no execution
- no runner creation
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

## Formal Status

`PRIOR_BEST_CONFIRMATION = ACCEPTED_CLEAN_NO_PASS`

`PRIOR_MODERATE_CELLS = NOT_ROBUSTLY_CONFIRMED`

`CURRENT_MODELING_PATH = PAUSED`

`FOLLOWUP_EXECUTION = NOT_AUTHORIZED`

## Evidence Base

The I-DARE prior-best 24-run confirmation was formally reviewed and accepted as technically clean.

Branch:

`idare/postwave1/idare-prior-best-cell-confirmation`

Latest result commit:

`2b72f40e6f1ed68090b820d6ae96a94e5de56479`

Run count:

`4 registered cells x 6 folds = 24 confirmation runs`

Technical status:

- leakage/scope audit passed
- 24/24 registered runs completed
- no blocker reported
- no one-class collapse reported as decision blocker
- no 144-run rerun occurred
- no DEAP
- no fusion
- no DG
- no Wave 2
- no model-capacity probe
- no augmentation
- no representation redesign v2
- no preprocessing change
- no threshold change
- no W1-owned edits
- no main push
- no final paper-level performance claim

## Confirmation Outcome

| Cell | Prior role | Confirmation outcome | Control ruling |
|---|---|---|---|
| C0 EEG arousal midpoint_as_high / CE weighted | prior moderate candidate | weakened, borderline | not confirmed moderate |
| C1 EEG valence discard_midpoint / balanced sampler | prior weak/best valence cell | weak | rejected as useful confirmation |
| C2 EMG arousal discard_midpoint / CE weighted | prior moderate candidate | weakened | prior moderate not confirmed |
| C3 EMG valence midpoint_as_high / CE weighted | prior weak/best valence cell | reproduced weakly | weak comparator only |

## Interpretation

The prior 144-run I-DARE label-policy matrix remains useful historical controlled evidence.

However, its apparent moderate cells did not robustly confirm in the focused 24-run confirmation.

Therefore, the prior-best cells must not be used to justify:

- DEAP escalation
- EEG+EMG fusion
- DG / Wave 2
- model-capacity probe
- augmentation
- representation redesign v2
- final paper-level operating-point claim

## Project-Level Ruling

`NO_ROBUST_IDARE_SINGLE_MODALITY_OPERATING_POINT_FOUND`

`NO_CONFIRMED_MODERATE_FINAL_CELL`

`MODELING_PATH_PAUSED_PENDING_HUMAN_DECISION`

## Required Next Human Decision

Control Tower requires a human decision between:

1. `STOP_HANDOFF`
2. `RETHINK_TARGET_PROTOCOL_MODELING_STRATEGY`
3. `REQUEST_FINAL_PROJECT_CLOSEOUT_SUMMARY`
4. `REQUEST_NON_EXECUTION_RESEARCH_WRITEUP`

No option authorizes execution by default.

## Current State

`AWAITING_STOP_HANDOFF_OR_STRATEGY_RETHINK_DECISION`
