# I-DARE Prior Best Confirmation Validation Report

- status: `PASSED`
- mode: `validate`
- expected_branch: `idare/postwave1/idare-prior-best-cell-confirmation`
- expected_worktree: `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-idare-prior-best-confirm`
- actual_root: `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-idare-prior-best-confirm`
- confirmation_execution_occurred: `false`
- experiment_or_model_result_created: `false`
- model_results_created: `false`
- final_paper_level_claim_made: `false`

## Registered Cells

| Cell | Dataset | Modality | Task | Label policy | Recipe |
|---|---|---|---|---|---|
| C0 | I-DARE | EEG | arousal | midpoint_as_high | ce_class_weighted |
| C1 | I-DARE | EEG | valence | discard_midpoint | balanced_sampler_ce |
| C2 | I-DARE | EMG | arousal | discard_midpoint | ce_class_weighted |
| C3 | I-DARE | EMG | valence | midpoint_as_high | ce_class_weighted |

## Planned Matrix Metadata

- 4 cells x 6 folds = 24 planned confirmation runs.
- Metadata only.
- No confirmation run executed.

## Blockers

- None.

## Check Summary

| Check | OK | Details |
|---|---:|---|
| git_root_matches_script_root | true | `{"git_root": "/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-idare-prior-best-confirm", "script_root": "/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-idare-prior-best-confirm"}` |
| expected_worktree_path | true | `{"actual": "/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-idare-prior-best-confirm", "expected": "/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-idare-prior-best-confirm"}` |
| expected_branch | true | `{"actual": "idare/postwave1/idare-prior-best-cell-confirmation", "expected": "idare/postwave1/idare-prior-best-cell-confirmation", "stderr": ""}` |
| git_status_readable | true | `{"status": "## idare/postwave1/idare-prior-best-cell-confirmation...origin/idare/control-tower\n A docs/idare_prior_best_confirm_objective.json\n A docs/idare_prior_best_confirm...` |
| git_changes_limited_to_allowed_prefix | true | `{"changed_paths": ["docs/idare_prior_best_confirm_objective.json", "docs/idare_prior_best_confirm_objective.md", "docs/idare_prior_best_confirm_validation_report.json", "docs/id...` |
| only_expected_prefix_files_present | true | `{"prefix_files": ["docs/idare_prior_best_confirm_objective.json", "docs/idare_prior_best_confirm_objective.md", "docs/idare_prior_best_confirm_validation_report.json", "docs/ida...` |
| objective_json_exists | true | `"docs/idare_prior_best_confirm_objective.json"` |
| exact_four_registered_cells | true | `[{"cell_id": "C0", "dataset": "I-DARE", "label_policy": "midpoint_as_high", "modality": "EEG", "recipe": "ce_class_weighted", "task": "arousal"}, {"cell_id": "C1", "dataset": "I...` |
| planned_matrix_metadata_only_4x6_24 | true | `{"cells": 4, "folds_per_cell": 6, "metadata_only": true, "planned_confirmation_runs": 24}` |
| required_doc_exists:docs/project_status_current.md | true | `"docs/project_status_current.md"` |
| required_doc_exists:docs/project_operating_protocol.md | true | `"docs/project_operating_protocol.md"` |
| required_doc_exists:docs/research_scope_and_objectives.md | true | `"docs/research_scope_and_objectives.md"` |
| required_doc_exists:docs/smoke_and_evaluation_protocol.md | true | `"docs/smoke_and_evaluation_protocol.md"` |
| required_doc_exists:docs/idare_label_policy_ablation_objective.md | true | `"docs/idare_label_policy_ablation_objective.md"` |
| required_doc_exists:docs/idare_label_policy_ablation_objective.json | true | `"docs/idare_label_policy_ablation_objective.json"` |
| required_doc_exists:docs/idare_label_policy_ablation_report.md | true | `"docs/idare_label_policy_ablation_report.md"` |
| required_doc_exists:docs/idare_label_policy_ablation_report.json | true | `"docs/idare_label_policy_ablation_report.json"` |
| required_doc_exists:docs/idare_label_policy_ablation_eeg_primary.json | true | `"docs/idare_label_policy_ablation_eeg_primary.json"` |
| required_doc_exists:docs/idare_label_policy_ablation_emg_primary.json | true | `"docs/idare_label_policy_ablation_emg_primary.json"` |
| required_doc_exists:docs/idare_label_policy_ablation_review_status.md | true | `"docs/idare_label_policy_ablation_review_status.md"` |
| required_doc_exists:docs/idare_label_policy_ablation_review_status.json | true | `"docs/idare_label_policy_ablation_review_status.json"` |
| required_input_exists:eeg_cache_npy | true | `".cache/idare_eeg_windows_32x640_float32_baseline_corrected.npy"` |
| npy_shape:eeg_cache_npy | true | `{"actual": [2016, 32, 640], "expected": [2016, 32, 640]}` |
| required_input_exists:eeg_cache_index_csv | true | `".cache/idare_eeg_cache_index_baseline_corrected.csv"` |
| csv_columns:eeg_cache_index_csv | true | `{"missing": [], "required": ["cache_row", "subject_id", "arousal_midpoint_as_high", "valence_discard_midpoint"], "rows": 2016}` |
| csv_nonempty:eeg_cache_index_csv | true | `{"rows": 2016}` |
| required_input_exists:emg_cache_npy | true | `".cache/idare_emg_features.npy"` |
| npy_shape:emg_cache_npy | true | `{"actual": [2016, 22], "expected": [2016, 22]}` |
| required_input_exists:emg_cache_index_csv | true | `".cache/idare_emg_feature_cache_index.csv"` |
| csv_columns:emg_cache_index_csv | true | `{"missing": [], "required": ["cache_row", "subject_id", "arousal_discard_midpoint", "valence_midpoint_as_high"], "rows": 2016}` |
| csv_nonempty:emg_cache_index_csv | true | `{"rows": 2016}` |
