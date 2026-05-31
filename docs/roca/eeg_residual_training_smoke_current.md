# ROCA-I-DARE EEG Residual Training Smoke

This is a strict-LOSO smoke run, not final full training.

## Configuration

- target: `arousal`
- cache: `baseline_corrected`
- model: `eeg_bc_residual_huber_smoke`
- test_subjects: `[1, 2, 3, 5, 6, 7]`
- epochs_max: `20`
- batch_size: `32`
- optimizer: `AdamW(lr=0.0003, weight_decay=0.001)`
- loss: `HuberLoss(delta=1.0)`

## Main metrics

| target | model | n | mae | rmse | pearson | balanced_accuracy | auroc | dev_rmse | dev_pearson | dev_sign_acc | pred_dev_std | lift_vs_stimulus_rmse | lift_vs_stimulus_balanced_accuracy | lift_vs_stimulus_auroc | lift_vs_stimulus_dev_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | eeg_bc_residual_huber_smoke | 192 | 1.9870 | 2.4794 | 0.4286 | 0.6280 | 0.6534 | 2.4794 | -0.0796 | 0.4531 | 0.2117 | -0.0964 | 0.0000 | 0.0057 | -0.0964 |
| arousal | stimulus_only | 192 | 1.9362 | 2.3830 | 0.4413 | 0.6280 | 0.6477 | 2.3830 |  | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |


## Fold-safe hard subset metrics

| target | subset | model | n | rmse | balanced_accuracy | auroc | dev_rmse | dev_pearson | pred_dev_std | lift_vs_stimulus_rmse | lift_vs_stimulus_balanced_accuracy | lift_vs_stimulus_auroc | lift_vs_stimulus_dev_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | top25_train_entropy | eeg_bc_residual_huber_smoke | 48 | 2.0376 | 0.6217 | 0.5520 | 2.0376 | -0.1448 | 0.2030 | -0.0786 | 0.0000 | 0.0115 | -0.0786 |
| arousal | top25_train_entropy | stimulus_only | 48 | 1.9589 | 0.6217 | 0.5406 | 1.9589 |  | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| arousal | top25_train_score_std | eeg_bc_residual_huber_smoke | 48 | 2.5475 | 0.6164 | 0.6490 | 2.5475 | -0.0043 | 0.1966 | -0.0745 | 0.0000 | 0.0406 | -0.0745 |
| arousal | top25_train_score_std | stimulus_only | 48 | 2.4730 | 0.6164 | 0.6085 | 2.4730 |  | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |


## Fold summary

| test_subject | best_epoch | best_val_dev_rmse | rmse | dev_rmse | dev_pearson | final_train_last_loss |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | 1.9572 | 1.8788 | 1.8788 | 0.2247 | 1.1486 |
| 2 | 1 | 1.7454 | 2.9620 | 2.9620 | 0.4226 | 1.1371 |
| 3 | 1 | 2.1752 | 1.8106 | 1.8106 | 0.0663 | 1.1539 |
| 5 | 4 | 2.2287 | 1.8875 | 1.8875 | -0.0139 | 1.0476 |
| 6 | 1 | 1.8153 | 3.9591 | 3.9591 | -0.1353 | 1.1218 |
| 7 | 1 | 1.7989 | 1.4367 | 1.4367 | -0.0566 | 1.1501 |


## Interpretation guide

- Positive `lift_vs_stimulus_rmse` means lower score RMSE than stimulus-only.
- `dev_pearson` is read directly because stimulus-only predicted deviation is constant zero.
- If this smoke run is stable and promising, the next step is full 63-subject LOSO.
