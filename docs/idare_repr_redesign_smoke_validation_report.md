# I-DARE Representation Redesign Smoke Validation Report

- status: `validation_passed`
- generated_at_utc: `2026-05-11T17:04:11+00:00`
- blocker_count: `0`
- smoke_execution_occurred: `False`
- experiment_execution_occurred: `False`

## Checks

| Level | Message | Details |
|---|---|---|
| OK | git metadata read | `{"branch": "idare/postwave1/representation-redesign-smoke", "cwd": "/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-repr-redesign-smoke", "head": "fc60e753d303ad5dfdbdd892fc220a0839cc95b9", "top": "/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-repr-redesign-smoke"}` |
| OK | branch matches expected branch | `{}` |
| OK | worktree matches expected worktree | `{}` |
| OK | dirty paths are empty or restricted to allowed idare_repr_redesign_smoke_* prefixes | `{"paths": ["docs/idare_repr_redesign_smoke_objective.json", "docs/idare_repr_redesign_smoke_objective.md", "scripts/idare_repr_redesign_smoke_runner.py"]}` |
| OK | objective JSON loaded | `{"path": "docs/idare_repr_redesign_smoke_objective.json"}` |
| OK | objective field validated: objective_id | `{}` |
| OK | objective field validated: allowed_branch | `{}` |
| OK | objective field validated: allowed_worktree | `{}` |
| OK | objective correctly keeps smoke execution unauthorized | `{}` |
| OK | required EEG cache/index files exist | `{"cache_index": ".cache/idare_eeg_cache_index_baseline_corrected.csv", "cache_npy": ".cache/idare_eeg_windows_32x640_float32_baseline_corrected.npy"}` |
| OK | EEG cache shape is compatible | `{"dtype": "float32", "shape": [2016, 32, 640]}` |
| OK | cache-index required arousal/subject/cache columns exist | `{"columns": ["cache_row", "subject_id", "subject_col", "stimulus_id", "raw_event_name", "bsl_raw_event_name", "eeg_file", "eeg_begin_raw", "bsl_eeg_begin_raw", "stim_event_index_0based", "bsl_event_index_0based", "stim_event_index_1based", "bsl_event_index_1based", "baseline_correction", "valence_score", "arousal_score", "diag_baseline_mean_global", "diag_baseline_mean_abs_mean", "diag_corrected_mean_before_zscore", "diag_corrected_std_before_zscore", "valence_discard_midpoint", "valence_midpoint_as_low", "valence_midpoint_as_high", "arousal_discard_midpoint", "arousal_midpoint_as_low", "arousal_midpoint_as_high"]}` |
| OK | planned outputs are restricted to allowed prefixes | `{"planned_outputs": ["docs/idare_repr_redesign_smoke_validation_report.md", "docs/idare_repr_redesign_smoke_validation_report.json", "docs/idare_repr_redesign_smoke_runs.csv", "docs/idare_repr_redesign_smoke_metric_summary.csv", "docs/idare_repr_redesign_smoke_fold_level_report.md", "docs/idare_repr_redesign_smoke_fold_level_report.json", "docs/idare_repr_redesign_smoke_leakage_audit.md", "docs/idare_repr_redesign_smoke_leakage_audit.json", "docs/idare_repr_redesign_smoke_representation_diagnostic_report.md", "docs/idare_repr_redesign_smoke_representation_diagnostic_report.json", "docs/idare_repr_redesign_smoke_closeout_report.md", "docs/idare_repr_redesign_smoke_closeout_report.json"]}` |
| OK | scope validated: dataset | `{}` |
| OK | scope validated: modality | `{}` |
| OK | scope validated: task | `{}` |
| OK | scope validated: evaluation | `{}` |
| OK | scope validated: comparison | `{}` |
| OK | scope validated: model_family | `{}` |
| OK | scope validated: cells_only | `{}` |
| OK | planned 4 x 6 = 24 run matrix is declared but not executed | `{"planned_matrix": {"cells": 4, "execution_authorized": false, "folds": 6, "planned_runs": 24}}` |
| OK | planned matrix correctly remains unauthorized for execution | `{}` |
| OK | representation cell set validated | `{"cells": ["R0", "R1", "R2", "R3"]}` |
| OK | hard leakage constraints asserted in objective | `{}` |
| OK | R1 leakage guard validated | `{}` |
| OK | R2 leakage guard validated | `{}` |
| OK | R3 leakage guard validated | `{}` |

## Blocker Status

`NO_BLOCKERS`

## Execution Boundary

No 24-run smoke execution occurred.
No experiment execution occurred.
Runner creation/validation only.
