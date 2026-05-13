# ROCA-I-DARE Stimulus-Only Baseline

Protocol: strict LOSO. No EEG/EMG model was trained.

## Main metrics

| target | model | n | mae | rmse | pearson | spearman | ccc | accuracy | balanced_accuracy | macro_f1 | auroc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| valence | global_mean | 2016 | 2.1035 | 2.5188 | -0.1497 | -0.1451 | -0.0007 | 0.5759 | 0.5000 | 0.3654 | 0.4159 |
| valence | stimulus_only | 2016 | 1.0221 | 1.2578 | 0.8663 | 0.8414 | 0.8581 | 0.8879 | 0.8922 | 0.8866 | 0.9443 |
| arousal | global_mean | 2016 | 2.1877 | 2.5210 | -0.3948 | -0.3802 | -0.0050 | 0.6592 | 0.5000 | 0.3973 | 0.2940 |
| arousal | stimulus_only | 2016 | 1.5799 | 1.9442 | 0.6344 | 0.5985 | 0.5794 | 0.8011 | 0.7686 | 0.7739 | 0.8041 |
