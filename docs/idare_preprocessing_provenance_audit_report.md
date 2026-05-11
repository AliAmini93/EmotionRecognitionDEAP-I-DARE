# I-DARE Preprocessing Provenance Audit Report

Generated: `2026-05-11T09:24:31+00:00`

## Status

Status: complete; pending human review.

## Executive Diagnosis

Diagnosis: `preprocessing_provenance_incomplete_or_failed`

Decision: `do_not_launch_parallel_wave1_until_provenance_resolved`

Recommendation: `resolve_missing_source_or_metadata_provenance_first`

## Paper Provenance Context

The I-DARE paper describes released processed modalities. For EEG, the expected processed pipeline includes 512Hz resampling, 0.1-40Hz band-pass, CleanLine at 50/100Hz, ASR, ICA/ICLabel, and REST rereference. For EMG, the expected processed pipeline includes notch filtering at 50/100Hz and 10-400Hz band-pass filtering.

## Source Provenance Audit

- EEG source audit pass: `False`
- EMG source audit pass: `True` (source_files)

## EEG Downsampling Audit

| Metric | Median | P95 | Max |
|---|---:|---:|---:|
| energy_ratio_gt_40hz | 0.009551216670462943 | 0.044733002354325306 | 0.14922668906884579 |
| energy_ratio_45_64hz | 0.005463037801216116 | 0.024734696040748416 | 0.08453501105812412 |
| energy_ratio_gt_64hz | 0.0007478957584921714 | 0.002957727187396191 | 0.013845429752532367 |
| line_50hz_energy_ratio | 0.0007767460133490144 | 0.0038338584820536 | 0.013023533016632147 |
| line_100hz_energy_ratio | 7.513466024675825e-06 | 2.4248788364492878e-05 | 8.005211957139097e-05 |
| stride_vs_poly_z_nrmse | 0.02628651966697826 | 0.05189118541646278 | 0.10498896549521787 |
| stride_vs_poly_z_corr | 0.9996545094152827 | 0.9998873364655244 | 0.9999716440136464 |

Downsampling pass: `False`

## Prior Result Validity

Prior results preprocessing-valid: `False`

See `docs/idare_preprocessing_provenance_prior_result_validity.csv` for per-result status.

## Output Files

- `docs/idare_preprocessing_provenance_audit_report.md`
- `docs/idare_preprocessing_provenance_audit_report.json`
- `docs/idare_preprocessing_provenance_eeg_source_audit.csv`
- `docs/idare_preprocessing_provenance_emg_source_audit.csv`
- `docs/idare_preprocessing_provenance_eeg_downsample_audit.csv`
- `docs/idare_preprocessing_provenance_prior_result_validity.csv`
- `scripts/idare/analysis/run_idare_preprocessing_provenance_audit.py`

## Interpretation

The audit could not fully verify that repository inputs match the expected processed I-DARE modalities. New experimental branches should remain blocked until provenance is resolved.

## Next Allowed Step

`prepare_reviewed_idare_preprocessing_provenance_followup_command`
