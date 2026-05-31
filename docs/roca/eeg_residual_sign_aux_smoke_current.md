# ROCA-I-DARE EEG Residual-Sign Auxiliary Smoke

This is a strict-LOSO residual-sign auxiliary smoke run, not final full training.

## Configuration

- target: `arousal`
- cache: `baseline_corrected`
- model: `eeg_bc_residual_huber_norm_residual_sign_aux_smoke`
- test_subjects: `[1, 2, 3, 5, 6, 7]`
- epochs_max: `50`
- patience: `8`
- batch_size: `32`
- optimizer: `AdamW(lr=0.0001, weight_decay=0.001)`
- loss: `HuberResidual + 0.25 * BCEResidualSign`
- residual-sign label: `residual > 0`
- dropout/head_dropout: `0.1` / `0.3`

## Main metrics

| target | model | n | mae | rmse | pearson | balanced_accuracy | auroc | dev_rmse | dev_pearson | dev_sign_acc | true_dev_std | pred_dev_std | aux_residual_sign_acc | aux_residual_sign_auroc | aux_residual_sign_prob_std | lift_vs_stimulus_rmse | lift_vs_stimulus_balanced_accuracy | lift_vs_stimulus_auroc | lift_vs_stimulus_dev_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | eeg_bc_residual_huber_norm_residual_sign_aux_smoke | 192 | 1.9614 | 2.4420 | 0.4157 | 0.6294 | 0.6405 | 2.4420 | -0.1671 | 0.5052 | 2.2785 | 0.2719 | 0.5052 | 0.4786 | 0.0346 | -0.0590 | 0.0014 | -0.0071 | -0.0590 |
| arousal | stimulus_only | 192 | 1.9362 | 2.3830 | 0.4413 | 0.6280 | 0.6477 | 2.3830 |  | 0.0000 | 2.2785 | 0.0000 |  |  |  | 0.0000 | 0.0000 | 0.0000 | 0.0000 |


## Fold-safe hard subset metrics

| target | subset | model | n | rmse | balanced_accuracy | auroc | dev_rmse | dev_pearson | true_dev_std | pred_dev_std | aux_residual_sign_acc | aux_residual_sign_auroc | lift_vs_stimulus_rmse | lift_vs_stimulus_balanced_accuracy | lift_vs_stimulus_auroc | lift_vs_stimulus_dev_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | top25_train_entropy | eeg_bc_residual_huber_norm_residual_sign_aux_smoke | 48 | 2.0028 | 0.6164 | 0.5538 | 2.0028 | -0.0883 | 1.9478 | 0.2732 | 0.5625 | 0.5052 | -0.0438 | -0.0053 | 0.0132 | -0.0438 |
| arousal | top25_train_entropy | stimulus_only | 48 | 1.9589 | 0.6217 | 0.5406 | 1.9589 |  | 1.9478 | 0.0000 |  |  | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| arousal | top25_train_score_std | eeg_bc_residual_huber_norm_residual_sign_aux_smoke | 48 | 2.5071 | 0.6217 | 0.6314 | 2.5071 | -0.1116 | 2.3755 | 0.2470 | 0.4792 | 0.5429 | -0.0340 | 0.0053 | 0.0229 | -0.0340 |
| arousal | top25_train_score_std | stimulus_only | 48 | 2.4730 | 0.6164 | 0.6085 | 2.4730 |  | 2.3755 | 0.0000 |  |  | 0.0000 | 0.0000 | 0.0000 | 0.0000 |


## Fold summary

| test_subject | best_epoch | best_val_rmse_scaled | best_val_sign_bce | best_val_objective | rmse | dev_rmse | dev_pearson | true_dev_std | pred_dev_std | aux_residual_sign_acc | aux_residual_sign_auroc | aux_residual_sign_prob_std | final_train_last_loss |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2 | 1.0143 | 0.6826 | 1.1850 | 1.7801 | 1.7801 | 0.3892 | 1.8731 | 0.3036 | 0.5625 | 0.7817 | 0.0271 | 0.6044 |
| 2 | 2 | 0.9386 | 0.6762 | 1.1076 | 2.7249 | 2.7249 | 0.0882 | 1.5829 | 0.2798 | 0.3125 | 0.7586 | 0.0359 | 0.6018 |
| 3 | 2 | 1.1085 | 0.6827 | 1.2792 | 1.8738 | 1.8738 | -0.1528 | 1.3539 | 0.1000 | 0.7500 | 0.2821 | 0.0187 | 0.6036 |
| 5 | 3 | 1.1537 | 0.6987 | 1.3284 | 1.6927 | 1.6927 | 0.0442 | 1.5102 | 0.3157 | 0.5312 | 0.5273 | 0.0475 | 0.5903 |
| 6 | 2 | 0.9413 | 0.6810 | 1.1115 | 3.9993 | 3.9993 | -0.1371 | 1.7902 | 0.1988 | 0.0625 | 0.4667 | 0.0155 | 0.6009 |
| 7 | 1 | 0.9054 | 0.6993 | 1.0802 | 1.6777 | 1.6777 | 0.0746 | 1.2462 | 0.0960 | 0.8125 | 0.6282 | 0.0089 | 0.6201 |


## Interpretation guide

- Positive `lift_vs_stimulus_rmse` means lower score RMSE than stimulus-only.
- `dev_pearson` is read directly because stimulus-only predicted deviation is constant zero.
- `aux_residual_sign_acc` checks whether the auxiliary head predicts residual direction.
- `pred_dev_std` should not collapse near zero if the model is learning residual variation.
- If this improves over 05c/05d, the next step is full LOSO or a broader smoke over more folds.
