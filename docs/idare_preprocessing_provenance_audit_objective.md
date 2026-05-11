# I-DARE Preprocessing Provenance Audit Objective

Generated: `2026-05-11T09:18:37+00:00`

## Status

Status: objective created; read-only preprocessing provenance audit only; no training is authorized.

## Scientific Question

Have we missed any essential EEG/EMG preprocessing step for I-DARE, and is the repository EEG 512Hz-to-128Hz downsampling safe enough that prior results remain valid?

## Accepted Paper Context

The I-DARE paper describes the released modalities as processed `.mat` files after TTL alignment and artifact/noise cleaning.

For EEG, the published pipeline includes linked-earlobes re-reference, resampling to 512Hz, 0.1-40Hz zero-phase Butterworth band-pass filtering, adaptive CleanLine filtering at 50Hz and 100Hz, ASR, ICA/RunICA, ICLabel-based artifact component rejection, back-projection, and REST re-reference.

For EMG, the published pipeline includes zero-phase 50Hz/100Hz notch filtering and 10-400Hz zero-phase Butterworth band-pass filtering.

## Why This Objective Exists

The project has produced many controlled negative or weak-positive I-DARE results. Before launching parallel ablation branches, we need to verify that the low EEG/EMG cross-subject performance is not caused by a missing basic preprocessing step or a repository-level downsampling mistake.

The highest-risk repository-level concern is the current EEG cache path: it assumes processed EEG at 512Hz and converts five-second windows to 128Hz. If this downsampling is safe, prior results remain valid from a preprocessing standpoint. If it is not safe, previous EEG results become preprocessing-contingent and reference baselines must be rerun with a corrected cache.

## Authorized Work

- Verify that local/repository EEG and EMG source files match the processed modalities described by the I-DARE paper.
- Audit EEG Fs, channel shape, event timing, and five-second window compatibility.
- Audit EMG processed-source consistency.
- Verify EEG downsampling safety from 512Hz to 128Hz using PSD/alias checks and stride-vs-anti-aliased comparison.
- Produce a prior-result validity matrix.

## Not Authorized

- No model training.
- No new performance claims.
- No overwrite of existing caches.
- No reprocessing raw EEG/EMG with new filters, ICA, ASR, or rereferencing.
- No DEAP.
- No fusion.
- No broad experimental branch launch until this audit is reviewed.

## Required Questions

See `docs/idare_preprocessing_provenance_audit_questions.csv`.

## Input Map

See `docs/idare_preprocessing_provenance_audit_input_map.csv`.

## Scope

See `docs/idare_preprocessing_provenance_audit_scope.csv`.

## Decision Tree

See `docs/idare_preprocessing_provenance_audit_decision_tree.csv`.

## Expected Outputs

See `docs/idare_preprocessing_provenance_audit_expected_outputs.csv`.

## Guardrails

See `docs/idare_preprocessing_provenance_audit_guardrails.csv`.

## Pass Criteria

This objective passes only if the follow-up audit report:

1. Confirms whether the repository uses I-DARE processed EEG/EMG `.mat` files.
2. Confirms whether EEG source Fs=512 is consistent with the paper and cache builder.
3. Quantifies whether simple 512Hz-to-128Hz stride downsampling is safe or materially distorting the signal.
4. Decides whether prior I-DARE EEG/EMG results remain preprocessing-valid.
5. Produces a clear next objective.

## Next Allowed Step

`prepare_reviewed_idare_preprocessing_provenance_audit_command`
