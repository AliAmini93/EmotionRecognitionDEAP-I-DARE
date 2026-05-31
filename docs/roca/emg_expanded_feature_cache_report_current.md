# ROCA-I-DARE Expanded EMG Feature Cache Report

No model training was performed.

## Status

Status: **PASSED**

## Counts

| Item | Value |
|---|---:|
| selected_rows | 2016 |
| extracted_rows | 2016 |
| subjects | 63 |
| stimuli | 32 |
| feature_dim | 812 |
| cache_file_size_bytes | 6548096 |
| cache_file_size_human | 6.24 MB |

## Outputs

- feature_npy: `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE/.cache/roca_idare_emg_expanded_features.npy`
- feature_index_csv: `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE/.cache/roca_idare_emg_expanded_feature_index.csv`
- feature_columns_json: `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE/.cache/roca_idare_emg_expanded_feature_columns.json`
- report_md: `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE/docs/roca/emg_expanded_feature_cache_report_current.md`
- report_json: `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE/docs/roca/emg_expanded_feature_cache_report_current.json`

## Feature Groups

- raw STIM statistics per channel
- raw BSL statistics per channel
- STIM minus BSL mean statistics per channel
- absolute activation delta statistics
- BSL-z-scored STIM statistics
- rectified/smoothed envelope features
- burst features using BSL-derived threshold
- 1-second temporal-bin features
- frequency-domain bandpower features
- channel interaction/asymmetry features

## Diagnostics

```json
{
  "feature_nan_count": 0,
  "feature_inf_count": 0,
  "feature_abs_max": 1.946719911464141e+16,
  "feature_mean_abs": 25470846976.0,
  "elapsed_sec": 34.405320302117616
}
```

## Feature Stats Preview

| Feature | Mean | Std | Min | Max |
|---|---:|---:|---:|---:|
| ch1_stim_raw_mean | -0.000164 | 0.016592 | -0.081652 | 0.105324 |
| ch1_stim_raw_std | 10.562294 | 6.870764 | 0.000000 | 82.846962 |
| ch1_stim_raw_var | 158.769453 | 358.182086 | 0.000000 | 6863.619141 |
| ch1_stim_raw_log_var | 4.431628 | 1.465563 | -27.563946 | 8.833990 |
| ch1_stim_raw_rms | 10.562308 | 6.870763 | 0.000000 | 82.846962 |
| ch1_stim_raw_mav | 7.429187 | 4.605652 | 0.000000 | 51.736195 |
| ch1_stim_raw_iemg | 74291.871544 | 46056.524735 | 0.002116 | 517361.937500 |
| ch1_stim_raw_min | -72.642592 | 49.497583 | -562.469482 | -0.000001 |
| ch1_stim_raw_max | 61.700125 | 55.647724 | 0.000001 | 636.579834 |
| ch1_stim_raw_ptp | 134.342717 | 102.149030 | 0.000002 | 1199.049316 |
| ch1_stim_raw_median | 0.044508 | 0.519200 | -4.806933 | 2.993773 |
| ch1_stim_raw_mad | 5.440128 | 3.164395 | 0.000000 | 31.643772 |
| ch1_stim_raw_q10 | -11.118615 | 7.327568 | -92.674553 | -0.000000 |
| ch1_stim_raw_q25 | -5.343565 | 3.238462 | -29.856678 | -0.000000 |
| ch1_stim_raw_q50 | 0.044508 | 0.519200 | -4.806933 | 2.993773 |
| ch1_stim_raw_q75 | 5.554947 | 3.156115 | 0.000000 | 33.976536 |
| ch1_stim_raw_q90 | 11.480524 | 7.326566 | 0.000000 | 92.282486 |
| ch1_stim_raw_q95 | 15.966007 | 10.938401 | 0.000000 | 127.178619 |
| ch1_stim_raw_q99 | 27.614020 | 21.074995 | 0.000001 | 297.382751 |
| ch1_stim_raw_iqr | 10.898512 | 6.358320 | 0.000000 | 63.527920 |
| ch1_stim_raw_abs_median | 5.460960 | 3.201663 | 0.000000 | 31.564732 |
| ch1_stim_raw_abs_q75 | 9.887997 | 6.249661 | 0.000000 | 78.190872 |
| ch1_stim_raw_abs_q90 | 15.813447 | 10.888619 | 0.000000 | 133.014709 |
| ch1_stim_raw_abs_q95 | 20.930034 | 14.962483 | 0.000001 | 191.750473 |
| ch1_stim_raw_abs_q99 | 36.200680 | 24.591940 | 0.000001 | 344.807770 |
| ch1_stim_raw_waveform_length | 27778.759021 | 20043.439435 | 0.000081 | 223977.718750 |
| ch1_stim_raw_zero_crossings | 1224.775794 | 187.205423 | 118.000000 | 2237.000000 |
| ch1_stim_raw_slope_sign_changes | 2283.858631 | 202.921791 | 222.000000 | 3443.000000 |
| ch1_stim_raw_skewness | -0.567644 | 0.644037 | -4.055357 | 2.311577 |
| ch1_stim_raw_kurtosis_excess | 6.468726 | 6.883544 | -0.182761 | 100.502007 |
| ch1_bsl_raw_mean | 0.000711 | 0.018239 | -0.280695 | 0.141647 |
| ch1_bsl_raw_std | 20.937168 | 439.150235 | 0.000000 | 19731.800781 |
| ch1_bsl_raw_var | 193291.296848 | 8669224.805924 | 0.000000 | 389343968.000000 |
| ch1_bsl_raw_log_var | 4.586809 | 1.239291 | -27.549549 | 19.779974 |
| ch1_bsl_raw_rms | 20.937180 | 439.150235 | 0.000000 | 19731.800781 |
| ch1_bsl_raw_mav | 9.538563 | 76.273086 | 0.000000 | 3428.256592 |
| ch1_bsl_raw_iemg | 95385.628717 | 762730.911083 | 0.002393 | 34282568.000000 |
| ch1_bsl_raw_min | -246.829703 | 7651.241763 | -343694.593750 | -0.000001 |
| ch1_bsl_raw_max | 156.981895 | 3885.586615 | 0.000001 | 174554.078125 |
| ch1_bsl_raw_ptp | 403.811605 | 11536.679805 | 0.000002 | 518248.687500 |

## Issues

- None.
