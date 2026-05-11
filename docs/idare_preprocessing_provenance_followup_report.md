# I-DARE Preprocessing Provenance Follow-up Report

## Status

Status: complete; pending human review.

## Executive Diagnosis

- Diagnosis: `preprocessing_provenance_followup_resolved_prior_results_valid`
- Decision: `proceed_to_wave0_after_human_review`
- Recommendation: `create_wave0_parallel_launch_pack_after_review`
- Recommended next objective: `idare_wave0_parallel_launch_pack_objective`
- Corrected EEG source pass: `True`
- Downsample pass: `True`
- Prior results preprocessing valid: `True`

## Path Bug Follow-up

The original audit likely failed EEG source provenance because a singleton tuple groupby key was converted directly to a `Path`. This follow-up unwraps singleton tuple keys before path construction and persists normalized sample paths.

## Corrected EEG Source Audit

- Corrected source rows: `63`
- Passing source rows: `63`

## Downsampling Method Comparison

Compared current stride decimation, `scipy.signal.resample_poly`, and low-pass-before-decimation.

| Metric | Median | P05 | P95 | Min | Max |
|---|---:|---:|---:|---:|---:|
| energy_ratio_gt40hz | 0.01412713404357471 | 0.0045975434025149545 | 0.057443823337142215 | 0.0015274138973928677 | 0.1535801795570032 |
| energy_ratio_gt64hz | 0.00047679731158205697 | 0.000124807786849428 | 0.0031531069446915985 | 4.213831592865966e-05 | 0.014020398991451412 |
| stride_vs_poly_z_nrmse | 0.026286519667004547 | 0.015010895564899474 | 0.051891185416514676 | 0.00753073520373818 | 0.10498896549532287 |
| stride_vs_poly_z_corr | 0.9996545094152827 | 0.9986536523012751 | 0.9998873364655244 | 0.9944886585621112 | 0.9999716440136464 |
| stride_vs_lowpass_z_nrmse | 0.02109334841453932 | 0.009789654779520294 | 0.05753957917883374 | 0.003912964805884928 | 0.12348069257253186 |
| stride_vs_lowpass_z_corr | 0.9997775352464153 | 0.9983445983417626 | 0.9999520813259181 | 0.992376259280904 | 0.9999923443532135 |
| poly_vs_lowpass_z_nrmse | 0.02049513509541634 | 0.01124871074682239 | 0.03510873378173781 | 0.004501273839953958 | 0.05625240390247909 |
| poly_vs_lowpass_z_corr | 0.9997899747186084 | 0.9993836876303925 | 0.9999367332532558 | 0.9984178335275963 | 0.9999898692669088 |

## Mini-cache

- Temporary mini-cache path: `/tmp/idare_preprocessing_followup_mini_cache_1778493594.npz`
- Temporary mini-cache rows: `24`
- Cache overwrite: `False`

## Decision Matrix

| Check | Pass | Decision impact |
|---|---:|---|
| corrected_eeg_source_audit | True | source provenance unblocked |
| downsample_stride_vs_resample_poly_and_lowpass | True | current EEG cache acceptable for prior-result validity |
| temporary_mini_cache | True | mini-cache verification path works without overwriting current cache |
| prior_result_validity | True | prior results valid from preprocessing standpoint |
| manual_source_provenance_needed | True | manual source check not required by repository evidence |

## Interpretation

The corrected EEG source audit passed and current stride downsampling is not materially different from anti-aliased alternatives under declared thresholds. Prior EEG/EMG I-DARE results can remain valid from a preprocessing/downsampling standpoint, pending human review.

## Next Allowed Step

`prepare_reviewed_idare_wave0_parallel_launch_pack_objective`
