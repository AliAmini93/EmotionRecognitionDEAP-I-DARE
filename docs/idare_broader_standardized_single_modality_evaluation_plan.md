# I-DARE Broader Standardized Single-Modality Evaluation Plan

## Status

Planning only.

No experiment is authorized by this document.

## Why this plan exists

The I-DARE single-modality BSL-stats vs baseline comparison has been reviewed.

Current decision:

- EEG mainline stays baseline-corrected `STIM-BSL`-only.
- EMG mainline stays feature-level EMG.
- BSL-stats sidecars stay controlled ablations.
- Fusion is not started.
- Current evidence is smoke/stabilization only.

This plan defines what a broader single-modality evaluation would look like if we decide to move beyond smoke evidence.

## Objective

Run a broader standardized evaluation of I-DARE single-modality models before any fusion decision.

The goal is to check whether the current smoke-level conclusions hold under a stronger and more standardized evaluation setup.

## Scientific question

Do the current I-DARE single-modality conclusions remain stable when evaluated more broadly?

Specifically:

1. Does EEG `STIM-BSL`-only remain stronger than EEG `STIM-BSL + BSL-stats`?
2. Does EMG feature-level remain the practical EMG mainline?
3. Are the small EMG BSL-stats gains stable or just smoke-level noise?

## Modalities

Include:

- I-DARE EEG.
- I-DARE EMG.

Do not include:

- EEG+EMG fusion.
- Full paired `model(BSL, STIM, STIM-BSL)`.
- Raw EMG as mainline.

## Comparisons

### EEG

Compare:

- baseline-corrected `STIM-BSL`-only EEG.
- baseline-corrected `STIM-BSL` EEG + compact BSL-stats sidecar.

### EMG

Compare:

- feature-level EMG.
- feature-level EMG + compact BSL-stats sidecar.

## Label policy

Use the current smoke policy only for controlled comparison:

- `midpoint_as_high`

But do not lock it as final.

A separate label-policy ablation is still needed before final claims.

## Required protocol alignment

All compared models should use the same:

- tasks: `valence`, `arousal`
- subject-held-out folds
- seeds
- recipes
- epochs
- learning rate
- batch size
- metrics
- threshold diagnostics
- prediction CSV schema where possible

## Minimum outputs

If this plan is later executed, expected outputs should include:

- markdown report
- JSON report
- prediction CSV files
- clear pass/fail/freeze decision
- update to central roadmap

## Pass criteria

A broader evaluation is useful if it gives a clearer answer than the current smoke comparison.

It should show:

- no data/protocol mismatch
- no accidental sidecar leakage
- no one-class collapse problem hidden in aggregates
- stable comparison across tasks
- clear documentation of failures or weak results

## What this plan does not prove

Even if executed, this plan still would not automatically prove final paper performance.

Final LOSO or final paper claims require a separate final-evaluation objective.

## Intentionally not started

This plan does not start:

- EEG+EMG fusion.
- Full `model(BSL, STIM, STIM-BSL)`.
- Final LOSO / final performance claim.
- Locking `midpoint_as_high`.
- Raw EMG mainline.
- Architecture ablations.
- Data augmentation.
- SupCon / VREx / domain generalization.

## Next allowed step after this plan

After this plan is reviewed, the next step can be one of:

1. Stop and keep the current smoke-level conclusions.
2. Refine this plan.
3. Create an explicit short-term objective to execute the broader standardized single-modality evaluation.

Do not execute the evaluation automatically.
