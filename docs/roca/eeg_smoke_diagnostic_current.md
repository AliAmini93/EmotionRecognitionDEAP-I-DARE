# ROCA-I-DARE EEG Smoke Diagnostic Report

No model training was performed in this step.

## Experiment-level summary

| experiment | target | model | aggregate_rmse | stimulus_rmse | aggregate_lift_vs_stimulus_rmse | aggregate_dev_pearson | subject_centered_dev_pearson | macro_mean_fold_dev_pearson | positive_fold_dev_pearson_count | negative_fold_dev_pearson_count | pred_dev_std | true_dev_std | std_ratio_pred_over_true | diagnostic_verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 05b_residual_smoke | arousal | eeg_bc_residual_huber_smoke | 2.4794 | 2.3830 | -0.0964 | -0.0796 | 0.0330 | 0.0847 | 3 | 3 | 0.2117 | 2.2785 | 0.0929 | collapsed_or_under_scaled |
| 05c_stabilized_residual_smoke | arousal | eeg_bc_residual_huber_norm_stabilized_smoke | 2.4436 | 2.3830 | -0.0606 | 0.0467 | 0.0655 | 0.0817 | 3 | 3 | 0.2714 | 2.2785 | 0.1191 | collapsed_or_under_scaled |
| 05d_multitask_highlow_smoke | arousal | eeg_bc_residual_huber_norm_multitask_smoke | 2.4861 | 2.3830 | -0.1031 | -0.2625 | 0.2066 | 0.1701 | 5 | 1 | 0.2821 | 2.2785 | 0.1238 | ranking_signal_but_calibration_problem |


## Fold-level diagnostics

| experiment | test_subject | model | rmse | stimulus_rmse | lift_vs_stimulus_rmse | dev_pearson | true_dev_mean | pred_dev_mean | dev_mean_bias_pred_minus_true | true_dev_std | pred_dev_std | std_ratio_pred_over_true |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 05b_residual_smoke | 1 | eeg_bc_residual_huber_smoke | 1.8788 | 1.8757 | -0.0031 | 0.2247 | 0.0998 | -0.2078 | -0.3076 | 1.8731 | 0.0983 | 0.0525 |
| 05b_residual_smoke | 2 | eeg_bc_residual_huber_smoke | 2.9620 | 2.7325 | -0.2295 | 0.4226 | 2.2273 | -0.2915 | -2.5189 | 1.5829 | 0.0601 | 0.0379 |
| 05b_residual_smoke | 3 | eeg_bc_residual_huber_smoke | 1.8106 | 1.8533 | 0.0427 | 0.0663 | -1.2656 | -0.0602 | 1.2054 | 1.3539 | 0.0723 | 0.0534 |
| 05b_residual_smoke | 5 | eeg_bc_residual_huber_smoke | 1.8875 | 1.7548 | -0.1327 | -0.0139 | 0.8936 | -0.1424 | -1.0360 | 1.5102 | 0.4361 | 0.2888 |
| 05b_residual_smoke | 6 | eeg_bc_residual_huber_smoke | 3.9591 | 3.7325 | -0.2266 | -0.1353 | 3.2752 | -0.2514 | -3.5266 | 1.7902 | 0.0607 | 0.0339 |
| 05b_residual_smoke | 7 | eeg_bc_residual_huber_smoke | 1.4367 | 1.6253 | 0.1885 | -0.0566 | -1.0433 | -0.3386 | 0.7047 | 1.2462 | 0.0694 | 0.0557 |
| 05c_stabilized_residual_smoke | 1 | eeg_bc_residual_huber_norm_stabilized_smoke | 1.8793 | 1.8757 | -0.0035 | 0.1154 | 0.0998 | -0.1642 | -0.2640 | 1.8731 | 0.2312 | 0.1234 |
| 05c_stabilized_residual_smoke | 2 | eeg_bc_residual_huber_norm_stabilized_smoke | 2.9232 | 2.7325 | -0.1907 | 0.3580 | 2.2273 | -0.2579 | -2.4852 | 1.5829 | 0.1373 | 0.0868 |
| 05c_stabilized_residual_smoke | 3 | eeg_bc_residual_huber_norm_stabilized_smoke | 1.8060 | 1.8533 | 0.0473 | -0.0113 | -1.2656 | -0.0759 | 1.1897 | 1.3539 | 0.1010 | 0.0746 |
| 05c_stabilized_residual_smoke | 5 | eeg_bc_residual_huber_norm_stabilized_smoke | 2.0865 | 1.7548 | -0.3317 | -0.0599 | 0.8936 | -0.5305 | -1.4241 | 1.5102 | 0.1391 | 0.0921 |
| 05c_stabilized_residual_smoke | 6 | eeg_bc_residual_huber_norm_stabilized_smoke | 3.7003 | 3.7325 | 0.0323 | -0.0473 | 3.2752 | 0.0590 | -3.2162 | 1.7902 | 0.3028 | 0.1692 |
| 05c_stabilized_residual_smoke | 7 | eeg_bc_residual_huber_norm_stabilized_smoke | 1.5629 | 1.6253 | 0.0624 | 0.1353 | -1.0433 | -0.0860 | 0.9574 | 1.2462 | 0.2062 | 0.1655 |
| 05d_multitask_highlow_smoke | 1 | eeg_bc_residual_huber_norm_multitask_smoke | 1.7972 | 1.8757 | 0.0786 | 0.3637 | 0.0998 | -0.0573 | -0.1571 | 1.8731 | 0.2802 | 0.1496 |
| 05d_multitask_highlow_smoke | 2 | eeg_bc_residual_huber_norm_multitask_smoke | 2.7582 | 2.7325 | -0.0257 | 0.3767 | 2.2273 | -0.0616 | -2.2889 | 1.5829 | 0.1289 | 0.0815 |
| 05d_multitask_highlow_smoke | 3 | eeg_bc_residual_huber_norm_multitask_smoke | 2.1399 | 1.8533 | -0.2865 | 0.0919 | -1.2656 | 0.3960 | 1.6616 | 1.3539 | 0.1480 | 0.1093 |
| 05d_multitask_highlow_smoke | 5 | eeg_bc_residual_huber_norm_multitask_smoke | 1.7866 | 1.7548 | -0.0318 | 0.0576 | 0.8936 | -0.0648 | -0.9585 | 1.5102 | 0.0747 | 0.0494 |
| 05d_multitask_highlow_smoke | 6 | eeg_bc_residual_huber_norm_multitask_smoke | 4.0354 | 3.7325 | -0.3029 | -0.0217 | 3.2752 | -0.3392 | -3.6144 | 1.7902 | 0.0935 | 0.0522 |
| 05d_multitask_highlow_smoke | 7 | eeg_bc_residual_huber_norm_multitask_smoke | 1.4800 | 1.6253 | 0.1452 | 0.1522 | -1.0433 | -0.2227 | 0.8207 | 1.2462 | 0.1841 | 0.1477 |


## Interpretation

- `aggregate_dev_pearson` is computed after pooling all smoke subjects.
- `macro_mean_fold_dev_pearson` averages per-subject correlations.
- `subject_centered_dev_pearson` removes subject-level mean bias before correlation.
- If macro/centered correlations are positive while aggregate correlation is poor, the model has a calibration problem rather than no signal.
- If `std_ratio_pred_over_true` is very small, residual predictions are under-scaled.


## Suggested next decision rule

- If the best experiment is `collapsed_or_under_scaled`, adjust model/head/loss before full LOSO.
- If the best experiment is `weak_within_subject_signal`, try residual-sign auxiliary instead of raw high/low auxiliary.
- If the best experiment is `ranking_signal_but_calibration_problem`, test fold-safe calibration of predicted residual scale.
- Only run full LOSO when RMSE lift or robust residual correlation is at least directionally promising.


## Missing inputs

- None.