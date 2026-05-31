# W1C I-DARE EMG Independent Ridge Baseline Report

- status: `complete`
- run_tag: `first_pass`
- registered_runs_executed: `72`
- model: `closed_form_binary_ridge`
- ridge_alpha: `1.0`
- label_policy: `midpoint_as_high`

## Aggregate Results

| Task | Cell | Input | Normalization | Runs | Bal acc mean | Macro F1 mean | Acc mean | Delta vs ref | One-class | Moderate | Strong |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---|
| arousal | C1 | emg | none | 6 | 0.4997 | 0.4352 | 0.5359 | -0.0368 | 0 | false | false |
| arousal | C2 | emg | per_subject_zscore | 6 | 0.4958 | 0.4306 | 0.5308 | -0.0407 | 0 | false | false |
| arousal | C3 | emg | train_fold_standard_scaler | 6 | 0.5017 | 0.4298 | 0.5388 | -0.0348 | 0 | false | false |
| arousal | C4 | emg_bsl | none | 6 | 0.5032 | 0.4678 | 0.5270 | -0.0333 | 0 | false | false |
| arousal | C5 | emg_bsl | per_subject_zscore | 6 | 0.4964 | 0.4584 | 0.5237 | -0.0401 | 0 | false | false |
| arousal | C6 | emg_bsl | train_fold_standard_scaler | 6 | 0.5059 | 0.4625 | 0.5329 | -0.0306 | 0 | false | false |
| valence | C1 | emg | none | 6 | 0.4958 | 0.3841 | 0.5902 | -0.0244 | 0 | false | false |
| valence | C2 | emg | per_subject_zscore | 6 | 0.5190 | 0.4519 | 0.6001 | -0.0012 | 0 | false | false |
| valence | C3 | emg | train_fold_standard_scaler | 6 | 0.4984 | 0.3842 | 0.5937 | -0.0218 | 1 | false | false |
| valence | C4 | emg_bsl | none | 6 | 0.4987 | 0.4025 | 0.5884 | -0.0215 | 0 | false | false |
| valence | C5 | emg_bsl | per_subject_zscore | 6 | 0.5216 | 0.4713 | 0.5950 | 0.0014 | 0 | false | false |
| valence | C6 | emg_bsl | train_fold_standard_scaler | 6 | 0.4929 | 0.3923 | 0.5828 | -0.0273 | 0 | false | false |

## Best Cells By Task

| Task | Best cell | Bal acc mean | Reference | Delta | Moderate | Strong |
|---|---|---:|---:|---:|---|---|
| arousal | C6 | 0.5059 | 0.5365 | -0.0306 | false | false |
| valence | C5 | 0.5216 | 0.5202 | 0.0014 | false | false |

## Interpretation

No moderate pass observed. W1C provides an independent EMG ridge reference but does not justify Wave 2 EMG or fusion-readiness work by itself.

## Not Started

- EEG
- fusion
- pairwise EMG retest
- neural training
- broad hyperparameter search
- DEAP
- cache overwrite
- push to main
