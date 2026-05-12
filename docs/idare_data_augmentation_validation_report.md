# I-DARE Data Augmentation Validation Report

- status: `PASSED`
- mode: `validate`
- expected_branch: `idare/postwave1/data-augmentation-track`
- actual_branch: `idare/postwave1/data-augmentation-track`
- expected_worktree: `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-data-augmentation`
- actual_worktree: `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-data-augmentation`
- execution_authorized: `false`
- da_execution_occurred: `false`
- experiment_or_model_result_created: `false`
- blocker_count: `0`

## Planned Matrix Metadata

- Option A: `2 targets x 2 modalities x 5 DA policies x 6 folds = 120 runs`
- Option B: `2 targets x 1 modality x 5 DA policies x 6 folds = 60 EEG-first runs`
- Metadata only; no DA run executed.

## Blockers

- None.

## Check Summary

| Check | OK | Details |
|---|---:|---|
| expected_worktree | true | `{"actual": "/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-data-augmentation", "expected": "/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-data-augmentation"}` |
| expected_branch | true | `{"actual": "idare/postwave1/data-augmentation-track", "expected": "idare/postwave1/data-augmentation-track"}` |
| cache_symlink_or_dir_exists | true | `".cache"` |
| venv_symlink_or_dir_exists | true | `".venv"` |
| dirty_paths_limited_to_allowed_prefix | true | `{"changed_paths": ["docs/idare_data_augmentation_objective.json", "docs/idare_data_augmentation_objective.md", "scripts/idare_data_augmentation_runner.py"], "disallowed": []}` |
| control_doc_exists:docs/idare_deap_cross_subject_data_augmentation_objective.md | true | `"docs/idare_deap_cross_subject_data_augmentation_objective.md"` |
| control_doc_exists:docs/idare_deap_cross_subject_data_augmentation_objective.json | true | `"docs/idare_deap_cross_subject_data_augmentation_objective.json"` |
| control_doc_exists:docs/idare_data_augmentation_track_execution_authorization_package.md | true | `"docs/idare_data_augmentation_track_execution_authorization_package.md"` |
| control_doc_exists:docs/idare_data_augmentation_track_execution_authorization_package.json | true | `"docs/idare_data_augmentation_track_execution_authorization_package.json"` |
| control_doc_exists:docs/project_status_current.md | true | `"docs/project_status_current.md"` |
| control_doc_exists:docs/project_status_current.json | true | `"docs/project_status_current.json"` |
| control_doc_exists:docs/project_operating_protocol.md | true | `"docs/project_operating_protocol.md"` |
| control_doc_exists:docs/research_scope_and_objectives.md | true | `"docs/research_scope_and_objectives.md"` |
| control_doc_exists:docs/smoke_and_evaluation_protocol.md | true | `"docs/smoke_and_evaluation_protocol.md"` |
| control_doc_exists:docs/idare_prior_best_confirmation_status_update.md | true | `"docs/idare_prior_best_confirmation_status_update.md"` |
| control_doc_exists:docs/idare_prior_best_confirmation_status_update.json | true | `"docs/idare_prior_best_confirmation_status_update.json"` |
| branch_objective_json_exists | true | `"docs/idare_data_augmentation_objective.json"` |
| required_input_exists:eeg_bsl_npy | true | `".cache/idare_eeg_windows_32x640_float32_baseline_corrected.npy"` |
| required_input_exists:eeg_bsl_index | true | `".cache/idare_eeg_cache_index_baseline_corrected.csv"` |
| required_input_exists:eeg_raw_npy | true | `".cache/idare_eeg_windows_32x640_float32.npy"` |
| required_input_exists:eeg_raw_index | true | `".cache/idare_eeg_cache_index.csv"` |
| required_input_exists:eeg_bsl_stats | true | `".cache/idare_eeg_bsl_stats.npy"` |
| required_input_exists:eeg_bsl_stats_index | true | `".cache/idare_eeg_bsl_stats_index.csv"` |
| required_input_exists:emg_features_npy | true | `".cache/idare_emg_features.npy"` |
| required_input_exists:emg_features_index | true | `".cache/idare_emg_feature_cache_index.csv"` |
| required_input_exists:emg_bsl_stats | true | `".cache/idare_emg_bsl_stats.npy"` |
| required_input_exists:emg_bsl_stats_index | true | `".cache/idare_emg_bsl_stats_index.csv"` |
| required_input_exists:raw_emg_npy | true | `".cache/idare_raw_emg_windows_2x10000_float32.npy"` |
| required_input_exists:raw_emg_index | true | `".cache/idare_raw_emg_cache_index.csv"` |
| eeg_bsl_npy_shape | true | `{"dtype": "float32", "shape": [2016, 32, 640]}` |
| eeg_raw_npy_shape | true | `{"dtype": "float32", "shape": [2016, 32, 640]}` |
| emg_features_npy_shape | true | `{"dtype": "float32", "shape": [2016, 22]}` |
| raw_emg_npy_shape | true | `{"dtype": "float32", "shape": [2016, 2, 10000]}` |
| eeg_bsl_index_required_columns | true | `{"columns": ["cache_row", "subject_id", "subject_col", "stimulus_id", "raw_event_name", "bsl_raw_event_name", "eeg_file", "eeg_begin_raw", "bsl_eeg_begin_raw", "stim_event_index_0based", "bsl_event_index_0based", "stim_event_index_1based...` |
| emg_features_index_required_columns | true | `{"columns": ["cache_row", "subject_id", "subject_col", "stimulus_id", "raw_event_name", "bsl_event_index_0based", "stim_event_index_0based", "bsl_event_index_1based", "stim_event_index_1based", "emg_file", "emg_channels", "emg_begin_raw"...` |
| eeg_policy_registry_exact | true | `["E0_none_baseline", "E1_additive_gaussian_noise_weak", "E2_additive_gaussian_noise_medium", "E3_amplitude_scaling", "E4_time_channel_masking_or_dropout"]` |
| emg_policy_registry_exact | true | `["M0_none_baseline", "M1_feature_gaussian_jitter_weak", "M2_feature_gaussian_jitter_medium", "M3_feature_scaling", "M4_feature_dropout"]` |
| option_A_metadata_120_runs | true | `{"execution_authorized": false, "folds": 6, "modalities": ["EEG", "EMG"], "policies_per_modality": 5, "targets": ["valence", "arousal"], "total_runs": 120}` |
| option_B_metadata_60_runs | true | `{"execution_authorized": false, "folds": 6, "modalities": ["EEG"], "policies_per_modality": 5, "targets": ["valence", "arousal"], "total_runs": 60}` |
