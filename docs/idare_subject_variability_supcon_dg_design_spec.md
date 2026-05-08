# I-DARE Subject-variability SupCon/DG Design Spec

## Status

Design/spec complete, pending human review.

No training is authorized by this document.

Generated UTC: `2026-05-08T09:27:29.681220+00:00`

## Parent Objective

- Objective: `docs/idare_subject_variability_supcon_dg_design_objective.md`
- Parent review: `docs/idare_subject_variability_intervention_failure_analysis_review_status.md`

## Starting Diagnosis

The accepted diagnosis is:

- `subject_variability_diagnosis_still_supported_intervention_too_weak`

Interpretation:

- subject variability remains supported;
- the subject-relative + preprocessing intervention was too weak/incomplete;
- SupCon/DG is scientifically plausible only if staged, smoke-tested, and diagnosable.

## Project Scan Summary

Files scanned: `388`

Keyword hits: `39627`

Top matching files:

- `docs/deap_emg_feature_arousal_training_smoke_predictions.csv`: 5760 hits
- `docs/deap_emg_feature_training_smoke_predictions.csv`: 5760 hits
- `docs/idare_broader_eval_eeg_stim_bsl_only_primary_predictions.csv`: 4033 hits
- `docs/idare_broader_eval_eeg_bsl_stats_primary_predictions.csv`: 4032 hits
- `docs/idare_broader_eval_emg_bsl_stats_primary_predictions.csv`: 4032 hits
- `docs/idare_broader_eval_emg_feature_only_primary_predictions.csv`: 4032 hits
- `docs/idare_root_cause_subject_summary.csv`: 1260 hits
- `docs/idare_subject_difficulty_ranking.csv`: 756 hits
- `docs/idare_eeg_stim_bsl_only_arousal_standardized_smoke_predictions.csv`: 705 hits
- `docs/idare_eeg_stim_bsl_only_valence_standardized_smoke_predictions.csv`: 705 hits
- `docs/idare_valence_fold_bias_predictions_smoke.csv`: 705 hits
- `docs/idare_eeg_bsl_stats_arousal_ablation_smoke_predictions.csv`: 704 hits
- `docs/idare_eeg_bsl_stats_valence_ablation_smoke_predictions.csv`: 704 hits
- `docs/idare_emg_bsl_stats_arousal_ablation_smoke_predictions.csv`: 704 hits
- `docs/idare_emg_bsl_stats_valence_ablation_smoke_predictions.csv`: 704 hits

## Evidence Risk

- Keyword scan found at least some SupCon/DG/sampler-related evidence.

## Representative SupCon/DG/Sampler Notes Found

- `docs/idare_subject_variability_intervention_failure_analysis_report.json` L171 [domain_generalization, sampler, supcon]: L170: "intervention_adequacy": "The tested intervention was too weak/incomplete because preprocessing and CE-only training do not enforce subject-invariant affective representation.", | L171: "supcon_dg_justification": "Affective SupCon and VREx/DG are justified for design, but positive/negative pairs, sampler, environment definition, and leakage constraints must be specified before training.", | L172: "feature_engineering_position": "Generic feature engineering should not be the primary next step unless future analysis rejects subject variability as the blocker."
- `docs/project_status_current.json` L1325 [domain_generalization, sampler, supcon]: L1324: "intervention_adequacy": "The tested intervention was too weak/incomplete because preprocessing and CE-only training do not enforce subject-invariant affective representation.", | L1325: "supcon_dg_justification": "Affective SupCon and VREx/DG are justified for design, but positive/negative pairs, sampler, environment definition, and leakage constraints must be specified before training." | L1326: },
- `docs/handoff_after_bsl_stats_review.md` L57 [domain_generalization, supcon]: L56: - Data augmentation. | L57: - SupCon / VREx / domain generalization. | L58: 
- `docs/handoff_bundle_latest.md` L1986 [domain_generalization, supcon]: L1985: ```text | L1986: L_total = L_CE + lambda_contrastive * L_supcon + lambda_vrex * L_vrex | L1987: ```
- `docs/handoff_bundle_latest.md` L2062 [domain_generalization, supcon]: L2061: C3: CE + SupCon + hard-negative weighting | L2062: C4: CE + SupCon + VREx | L2063: ```
- `docs/handoff_bundle_latest.md` L2116 [domain_generalization, supcon]: L2115:  | L2116: VREx or GroupDRO can be tested after baseline and SupCon are stable. | L2117: 
- `docs/handoff_bundle_latest.md` L2148 [domain_generalization, supcon]: L2147: CE + SupCon | L2148: CE + SupCon + VREx | L2149: ```
- `docs/handoff_bundle_latest.md` L2401 [domain_generalization, supcon]: L2400: C3: CE + SupCon + hard-negative weighting | L2401: C4: CE + SupCon + VREx | L2402: ```
- `docs/idare_broader_standardized_single_modality_evaluation_execution_spec.json` L72 [domain_generalization, supcon]: L71: "data augmentation", | L72: "SupCon / VREx / domain generalization" | L73: ],
- `docs/idare_broader_standardized_single_modality_evaluation_execution_spec.md` L33 [domain_generalization, supcon]: L32: - Data augmentation. | L33: - SupCon / VREx / domain generalization. | L34: 
- `docs/idare_broader_standardized_single_modality_evaluation_objective.json` L68 [domain_generalization, supcon]: L67: "data augmentation", | L68: "SupCon / VREx / domain generalization" | L69: ],
- `docs/idare_broader_standardized_single_modality_evaluation_objective.md` L64 [domain_generalization, supcon]: L63: - data augmentation | L64: - SupCon / VREx / domain generalization | L65: 
- `docs/idare_broader_standardized_single_modality_evaluation_plan.json` L49 [domain_generalization, supcon]: L48: "data augmentation", | L49: "SupCon / VREx / domain generalization" | L50: ],
- `docs/idare_broader_standardized_single_modality_evaluation_plan.md` L132 [domain_generalization, supcon]: L131: - Data augmentation. | L132: - SupCon / VREx / domain generalization. | L133: 
- `docs/idare_broader_standardized_single_modality_evaluation_report.json` L1193 [domain_generalization, supcon]: L1192: "data augmentation", | L1193: "SupCon / VREx / domain generalization", | L1194: "optional robustness seed 13 without explicit objective"
- `docs/idare_broader_standardized_single_modality_evaluation_report.md` L75 [domain_generalization, supcon]: L74: - data augmentation | L75: - SupCon / VREx / domain generalization | L76: - optional robustness seed 13 without explicit objective
- `docs/idare_broader_standardized_single_modality_evaluation_review_status.json` L25 [domain_generalization, supcon]: L24: "data augmentation", | L25: "SupCon / VREx / domain generalization", | L26: "optional robustness seed 13 without explicit objective"
- `docs/idare_broader_standardized_single_modality_evaluation_review_status.md` L63 [domain_generalization, supcon]: L62: - data augmentation | L63: - SupCon / VREx / domain generalization | L64: - optional robustness seed 13 without explicit objective
- `docs/idare_calibration_and_subject_generalization_objective.json` L113 [domain_generalization, supcon]: L112: "data augmentation", | L113: "SupCon / VREx / domain generalization", | L114: "broad hyperparameter search",
- `docs/idare_calibration_and_subject_generalization_objective.md` L132 [domain_generalization, supcon]: L131: - data augmentation | L132: - SupCon / VREx / domain generalization | L133: - broad hyperparameter search
- `docs/idare_calibration_protocol_objective.json` L99 [domain_generalization, supcon]: L98: "data augmentation", | L99: "SupCon / VREx / domain generalization", | L100: "broad hyperparameter search",
- `docs/idare_calibration_protocol_objective.md` L111 [domain_generalization, supcon]: L110: - data augmentation | L111: - SupCon / VREx / domain generalization | L112: - broad hyperparameter search
- `docs/idare_calibration_protocol_report.json` L1385 [domain_generalization, supcon]: L1384: "data augmentation", | L1385: "SupCon / VREx / domain generalization", | L1386: "broad hyperparameter search",
- `docs/idare_calibration_protocol_report.md` L111 [domain_generalization, supcon]: L110: - data augmentation | L111: - SupCon / VREx / domain generalization | L112: - broad hyperparameter search
- `docs/idare_calibration_protocol_review_status.json` L53 [domain_generalization, supcon]: L52: "data augmentation", | L53: "SupCon / VREx / domain generalization", | L54: "broad hyperparameter search",
- `docs/idare_calibration_protocol_review_status.md` L40 [domain_generalization, supcon]: L39: - data augmentation | L40: - SupCon / VREx / domain generalization | L41: - broad hyperparameter search
- `docs/idare_calibration_subject_generalization_report.json` L1852 [domain_generalization, supcon]: L1851: "data augmentation", | L1852: "SupCon / VREx / domain generalization", | L1853: "broad hyperparameter search",
- `docs/idare_calibration_subject_generalization_report.md` L165 [domain_generalization, supcon]: L164: - data augmentation | L165: - SupCon / VREx / domain generalization | L166: - broad hyperparameter search
- `docs/idare_calibration_subject_generalization_review_status.json` L62 [domain_generalization, supcon]: L61: "data augmentation", | L62: "SupCon / VREx / domain generalization", | L63: "broad hyperparameter search",
- `docs/idare_calibration_subject_generalization_review_status.md` L38 [domain_generalization, supcon]: L37: - data augmentation | L38: - SupCon / VREx / domain generalization | L39: - broad hyperparameter search
- `docs/idare_diagnostic_sanity_tests_objective.json` L117 [domain_generalization, supcon]: L116: "data augmentation", | L117: "SupCon / VREx / domain generalization", | L118: "broad hyperparameter search",
- `docs/idare_diagnostic_sanity_tests_objective.md` L120 [domain_generalization, supcon]: L119: - data augmentation | L120: - SupCon / VREx / domain generalization | L121: - broad hyperparameter search
- `docs/idare_diagnostic_sanity_tests_report.json` L934 [domain_generalization, supcon]: L933: "data augmentation", | L934: "SupCon / VREx / domain generalization", | L935: "broad hyperparameter search",
- `docs/idare_diagnostic_sanity_tests_report.md` L87 [domain_generalization, supcon]: L86: - data augmentation | L87: - SupCon / VREx / domain generalization | L88: - broad hyperparameter search
- `docs/idare_diagnostic_sanity_tests_review_status.json` L48 [domain_generalization, supcon]: L47: "data augmentation", | L48: "SupCon / VREx / domain generalization", | L49: "broad hyperparameter search",

## Selected First-pass Direction

Primary design path:

- `CE_plus_SupCon`

Reason:

- SupCon directly targets cross-subject same-class representation alignment.
- This is closer to the accepted diagnosis than plain preprocessing or CE-only training.

Controlled probes:

- `CE_plus_VREx`
- `CE_plus_SupCon_plus_VREx`

Not selected:

- full Cartesian hyperparameter grid
- direct broad performance training
- fusion

## Pair and Sampler Rules

Detailed CSV:

- `docs/idare_subject_variability_supcon_dg_pair_sampler_spec.csv`

Core rules:

- positives: same task, same class, cross-subject preferred/required when feasible;
- negatives: same task, opposite class;
- hard negatives: log/audit first, do not weight aggressively in first pass;
- sampler: at least 4 subjects and both classes per contrastive batch;
- anchor exceptions must be logged;
- validation samples must never be used in train pairs.

## Hyperparameter Registry

Detailed CSV:

- `docs/idare_subject_variability_supcon_dg_hyperparameter_registry.csv`

Initial registry:

- `loss_family`: candidates `CE+SupCon | CE+VREx | CE+SupCon+VREx`, default `CE+SupCon`
- `supcon_temperature_tau`: candidates `0.07 | 0.10 | 0.20`, default `0.10`
- `lambda_supcon`: candidates `0.05 | 0.10 | 0.20 | 0.50`, default `0.10`
- `lambda_vrex`: candidates `0.01 | 0.05 | 0.10`, default `0.05 if VREx selected`
- `projection_dim`: candidates `32 | 64 | 128`, default `64`
- `warmup_epochs`: candidates `0 | 3 | 5`, default `3`
- `batch_policy`: candidates `largest_valid_subject_class_balanced_batch | fixed_64_if_valid | fixed_128_if_valid`, default `largest_valid_subject_class_balanced_batch`
- `optimizer_lr`: candidates `reuse_current_mainline | one_lower_lr_if_micro_overfit_unstable`, default `reuse_current_mainline`

Important rule:

- do not run the full Cartesian product.
- use smoke tests first, then a small staged matrix.

## Smoke Test Plan

Detailed CSV:

- `docs/idare_subject_variability_supcon_dg_smoke_test_plan.csv`

Required smoke gates:

1. `pair_sampler_integrity_smoke` — pass gate: all batches have both classes, >=4 subjects, positive_pair_coverage >= 0.95, anchors_without_positive <= 0.05
2. `leakage_guard_smoke` — pass gate: no validation labels/features used in train scaler, sampler, pair mining, environment risk computation
3. `supcon_micro_overfit_smoke` — pass gate: CE+SupCon loss decreases; train macro_f1 or proxy overfits; no NaN/collapse
4. `shuffled_label_negative_control` — pass gate: performance near chance; no suspicious leakage-driven gain
5. `one_fold_one_task_minimal_smoke` — pass gate: no collapse; valid pair coverage logs; embedding diagnostics produced

## Minimal First-pass Run Matrix Draft

Detailed CSV:

- `docs/idare_subject_variability_supcon_dg_first_pass_run_matrix.csv`

This matrix is a draft for a future training objective only.

It is not authorized until human review accepts this design spec.

## Diagnostic Metrics to Log

Mandatory logs:

- macro-F1
- balanced accuracy
- one-class prediction flag
- CE loss
- SupCon loss
- VREx loss when applicable
- environment risk variance
- same-class cross-subject embedding distance
- different-class cross-subject embedding distance
- positive-pair coverage
- anchors without positives
- batch subject count distribution

## Failure Interpretation Decision Tree

- If **pair_sampler_integrity_smoke fails**: The method has not been tested; sampler is invalid. Next: Fix sampler/pair rules before any training.
- If **leakage_guard_smoke fails**: Protocol is invalid. Next: Fix preprocessing/pair construction and rerun smoke only.
- If **micro_overfit fails**: Implementation/optimization bug likely. Next: Inspect loss implementation, projection head, tau, lambda, lr.
- If **shuffled-label negative control succeeds too well**: Leakage or invalid evaluation likely. Next: Stop; audit labels, folds, sampler and metrics.
- If **SupCon loss decreases but validation macro-F1 does not improve**: Embedding alignment alone may not solve task signal, labels, or classifier calibration. Next: Inspect embedding distance metrics and per-subject risk before adding VREx or changing labels.
- If **VREx reduces risk variance but macro-F1 does not improve**: Subject risk stability improved without enough class signal. Next: Consider CE/SupCon balance, task formulation, or representation—not claim success.
- If **Only EMG or only EEG improves**: Subject variability may be modality-dependent or representation-dependent. Next: Keep modality-specific conclusions; do not fuse.

## Pass/Fail Interpretation

A future SupCon/DG run should be considered scientifically useful only if it can answer:

1. Did sampler integrity hold?
2. Did leakage controls hold?
3. Did SupCon loss behave correctly?
4. Did embedding geometry move in the expected cross-subject direction?
5. Did task metrics improve beyond previous subject-relative/preprocessed first pass?
6. If not, did diagnostics identify whether the failure was task-label, sampler, optimization, or representation related?

## Recommendation

Next objective after human review:

- `supcon_dg_smoke_tests_objective_after_human_review`

That objective should implement smoke tests only.

Full SupCon/DG performance training should wait until smoke tests pass.

## Not Authorized

- training
- performance claim
- mainline change
- EEG+EMG fusion
- final LOSO claim
- broad hyperparameter search
