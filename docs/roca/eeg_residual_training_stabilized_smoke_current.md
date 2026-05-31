# ROCA-I-DARE EEG Residual Training Stabilized Smoke

This is a strict-LOSO stabilized smoke run, not final full training.

## Configuration

- target: `arousal`
- cache: `baseline_corrected`
- model: `eeg_bc_residual_huber_norm_stabilized_smoke`
- test_subjects: `[1, 2, 3, 5, 6, 7]`
- epochs_max: `50`
- patience: `8`
- batch_size: `32`
- optimizer: `AdamW(lr=0.0001, weight_decay=0.001)`
- loss: `HuberLoss(delta=1.0) on scaled residual`
- dropout/head_dropout: `0.1` / `0.3`

## Main metrics

| target | model | n | mae | rmse | pearson | balanced_accuracy | auroc | dev_rmse | dev_pearson | dev_sign_acc | true_dev_std | pred_dev_std | lift_vs_stimulus_rmse | lift_vs_stimulus_balanced_accuracy | lift_vs_stimulus_auroc | lift_vs_stimulus_dev_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | eeg_bc_residual_huber_norm_stabilized_smoke | 192 | 1.9772 | 2.4436 | 0.4440 | 0.6280 | 0.6567 | 2.4436 | 0.0467 | 0.4583 | 2.2785 | 0.2714 | -0.0606 | 0.0000 | 0.0090 | -0.0606 |
| arousal | stimulus_only | 192 | 1.9362 | 2.3830 | 0.4413 | 0.6280 | 0.6477 | 2.3830 |  | 0.0000 | 2.2785 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |


## Fold-safe hard subset metrics

| target | subset | model | n | rmse | balanced_accuracy | auroc | dev_rmse | dev_pearson | true_dev_std | pred_dev_std | lift_vs_stimulus_rmse | lift_vs_stimulus_balanced_accuracy | lift_vs_stimulus_auroc | lift_vs_stimulus_dev_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | top25_train_entropy | eeg_bc_residual_huber_norm_stabilized_smoke | 48 | 2.0476 | 0.6217 | 0.5326 | 2.0476 | -0.1750 | 1.9478 | 0.2547 | -0.0887 | 0.0000 | -0.0079 | -0.0887 |
| arousal | top25_train_entropy | stimulus_only | 48 | 1.9589 | 0.6217 | 0.5406 | 1.9589 |  | 1.9478 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| arousal | top25_train_score_std | eeg_bc_residual_huber_norm_stabilized_smoke | 48 | 2.4775 | 0.6164 | 0.6614 | 2.4775 | 0.2439 | 2.3755 | 0.2694 | -0.0045 | 0.0000 | 0.0529 | -0.0045 |
| arousal | top25_train_score_std | stimulus_only | 48 | 2.4730 | 0.6164 | 0.6085 | 2.4730 |  | 2.3755 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |


## Fold summary

| test_subject | best_epoch | best_val_rmse_scaled | rmse | dev_rmse | dev_pearson | true_dev_std | pred_dev_std | y_outer_std | final_train_last_loss |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2 | 1.0107 | 1.8793 | 1.8793 | 0.1154 | 1.8731 | 0.2312 | 1.9456 | 0.4262 |
| 2 | 1 | 0.9363 | 2.9232 | 2.9232 | 0.3580 | 1.5829 | 0.1373 | 1.9289 | 0.4359 |
| 3 | 1 | 1.0967 | 1.8060 | 1.8060 | -0.0113 | 1.3539 | 0.1010 | 1.9459 | 0.4413 |
| 5 | 1 | 1.1535 | 2.0865 | 2.0865 | -0.0599 | 1.5102 | 0.1391 | 1.9474 | 0.4389 |
| 6 | 2 | 0.9373 | 3.7003 | 3.7003 | -0.0473 | 1.7902 | 0.3028 | 1.9012 | 0.4237 |
| 7 | 2 | 0.9177 | 1.5629 | 1.5629 | 0.1353 | 1.2462 | 0.2062 | 1.9493 | 0.4266 |


## Interpretation guide

- Positive `lift_vs_stimulus_rmse` means lower score RMSE than stimulus-only.
- `dev_pearson` is read directly because stimulus-only predicted deviation is constant zero.
- `pred_dev_std` should not collapse near zero if the model is learning residual variation.
- If this smoke run is stable and promising, the next step is full 63-subject LOSO.
