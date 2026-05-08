# I-DARE SupCon/DG Pair-Sampler Failure Analysis Review Status

## Status

Status: human review accepted.

Created UTC: `2026-05-08T10:44:24+00:00`

## Review Decision

The read-only SupCon/DG pair-sampler failure analysis is accepted as the current controlling evidence.

Accepted diagnosis: `pair_sampler_valid_but_not_primary_failure_mode`

Accepted next selected step: `representation_or_label_semantics_failure_analysis_objective`

## Result Summary

The targeted pair/sampler ablation showed that pair/sampler mechanics were valid but not the primary failure mode.

Best candidate:

- Candidate: `A5_cross_subject_supcon_vrex`
- Mean macro-F1: `0.5118600603082725`
- Mean balanced accuracy: `0.5163997255823266`

The evidence indicates that positive-pair coverage and smoke/guardrail validity were not enough to produce stable held-out subject performance.

## Interpretation Accepted by Review

The failure mode should no longer be treated as a simple pair-sampler implementation issue.

The next diagnosis must localize whether the remaining blocker is primarily:

1. label semantics across subjects,
2. representation weakness under held-out subject transfer,
3. task formulation mismatch,
4. objective/metric mismatch between training losses and held-out macro-F1.

## Blocked Steps

The following remain blocked:

- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change
- new training before representation/label-semantics failure analysis review

## Next Selected Step

Create a read-only representation or label-semantics failure-analysis objective.

## Next Allowed Step

Prepare a reviewed read-only analysis command/script for representation or label-semantics failure analysis.
