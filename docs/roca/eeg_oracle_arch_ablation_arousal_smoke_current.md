# ROCA EEG Oracle Architecture Ablation - arousal

This report tests architecture-internal ablations of the existing EEGSegmentClassifier/EEGSegmentEncoder.

## Configuration

- target: `arousal`
- cache: `baseline_corrected`
- augmentation_config: `gaussian_0p10`
- oracle_test_checkpoint_selection: `true`
- arch_configs: `A0_current, A7_no_channel_mha, A5_stem_attn`
- max_folds: `3`
- epochs/patience: `12` / `4`
- base optimizer: `AdamW(lr=0.0001, weight_decay=0.001)`

## Best EEG configs by RMSE lift, then dev_pearson

| arch_config | augmentation_config | target | model | n | rmse | lift_vs_stimulus_rmse | balanced_accuracy | lift_vs_stimulus_balanced_accuracy | macro_f1 | auroc | lift_vs_stimulus_auroc | dev_rmse | dev_pearson | pred_dev_std | true_dev_std |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A7_no_channel_mha | gaussian_0p10 | arousal | eeg_oracle_arch_A7_no_channel_mha | 96 | 1.921876 | 0.270527 | 0.718033 | 0.059251 | 0.722944 | 0.817330 | 0.107963 | 1.921876 | 0.528141 | 0.792185 | 2.163662 |
| A0_current | gaussian_0p10 | arousal | eeg_oracle_arch_A0_current | 96 | 1.948237 | 0.244166 | 0.711944 | 0.053162 | 0.718750 | 0.822014 | 0.112646 | 1.948237 | 0.549976 | 0.758836 | 2.163662 |
| A5_stem_attn | gaussian_0p10 | arousal | eeg_oracle_arch_A5_stem_attn | 96 | 2.102658 | 0.089745 | 0.658782 | 0.000000 | 0.662750 | 0.772365 | 0.062998 | 2.102658 | 0.578398 | 0.250656 | 2.163662 |


## All pooled/main metrics

| arch_config | augmentation_config | target | model | n | rmse | lift_vs_stimulus_rmse | balanced_accuracy | lift_vs_stimulus_balanced_accuracy | macro_f1 | auroc | lift_vs_stimulus_auroc | dev_rmse | dev_pearson | pred_dev_std | true_dev_std |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A0_current | gaussian_0p10 | arousal | eeg_oracle_arch_A0_current | 96 | 1.948237 | 0.244166 | 0.711944 | 0.053162 | 0.718750 | 0.822014 | 0.112646 | 1.948237 | 0.549976 | 0.758836 | 2.163662 |
| A0_current | gaussian_0p10 | arousal | stimulus_only | 96 | 2.192403 | 0.000000 | 0.658782 | 0.000000 | 0.662750 | 0.709368 | 0.000000 | 2.192403 |  | 0.000000 | 2.163662 |
| A5_stem_attn | gaussian_0p10 | arousal | eeg_oracle_arch_A5_stem_attn | 96 | 2.102658 | 0.089745 | 0.658782 | 0.000000 | 0.662750 | 0.772365 | 0.062998 | 2.102658 | 0.578398 | 0.250656 | 2.163662 |
| A5_stem_attn | gaussian_0p10 | arousal | stimulus_only | 96 | 2.192403 | 0.000000 | 0.658782 | 0.000000 | 0.662750 | 0.709368 | 0.000000 | 2.192403 |  | 0.000000 | 2.163662 |
| A7_no_channel_mha | gaussian_0p10 | arousal | eeg_oracle_arch_A7_no_channel_mha | 96 | 1.921876 | 0.270527 | 0.718033 | 0.059251 | 0.722944 | 0.817330 | 0.107963 | 1.921876 | 0.528141 | 0.792185 | 2.163662 |
| A7_no_channel_mha | gaussian_0p10 | arousal | stimulus_only | 96 | 2.192403 | 0.000000 | 0.658782 | 0.000000 | 0.662750 | 0.709368 | 0.000000 | 2.192403 |  | 0.000000 | 2.163662 |


## Fold summary

| arch_config | test_subject | best_epoch | best_val_rmse_scaled | rmse | balanced_accuracy | auroc | dev_rmse | dev_pearson | pred_dev_std | true_dev_std | final_train_last_loss |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A0_current | 1 | 3 | 0.938342 | 1.825601 | 0.716667 | 0.804167 | 1.825601 | 0.225491 | 0.376747 | 1.873076 | 0.334463 |
| A0_current | 2 | 6 | 1.291136 | 2.490408 | 0.772727 | 0.854545 | 2.490408 | 0.159356 | 0.527844 | 1.582934 | 0.269611 |
| A0_current | 3 | 6 | 0.699342 | 1.360858 | 0.903226 | 0.967742 | 1.360858 | 0.099016 | 0.273043 | 1.353914 | 0.272133 |
| A7_no_channel_mha | 1 | 3 | 0.950203 | 1.848677 | 0.716667 | 0.791667 | 1.848677 | 0.205502 | 0.211246 | 1.873076 | 0.346316 |
| A7_no_channel_mha | 2 | 5 | 1.249149 | 2.409421 | 0.745455 | 0.859091 | 2.409421 | 0.103164 | 0.508097 | 1.582934 | 0.304323 |
| A7_no_channel_mha | 3 | 10 | 0.714196 | 1.363048 | 0.903226 | 1.000000 | 1.363048 | 0.274828 | 0.641766 | 1.353914 | 0.196244 |
| A5_stem_attn | 1 | 5 | 0.923983 | 1.797664 | 0.716667 | 0.808333 | 1.797664 | 0.410333 | 0.336387 | 1.873076 | 0.391890 |
| A5_stem_attn | 2 | 1 | 1.403497 | 2.707136 | 0.727273 | 0.881818 | 2.707136 | 0.427018 | 0.071337 | 1.582934 | 0.419671 |
| A5_stem_attn | 3 | 1 | 0.844940 | 1.644179 | 0.854839 | 0.967742 | 1.644179 | -0.287181 | 0.032825 | 1.353914 | 0.426561 |


## Interpretation

- Positive `lift_vs_stimulus_rmse` means the EEG residual model beats stimulus-only RMSE.
- `dev_pearson` measures whether predicted residuals track true subject-specific deviations.
- `pred_dev_std` must be read against `true_dev_std`; variance inflation alone is not success.
- Because oracle mode uses the test subject for checkpoint selection, this is an upper-bound diagnostic, not a clean result.
