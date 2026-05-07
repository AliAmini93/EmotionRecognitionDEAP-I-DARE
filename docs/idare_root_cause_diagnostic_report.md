# I-DARE Root-Cause Diagnostic Report

## Status

Read-only root-cause diagnostic report complete; pending human review.

No new training was run.

Generated UTC: `2026-05-07T15:37:05.215064+00:00`

## Source Validation

| Source | Rows | Runs | Tasks | Policies | Recipes | Subjects |
|---|---:|---:|---|---|---|---:|
| `label_eeg_mainline` | 23060 | 72 | arousal, valence | discard_midpoint, midpoint_as_high, midpoint_as_low | balanced_sampler_ce, ce_class_weighted | 63 |
| `label_emg_mainline` | 23060 | 72 | arousal, valence | discard_midpoint, midpoint_as_high, midpoint_as_low | balanced_sampler_ce, ce_class_weighted | 63 |
| `broader_eeg_stim_bsl_only` | 8064 | 24 | arousal, valence | midpoint_as_high | balanced_sampler_ce, ce_class_weighted | 63 |
| `broader_eeg_bsl_stats` | 8064 | 24 | arousal, valence | midpoint_as_high | balanced_sampler_ce, ce_class_weighted | 63 |
| `broader_emg_feature_only` | 8064 | 24 | arousal, valence | midpoint_as_high | balanced_sampler_ce, ce_class_weighted | 63 |
| `broader_emg_bsl_stats` | 8064 | 24 | arousal, valence | midpoint_as_high | balanced_sampler_ce, ce_class_weighted | 63 |

## Diagnostic Summary

| Diagnostic | Value |
|---|---:|
| Aggregate rows analyzed | 40 |
| Subject-summary rows | 2520 |
| Fold/calibration rows | 240 |
| Error-overlap rows | 44 |
| Weak aggregate ratio, macro-F1 <= 0.53 | 95.00% |
| Strong aggregate ratio, macro-F1 >= 0.58 | 0.00% |
| Mean fold macro-F1 range | 0.0757 |
| Max fold macro-F1 range | 0.1617 |
| Mean threshold macro-F1 gain | 0.0252 |
| Max threshold macro-F1 gain | 0.1534 |
| Mean ECE-10 | 0.1704 |
| Subjects weak in at least 8 diagnostic rows | 59/63 |
| Mean EEG/EMG error-overlap Jaccard | 0.2188 |
| Mean absolute BSL-stats representation delta | 0.0099 |

## Root-Cause Ranking

| Rank | Candidate cause | Score | Confidence | Main support |
| --- | --- | --- | --- | --- |
| 1 | subject/fold generalization issue | 1.0000 | medium-high | mean fold macro-F1 range = 0.0757; max fold macro-F1 range = 0.1617; subjects weak in at least 8 diagnostic rows = 59/63 |
| 2 | representation weakness | 0.9725 | medium | aggregate groups at or below macro-F1 0.53 = 95.00%; aggregate groups at or above macro-F1 0.58 = 0.00%; mean absolute BSL-stats representation delta = 0.0099 |
| 3 | model/pipeline learning issue | 0.8733 | low-medium | Read-only outputs cannot prove pipeline failure.; weak aggregate ratio = 95.00%; strong aggregate ratio = 0.00% |
| 4 | calibration/threshold issue | 0.7248 | medium-high | mean threshold macro-F1 gain = 0.0252; max threshold macro-F1 gain = 0.1534; mean ECE-10 = 0.1704 |
| 5 | label/task definition issue | 0.6044 | medium | mixed best policies across modality/task = True; mean best-policy macro-F1 range by modality/task = 0.0168; best policies: EEG arousal=midpoint_as_high (0.5335); EEG valence=discard_midpoint (0.5179); EMG arousal=discard_midpoint (0.5276); EMG valence=midpoint_as_high (0.5161) |

## Label-Policy Sensitivity

| Modality | Task | Best policy | Best recipe | Best macro F1 | Best bal acc | Policy macro-F1 range |
| --- | --- | --- | --- | --- | --- | --- |
| EEG | arousal | midpoint_as_high | ce_class_weighted | 0.5335 | 0.5370 | 0.0180 |
| EEG | valence | discard_midpoint | balanced_sampler_ce | 0.5179 | 0.5213 | 0.0268 |
| EMG | arousal | discard_midpoint | ce_class_weighted | 0.5276 | 0.5318 | 0.0113 |
| EMG | valence | midpoint_as_high | ce_class_weighted | 0.5161 | 0.5203 | 0.0112 |

## Representation Delta Snapshot

Positive delta means the BSL-stats representation beat the corresponding baseline.

| Modality | Task | Policy | Recipe | Delta macro F1 | Delta bal acc |
| --- | --- | --- | --- | --- | --- |
| EEG | arousal | midpoint_as_high | ce_class_weighted | 0.0078 | 0.0112 |
| EEG | valence | midpoint_as_high | ce_class_weighted | -0.0117 | -0.0139 |
| EEG | arousal | midpoint_as_high | balanced_sampler_ce | 0.0179 | 0.0259 |
| EEG | valence | midpoint_as_high | balanced_sampler_ce | 0.0139 | 0.0143 |
| EMG | arousal | midpoint_as_high | ce_class_weighted | -0.0175 | -0.0178 |
| EMG | valence | midpoint_as_high | ce_class_weighted | -0.0024 | -0.0029 |
| EMG | arousal | midpoint_as_high | balanced_sampler_ce | -0.0007 | -0.0013 |
| EMG | valence | midpoint_as_high | balanced_sampler_ce | 0.0071 | 0.0074 |

## Repeated Weak Subjects

| Subject | Weak rows | Worst macro F1 | Mean macro F1 | Worst bal acc |
| --- | --- | --- | --- | --- |
| 3 | 29 | 0.1099 | 0.3427 | 0.2903 |
| 11 | 29 | 0.2222 | 0.3648 | 0.2762 |
| 14 | 28 | 0.1579 | 0.3464 | 0.2167 |
| 41 | 26 | 0.0303 | 0.3301 | 0.0156 |
| 7 | 26 | 0.2000 | 0.3572 | 0.1250 |
| 58 | 26 | 0.2805 | 0.3946 | 0.3268 |
| 28 | 25 | 0.2118 | 0.3605 | 0.2853 |
| 13 | 25 | 0.2195 | 0.3819 | 0.1500 |
| 19 | 25 | 0.2227 | 0.3377 | 0.3164 |
| 42 | 25 | 0.2805 | 0.3750 | 0.2897 |

## Weak Fold Hotspots

| Source | Modality | Task | Policy | Fold | Weak recipe rows | Worst macro F1 | Mean macro F1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| broader_eeg_bsl_stats | EEG | valence | midpoint_as_high | 2 | 2 | 0.4214 | 0.4332 |
| label_emg_mainline | EMG | valence | discard_midpoint | 1 | 2 | 0.4620 | 0.4650 |
| label_eeg_mainline | EEG | valence | midpoint_as_low | 5 | 2 | 0.4656 | 0.4673 |
| label_eeg_mainline | EEG | valence | midpoint_as_high | 5 | 1 | 0.4038 | 0.4038 |
| broader_emg_feature_only | EMG | valence | midpoint_as_high | 6 | 1 | 0.4092 | 0.4092 |
| label_emg_mainline | EMG | valence | midpoint_as_high | 6 | 1 | 0.4092 | 0.4092 |
| broader_eeg_bsl_stats | EEG | valence | midpoint_as_high | 5 | 1 | 0.4240 | 0.4240 |
| label_eeg_mainline | EEG | valence | midpoint_as_low | 6 | 1 | 0.4388 | 0.4388 |
| label_eeg_mainline | EEG | arousal | discard_midpoint | 3 | 1 | 0.4412 | 0.4412 |
| label_eeg_mainline | EEG | valence | midpoint_as_low | 4 | 1 | 0.4520 | 0.4520 |

## Error-Overlap Snapshot

| Pair | Type | Task | Policy | Recipe | N aligned | Left err | Right err | Both err | Error Jaccard |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| label_policy_mainline:EEG_vs_EMG | modality_overlap | arousal | midpoint_as_high | ce_class_weighted | 2 | 0.5000 | 0.5000 | 0.5000 | 1.0000 |
| broader_mainline:EEG_vs_EMG | modality_overlap | arousal | midpoint_as_high | ce_class_weighted | 2 | 0.5000 | 0.5000 | 0.5000 | 1.0000 |
| label_policy_mainline:EEG_vs_EMG | modality_overlap | arousal | midpoint_as_low | ce_class_weighted | 2 | 1.0000 | 0.5000 | 0.5000 | 0.5000 |
| label_policy_mainline:EEG_vs_EMG | modality_overlap | arousal | midpoint_as_high | balanced_sampler_ce | 2 | 1.0000 | 0.5000 | 0.5000 | 0.5000 |
| broader_EMG:baseline_vs_BSL-stats | representation_overlap | arousal | midpoint_as_high | balanced_sampler_ce | 2 | 0.5000 | 1.0000 | 0.5000 | 0.5000 |
| label_policy_mainline:EEG_vs_EMG | modality_overlap | arousal | midpoint_as_low | balanced_sampler_ce | 2 | 0.5000 | 1.0000 | 0.5000 | 0.5000 |
| label_emg_mainline:valence_vs_arousal | task_overlap | valence_vs_arousal | midpoint_as_high | balanced_sampler_ce | 2016 | 0.4901 | 0.4841 | 0.2584 | 0.3611 |
| broader_emg_feature_only:valence_vs_arousal | task_overlap | valence_vs_arousal | midpoint_as_high | balanced_sampler_ce | 2016 | 0.4901 | 0.4841 | 0.2584 | 0.3611 |
| broader_emg_feature_only:valence_vs_arousal | task_overlap | valence_vs_arousal | midpoint_as_high | ce_class_weighted | 2016 | 0.4782 | 0.4792 | 0.2485 | 0.3506 |
| label_emg_mainline:valence_vs_arousal | task_overlap | valence_vs_arousal | midpoint_as_high | ce_class_weighted | 2016 | 0.4782 | 0.4792 | 0.2485 | 0.3506 |

## Interpretation

The read-only evidence does not support another blind training sweep.

The strongest current explanation is a combination of subject/fold generalization difficulty, calibration/threshold weakness, and label/task sensitivity. Representation weakness is also plausible because BSL-stats does not produce a consistent large gain. A model/pipeline learning issue cannot be proven from read-only outputs, but it also cannot be ruled out.

## Recommended Next Objective

`diagnostic_sanity_tests_objective`

Rationale:

- Read-only evidence points to subject/fold, label, calibration, and representation issues, but it cannot conclusively rule out model/pipeline learning failure.
- Before proposing fixes, run diagnostic-only sanity tests: micro-overfit, shuffled-label negative control, within-subject contrast, and a simple classical baseline.
- This is not a performance-training objective; it is the fastest way to localize whether the pipeline can learn signal at all.

## Not Authorized From This Report

- new performance training without a reviewed follow-up objective
- EEG+EMG fusion
- final LOSO / final paper claim
- final global label-policy lock
- architecture ablation
- data augmentation
- SupCon / VREx / domain generalization

## Output Files

- `docs/idare_root_cause_diagnostic_report.md`
- `docs/idare_root_cause_diagnostic_report.json`
- `docs/idare_root_cause_subject_summary.csv`
- `docs/idare_root_cause_calibration_summary.csv`
- `docs/idare_root_cause_error_overlap_summary.csv`

## Next Allowed Step

Human review / closeout of this root-cause diagnostic report.

Only after review should we create the next objective.
