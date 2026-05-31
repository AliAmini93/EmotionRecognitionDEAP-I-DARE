# I-DARE Root-Cause Triage Subject-Domain Shift Report

Status: `completed`

## Summary

- Existing synthesis says affective signal exists within subject while cross-subject representations collapse.
- W1D and related Wave 1 evidence point to subject-dominated geometry as a core mechanism.
- Subject/domain-generalization work is plausible later, but should remain deferred until label and protocol root causes are reconciled.

## Classification Pressure

- **A**: moderate if subject-domain shift is actually label tendency by subject
- **B**: moderate if held-out-subject protocol is stricter than source evidence supports
- **C**: moderate if feature geometry is the dominant failure and label/protocol checks pass
- **D**: strong mechanistic support, but execution remains deferred
- **E**: reviewable if subject-domain shift is irreducible under current formulation

## Evidence Snippets

- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_subject_variability_supcon_dg_smoke_tests_review_status.json:39` — "reviewed_report": "docs/idare_subject_variability_supcon_dg_smoke_tests_report.md",
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_subject_variability_supcon_dg_smoke_tests_review_status.json:40` — "reviewed_report_json": "docs/idare_subject_variability_supcon_dg_smoke_tests_report.json",
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_subject_relative_preprocessed_minimal_training_review_status.json:4` — "reviewed_document": "docs/idare_subject_relative_preprocessed_minimal_training_report.md",
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_subject_relative_preprocessed_minimal_training_review_status.json:5` — "reviewed_json": "docs/idare_subject_relative_preprocessed_minimal_training_report.json",
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_subject_relative_preprocessed_minimal_training_review_status.json:10` — "preprocessed_subject_relative_result": "preprocessed_subject_relative_first_pass_not_sufficient",
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_subject_relative_preprocessed_minimal_training_review_status.json:12` — "selected_next_step": "subject_variability_intervention_failure_analysis_objective",
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_subject_relative_preprocessed_minimal_training_review_status.json:13` — "decision": "Do not jump directly to generic feature engineering, SupCon, VREx, domain generalization, fusion, architecture changes, or broad hyperparameter search. First analyze why the subject-relative + preprocessing intervention failed.
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_subject_relative_preprocessed_minimal_training_review_status.json:16` — "why_review_needed": "If the project diagnosis is subject variability, a failed intervention must be audited before selecting the next fix.",
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_subject_relative_preprocessed_minimal_training_review_status.json:17` — "current_result": "The subject-relative preprocessed first pass remained close to chance/mixed and was not sufficient to justify a mainline change.",
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_subject_relative_preprocessed_minimal_training_review_status.json:18` — "preprocessing_result": "The preprocessing diagnostic justified a small test, but preprocessing alone did not establish a strong label-discriminative or subject-invariant representation."
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_subject_relative_preprocessed_minimal_training_review_status.json:31` — "allowed_next_step": "docs/idare_subject_variability_intervention_failure_analysis_objective.md"
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_subject_relative_preprocessed_minimal_training_review_status.json:34` — "preprocessed_training_report": "docs/idare_subject_relative_preprocessed_minimal_training_report.md",
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_subject_relative_preprocessed_minimal_training_review_status.json:35` — "preprocessing_diagnostic_report": "docs/idare_subject_relative_representation_preprocessing_report.md",
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_calibration_subject_generalization_report.md:1` — # I-DARE Calibration and Subject-Generalization Report
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_calibration_subject_generalization_report.md:5` — Calibration and subject-generalization diagnostic complete; pending human review.
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_calibration_subject_generalization_report.md:19` — | Subject difficulty rows | 756 |
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_calibration_subject_generalization_report.md:27` — | Hard subject count | 163 |
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_calibration_subject_generalization_report.md:75` — ## Hard Subject Ranking

## Notes

- No DG execution was run.
- No model-capacity probe was run.
- No new feature extraction or preprocessing was performed.

