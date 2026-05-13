# ROCA-I-DARE EMG-only Closeout Report

This report aggregates prior EMG-only probes. No new model was trained.

## Overall verdict

**Conditional No-Go for EMG-only**

- Decision: Close EMG-only as primary path for now; proceed to EEG-only residual probe.
- Reason: Across feature sets, nonlinear models, and train-only augmentation, EMG-only did not robustly beat stimulus-only.

## Target verdicts

| target | best_rmse_lift | best_dev_pearson | best_auroc_lift | verdict | reason |
| --- | --- | --- | --- | --- | --- |
| arousal | -0.0247 | 0.0388 | 0.0026 | Weak AUROC-only hint | Some AUROC lift exists, but no RMSE lift and no meaningful deviation correlation. |
| valence | -0.0026 | 0.0336 | 0.0042 | Weak AUROC-only hint | Some AUROC lift exists, but no RMSE lift and no meaningful deviation correlation. |


## Best full-set residual EMG results

| target | best_metric | best_metric_value | experiment | model | rmse | lift_vs_stimulus_rmse | balanced_accuracy | lift_vs_stimulus_balanced_accuracy | auroc | lift_vs_stimulus_auroc | dev_pearson | pred_dev_std |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | lift_vs_stimulus_rmse | -0.0247 | 04c_nonlinear_22feat | emg_residual_extratrees | 1.9689 | -0.0247 | 0.7652 | -0.0034 | 0.8161 | -0.0000 | -0.0926 | 0.1790 |
| arousal | lift_vs_stimulus_auroc | 0.0026 | 04f_augmented_812feat | emg_expanded_extratrees_residual_aug | 1.9702 | -0.0260 | 0.7692 | 0.0006 | 0.8187 | 0.0026 | -0.0370 | 0.2548 |
| arousal | lift_vs_stimulus_balanced_accuracy | 0.0010 | 04e_expanded_812feat | emg_expanded_extratrees_residual | 1.9722 | -0.0279 | 0.7696 | 0.0010 | 0.8170 | 0.0009 | -0.0323 | 0.2740 |
| arousal | dev_pearson | 0.0388 | 04f_augmented_812feat | emg_expanded_ridge_residual_aug | 2.0532 | -0.1090 | 0.7597 | -0.0089 | 0.8090 | -0.0071 | 0.0388 | 0.7394 |
| arousal | rmse | 1.9689 | 04c_nonlinear_22feat | emg_residual_extratrees | 1.9689 | -0.0247 | 0.7652 | -0.0034 | 0.8161 | -0.0000 | -0.0926 | 0.1790 |
| valence | lift_vs_stimulus_rmse | -0.0026 | 04c_nonlinear_22feat | emg_residual_extratrees | 1.2603 | -0.0026 | 0.8806 | 0.0010 | 0.9471 | 0.0038 | 0.0066 | 0.0891 |
| valence | lift_vs_stimulus_auroc | 0.0042 | 04b_clipped_ridge | emg_residual_ridge | 1.2610 | -0.0033 | 0.8796 | 0.0000 | 0.9475 | 0.0042 | 0.0336 | 0.1423 |
| valence | lift_vs_stimulus_balanced_accuracy | 0.0010 | 04c_nonlinear_22feat | emg_residual_extratrees | 1.2603 | -0.0026 | 0.8806 | 0.0010 | 0.9471 | 0.0038 | 0.0066 | 0.0891 |
| valence | dev_pearson | 0.0336 | 04b_clipped_ridge | emg_residual_ridge | 1.2610 | -0.0033 | 0.8796 | 0.0000 | 0.9475 | 0.0042 | 0.0336 | 0.1423 |
| valence | rmse | 1.2603 | 04c_nonlinear_22feat | emg_residual_extratrees | 1.2603 | -0.0026 | 0.8806 | 0.0010 | 0.9471 | 0.0038 | 0.0066 | 0.0891 |


## Best fold-safe hard-subset residual EMG results

| target | subset | best_metric | best_metric_value | experiment | model | rmse | lift_vs_stimulus_rmse | balanced_accuracy | lift_vs_stimulus_balanced_accuracy | auroc | lift_vs_stimulus_auroc | dev_pearson | pred_dev_std |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | top25_train_entropy | lift_vs_stimulus_rmse | -0.0296 | 04c_nonlinear_22feat | emg_residual_extratrees | 2.1059 | -0.0296 | 0.6242 | -0.0232 | 0.6420 | 0.0188 | -0.1242 | 0.1777 |
| arousal | top25_train_entropy | lift_vs_stimulus_auroc | 0.0249 | 04f_augmented_812feat | emg_expanded_ridge_residual_aug | 2.1921 | -0.1157 | 0.5985 | -0.0490 | 0.6482 | 0.0249 | 0.0266 | 0.7611 |
| arousal | top25_train_entropy | lift_vs_stimulus_balanced_accuracy | -0.0135 | 04e_expanded_812feat | emg_expanded_extratrees_residual | 2.1118 | -0.0354 | 0.6339 | -0.0135 | 0.6428 | 0.0196 | -0.0595 | 0.2811 |
| arousal | top25_train_entropy | dev_pearson | 0.0266 | 04f_augmented_812feat | emg_expanded_ridge_residual_aug | 2.1921 | -0.1157 | 0.5985 | -0.0490 | 0.6482 | 0.0249 | 0.0266 | 0.7611 |
| arousal | top25_train_entropy | rmse | 2.1059 | 04c_nonlinear_22feat | emg_residual_extratrees | 2.1059 | -0.0296 | 0.6242 | -0.0232 | 0.6420 | 0.0188 | -0.1242 | 0.1777 |
| arousal | top25_train_score_std | lift_vs_stimulus_rmse | -0.0199 | 04c_nonlinear_22feat | emg_residual_extratrees | 2.2938 | -0.0199 | 0.6357 | -0.0141 | 0.6970 | 0.0270 | -0.0751 | 0.1760 |
| arousal | top25_train_score_std | lift_vs_stimulus_auroc | 0.0297 | 04f_augmented_812feat | emg_expanded_extratrees_residual_aug | 2.2997 | -0.0257 | 0.6520 | 0.0022 | 0.6997 | 0.0297 | -0.0425 | 0.2600 |
| arousal | top25_train_score_std | lift_vs_stimulus_balanced_accuracy | 0.0022 | 04e_expanded_812feat | emg_expanded_extratrees_residual | 2.3035 | -0.0295 | 0.6520 | 0.0022 | 0.6977 | 0.0277 | -0.0475 | 0.2752 |
| arousal | top25_train_score_std | dev_pearson | -0.0012 | 04e_expanded_812feat | emg_expanded_ridge_residual | 2.3636 | -0.0896 | 0.6484 | -0.0014 | 0.6804 | 0.0104 | -0.0012 | 0.6422 |
| arousal | top25_train_score_std | rmse | 2.2938 | 04c_nonlinear_22feat | emg_residual_extratrees | 2.2938 | -0.0199 | 0.6357 | -0.0141 | 0.6970 | 0.0270 | -0.0751 | 0.1760 |
| valence | top25_train_entropy | lift_vs_stimulus_rmse | -0.0025 | 04b_clipped_ridge | emg_residual_ridge | 1.3255 | -0.0025 | 0.5064 | 0.0027 | 0.7288 | 0.0435 | 0.0304 | 0.1219 |
| valence | top25_train_entropy | lift_vs_stimulus_auroc | 0.0444 | 04c_nonlinear_22feat | emg_residual_extratrees | 1.3270 | -0.0039 | 0.5064 | 0.0027 | 0.7297 | 0.0444 | -0.0115 | 0.0846 |
| valence | top25_train_entropy | lift_vs_stimulus_balanced_accuracy | 0.0119 | 04f_augmented_812feat | emg_expanded_ridge_residual_aug | 1.4008 | -0.0778 | 0.5157 | 0.0119 | 0.6716 | -0.0136 | -0.0220 | 0.4333 |
| valence | top25_train_entropy | dev_pearson | 0.0335 | 04e_expanded_812feat | emg_expanded_extratrees_residual | 1.3256 | -0.0026 | 0.5038 | 0.0000 | 0.7286 | 0.0433 | 0.0335 | 0.1315 |
| valence | top25_train_entropy | rmse | 1.3255 | 04b_clipped_ridge | emg_residual_ridge | 1.3255 | -0.0025 | 0.5064 | 0.0027 | 0.7288 | 0.0435 | 0.0304 | 0.1219 |
| valence | top25_train_score_std | lift_vs_stimulus_rmse | 0.0009 | 04b_clipped_ridge | emg_residual_ridge | 1.2963 | 0.0009 | 0.7381 | 0.0000 | 0.8627 | 0.0267 | 0.0558 | 0.1272 |
| valence | top25_train_score_std | lift_vs_stimulus_auroc | 0.0267 | 04b_clipped_ridge | emg_residual_ridge | 1.2963 | 0.0009 | 0.7381 | 0.0000 | 0.8627 | 0.0267 | 0.0558 | 0.1272 |
| valence | top25_train_score_std | lift_vs_stimulus_balanced_accuracy | 0.0038 | 04f_augmented_812feat | emg_expanded_ridge_residual_aug | 1.3856 | -0.0885 | 0.7419 | 0.0038 | 0.8421 | 0.0061 | -0.0332 | 0.4461 |
| valence | top25_train_score_std | dev_pearson | 0.0558 | 04b_clipped_ridge | emg_residual_ridge | 1.2963 | 0.0009 | 0.7381 | 0.0000 | 0.8627 | 0.0267 | 0.0558 | 0.1272 |
| valence | top25_train_score_std | rmse | 1.2963 | 04b_clipped_ridge | emg_residual_ridge | 1.2963 | 0.0009 | 0.7381 | 0.0000 | 0.8627 | 0.0267 | 0.0558 | 0.1272 |


## Interpretation

- EMG-only is closed as a primary path for now because it did not show robust RMSE improvement or meaningful deviation correlation.
- Small AUROC gains appeared in some hard subsets, especially Valence, but they were not supported by RMSE/deviation metrics.
- EMG should remain available for later multimodal fusion, calibration, uncertainty, or QC experiments.
- Next recommended step: EEG-only residual probe under the same strict LOSO protocol.


## Missing inputs

- None.