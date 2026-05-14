# ROCA-I-DARE EEG Augmentation Matrix Smoke

This is an exploratory train-only augmentation matrix. It is not final model selection.

## Configuration

- target: `valence`
- cache: `baseline_corrected`
- model: `eeg_bc_residual_huber_norm_gaussian10_valence_test_oracle`
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
| gaussian_0p10 | valence | eeg_bc_residual_huber_norm_gaussian10_valence_test_oracle | 2016 | 0.9746 | 1.2153 | 0.8758 | 0.8799 | 0.9521 | 1.2153 | 0.2579 | 0.5843 | 1.2578 | 0.3132 | 0.0425 | 0.0003 | 0.0088 | 0.0425 |
| gaussian_0p10 | valence | stimulus_only | 2016 | 1.0221 | 1.2578 | 0.8663 | 0.8796 | 0.9433 | 1.2578 |  | 0.0000 | 1.2578 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |


## Best rows

| best_metric | best_metric_value | augmentation_config | rmse | lift_vs_stimulus_rmse | balanced_accuracy | lift_vs_stimulus_balanced_accuracy | auroc | lift_vs_stimulus_auroc | dev_pearson | pred_dev_std |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lift_vs_stimulus_rmse | 0.0425 | gaussian_0p10 | 1.2153 | 0.0425 | 0.8799 | 0.0003 | 0.9521 | 0.0088 | 0.2579 | 0.3132 |
| dev_pearson | 0.2579 | gaussian_0p10 | 1.2153 | 0.0425 | 0.8799 | 0.0003 | 0.9521 | 0.0088 | 0.2579 | 0.3132 |
| lift_vs_stimulus_auroc | 0.0088 | gaussian_0p10 | 1.2153 | 0.0425 | 0.8799 | 0.0003 | 0.9521 | 0.0088 | 0.2579 | 0.3132 |
| pred_dev_std | 0.3132 | gaussian_0p10 | 1.2153 | 0.0425 | 0.8799 | 0.0003 | 0.9521 | 0.0088 | 0.2579 | 0.3132 |
| rmse | 1.2153 | gaussian_0p10 | 1.2153 | 0.0425 | 0.8799 | 0.0003 | 0.9521 | 0.0088 | 0.2579 | 0.3132 |


## Fold summary

| augmentation_config | test_subject | best_epoch | best_val_rmse_scaled | rmse | dev_rmse | dev_pearson | true_dev_std | pred_dev_std | final_train_last_loss |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gaussian_0p10 | 1 | 4 | 0.8896 | 1.1198 | 1.1198 | 0.3294 | 1.1175 | 0.2061 | 0.1035 |
| gaussian_0p10 | 2 | 1 | 1.2290 | 1.5394 | 1.5394 | -0.1571 | 1.4998 | 0.0845 | 0.1236 |
| gaussian_0p10 | 3 | 6 | 0.8934 | 1.1247 | 1.1247 | 0.3068 | 1.1804 | 0.3512 | 0.0931 |
| gaussian_0p10 | 5 | 12 | 1.1040 | 1.3838 | 1.3838 | 0.3955 | 1.4830 | 0.7148 | 0.0699 |
| gaussian_0p10 | 6 | 1 | 0.9273 | 1.1679 | 1.1679 | -0.2107 | 1.1527 | 0.0630 | 0.1101 |
| gaussian_0p10 | 7 | 2 | 0.6002 | 0.7589 | 0.7589 | 0.1742 | 0.7539 | 0.0522 | 0.1118 |
| gaussian_0p10 | 8 | 3 | 0.7845 | 0.9896 | 0.9896 | 0.0420 | 0.9651 | 0.1363 | 0.0988 |
| gaussian_0p10 | 9 | 4 | 0.9226 | 1.1618 | 1.1618 | -0.0922 | 1.0618 | 0.1227 | 0.1129 |
| gaussian_0p10 | 10 | 1 | 0.8044 | 1.0150 | 1.0150 | -0.1693 | 0.9997 | 0.0655 | 0.1182 |
| gaussian_0p10 | 11 | 2 | 1.1491 | 1.4416 | 1.4416 | 0.1535 | 1.4456 | 0.0433 | 0.1169 |
| gaussian_0p10 | 12 | 8 | 0.9328 | 1.1746 | 1.1746 | 0.0515 | 1.1566 | 0.2724 | 0.0842 |
| gaussian_0p10 | 13 | 8 | 0.7677 | 0.9681 | 0.9681 | 0.1250 | 0.9336 | 0.2586 | 0.0807 |
| gaussian_0p10 | 14 | 2 | 0.6967 | 0.8799 | 0.8799 | -0.1988 | 0.8364 | 0.0659 | 0.0985 |
| gaussian_0p10 | 15 | 3 | 0.8529 | 1.0748 | 1.0748 | 0.2707 | 1.1003 | 0.1170 | 0.1063 |
| gaussian_0p10 | 16 | 4 | 0.7415 | 0.9354 | 0.9354 | 0.1032 | 0.9397 | 0.1292 | 0.1100 |
| gaussian_0p10 | 17 | 1 | 0.9576 | 1.2056 | 1.2056 | 0.0179 | 1.1698 | 0.0861 | 0.1040 |
| gaussian_0p10 | 18 | 5 | 1.3877 | 1.7305 | 1.7305 | 0.1533 | 1.7489 | 0.2723 | 0.0870 |
| gaussian_0p10 | 19 | 6 | 1.0160 | 1.2770 | 1.2770 | 0.2687 | 1.3052 | 0.1884 | 0.0856 |
| gaussian_0p10 | 20 | 1 | 0.8000 | 1.0092 | 1.0092 | -0.0738 | 0.9188 | 0.0737 | 0.1088 |
| gaussian_0p10 | 21 | 7 | 0.8172 | 1.0305 | 1.0305 | 0.2706 | 1.0395 | 0.3114 | 0.0840 |
| gaussian_0p10 | 22 | 1 | 0.9327 | 1.1742 | 1.1742 | -0.0763 | 1.1568 | 0.0411 | 0.1208 |
| gaussian_0p10 | 23 | 7 | 0.7994 | 1.0082 | 1.0082 | 0.1819 | 1.0232 | 0.2433 | 0.0774 |
| gaussian_0p10 | 24 | 4 | 0.9192 | 1.1574 | 1.1574 | -0.0422 | 1.0480 | 0.1107 | 0.1037 |
| gaussian_0p10 | 25 | 13 | 1.2120 | 1.5183 | 1.5183 | 0.2630 | 1.5409 | 0.7029 | 0.0756 |
| gaussian_0p10 | 26 | 8 | 1.1860 | 1.4857 | 1.4857 | 0.4104 | 1.5027 | 0.3925 | 0.0780 |
| gaussian_0p10 | 27 | 6 | 0.9969 | 1.2532 | 1.2532 | 0.2197 | 1.2826 | 0.2867 | 0.1103 |
| gaussian_0p10 | 28 | 5 | 1.0172 | 1.2793 | 1.2793 | 0.1531 | 1.2734 | 0.2395 | 0.0938 |
| gaussian_0p10 | 29 | 2 | 0.7264 | 0.9167 | 0.9167 | 0.1347 | 0.8583 | 0.0786 | 0.1127 |
| gaussian_0p10 | 30 | 1 | 0.7808 | 0.9853 | 0.9853 | -0.0829 | 0.9805 | 0.0384 | 0.1155 |
| gaussian_0p10 | 31 | 3 | 1.2446 | 1.5565 | 1.5565 | 0.0654 | 1.5158 | 0.1059 | 0.1118 |
| gaussian_0p10 | 32 | 4 | 0.7985 | 1.0046 | 1.0046 | -0.0245 | 0.9821 | 0.1882 | 0.1023 |
| gaussian_0p10 | 33 | 13 | 0.5959 | 0.7201 | 0.7201 | 0.4624 | 0.7908 | 0.5280 | 0.0707 |
| gaussian_0p10 | 34 | 4 | 0.9945 | 1.2491 | 1.2491 | 0.0224 | 1.0639 | 0.1707 | 0.0931 |
| gaussian_0p10 | 35 | 1 | 0.6983 | 0.8820 | 0.8820 | -0.1328 | 0.8615 | 0.0469 | 0.1243 |
| gaussian_0p10 | 36 | 7 | 0.7257 | 0.9155 | 0.9155 | 0.4058 | 0.9870 | 0.3571 | 0.0842 |
| gaussian_0p10 | 37 | 2 | 0.9660 | 1.2157 | 1.2157 | 0.0637 | 1.2104 | 0.0575 | 0.1147 |
| gaussian_0p10 | 38 | 8 | 1.1518 | 1.4413 | 1.4413 | 0.4344 | 1.5947 | 0.5940 | 0.0792 |
| gaussian_0p10 | 39 | 1 | 0.9274 | 1.1679 | 1.1679 | 0.0170 | 1.1533 | 0.0498 | 0.1193 |
| gaussian_0p10 | 40 | 1 | 1.1633 | 1.4599 | 1.4599 | -0.3257 | 1.4100 | 0.0633 | 0.1272 |
| gaussian_0p10 | 41 | 10 | 1.1994 | 1.5028 | 1.5028 | 0.1532 | 1.5121 | 0.3895 | 0.0768 |
| gaussian_0p10 | 42 | 9 | 0.8176 | 1.0307 | 1.0307 | 0.2704 | 1.0508 | 0.3371 | 0.0753 |
| gaussian_0p10 | 43 | 3 | 0.8259 | 1.0413 | 1.0413 | -0.0067 | 1.0277 | 0.0873 | 0.1064 |
| gaussian_0p10 | 44 | 5 | 1.2186 | 1.5264 | 1.5264 | -0.1271 | 1.3716 | 0.1769 | 0.1059 |
| gaussian_0p10 | 45 | 1 | 0.7465 | 0.9425 | 0.9425 | -0.0536 | 0.9360 | 0.0490 | 0.1208 |
| gaussian_0p10 | 46 | 4 | 1.0239 | 1.2865 | 1.2865 | 0.1132 | 1.2878 | 0.2027 | 0.0950 |
| gaussian_0p10 | 47 | 1 | 1.4603 | 1.8207 | 1.8207 | -0.1859 | 1.8135 | 0.0233 | 0.1073 |
| gaussian_0p10 | 48 | 3 | 0.8165 | 1.0297 | 1.0297 | -0.0612 | 0.9611 | 0.1773 | 0.0968 |
| gaussian_0p10 | 49 | 37 | 0.9272 | 1.1414 | 1.1414 | 0.5318 | 1.3317 | 0.7737 | 0.0459 |
| gaussian_0p10 | 50 | 4 | 1.0051 | 1.2639 | 1.2639 | 0.2018 | 1.2861 | 0.2134 | 0.1065 |
| gaussian_0p10 | 52 | 4 | 1.1952 | 1.4980 | 1.4980 | 0.0119 | 1.3984 | 0.2126 | 0.0991 |
| gaussian_0p10 | 53 | 5 | 0.8546 | 1.0769 | 1.0769 | -0.0064 | 0.8935 | 0.2247 | 0.0892 |
| gaussian_0p10 | 54 | 5 | 1.0826 | 1.3583 | 1.3583 | 0.3037 | 1.4152 | 0.3161 | 0.1076 |
| gaussian_0p10 | 55 | 9 | 0.8614 | 1.0829 | 1.0829 | 0.5075 | 1.2155 | 0.4557 | 0.0747 |
| gaussian_0p10 | 56 | 1 | 0.8697 | 1.0962 | 1.0962 | -0.0346 | 1.0862 | 0.0430 | 0.1078 |
| gaussian_0p10 | 57 | 5 | 0.8902 | 1.1191 | 1.1191 | 0.3504 | 1.0644 | 0.3331 | 0.1016 |
| gaussian_0p10 | 58 | 5 | 0.7706 | 0.9722 | 0.9722 | 0.1082 | 0.9651 | 0.2455 | 0.0982 |
| gaussian_0p10 | 59 | 1 | 1.0931 | 1.3726 | 1.3726 | 0.2200 | 1.3710 | 0.0287 | 0.1132 |
| gaussian_0p10 | 60 | 3 | 0.9664 | 1.2158 | 1.2158 | 0.2132 | 1.2404 | 0.1955 | 0.1188 |
| gaussian_0p10 | 61 | 5 | 1.4286 | 1.7816 | 1.7816 | -0.0478 | 1.4155 | 0.2034 | 0.1030 |
| gaussian_0p10 | 62 | 4 | 0.9792 | 1.2312 | 1.2312 | 0.2567 | 1.1467 | 0.1806 | 0.0977 |
| gaussian_0p10 | 63 | 1 | 0.9074 | 1.1431 | 1.1431 | -0.1559 | 1.1369 | 0.0360 | 0.1112 |
| gaussian_0p10 | 64 | 1 | 0.9681 | 1.2184 | 1.2184 | -0.2765 | 1.0763 | 0.0402 | 0.1082 |
| gaussian_0p10 | 65 | 1 | 0.7619 | 0.9617 | 0.9617 | -0.0344 | 0.9559 | 0.0644 | 0.1150 |


## Interpretation guide

- Positive `lift_vs_stimulus_rmse` means lower score RMSE than stimulus-only.
- `dev_pearson` is read directly because stimulus-only predicted deviation is constant zero.
- `pred_dev_std` tracks whether the model escapes near-zero residual collapse.
- A config is only interesting if it improves RMSE/deviation metrics without simply inflating noise.
- Any promising config should be re-tested on broader smoke folds before full LOSO.
