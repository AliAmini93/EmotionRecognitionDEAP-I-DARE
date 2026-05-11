# I-DARE Strict NTD Normalization Smoke Report

Status: `executed`

This is a smoke-level strict non-transductive normalization check, not a final LOSO claim.

## Scope

- I-DARE only
- EEG-only
- arousal-only
- within-subject pairwise affect-preference ranking
- fixed ridge readout
- strict non-transductive normalization only

## Inputs

- cache_npy: `.cache/idare_eeg_windows_32x640_float32_baseline_corrected.npy`
- cache_index: `.cache/idare_eeg_cache_index_baseline_corrected.csv`

## Aggregate

| Cell | Runs | Mean bal acc | Std bal acc | Mean macro F1 | Mean acc | Majority bal acc | Delta vs majority | One-class runs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| S0_current_no_additional_normalization | 6 | 0.5085 | 0.0128 | 0.5085 | 0.5085 | 0.5000 | 0.0085 | 0 |
| S1_train_fold_standard_scaler | 6 | 0.5088 | 0.0127 | 0.5088 | 0.5088 | 0.5000 | 0.0088 | 0 |
| S2_train_fold_robust_scaler | 6 | 0.5088 | 0.0127 | 0.5088 | 0.5088 | 0.5000 | 0.0088 | 0 |
| S3_train_fold_frozen_quantile_rank_mapper | 6 | 0.5142 | 0.0191 | 0.5142 | 0.5142 | 0.5000 | 0.0142 | 0 |

## Per-run Summary

| Run | Cell | Fold | Test subjects | Test pairs | Bal acc | Macro F1 | Acc | Delta vs majority | One-class |
|---:|---|---:|---|---:|---:|---:|---:|---:|---|
| 1 | S0_current_no_additional_normalization | 1 | 6 7 8 13 28 38 43 54 58 59 65 | 8662 | 0.5223 | 0.5223 | 0.5223 | 0.0223 | false |
| 2 | S0_current_no_additional_normalization | 2 | 2 5 11 17 26 31 34 44 46 49 63 | 9076 | 0.5163 | 0.5163 | 0.5163 | 0.0163 | false |
| 3 | S0_current_no_additional_normalization | 3 | 9 10 20 35 39 45 47 48 52 57 62 | 9416 | 0.5017 | 0.5017 | 0.5017 | 0.0017 | false |
| 4 | S0_current_no_additional_normalization | 4 | 1 3 19 25 36 40 42 53 55 61 | 8338 | 0.5035 | 0.5035 | 0.5035 | 0.0035 | false |
| 5 | S0_current_no_additional_normalization | 5 | 14 23 24 27 29 30 37 56 60 64 | 8454 | 0.4862 | 0.4862 | 0.4862 | -0.0138 | false |
| 6 | S0_current_no_additional_normalization | 6 | 12 15 16 18 21 22 32 33 41 50 | 8246 | 0.5210 | 0.5210 | 0.5210 | 0.0210 | false |
| 7 | S1_train_fold_standard_scaler | 1 | 6 7 8 13 28 38 43 54 58 59 65 | 8662 | 0.5241 | 0.5241 | 0.5241 | 0.0241 | false |
| 8 | S1_train_fold_standard_scaler | 2 | 2 5 11 17 26 31 34 44 46 49 63 | 9076 | 0.5156 | 0.5156 | 0.5156 | 0.0156 | false |
| 9 | S1_train_fold_standard_scaler | 3 | 9 10 20 35 39 45 47 48 52 57 62 | 9416 | 0.5023 | 0.5023 | 0.5023 | 0.0023 | false |
| 10 | S1_train_fold_standard_scaler | 4 | 1 3 19 25 36 40 42 53 55 61 | 8338 | 0.5020 | 0.5020 | 0.5020 | 0.0020 | false |
| 11 | S1_train_fold_standard_scaler | 5 | 14 23 24 27 29 30 37 56 60 64 | 8454 | 0.4876 | 0.4876 | 0.4876 | -0.0124 | false |
| 12 | S1_train_fold_standard_scaler | 6 | 12 15 16 18 21 22 32 33 41 50 | 8246 | 0.5210 | 0.5210 | 0.5210 | 0.0210 | false |
| 13 | S2_train_fold_robust_scaler | 1 | 6 7 8 13 28 38 43 54 58 59 65 | 8662 | 0.5241 | 0.5241 | 0.5241 | 0.0241 | false |
| 14 | S2_train_fold_robust_scaler | 2 | 2 5 11 17 26 31 34 44 46 49 63 | 9076 | 0.5156 | 0.5156 | 0.5156 | 0.0156 | false |
| 15 | S2_train_fold_robust_scaler | 3 | 9 10 20 35 39 45 47 48 52 57 62 | 9416 | 0.5025 | 0.5025 | 0.5025 | 0.0025 | false |
| 16 | S2_train_fold_robust_scaler | 4 | 1 3 19 25 36 40 42 53 55 61 | 8338 | 0.5020 | 0.5020 | 0.5020 | 0.0020 | false |
| 17 | S2_train_fold_robust_scaler | 5 | 14 23 24 27 29 30 37 56 60 64 | 8454 | 0.4873 | 0.4873 | 0.4873 | -0.0127 | false |
| 18 | S2_train_fold_robust_scaler | 6 | 12 15 16 18 21 22 32 33 41 50 | 8246 | 0.5210 | 0.5210 | 0.5210 | 0.0210 | false |
| 19 | S3_train_fold_frozen_quantile_rank_mapper | 1 | 6 7 8 13 28 38 43 54 58 59 65 | 8662 | 0.5290 | 0.5290 | 0.5290 | 0.0290 | false |
| 20 | S3_train_fold_frozen_quantile_rank_mapper | 2 | 2 5 11 17 26 31 34 44 46 49 63 | 9076 | 0.5353 | 0.5353 | 0.5353 | 0.0353 | false |
| 21 | S3_train_fold_frozen_quantile_rank_mapper | 3 | 9 10 20 35 39 45 47 48 52 57 62 | 9416 | 0.5202 | 0.5202 | 0.5202 | 0.0202 | false |
| 22 | S3_train_fold_frozen_quantile_rank_mapper | 4 | 1 3 19 25 36 40 42 53 55 61 | 8338 | 0.4929 | 0.4929 | 0.4929 | -0.0071 | false |
| 23 | S3_train_fold_frozen_quantile_rank_mapper | 5 | 14 23 24 27 29 30 37 56 60 64 | 8454 | 0.4836 | 0.4836 | 0.4836 | -0.0164 | false |
| 24 | S3_train_fold_frozen_quantile_rank_mapper | 6 | 12 15 16 18 21 22 32 33 41 50 | 8246 | 0.5244 | 0.5244 | 0.5244 | 0.0244 | false |

## Leakage Guard Summary

- Transform fitting uses training-subject rows only.
- Held-out/test-subject feature statistics are not fitted.
- No global scaler is used.
- No per-test-subject normalization is used.
- No threshold tuning is performed on test folds.
- Test arousal scores are used only as evaluation labels for held-out pairwise comparisons.

