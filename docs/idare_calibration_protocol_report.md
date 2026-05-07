# I-DARE Validation-only Calibration Protocol Report

## Status

Calibration protocol analysis complete; pending human review.

Generated UTC: `2026-05-07T15:57:23.340681+00:00`

This report is read-only and uses existing prediction outputs only.

No new model training was run.

## Protocol Summary

| Item | Value |
|---|---:|
| Prediction rows loaded | 78376 |
| Protocol groups | 12 |
| Positive validation-calibration gain groups | 11 |
| Material gain groups >= 0.01 | 2 |
| Negative gain groups | 1 |
| Pass-like groups | 4 |
| Threshold-unstable groups | 0 |
| Calibrated one-class groups | 0 |
| Mean calibrated macro-F1 gain | 0.0050 |
| Median calibrated macro-F1 gain | 0.0047 |
| Max calibrated macro-F1 gain | 0.0143 |
| Mean oracle gap | 0.0095 |
| Mean selected-threshold std | 0.0065 |
| Diagnosis | `calibration_not_sufficient_as_primary_fix` |
| Recommended next objective | `representation_label_task_redesign_objective` |

## Protocol Definition

For each modality/variant/task/policy/recipe group and target fold:

1. choose the threshold that maximizes macro-F1 on all **other** folds only;
2. apply that threshold to the target fold;
3. compute calibrated metrics on the target fold;
4. compute oracle fold threshold only as a diagnostic upper bound.

The target fold labels are not used to select the threshold applied to that same target fold.

## Top Validation-calibration Gains

| Source | Mod | Variant | Task | Policy | Recipe | Default F1 | Cal F1 | Gain | Oracle gain | Oracle gap | Th mean | Th std | Pass-like |
|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| nan | nan | nan | arousal | midpoint_as_low | ce_class_weighted | 0.5109 | 0.5252 | 0.0143 | 0.0169 | 0.0026 | 0.5500 | 0.0000 | True |
| nan | nan | nan | valence | midpoint_as_low | balanced_sampler_ce | 0.4887 | 0.4993 | 0.0106 | 0.0214 | 0.0108 | 0.5233 | 0.0149 | True |
| nan | nan | nan | valence | discard_midpoint | balanced_sampler_ce | 0.5096 | 0.5186 | 0.0090 | 0.0134 | 0.0045 | 0.4900 | 0.0000 | True |
| nan | nan | nan | arousal | midpoint_as_low | balanced_sampler_ce | 0.5191 | 0.5249 | 0.0058 | 0.0211 | 0.0153 | 0.5750 | 0.0112 | False |
| nan | nan | nan | valence | discard_midpoint | ce_class_weighted | 0.5040 | 0.5093 | 0.0053 | 0.0161 | 0.0108 | 0.5200 | 0.0000 | True |
| nan | nan | nan | arousal | discard_midpoint | balanced_sampler_ce | 0.5141 | 0.5190 | 0.0050 | 0.0216 | 0.0167 | 0.5567 | 0.0213 | False |
| nan | nan | nan | arousal | discard_midpoint | ce_class_weighted | 0.5167 | 0.5212 | 0.0045 | 0.0138 | 0.0093 | 0.5200 | 0.0100 | False |
| nan | nan | nan | arousal | midpoint_as_high | ce_class_weighted | 0.5203 | 0.5239 | 0.0037 | 0.0081 | 0.0045 | 0.5183 | 0.0037 | False |
| nan | nan | nan | valence | midpoint_as_high | balanced_sampler_ce | 0.5065 | 0.5099 | 0.0034 | 0.0101 | 0.0066 | 0.4767 | 0.0047 | False |
| nan | nan | nan | valence | midpoint_as_high | ce_class_weighted | 0.5143 | 0.5162 | 0.0019 | 0.0097 | 0.0077 | 0.4900 | 0.0000 | False |
| nan | nan | nan | arousal | midpoint_as_high | balanced_sampler_ce | 0.5180 | 0.5184 | 0.0004 | 0.0142 | 0.0139 | 0.5183 | 0.0090 | False |
| nan | nan | nan | valence | midpoint_as_low | ce_class_weighted | 0.4968 | 0.4927 | -0.0041 | 0.0076 | 0.0117 | 0.5017 | 0.0037 | False |

## Worst Validation-calibration Gains

| Source | Mod | Variant | Task | Policy | Recipe | Default F1 | Cal F1 | Gain | Oracle gap | Th std |
|---|---|---|---|---|---|---:|---:|---:|---:|---:|
| nan | nan | nan | valence | midpoint_as_low | ce_class_weighted | 0.4968 | 0.4927 | -0.0041 | 0.0117 | 0.0037 |
| nan | nan | nan | arousal | midpoint_as_high | balanced_sampler_ce | 0.5180 | 0.5184 | 0.0004 | 0.0139 | 0.0090 |
| nan | nan | nan | valence | midpoint_as_high | ce_class_weighted | 0.5143 | 0.5162 | 0.0019 | 0.0077 | 0.0000 |
| nan | nan | nan | valence | midpoint_as_high | balanced_sampler_ce | 0.5065 | 0.5099 | 0.0034 | 0.0066 | 0.0047 |
| nan | nan | nan | arousal | midpoint_as_high | ce_class_weighted | 0.5203 | 0.5239 | 0.0037 | 0.0045 | 0.0037 |
| nan | nan | nan | arousal | discard_midpoint | ce_class_weighted | 0.5167 | 0.5212 | 0.0045 | 0.0093 | 0.0100 |
| nan | nan | nan | arousal | discard_midpoint | balanced_sampler_ce | 0.5141 | 0.5190 | 0.0050 | 0.0167 | 0.0213 |
| nan | nan | nan | valence | discard_midpoint | ce_class_weighted | 0.5040 | 0.5093 | 0.0053 | 0.0108 | 0.0000 |
| nan | nan | nan | arousal | midpoint_as_low | balanced_sampler_ce | 0.5191 | 0.5249 | 0.0058 | 0.0153 | 0.0112 |
| nan | nan | nan | valence | discard_midpoint | balanced_sampler_ce | 0.5096 | 0.5186 | 0.0090 | 0.0045 | 0.0000 |
| nan | nan | nan | valence | midpoint_as_low | balanced_sampler_ce | 0.4887 | 0.4993 | 0.0106 | 0.0108 | 0.0149 |
| nan | nan | nan | arousal | midpoint_as_low | ce_class_weighted | 0.5109 | 0.5252 | 0.0143 | 0.0026 | 0.0000 |

## Threshold Instability Examples

| Source | Mod | Variant | Task | Policy | Recipe | Th mean | Th std | Th min | Th max | Range |
|---|---|---|---|---|---|---:|---:|---:|---:|---:|
| nan | nan | nan | arousal | discard_midpoint | balanced_sampler_ce | 0.5567 | 0.0213 | 0.5300 | 0.5900 | 0.0600 |
| nan | nan | nan | valence | midpoint_as_low | balanced_sampler_ce | 0.5233 | 0.0149 | 0.5100 | 0.5500 | 0.0400 |
| nan | nan | nan | arousal | midpoint_as_low | balanced_sampler_ce | 0.5750 | 0.0112 | 0.5500 | 0.5800 | 0.0300 |
| nan | nan | nan | arousal | discard_midpoint | ce_class_weighted | 0.5200 | 0.0100 | 0.5100 | 0.5300 | 0.0200 |
| nan | nan | nan | arousal | midpoint_as_high | balanced_sampler_ce | 0.5183 | 0.0090 | 0.5100 | 0.5300 | 0.0200 |
| nan | nan | nan | valence | midpoint_as_high | balanced_sampler_ce | 0.4767 | 0.0047 | 0.4700 | 0.4800 | 0.0100 |
| nan | nan | nan | arousal | midpoint_as_high | ce_class_weighted | 0.5183 | 0.0037 | 0.5100 | 0.5200 | 0.0100 |
| nan | nan | nan | valence | midpoint_as_low | ce_class_weighted | 0.5017 | 0.0037 | 0.5000 | 0.5100 | 0.0100 |
| nan | nan | nan | arousal | midpoint_as_low | ce_class_weighted | 0.5500 | 0.0000 | 0.5500 | 0.5500 | 0.0000 |
| nan | nan | nan | valence | discard_midpoint | balanced_sampler_ce | 0.4900 | 0.0000 | 0.4900 | 0.4900 | 0.0000 |
| nan | nan | nan | valence | midpoint_as_high | ce_class_weighted | 0.4900 | 0.0000 | 0.4900 | 0.4900 | 0.0000 |
| nan | nan | nan | valence | discard_midpoint | ce_class_weighted | 0.5200 | 0.0000 | 0.5200 | 0.5200 | 0.0000 |

## Recommendation

- Validation-only calibration gains are too small or inconsistent.
- Calibration alone should not be treated as the main fix.
- A representation/label-task redesign objective is more appropriate after review.

Recommended next objective: `representation_label_task_redesign_objective`

## Not Authorized

- EEG+EMG fusion
- final LOSO / final paper claim
- final global label-policy lock
- new model training
- architecture ablation for improvement
- data augmentation
- SupCon / VREx / domain generalization
- broad hyperparameter search
- mainline change

## Next Allowed Step

Human review / closeout of this calibration protocol report.

Do not start fusion, architecture changes, augmentation, domain generalization, or final claims from this report alone.
