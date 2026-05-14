# ROCA-I-DARE EEG Augmentation Matrix Smoke

This is an exploratory train-only augmentation matrix. It is not final model selection.

## Configuration

- target: `arousal`
- cache: `baseline_corrected`
- model: `eeg_bc_residual_huber_norm_gaussian10_arousal_test_oracle`
- max_folds: `63`
- epochs_max: `100`
- patience: `20`
- batch_size: `32`
- optimizer: `AdamW(lr=0.0001, weight_decay=0.001)`
- loss: `HuberLoss(delta=1.0) on scaled residual`
- configs: `['gaussian_0p10']`

## Augmentation configs

```json
{
  "gaussian_0p10": {
    "description": "Additive Gaussian noise, std=0.10 in normalized EEG units",
    "gaussian_std": 0.1,
    "gain_jitter": 0.0,
    "time_shift_max": 0,
    "time_mask_frac": 0.0,
    "channel_drop_prob": 0.0
  }
}
```

## Main metrics

| augmentation_config | target | model | n | mae | rmse | pearson | balanced_accuracy | auroc | dev_rmse | dev_pearson | dev_sign_acc | true_dev_std | pred_dev_std | lift_vs_stimulus_rmse | lift_vs_stimulus_balanced_accuracy | lift_vs_stimulus_auroc | lift_vs_stimulus_dev_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gaussian_0p10 | arousal | eeg_bc_residual_huber_norm_gaussian10_arousal_test_oracle | 2016 | 1.4671 | 1.8310 | 0.6857 | 0.7776 | 0.8551 | 1.8310 | 0.3372 | 0.6230 | 1.9442 | 0.6420 | 0.1132 | 0.0089 | 0.0391 | 0.1132 |
| gaussian_0p10 | arousal | stimulus_only | 2016 | 1.5799 | 1.9442 | 0.6344 | 0.7686 | 0.8161 | 1.9442 |  | 0.0000 | 1.9442 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |


## Best rows

| best_metric | best_metric_value | augmentation_config | rmse | lift_vs_stimulus_rmse | balanced_accuracy | lift_vs_stimulus_balanced_accuracy | auroc | lift_vs_stimulus_auroc | dev_pearson | pred_dev_std |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lift_vs_stimulus_rmse | 0.1132 | gaussian_0p10 | 1.8310 | 0.1132 | 0.7776 | 0.0089 | 0.8551 | 0.0391 | 0.3372 | 0.6420 |
| dev_pearson | 0.3372 | gaussian_0p10 | 1.8310 | 0.1132 | 0.7776 | 0.0089 | 0.8551 | 0.0391 | 0.3372 | 0.6420 |
| lift_vs_stimulus_auroc | 0.0391 | gaussian_0p10 | 1.8310 | 0.1132 | 0.7776 | 0.0089 | 0.8551 | 0.0391 | 0.3372 | 0.6420 |
| pred_dev_std | 0.6420 | gaussian_0p10 | 1.8310 | 0.1132 | 0.7776 | 0.0089 | 0.8551 | 0.0391 | 0.3372 | 0.6420 |
| rmse | 1.8310 | gaussian_0p10 | 1.8310 | 0.1132 | 0.7776 | 0.0089 | 0.8551 | 0.0391 | 0.3372 | 0.6420 |


## Fold summary

| augmentation_config | test_subject | best_epoch | best_val_rmse_scaled | rmse | dev_rmse | dev_pearson | true_dev_std | pred_dev_std | final_train_last_loss |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gaussian_0p10 | 1 | 3 | 0.9383 | 1.8256 | 1.8256 | 0.2255 | 1.8731 | 0.3767 | 0.0835 |
| gaussian_0p10 | 2 | 12 | 1.3358 | 2.5766 | 2.5766 | 0.1441 | 1.5829 | 1.2249 | 0.0695 |
| gaussian_0p10 | 3 | 7 | 0.8256 | 1.5997 | 1.5997 | -0.1245 | 1.3539 | 0.4872 | 0.0745 |
| gaussian_0p10 | 5 | 7 | 0.8276 | 1.6117 | 1.6117 | 0.1184 | 1.5102 | 0.5032 | 0.0769 |
| gaussian_0p10 | 6 | 13 | 1.8098 | 3.4408 | 3.4408 | -0.0129 | 1.7902 | 0.8402 | 0.0670 |
| gaussian_0p10 | 7 | 2 | 0.7612 | 1.4837 | 1.4837 | 0.0830 | 1.2462 | 0.2092 | 0.1042 |
| gaussian_0p10 | 8 | 2 | 0.8952 | 1.7410 | 1.7410 | 0.3329 | 1.6305 | 0.1868 | 0.0924 |
| gaussian_0p10 | 9 | 1 | 1.0303 | 1.9994 | 1.9994 | 0.1262 | 1.8982 | 0.1172 | 0.0952 |
| gaussian_0p10 | 10 | 1 | 0.8990 | 1.7512 | 1.7512 | -0.2007 | 1.7130 | 0.0900 | 0.1089 |
| gaussian_0p10 | 11 | 16 | 0.9225 | 1.7908 | 1.7908 | 0.3501 | 1.9006 | 0.8239 | 0.0607 |
| gaussian_0p10 | 12 | 1 | 0.6736 | 1.3155 | 1.3155 | 0.0981 | 1.2274 | 0.1620 | 0.1031 |
| gaussian_0p10 | 13 | 3 | 0.9856 | 1.9079 | 1.9079 | 0.0537 | 1.4089 | 0.3713 | 0.0880 |
| gaussian_0p10 | 14 | 13 | 0.7983 | 1.5533 | 1.5533 | 0.3422 | 0.8494 | 0.8160 | 0.0746 |
| gaussian_0p10 | 15 | 6 | 0.8570 | 1.6698 | 1.6698 | 0.0674 | 1.6186 | 0.5313 | 0.0803 |
| gaussian_0p10 | 16 | 7 | 0.6835 | 1.3240 | 1.3240 | 0.2822 | 1.3712 | 0.5089 | 0.0774 |
| gaussian_0p10 | 17 | 4 | 0.7127 | 1.3910 | 1.3910 | 0.2530 | 1.3129 | 0.4845 | 0.0843 |
| gaussian_0p10 | 18 | 5 | 1.0750 | 2.0852 | 2.0852 | 0.2426 | 2.1201 | 0.6633 | 0.0974 |
| gaussian_0p10 | 19 | 3 | 0.8708 | 1.6943 | 1.6943 | 0.1828 | 1.4699 | 0.2211 | 0.1019 |
| gaussian_0p10 | 20 | 6 | 0.6528 | 1.2727 | 1.2727 | 0.1340 | 1.2401 | 0.4772 | 0.0755 |
| gaussian_0p10 | 21 | 2 | 0.8159 | 1.5903 | 1.5903 | 0.2272 | 1.6318 | 0.3147 | 0.0996 |
| gaussian_0p10 | 22 | 2 | 1.1597 | 2.2498 | 2.2498 | -0.2221 | 2.1436 | 0.2325 | 0.0852 |
| gaussian_0p10 | 23 | 1 | 0.7370 | 1.4383 | 1.4383 | -0.1207 | 1.1591 | 0.0988 | 0.1074 |
| gaussian_0p10 | 24 | 1 | 0.7461 | 1.4558 | 1.4558 | 0.2307 | 1.4823 | 0.2113 | 0.1012 |
| gaussian_0p10 | 25 | 3 | 1.1020 | 2.1380 | 2.1380 | 0.2327 | 2.1892 | 0.5841 | 0.0953 |
| gaussian_0p10 | 26 | 13 | 0.9707 | 1.8552 | 1.8552 | 0.1407 | 1.7189 | 0.9792 | 0.0642 |
| gaussian_0p10 | 27 | 14 | 0.6156 | 1.2006 | 1.2006 | 0.5331 | 1.3303 | 0.9729 | 0.0712 |
| gaussian_0p10 | 28 | 5 | 0.6795 | 1.3235 | 1.3235 | 0.2092 | 1.2832 | 0.3593 | 0.0847 |
| gaussian_0p10 | 29 | 2 | 0.7226 | 1.4103 | 1.4103 | -0.2058 | 1.3388 | 0.1393 | 0.0977 |
| gaussian_0p10 | 30 | 1 | 0.4758 | 0.9310 | 0.9310 | 0.2318 | 0.9562 | 0.2224 | 0.0938 |
| gaussian_0p10 | 31 | 2 | 1.1666 | 2.2599 | 2.2599 | 0.2335 | 2.1966 | 0.2511 | 0.0972 |
| gaussian_0p10 | 32 | 1 | 0.6418 | 1.2537 | 1.2537 | 0.2277 | 1.2824 | 0.2727 | 0.1048 |
| gaussian_0p10 | 33 | 1 | 0.8236 | 1.6045 | 1.6045 | 0.1620 | 1.5471 | 0.0389 | 0.1084 |
| gaussian_0p10 | 34 | 2 | 0.6910 | 1.3491 | 1.3491 | -0.3227 | 1.2872 | 0.1100 | 0.0936 |
| gaussian_0p10 | 35 | 1 | 0.8330 | 1.6245 | 1.6245 | -0.3616 | 1.5254 | 0.1343 | 0.1080 |
| gaussian_0p10 | 36 | 6 | 0.7791 | 1.5188 | 1.5188 | 0.1657 | 1.5074 | 0.5309 | 0.0821 |
| gaussian_0p10 | 37 | 5 | 0.7561 | 1.4743 | 1.4743 | 0.2429 | 1.5139 | 0.4978 | 0.0948 |
| gaussian_0p10 | 38 | 3 | 0.6954 | 1.3574 | 1.3574 | 0.2037 | 1.3856 | 0.3309 | 0.0911 |
| gaussian_0p10 | 39 | 1 | 1.0096 | 1.9615 | 1.9615 | 0.4445 | 1.9868 | 0.0923 | 0.1043 |
| gaussian_0p10 | 40 | 2 | 1.4937 | 2.8744 | 2.8744 | -0.0909 | 2.7104 | 0.2079 | 0.1092 |
| gaussian_0p10 | 41 | 24 | 1.1191 | 2.1341 | 2.1341 | 0.1434 | 1.4960 | 0.9255 | 0.0481 |
| gaussian_0p10 | 42 | 14 | 1.2634 | 2.4335 | 2.4335 | -0.0725 | 1.6601 | 0.9436 | 0.0676 |
| gaussian_0p10 | 43 | 1 | 0.9188 | 1.7885 | 1.7885 | 0.1509 | 1.8027 | 0.2049 | 0.1115 |
| gaussian_0p10 | 44 | 8 | 1.1525 | 2.2238 | 2.2238 | 0.4551 | 2.4099 | 0.8282 | 0.0792 |
| gaussian_0p10 | 45 | 4 | 0.7531 | 1.4690 | 1.4690 | 0.1244 | 1.4723 | 0.3360 | 0.0941 |
| gaussian_0p10 | 46 | 7 | 0.9795 | 1.9048 | 1.9048 | 0.2416 | 1.9286 | 0.6860 | 0.0882 |
| gaussian_0p10 | 47 | 2 | 1.2601 | 2.4386 | 2.4386 | 0.0363 | 2.3477 | 0.2631 | 0.0934 |
| gaussian_0p10 | 48 | 4 | 0.6831 | 1.3342 | 1.3342 | 0.0591 | 1.3009 | 0.3279 | 0.0868 |
| gaussian_0p10 | 49 | 7 | 1.0264 | 1.9730 | 1.9730 | -0.0490 | 1.6925 | 0.5860 | 0.0798 |
| gaussian_0p10 | 50 | 2 | 0.6914 | 1.3498 | 1.3498 | 0.3286 | 1.3911 | 0.1491 | 0.0905 |
| gaussian_0p10 | 52 | 2 | 1.0222 | 1.9864 | 1.9864 | 0.0744 | 1.9523 | 0.2139 | 0.1069 |
| gaussian_0p10 | 53 | 3 | 0.5820 | 1.1378 | 1.1378 | -0.1470 | 1.0633 | 0.2555 | 0.1071 |
| gaussian_0p10 | 54 | 1 | 0.8718 | 1.6985 | 1.6985 | 0.0332 | 1.6943 | 0.1195 | 0.1052 |
| gaussian_0p10 | 55 | 4 | 1.0700 | 2.0703 | 2.0703 | 0.0962 | 0.9986 | 0.3654 | 0.0853 |
| gaussian_0p10 | 56 | 1 | 0.7605 | 1.4842 | 1.4842 | 0.0049 | 1.3444 | 0.1436 | 0.0959 |
| gaussian_0p10 | 57 | 12 | 1.1216 | 2.1765 | 2.1765 | 0.2382 | 2.1643 | 0.9723 | 0.0778 |
| gaussian_0p10 | 58 | 5 | 0.7532 | 1.4687 | 1.4687 | 0.0169 | 1.1333 | 0.3432 | 0.0875 |
| gaussian_0p10 | 59 | 2 | 1.0289 | 1.9986 | 1.9986 | -0.2799 | 1.6409 | 0.1841 | 0.0862 |
| gaussian_0p10 | 60 | 1 | 1.2907 | 2.4986 | 2.4986 | -0.1417 | 2.0713 | 0.2215 | 0.1012 |
| gaussian_0p10 | 61 | 1 | 0.9054 | 1.7617 | 1.7617 | -0.0134 | 1.6418 | 0.1015 | 0.1099 |
| gaussian_0p10 | 62 | 5 | 1.0444 | 2.0281 | 2.0281 | 0.2505 | 2.0588 | 0.5009 | 0.1001 |
| gaussian_0p10 | 63 | 21 | 1.1291 | 2.1909 | 2.1909 | 0.1879 | 2.1645 | 0.9364 | 0.0569 |
| gaussian_0p10 | 64 | 1 | 0.8049 | 1.5701 | 1.5701 | -0.1916 | 1.5037 | 0.1247 | 0.1031 |
| gaussian_0p10 | 65 | 1 | 0.9755 | 1.8954 | 1.8954 | 0.1186 | 1.7398 | 0.1426 | 0.1028 |


## Interpretation guide

- Positive `lift_vs_stimulus_rmse` means lower score RMSE than stimulus-only.
- `dev_pearson` is read directly because stimulus-only predicted deviation is constant zero.
- `pred_dev_std` tracks whether the model escapes near-zero residual collapse.
- A config is only interesting if it improves RMSE/deviation metrics without simply inflating noise.
- Any promising config should be re-tested on broader smoke folds before full LOSO.
