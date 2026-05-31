# ROCA-I-DARE EEG Multitask Residual Training Smoke

This is a strict-LOSO multitask smoke run, not final full training.

## Configuration

- target: `arousal`
- cache: `baseline_corrected`
- model: `eeg_bc_residual_huber_norm_multitask_smoke`
- test_subjects: `[1, 2, 3, 5, 6, 7]`
- epochs_max: `50`
- patience: `8`
- batch_size: `32`
- optimizer: `AdamW(lr=0.0001, weight_decay=0.001)`
- loss: `HuberResidual + 0.25 * BCEHighLow`
- dropout/head_dropout: `0.1` / `0.3`

## Main metrics

| target | model | n | mae | rmse | pearson | balanced_accuracy | auroc | dev_rmse | dev_pearson | dev_sign_acc | true_dev_std | pred_dev_std | lift_vs_stimulus_rmse | lift_vs_stimulus_balanced_accuracy | lift_vs_stimulus_auroc | lift_vs_stimulus_dev_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | eeg_bc_residual_huber_norm_multitask_smoke | 192 | 1.9922 | 2.4861 | 0.3971 | 0.6234 | 0.6257 | 2.4861 | -0.2625 | 0.4167 | 2.2785 | 0.2821 | -0.1031 | -0.0046 | -0.0219 | -0.1031 |
| arousal | stimulus_only | 192 | 1.9362 | 2.3830 | 0.4413 | 0.6280 | 0.6477 | 2.3830 |  | 0.0000 | 2.2785 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |


## Fold-safe hard subset metrics

| target | subset | model | n | rmse | balanced_accuracy | auroc | dev_rmse | dev_pearson | true_dev_std | pred_dev_std | lift_vs_stimulus_rmse | lift_vs_stimulus_balanced_accuracy | lift_vs_stimulus_auroc | lift_vs_stimulus_dev_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | top25_train_entropy | eeg_bc_residual_huber_norm_multitask_smoke | 48 | 2.0425 | 0.5979 | 0.5256 | 2.0425 | -0.1971 | 1.9478 | 0.2885 | -0.0836 | -0.0238 | -0.0150 | -0.0836 |
| arousal | top25_train_entropy | stimulus_only | 48 | 1.9589 | 0.6217 | 0.5406 | 1.9589 |  | 1.9478 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| arousal | top25_train_score_std | eeg_bc_residual_huber_norm_multitask_smoke | 48 | 2.5514 | 0.5979 | 0.6049 | 2.5514 | -0.1847 | 2.3755 | 0.2656 | -0.0784 | -0.0185 | -0.0035 | -0.0784 |
| arousal | top25_train_score_std | stimulus_only | 48 | 2.4730 | 0.6164 | 0.6085 | 2.4730 |  | 2.3755 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |


## Fold summary

| test_subject | best_epoch | best_val_rmse_scaled | best_val_bce | best_val_objective | rmse | dev_rmse | dev_pearson | true_dev_std | pred_dev_std | aux_binary_prob_std | final_train_last_loss |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2 | 1.0136 | 0.6192 | 1.1684 | 1.7972 | 1.7972 | 0.3637 | 1.8731 | 0.2802 | 0.0185 | 0.5933 |
| 2 | 1 | 0.9386 | 0.5994 | 1.0884 | 2.7582 | 2.7582 | 0.3767 | 1.5829 | 0.1289 | 0.0065 | 0.6127 |
| 3 | 2 | 1.1131 | 0.6013 | 1.2634 | 2.1399 | 2.1399 | 0.0919 | 1.3539 | 0.1480 | 0.0122 | 0.5995 |
| 5 | 1 | 1.1528 | 0.6905 | 1.3254 | 1.7866 | 1.7866 | 0.0576 | 1.5102 | 0.0747 | 0.0061 | 0.6155 |
| 6 | 1 | 0.9583 | 0.6091 | 1.1106 | 4.0354 | 4.0354 | -0.0217 | 1.7902 | 0.0935 | 0.0068 | 0.6010 |
| 7 | 2 | 0.9044 | 0.6729 | 1.0726 | 1.4800 | 1.4800 | 0.1522 | 1.2462 | 0.1841 | 0.0231 | 0.5920 |


## Interpretation guide

- Positive `lift_vs_stimulus_rmse` means lower score RMSE than stimulus-only.
- `dev_pearson` is read directly because stimulus-only predicted deviation is constant zero.
- `pred_dev_std` should not collapse near zero if the model is learning residual variation.
- The auxiliary binary head is not the main output; it is only a training signal.
- If this smoke run is stable and promising, the next step is full 63-subject LOSO.
