# ROCA-I-DARE EEG Gaussian Broader Fold Diagnostic

No model training was performed in this step. This report analyzes the 20-fold Gaussian broader smoke outputs.

## Decision verdict

- verdict: `borderline_candidate_for_full_loso`
- reason: Gaussian 0.10 is near-tied on RMSE but improves AUROC/BA and residual correlation.

## Config-level fold summary

| augmentation_config | folds | aggregate_rmse | aggregate_rmse_lift | aggregate_auroc | aggregate_auroc_lift | aggregate_balanced_accuracy | aggregate_ba_lift | aggregate_dev_pearson | positive_rmse_lift_folds | negative_rmse_lift_folds | positive_auroc_lift_folds | positive_ba_lift_folds | positive_dev_pearson_folds | negative_dev_pearson_folds | aggregate_pred_dev_std | mean_fold_dev_pearson |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gaussian_0p05 | 20 | 2.0450 | -0.0339 | 0.7496 | 0.0020 | 0.7038 | -0.0071 | 0.0164 | 9 | 11 | 4 | 0 | 10 | 10 | 0.3363 | 0.0466 |
| gaussian_0p10 | 20 | 2.0126 | -0.0016 | 0.7620 | 0.0144 | 0.7179 | 0.0071 | 0.1141 | 11 | 9 | 5 | 2 | 12 | 8 | 0.5166 | 0.0570 |
| gaussian_0p15 | 20 | 2.0309 | -0.0198 | 0.7585 | 0.0109 | 0.7127 | 0.0019 | 0.0547 | 9 | 11 | 3 | 2 | 13 | 7 | 0.3224 | 0.0490 |
| none | 20 | 2.0619 | -0.0508 | 0.7524 | 0.0048 | 0.7139 | 0.0031 | 0.0214 | 8 | 12 | 3 | 3 | 11 | 9 | 0.4272 | 0.0762 |


## Gaussian 0.10 vs no augmentation by fold

| test_subject | gaussian_0p10_rmse | none_rmse | delta_rmse_gauss10_minus_none | gaussian_0p10_lift_vs_stimulus_rmse | gauss10_better_rmse_than_stimulus | gauss10_better_rmse_than_none | gaussian_0p10_auroc | none_auroc | delta_auroc_gauss10_minus_none | gaussian_0p10_dev_pearson | none_dev_pearson | delta_dev_pearson_gauss10_minus_none | gauss10_positive_dev_pearson |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1.8642 | 1.8793 | -0.0151 | 0.0115 | True | True | 0.7750 | 0.7667 | 0.0083 | 0.1650 | 0.1153 | 0.0496 | True |
| 2 | 2.7857 | 2.9232 | -0.1375 | -0.0532 | False | True | 0.8727 | 0.8682 | 0.0045 | 0.4364 | 0.3580 | 0.0784 | True |
| 3 | 1.7408 | 1.8060 | -0.0653 | 0.1126 | True | True | 0.9677 | 0.9677 | 0.0000 | -0.1802 | -0.0113 | -0.1689 | False |
| 5 | 1.7463 | 2.0865 | -0.3402 | 0.0085 | True | True | 0.8730 | 0.8611 | 0.0119 | -0.0221 | -0.0599 | 0.0379 | False |
| 6 | 3.8246 | 3.7003 | 0.1243 | -0.0921 | False | False | 0.5000 | 0.4833 | 0.0167 | -0.2154 | -0.0473 | -0.1680 | False |
| 7 | 1.4578 | 1.5629 | -0.1050 | 0.1675 | True | True |  |  |  | 0.1290 | 0.1353 | -0.0063 | True |
| 8 | 2.0905 | 1.9751 | 0.1154 | -0.1717 | False | False | 0.8958 | 0.9062 | -0.0104 | 0.1248 | 0.0991 | 0.0258 | True |
| 9 | 1.9473 | 2.3655 | -0.4182 | 0.2231 | True | True | 0.7765 | 0.7647 | 0.0118 | 0.1372 | -0.0094 | 0.1466 | True |
| 10 | 1.8493 | 1.7274 | 0.1220 | -0.1320 | False | False | 0.8615 | 0.8701 | -0.0087 | -0.2702 | -0.0365 | -0.2337 | False |
| 11 | 2.0712 | 2.2895 | -0.2184 | -0.0446 | False | True | 0.5749 | 0.5789 | -0.0040 | -0.1809 | -0.0060 | -0.1749 | False |
| 12 | 1.3607 | 1.3411 | 0.0196 | -0.0305 | False | False | 0.9275 | 0.9130 | 0.0145 | 0.1536 | 0.1587 | -0.0051 | True |
| 13 | 2.3140 | 2.3114 | 0.0026 | 0.1033 | True | False |  |  |  | -0.0199 | -0.1429 | 0.1230 | False |
| 14 | 1.7439 | 1.9260 | -0.1821 | 0.0528 | True | True | 0.9000 | 0.8833 | 0.0167 | 0.0993 | 0.1284 | -0.0291 | True |
| 15 | 1.7296 | 1.8072 | -0.0776 | -0.0344 | False | True | 0.7773 | 0.7818 | -0.0045 | -0.0765 | -0.0185 | -0.0580 | False |
| 16 | 1.3865 | 1.5024 | -0.1159 | 0.0072 | True | True | 0.9372 | 0.9275 | 0.0097 | 0.0818 | 0.0740 | 0.0078 | True |
| 17 | 1.3505 | 1.3872 | -0.0367 | 0.0925 | True | True | 0.9714 | 0.9943 | -0.0229 | 0.3353 | 0.2752 | 0.0601 | True |
| 18 | 2.1685 | 2.1770 | -0.0085 | 0.0460 | True | True | 0.8164 | 0.8008 | 0.0156 | 0.0584 | 0.0023 | 0.0562 | True |
| 19 | 2.0183 | 1.7031 | 0.3152 | -0.1534 | False | False | 0.8929 | 0.8889 | 0.0040 | 0.3143 | 0.3774 | -0.0631 | True |
| 20 | 1.3517 | 1.5992 | -0.2475 | 0.2544 | True | True | 0.8532 | 0.8571 | -0.0040 | 0.1136 | -0.1353 | 0.2490 | True |
| 21 | 1.8668 | 1.7270 | 0.1399 | -0.2346 | False | False | 0.9903 | 1.0000 | -0.0097 | -0.0428 | 0.2668 | -0.3096 | False |


## Gaussian 0.10 best folds by RMSE lift

| test_subject | rmse | lift_vs_stimulus_rmse | auroc | lift_vs_stimulus_auroc | balanced_accuracy | lift_vs_stimulus_balanced_accuracy | dev_pearson | dev_sign_acc | pred_dev_std | true_dev_std |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20 | 1.3517 | 0.2544 | 0.8532 | -0.0278 | 0.7619 | -0.0159 | 0.1136 | 0.8438 | 0.5664 | 1.2401 |
| 9 | 1.9473 | 0.2231 | 0.7765 | 0.0078 | 0.6784 | 0.0098 | 0.1372 | 0.6562 | 0.5563 | 1.8982 |
| 7 | 1.4578 | 0.1675 |  |  | 0.6875 | 0.0000 | 0.1290 | 0.7812 | 0.1570 | 1.2462 |
| 3 | 1.7408 | 0.1126 | 0.9677 | 0.0000 | 0.8548 | 0.0000 | -0.1802 | 0.8125 | 0.0852 | 1.3539 |
| 13 | 2.3140 | 0.1033 |  |  | 0.6875 | 0.0000 | -0.0199 | 0.6562 | 0.3826 | 1.4089 |
| 17 | 1.3505 | 0.0925 | 0.9714 | -0.0114 | 0.9400 | 0.0000 | 0.3353 | 0.5938 | 0.5018 | 1.3129 |
| 14 | 1.7439 | 0.0528 | 0.9000 | -0.0333 | 0.8667 | 0.0000 | 0.0993 | 0.6250 | 0.1111 | 0.8494 |
| 18 | 2.1685 | 0.0460 | 0.8164 | 0.0000 | 0.8125 | 0.0000 | 0.0584 | 0.5625 | 0.0538 | 2.1201 |


## Gaussian 0.10 worst folds by RMSE lift

| test_subject | rmse | lift_vs_stimulus_rmse | auroc | lift_vs_stimulus_auroc | balanced_accuracy | lift_vs_stimulus_balanced_accuracy | dev_pearson | dev_sign_acc | pred_dev_std | true_dev_std |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 21 | 1.8668 | -0.2346 | 0.9903 | 0.0000 | 0.9348 | -0.0435 | -0.0428 | 0.5312 | 0.7539 | 1.6318 |
| 8 | 2.0905 | -0.1717 | 0.8958 | -0.0104 | 0.8958 | 0.1042 | 0.1248 | 0.4688 | 0.4036 | 1.6305 |
| 19 | 2.0183 | -0.1534 | 0.8929 | 0.0020 | 0.7143 | 0.0000 | 0.3143 | 0.3750 | 0.1493 | 1.4699 |
| 10 | 1.8493 | -0.1320 | 0.8615 | -0.0325 | 0.8615 | -0.0238 | -0.2702 | 0.4375 | 0.3331 | 1.7130 |
| 6 | 3.8246 | -0.0921 | 0.5000 | 0.0000 | 0.6667 | 0.0000 | -0.2154 | 0.3125 | 0.1317 | 1.7902 |
| 2 | 2.7857 | -0.0532 | 0.8727 | 0.0045 | 0.7273 | 0.0000 | 0.4364 | 0.3125 | 0.1221 | 1.5829 |
| 11 | 2.0712 | -0.0446 | 0.5749 | -0.0121 | 0.5607 | 0.0000 | -0.1809 | 0.3438 | 0.0780 | 1.9006 |
| 15 | 1.7296 | -0.0344 | 0.7773 | -0.0045 | 0.7091 | 0.0000 | -0.0765 | 0.3125 | 0.1266 | 1.6186 |


## Gaussian 0.10 best folds by dev_pearson

| test_subject | rmse | lift_vs_stimulus_rmse | auroc | lift_vs_stimulus_auroc | balanced_accuracy | lift_vs_stimulus_balanced_accuracy | dev_pearson | dev_sign_acc | pred_dev_std | true_dev_std |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 2.7857 | -0.0532 | 0.8727 | 0.0045 | 0.7273 | 0.0000 | 0.4364 | 0.3125 | 0.1221 | 1.5829 |
| 17 | 1.3505 | 0.0925 | 0.9714 | -0.0114 | 0.9400 | 0.0000 | 0.3353 | 0.5938 | 0.5018 | 1.3129 |
| 19 | 2.0183 | -0.1534 | 0.8929 | 0.0020 | 0.7143 | 0.0000 | 0.3143 | 0.3750 | 0.1493 | 1.4699 |
| 1 | 1.8642 | 0.0115 | 0.7750 | 0.0167 | 0.7167 | 0.0000 | 0.1650 | 0.5625 | 0.2979 | 1.8731 |
| 12 | 1.3607 | -0.0305 | 0.9275 | -0.0072 | 0.8237 | 0.0000 | 0.1536 | 0.5000 | 0.2844 | 1.2274 |
| 9 | 1.9473 | 0.2231 | 0.7765 | 0.0078 | 0.6784 | 0.0098 | 0.1372 | 0.6562 | 0.5563 | 1.8982 |
| 7 | 1.4578 | 0.1675 |  |  | 0.6875 | 0.0000 | 0.1290 | 0.7812 | 0.1570 | 1.2462 |
| 8 | 2.0905 | -0.1717 | 0.8958 | -0.0104 | 0.8958 | 0.1042 | 0.1248 | 0.4688 | 0.4036 | 1.6305 |


## Gaussian 0.10 worst folds by dev_pearson

| test_subject | rmse | lift_vs_stimulus_rmse | auroc | lift_vs_stimulus_auroc | balanced_accuracy | lift_vs_stimulus_balanced_accuracy | dev_pearson | dev_sign_acc | pred_dev_std | true_dev_std |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10 | 1.8493 | -0.1320 | 0.8615 | -0.0325 | 0.8615 | -0.0238 | -0.2702 | 0.4375 | 0.3331 | 1.7130 |
| 6 | 3.8246 | -0.0921 | 0.5000 | 0.0000 | 0.6667 | 0.0000 | -0.2154 | 0.3125 | 0.1317 | 1.7902 |
| 11 | 2.0712 | -0.0446 | 0.5749 | -0.0121 | 0.5607 | 0.0000 | -0.1809 | 0.3438 | 0.0780 | 1.9006 |
| 3 | 1.7408 | 0.1126 | 0.9677 | 0.0000 | 0.8548 | 0.0000 | -0.1802 | 0.8125 | 0.0852 | 1.3539 |
| 15 | 1.7296 | -0.0344 | 0.7773 | -0.0045 | 0.7091 | 0.0000 | -0.0765 | 0.3125 | 0.1266 | 1.6186 |
| 21 | 1.8668 | -0.2346 | 0.9903 | 0.0000 | 0.9348 | -0.0435 | -0.0428 | 0.5312 | 0.7539 | 1.6318 |
| 5 | 1.7463 | 0.0085 | 0.8730 | 0.0079 | 0.7421 | -0.0357 | -0.0221 | 0.5625 | 0.3606 | 1.5102 |
| 13 | 2.3140 | 0.1033 |  |  | 0.6875 | 0.0000 | -0.0199 | 0.6562 | 0.3826 | 1.4089 |


## Interpretation guide

- `aggregate_rmse_lift > 0` means the EEG model beats stimulus-only on pooled RMSE.
- `positive_rmse_lift_folds` counts subjects where EEG beats stimulus-only on RMSE.
- `gauss10_better_rmse_than_none` checks whether Gaussian 0.10 improves over no augmentation for the same subject.
- If Gaussian 0.10 is near-tied on RMSE but improves AUROC/BA/dev_pearson, it is a borderline but real candidate.
- Any full LOSO after this point should use Gaussian 0.10 as a locked candidate, not continue tuning noise levels on the same folds.
