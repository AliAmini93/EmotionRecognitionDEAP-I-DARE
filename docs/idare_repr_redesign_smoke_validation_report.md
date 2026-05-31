# I-DARE Representation Redesign Smoke Validation Report

- status: `validation_passed`
- generated_at_utc: `2026-05-11T17:33:49+00:00`
- blocker_count: `0`
- smoke_execution_occurred: `False`
- experiment_execution_occurred: `False`

## Checks

| Level | Message | Details |
|---|---|---|
| OK | git metadata read | `{"branch": "idare/postwave1/representation-redesign-smoke", "cwd": "/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-repr-redesign-smoke", "head": "c9f93ded15a6dcb6bea812e5bee3d1b5a6c53d86", "top": "/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-repr-redesign-smoke"}` |
| OK | branch matches expected branch | `{}` |
| OK | worktree matches expected worktree | `{}` |
| OK | dirty paths are empty or restricted to allowed idare_repr_redesign_smoke_* prefixes | `{"paths": ["docs/idare_repr_redesign_smoke_validation_report.json", "docs/idare_repr_redesign_smoke_validation_report.md", "scripts/idare_repr_redesign_smoke_runner.py", "docs/idare_repr_redesign_smoke_artifact_review_bundle.json", "docs/idare_repr_redesign_smoke_artifact_review_bundle.md", "docs/idare_repr_redesign_smoke_closeout_report.json", "docs/idare_repr_redesign_smoke_closeout_report.md", "docs/idare_repr_redesign_smoke_fold_level_report.json", "docs/idare_repr_redesign_smoke_fold_level_report.md", "docs/idare_repr_redesign_smoke_leakage_audit.json", "docs/idare_repr_redesign_smoke_leakage_audit.md", "docs/idare_repr_redesign_smoke_metric_summary.csv", "docs/idare_repr_redesign_smoke_representation_diagnostic_report.json", "docs/idare_repr_redesign_smoke_representation_diagnostic_report.md", "docs/idare_repr_redesign_smoke_runs.csv"]}` |
| OK | objective JSON loaded | `{"path": "docs/idare_repr_redesign_smoke_objective.json"}` |
| OK | objective keeps smoke execution unauthorized until runtime token | `{}` |
| OK | EEG cache shape is compatible | `{"dtype": "float32", "shape": [2016, 32, 640]}` |
| OK | cache-index required arousal/subject/cache columns exist | `{"columns": ["cache_row", "subject_id", "subject_col", "stimulus_id", "raw_event_name", "bsl_raw_event_name", "eeg_file", "eeg_begin_raw", "bsl_eeg_begin_raw", "stim_event_index_0based", "bsl_event_index_0based", "stim_event_index_1based", "bsl_event_index_1based", "baseline_correction", "valence_score", "arousal_score", "diag_baseline_mean_global", "diag_baseline_mean_abs_mean", "diag_corrected_mean_before_zscore", "diag_corrected_std_before_zscore", "valence_discard_midpoint", "valence_midpoint_as_low", "valence_midpoint_as_high", "arousal_discard_midpoint", "arousal_midpoint_as_low", "arousal_midpoint_as_high"]}` |
| OK | planned outputs are restricted to allowed prefixes | `{"planned_outputs": ["docs/idare_repr_redesign_smoke_validation_report.md", "docs/idare_repr_redesign_smoke_validation_report.json", "docs/idare_repr_redesign_smoke_runs.csv", "docs/idare_repr_redesign_smoke_metric_summary.csv", "docs/idare_repr_redesign_smoke_fold_level_report.md", "docs/idare_repr_redesign_smoke_fold_level_report.json", "docs/idare_repr_redesign_smoke_leakage_audit.md", "docs/idare_repr_redesign_smoke_leakage_audit.json", "docs/idare_repr_redesign_smoke_representation_diagnostic_report.md", "docs/idare_repr_redesign_smoke_representation_diagnostic_report.json", "docs/idare_repr_redesign_smoke_closeout_report.md", "docs/idare_repr_redesign_smoke_closeout_report.json", "docs/idare_repr_redesign_smoke_artifact_review_bundle.md", "docs/idare_repr_redesign_smoke_artifact_review_bundle.json"]}` |
| OK | scope validated: dataset | `{}` |
| OK | scope validated: modality | `{}` |
| OK | scope validated: task | `{}` |
| OK | scope validated: evaluation | `{}` |
| OK | scope validated: comparison | `{}` |
| OK | scope validated: model_family | `{}` |
| OK | scope validated: cells_only | `{}` |
| OK | planned 4 x 6 = 24 run matrix validated | `{"planned_matrix": {"cells": 4, "execution_authorized": false, "folds": 6, "planned_runs": 24}}` |
| OK | hard leakage constraints asserted in objective | `{}` |

## Blocker Status

`NO_BLOCKERS`

## Execution Boundary

Validation/preflight only.
