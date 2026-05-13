# ROCA-I-DARE Fold-safe High-disagreement Analysis

No EEG/EMG model was trained.

For each LOSO fold, high-disagreement stimuli are selected using train subjects only.

## Aggregate official subset metrics

| target | subset | n_subjects | n_stimuli_per_subject | n_trials | mae | rmse | pearson | spearman | balanced_accuracy | macro_f1 | auroc | mean_abs_deviation | prop_abs_dev_ge_1p0 | prop_abs_dev_ge_2p0 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| valence | top25_train_score_std | 63 | 8 | 504 | 1.0548 | 1.2972 | 0.7378 | 0.6315 | 0.8086 | 0.8043 | 0.8329 | 1.0548 | 0.4246 | 0.1210 |
| valence | top25_train_entropy | 63 | 8 | 504 | 1.0589 | 1.3231 | 0.3319 | 0.2667 | 0.6664 | 0.6727 | 0.7118 | 1.0589 | 0.4167 | 0.1230 |
| arousal | top25_train_score_std | 63 | 8 | 504 | 1.9104 | 2.2740 | 0.3813 | 0.3027 | 0.6498 | 0.6553 | 0.6181 | 1.9104 | 0.7321 | 0.4266 |
| arousal | top25_train_entropy | 63 | 8 | 504 | 1.7458 | 2.0764 | 0.3927 | 0.2674 | 0.6474 | 0.6511 | 0.6044 | 1.7458 | 0.6925 | 0.4048 |


## Interpretation

- These subsets are official/evaluation-safe because they are selected train-only inside each fold.
- Later EEG/EMG probes should report both full-test performance and these fold-safe high-disagreement subsets.
- Subsets selected using test deviation or all-subject disagreement remain exploratory only.
