# I-DARE Residual Signal Reliability Audit

This is the patched interpretation of the residual reliability audit.

## Key correction

The previous `stimulus_residual_across_subjects = -1` result should **not** be interpreted as scientific stimulus reliability. Under LOSO stimulus-only residuals, residuals are algebraically centered within each stimulus. Splitting subjects can force per-stimulus half-means into anti-correlation. Therefore this axis is not used in the verdict.

## Verdict

| target | residual_signal_verdict | confirmatory_physiology_verdict | residual_std | subject_r2_on_residual | stimulus_r2_on_residual | additive_subject_stimulus_r2_on_residual | subject_split_half_pearson_median | subject_split_half_pearson_q025 | stimulus_split_half_status | stimulus_split_half_artifact_note | few_shot_or_subject_calibration_plausible | stimulus_residual_structure_plausible | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | SUBJECT_STRUCTURED_RESIDUAL_PRESENT__ZERO_SHOT_PHYSIOLOGY_NO_GO__FEW_SHOT_RECOMMENDED | NO_GO_CONFIRMED_CURRENT_FEATURE_SET | 1.944205 | 0.269176 | 0.000000 | 0.269176 | 0.847820 | 0.741006 | NOT_USED_ARTIFACT_UNDER_LOSO_RESIDUAL_DEFINITION | Splitting subjects and correlating per-stimulus residual means is not used; LOSO stimulus residuals are algebraically centered within stimulus and can induce anti-correlation. | True | False | Residual is reliable mainly as subject-specific bias/profile across stimuli. The current physiology feature audit remains no-go for zero-shot LOSO, but few-shot subject calibration is scientifically plausible. |
| valence | SUBJECT_STRUCTURED_RESIDUAL_PRESENT__ZERO_SHOT_PHYSIOLOGY_NO_GO__FEW_SHOT_RECOMMENDED | NO_GO_CONFIRMED_CURRENT_FEATURE_SET | 1.257774 | 0.092777 | 0.000000 | 0.092777 | 0.549355 | 0.287371 | NOT_USED_ARTIFACT_UNDER_LOSO_RESIDUAL_DEFINITION | Splitting subjects and correlating per-stimulus residual means is not used; LOSO stimulus residuals are algebraically centered within stimulus and can induce anti-correlation. | True | False | Residual is reliable mainly as subject-specific bias/profile across stimuli. The current physiology feature audit remains no-go for zero-shot LOSO, but few-shot subject calibration is scientifically plausible. |


## Residual summary

| target | n | mean | std | median | q25 | q75 | iqr | mad | scaled_mad | mean_abs | median_abs | q90_abs | q95_abs | skew | kurtosis_excess | outlier_rate_3mad | positive_rate | negative_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | 2016 | -0.000000 | 1.944205 | -0.193548 | -1.435484 | 1.419355 | 2.854839 | 1.370968 | 2.032597 | 1.579925 | 1.427419 | 3.000000 | 3.822581 | 0.347002 | -0.080825 | 0.001984 | 0.463790 | 0.536210 |
| valence | 2016 | -0.000000 | 1.257774 | -0.161290 | -0.774194 | 0.854839 | 1.629032 | 0.774194 | 1.147819 | 1.022065 | 0.822581 | 1.911290 | 2.403226 | 0.036699 | 0.107666 | 0.009921 | 0.485119 | 0.514881 |


## Residual variance/effect decomposition

| target | subject_r2_on_residual | stimulus_r2_on_residual | subject_plus_stimulus_r2_on_residual | unique_subject_r2_over_stimulus | unique_stimulus_r2_over_subject | additive_design_rank | additive_design_cols |
| --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | 0.269176 | 0.000000 | 0.269176 | 0.269176 | 0.000000 | 94 | 95 |
| valence | 0.092777 | 0.000000 | 0.092777 | 0.092777 | -0.000000 | 94 | 95 |


## Used split-half reliability: subject residual bias across stimuli

| target | axis | metric | splits | mean | std | q025 | q25 | median | q75 | q975 | positive_rate | used_in_verdict | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | subject_bias_across_stimuli | pearson | 5000 | 0.841025 | 0.042740 | 0.741006 | 0.817541 | 0.847820 | 0.870498 | 0.904606 | 1.000000 | True | Meaningful split-half reliability of subject residual bias across stimuli. |
| arousal | subject_bias_across_stimuli | spearman | 5000 | 0.798990 | 0.049919 | 0.685894 | 0.770669 | 0.805388 | 0.833525 | 0.877282 | 1.000000 | True | Meaningful split-half reliability of subject residual bias across stimuli. |
| valence | subject_bias_across_stimuli | pearson | 5000 | 0.533458 | 0.100009 | 0.287371 | 0.481825 | 0.549355 | 0.602131 | 0.687740 | 1.000000 | True | Meaningful split-half reliability of subject residual bias across stimuli. |
| valence | subject_bias_across_stimuli | spearman | 5000 | 0.520395 | 0.105087 | 0.264576 | 0.465471 | 0.536637 | 0.592848 | 0.682543 | 0.999800 | True | Meaningful split-half reliability of subject residual bias across stimuli. |


## Artifact check, not used in verdict

| target | artifact_check | split_idx | pearson | spearman | used_in_verdict | why_not_used |
| --- | --- | --- | --- | --- | --- | --- |
| arousal | stimulus_residual_split_subjects_not_used | 0 | -1.000000 | -1.000000 | False | LOSO residuals are algebraically centered by stimulus; split-subject stimulus residual means can be forced into anti-correlation. Do not interpret near -1 as scientific stimulus reliability. |
| arousal | stimulus_residual_split_subjects_not_used | 1 | -1.000000 | -1.000000 | False | LOSO residuals are algebraically centered by stimulus; split-subject stimulus residual means can be forced into anti-correlation. Do not interpret near -1 as scientific stimulus reliability. |
| arousal | stimulus_residual_split_subjects_not_used | 2 | -1.000000 | -1.000000 | False | LOSO residuals are algebraically centered by stimulus; split-subject stimulus residual means can be forced into anti-correlation. Do not interpret near -1 as scientific stimulus reliability. |
| arousal | stimulus_residual_split_subjects_not_used | 3 | -1.000000 | -1.000000 | False | LOSO residuals are algebraically centered by stimulus; split-subject stimulus residual means can be forced into anti-correlation. Do not interpret near -1 as scientific stimulus reliability. |
| arousal | stimulus_residual_split_subjects_not_used | 4 | -1.000000 | -1.000000 | False | LOSO residuals are algebraically centered by stimulus; split-subject stimulus residual means can be forced into anti-correlation. Do not interpret near -1 as scientific stimulus reliability. |
| arousal | stimulus_residual_split_subjects_not_used | 5 | -1.000000 | -1.000000 | False | LOSO residuals are algebraically centered by stimulus; split-subject stimulus residual means can be forced into anti-correlation. Do not interpret near -1 as scientific stimulus reliability. |
| arousal | stimulus_residual_split_subjects_not_used | 6 | -1.000000 | -1.000000 | False | LOSO residuals are algebraically centered by stimulus; split-subject stimulus residual means can be forced into anti-correlation. Do not interpret near -1 as scientific stimulus reliability. |
| arousal | stimulus_residual_split_subjects_not_used | 7 | -1.000000 | -1.000000 | False | LOSO residuals are algebraically centered by stimulus; split-subject stimulus residual means can be forced into anti-correlation. Do not interpret near -1 as scientific stimulus reliability. |


## Interpretation

- Residuals are not pure noise.
- The reliable component currently looks subject-specific, especially for arousal.
- This supports a pivot toward few-shot subject calibration / subject-adaptive modeling.
- It does not rescue the current zero-shot LOSO physiology feature results; those remain no-go under 05y.


## Recommended next step

Run `05aa` few-shot residual calibration: hold out one subject, use k calibration stimuli from that subject, then predict residuals on the remaining stimuli for k = 1, 2, 4, 8, 16.
