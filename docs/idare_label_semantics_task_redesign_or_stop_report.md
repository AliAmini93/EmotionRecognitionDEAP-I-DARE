# I-DARE Label-Semantics Task-Redesign-or-Stop Report

## Status

Status: complete; pending human review.

Created UTC: `2026-05-08T11:06:28+00:00`

## Executive Decision

Diagnosis: `current_global_binary_loso_task_not_defensible_for_more_model_search`

Decision: `pause_current_global_binary_loso_training_and_prepare_task_redesign_spec`

Recommended next objective: `label_semantics_task_redesign_spec_objective`

Stop condition: If a defensible redesign spec cannot be accepted, stop/archive the current binary LOSO branch.

## Why More Model Search Is Blocked

The current evidence says the bottleneck is not primarily a missing optimizer trick, pair sampler, or SupCon/DG toggle. The best targeted pair-sampler cell remained weak and unstable, and the previous report diagnosed a joint label-semantics and representation-transfer bottleneck.

Key indicators:

- best pair-sampler candidate mean macro-F1: `0.5119`

- best pair-sampler candidate folds under 0.50 macro-F1: `7`

- mean label entropy: `0.9191`

- high subject rating shift: `True`

- low entropy problem: `True`

- objective alignment weak: `True`

- max absolute loss/embedding correlation with macro-F1: `0.3001`

## Candidate Task Decisions

| candidate | decision_type | scientific_value | evidence_for | evidence_against | main_risk | recommended_role |
| --- | --- | --- | --- | --- | --- | --- |
| stop_archive_current_global_binary_loso_path | stop | high if documented honestly; prevents chasing non-defensible task | Repeated CE/SupCon/DG/preprocessing/pair-sampler attempts stayed near chance. | Some folds/cells exceed 0.55, so the data is not pure noise. | Could stop too early before testing a better task semantics. | fallback if task redesign is not accepted |
| pause_global_binary_loso_claim_and_redesign_task_semantics | pause_redesign | highest; directly targets label semantics before new modeling | Joint label-semantics and representation-transfer bottleneck; pair sampler not primary failure mode. | Requires a new spec and careful anti-cherry-picking constraints. | May delay training, but avoids uncontrolled model search. | selected |
| subject_relative_binary_top_bottom_q33 | redesign_variant | moderate; addresses subject rating scale differences | Retains within-subject semantics and reduces global-threshold mismatch. | First-pass subject-relative training was not sufficient alone. | Could still be representation-limited or too narrow for LOSO claim. | candidate for future spec only |
| ordinal_or_regression_affect_rating_task | redesign_variant | high; preserves rating magnitude instead of binary thresholding | Binary discretization likely collapses subject-specific semantics and confidence. | Needs new metrics and baselines; not directly comparable to old binary results. | May be harder, but more scientifically faithful. | primary redesign candidate |
| restricted_high_confidence_label_task | narrow_validation | moderate if pre-registered; useful as sanity validation | Can test whether low-confidence/mid ratings are diluting supervision. | High cherry-picking risk unless locked before training. | Inflated result if cohort/item selection is unconstrained. | secondary diagnostic candidate |
| personalization_or_few_shot_adaptation_task | redesign_variant | high if subject variability is central scientific target | Subject variability remains supported across many diagnostics. | Changes final claim away from pure LOSO generalization. | Requires a new claim and protocol. | alternative mainline candidate |

## Decision Matrix

| decision | verdict | reason | next_step_allowed |
| --- | --- | --- | --- |
| continue_current_global_binary_loso_training | reject | Model-side and pair/sampler interventions did not produce robust gains; label/task semantics remain unresolved. | none |
| direct_full_supcon_dg_training | reject_block | Smoke tests passed but first-pass and targeted ablations were not sufficient. | none |
| broad_hyperparameter_search | reject_block | Would obscure root cause and violate the current diagnosis workflow. | none |
| task_semantics_redesign_spec | select | Directly addresses the accepted joint label-semantics and representation-transfer bottleneck. | create reviewed task redesign spec with no training |
| stop_archive_if_redesign_not_accepted | conditional | If no defensible task redesign is accepted, the current branch should be stopped rather than patched with more models. | create stop/archive closeout |

## Evidence Gap Audit

| evidence_gap | current_state | required_before_training | blocking |
| --- | --- | --- | --- |
| task_semantic_validity | global binary labels show subject-semantics risk | pre-register a redesigned target and justify label semantics | yes |
| metric_alignment | weak objective alignment; max_abs_corr=0.3001 | define metric expected to improve and how it maps to scientific claim | yes |
| representation_transfer | best observed transfer summary remains low; repr_best=0.5304 | specify whether the task is LOSO, personalization, or few-shot adaptation | yes |
| subject_relative_interpretation | subject-relative retention estimate=0.8814; first-pass not sufficient | decide if subject-relative labels are the claim or only a diagnostic | yes |
| anti_cherry_picking_guardrails | restricted/high-confidence task not yet pre-registered | lock inclusion criteria before any new training | yes |

## Interpretation

The current global binary LOSO task should be paused as a final-performance target. Continuing with direct full SupCon/DG training or broad hyperparameter search would not answer the accepted failure mode. The scientifically cleaner path is to write a task redesign spec first, with the main candidates being ordinal/regression affect modeling, a pre-registered restricted high-confidence task, or a personalization/few-shot formulation. If none of these can be justified without cherry-picking, the current binary global-label branch should be stopped/archived.

## Next Allowed Step

Human review / closeout before one of the following:

- create a label-semantics task-redesign specification objective;

- create a stop/archive closeout objective.


Blocked until review:

- direct full SupCon/DG training

- broad hyperparameter search

- EEG+EMG fusion

- final LOSO claim

- mainline change

- new model training before task redesign spec review
