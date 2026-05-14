# ROCA-I-DARE EEG Augmentation Matrix Smoke

This is an exploratory train-only augmentation matrix. It is not final model selection.

## Configuration

- target: `valence`
- cache: `baseline_corrected`
- model: `eeg_bc_residual_huber_norm_gaussian10_valence_full_loso`
- max_folds: `63`
- epochs_max: `50`
- patience: `8`
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
| gaussian_0p10 | valence | eeg_bc_residual_huber_norm_gaussian10_valence_full_loso | 2016 | 1.0259 | 1.2645 | 0.8648 | 0.8774 | 0.9474 | 1.2645 | 0.0284 | 0.5134 | 1.2578 | 0.1693 | -0.0067 | -0.0022 | 0.0041 | -0.0067 |
| gaussian_0p10 | valence | stimulus_only | 2016 | 1.0221 | 1.2578 | 0.8663 | 0.8796 | 0.9433 | 1.2578 |  | 0.0000 | 1.2578 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |


## Best rows

| best_metric | best_metric_value | augmentation_config | rmse | lift_vs_stimulus_rmse | balanced_accuracy | lift_vs_stimulus_balanced_accuracy | auroc | lift_vs_stimulus_auroc | dev_pearson | pred_dev_std |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lift_vs_stimulus_rmse | -0.0067 | gaussian_0p10 | 1.2645 | -0.0067 | 0.8774 | -0.0022 | 0.9474 | 0.0041 | 0.0284 | 0.1693 |
| dev_pearson | 0.0284 | gaussian_0p10 | 1.2645 | -0.0067 | 0.8774 | -0.0022 | 0.9474 | 0.0041 | 0.0284 | 0.1693 |
| lift_vs_stimulus_auroc | 0.0041 | gaussian_0p10 | 1.2645 | -0.0067 | 0.8774 | -0.0022 | 0.9474 | 0.0041 | 0.0284 | 0.1693 |
| pred_dev_std | 0.1693 | gaussian_0p10 | 1.2645 | -0.0067 | 0.8774 | -0.0022 | 0.9474 | 0.0041 | 0.0284 | 0.1693 |
| rmse | 1.2645 | gaussian_0p10 | 1.2645 | -0.0067 | 0.8774 | -0.0022 | 0.9474 | 0.0041 | 0.0284 | 0.1693 |


## Fold summary

| augmentation_config | test_subject | best_epoch | best_val_rmse_scaled | rmse | dev_rmse | dev_pearson | true_dev_std | pred_dev_std | final_train_last_loss |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gaussian_0p10 | 1 | 1 | 1.0133 | 1.1813 | 1.1813 | 0.3012 | 1.1175 | 0.0633 | 0.4415 |
| gaussian_0p10 | 2 | 4 | 0.9037 | 1.5746 | 1.5746 | 0.1244 | 1.4998 | 0.1963 | 0.4183 |
| gaussian_0p10 | 3 | 1 | 1.0773 | 1.1856 | 1.1856 | 0.2757 | 1.1804 | 0.0431 | 0.4438 |
| gaussian_0p10 | 5 | 1 | 1.0760 | 1.4816 | 1.4816 | 0.3269 | 1.4830 | 0.0513 | 0.4399 |
| gaussian_0p10 | 6 | 1 | 1.1382 | 1.1897 | 1.1897 | -0.3974 | 1.1527 | 0.0654 | 0.4388 |
| gaussian_0p10 | 7 | 2 | 1.0115 | 0.7913 | 0.7913 | 0.1781 | 0.7539 | 0.0800 | 0.4229 |
| gaussian_0p10 | 8 | 3 | 1.0150 | 1.0450 | 1.0450 | 0.1343 | 0.9651 | 0.1090 | 0.4280 |
| gaussian_0p10 | 9 | 2 | 1.0044 | 1.1704 | 1.1704 | 0.0425 | 1.0618 | 0.1358 | 0.4288 |
| gaussian_0p10 | 10 | 1 | 1.0744 | 1.0186 | 1.0186 | -0.2213 | 0.9997 | 0.0493 | 0.4381 |
| gaussian_0p10 | 11 | 2 | 0.8947 | 1.4626 | 1.4626 | -0.1122 | 1.4456 | 0.1019 | 0.4294 |
| gaussian_0p10 | 12 | 4 | 1.0989 | 1.1693 | 1.1693 | 0.1266 | 1.1566 | 0.1080 | 0.4221 |
| gaussian_0p10 | 13 | 1 | 0.9329 | 1.0291 | 1.0291 | -0.3280 | 0.9336 | 0.0278 | 0.4357 |
| gaussian_0p10 | 14 | 1 | 0.9608 | 0.8861 | 0.8861 | 0.0115 | 0.8364 | 0.0616 | 0.4351 |
| gaussian_0p10 | 15 | 1 | 0.9396 | 1.0986 | 1.0986 | 0.3127 | 1.1003 | 0.0193 | 0.4401 |
| gaussian_0p10 | 16 | 1 | 0.9975 | 1.1365 | 1.1365 | -0.2039 | 0.9397 | 0.0490 | 0.4399 |
| gaussian_0p10 | 17 | 1 | 0.9441 | 1.1893 | 1.1893 | 0.0077 | 1.1698 | 0.0422 | 0.4375 |
| gaussian_0p10 | 18 | 2 | 1.0302 | 1.7339 | 1.7339 | 0.2644 | 1.7489 | 0.1466 | 0.4316 |
| gaussian_0p10 | 19 | 1 | 0.8890 | 1.3039 | 1.3039 | 0.1938 | 1.3052 | 0.0451 | 0.4399 |
| gaussian_0p10 | 20 | 2 | 0.9645 | 1.1715 | 1.1715 | 0.0663 | 0.9188 | 0.0888 | 0.4293 |
| gaussian_0p10 | 21 | 2 | 1.0570 | 1.0387 | 1.0387 | 0.1614 | 1.0395 | 0.0752 | 0.4345 |
| gaussian_0p10 | 22 | 1 | 0.9978 | 1.1998 | 1.1998 | -0.1233 | 1.1568 | 0.0160 | 0.4453 |
| gaussian_0p10 | 23 | 4 | 1.0238 | 1.0379 | 1.0379 | 0.0854 | 1.0232 | 0.1230 | 0.4258 |
| gaussian_0p10 | 24 | 1 | 0.9722 | 1.2142 | 1.2142 | 0.0087 | 1.0480 | 0.0464 | 0.4373 |
| gaussian_0p10 | 25 | 5 | 0.8950 | 1.6220 | 1.6220 | -0.1189 | 1.5409 | 0.2864 | 0.4048 |
| gaussian_0p10 | 26 | 3 | 1.0164 | 1.7307 | 1.7307 | 0.0896 | 1.5027 | 0.2328 | 0.4155 |
| gaussian_0p10 | 27 | 2 | 0.9786 | 1.3280 | 1.3280 | 0.1976 | 1.2826 | 0.0970 | 0.4292 |
| gaussian_0p10 | 28 | 1 | 0.8889 | 1.3213 | 1.3213 | -0.2098 | 1.2734 | 0.0702 | 0.4442 |
| gaussian_0p10 | 29 | 4 | 1.0446 | 1.0401 | 1.0401 | 0.0622 | 0.8583 | 0.1583 | 0.4210 |
| gaussian_0p10 | 30 | 3 | 0.9858 | 1.0360 | 1.0360 | -0.1969 | 0.9805 | 0.1929 | 0.4176 |
| gaussian_0p10 | 31 | 3 | 1.0393 | 1.6065 | 1.6065 | 0.1780 | 1.5158 | 0.1349 | 0.4240 |
| gaussian_0p10 | 32 | 2 | 0.9305 | 1.0964 | 1.0964 | 0.1107 | 0.9821 | 0.0712 | 0.4308 |
| gaussian_0p10 | 33 | 2 | 0.9824 | 0.7946 | 0.7946 | -0.0275 | 0.7908 | 0.0513 | 0.4307 |
| gaussian_0p10 | 34 | 2 | 0.9771 | 1.3950 | 1.3950 | -0.0086 | 1.0639 | 0.0792 | 0.4312 |
| gaussian_0p10 | 35 | 2 | 0.9935 | 0.9126 | 0.9126 | -0.0303 | 0.8615 | 0.0689 | 0.4318 |
| gaussian_0p10 | 36 | 4 | 0.9295 | 0.9574 | 0.9574 | 0.3584 | 0.9870 | 0.2216 | 0.4147 |
| gaussian_0p10 | 37 | 3 | 0.9764 | 1.2202 | 1.2202 | 0.0355 | 1.2104 | 0.0956 | 0.4237 |
| gaussian_0p10 | 38 | 1 | 1.0557 | 1.5907 | 1.5907 | 0.1467 | 1.5947 | 0.0316 | 0.4338 |
| gaussian_0p10 | 39 | 2 | 0.9322 | 1.1660 | 1.1660 | 0.0989 | 1.1533 | 0.1135 | 0.4290 |
| gaussian_0p10 | 40 | 1 | 0.8570 | 1.4591 | 1.4591 | -0.3656 | 1.4100 | 0.0367 | 0.4371 |
| gaussian_0p10 | 41 | 6 | 0.9261 | 1.5526 | 1.5526 | 0.1240 | 1.5121 | 0.2829 | 0.3978 |
| gaussian_0p10 | 42 | 1 | 1.0526 | 1.0859 | 1.0859 | 0.2506 | 1.0508 | 0.0349 | 0.4394 |
| gaussian_0p10 | 43 | 4 | 1.0682 | 1.0824 | 1.0824 | -0.1672 | 1.0277 | 0.1629 | 0.4121 |
| gaussian_0p10 | 44 | 1 | 1.0237 | 1.5390 | 1.5390 | -0.0393 | 1.3716 | 0.0390 | 0.4359 |
| gaussian_0p10 | 45 | 1 | 0.9529 | 0.9437 | 0.9437 | -0.3381 | 0.9360 | 0.0218 | 0.4441 |
| gaussian_0p10 | 46 | 2 | 1.0332 | 1.3144 | 1.3144 | 0.2401 | 1.2878 | 0.0599 | 0.4279 |
| gaussian_0p10 | 47 | 2 | 0.9141 | 1.8224 | 1.8224 | -0.0935 | 1.8135 | 0.0740 | 0.4337 |
| gaussian_0p10 | 48 | 3 | 0.9463 | 1.0703 | 1.0703 | -0.2510 | 0.9611 | 0.1972 | 0.4237 |
| gaussian_0p10 | 49 | 2 | 1.0382 | 1.3378 | 1.3378 | -0.0195 | 1.3317 | 0.0576 | 0.4279 |
| gaussian_0p10 | 50 | 1 | 1.2373 | 1.2882 | 1.2882 | -0.0923 | 1.2861 | 0.0210 | 0.4408 |
| gaussian_0p10 | 52 | 2 | 0.9677 | 1.5379 | 1.5379 | 0.1263 | 1.3984 | 0.1839 | 0.4319 |
| gaussian_0p10 | 53 | 1 | 0.8521 | 1.0174 | 1.0174 | -0.0351 | 0.8935 | 0.0392 | 0.4469 |
| gaussian_0p10 | 54 | 3 | 0.9823 | 1.4142 | 1.4142 | 0.1552 | 1.4152 | 0.2382 | 0.4221 |
| gaussian_0p10 | 55 | 1 | 1.0715 | 1.2669 | 1.2669 | 0.1633 | 1.2155 | 0.0340 | 0.4324 |
| gaussian_0p10 | 56 | 1 | 1.1750 | 1.0811 | 1.0811 | 0.2413 | 1.0862 | 0.0229 | 0.4422 |
| gaussian_0p10 | 57 | 3 | 0.9348 | 1.3071 | 1.3071 | 0.3741 | 1.0644 | 0.1077 | 0.4300 |
| gaussian_0p10 | 58 | 1 | 1.0111 | 0.9956 | 0.9956 | 0.2243 | 0.9651 | 0.0319 | 0.4409 |
| gaussian_0p10 | 59 | 3 | 0.8633 | 1.3711 | 1.3711 | 0.0713 | 1.3710 | 0.1434 | 0.4316 |
| gaussian_0p10 | 60 | 2 | 0.9343 | 1.2345 | 1.2345 | 0.1002 | 1.2404 | 0.1105 | 0.4347 |
| gaussian_0p10 | 61 | 1 | 0.8695 | 1.7332 | 1.7332 | 0.1031 | 1.4155 | 0.0292 | 0.4384 |
| gaussian_0p10 | 62 | 1 | 1.1247 | 1.2631 | 1.2631 | -0.0327 | 1.1467 | 0.0441 | 0.4363 |
| gaussian_0p10 | 63 | 4 | 0.9969 | 1.2210 | 1.2210 | -0.2347 | 1.1369 | 0.2291 | 0.4165 |
| gaussian_0p10 | 64 | 1 | 1.1736 | 1.1906 | 1.1906 | 0.0895 | 1.0763 | 0.0606 | 0.4454 |
| gaussian_0p10 | 65 | 1 | 1.0685 | 0.9713 | 0.9713 | -0.0102 | 0.9559 | 0.0774 | 0.4460 |


## Interpretation guide

- Positive `lift_vs_stimulus_rmse` means lower score RMSE than stimulus-only.
- `dev_pearson` is read directly because stimulus-only predicted deviation is constant zero.
- `pred_dev_std` tracks whether the model escapes near-zero residual collapse.
- A config is only interesting if it improves RMSE/deviation metrics without simply inflating noise.
- Any promising config should be re-tested on broader smoke folds before full LOSO.
