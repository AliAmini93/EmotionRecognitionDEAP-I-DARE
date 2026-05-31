# ROCA-I-DARE EMG-only Clipped Evaluation

No model was retrained. Predictions are clipped to SAM range `[1, 9]`.

## Main clipped metrics

| target | model | n | mae | rmse | pearson | balanced_accuracy | macro_f1 | auroc | dev_rmse | dev_pearson | dev_sign_acc | pred_dev_std | lift_vs_stimulus_rmse | lift_vs_stimulus_balanced_accuracy | lift_vs_stimulus_auroc | lift_vs_stimulus_dev_rmse | lift_vs_stimulus_dev_pearson |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | stimulus_only | 2016 | 1.5799 | 1.9442 | 0.6344 | 0.7686 | 0.7739 | 0.8161 | 1.9442 |  | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |  |
| arousal | emg_direct_ridge | 2016 | 2.2111 | 2.5581 | -0.0039 | 0.4992 | 0.4149 | 0.4859 | 2.5581 | 0.0158 | 0.4281 | 1.6934 | -0.6139 | -0.2694 | -0.3302 | -0.6139 |  |
| arousal | emg_residual_ridge | 2016 | 1.6142 | 1.9916 | 0.6128 | 0.7649 | 0.7692 | 0.8093 | 1.9916 | -0.0490 | 0.4940 | 0.3455 | -0.0474 | -0.0038 | -0.0068 | -0.0474 |  |
| valence | stimulus_only | 2016 | 1.0221 | 1.2578 | 0.8663 | 0.8796 | 0.8658 | 0.9433 | 1.2578 |  | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |  |
| valence | emg_direct_ridge | 2016 | 2.1212 | 2.5435 | 0.0001 | 0.4916 | 0.4555 | 0.4836 | 2.5435 | 0.0120 | 0.5109 | 2.2258 | -1.2857 | -0.3879 | -0.4597 | -1.2857 |  |
| valence | emg_residual_ridge | 2016 | 1.0218 | 1.2610 | 0.8656 | 0.8796 | 0.8658 | 0.9475 | 1.2610 | 0.0336 | 0.5030 | 0.1423 | -0.0033 | 0.0000 | 0.0042 | -0.0033 |  |


## Fold-safe hard subset clipped metrics

| target | subset | model | n | mae | rmse | balanced_accuracy | auroc | dev_rmse | dev_pearson | dev_sign_acc | pred_dev_std | lift_vs_stimulus_rmse | lift_vs_stimulus_balanced_accuracy | lift_vs_stimulus_auroc | lift_vs_stimulus_dev_rmse | lift_vs_stimulus_dev_pearson |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | top25_train_entropy | stimulus_only | 504 | 1.7458 | 2.0764 | 0.6474 | 0.6232 | 2.0764 |  | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |  |
| arousal | top25_train_entropy | emg_direct_ridge | 504 | 2.3674 | 2.7231 | 0.5010 | 0.4893 | 2.7231 | -0.0278 | 0.4345 | 0.9307 | -0.6467 | -0.1465 | -0.1339 | -0.6467 |  |
| arousal | top25_train_entropy | emg_residual_ridge | 504 | 1.8006 | 2.1399 | 0.6326 | 0.6425 | 2.1399 | -0.0732 | 0.4365 | 0.3832 | -0.0635 | -0.0148 | 0.0193 | -0.0635 |  |
| arousal | top25_train_score_std | stimulus_only | 504 | 1.9104 | 2.2740 | 0.6498 | 0.6700 | 2.2740 |  | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |  |
| arousal | top25_train_score_std | emg_direct_ridge | 504 | 2.1813 | 2.4938 | 0.5026 | 0.4767 | 2.4938 | 0.0271 | 0.4286 | 1.0867 | -0.2199 | -0.1471 | -0.1933 | -0.2199 |  |
| arousal | top25_train_score_std | emg_residual_ridge | 504 | 1.9516 | 2.3274 | 0.6470 | 0.6842 | 2.3274 | -0.0831 | 0.4782 | 0.3419 | -0.0535 | -0.0028 | 0.0142 | -0.0535 |  |
| valence | top25_train_entropy | stimulus_only | 504 | 1.0589 | 1.3231 | 0.5038 | 0.6853 | 1.3231 |  | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |  |
| valence | top25_train_entropy | emg_direct_ridge | 504 | 1.4858 | 1.9658 | 0.5006 | 0.4953 | 1.9658 | 0.0055 | 0.5437 | 0.6377 | -0.6428 | -0.0032 | -0.1900 | -0.6428 |  |
| valence | top25_train_entropy | emg_residual_ridge | 504 | 1.0548 | 1.3255 | 0.5064 | 0.7288 | 1.3255 | 0.0304 | 0.5079 | 0.1219 | -0.0025 | 0.0027 | 0.0435 | -0.0025 |  |
| valence | top25_train_score_std | stimulus_only | 504 | 1.0548 | 1.2972 | 0.7381 | 0.8359 | 1.2972 |  | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |  |
| valence | top25_train_score_std | emg_direct_ridge | 504 | 1.5991 | 2.0544 | 0.4915 | 0.4702 | 2.0544 | 0.0107 | 0.5218 | 1.4623 | -0.7572 | -0.2466 | -0.3657 | -0.7572 |  |
| valence | top25_train_score_std | emg_residual_ridge | 504 | 1.0516 | 1.2963 | 0.7381 | 0.8627 | 1.2963 | 0.0558 | 0.4960 | 0.1272 | 0.0009 | 0.0000 | 0.0267 | 0.0009 |  |
