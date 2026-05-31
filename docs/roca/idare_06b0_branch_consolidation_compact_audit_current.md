# I-DARE 06b0 Branch Consolidation Compact Audit

- generated_at: `2026-05-31T10:43:10+00:00`
- current_branch: `roca-idare-killtest`
- target_branch: `origin/roca-idare-killtest`
- old_remote_branches_audited: `13`

## Decision table
| decision | why | action |
| --- | --- | --- |
| DO_NOT_MERGE_OLD_BRANCHES_WHOLESALE | old wave/postwave branches contain useful evidence but also outdated objectives, old protocols, and non-current claims | cherry-pick only missing evidence docs; keep 06a7/06a7b as current root-cause conclusion |
| KEEP_ROCA_IDARE_KILLTEST_AS_CURRENT_TRUTH_BRANCH | it contains locked-gate reruns: 06a5b augmentation no-go, 06a6 neural anchor no-go, 06a7/06a7b final conclusion | merge this branch to main when ready, then archive/delete old experimental branches after confirming evidence is preserved |
| DATA_AUGMENTATION_TRACK_IS_HISTORICAL_EVIDENCE_ONLY | old augmentation helped in older/non-current setups, but gaussian10 failed the current locked LOSO residual gate | cite as prior attempt; do not use it as proof that augmentation solves current LOSO crisis |

## Branch summary
| branch | last_commit_date | last_commit_hash | commits_ahead_of_roca | files_changed_vs_roca | recommended_action | reason |
| --- | --- | --- | --- | --- | --- | --- |
| origin/idare/postwave1/data-augmentation-track | 2026-05-12T18:56:36+03:00 | f9728de | 29 | 96 | KEEP_EVIDENCE_CHERRY_PICK_ONLY | contains prior augmentation evidence; do not merge whole branch because current locked-gate tests supersede it |
| origin/idare/control-tower | 2026-05-12T17:35:27+03:00 | e6b021c | 24 | 65 | KEEP_EVIDENCE_CHERRY_PICK_ONLY | contains prior augmentation evidence; do not merge whole branch because current locked-gate tests supersede it |
| origin/idare/postwave1/idare-prior-best-cell-confirmation | 2026-05-12T14:51:48+03:00 | 2b72f40 | 23 | 84 | KEEP_EVIDENCE_CHERRY_PICK_ONLY | contains prior-best confirmation reports; useful for history, not enough to override current ROCA conclusion |
| origin/idare/postwave1/label-task-protocol-reconciliation | 2026-05-12T13:14:55+03:00 | 19188db | 18 | 60 | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY | contains strict non-transductive normalization / DG design notes |
| origin/idare/postwave1/root-cause-triage | 2026-05-12T12:50:23+03:00 | 86b239a | 17 | 58 | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY | contains strict non-transductive normalization / DG design notes |
| origin/idare/postwave1/representation-redesign-confirmation | 2026-05-11T21:18:11+03:00 | 79438a0 | 12 | 40 | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY | contains strict non-transductive normalization / DG design notes |
| origin/idare/postwave1/representation-redesign-smoke | 2026-05-11T20:41:35+03:00 | 2fd7f18 | 12 | 43 | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY | contains strict non-transductive normalization / DG design notes |
| origin/idare/postwave1/strict-ntd-norm-smoke | 2026-05-11T18:55:38+03:00 | 908dd55 | 7 | 25 | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY | contains strict non-transductive normalization / DG design notes |
| origin/idare/wave1/eeg-input-definition | 2026-05-11T17:40:32+03:00 | 195c148 | 2 | 11 | REVIEW_BEFORE_ACTION | branch category not recognized automatically |
| origin/idare/wave1/emg-baseline-ablation | 2026-05-11T16:34:25+03:00 | 5a008c8 | 1 | 11 | REVIEW_BEFORE_ACTION | branch category not recognized automatically |
| origin/idare/wave1/eeg-subject-normalization | 2026-05-11T16:26:24+03:00 | 91f6573 | 1 | 9 | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY | contains EEG subject-normalization audit/design evidence |
| origin/idare/wave1/feature-discriminability | 2026-05-11T15:40:14+03:00 | f35d1a2 | 2 | 7 | REVIEW_BEFORE_ACTION | branch category not recognized automatically |
| origin | 2026-05-11T14:43:05+03:00 | d7e93ad | 0 | 0 | REVIEW_BEFORE_ACTION | branch category not recognized automatically |

## Top relevant files by branch
| branch | rank | file | recommended_action |
| --- | --- | --- | --- |
| origin/idare/postwave1/data-augmentation-track | 1 | docs/idare_cross_subject_failure_root_cause_triage_objective.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/postwave1/data-augmentation-track | 2 | docs/idare_data_augmentation_best_policy_report.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/postwave1/data-augmentation-track | 3 | docs/idare_label_task_protocol_target_policy_decision_matrix.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/postwave1/data-augmentation-track | 4 | docs/idare_label_task_protocol_target_policy_decision_package.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/postwave1/data-augmentation-track | 5 | docs/idare_post_strict_ntd_smoke_synthesis_and_pivot_decision.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/postwave1/data-augmentation-track | 6 | docs/idare_data_augmentation_closeout_report.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/postwave1/data-augmentation-track | 7 | docs/idare_data_augmentation_fold_level_report.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/postwave1/data-augmentation-track | 8 | docs/idare_data_augmentation_option_a_implementation_report.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/postwave1/data-augmentation-track | 9 | docs/idare_data_augmentation_validation_report.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/postwave1/data-augmentation-track | 10 | docs/idare_deap_cross_subject_data_augmentation_objective.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/postwave1/data-augmentation-track | 11 | docs/idare_label_task_protocol_final_decision_matrix.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/postwave1/data-augmentation-track | 12 | docs/idare_label_task_protocol_final_decision_objective.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/postwave1/data-augmentation-track | 13 | docs/idare_prior_best_cell_confirmation_authorization_package.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/postwave1/data-augmentation-track | 14 | docs/idare_prior_best_cell_confirmation_matrix.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/postwave1/data-augmentation-track | 15 | docs/idare_prior_best_confirmation_status_update.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/postwave1/data-augmentation-track | 16 | docs/idare_root_cause_triage_execution_authorization_package.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/postwave1/data-augmentation-track | 17 | docs/idare_strict_ntd_norm_dg_candidate_spec.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/postwave1/data-augmentation-track | 18 | docs/idare_strict_ntd_norm_dg_leakage_review.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/control-tower | 1 | docs/idare_cross_subject_failure_root_cause_triage_objective.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/control-tower | 2 | docs/idare_label_task_protocol_target_policy_decision_matrix.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/control-tower | 3 | docs/idare_label_task_protocol_target_policy_decision_package.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/control-tower | 4 | docs/idare_post_strict_ntd_smoke_synthesis_and_pivot_decision.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/control-tower | 5 | docs/idare_deap_cross_subject_data_augmentation_objective.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/control-tower | 6 | docs/idare_label_task_protocol_final_decision_matrix.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/control-tower | 7 | docs/idare_label_task_protocol_final_decision_objective.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/control-tower | 8 | docs/idare_prior_best_cell_confirmation_authorization_package.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/control-tower | 9 | docs/idare_prior_best_cell_confirmation_matrix.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/control-tower | 10 | docs/idare_prior_best_confirmation_status_update.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/control-tower | 11 | docs/idare_root_cause_triage_execution_authorization_package.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/control-tower | 12 | docs/idare_strict_ntd_norm_dg_candidate_spec.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/control-tower | 13 | docs/idare_strict_ntd_norm_dg_leakage_review.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/control-tower | 14 | docs/idare_strict_ntd_norm_minimal_smoke_design_matrix.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/control-tower | 15 | docs/idare_strict_ntd_norm_minimal_smoke_design_objective.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/control-tower | 16 | docs/idare_strict_ntd_norm_smoke_execution_authorization_package.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/control-tower | 17 | docs/idare_target_protocol_lock_decision_matrix.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/control-tower | 18 | docs/idare_target_protocol_lock_review_and_minimal_execution_decision.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/postwave1/idare-prior-best-cell-confirmation | 1 | docs/idare_cross_subject_failure_root_cause_triage_objective.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/postwave1/idare-prior-best-cell-confirmation | 2 | docs/idare_label_task_protocol_target_policy_decision_matrix.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/postwave1/idare-prior-best-cell-confirmation | 3 | docs/idare_label_task_protocol_target_policy_decision_package.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/postwave1/idare-prior-best-cell-confirmation | 4 | docs/idare_post_strict_ntd_smoke_synthesis_and_pivot_decision.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/postwave1/idare-prior-best-cell-confirmation | 5 | docs/idare_prior_best_confirm_closeout_report.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/postwave1/idare-prior-best-cell-confirmation | 6 | docs/idare_prior_best_confirm_execution_report.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/postwave1/idare-prior-best-cell-confirmation | 7 | docs/idare_prior_best_confirm_fold_level_report.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/postwave1/idare-prior-best-cell-confirmation | 8 | docs/idare_prior_best_confirm_metric_summary.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/postwave1/idare-prior-best-cell-confirmation | 9 | docs/idare_prior_best_confirm_validation_report.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/postwave1/idare-prior-best-cell-confirmation | 10 | docs/idare_label_task_protocol_final_decision_matrix.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/postwave1/idare-prior-best-cell-confirmation | 11 | docs/idare_label_task_protocol_final_decision_objective.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/postwave1/idare-prior-best-cell-confirmation | 12 | docs/idare_prior_best_cell_confirmation_authorization_package.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/postwave1/idare-prior-best-cell-confirmation | 13 | docs/idare_prior_best_cell_confirmation_matrix.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/postwave1/idare-prior-best-cell-confirmation | 14 | docs/idare_prior_best_confirm_artifact_review_bundle.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/postwave1/idare-prior-best-cell-confirmation | 15 | docs/idare_prior_best_confirm_leakage_scope_audit.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/postwave1/idare-prior-best-cell-confirmation | 16 | docs/idare_prior_best_confirm_objective.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/postwave1/idare-prior-best-cell-confirmation | 17 | docs/idare_prior_best_confirm_prior_vs_confirmation_comparison.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/postwave1/idare-prior-best-cell-confirmation | 18 | docs/idare_root_cause_triage_execution_authorization_package.md | KEEP_EVIDENCE_CHERRY_PICK_ONLY |
| origin/idare/postwave1/label-task-protocol-reconciliation | 1 | docs/idare_cross_subject_failure_root_cause_triage_objective.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/label-task-protocol-reconciliation | 2 | docs/idare_label_task_protocol_midpoint_fold_subject_bias_report.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/label-task-protocol-reconciliation | 3 | docs/idare_label_task_protocol_prior_results_interpretation_report.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/label-task-protocol-reconciliation | 4 | docs/idare_post_strict_ntd_smoke_synthesis_and_pivot_decision.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/label-task-protocol-reconciliation | 5 | docs/idare_label_task_protocol_final_reconciliation_decision_matrix.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/label-task-protocol-reconciliation | 6 | docs/idare_label_task_protocol_label_task_policy_report.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/label-task-protocol-reconciliation | 7 | docs/idare_label_task_protocol_protocol_comparison_report.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/label-task-protocol-reconciliation | 8 | docs/idare_root_cause_triage_execution_authorization_package.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/label-task-protocol-reconciliation | 9 | docs/idare_strict_ntd_norm_dg_candidate_spec.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/label-task-protocol-reconciliation | 10 | docs/idare_strict_ntd_norm_dg_leakage_review.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/label-task-protocol-reconciliation | 11 | docs/idare_strict_ntd_norm_minimal_smoke_design_matrix.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/label-task-protocol-reconciliation | 12 | docs/idare_strict_ntd_norm_minimal_smoke_design_objective.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/label-task-protocol-reconciliation | 13 | docs/idare_strict_ntd_norm_smoke_execution_authorization_package.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/label-task-protocol-reconciliation | 14 | docs/idare_cross_subject_failure_root_cause_triage_objective.json | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/label-task-protocol-reconciliation | 15 | docs/idare_label_task_protocol_artifact_review_bundle.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/label-task-protocol-reconciliation | 16 | docs/idare_label_task_protocol_midpoint_fold_subject_bias_report.json | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/label-task-protocol-reconciliation | 17 | docs/idare_label_task_protocol_prior_results_interpretation_report.json | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/label-task-protocol-reconciliation | 18 | docs/idare_label_task_protocol_reconciliation_closeout.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/root-cause-triage | 1 | docs/idare_root_cause_triage_label_task_sanity_report.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/root-cause-triage | 2 | docs/idare_root_cause_triage_representation_failure_report.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/root-cause-triage | 3 | docs/idare_root_cause_triage_subject_domain_shift_report.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/root-cause-triage | 4 | docs/idare_cross_subject_failure_root_cause_triage_objective.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/root-cause-triage | 5 | docs/idare_post_strict_ntd_smoke_synthesis_and_pivot_decision.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/root-cause-triage | 6 | docs/idare_root_cause_triage_closeout_report.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/root-cause-triage | 7 | docs/idare_root_cause_triage_decision_matrix.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/root-cause-triage | 8 | docs/idare_root_cause_triage_null_permutation_sanity_report.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/root-cause-triage | 9 | docs/idare_root_cause_triage_protocol_alignment_report.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/root-cause-triage | 10 | docs/idare_root_cause_triage_artifact_review_bundle.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/root-cause-triage | 11 | docs/idare_root_cause_triage_branch_objective.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/root-cause-triage | 12 | docs/idare_root_cause_triage_execution_authorization_package.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/root-cause-triage | 13 | docs/idare_root_cause_triage_label_task_sanity_report.json | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/root-cause-triage | 14 | docs/idare_root_cause_triage_representation_failure_report.json | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/root-cause-triage | 15 | docs/idare_root_cause_triage_runner_plan.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/root-cause-triage | 16 | docs/idare_root_cause_triage_subject_domain_shift_report.json | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/root-cause-triage | 17 | docs/idare_strict_ntd_norm_dg_candidate_spec.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/root-cause-triage | 18 | docs/idare_strict_ntd_norm_dg_leakage_review.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/representation-redesign-confirmation | 1 | docs/idare_post_strict_ntd_smoke_synthesis_and_pivot_decision.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/representation-redesign-confirmation | 2 | docs/idare_strict_ntd_norm_dg_candidate_spec.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/representation-redesign-confirmation | 3 | docs/idare_strict_ntd_norm_dg_leakage_review.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/representation-redesign-confirmation | 4 | docs/idare_strict_ntd_norm_minimal_smoke_design_matrix.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/representation-redesign-confirmation | 5 | docs/idare_strict_ntd_norm_minimal_smoke_design_objective.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/representation-redesign-confirmation | 6 | docs/idare_strict_ntd_norm_smoke_execution_authorization_package.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/representation-redesign-confirmation | 7 | docs/idare_post_strict_ntd_smoke_synthesis_and_pivot_decision.json | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/representation-redesign-confirmation | 8 | docs/idare_post_wave1_synthesis_and_next_decision_matrix.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/representation-redesign-confirmation | 9 | docs/idare_post_wave1_synthesis_and_next_decision_objective.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/representation-redesign-confirmation | 10 | docs/idare_repr_redesign_confirm_closeout_report.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/representation-redesign-confirmation | 11 | docs/idare_repr_redesign_confirm_fold_level_report.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/representation-redesign-confirmation | 12 | docs/idare_representation_redesign_candidate_spec_and_leakage_review.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/representation-redesign-confirmation | 13 | docs/idare_representation_redesign_confirmation_objective.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/representation-redesign-confirmation | 14 | docs/idare_representation_redesign_design_objective.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/representation-redesign-confirmation | 15 | docs/idare_representation_redesign_smoke_authorization_package.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/representation-redesign-confirmation | 16 | docs/idare_strict_nontransductive_norm_dg_design_matrix.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/representation-redesign-confirmation | 17 | docs/idare_strict_nontransductive_norm_dg_design_objective.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/representation-redesign-confirmation | 18 | docs/idare_repr_redesign_confirm_artifact_review_bundle.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/representation-redesign-smoke | 1 | docs/idare_post_strict_ntd_smoke_synthesis_and_pivot_decision.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/representation-redesign-smoke | 2 | docs/idare_repr_redesign_smoke_representation_diagnostic_report.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/representation-redesign-smoke | 3 | docs/idare_strict_ntd_norm_dg_candidate_spec.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/representation-redesign-smoke | 4 | docs/idare_strict_ntd_norm_dg_leakage_review.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/representation-redesign-smoke | 5 | docs/idare_strict_ntd_norm_minimal_smoke_design_matrix.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/representation-redesign-smoke | 6 | docs/idare_strict_ntd_norm_minimal_smoke_design_objective.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/representation-redesign-smoke | 7 | docs/idare_strict_ntd_norm_smoke_execution_authorization_package.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/representation-redesign-smoke | 8 | docs/idare_post_strict_ntd_smoke_synthesis_and_pivot_decision.json | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/representation-redesign-smoke | 9 | docs/idare_post_wave1_synthesis_and_next_decision_matrix.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/representation-redesign-smoke | 10 | docs/idare_post_wave1_synthesis_and_next_decision_objective.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/representation-redesign-smoke | 11 | docs/idare_repr_redesign_smoke_closeout_report.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/representation-redesign-smoke | 12 | docs/idare_repr_redesign_smoke_fold_level_report.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/representation-redesign-smoke | 13 | docs/idare_repr_redesign_smoke_validation_report.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/representation-redesign-smoke | 14 | docs/idare_representation_redesign_candidate_spec_and_leakage_review.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/representation-redesign-smoke | 15 | docs/idare_representation_redesign_design_objective.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/representation-redesign-smoke | 16 | docs/idare_representation_redesign_smoke_authorization_package.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/representation-redesign-smoke | 17 | docs/idare_strict_nontransductive_norm_dg_design_matrix.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/representation-redesign-smoke | 18 | docs/idare_strict_nontransductive_norm_dg_design_objective.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/strict-ntd-norm-smoke | 1 | docs/idare_strict_ntd_norm_smoke_report.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/strict-ntd-norm-smoke | 2 | docs/idare_strict_ntd_norm_dg_candidate_spec.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/strict-ntd-norm-smoke | 3 | docs/idare_strict_ntd_norm_dg_leakage_review.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/strict-ntd-norm-smoke | 4 | docs/idare_strict_ntd_norm_minimal_smoke_design_matrix.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/strict-ntd-norm-smoke | 5 | docs/idare_strict_ntd_norm_minimal_smoke_design_objective.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/strict-ntd-norm-smoke | 6 | docs/idare_strict_ntd_norm_smoke_execution_authorization_package.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/strict-ntd-norm-smoke | 7 | docs/idare_strict_ntd_norm_smoke_objective.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/strict-ntd-norm-smoke | 8 | docs/idare_post_wave1_synthesis_and_next_decision_matrix.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/strict-ntd-norm-smoke | 9 | docs/idare_post_wave1_synthesis_and_next_decision_objective.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/strict-ntd-norm-smoke | 10 | docs/idare_strict_nontransductive_norm_dg_design_matrix.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/strict-ntd-norm-smoke | 11 | docs/idare_strict_nontransductive_norm_dg_design_objective.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/strict-ntd-norm-smoke | 12 | docs/idare_strict_ntd_norm_smoke_report.json | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/strict-ntd-norm-smoke | 13 | docs/idare_strict_ntd_norm_dg_candidate_spec.json | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/strict-ntd-norm-smoke | 14 | docs/idare_strict_ntd_norm_dg_leakage_review.json | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/strict-ntd-norm-smoke | 15 | docs/idare_strict_ntd_norm_minimal_smoke_design_matrix.json | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/strict-ntd-norm-smoke | 16 | docs/idare_strict_ntd_norm_minimal_smoke_design_objective.json | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/strict-ntd-norm-smoke | 17 | docs/idare_strict_ntd_norm_smoke_execution_authorization_package.json | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/postwave1/strict-ntd-norm-smoke | 18 | docs/idare_strict_ntd_norm_smoke_objective.json | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/wave1/eeg-input-definition | 1 | docs/idare_w1a_eeg_input_def_report.md | REVIEW_BEFORE_ACTION |
| origin/idare/wave1/eeg-input-definition | 2 | docs/idare_w1a_eeg_input_def_closeout.md | REVIEW_BEFORE_ACTION |
| origin/idare/wave1/eeg-input-definition | 3 | docs/idare_w1a_eeg_input_def_objective.md | REVIEW_BEFORE_ACTION |
| origin/idare/wave1/eeg-input-definition | 4 | docs/idare_w1a_eeg_input_def_report.json | REVIEW_BEFORE_ACTION |
| origin/idare/wave1/eeg-input-definition | 5 | docs/idare_w1a_eeg_input_def_closeout.json | REVIEW_BEFORE_ACTION |
| origin/idare/wave1/eeg-input-definition | 6 | docs/idare_w1a_eeg_input_def_input_manifest.csv | REVIEW_BEFORE_ACTION |
| origin/idare/wave1/eeg-input-definition | 7 | docs/idare_w1a_eeg_input_def_objective.json | REVIEW_BEFORE_ACTION |
| origin/idare/wave1/eeg-input-definition | 8 | docs/idare_w1a_eeg_input_def_predictions.csv | REVIEW_BEFORE_ACTION |
| origin/idare/wave1/eeg-input-definition | 9 | docs/idare_w1a_eeg_input_def_run_matrix.csv | REVIEW_BEFORE_ACTION |
| origin/idare/wave1/eeg-input-definition | 10 | docs/idare_w1a_eeg_input_def_runs.csv | REVIEW_BEFORE_ACTION |
| origin/idare/wave1/eeg-input-definition | 11 | docs/idare_w1a_eeg_input_def_runner.py | REVIEW_BEFORE_ACTION |
| origin/idare/wave1/emg-baseline-ablation | 1 | docs/idare_w1c_emg_baseline_report.md | REVIEW_BEFORE_ACTION |
| origin/idare/wave1/emg-baseline-ablation | 2 | docs/idare_w1c_emg_baseline_smoke_report.md | REVIEW_BEFORE_ACTION |
| origin/idare/wave1/emg-baseline-ablation | 3 | docs/idare_w1c_emg_baseline_closeout.md | REVIEW_BEFORE_ACTION |
| origin/idare/wave1/emg-baseline-ablation | 4 | docs/idare_w1c_emg_baseline_objective.md | REVIEW_BEFORE_ACTION |
| origin/idare/wave1/emg-baseline-ablation | 5 | docs/idare_w1c_emg_baseline_report.json | REVIEW_BEFORE_ACTION |
| origin/idare/wave1/emg-baseline-ablation | 6 | docs/idare_w1c_emg_baseline_smoke_report.json | REVIEW_BEFORE_ACTION |
| origin/idare/wave1/emg-baseline-ablation | 7 | docs/idare_w1c_emg_baseline_closeout.json | REVIEW_BEFORE_ACTION |
| origin/idare/wave1/emg-baseline-ablation | 8 | docs/idare_w1c_emg_baseline_objective.json | REVIEW_BEFORE_ACTION |
| origin/idare/wave1/emg-baseline-ablation | 9 | docs/idare_w1c_emg_baseline_predictions.csv | REVIEW_BEFORE_ACTION |
| origin/idare/wave1/emg-baseline-ablation | 10 | docs/idare_w1c_emg_baseline_smoke_predictions.csv | REVIEW_BEFORE_ACTION |
| origin/idare/wave1/emg-baseline-ablation | 11 | scripts/idare_w1c_emg_baseline_runner.py | REVIEW_BEFORE_ACTION |
| origin/idare/wave1/eeg-subject-normalization | 1 | docs/idare_w1b_eeg_subj_norm_report.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/wave1/eeg-subject-normalization | 2 | docs/idare_w1b_eeg_subj_norm_closeout.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/wave1/eeg-subject-normalization | 3 | docs/idare_w1b_eeg_subj_norm_objective.md | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/wave1/eeg-subject-normalization | 4 | docs/idare_w1b_eeg_subj_norm_report.json | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/wave1/eeg-subject-normalization | 5 | docs/idare_w1b_eeg_subj_norm_closeout.json | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/wave1/eeg-subject-normalization | 6 | docs/idare_w1b_eeg_subj_norm_fold_diagnostics.csv | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/wave1/eeg-subject-normalization | 7 | docs/idare_w1b_eeg_subj_norm_objective.json | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/wave1/eeg-subject-normalization | 8 | docs/idare_w1b_eeg_subj_norm_runs.csv | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/wave1/eeg-subject-normalization | 9 | scripts/idare_w1b_eeg_subj_norm_runner.py | KEEP_METHOD_NOTES_CHERRY_PICK_ONLY |
| origin/idare/wave1/feature-discriminability | 1 | docs/idare_w1d_feat_discrim_decision_matrix.md | REVIEW_BEFORE_ACTION |
| origin/idare/wave1/feature-discriminability | 2 | docs/idare_w1d_feat_discrim_report.md | REVIEW_BEFORE_ACTION |
| origin/idare/wave1/feature-discriminability | 3 | docs/idare_w1d_feat_discrim_closeout.md | REVIEW_BEFORE_ACTION |
| origin/idare/wave1/feature-discriminability | 4 | docs/idare_w1d_feat_discrim_objective.md | REVIEW_BEFORE_ACTION |
| origin/idare/wave1/feature-discriminability | 5 | docs/idare_w1d_feat_discrim_report.json | REVIEW_BEFORE_ACTION |
| origin/idare/wave1/feature-discriminability | 6 | docs/idare_w1d_feat_discrim_top_features.csv | REVIEW_BEFORE_ACTION |
| origin/idare/wave1/feature-discriminability | 7 | scripts/idare_w1d_feat_discrim_audit.py | REVIEW_BEFORE_ACTION |

## Interpretation

The extra branches are not a GitHub connection error. They are old Wave/PostWave experimental branches. They should not be merged wholesale into the current ROCA branch because they contain older objectives, older protocols, and historical claims. The safe route is to preserve them as evidence, cherry-pick only missing reports if needed, and keep the current locked-gate ROCA conclusion as the project truth.
