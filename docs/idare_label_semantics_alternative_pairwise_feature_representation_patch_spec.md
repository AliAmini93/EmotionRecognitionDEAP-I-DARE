# I-DARE Alternative Pairwise Feature-Representation Patch Spec

## Status

Status: complete; pending human review; no training is authorized.

Created UTC: `2026-05-09T00:47:54+00:00`

## Executive Selection

Selected primary patch: `PATCH_A_eeg_arousal_bandpower_temporal_stats_v1`

Selected auxiliary control: `PATCH_C_eeg_arousal_bandpower_only_control_v1`

Selected branch: `EEG / arousal / within_subject_pairwise_affect_preference_ranking_v1`

Recommended next objective: `label_semantics_alternative_pairwise_feature_representation_patch_smoke_tests_objective`

## Why This Patch Was Selected

The metric-debug report found a weak but consistent pairwise signal:

- Current best model: `ridge_classifier_pairwise_summary_diff`
- Current best mean balanced accuracy: `0.521671`
- Delta vs majority baseline: `0.021671`
- Positive-delta folds: `6` / `6`
- Subject positive-lift fraction: `0.603175`

This supports a narrow representation patch. It does not support broad model search, SupCon/DG, fusion, or a final LOSO claim.

## Frozen Label Formulation

`within_subject_pairwise_affect_preference_ranking_v1`

No label semantic change is permitted in this patch branch.

## Candidate Matrix Considered

| candidate_id | scope | feature_patch | priority |
| --- | --- | --- | --- |
| PATCH_A_eeg_arousal_bandpower_temporal_stats_v1 | EEG/arousal only | add compact bandpower plus temporal statistics to current pairwise summary-diff features | 1 |
| PATCH_B_eeg_arousal_robust_subject_relative_scaling_v1 | EEG/arousal only | apply train-fold-only robust feature scaling and subject-relative normalization audit | 2 |
| PATCH_C_eeg_arousal_bandpower_only_control_v1 | EEG/arousal only | bandpower-only control to isolate whether temporal raw summary is the bottleneck | 3 |
| PATCH_D_emg_valence_negative_control_v1 | EMG/valence negative control | optional negative-control cell using same classical pairwise pipeline | 4 |

## Selected Feature Sets

| feature_set_id | modality | task | feature_blocks | role |
| --- | --- | --- | --- | --- |
| current_summary_diff_control | EEG | arousal | current mean/std/min/max-style summary diff as already used | control to preserve comparability with first pass |
| bandpower_temporal_stats_v1 | EEG | arousal | per-channel temporal mean/std/rms/line-length plus coarse bandpower summary over fixed bands; pairwise diff and absolute diff | primary narrow patch candidate |
| bandpower_only_control_v1 | EEG | arousal | coarse bandpower summary only; pairwise diff and absolute diff | diagnostic control for spectral vs temporal contribution |
| robust_scaled_current_summary_diff_control | EEG | arousal | current summary-diff features with fold-local robust/standard scaling audit | normalization control |

## Frozen Future Run Matrix

Run matrix: `docs/idare_label_semantics_alternative_pairwise_feature_representation_patch_run_matrix.csv`

Rows: `96`

Status: matrix defined for future reviewed execution; not authorized by this spec.

## Metric Thresholds

| threshold_id | metric | comparison | decision |
| --- | --- | --- | --- |
| T1_actionable_patch_signal | mean_balanced_accuracy | >= 0.55 on best learned patch cell | candidate for narrow confirmation objective if also fold stability passes |
| T2_fold_stability | folds_over_055_bal_acc | >= 3 folds and no folds under 0.45 | supports non-spurious patch signal |
| T3_control_lift | delta_vs_majority_baseline_bal_acc | >= +0.03 | practical improvement over majority control |
| T4_subject_lift | subject_positive_lift_fraction | >= 0.65 | supports broader subject-level lift |
| T5_archive_floor | mean_balanced_accuracy | < 0.53 or no improvement over current first-pass best | archive patch branch or redesign representation; do not broaden search |

## Stop / Archive Criteria

See: `docs/idare_label_semantics_alternative_pairwise_feature_representation_patch_stop_criteria.csv`

## Reproducibility Plan

See: `docs/idare_label_semantics_alternative_pairwise_feature_representation_patch_reproducibility_plan.csv`

## Protocol Matrix

| step_id | step | authorized_now | requires_next_objective | notes |
| --- | --- | --- | --- | --- |
| P1 | smoke-test feature extraction only | no | yes | Check dimensions, finite values, fold-local transforms, pair counts. |
| P2 | run frozen patch first-pass matrix | no | yes after smoke passes | Use the 96-row matrix only if smoke tests pass and are reviewed. |
| P3 | narrow confirmation | no | yes only if thresholds pass | No final LOSO claim. |
| P4 | broad model search / SupCon / fusion | no | not allowed from this evidence | Explicitly blocked. |

## Not Authorized

- running patch training before smoke-test objective and review
- broad hyperparameter search
- direct full SupCon/DG training
- EEG+EMG fusion
- final LOSO claim
- changing label formulation during this patch branch

## Interpretation

This is a narrow design/spec closeout, not a training result. The patch is justified because the best pairwise signal is consistent across folds but below the actionable threshold.

The immediate next step is a smoke-test objective for the feature extraction and leakage guards, not patch training.

## Next Allowed Step

`create_reviewed_feature_representation_patch_smoke_tests_objective_after_human_review`
