# ROCA-I-DARE EEG Augmentation Matrix Smoke

This is an exploratory train-only augmentation matrix. It is not final model selection.

## Configuration

- target: `arousal`
- cache: `baseline_corrected`
- model: `eeg_bc_residual_huber_norm_augmented_smoke`
- max_folds: `6`
- epochs_max: `50`
- patience: `8`
- batch_size: `32`
- optimizer: `AdamW(lr=0.0001, weight_decay=0.001)`
- loss: `HuberLoss(delta=1.0) on scaled residual`
- configs: `['none', 'gaussian_0p05', 'gaussian_0p10', 'gain_0p10', 'gaussian_0p05_gain_0p10', 'gaussian_0p05_shift16']`

## Augmentation configs

```json
{
  "none": {
    "description": "No augmentation control",
    "gaussian_std": 0.0,
    "gain_jitter": 0.0,
    "time_shift_max": 0,
    "time_mask_frac": 0.0,
    "channel_drop_prob": 0.0
  },
  "gaussian_0p05": {
    "description": "Additive Gaussian noise, std=0.05 in normalized EEG units",
    "gaussian_std": 0.05,
    "gain_jitter": 0.0,
    "time_shift_max": 0,
    "time_mask_frac": 0.0,
    "channel_drop_prob": 0.0
  },
  "gaussian_0p10": {
    "description": "Additive Gaussian noise, std=0.10 in normalized EEG units",
    "gaussian_std": 0.1,
    "gain_jitter": 0.0,
    "time_shift_max": 0,
    "time_mask_frac": 0.0,
    "channel_drop_prob": 0.0
  },
  "gain_0p10": {
    "description": "Global amplitude gain jitter, gain in [0.90, 1.10]",
    "gaussian_std": 0.0,
    "gain_jitter": 0.1,
    "time_shift_max": 0,
    "time_mask_frac": 0.0,
    "channel_drop_prob": 0.0
  },
  "gaussian_0p05_gain_0p10": {
    "description": "Gaussian noise std=0.05 plus global gain jitter 0.10",
    "gaussian_std": 0.05,
    "gain_jitter": 0.1,
    "time_shift_max": 0,
    "time_mask_frac": 0.0,
    "channel_drop_prob": 0.0
  },
  "gaussian_0p05_shift16": {
    "description": "Gaussian noise std=0.05 plus random time shift up to 16 samples",
    "gaussian_std": 0.05,
    "gain_jitter": 0.0,
    "time_shift_max": 16,
    "time_mask_frac": 0.0,
    "channel_drop_prob": 0.0
  }
}
```

## Main metrics

| augmentation_config | target | model | n | mae | rmse | pearson | balanced_accuracy | auroc | dev_rmse | dev_pearson | dev_sign_acc | true_dev_std | pred_dev_std | lift_vs_stimulus_rmse | lift_vs_stimulus_balanced_accuracy | lift_vs_stimulus_auroc | lift_vs_stimulus_dev_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gain_0p10 | arousal | eeg_bc_residual_huber_norm_augmented_smoke | 192 | 1.9356 | 2.3727 | 0.4399 | 0.6188 | 0.6607 | 2.3727 | 0.0216 | 0.5312 | 2.2785 | 0.2459 | 0.0103 | -0.0092 | 0.0130 | 0.0103 |
| gain_0p10 | arousal | stimulus_only | 192 | 1.9362 | 2.3830 | 0.4413 | 0.6280 | 0.6477 | 2.3830 |  | 0.0000 | 2.2785 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| gaussian_0p05 | arousal | eeg_bc_residual_huber_norm_augmented_smoke | 192 | 1.9107 | 2.3484 | 0.4508 | 0.6355 | 0.6602 | 2.3484 | 0.0930 | 0.5729 | 2.2785 | 0.3395 | 0.0346 | 0.0075 | 0.0125 | 0.0346 |
| gaussian_0p05 | arousal | stimulus_only | 192 | 1.9362 | 2.3830 | 0.4413 | 0.6280 | 0.6477 | 2.3830 |  | 0.0000 | 2.2785 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| gaussian_0p05_gain_0p10 | arousal | eeg_bc_residual_huber_norm_augmented_smoke | 192 | 1.9546 | 2.4491 | 0.4342 | 0.6174 | 0.6577 | 2.4491 | -0.0220 | 0.5260 | 2.2785 | 0.2759 | -0.0661 | -0.0106 | 0.0100 | -0.0661 |
| gaussian_0p05_gain_0p10 | arousal | stimulus_only | 192 | 1.9362 | 2.3830 | 0.4413 | 0.6280 | 0.6477 | 2.3830 |  | 0.0000 | 2.2785 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| gaussian_0p05_shift16 | arousal | eeg_bc_residual_huber_norm_augmented_smoke | 192 | 2.0102 | 2.4646 | 0.3939 | 0.6188 | 0.6153 | 2.4646 | -0.2895 | 0.3698 | 2.2785 | 0.2726 | -0.0815 | -0.0092 | -0.0323 | -0.0815 |
| gaussian_0p05_shift16 | arousal | stimulus_only | 192 | 1.9362 | 2.3830 | 0.4413 | 0.6280 | 0.6477 | 2.3830 |  | 0.0000 | 2.2785 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| gaussian_0p10 | arousal | eeg_bc_residual_huber_norm_augmented_smoke | 192 | 1.8412 | 2.3061 | 0.4965 | 0.6234 | 0.6982 | 2.3061 | 0.4671 | 0.6927 | 2.2785 | 0.2269 | 0.0770 | -0.0046 | 0.0506 | 0.0770 |
| gaussian_0p10 | arousal | stimulus_only | 192 | 1.9362 | 2.3830 | 0.4413 | 0.6280 | 0.6477 | 2.3830 |  | 0.0000 | 2.2785 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| none | arousal | eeg_bc_residual_huber_norm_augmented_smoke | 192 | 1.9772 | 2.4436 | 0.4440 | 0.6280 | 0.6567 | 2.4436 | 0.0467 | 0.4583 | 2.2785 | 0.2714 | -0.0606 | 0.0000 | 0.0090 | -0.0606 |
| none | arousal | stimulus_only | 192 | 1.9362 | 2.3830 | 0.4413 | 0.6280 | 0.6477 | 2.3830 |  | 0.0000 | 2.2785 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |


## Best rows

| best_metric | best_metric_value | augmentation_config | rmse | lift_vs_stimulus_rmse | balanced_accuracy | lift_vs_stimulus_balanced_accuracy | auroc | lift_vs_stimulus_auroc | dev_pearson | pred_dev_std |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lift_vs_stimulus_rmse | 0.0770 | gaussian_0p10 | 2.3061 | 0.0770 | 0.6234 | -0.0046 | 0.6982 | 0.0506 | 0.4671 | 0.2269 |
| dev_pearson | 0.4671 | gaussian_0p10 | 2.3061 | 0.0770 | 0.6234 | -0.0046 | 0.6982 | 0.0506 | 0.4671 | 0.2269 |
| lift_vs_stimulus_auroc | 0.0506 | gaussian_0p10 | 2.3061 | 0.0770 | 0.6234 | -0.0046 | 0.6982 | 0.0506 | 0.4671 | 0.2269 |
| pred_dev_std | 0.3395 | gaussian_0p05 | 2.3484 | 0.0346 | 0.6355 | 0.0075 | 0.6602 | 0.0125 | 0.0930 | 0.3395 |
| rmse | 2.3061 | gaussian_0p10 | 2.3061 | 0.0770 | 0.6234 | -0.0046 | 0.6982 | 0.0506 | 0.4671 | 0.2269 |


## Fold summary

| augmentation_config | test_subject | best_epoch | best_val_rmse_scaled | rmse | dev_rmse | dev_pearson | true_dev_std | pred_dev_std | final_train_last_loss |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| none | 1 | 2 | 1.0107 | 1.8793 | 1.8793 | 0.1154 | 1.8731 | 0.2312 | 0.4262 |
| none | 2 | 1 | 0.9363 | 2.9232 | 2.9232 | 0.3580 | 1.5829 | 0.1373 | 0.4359 |
| none | 3 | 1 | 1.0967 | 1.8060 | 1.8060 | -0.0113 | 1.3539 | 0.1010 | 0.4413 |
| none | 5 | 1 | 1.1535 | 2.0865 | 2.0865 | -0.0599 | 1.5102 | 0.1391 | 0.4389 |
| none | 6 | 2 | 0.9373 | 3.7003 | 3.7003 | -0.0473 | 1.7902 | 0.3028 | 0.4237 |
| none | 7 | 2 | 0.9177 | 1.5629 | 1.5629 | 0.1353 | 1.2462 | 0.2062 | 0.4266 |
| gaussian_0p05 | 1 | 4 | 1.0155 | 1.8869 | 1.8869 | 0.1178 | 1.8731 | 0.4949 | 0.3964 |
| gaussian_0p05 | 2 | 3 | 0.9106 | 2.5546 | 2.5546 | 0.1636 | 1.5829 | 0.3726 | 0.4184 |
| gaussian_0p05 | 3 | 1 | 1.1072 | 1.8246 | 1.8246 | -0.0874 | 1.3539 | 0.0708 | 0.4370 |
| gaussian_0p05 | 5 | 4 | 1.1394 | 1.8051 | 1.8051 | 0.0485 | 1.5102 | 0.4029 | 0.4042 |
| gaussian_0p05 | 6 | 1 | 0.9439 | 3.6678 | 3.6678 | -0.0035 | 1.7902 | 0.1402 | 0.4351 |
| gaussian_0p05 | 7 | 2 | 0.9162 | 1.7216 | 1.7216 | 0.2369 | 1.2462 | 0.1857 | 0.4260 |
| gaussian_0p10 | 1 | 1 | 1.0056 | 1.8408 | 1.8408 | 0.4272 | 1.8731 | 0.0788 | 0.4415 |
| gaussian_0p10 | 2 | 2 | 0.9229 | 2.6726 | 2.6726 | 0.3345 | 1.5829 | 0.2145 | 0.4319 |
| gaussian_0p10 | 3 | 1 | 1.1185 | 1.6447 | 1.6447 | -0.0223 | 1.3539 | 0.0691 | 0.4451 |
| gaussian_0p10 | 5 | 1 | 1.1541 | 1.6810 | 1.6810 | 0.0515 | 1.5102 | 0.1098 | 0.4491 |
| gaussian_0p10 | 6 | 1 | 0.9698 | 3.7094 | 3.7094 | -0.0809 | 1.7902 | 0.0921 | 0.4417 |
| gaussian_0p10 | 7 | 1 | 0.9033 | 1.4440 | 1.4440 | 0.2027 | 1.2462 | 0.1246 | 0.4460 |
| gain_0p10 | 1 | 2 | 0.9936 | 1.8920 | 1.8920 | 0.0529 | 1.8731 | 0.2518 | 0.4322 |
| gain_0p10 | 2 | 1 | 0.9219 | 2.8194 | 2.8194 | 0.2814 | 1.5829 | 0.1519 | 0.4433 |
| gain_0p10 | 3 | 1 | 1.1020 | 1.8546 | 1.8546 | -0.0476 | 1.3539 | 0.0574 | 0.4446 |
| gain_0p10 | 5 | 5 | 1.1812 | 1.6045 | 1.6045 | 0.1371 | 1.5102 | 0.2461 | 0.4084 |
| gain_0p10 | 6 | 1 | 0.9483 | 3.6296 | 3.6296 | -0.2562 | 1.7902 | 0.1030 | 0.4399 |
| gain_0p10 | 7 | 1 | 0.9067 | 1.7499 | 1.7499 | 0.1985 | 1.2462 | 0.1720 | 0.4400 |
| gaussian_0p05_gain_0p10 | 1 | 1 | 1.0084 | 1.8621 | 1.8621 | 0.2188 | 1.8731 | 0.0607 | 0.4438 |
| gaussian_0p05_gain_0p10 | 2 | 2 | 0.9367 | 3.0677 | 3.0677 | 0.2045 | 1.5829 | 0.3382 | 0.4301 |
| gaussian_0p05_gain_0p10 | 3 | 2 | 1.1037 | 1.7365 | 1.7365 | -0.3637 | 1.3539 | 0.0518 | 0.4357 |
| gaussian_0p05_gain_0p10 | 5 | 3 | 1.1495 | 1.6411 | 1.6411 | 0.1675 | 1.5102 | 0.2350 | 0.4229 |
| gaussian_0p05_gain_0p10 | 6 | 1 | 0.9452 | 3.9037 | 3.9037 | -0.0387 | 1.7902 | 0.1054 | 0.4482 |
| gaussian_0p05_gain_0p10 | 7 | 1 | 0.9118 | 1.4707 | 1.4707 | 0.0742 | 1.2462 | 0.1554 | 0.4428 |
| gaussian_0p05_shift16 | 1 | 2 | 0.9972 | 1.7803 | 1.7803 | 0.4719 | 1.8731 | 0.2320 | 0.4313 |
| gaussian_0p05_shift16 | 2 | 2 | 0.9174 | 2.7072 | 2.7072 | 0.3237 | 1.5829 | 0.2939 | 0.4334 |
| gaussian_0p05_shift16 | 3 | 1 | 1.1077 | 2.1395 | 2.1395 | -0.0804 | 1.3539 | 0.0731 | 0.4439 |
| gaussian_0p05_shift16 | 5 | 1 | 1.1678 | 1.8998 | 1.8998 | -0.0233 | 1.5102 | 0.1484 | 0.4398 |
| gaussian_0p05_shift16 | 6 | 1 | 0.9404 | 3.8359 | 3.8359 | -0.0303 | 1.7902 | 0.1364 | 0.4409 |
| gaussian_0p05_shift16 | 7 | 1 | 0.9076 | 1.7450 | 1.7450 | 0.2027 | 1.2462 | 0.0772 | 0.4376 |


## Interpretation guide

- Positive `lift_vs_stimulus_rmse` means lower score RMSE than stimulus-only.
- `dev_pearson` is read directly because stimulus-only predicted deviation is constant zero.
- `pred_dev_std` tracks whether the model escapes near-zero residual collapse.
- A config is only interesting if it improves RMSE/deviation metrics without simply inflating noise.
- Any promising config should be re-tested on broader smoke folds before full LOSO.
