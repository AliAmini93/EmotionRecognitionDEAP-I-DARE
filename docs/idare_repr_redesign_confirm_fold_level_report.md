# I-DARE Representation Redesign Confirmation Fold-Level Report

Generated: `2026-05-11T18:11:42.238996+00:00`

## Scope

- dataset: `I-DARE`
- modality: `EEG-only`
- task: `arousal-only`
- label_column: `arousal_midpoint_as_high`
- setting: `cross-subject / held-out-subject`
- model_family: `Ridge/classical`
- folds: `same deterministic held-out-subject folds for R0/R2/R3`

## Fold-Level Balanced Accuracy

| Fold | R0 BA | R2 BA | R3 BA | R2-R0 | R3-R0 | R3-R2 | R2/R3 winner |
|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | 0.552288 | 0.488290 | 0.490196 | -0.063998 | -0.062092 | 0.001906 | R3 |
| 2 | 0.470485 | 0.518868 | 0.469946 | 0.048383 | -0.000539 | -0.048922 | R2 |
| 3 | 0.477685 | 0.491774 | 0.484260 | 0.014089 | 0.006575 | -0.007514 | R2 |
| 4 | 0.588875 | 0.607896 | 0.537564 | 0.019022 | -0.051311 | -0.070332 | R2 |
| 5 | 0.557912 | 0.530943 | 0.471144 | -0.026968 | -0.086768 | -0.059800 | R2 |
| 6 | 0.502055 | 0.483288 | 0.502661 | -0.018766 | 0.000607 | 0.019373 | R3 |

## Cell Summary

| Cell | Runs | Mean BA | Std BA | Mean macro F1 | One-class collapses |
|---|---:|---:|---:|---:|---:|
| R0_current_representation_anchor | 6 | 0.524883 | 0.044054 | 0.514062 | 0 |
| R2_train_only_subject_invariant_feature_selection | 6 | 0.520177 | 0.042811 | 0.508797 | 0 |
| R3_diagnostics_first_stable_feature_subset | 6 | 0.492628 | 0.022992 | 0.466861 | 0 |
