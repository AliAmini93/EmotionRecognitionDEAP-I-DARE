# I-DARE Representation or Label-Semantics Failure Analysis Report

## Status

Status: complete; pending human review.

Created UTC: `2026-05-08T10:53:45+00:00`

This is a read-only analysis. No new training was run.

## Executive Diagnosis

Diagnosis: `label_semantics_and_representation_transfer_joint_bottleneck`

Recommended next objective: `label_semantics_task_redesign_or_stop_objective`

The pair/sampler failure analysis concluded that valid SupCon/DG pair mechanics were not enough. This report moves one level deeper and separates four possible blockers: label semantics, representation transfer, task formulation, and objective/metric mismatch.

## Why the SupCon/DG Pair-Sampler Intervention Was Insufficient

Best pair-sampler candidate from the previous report:

- mean macro-F1: `0.5119`
- folds under 0.50 macro-F1: `7`

This is not a stable held-out subject result. Since coverage/smoke/guardrails were valid, the remaining failure is more likely semantic/representational than mechanical.

## Label-Semantics Cross-Subject Audit

Output: `docs/idare_label_semantics_cross_subject_audit.csv`

Aggregate summary:

| modality | task | n_subjects | mean_rating_subject_std | global_high_rate_range | mean_global_entropy | low_entropy_subjects | low_range_subjects | mean_sr_retention | sr_high_rate_range |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EEG | arousal | 63 | 1.0007 | 0.9375 | 0.8814 | 6 | 0 | 0.8309 | 0.2812 |
| EEG | valence | 63 | 0.3801 | 0.3438 | 0.9567 | 0 | 0 | 0.8080 | 0.3125 |
| EMG | arousal | 63 | 1.0007 | 0.9375 | 0.8814 | 6 | 0 | 0.8309 | 0.2812 |
| EMG | valence | 63 | 0.3801 | 0.3438 | 0.9567 | 0 | 0 | 0.8080 | 0.3125 |

Interpretation: subject-level rating distributions and binary label balance remain a major concern. If a binary label does not mean the same affective state across subjects, cross-subject SupCon positives can be mathematically valid but semantically noisy.

## Representation Transfer Audit

Output: `docs/idare_representation_transfer_failure_summary.csv`

Top rows:

| source | candidate_id | modality | task | n_runs | mean_macro_f1 | std_macro_f1 | macro_f1_range | folds_under_050 | folds_over_055 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| runs_fold_instability | A4_rating_distance_guarded_supcon | EEG | arousal | 6.0000 | 0.5304 | 0.0240 | 0.0634 | 1.0000 | 1.0000 |
| runs_fold_instability | A2_cross_subject_positive_only | EEG | arousal | 6.0000 | 0.5285 | 0.0154 | 0.0419 | 0.0000 | 1.0000 |
| runs_fold_instability | A5_cross_subject_supcon_vrex | EEG | arousal | 6.0000 | 0.5236 | 0.0196 | 0.0548 | 1.0000 | 0.0000 |
| runs_fold_instability | A0_CE_control | EEG | valence | 6.0000 | 0.5228 | 0.0085 | 0.0234 | 0.0000 | 0.0000 |
| runs_fold_instability | A5_cross_subject_supcon_vrex | EMG | arousal | 6.0000 | 0.5197 | 0.0310 | 0.0842 | 1.0000 | 1.0000 |
| runs_fold_instability | A6_vrex_only_recheck | EMG | arousal | 6.0000 | 0.5164 | 0.0307 | 0.0721 | 2.0000 | 1.0000 |
| runs_fold_instability | A0_CE_control | EEG | arousal | 6.0000 | 0.5154 | 0.0282 | 0.0793 | 1.0000 | 0.0000 |
| runs_fold_instability | A6_vrex_only_recheck | EEG | arousal | 6.0000 | 0.5109 | 0.0216 | 0.0545 | 3.0000 | 0.0000 |
| runs_fold_instability | A4_rating_distance_guarded_supcon | EEG | valence | 6.0000 | 0.5104 | 0.0250 | 0.0607 | 2.0000 | 0.0000 |
| runs_fold_instability | A6_vrex_only_recheck | EEG | valence | 6.0000 | 0.5096 | 0.0343 | 0.0857 | 2.0000 | 0.0000 |
| runs_fold_instability | A5_cross_subject_supcon_vrex | EEG | valence | 6.0000 | 0.5092 | 0.0289 | 0.0858 | 2.0000 | 1.0000 |
| runs_fold_instability | A2_cross_subject_positive_only | EMG | arousal | 6.0000 | 0.5090 | 0.0401 | 0.1087 | 3.0000 | 1.0000 |
| runs_fold_instability | A2_cross_subject_positive_only | EEG | valence | 6.0000 | 0.5048 | 0.0346 | 0.0908 | 4.0000 | 1.0000 |
| runs_fold_instability | A4_rating_distance_guarded_supcon | EMG | arousal | 6.0000 | 0.5042 | 0.0281 | 0.0688 | 4.0000 | 0.0000 |
| runs_fold_instability | A0_CE_control | EMG | arousal | 6.0000 | 0.5036 | 0.0382 | 0.0849 | 4.0000 | 1.0000 |
| runs_fold_instability | A5_cross_subject_supcon_vrex | EMG | valence | 6.0000 | 0.4950 | 0.0263 | 0.0642 | 3.0000 | 0.0000 |
| runs_fold_instability | A0_CE_control | EMG | valence | 6.0000 | 0.4934 | 0.0314 | 0.0848 | 3.0000 | 0.0000 |
| runs_fold_instability | A4_rating_distance_guarded_supcon | EMG | valence | 6.0000 | 0.4834 | 0.0303 | 0.0722 | 4.0000 | 0.0000 |
| runs_fold_instability | A6_vrex_only_recheck | EMG | valence | 6.0000 | 0.4823 | 0.0272 | 0.0585 | 4.0000 | 0.0000 |
| runs_fold_instability | A2_cross_subject_positive_only | EMG | valence | 6.0000 | 0.4820 | 0.0182 | 0.0484 | 5.0000 | 0.0000 |

Interpretation: the representation has intermittent signal, but it is not stable under held-out subject transfer. This is consistent with the repeated pattern of isolated good folds and weak aggregate performance.

## Objective / Metric Alignment Audit

Output: `docs/idare_objective_metric_alignment_summary.csv`

Top rows:

| analysis | candidate_id | metric | n | mean_macro_f1 | mean_delta_vs_A0_macro_f1 | corr_with_macro_f1 | corr_with_bal_acc |
| --- | --- | --- | --- | --- | --- | --- | --- |
| loss_embedding_metric_alignment |  | ce_loss | 120.0000 |  |  | -0.3001 | -0.2436 |
| loss_embedding_metric_alignment |  | supcon_loss | 120.0000 |  |  | 0.0182 | 0.0176 |
| candidate_delta_map | A0_CE_control |  |  | 0.5088 | 0.0000 |  |  |
| candidate_delta_map | A2_cross_subject_positive_only |  |  | 0.5061 | -0.0027 |  |  |
| candidate_delta_map | A4_rating_distance_guarded_supcon |  |  | 0.5071 | -0.0017 |  |  |
| candidate_delta_map | A5_cross_subject_supcon_vrex |  |  | 0.5119 | 0.0031 |  |  |
| candidate_delta_map | A6_vrex_only_recheck |  |  | 0.5048 | -0.0040 |  |  |

Interpretation: if loss/embedding summaries do not align with held-out macro-F1, then CE/SupCon/VREx can optimize internal objectives without producing the subject-generalizable decision boundary we need.

## Task Formulation Decision Matrix

Output: `docs/idare_task_formulation_failure_decision_matrix.csv`

| hypothesis | verdict | evidence_for | evidence_against |
| --- | --- | --- | --- |
| Label semantics across subjects are inconsistent | supported_primary | Subject rating distributions vary; mean global entropy=0.919; high_subject_rating_shift=True; low_entropy_problem=True. | Subject-relative formulations were tried, so label semantics alone may not be the only blocker. |
| Representation transfer is weak under held-out subjects | supported_primary | Best pair/SupCon/DG candidate mean macro-F1=0.5119; folds_under_050=7; candidate improvements are fold-dependent. | Some isolated folds/cells exceed 0.55, so signal is intermittent rather than absent. |
| Task formulation is not currently defensible for a final LOSO claim | supported_primary | Global labels, subject-relative labels, preprocessing, SupCon, pair redesign, and VREx all failed to create stable held-out performance. | A few cells improve, so a redesigned task may still be viable. |
| Objective/metric mismatch explains SupCon/DG failure | supported_partial | Loss/embedding metric alignment with held-out macro-F1 appears weak; max_abs_corr=0.3001215860428951. | Correlation evidence is post-hoc and based on logged summaries, not a controlled causal test. |
| Pair sampler remains the primary issue | not_primary | Pair design may still contain semantic noise. | Coverage and smoke tests passed; targeted pair/sampler changes were not sufficient. |

## Scientific Conclusion

The current evidence supports a joint bottleneck:

1. label semantics are likely not stable enough across subjects,
2. representation transfer remains weak,
3. valid SupCon/DG pair mechanics do not fix that by themselves,
4. the current task formulation is not yet defensible for a final LOSO-style claim.

The most scientific next move is not another broad training run. The next move should explicitly decide whether the task should be redesigned, narrowed, parked, or reframed before any further model work.

## Next Allowed Step

Human review / closeout before the next objective.

Direct full SupCon/DG training remains blocked. Broad hyperparameter search remains blocked. EEG+EMG fusion and final LOSO claims remain blocked.
