# I-DARE Diagnostic Sanity Tests Report

## Status

Diagnostic sanity tests complete; pending human review.

Generated UTC: `2026-05-07T15:45:10.643998+00:00`

Device: `cuda`

Policy: `midpoint_as_high`

This report is diagnostic-only. It does not make a final performance claim.

## Diagnostic Summary

| Item | Value |
|---|---|
| Micro-overfit all passed | True |
| Shuffled-label negative control all passed | True |
| Mean within-subject minus subject-heldout macro-F1 | 0.0206 |
| Max within-subject minus subject-heldout macro-F1 | 0.0834 |
| Subject-generalization contrast hits | 0 |
| Best classical macro-F1 | 0.5434 |
| Mean classical macro-F1 | 0.4787 |
| Diagnosis | `mixed_issue_unresolved` |
| Recommended next objective | `calibration_and_subject_generalization_objective` |

## Micro-overfit Subset Test

| Modality | Task | N | Macro F1 | Bal acc | Acc | Passed | Interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EEG | valence | 96.0000 | 1.0000 | 1.0000 | 1.0000 | True | pass: model/data path can memorize a small subset |
| EEG | arousal | 96.0000 | 1.0000 | 1.0000 | 1.0000 | True | pass: model/data path can memorize a small subset |
| EMG | valence | 96.0000 | 1.0000 | 1.0000 | 1.0000 | True | pass: model/data path can memorize a small subset |
| EMG | arousal | 96.0000 | 1.0000 | 1.0000 | 1.0000 | True | pass: model/data path can memorize a small subset |

## Shuffled-label Negative Control

| Modality | Task | N | Macro F1 | Bal acc | Acc | Passed | Interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EEG | valence | 352.0000 | 0.4337 | 0.4409 | 0.4659 | True | pass: shuffled-label validation remains near chance |
| EEG | arousal | 352.0000 | 0.5459 | 0.5460 | 0.5540 | True | pass: shuffled-label validation remains near chance |
| EMG | valence | 352.0000 | 0.5586 | 0.5642 | 0.5597 | True | pass: shuffled-label validation remains near chance |
| EMG | arousal | 352.0000 | 0.5340 | 0.5476 | 0.5341 | True | pass: shuffled-label validation remains near chance |

## Within-subject vs Subject-heldout Contrast

| Modality | Task | Within macro F1 | Heldout macro F1 | Delta | Interpretation |
| --- | --- | --- | --- | --- | --- |
| EEG | valence | 0.4934 | 0.4841 | 0.0093 | subject/domain generalization not isolated by this contrast |
| EEG | arousal | 0.5455 | 0.4621 | 0.0834 | subject/domain generalization not isolated by this contrast |
| EMG | valence | 0.4689 | 0.5163 | -0.0474 | subject/domain generalization not isolated by this contrast |
| EMG | arousal | 0.5625 | 0.5254 | 0.0371 | subject/domain generalization not isolated by this contrast |

## Simple Classical Baseline

| Modality | Task | Model | N | Macro F1 | Bal acc | Acc | Passed | Interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EEG | valence | ridge_classifier_summary_features | 352.0000 | 0.4889 | 0.5172 | 0.5597 | False | classical baseline also near chance |
| EEG | valence | nearest_centroid_summary_features | 352.0000 | 0.4786 | 0.4898 | 0.5199 | False | centroid baseline also near chance |
| EEG | arousal | ridge_classifier_summary_features | 352.0000 | 0.5434 | 0.5444 | 0.5625 | True | classical baseline finds some signal |
| EEG | arousal | nearest_centroid_summary_features | 352.0000 | 0.4943 | 0.5028 | 0.4943 | False | centroid baseline also near chance |
| EMG | valence | ridge_classifier_features | 352.0000 | 0.3785 | 0.4975 | 0.5653 | False | classical baseline also near chance |
| EMG | valence | nearest_centroid_features | 352.0000 | 0.4792 | 0.4823 | 0.5028 | False | centroid baseline also near chance |
| EMG | arousal | ridge_classifier_features | 352.0000 | 0.4436 | 0.5198 | 0.5795 | False | classical baseline also near chance |
| EMG | arousal | nearest_centroid_features | 352.0000 | 0.5234 | 0.5245 | 0.5284 | False | centroid baseline also near chance |

## Recommendation

Recommended next objective:

`calibration_and_subject_generalization_objective`

Reason:

- Core sanity checks passed, but results remain weak/mixed.
- Next diagnostic work should focus on calibration and subject-generalization without fusion or architecture escalation.

## Not Authorized

- EEG+EMG fusion
- final LOSO / final paper claim
- final global label-policy lock
- architecture ablation for improvement
- data augmentation
- SupCon / VREx / domain generalization
- broad hyperparameter search
- mainline change

## Output Files

- `docs/idare_diagnostic_sanity_tests_report.md`
- `docs/idare_diagnostic_sanity_tests_report.json`
- `docs/idare_diagnostic_sanity_tests_summary.csv`

## Next Allowed Step

Human review / closeout of this diagnostic sanity report.

Only after review should the next objective be created.
