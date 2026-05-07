# I-DARE Calibration and Subject-Generalization Report

## Status

Calibration and subject-generalization diagnostic complete; pending human review.

Generated UTC: `2026-05-07T15:51:29.295866+00:00`

This report is read-only and uses existing prediction outputs only.

No new performance training was run.

## Diagnostic Summary

| Item | Value |
|---|---|
| Prediction rows loaded | 78376 |
| Threshold summary rows | 280 |
| Subject difficulty rows | 756 |
| Cross-modality overlap rows | 378 |
| Overall macro-F1 gain mean | 0.0093 |
| Overall macro-F1 gain max | 0.0252 |
| Fold macro-F1 gain mean | 0.0279 |
| Mean threshold std | 0.1045 |
| Threshold instability count | 14 |
| Large threshold-gain count | 15 |
| Hard subject count | 163 |
| Cross-modality both-hard count | 20 |
| Cross-modality mean common-failure score | 0.2328 |
| Diagnosis | `calibration_instability_supported` |
| Recommended next objective | `calibration_protocol_objective` |

## Top Threshold Gains

| Source | Modality | Variant | Task | Policy | Recipe | Default F1 | Best F1 | F1 gain | Best th | One-class |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| label_policy_ablation | EMG | mainline_label_policy_ablation | arousal | discard_midpoint | balanced_sampler_ce | 0.5099 | 0.5351 | 0.0252 | 0.5600 | False |
| label_policy_ablation | EMG | mainline_label_policy_ablation | arousal | midpoint_as_low | ce_class_weighted | 0.5163 | 0.5390 | 0.0227 | 0.5500 | False |
| label_policy_ablation | EMG | mainline_label_policy_ablation | arousal | midpoint_as_low | balanced_sampler_ce | 0.5132 | 0.5307 | 0.0175 | 0.5547 | False |
| broader_eval_primary | EMG | feature_only | arousal | midpoint_as_high | ce_class_weighted | 0.5178 | 0.5335 | 0.0157 | 0.5160 | False |
| label_policy_ablation | EMG | mainline_label_policy_ablation | arousal | midpoint_as_high | ce_class_weighted | 0.5178 | 0.5335 | 0.0157 | 0.5160 | False |
| label_policy_ablation | EEG | mainline_label_policy_ablation | arousal | midpoint_as_high | balanced_sampler_ce | 0.5151 | 0.5307 | 0.0156 | 0.7000 | False |
| label_policy_ablation | EMG | mainline_label_policy_ablation | valence | midpoint_as_low | balanced_sampler_ce | 0.4863 | 0.5017 | 0.0154 | 0.5100 | False |
| label_policy_ablation | EMG | mainline_label_policy_ablation | valence | discard_midpoint | balanced_sampler_ce | 0.5013 | 0.5166 | 0.0153 | 0.4900 | False |
| label_policy_ablation | EEG | mainline_label_policy_ablation | valence | discard_midpoint | ce_class_weighted | 0.5016 | 0.5162 | 0.0146 | 0.5500 | False |
| label_policy_ablation | EMG | mainline_label_policy_ablation | arousal | discard_midpoint | ce_class_weighted | 0.5276 | 0.5412 | 0.0136 | 0.5100 | False |
| broader_eval_primary | EMG | bsl_stats | valence | midpoint_as_high | balanced_sampler_ce | 0.5136 | 0.5272 | 0.0136 | 0.4811 | False |
| label_policy_ablation | EEG | mainline_label_policy_ablation | valence | midpoint_as_high | balanced_sampler_ce | 0.4997 | 0.5107 | 0.0110 | 0.3340 | False |
| label_policy_ablation | EEG | mainline_label_policy_ablation | arousal | discard_midpoint | ce_class_weighted | 0.5058 | 0.5167 | 0.0109 | 0.7079 | False |
| label_policy_ablation | EEG | mainline_label_policy_ablation | arousal | midpoint_as_low | balanced_sampler_ce | 0.5218 | 0.5319 | 0.0101 | 0.7097 | False |
| label_policy_ablation | EEG | mainline_label_policy_ablation | arousal | midpoint_as_low | ce_class_weighted | 0.5052 | 0.5153 | 0.0101 | 0.7500 | False |
| broader_eval_primary | EMG | bsl_stats | valence | midpoint_as_high | ce_class_weighted | 0.5136 | 0.5236 | 0.0100 | 0.4800 | False |

## Fold Threshold Instability

| Source | Modality | Variant | Task | Policy | Recipe | Folds | Mean gain | Th std | Th min | Th max | Instability |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| broader_eval_primary | EEG | stim_bsl_only | arousal | midpoint_as_high | balanced_sampler_ce | 6 | 0.0288 | 0.2946 | 0.1300 | 0.9300 | True |
| label_policy_ablation | EEG | mainline_label_policy_ablation | arousal | discard_midpoint | ce_class_weighted | 6 | 0.0522 | 0.2910 | 0.2100 | 0.9500 | True |
| label_policy_ablation | EEG | mainline_label_policy_ablation | valence | midpoint_as_high | balanced_sampler_ce | 6 | 0.0391 | 0.2482 | 0.0800 | 0.7400 | True |
| label_policy_ablation | EEG | mainline_label_policy_ablation | valence | discard_midpoint | balanced_sampler_ce | 6 | 0.0332 | 0.2465 | 0.1866 | 0.8500 | True |
| label_policy_ablation | EEG | mainline_label_policy_ablation | arousal | midpoint_as_low | balanced_sampler_ce | 6 | 0.0187 | 0.2349 | 0.1400 | 0.8800 | True |
| label_policy_ablation | EEG | mainline_label_policy_ablation | valence | midpoint_as_low | ce_class_weighted | 6 | 0.0431 | 0.2310 | 0.1307 | 0.7000 | True |
| label_policy_ablation | EEG | mainline_label_policy_ablation | arousal | midpoint_as_high | balanced_sampler_ce | 6 | 0.0288 | 0.2309 | 0.1700 | 0.9409 | True |
| label_policy_ablation | EEG | mainline_label_policy_ablation | arousal | midpoint_as_low | ce_class_weighted | 6 | 0.0295 | 0.2065 | 0.3200 | 0.8900 | True |
| broader_eval_primary | EEG | stim_bsl_only | valence | midpoint_as_high | balanced_sampler_ce | 6 | 0.0258 | 0.2042 | 0.2500 | 0.8103 | True |
| broader_eval_primary | EEG | bsl_stats | arousal | midpoint_as_high | ce_class_weighted | 6 | 0.0437 | 0.1865 | 0.2800 | 0.7447 | True |
| label_policy_ablation | EEG | mainline_label_policy_ablation | valence | midpoint_as_high | ce_class_weighted | 6 | 0.0228 | 0.1786 | 0.3700 | 0.8567 | True |
| label_policy_ablation | EEG | mainline_label_policy_ablation | arousal | discard_midpoint | balanced_sampler_ce | 6 | 0.0175 | 0.1746 | 0.2700 | 0.7200 | True |
| label_policy_ablation | EEG | mainline_label_policy_ablation | valence | midpoint_as_low | balanced_sampler_ce | 6 | 0.0270 | 0.1676 | 0.4500 | 0.9300 | True |
| broader_eval_primary | EEG | bsl_stats | valence | midpoint_as_high | balanced_sampler_ce | 6 | 0.0399 | 0.1523 | 0.2856 | 0.7600 | True |
| broader_eval_primary | EEG | bsl_stats | valence | midpoint_as_high | ce_class_weighted | 6 | 0.0444 | 0.1490 | 0.2900 | 0.7300 | False |
| label_policy_ablation | EEG | mainline_label_policy_ablation | valence | discard_midpoint | ce_class_weighted | 6 | 0.0363 | 0.1461 | 0.2800 | 0.7700 | False |

## Hard Subject Ranking

| Subject | Modality | Task | Policy | N | Errors | Error rate | Sources | Recipes | Hard |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3 | EMG | arousal | discard_midpoint | 54 | 46 | 0.8519 | 1 | 2 | True |
| 65 | EMG | arousal | discard_midpoint | 60 | 46 | 0.7667 | 1 | 2 | True |
| 37 | EMG | valence | midpoint_as_low | 64 | 48 | 0.7500 | 1 | 2 | True |
| 3 | EMG | arousal | midpoint_as_high | 192 | 139 | 0.7240 | 3 | 2 | True |
| 21 | EEG | valence | midpoint_as_low | 64 | 46 | 0.7188 | 1 | 2 | True |
| 33 | EMG | valence | midpoint_as_low | 64 | 46 | 0.7188 | 1 | 2 | True |
| 11 | EMG | arousal | discard_midpoint | 48 | 34 | 0.7083 | 1 | 2 | True |
| 11 | EMG | arousal | midpoint_as_low | 64 | 45 | 0.7031 | 1 | 2 | True |
| 65 | EMG | arousal | midpoint_as_low | 64 | 45 | 0.7031 | 1 | 2 | True |
| 10 | EMG | valence | discard_midpoint | 52 | 35 | 0.6731 | 1 | 2 | True |
| 12 | EEG | arousal | discard_midpoint | 52 | 35 | 0.6731 | 1 | 2 | True |
| 22 | EMG | arousal | discard_midpoint | 58 | 39 | 0.6724 | 1 | 2 | True |
| 65 | EMG | arousal | midpoint_as_high | 192 | 129 | 0.6719 | 3 | 2 | True |
| 28 | EMG | arousal | midpoint_as_low | 64 | 43 | 0.6719 | 1 | 2 | True |
| 43 | EEG | arousal | midpoint_as_low | 64 | 43 | 0.6719 | 1 | 2 | True |
| 14 | EMG | arousal | midpoint_as_high | 192 | 128 | 0.6667 | 3 | 2 | True |
| 28 | EMG | arousal | midpoint_as_high | 192 | 128 | 0.6667 | 3 | 2 | True |
| 41 | EMG | arousal | midpoint_as_high | 192 | 128 | 0.6667 | 3 | 2 | True |
| 55 | EMG | valence | midpoint_as_high | 192 | 128 | 0.6667 | 3 | 2 | True |
| 57 | EMG | valence | discard_midpoint | 54 | 36 | 0.6667 | 1 | 2 | True |

## Cross-modality Error Overlap

| Subject | Task | Policy | EEG err | EMG err | Common score | Both hard | EEG-specific | EMG-specific |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 11 | arousal | discard_midpoint | 0.5833 | 0.7083 | 0.4132 | True | False | False |
| 14 | arousal | midpoint_as_low | 0.6250 | 0.6562 | 0.4102 | True | False | False |
| 28 | arousal | midpoint_as_low | 0.5938 | 0.6719 | 0.3989 | True | False | False |
| 37 | valence | midpoint_as_low | 0.5312 | 0.7500 | 0.3984 | False | False | False |
| 11 | valence | discard_midpoint | 0.6429 | 0.6071 | 0.3903 | True | False | False |
| 19 | arousal | midpoint_as_high | 0.6094 | 0.6250 | 0.3809 | True | False | False |
| 5 | arousal | discard_midpoint | 0.6167 | 0.6167 | 0.3803 | True | False | False |
| 65 | arousal | midpoint_as_high | 0.5625 | 0.6719 | 0.3779 | True | False | False |
| 33 | valence | midpoint_as_low | 0.5156 | 0.7188 | 0.3706 | False | False | False |
| 14 | arousal | midpoint_as_high | 0.5521 | 0.6667 | 0.3681 | True | False | False |
| 65 | arousal | midpoint_as_low | 0.5156 | 0.7031 | 0.3625 | False | False | False |
| 22 | arousal | discard_midpoint | 0.5345 | 0.6724 | 0.3594 | False | False | False |
| 35 | valence | midpoint_as_low | 0.5938 | 0.5938 | 0.3525 | True | False | False |
| 28 | arousal | discard_midpoint | 0.5938 | 0.5938 | 0.3525 | True | False | False |
| 49 | valence | midpoint_as_low | 0.5781 | 0.6094 | 0.3523 | True | False | False |
| 19 | valence | midpoint_as_high | 0.5260 | 0.6615 | 0.3480 | False | False | False |
| 43 | arousal | midpoint_as_low | 0.6719 | 0.5156 | 0.3464 | False | False | False |
| 12 | valence | discard_midpoint | 0.5227 | 0.6591 | 0.3445 | False | False | False |
| 1 | arousal | midpoint_as_low | 0.6406 | 0.5312 | 0.3403 | False | False | False |
| 34 | valence | discard_midpoint | 0.5833 | 0.5833 | 0.3403 | True | False | False |

## Recipe / Policy Stability Map

| Source | Modality | Variant | Task | Policy | Recipe | Default F1 mean | Default F1 std | Gain mean | Stable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| label_policy_ablation | EEG | mainline_label_policy_ablation | arousal | midpoint_as_high | ce_class_weighted | 0.5313 | 0.0173 | 0.0121 | True |
| broader_eval_primary | EEG | bsl_stats | arousal | midpoint_as_high | balanced_sampler_ce | 0.5302 | 0.0128 | 0.0134 | True |
| label_policy_ablation | EMG | mainline_label_policy_ablation | arousal | discard_midpoint | ce_class_weighted | 0.5253 | 0.0146 | 0.0333 | False |
| label_policy_ablation | EEG | mainline_label_policy_ablation | arousal | midpoint_as_low | balanced_sampler_ce | 0.5160 | 0.0321 | 0.0187 | False |
| broader_eval_primary | EMG | feature_only | arousal | midpoint_as_high | ce_class_weighted | 0.5159 | 0.0160 | 0.0241 | False |
| label_policy_ablation | EMG | mainline_label_policy_ablation | arousal | midpoint_as_high | ce_class_weighted | 0.5159 | 0.0160 | 0.0241 | False |
| broader_eval_primary | EMG | feature_only | valence | midpoint_as_high | ce_class_weighted | 0.5140 | 0.0306 | 0.0187 | False |
| label_policy_ablation | EMG | mainline_label_policy_ablation | valence | midpoint_as_high | ce_class_weighted | 0.5140 | 0.0306 | 0.0187 | False |
| broader_eval_primary | EMG | feature_only | arousal | midpoint_as_high | balanced_sampler_ce | 0.5131 | 0.0192 | 0.0230 | False |
| label_policy_ablation | EMG | mainline_label_policy_ablation | arousal | midpoint_as_high | balanced_sampler_ce | 0.5131 | 0.0192 | 0.0230 | False |
| label_policy_ablation | EMG | mainline_label_policy_ablation | arousal | midpoint_as_low | balanced_sampler_ce | 0.5124 | 0.0340 | 0.0366 | False |
| label_policy_ablation | EMG | mainline_label_policy_ablation | arousal | midpoint_as_low | ce_class_weighted | 0.5121 | 0.0326 | 0.0369 | False |
| broader_eval_primary | EMG | bsl_stats | valence | midpoint_as_high | ce_class_weighted | 0.5116 | 0.0250 | 0.0219 | False |
| broader_eval_primary | EMG | bsl_stats | arousal | midpoint_as_high | balanced_sampler_ce | 0.5103 | 0.0215 | 0.0135 | False |
| broader_eval_primary | EEG | stim_bsl_only | arousal | midpoint_as_high | ce_class_weighted | 0.5103 | 0.0326 | 0.0226 | False |
| broader_eval_primary | EMG | bsl_stats | valence | midpoint_as_high | balanced_sampler_ce | 0.5094 | 0.0248 | 0.0242 | False |

## Recommendation

Recommended next objective:

`calibration_protocol_objective`

Reason:

- Threshold sweeps show repeated macro-F1 gains.
- Best thresholds vary substantially across folds/conditions, so calibration needs a protocol before model changes.

## Not Authorized

- EEG+EMG fusion
- final LOSO / final paper claim
- final global label-policy lock
- new performance training
- architecture ablation for improvement
- data augmentation
- SupCon / VREx / domain generalization
- broad hyperparameter search
- mainline change

## Output Files

- `docs/idare_calibration_subject_generalization_report.md`
- `docs/idare_calibration_subject_generalization_report.json`
- `docs/idare_calibration_subject_threshold_summary.csv`
- `docs/idare_subject_difficulty_ranking.csv`
- `docs/idare_cross_modality_error_overlap.csv`

## Next Allowed Step

Human review / closeout of this calibration and subject-generalization report.

Only after review should the next objective be created.
