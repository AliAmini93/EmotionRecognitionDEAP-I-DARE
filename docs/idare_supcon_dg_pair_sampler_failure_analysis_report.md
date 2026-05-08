# I-DARE SupCon/DG Pair-Sampler Failure Analysis Report

## Status

Status: complete; pending human review.

Created UTC: `2026-05-08T10:40:16+00:00`

This is a read-only analysis. No new training was run.

## Executive Diagnosis

Diagnosis: `pair_sampler_valid_but_not_primary_failure_mode`

Recommended next objective: `representation_or_label_semantics_failure_analysis_objective`

The targeted pair/sampler ablation passed smoke/guardrail checks and completed `120` runs, but it still did not produce a stable subject-heldout improvement.

The best aggregate candidate was `A5_cross_subject_supcon_vrex` with mean macro-F1 `0.5119` and mean balanced accuracy `0.5164`.

## Candidate-Level Summary

| candidate_id | candidate_label | n_runs | mean_macro_f1 | std_macro_f1 | mean_bal_acc | folds_over_055_macro_f1 | folds_under_050_macro_f1 | mean_pos_cov |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A5_cross_subject_supcon_vrex | cross-subject SupCon + VREx | 24 | 0.5119 | 0.0274 | 0.5164 | 2 | 7 | 1.0000 |
| A0_CE_control | CE control | 24 | 0.5088 | 0.0292 | 0.5144 | 1 | 8 | 0.0000 |
| A4_rating_distance_guarded_supcon | rating-distance guarded SupCon | 24 | 0.5071 | 0.0304 | 0.5131 | 1 | 11 | 1.0000 |
| A2_cross_subject_positive_only | cross-subject SupCon only | 24 | 0.5061 | 0.0319 | 0.5127 | 3 | 12 | 1.0000 |
| A6_vrex_only_recheck | VREx only | 24 | 0.5048 | 0.0301 | 0.5110 | 1 | 11 | 0.0000 |

## A5 vs Controls

A5 was the intended strongest targeted candidate: cross-subject SupCon plus VREx.

- A5 mean macro-F1: `0.5119`
- A0 CE-control mean macro-F1: `0.5088`
- A6 VREx-only mean macro-F1: `0.5048`
- A2 cross-subject SupCon-only mean macro-F1: `0.5061`
- A4 rating-distance guarded SupCon mean macro-F1: `0.5071`
- A5 delta vs A0: `0.0031`
- A5 delta vs A6: `0.0071`
- A5 delta vs A2: `0.0058`

Interpretation: A5 was not clearly separable from the best control/regularizer variants. The improvement, where present, is small and fold-dependent rather than stable.

## Modality/Task Delta Map

| candidate_id | modality | task | mean_macro_f1 | delta_vs_A0_macro_f1 | delta_vs_A6_macro_f1 | folds_over_055_macro_f1 | folds_under_050_macro_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A5_cross_subject_supcon_vrex | EMG | arousal | 0.5197 | 0.0161 | 0.0033 | 1 | 1 |
| A4_rating_distance_guarded_supcon | EEG | arousal | 0.5304 | 0.0150 | 0.0195 | 1 | 1 |
| A2_cross_subject_positive_only | EEG | arousal | 0.5285 | 0.0131 | 0.0176 | 1 | 0 |
| A6_vrex_only_recheck | EMG | arousal | 0.5164 | 0.0128 | 0.0000 | 1 | 2 |
| A5_cross_subject_supcon_vrex | EEG | arousal | 0.5236 | 0.0082 | 0.0128 | 0 | 1 |
| A2_cross_subject_positive_only | EMG | arousal | 0.5090 | 0.0054 | -0.0074 | 1 | 3 |
| A5_cross_subject_supcon_vrex | EMG | valence | 0.4950 | 0.0016 | 0.0127 | 0 | 3 |
| A4_rating_distance_guarded_supcon | EMG | arousal | 0.5042 | 0.0007 | -0.0122 | 0 | 4 |
| A0_CE_control | EEG | valence | 0.5228 | 0.0000 | 0.0132 | 0 | 0 |
| A0_CE_control | EEG | arousal | 0.5154 | 0.0000 | 0.0045 | 0 | 1 |
| A0_CE_control | EMG | arousal | 0.5036 | 0.0000 | -0.0128 | 1 | 4 |
| A0_CE_control | EMG | valence | 0.4934 | 0.0000 | 0.0111 | 0 | 3 |
| A6_vrex_only_recheck | EEG | arousal | 0.5109 | -0.0045 | 0.0000 | 0 | 3 |
| A4_rating_distance_guarded_supcon | EMG | valence | 0.4834 | -0.0100 | 0.0011 | 0 | 4 |
| A6_vrex_only_recheck | EMG | valence | 0.4823 | -0.0111 | 0.0000 | 0 | 4 |
| A2_cross_subject_positive_only | EMG | valence | 0.4820 | -0.0113 | -0.0002 | 0 | 5 |
| A4_rating_distance_guarded_supcon | EEG | valence | 0.5104 | -0.0124 | 0.0007 | 0 | 2 |
| A6_vrex_only_recheck | EEG | valence | 0.5096 | -0.0132 | 0.0000 | 0 | 2 |
| A5_cross_subject_supcon_vrex | EEG | valence | 0.5092 | -0.0137 | -0.0005 | 1 | 2 |
| A2_cross_subject_positive_only | EEG | valence | 0.5048 | -0.0180 | -0.0048 | 1 | 4 |

## Loss / Embedding Alignment

The aligned loss/embedding table is saved to:

`docs/idare_supcon_dg_pair_sampler_failure_loss_alignment.csv`

Top absolute correlations between final logged loss/embedding metrics and validation outcomes:

| metric | target | n | pearson_r |
| --- | --- | --- | --- |
| ce_loss | macro_f1 | 120 | -0.3001 |
| ce_loss | bal_acc | 120 | -0.2436 |
| supcon_loss | macro_f1 | 120 | 0.0182 |
| supcon_loss | bal_acc | 120 | 0.0176 |

Interpretation: if contrastive/embedding diagnostics do not track validation macro-F1, then SupCon may be optimizing an internal geometry that is not aligned with the held-out subject decision boundary.

## Fold and Subject Localization

The fold/subject summary is saved to:

`docs/idare_supcon_dg_pair_sampler_failure_fold_subject_summary.csv`

Subject-level summaries were available. Total hard-subject counts across fold/candidate cells: `312`.

The ablation remains fold-sensitive. This supports the view that the main blocker is not merely positive-pair availability, but the interaction among subject-specific affect labels, weak representations, and held-out subject shift.

## Decision Matrix

| hypothesis | verdict | evidence_for | evidence_against |
| --- | --- | --- | --- |
| Implementation/leakage failure | unlikely_primary | Smoke and guardrail checks were required and passed before ablation training. | All 120 runs completed; one-class prediction count remains zero in candidate-level aggregation. |
| Positive-pair coverage failure | unlikely_primary | SupCon variants depend on enough positives per batch/fold. | SupCon candidates have mean positive-pair coverage near 1.0 but still hover near chance. |
| Pair design semantic-noise failure | supported_partial | Cross-subject positives may connect trials with the same binary label but different subject-specific affect semantics. | A5 and A4 sometimes improve isolated cells, so pair design is not fully useless. |
| VREx / DG regularizer mismatch | supported_but_insufficient | A6 VREx-only mean macro-F1=0.5048; A5 mean macro-F1=0.5119; A5-A6 delta=0.0071. | VREx alone is also unstable and not sufficient. |
| Representation or label/task semantic bottleneck | most_supported | Valid pairs and valid smokes do not translate into stable held-out subject performance; this matches previous subject-variability and label/task diagnoses. | Some fold/task cells exceed 0.55, so the signal is weak/intermittent rather than absent. |

## Scientific Conclusion

The strongest supported interpretation is that the targeted pair/sampler changes were valid but insufficient. Positive-pair coverage was high, and the runs were not broken, but the learned representation did not become stable enough across held-out subjects.

This shifts the likely failure mode away from simple pair coverage and toward:

1. subject-specific label/task semantics,
2. representation weakness under subject-heldout transfer,
3. SupCon/VREx objective mismatch with the actual LOSO-style decision boundary.

## Next Allowed Step

Human review / closeout before any next objective.

Full SupCon/DG training remains blocked. Broad hyperparameter search remains blocked.
