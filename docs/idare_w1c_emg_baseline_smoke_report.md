# W1C I-DARE EMG Independent Ridge Baseline Report

- status: `complete`
- run_tag: `smoke`
- registered_runs_executed: `2`
- model: `closed_form_binary_ridge`
- ridge_alpha: `1.0`
- label_policy: `midpoint_as_high`

## Aggregate Results

| Task | Cell | Input | Normalization | Runs | Bal acc mean | Macro F1 mean | Acc mean | Delta vs ref | One-class | Moderate | Strong |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---|
| arousal | C1 | emg | none | 1 | 0.4786 | 0.4473 | 0.5227 | -0.0579 | 0 | false | false |
| arousal | C2 | emg | per_subject_zscore | 1 | 0.4884 | 0.4484 | 0.5369 | -0.0481 | 0 | false | false |

## Best Cells By Task

| Task | Best cell | Bal acc mean | Reference | Delta | Moderate | Strong |
|---|---|---:|---:|---:|---|---|
| arousal | C2 | 0.4884 | 0.5365 | -0.0481 | false | false |

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
