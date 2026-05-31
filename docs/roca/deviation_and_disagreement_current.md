# ROCA-I-DARE Deviation and High-disagreement Analysis

No EEG/EMG model was trained.

This report analyzes the residual left by strict LOSO stimulus-only baseline.


## Target: valence

### Stimulus-only metrics

| n | mae | rmse | pearson | spearman | accuracy | balanced_accuracy | macro_f1 | auroc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2016 | 1.0221 | 1.2578 | 0.8663 | 0.8414 | 0.8879 | 0.8922 | 0.8866 | 0.9443 |


### Deviation summary

| n | mean_deviation | std_deviation | mean_abs_deviation | median_abs_deviation | rmse_if_predict_zero_deviation | q75_abs_deviation | q90_abs_deviation | q95_abs_deviation | prop_abs_dev_ge_1p0 | prop_abs_dev_ge_2p0 | positive_deviation_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2016 | -0.0000 | 1.2578 | 1.0221 | 0.8226 | 1.2578 | 1.4355 | 1.9113 | 2.4032 | 0.4251 | 0.0947 | 0.4851 |


### High-disagreement subset metrics

| subset | n_stimuli | n_trials | mae | rmse | pearson | balanced_accuracy | macro_f1 | auroc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| top25_score_std | 8 | 504 | 1.1537 | 1.4392 | 0.6781 | 0.7869 | 0.7809 | 0.7979 |
| top25_entropy | 8 | 504 | 1.0566 | 1.3273 | 0.3960 | 0.6893 | 0.6888 | 0.6880 |
| top25_deviation_rmse | 8 | 504 | 1.1537 | 1.4392 | 0.6781 | 0.7869 | 0.7809 | 0.7979 |


### top25_score_std: top stimuli

| stimulus_id | score_mean | score_std | high_rate | high_low_entropy | mean_abs_deviation | rmse_deviation |
| --- | --- | --- | --- | --- | --- | --- |
| Lake_3 | 6.1905 | 1.6022 | 0.6508 | 0.6470 | 1.3180 | 1.6280 |
| 8370 | 6.5556 | 1.4669 | 0.8095 | 0.4869 | 1.1828 | 1.4905 |
| Tumor_1 | 2.6349 | 1.4287 | 0.0000 | 0.0000 | 1.2770 | 1.4518 |
| Yarn_1 | 5.3333 | 1.3801 | 0.2381 | 0.5489 | 0.9677 | 1.4024 |
| 8492 | 6.6667 | 1.3686 | 0.8095 | 0.4869 | 1.1290 | 1.3907 |
| Flowers_6 | 6.7302 | 1.3593 | 0.7778 | 0.5297 | 1.2053 | 1.3813 |
| 9360 | 4.1587 | 1.3593 | 0.0794 | 0.2772 | 1.0722 | 1.3813 |
| 8080 | 5.8413 | 1.3476 | 0.5397 | 0.6900 | 1.0773 | 1.3694 |


### top25_entropy: top stimuli

| stimulus_id | score_mean | score_std | high_rate | high_low_entropy | mean_abs_deviation | rmse_deviation |
| --- | --- | --- | --- | --- | --- | --- |
| 8080 | 5.8413 | 1.3476 | 0.5397 | 0.6900 | 1.0773 | 1.3694 |
| Pinecone_1 | 5.6349 | 1.1170 | 0.4127 | 0.6778 | 0.8868 | 1.1350 |
| Lake_3 | 6.1905 | 1.6022 | 0.6508 | 0.6470 | 1.3180 | 1.6280 |
| Snow_1 | 6.3968 | 1.2413 | 0.6984 | 0.6122 | 1.1060 | 1.2614 |
| 4220 | 6.4127 | 1.2553 | 0.7460 | 0.5667 | 1.0655 | 1.2755 |
| Yarn_1 | 5.3333 | 1.3801 | 0.2381 | 0.5489 | 0.9677 | 1.4024 |
| Flowers_6 | 6.7302 | 1.3593 | 0.7778 | 0.5297 | 1.2053 | 1.3813 |
| 2491 | 4.7302 | 1.0721 | 0.1905 | 0.4869 | 0.8259 | 1.0894 |


### top25_deviation_rmse: top stimuli

| stimulus_id | score_mean | score_std | high_rate | high_low_entropy | mean_abs_deviation | rmse_deviation |
| --- | --- | --- | --- | --- | --- | --- |
| Lake_3 | 6.1905 | 1.6022 | 0.6508 | 0.6470 | 1.3180 | 1.6280 |
| 8370 | 6.5556 | 1.4669 | 0.8095 | 0.4869 | 1.1828 | 1.4905 |
| Tumor_1 | 2.6349 | 1.4287 | 0.0000 | 0.0000 | 1.2770 | 1.4518 |
| Yarn_1 | 5.3333 | 1.3801 | 0.2381 | 0.5489 | 0.9677 | 1.4024 |
| 8492 | 6.6667 | 1.3686 | 0.8095 | 0.4869 | 1.1290 | 1.3907 |
| Flowers_6 | 6.7302 | 1.3593 | 0.7778 | 0.5297 | 1.2053 | 1.3813 |
| 9360 | 4.1587 | 1.3593 | 0.0794 | 0.2772 | 1.0722 | 1.3813 |
| 8080 | 5.8413 | 1.3476 | 0.5397 | 0.6900 | 1.0773 | 1.3694 |


## Target: arousal

### Stimulus-only metrics

| n | mae | rmse | pearson | spearman | accuracy | balanced_accuracy | macro_f1 | auroc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2016 | 1.5799 | 1.9442 | 0.6344 | 0.5985 | 0.8011 | 0.7686 | 0.7739 | 0.8041 |


### Deviation summary

| n | mean_deviation | std_deviation | mean_abs_deviation | median_abs_deviation | rmse_if_predict_zero_deviation | q75_abs_deviation | q90_abs_deviation | q95_abs_deviation | prop_abs_dev_ge_1p0 | prop_abs_dev_ge_2p0 | positive_deviation_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2016 | -0.0000 | 1.9442 | 1.5799 | 1.4274 | 1.9442 | 2.2097 | 3.0000 | 3.8226 | 0.6523 | 0.3011 | 0.4638 |


### High-disagreement subset metrics

| subset | n_stimuli | n_trials | mae | rmse | pearson | balanced_accuracy | macro_f1 | auroc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| top25_score_std | 8 | 504 | 1.9249 | 2.2920 | 0.3757 | 0.6470 | 0.6519 | 0.6128 |
| top25_entropy | 8 | 504 | 1.7758 | 2.1021 | 0.3000 | 0.5985 | 0.5971 | 0.5065 |
| top25_deviation_rmse | 8 | 504 | 1.9249 | 2.2920 | 0.3757 | 0.6470 | 0.6519 | 0.6128 |


### top25_score_std: top stimuli

| stimulus_id | score_mean | score_std | high_rate | high_low_entropy | mean_abs_deviation | rmse_deviation |
| --- | --- | --- | --- | --- | --- | --- |
| Dog_6 | 3.3492 | 2.4310 | 0.1746 | 0.4631 | 1.9990 | 2.4702 |
| 8080 | 4.8095 | 2.3221 | 0.4286 | 0.6829 | 2.0476 | 2.3596 |
| Lake_12 | 2.9048 | 2.3212 | 0.1746 | 0.4631 | 1.8218 | 2.3586 |
| 8370 | 5.6508 | 2.3036 | 0.6349 | 0.6563 | 1.9990 | 2.3408 |
| 4220 | 4.4444 | 2.2592 | 0.4286 | 0.6829 | 1.9928 | 2.2957 |
| 8492 | 5.9524 | 2.1998 | 0.6508 | 0.6470 | 1.9017 | 2.2353 |
| Garbage_dump_6 | 4.2222 | 2.1115 | 0.2857 | 0.5983 | 1.7921 | 2.1456 |
| Dog_18 | 3.5873 | 2.0751 | 0.1746 | 0.4631 | 1.8454 | 2.1085 |


### top25_entropy: top stimuli

| stimulus_id | score_mean | score_std | high_rate | high_low_entropy | mean_abs_deviation | rmse_deviation |
| --- | --- | --- | --- | --- | --- | --- |
| 8080 | 4.8095 | 2.3221 | 0.4286 | 0.6829 | 2.0476 | 2.3596 |
| 4220 | 4.4444 | 2.2592 | 0.4286 | 0.6829 | 1.9928 | 2.2957 |
| 8370 | 5.6508 | 2.3036 | 0.6349 | 0.6563 | 1.9990 | 2.3408 |
| 8492 | 5.9524 | 2.1998 | 0.6508 | 0.6470 | 1.9017 | 2.2353 |
| Dog_26 | 6.2063 | 1.6824 | 0.6667 | 0.6365 | 1.4009 | 1.7095 |
| Dummy_1 | 6.5714 | 1.9818 | 0.6825 | 0.6249 | 1.7558 | 2.0137 |
| 3170 | 6.6032 | 1.8648 | 0.7143 | 0.5983 | 1.6093 | 1.8949 |
| Miserable_pose_3 | 6.3175 | 1.8329 | 0.7143 | 0.5983 | 1.4992 | 1.8625 |


### top25_deviation_rmse: top stimuli

| stimulus_id | score_mean | score_std | high_rate | high_low_entropy | mean_abs_deviation | rmse_deviation |
| --- | --- | --- | --- | --- | --- | --- |
| Dog_6 | 3.3492 | 2.4310 | 0.1746 | 0.4631 | 1.9990 | 2.4702 |
| 8080 | 4.8095 | 2.3221 | 0.4286 | 0.6829 | 2.0476 | 2.3596 |
| Lake_12 | 2.9048 | 2.3212 | 0.1746 | 0.4631 | 1.8218 | 2.3586 |
| 8370 | 5.6508 | 2.3036 | 0.6349 | 0.6563 | 1.9990 | 2.3408 |
| 4220 | 4.4444 | 2.2592 | 0.4286 | 0.6829 | 1.9928 | 2.2957 |
| 8492 | 5.9524 | 2.1998 | 0.6508 | 0.6470 | 1.9017 | 2.2353 |
| Garbage_dump_6 | 4.2222 | 2.1115 | 0.2857 | 0.5983 | 1.7921 | 2.1456 |
| Dog_18 | 3.5873 | 2.0751 | 0.1746 | 0.4631 | 1.8454 | 2.1085 |


## Interpretation

- The deviation is the remaining error after train-subject stimulus mean is used.
- EEG/EMG probes should try to predict this deviation, not merely reproduce stimulus prior.
- High-disagreement stimuli are where physiology has the clearest chance to add value.
