# ROCA-I-DARE EMG Nonlinear Probe

Model: `ExtraTreesRegressor`. Strict LOSO. Fixed hyperparameters. No test tuning.

## Main metrics

| target | model | n | mae | rmse | pearson | balanced_accuracy | auroc | dev_rmse | dev_pearson | dev_sign_acc | pred_dev_std | lift_vs_stimulus_rmse | lift_vs_stimulus_balanced_accuracy | lift_vs_stimulus_auroc | lift_vs_stimulus_dev_rmse | lift_vs_stimulus_dev_pearson |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | stimulus_only | 2016 | 1.5799 | 1.9442 | 0.6344 | 0.7686 | 0.8161 | 1.9442 |  | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |  |
| arousal | emg_direct_extratrees | 2016 | 2.2036 | 2.5439 | -0.0880 | 0.5010 | 0.4650 | 2.5439 | 0.0028 | 0.4311 | 1.6461 | -0.5997 | -0.2676 | -0.3511 | -0.5997 |  |
| arousal | emg_residual_extratrees | 2016 | 1.6006 | 1.9689 | 0.6229 | 0.7652 | 0.8161 | 1.9689 | -0.0926 | 0.4846 | 0.1790 | -0.0247 | -0.0034 | -0.0000 | -0.0247 |  |
| valence | stimulus_only | 2016 | 1.0221 | 1.2578 | 0.8663 | 0.8796 | 0.9433 | 1.2578 |  | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |  |
| valence | emg_direct_extratrees | 2016 | 2.1089 | 2.5252 | -0.0333 | 0.4909 | 0.4817 | 2.5252 | 0.0082 | 0.5094 | 2.2000 | -1.2674 | -0.3886 | -0.4616 | -1.2674 |  |
| valence | emg_residual_extratrees | 2016 | 1.0205 | 1.2603 | 0.8657 | 0.8806 | 0.9471 | 1.2603 | 0.0066 | 0.5134 | 0.0891 | -0.0026 | 0.0010 | 0.0038 | -0.0026 |  |


## Fold-safe hard subset metrics

| target | subset | model | n | rmse | balanced_accuracy | auroc | dev_rmse | dev_pearson | dev_sign_acc | pred_dev_std | lift_vs_stimulus_rmse | lift_vs_stimulus_balanced_accuracy | lift_vs_stimulus_auroc | lift_vs_stimulus_dev_rmse | lift_vs_stimulus_dev_pearson |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | top25_train_entropy | stimulus_only | 504 | 2.0764 | 0.6474 | 0.6232 | 2.0764 |  | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |  |
| arousal | top25_train_entropy | emg_direct_extratrees | 504 | 2.7290 | 0.5016 | 0.4393 | 2.7290 | -0.0723 | 0.4306 | 0.8446 | -0.6527 | -0.1458 | -0.1839 | -0.6527 |  |
| arousal | top25_train_entropy | emg_residual_extratrees | 504 | 2.1059 | 0.6242 | 0.6420 | 2.1059 | -0.1242 | 0.4405 | 0.1777 | -0.0296 | -0.0232 | 0.0188 | -0.0296 |  |
| arousal | top25_train_score_std | stimulus_only | 504 | 2.2740 | 0.6498 | 0.6700 | 2.2740 |  | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |  |
| arousal | top25_train_score_std | emg_direct_extratrees | 504 | 2.4861 | 0.4996 | 0.4739 | 2.4861 | 0.0134 | 0.4345 | 1.0354 | -0.2122 | -0.1502 | -0.1961 | -0.2122 |  |
| arousal | top25_train_score_std | emg_residual_extratrees | 504 | 2.2938 | 0.6357 | 0.6970 | 2.2938 | -0.0751 | 0.4821 | 0.1760 | -0.0199 | -0.0141 | 0.0270 | -0.0199 |  |
| valence | top25_train_entropy | stimulus_only | 504 | 1.3231 | 0.5038 | 0.6853 | 1.3231 |  | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |  |
| valence | top25_train_entropy | emg_direct_extratrees | 504 | 1.9079 | 0.4881 | 0.5016 | 1.9079 | 0.0100 | 0.5437 | 0.4972 | -0.5848 | -0.0156 | -0.1836 | -0.5848 |  |
| valence | top25_train_entropy | emg_residual_extratrees | 504 | 1.3270 | 0.5064 | 0.7297 | 1.3270 | -0.0115 | 0.5139 | 0.0846 | -0.0039 | 0.0027 | 0.0444 | -0.0039 |  |
| valence | top25_train_score_std | stimulus_only | 504 | 1.2972 | 0.7381 | 0.8359 | 1.2972 |  | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |  |
| valence | top25_train_score_std | emg_direct_extratrees | 504 | 2.0355 | 0.4750 | 0.4669 | 2.0355 | -0.0157 | 0.5179 | 1.4128 | -0.7384 | -0.2631 | -0.3691 | -0.7384 |  |
| valence | top25_train_score_std | emg_residual_extratrees | 504 | 1.3048 | 0.7381 | 0.8549 | 1.3048 | -0.0544 | 0.5198 | 0.0873 | -0.0077 | 0.0000 | 0.0190 | -0.0077 |  |


## Interpretation guide

- Positive `lift_vs_stimulus_rmse` means lower RMSE than stimulus-only.
- Positive `lift_vs_stimulus_auroc` means better high/low ranking than stimulus-only.
- `dev_pearson` is read directly because stimulus-only predicted deviation is constant zero.
