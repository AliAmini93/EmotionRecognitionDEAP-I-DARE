# I-DARE Branch Consolidation Merge Policy

## Purpose

This document records the policy for consolidating historical I-DARE experiment branches into the current ROCA branch.

Current truth branch:

- `roca-idare-killtest`

Main branch status:

- `main` was accidentally merged with ROCA once.
- That merge was reverted.
- `main` is restored to its pre-merge content and should not be used as the active I-DARE research branch.

## Why document before merging?

The old `idare/*` branches contain useful historical evidence, but they are not necessarily the current conclusion.

Before merging them into ROCA, each branch must be treated as one of:

1. **Historical evidence**
2. **Method notes**
3. **Artifact to preserve**
4. **Result superseded by newer locked-gate ROCA evidence**
5. **Branch requiring manual review before inclusion**

This prevents old exploratory results from being confused with the final locked-gate conclusion.

## Current scientific conclusion to preserve

The current ROCA conclusion remains:

- Strict LOSO global raw EEG/EMG residual decoding did not pass the locked gates.
- Generic Gaussian augmentation did not fix the LOSO residual problem.
- Raw neural EEG capacity/augmentation search did not beat the practical gates.
- The dominant issue is subject calibration/domain shift plus weak transferable residual identifiability.
- Explicit calibration/personalization helped more than blind global modelling.
- Any positive future claim must be framed as calibrated / personalized / adaptation-assisted, not pure zero-calibration LOSO.

## Merge rule

Do not merge old branches as if they are newer truth.

Merge them only to preserve:

- documentation,
- audit artifacts,
- historical experiment outputs,
- reproducibility scripts,
- evidence supporting why certain routes were stopped.

If conflicts happen, prefer the current ROCA locked-gate conclusion files over older branch conclusions.

## Branch handling policy

| Branch family | Policy |
|---|---|
| `idare/wave1/*` | Preserve as early evidence / diagnostics |
| `idare/postwave1/strict-ntd-norm-smoke` | Preserve as normalization/DG evidence |
| `idare/postwave1/representation-redesign-*` | Preserve as representation redesign evidence |
| `idare/postwave1/root-cause-triage` | Preserve as root-cause evidence |
| `idare/postwave1/label-task-protocol-reconciliation` | Preserve as protocol/label decision evidence |
| `idare/postwave1/idare-prior-best-cell-confirmation` | Preserve as prior-best verification evidence |
| `idare/postwave1/data-augmentation-track` | Preserve as historical augmentation evidence only |
| `idare/control-tower` | Preserve as planning/control documentation only |

## Final merge destination

All consolidation should happen first on:

- `roca-consolidate-branches`

Only after inspection, this branch may be merged back into:

- `roca-idare-killtest`

Do not merge this work into `main` unless the project explicitly decides that ROCA should become the public/default project state.
