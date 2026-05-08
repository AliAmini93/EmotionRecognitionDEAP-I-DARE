# I-DARE Script Archival and Reproducibility Report

## Status

Status: complete; pending human review.

Created UTC: `2026-05-08T13:00:51+00:00`

## Executive Result

Diagnosis: `reproducibility_layer_fixed_for_active_next_step`

Recommended next objective: `run_committed_failure_or_confirmation_analysis_after_review`

The active next analysis script is now committed under `scripts/idare/analysis/` and linked to its objective through `docs/idare_script_archival_manifest.csv`.

## Created Script Assets

| Asset | Status | Purpose |
|---|---|---|
| `scripts/idare/README.md` | created | Documents script archival policy and layout. |
| `scripts/idare/analysis/run_idare_label_semantics_minimal_redesigned_task_failure_or_confirmation_analysis.py` | created, not yet run | Read-only active analysis script for the paused failure-or-confirmation objective. |
| `docs/idare_script_archival_manifest.csv` | created | Links objective, script, command, expected outputs, and provenance. |

## Historical Backfill Policy

Historical `~/Downloads` scripts are **not** silently treated as original committed scripts.

They may be backfilled only when reconstructable from logs, and must be labeled:

`reconstructed_from_log`

or:

`not_original_download_file`

## Active Analysis Command After Review

```bash
cd /mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE
scripts/idare/analysis/run_idare_label_semantics_minimal_redesigned_task_failure_or_confirmation_analysis.py
```

## Interpretation

The reproducibility layer is now fixed for the active next step.

No analysis or training was executed by this archival command.

## Next Allowed Step

Human review / closeout, then run the committed failure-or-confirmation analysis script.

## Blocked

- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change unrelated to script archival
- deep neural training for redesigned task
- unregistered feature engineering
