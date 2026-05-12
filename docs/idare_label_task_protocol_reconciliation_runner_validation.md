# I-DARE Label/Task Protocol Reconciliation Runner Validation

- status: `PASSED`
- mode: `audit`
- blocker_count: `0`
- audit_execution_occurred: `false`
- experiment_or_model_result_created: `false`
- allowed_prefix: `idare_label_task_protocol_`

## Checks

| Check | Status | Detail |
|---|---|---|
| `branch` | `PASSED` | idare/postwave1/label-task-protocol-reconciliation |
| `worktree` | `PASSED` | /mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-label-task-protocol |
| `git_status_allowed_prefix` | `PASSED` | only allowed-prefix changes: M docs/idare_label_task_protocol_reconciliation_runner_validation.json |  M docs/idare_label_task_protocol_reconciliation_runner_validation.md |  M scripts/idare_label_task_protocol_reconciliation_runner.py |
| `staged_changes` | `PASSED` | no staged changes |
| `required_doc:docs/idare_label_task_protocol_reconciliation_execution_authorization_package.md` | `PASSED` | exists |
| `required_doc:docs/idare_label_task_protocol_reconciliation_execution_authorization_package.json` | `PASSED` | exists |
| `required_doc:docs/idare_label_task_protocol_reconciliation_design_objective.md` | `PASSED` | exists |
| `required_doc:docs/idare_label_task_protocol_reconciliation_design_objective.json` | `PASSED` | exists |
| `required_doc:docs/idare_label_task_protocol_reconciliation_objective.md` | `PASSED` | exists |
| `required_doc:docs/idare_label_task_protocol_reconciliation_objective.json` | `PASSED` | exists |
| `required_doc:docs/idare_root_cause_triage_execution_authorization_package.md` | `PASSED` | exists |
| `required_doc:docs/idare_cross_subject_failure_root_cause_triage_objective.md` | `PASSED` | exists |
| `required_doc:docs/idare_project_final_registry.csv` | `PASSED` | exists |
| `required_doc:docs/idare_project_synthesis_review_and_final_registry_update.json` | `PASSED` | exists |
| `required_cache_or_index:.cache/idare_eeg_cache_index.csv` | `PASSED` | exists |
| `required_cache_or_index:.cache/idare_eeg_cache_index_baseline_corrected.csv` | `PASSED` | exists |
| `required_cache_or_index:.cache/idare_trial_index.csv` | `PASSED` | exists |
| `required_cache_array_metadata_only:.cache/idare_eeg_windows_32x640_float32.npy` | `PASSED` | exists size_bytes=165150848 |
| `required_cache_array_metadata_only:.cache/idare_eeg_windows_32x640_float32_baseline_corrected.npy` | `PASSED` | exists size_bytes=165150848 |
| `local_link_or_dir:.cache` | `PASSED` | /mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE/.cache |
| `local_link_or_dir:.venv` | `PASSED` | /mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE/.venv |
| `output_prefix` | `PASSED` | all intended outputs use idare_label_task_protocol_ |
| `scope` | `PASSED` | compact label/task + protocol reconciliation only |
| `audit_categories_encoded` | `PASSED` | protocol alignment; label/task formulation; midpoint and threshold policy review; fold/subject label-bias review; prior-results interpretation; final label-task/protocol decision matrix |
| `forbidden_now_encoded` | `PASSED` | experiments; model results; Wave 2; DG; model-capacity probe; augmentation; representation redesign v2; DEAP; fusion; preprocessing changes; threshold changes; W1-owned file edits; main push; new operating-point claim |
| `audit_execution_guard` | `PASSED` | explicit Control Tower audit run approval phrase supplied |

## Encoded Audit Categories

- protocol alignment
- label/task formulation
- midpoint and threshold policy review
- fold/subject label-bias review
- prior-results interpretation
- final label-task/protocol decision matrix

## Current Boundary

Validation/preflight does not create model results.
Audit mode was authorized by explicit Control Tower run approval.
