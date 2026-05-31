# I-DARE Personalization Decision Synthesis

This checkpoint synthesizes 05z, 05aa, and 05ab after the residual reliability and few-shot audits.

## Final decision

| target | final_decision | residual_signal_verdict | zero_shot_physiology_verdict | fewshot_decision | physiology_after_fewshot_decision | recommended_next_action |
| --- | --- | --- | --- | --- | --- | --- |
| arousal | PIVOT_TO_PERSONALIZATION_FEWSHOT | SUBJECT_STRUCTURED_RESIDUAL_PRESENT__ZERO_SHOT_PHYSIOLOGY_NO_GO__FEW_SHOT_RECOMMENDED | NO_GO_CONFIRMED_CURRENT_FEATURE_SET | GO_FEWSHOT_SUBJECT_CALIBRATION | NO_GO_PHYSIOLOGY_AFTER_FEWSHOT | Build 05ad few-shot calibration confirmatory/stability audit before any new physiology or architecture search. |
| valence | PIVOT_TO_PERSONALIZATION_FEWSHOT | SUBJECT_STRUCTURED_RESIDUAL_PRESENT__ZERO_SHOT_PHYSIOLOGY_NO_GO__FEW_SHOT_RECOMMENDED | NO_GO_CONFIRMED_CURRENT_FEATURE_SET | WEAK_GO_FEWSHOT_CALIBRATION_NEEDS_CONFIRMATION | NO_GO_PHYSIOLOGY_AFTER_FEWSHOT | Build 05ad few-shot calibration confirmatory/stability audit before any new physiology or architecture search. |


## Evidence table

| target | subject_r2_on_residual | stimulus_r2_on_residual | subject_split_half_pearson_median | subject_split_half_pearson_q025 | fewshot_best_model | fewshot_best_k | fewshot_lift_vs_stimulus_rmse | fewshot_rmse_win_margin | phys_after_fewshot_best_block | phys_after_fewshot_best_k | phys_after_fewshot_lift_vs_fewshot_rmse | phys_after_fewshot_win_margin |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | 0.2692 | 0.0000 | 0.8478 | 0.7410 | stimulus_plus_fewshot_bias_shrink4 | 16.0000 | 0.2110 | 17.0000 | emg_lagged_interaction_experimental | 16.0000 | -0.0008 | -5.0000 |
| valence | 0.0928 | 0.0000 | 0.5494 | 0.2874 | stimulus_plus_fewshot_bias_shrink4 | 16.0000 | 0.0147 | -15.0000 | emg_lagged_interaction_experimental | 8.0000 | -0.0012 | -23.0000 |


## Interpretation lock

- The residual is not being treated as random noise: 05z shows reliable subject-structured residual bias/profile.

- The current zero-shot EEG/EMG feature blocks remain no-go against stimulus-only.

- Few-shot subject calibration is the first path that clearly changes the decision, especially for arousal.

- Adding the tested physiology blocks after few-shot calibration does not improve the few-shot baseline.

- Therefore, future claims must compare against a locked few-shot baseline, not just stimulus-only.


## Recommended next steps

| step | title | purpose | why_now | success_condition |
| --- | --- | --- | --- | --- |
| 05ad | Few-shot calibration confirmatory stability audit | Validate 05aa with paired subject statistics, calibration-size curves, bootstrap/sign tests, and subject-level failure analysis. | 05aa is the only route that clearly moves beyond stimulus-only; 05ab says physiology does not add after few-shot. | Arousal remains positive with subject-level win margin and CI/p-value support; valence is classified honestly as weak/unstable or recoverable. |
| 05ae | Subject calibration model-family comparison | Compare mean-bias, shrinkage, ridge residual calibration, hierarchical/mixed-effect calibration, and small adapter models. | 05z says residual is subject-profile structured, so the math should target subject calibration directly. | A method beats the simple few-shot bias baseline, not just stimulus-only. |
| 05af | Physiology as moderator of personalization | Use physiology only as a moderator/adapter after 05ad/05ae, not as standalone zero-shot decoder. | 05ab says current physiology does not improve after few-shot, so future physiology claims need a stricter target. | Physiology improves over the locked few-shot baseline with paired subject-level evidence. |


## Practical note

Do not start a large deep architecture search yet. The next high-value step is 05ad: a confirmatory few-shot calibration stability audit with paired subject-level uncertainty. Only after that should we test adapter/domain-adaptation models.
