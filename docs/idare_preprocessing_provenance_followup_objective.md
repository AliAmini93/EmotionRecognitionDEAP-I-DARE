# I-DARE Preprocessing Provenance Follow-up Objective

Generated: `2026-05-11T09:48:21+00:00`

## Status

Status: objective created; read-only follow-up audit only; no training is authorized.

## Scientific Question

Are the failed EEG source audit and downsampling warning real blockers, or were they caused by an audit path bug and conservative downsampling thresholds?

## Accepted Context

The previous preprocessing provenance audit produced diagnosis `preprocessing_provenance_incomplete_or_failed` and decision `do_not_launch_parallel_wave1_until_provenance_resolved`.

The project must not launch Wave 0 or Wave 1 until this follow-up resolves whether the EEG source failure was a path parsing bug and whether current EEG downsampling materially affects prior EEG results.

## Authorized Work

- Fix the EEG source audit path parsing bug by unwrapping singleton tuple groupby keys.
- Print/persist sample real `trial_index` EEG paths and existence checks.
- Compare EEG downsampling methods: current stride, `scipy.signal.resample_poly`, and low-pass-before-decimation.
- Build a temporary read-only mini-cache/manifest only for verification.
- Update prior-result validity status.
- Emit a decision matrix choosing among Wave 0, corrected EEG cache rebuild, or manual source provenance confirmation.

## Not Authorized

- No model training.
- No Wave 0 launch pack.
- No Wave 1 branches.
- No overwrite of current `.cache` arrays or cache indexes.
- No full EEG preprocessing redesign, ICA, artifact rejection, or filtering rebuild.

## Required Questions

See `idare_preprocessing_provenance_followup_questions.csv`.

## Input Map

See `idare_preprocessing_provenance_followup_input_map.csv`.

## Scope

See `idare_preprocessing_provenance_followup_scope.csv`.

## Method Plan

See `idare_preprocessing_provenance_followup_method_plan.csv`.

## Decision Tree

See `idare_preprocessing_provenance_followup_decision_tree.csv`.

## Expected Outputs

See `idare_preprocessing_provenance_followup_expected_outputs.csv`.

## Guardrails

See `idare_preprocessing_provenance_followup_guardrails.csv`.

## Pass Criteria

The follow-up objective is complete only if all expected report artifacts are produced and one of these decisions is explicit:

1. prior EEG results remain preprocessing-valid and Wave 0 can proceed after review;
2. prior EEG results are preprocessing-contingent and corrected EEG downsampling cache is required;
3. source provenance remains unresolved and manual source/path resolution is required.

## Next Allowed Step

`prepare_reviewed_idare_preprocessing_provenance_followup_command`
