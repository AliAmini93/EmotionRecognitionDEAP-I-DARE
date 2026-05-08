# I-DARE Label-Semantics Task Redesign Spec

## Status

Status: complete; pending human review; no training is authorized.

Created UTC: `2026-05-08T11:15:29+00:00`

## Selected Primary Formulation

Selected formulation: `subject_relative_ordinal_affect_regression_v1`

Scientific claim: Predict within-subject affect-rating order/percentile for held-out subjects, not global high/low affect by an absolute threshold.

This replaces the current global binary LOSO target as the next candidate task. It does not validate a final claim yet.

## Why This Formulation Was Selected

The accepted diagnosis says the current global binary LOSO task is not defensible for more model search. The previous interventions did not fail because pair sampling was invalid; they failed because the target semantics and representation transfer are jointly weak. A subject-relative ordinal/regression target is selected because it attacks both problems: it avoids global absolute thresholds and avoids collapsing continuous ratings into a brittle binary label.

Key evidence:

- `decision_report_diagnosis`: `current_global_binary_loso_task_not_defensible_for_more_model_search`

- `decision_report_decision`: `pause_current_global_binary_loso_training_and_prepare_task_redesign_spec`

- `failure_report_diagnosis`: `label_semantics_and_representation_transfer_joint_bottleneck`

- `best_pair_sampler_candidate_mean_macro_f1`: `0.5118600603082725`

- `best_pair_sampler_candidate_folds_under_050`: `7`

- `mean_label_entropy`: `0.9190643971472996`

- `high_subject_rating_shift`: `True`

- `objective_alignment_weak`: `True`

- `max_abs_loss_embedding_corr_with_macro_f1`: `0.3001215860428951`

## Locked Task Definition

| field | value | locked | rationale |
| --- | --- | --- | --- |
| selected_primary_formulation | subject_relative_ordinal_affect_regression_v1 | yes | Combines ordinal/regression preservation of rating magnitude with subject-relative semantics. |
| scientific_claim | Predict within-subject affect-rating order/percentile for held-out subjects, not global high/low affect by an absolute threshold. | yes | Avoids unsupported global binary LOSO claim. |
| raw_label_source | raw valence_score and arousal_score ratings from cache/index files | yes | Uses existing labels only; no new annotation or model-derived labels. |
| target_transform | per_subject_average_rank_percentile: rank(raw_rating within subject and task, ties averaged, mapped to [0,1] | yes | Removes between-subject scale offsets while preserving within-subject ordering. |
| secondary_target | per_subject_z_score_rating for audit only, not the primary target | yes | Useful to check scale sensitivity without changing primary target. |
| primary_tasks | valence and arousal evaluated separately | yes | Keeps task-specific interpretation. |
| primary_split | existing 6-fold subject-heldout protocol; no subject overlap between train and validation | yes | Preserves the most important leakage guardrail. |
| allowed_modalities_first_pass | EEG summary features and EMG signed_log1p features only, separately | yes | No fusion and no architecture jump before redesigned-task smoke review. |
| training_status | not authorized by this spec | yes | This document only defines the task; future training requires review and a new objective. |

## Metric Plan

| metric | role | definition | direction | pass_rule_for_future_minimal_training |
| --- | --- | --- | --- | --- |
| spearman_rho | primary | Spearman rank correlation between predicted continuous score and target rank percentile within each fold/task/modality. | higher_better | mean across folds must be positive and exceed mean-baseline/permutation controls by a pre-registered margin. |
| mae_rank_percentile | secondary | Mean absolute error on [0,1] rank-percentile target. | lower_better | must improve over train-mean predictor. |
| rmse_rank_percentile | secondary | Root mean squared error on [0,1] rank-percentile target. | lower_better | must improve over train-mean predictor. |
| top_bottom_q33_balanced_accuracy | audit_only | Evaluate predicted score as top-vs-bottom third after excluding middle third, with thresholds locked from target rank percentiles. | higher_better | used only as a secondary bridge to old binary results; cannot be sole success criterion. |
| per_subject_error_dispersion | fairness_stability_audit | Distribution of rank-percentile errors by held-out subject. | lower_dispersion_better | must report hard-subject concentration; no fold hiding. |
| permutation_control_spearman | negative_control | Same pipeline with train labels shuffled within fold. | near_zero_expected | must stay near zero; if not, leakage or metric bug suspected. |

## Protocol Matrix

| component | locked_rule | leakage_control | review_required |
| --- | --- | --- | --- |
| label_construction | For each subject and task, compute average rank of raw rating and convert to percentile in [0,1]. | Labels only; no feature or model input gets held-out label statistics. | yes |
| split | Use the existing 6 subject-heldout folds. | Validation subjects are completely held out from training. | yes |
| preprocessing | Feature scalers fit on train fold only; apply to held-out fold. | No validation statistics in scaler. | yes |
| baseline | Train-mean predictor and shuffled-label negative control must be reported. | Controls are generated within each fold. | yes |
| primary_model_family_if_later_authorized | Start with minimal ridge/linear regression or a single small MLP regression; no SupCon/DG first. | No tuning on validation beyond pre-registered run matrix. | yes |
| success_claim | Success means evidence for within-subject affect-order prediction, not global high/low classification. | Claim text must match target definition. | yes |

## Guardrails

| guardrail | rule | why | blocking |
| --- | --- | --- | --- |
| no_global_binary_threshold | Do not use raw rating >= midpoint as the primary label. | The accepted diagnosis says the current global binary LOSO task is not defensible for more model search. | yes |
| no_model_training_in_spec_step | This spec does not authorize training. | Task definition must be reviewed before implementation. | yes |
| no_direct_full_supcon_dg_training | direct full SupCon/DG training remains blocked. | SupCon/DG and pair-sampler ablations were not sufficient. | yes |
| no_broad_hyperparameter_search | broad hyperparameter search remains blocked. | Would obscure whether the task redesign fixed the root issue. | yes |
| heldout_subject_isolation | No subject overlap between train and validation folds; scalers fit train only. | Keeps LOSO leakage controls intact. | yes |
| target_transform_usage | Held-out labels may be transformed only to define evaluation targets; target statistics must not enter feature preprocessing, training inputs, sampler state, or model selection. | Allows subject-relative ground truth without leaking into the predictor. | yes |
| anti_cherry_picking | No fold/task/modality exclusion after seeing results; all exclusions must be declared before any training. | Avoids converting redesign into outcome selection. | yes |
| final_loso_claim_blocked | final LOSO claim remains blocked until redesigned-task results pass review. | This spec changes the scientific target. | yes |

## Future Minimal Run Matrix If Later Authorized

The future matrix is intentionally minimal and is not authorized by this spec. It exists only so the next objective can be reviewed without inventing runs later.

- Planned rows: `48`

- Methods: `mean_baseline_no_training`, `ridge_regression_summary_features`

- Modalities: `EEG`, `EMG`

- Tasks: `valence`, `arousal`

- Folds: existing 1..6 subject-heldout folds

## Stop / Archive Criteria

| condition | action | reason |
| --- | --- | --- |
| spec_rejected | stop_archive_current_global_binary_loso_branch | No defensible target was accepted. |
| smoke_tests_fail_label_construction_or_leakage | fix_spec_or_stop_archive | Cannot train on a target that fails construction/leakage sanity checks. |
| future_minimal_regression_not_above_controls | stop_or_reframe_as_negative_result | Would indicate even redesigned target has weak physiological signal under current features. |
| future_success_only_in_one_fold_or_one_subject_cluster | run failure analysis_before_any_claim | Avoids false positives from subject/fold idiosyncrasy. |
| request_to_resume_direct_full_supcon_dg_training | block_until_redesigned_task_review_and_smoke_tests_pass | Model-side search is not the accepted next scientific step. |

## Next Allowed Step

Human review / closeout, then create a redesigned-task smoke-test objective.


The smoke-test objective must validate label construction, fold leakage, metric computation, baseline controls, and target distribution before any training objective.


## Still Blocked

- direct full SupCon/DG training

- broad hyperparameter search

- EEG+EMG fusion

- final LOSO claim

- mainline change

- new training before redesigned-task smoke-test review
