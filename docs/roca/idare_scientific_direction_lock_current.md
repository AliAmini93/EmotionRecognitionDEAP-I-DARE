# I-DARE Scientific Direction Lock

This report locks the current scientific direction after the residual reliability, physiology, few-shot, and model-family audits.

## Current claim lock

- The project is still aiming for EEG/EMG value, but EEG/EMG must now beat a stronger personalized baseline, not just `stimulus_only`.
- `stimulus_only` is now a historical reference, not the final comparator for physiology claims.
- The currently locked baseline is `kernel_residual_shrink4` with `k=16` calibration trials.
- Future physiology work should test EEG/EMG as a personalization moderator, calibration-sample reducer, or failure-subject rescue signal.

## Decision table

| target | final_direction | residual_signal_verdict | zero_shot_physiology_verdict | fewshot_decision | physiology_after_fewshot_decision | model_family_confirmatory_decision | locked_best_model | locked_k_calibration | locked_reference_model | locked_best_rmse | locked_reference_rmse | locked_lift_vs_reference_rmse | locked_lift_vs_stimulus_rmse | paired_ci95_low | paired_signflip_p | wins | losses | win_margin | physiology_claim_status | recommended_next_focus | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | LOCK_PERSONALIZED_KERNEL_RESIDUAL_BASELINE | SUBJECT_STRUCTURED_RESIDUAL_PRESENT__ZERO_SHOT_PHYSIOLOGY_NO_GO__FEW_SHOT_RECOMMENDED | NO_GO_CONFIRMED_CURRENT_FEATURE_SET | GO_CONFIRMED_FEWSHOT_SUBJECT_CALIBRATION | NO_GO_PHYSIOLOGY_AFTER_FEWSHOT | GO_CONFIRMED_MODEL_FAMILY_CALIBRATION | kernel_residual_shrink4 | 16.000000 | bias_shrink4 | 1.657667 | 1.734361 | 0.076694 | 0.288276 | 0.046820 | 0.000050 | 47.000000 | 16.000000 | 31.000000 | PHYSIOLOGY_MUST_BEAT_LOCKED_PERSONALIZATION_BASELINE | 05ah physiology-informed personalization challenge against locked kernel baseline | A personalized residual model is now the strongest confirmed baseline. EEG/EMG is still central to the project, but future physiology claims must show incremental value over this locked subject-calibration baseline, not merely over stimulus_only. |
| valence | LOCK_PERSONALIZED_KERNEL_RESIDUAL_BASELINE | SUBJECT_STRUCTURED_RESIDUAL_PRESENT__ZERO_SHOT_PHYSIOLOGY_NO_GO__FEW_SHOT_RECOMMENDED | NO_GO_CONFIRMED_CURRENT_FEATURE_SET | WEAK_GO_FEWSHOT_NEEDS_CAUTION | NO_GO_PHYSIOLOGY_AFTER_FEWSHOT | GO_CONFIRMED_MODEL_FAMILY_CALIBRATION | kernel_residual_shrink4 | 16.000000 | bias_shrink4 | 1.159189 | 1.246118 | 0.086929 | 0.100024 | 0.056769 | 0.000050 | 43.000000 | 20.000000 | 23.000000 | PHYSIOLOGY_MUST_BEAT_LOCKED_PERSONALIZATION_BASELINE | 05ah physiology-informed personalization challenge against locked kernel baseline | A personalized residual model is now the strongest confirmed baseline. EEG/EMG is still central to the project, but future physiology claims must show incremental value over this locked subject-calibration baseline, not merely over stimulus_only. |


## Locked baselines

| target | baseline_level | baseline_name | status | rmse | how_to_use |
| --- | --- | --- | --- | --- | --- |
| arousal | B0 | stimulus_only | historical_reference_only | 1.944205 | Do not claim physiology success by beating this alone. |
| arousal | B1 | stimulus_plus_fewshot_bias_shrink4 | GO_CONFIRMED_FEWSHOT_SUBJECT_CALIBRATION | 1.733828 | Few-shot subject calibration reference. |
| arousal | B2_LOCKED | kernel_residual_shrink4 | GO_CONFIRMED_MODEL_FAMILY_CALIBRATION | 1.657667 | Locked challenge baseline for future EEG/EMG or multimodal personalization claims. |
| valence | B0 | stimulus_only | historical_reference_only | 1.257774 | Do not claim physiology success by beating this alone. |
| valence | B1 | stimulus_plus_fewshot_bias_shrink4 | WEAK_GO_FEWSHOT_NEEDS_CAUTION | 1.241848 | Few-shot subject calibration reference. |
| valence | B2_LOCKED | kernel_residual_shrink4 | GO_CONFIRMED_MODEL_FAMILY_CALIBRATION | 1.159189 | Locked challenge baseline for future EEG/EMG or multimodal personalization claims. |


## Evidence rollup

| target | subject_r2_on_residual | stimulus_r2_on_residual | subject_split_half_pearson_median | zero_shot_best_candidate_pooled_lift | fewshot_best_lift_vs_stimulus | fewshot_mean_subject_improvement | phys_after_fewshot_best_lift | model_family_lift_vs_locked | model_family_ci95_low | model_family_signflip_p | model_family_win_margin | personalization_prior_decision | personalization_prior_fewshot_best_k |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | 0.269176 | 0.000000 | 0.847820 | -0.002163 | 0.210979 | 0.194921 | -0.000802 | 0.076694 | 0.046820 | 0.000050 | 31.000000 | PIVOT_TO_PERSONALIZATION_FEWSHOT | 16.000000 |
| valence | 0.092777 | 0.000000 | 0.549355 | -0.001378 | 0.014743 | 0.016499 | -0.001151 | 0.086929 | 0.056769 | 0.000050 | 23.000000 | PIVOT_TO_PERSONALIZATION_FEWSHOT | 16.000000 |


## Physiology challenge matrix

| target | challenge | required_comparator | required_k | minimum_evidence | success_interpretation | failure_interpretation |
| --- | --- | --- | --- | --- | --- | --- |
| arousal | C1_physio_moderator_over_locked_baseline | kernel_residual_shrink4 | 16.000000 | positive pooled RMSE lift + positive paired subject mean + CI low > 0 + signflip p < 0.05 + win margin > 3 | EEG/EMG provides incremental personalization value beyond subject residual calibration. | EEG/EMG does not add measurable value beyond the locked personalized baseline under this protocol. |
| arousal | C2_reduce_calibration_samples | kernel_residual_shrink4 at k=16 | 1,2,4,8 | physiology-assisted model at smaller k matches or beats locked k=16 baseline with paired evidence | EEG/EMG is useful by lowering calibration burden. | Personalization still depends mainly on explicit subject calibration samples. |
| arousal | C3_rescue_failure_subjects | kernel_residual_shrink4 | 16.000000 | improvement concentrated in locked-baseline failure subjects without pooled regression | EEG/EMG helps specific subjects even if global average lift is modest. | Physiology features are not explaining current failure modes. |
| valence | C1_physio_moderator_over_locked_baseline | kernel_residual_shrink4 | 16.000000 | positive pooled RMSE lift + positive paired subject mean + CI low > 0 + signflip p < 0.05 + win margin > 3 | EEG/EMG provides incremental personalization value beyond subject residual calibration. | EEG/EMG does not add measurable value beyond the locked personalized baseline under this protocol. |
| valence | C2_reduce_calibration_samples | kernel_residual_shrink4 at k=16 | 1,2,4,8 | physiology-assisted model at smaller k matches or beats locked k=16 baseline with paired evidence | EEG/EMG is useful by lowering calibration burden. | Personalization still depends mainly on explicit subject calibration samples. |
| valence | C3_rescue_failure_subjects | kernel_residual_shrink4 | 16.000000 | improvement concentrated in locked-baseline failure subjects without pooled regression | EEG/EMG helps specific subjects even if global average lift is modest. | Physiology features are not explaining current failure modes. |


## Recommended next steps

| step | title | purpose | why_now | success_condition |
| --- | --- | --- | --- | --- |
| 05ah | Physiology-informed personalization challenge | Test whether EEG/EMG improves over the locked kernel_residual_shrink4 personalization baseline. | 05af confirms the personalization baseline; the next physiology test must be stricter and targeted. | EEG/EMG model beats locked B2 baseline with paired subject-level confirmatory evidence. |
| 05ai | Calibration-sample reduction audit | Test whether EEG/EMG reduces required calibration samples, e.g. k=4 or k=8 matching k=16 personalization. | Even if EEG/EMG does not improve final RMSE, it may be valuable if it reduces subject calibration burden. | Physiology-assisted lower-k model matches or beats locked k=16 baseline without subject-level instability. |
| 05aj | Failure-subject physiology rescue audit | Focus on subjects where locked personalization still regresses and test whether physiology explains those failures. | 05af failure subjects define the most scientifically useful error surface. | Physiology improves failure-subject RMSE while preserving pooled and paired metrics. |


## Interpretation

The result is not a retreat from EEG/EMG. It is a stricter scientific framing: EEG/EMG should be evaluated only after locking the strongest non-physiology personalization baseline. If physiology can beat this baseline, reduce the calibration burden, or rescue failure subjects, the project has a stronger and more defensible claim.

## Practical next action

Build `05ah`: a physiology-informed personalization challenge against the locked `kernel_residual_shrink4, k=16` baseline, with paired subject-level confirmatory statistics and no huge prediction dumps committed.