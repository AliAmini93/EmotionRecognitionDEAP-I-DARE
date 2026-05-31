# I-DARE Subject-Calibration Model-Family Confirmatory Statistics

This report validates whether the 05ae model-family winner beats the locked few-shot reference at paired subject level.

Positive improvement means `locked_reference_RMSE - candidate_RMSE`; positive is good for the candidate.

## Confirmatory verdict

| target | decision | best_candidate_model | best_k_calibration | locked_reference_model | best_rmse | locked_reference_rmse | best_lift_vs_locked_reference_rmse | mean_subject_improvement_locked_minus_model | ci95_low_mean_subject_improvement | signflip_p_one_sided_mean_gt_zero | wins | losses | win_margin | confirmatory_pass | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | GO_CONFIRMED_MODEL_FAMILY_CALIBRATION | kernel_residual_shrink4 | 16 | bias_shrink4 | 1.657667 | 1.734361 | 0.076694 | 0.076916 | 0.046820 | 0.000050 | 47 | 16 | 31 | True | candidate beats locked few-shot reference in pooled RMSE and paired subject-level confirmatory statistics |
| valence | GO_CONFIRMED_MODEL_FAMILY_CALIBRATION | kernel_residual_shrink4 | 16 | bias_shrink4 | 1.159189 | 1.246118 | 0.086929 | 0.091414 | 0.056769 | 0.000050 | 43 | 20 | 23 | True | candidate beats locked few-shot reference in pooled RMSE and paired subject-level confirmatory statistics |


## Model-family calibration curve / paired subject statistics

| target | k_calibration | model | locked_reference_model | candidate_rmse_pooled | locked_reference_rmse_pooled | pooled_lift_vs_locked_reference_rmse | lift_vs_stimulus_rmse | mean_subject_improvement_locked_minus_model | ci95_low_mean_subject_improvement | signflip_p_one_sided_mean_gt_zero | wins | losses | win_margin | passes_confirmatory_metric |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | 16 | kernel_residual_shrink4 | bias_shrink4 | 1.657667 | 1.734361 | 0.076694 | 0.288276 | 0.076916 | 0.046820 | 0.000050 | 47 | 16 | 31 | True |
| arousal | 16 | affine_residual_ridge4 | bias_shrink4 | 1.669731 | 1.734361 | 0.064630 | 0.276213 | 0.080289 | 0.038941 | 0.000250 | 35 | 28 | 7 | True |
| arousal | 16 | affine_residual_ridge1 | bias_shrink4 | 1.675424 | 1.734361 | 0.058937 | 0.270520 | 0.074858 | 0.032726 | 0.000300 | 34 | 29 | 5 | True |
| arousal | 8 | kernel_residual_shrink4 | bias_shrink4 | 1.732998 | 1.766245 | 0.033247 | 0.210161 | 0.032882 | 0.004208 | 0.016949 | 42 | 21 | 21 | True |
| arousal | 4 | kernel_residual_shrink4 | bias_shrink4 | 1.798294 | 1.803261 | 0.004967 | 0.145603 | 0.006953 | -0.018510 | 0.291135 | 38 | 25 | 13 | False |
| arousal | 16 | bias_shrink4 | bias_shrink4 | 1.734361 | 1.734361 | 0.000000 | 0.211583 | 0.000000 | 0.000000 | 1.000000 | 0 | 0 | 0 | False |
| arousal | 8 | bias_shrink4 | bias_shrink4 | 1.766245 | 1.766245 | 0.000000 | 0.176914 | 0.000000 | 0.000000 | 1.000000 | 0 | 0 | 0 | False |
| arousal | 4 | bias_shrink4 | bias_shrink4 | 1.803261 | 1.803261 | 0.000000 | 0.140636 | 0.000000 | 0.000000 | 1.000000 | 0 | 0 | 0 | False |
| arousal | 2 | bias_shrink4 | bias_shrink4 | 1.848195 | 1.848195 | 0.000000 | 0.095374 | 0.000000 | 0.000000 | 1.000000 | 0 | 0 | 0 | False |
| arousal | 1 | bias_shrink4 | bias_shrink4 | 1.890484 | 1.890484 | 0.000000 | 0.054084 | 0.000000 | 0.000000 | 1.000000 | 0 | 0 | 0 | False |
| arousal | 0 | stimulus_only | stimulus_only | 1.944205 | 1.944205 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 1.000000 | 0 | 0 | 0 | False |
| arousal | 16 | bias_empirical_bayes | bias_shrink4 | 1.734540 | 1.734361 | -0.000179 | 0.211404 | 0.000578 | -0.001556 | 0.317834 | 21 | 42 | -21 | False |
| arousal | 1 | kernel_residual_shrink4 | bias_shrink4 | 1.890702 | 1.890484 | -0.000217 | 0.053866 | 0.000927 | -0.002803 | 0.309635 | 40 | 23 | 17 | False |
| arousal | 16 | bias_shrink2 | bias_shrink4 | 1.734584 | 1.734361 | -0.000223 | 0.211360 | 0.000932 | -0.002628 | 0.324384 | 19 | 44 | -25 | False |
| arousal | 4 | bias_empirical_bayes | bias_shrink4 | 1.804173 | 1.803261 | -0.000912 | 0.139724 | 0.000250 | -0.007897 | 0.475126 | 21 | 42 | -21 | False |
| arousal | 8 | bias_empirical_bayes | bias_shrink4 | 1.767369 | 1.766245 | -0.001124 | 0.175790 | 0.000287 | -0.004777 | 0.453677 | 22 | 41 | -19 | False |
| arousal | 4 | bias_shrink2 | bias_shrink4 | 1.804659 | 1.803261 | -0.001398 | 0.139238 | 0.000569 | -0.014434 | 0.478226 | 19 | 44 | -25 | False |
| arousal | 8 | bias_shrink2 | bias_shrink4 | 1.767765 | 1.766245 | -0.001520 | 0.175394 | 0.000703 | -0.007973 | 0.446878 | 19 | 44 | -25 | False |
| arousal | 2 | kernel_residual_shrink4 | bias_shrink4 | 1.850254 | 1.848195 | -0.002059 | 0.093315 | 0.000788 | -0.014438 | 0.459177 | 40 | 23 | 17 | False |
| arousal | 16 | bias_shrink1 | bias_shrink4 | 1.737064 | 1.734361 | -0.002703 | 0.208879 | -0.001056 | -0.005829 | 0.646718 | 18 | 45 | -27 | False |
| arousal | 2 | bias_empirical_bayes | bias_shrink4 | 1.851054 | 1.848195 | -0.002859 | 0.092515 | -0.002929 | -0.012715 | 0.705315 | 20 | 43 | -23 | False |
| arousal | 8 | affine_residual_ridge4 | bias_shrink4 | 1.769557 | 1.766245 | -0.003312 | 0.173602 | 0.017384 | -0.031429 | 0.259637 | 24 | 39 | -15 | False |
| arousal | 1 | bias_empirical_bayes | bias_shrink4 | 1.894475 | 1.890484 | -0.003991 | 0.050093 | -0.005730 | -0.014100 | 0.894705 | 21 | 42 | -21 | False |
| arousal | 2 | bias_shrink2 | bias_shrink4 | 1.853122 | 1.848195 | -0.004927 | 0.090447 | -0.005242 | -0.025432 | 0.678416 | 18 | 45 | -27 | False |
| arousal | 1 | bias_shrink2 | bias_shrink4 | 1.897816 | 1.890484 | -0.007332 | 0.046752 | -0.011390 | -0.029254 | 0.872456 | 16 | 47 | -31 | False |
| arousal | 16 | bias_mean | bias_shrink4 | 1.741925 | 1.734361 | -0.007563 | 0.204019 | -0.005584 | -0.010940 | 0.965652 | 13 | 50 | -37 | False |
| arousal | 16 | bias_shrink8 | bias_shrink4 | 1.743440 | 1.734361 | -0.009079 | 0.202504 | -0.011006 | -0.020972 | 0.989951 | 36 | 27 | 9 | False |
| arousal | 8 | bias_shrink1 | bias_shrink4 | 1.775915 | 1.766245 | -0.009670 | 0.167244 | -0.006067 | -0.018812 | 0.802460 | 16 | 47 | -31 | False |
| arousal | 1 | bias_shrink8 | bias_shrink4 | 1.905049 | 1.890484 | -0.014565 | 0.039518 | -0.009815 | -0.023589 | 0.927004 | 37 | 26 | 11 | False |
| arousal | 8 | bias_shrink8 | bias_shrink4 | 1.782399 | 1.766245 | -0.016155 | 0.160760 | -0.017646 | -0.035031 | 0.981551 | 39 | 24 | 15 | False |
| arousal | 16 | bias_huber | bias_shrink4 | 1.751849 | 1.734361 | -0.017488 | 0.194095 | -0.014576 | -0.021462 | 0.999900 | 14 | 49 | -35 | False |
| arousal | 4 | bias_shrink1 | bias_shrink4 | 1.823701 | 1.803261 | -0.020439 | 0.120197 | -0.016066 | -0.039360 | 0.886256 | 17 | 46 | -29 | False |
| arousal | 2 | bias_shrink8 | bias_shrink4 | 1.869968 | 1.848195 | -0.021773 | 0.073601 | -0.017790 | -0.037580 | 0.964952 | 38 | 25 | 13 | False |
| arousal | 4 | bias_shrink8 | bias_shrink4 | 1.826762 | 1.803261 | -0.023501 | 0.117135 | -0.022266 | -0.044133 | 0.983751 | 37 | 26 | 11 | False |
| arousal | 16 | bias_trimmed_mean | bias_shrink4 | 1.757982 | 1.734361 | -0.023621 | 0.187961 | -0.020286 | -0.027811 | 1.000000 | 12 | 51 | -39 | False |
| arousal | 8 | bias_mean | bias_shrink4 | 1.794000 | 1.766245 | -0.027756 | 0.149159 | -0.023001 | -0.037887 | 0.997150 | 15 | 48 | -33 | False |
| arousal | 8 | affine_residual_ridge1 | bias_shrink4 | 1.806901 | 1.766245 | -0.040656 | 0.136258 | -0.017837 | -0.068716 | 0.737013 | 20 | 43 | -23 | False |
| arousal | 8 | bias_trimmed_mean | bias_shrink4 | 1.809499 | 1.766245 | -0.043255 | 0.133659 | -0.037437 | -0.053583 | 0.999900 | 11 | 52 | -41 | False |
| arousal | 2 | bias_shrink1 | bias_shrink4 | 1.893410 | 1.848195 | -0.045215 | 0.050159 | -0.042146 | -0.078305 | 0.981451 | 16 | 47 | -31 | False |
| arousal | 8 | bias_huber | bias_shrink4 | 1.812678 | 1.766245 | -0.046434 | 0.130481 | -0.040525 | -0.057093 | 1.000000 | 11 | 52 | -41 | False |
| arousal | 16 | bias_median | bias_shrink4 | 1.783022 | 1.734361 | -0.048661 | 0.162922 | -0.043191 | -0.057448 | 1.000000 | 10 | 53 | -43 | False |
| arousal | 1 | stimulus_only | bias_shrink4 | 1.944568 | 1.890484 | -0.054084 | 0.000000 | -0.041458 | -0.071983 | 0.997600 | 32 | 31 | 1 | False |
| arousal | 1 | bias_shrink1 | bias_shrink4 | 1.955310 | 1.890484 | -0.064826 | -0.010742 | -0.068822 | -0.107833 | 0.998900 | 13 | 50 | -37 | False |
| arousal | 4 | bias_mean | bias_shrink4 | 1.880941 | 1.803261 | -0.077680 | 0.062956 | -0.070789 | -0.099277 | 1.000000 | 10 | 53 | -43 | False |
| arousal | 4 | bias_trimmed_mean | bias_shrink4 | 1.880941 | 1.803261 | -0.077680 | 0.062956 | -0.070789 | -0.099341 | 0.999950 | 10 | 53 | -43 | False |
| arousal | 8 | bias_median | bias_shrink4 | 1.849686 | 1.766245 | -0.083442 | 0.093472 | -0.075439 | -0.097057 | 1.000000 | 9 | 54 | -45 | False |
| arousal | 2 | stimulus_only | bias_shrink4 | 1.943569 | 1.848195 | -0.095374 | 0.000000 | -0.078926 | -0.129404 | 0.999650 | 29 | 34 | -5 | False |
| arousal | 4 | bias_huber | bias_shrink4 | 1.920696 | 1.803261 | -0.117434 | 0.023202 | -0.107982 | -0.139537 | 1.000000 | 7 | 56 | -49 | False |
| arousal | 4 | affine_residual_ridge4 | bias_shrink4 | 1.921985 | 1.803261 | -0.118723 | 0.021913 | -0.096492 | -0.154216 | 0.998850 | 15 | 48 | -33 | False |
| arousal | 4 | bias_median | bias_shrink4 | 1.940625 | 1.803261 | -0.137364 | 0.003272 | -0.126822 | -0.160910 | 1.000000 | 7 | 56 | -49 | False |
| arousal | 4 | stimulus_only | bias_shrink4 | 1.943898 | 1.803261 | -0.140636 | 0.000000 | -0.122728 | -0.194200 | 0.999950 | 28 | 35 | -7 | False |
| arousal | 8 | stimulus_only | bias_shrink4 | 1.943159 | 1.766245 | -0.176914 | 0.000000 | -0.159628 | -0.247313 | 1.000000 | 27 | 36 | -9 | False |
| arousal | 16 | stimulus_only | bias_shrink4 | 1.945944 | 1.734361 | -0.211583 | 0.000000 | -0.196031 | -0.291927 | 1.000000 | 25 | 38 | -13 | False |
| arousal | 2 | bias_huber | bias_shrink4 | 2.070022 | 1.848195 | -0.221827 | -0.126453 | -0.210162 | -0.264009 | 1.000000 | 7 | 56 | -49 | False |
| arousal | 2 | bias_mean | bias_shrink4 | 2.070022 | 1.848195 | -0.221827 | -0.126453 | -0.210162 | -0.263878 | 1.000000 | 7 | 56 | -49 | False |
| arousal | 2 | bias_median | bias_shrink4 | 2.070022 | 1.848195 | -0.221827 | -0.126453 | -0.210162 | -0.264486 | 1.000000 | 7 | 56 | -49 | False |
| arousal | 2 | bias_trimmed_mean | bias_shrink4 | 2.070022 | 1.848195 | -0.221827 | -0.126453 | -0.210162 | -0.263770 | 1.000000 | 7 | 56 | -49 | False |
| arousal | 2 | affine_residual_ridge4 | bias_shrink4 | 2.128135 | 1.848195 | -0.279940 | -0.184566 | -0.260918 | -0.328363 | 1.000000 | 9 | 54 | -45 | False |
| arousal | 4 | affine_residual_ridge1 | bias_shrink4 | 2.097438 | 1.803261 | -0.294177 | -0.153541 | -0.257778 | -0.334878 | 1.000000 | 10 | 53 | -43 | False |
| arousal | 1 | affine_residual_ridge1 | bias_shrink4 | 2.394415 | 1.890484 | -0.503931 | -0.449847 | -0.491895 | -0.574233 | 1.000000 | 6 | 57 | -51 | False |
| arousal | 1 | affine_residual_ridge4 | bias_shrink4 | 2.394415 | 1.890484 | -0.503931 | -0.449847 | -0.491895 | -0.573633 | 1.000000 | 6 | 57 | -51 | False |
| arousal | 1 | bias_huber | bias_shrink4 | 2.394415 | 1.890484 | -0.503931 | -0.449847 | -0.491895 | -0.574212 | 1.000000 | 6 | 57 | -51 | False |
| arousal | 1 | bias_mean | bias_shrink4 | 2.394415 | 1.890484 | -0.503931 | -0.449847 | -0.491895 | -0.573428 | 1.000000 | 6 | 57 | -51 | False |
| arousal | 1 | bias_median | bias_shrink4 | 2.394415 | 1.890484 | -0.503931 | -0.449847 | -0.491895 | -0.574409 | 1.000000 | 6 | 57 | -51 | False |
| arousal | 1 | bias_trimmed_mean | bias_shrink4 | 2.394415 | 1.890484 | -0.503931 | -0.449847 | -0.491895 | -0.574043 | 1.000000 | 6 | 57 | -51 | False |
| arousal | 2 | affine_residual_ridge1 | bias_shrink4 | 2.387284 | 1.848195 | -0.539089 | -0.443715 | -0.505675 | -0.595266 | 1.000000 | 6 | 57 | -51 | False |
| valence | 16 | kernel_residual_shrink4 | bias_shrink4 | 1.159189 | 1.246118 | 0.086929 | 0.100024 | 0.091414 | 0.056769 | 0.000050 | 43 | 20 | 23 | True |
| valence | 16 | affine_residual_ridge4 | bias_shrink4 | 1.174206 | 1.246118 | 0.071912 | 0.085007 | 0.079781 | 0.038698 | 0.000100 | 37 | 26 | 11 | True |
| valence | 16 | affine_residual_ridge1 | bias_shrink4 | 1.176348 | 1.246118 | 0.069770 | 0.082864 | 0.077754 | 0.035932 | 0.000250 | 36 | 27 | 9 | True |
| valence | 8 | kernel_residual_shrink4 | bias_shrink4 | 1.186439 | 1.253277 | 0.066838 | 0.069952 | 0.067905 | 0.041374 | 0.000050 | 45 | 18 | 27 | True |
| valence | 4 | kernel_residual_shrink4 | bias_shrink4 | 1.216630 | 1.264810 | 0.048180 | 0.041235 | 0.047654 | 0.029232 | 0.000050 | 46 | 17 | 29 | True |
| valence | 2 | kernel_residual_shrink4 | bias_shrink4 | 1.239173 | 1.268266 | 0.029092 | 0.018476 | 0.028238 | 0.017940 | 0.000050 | 50 | 13 | 37 | True |
| valence | 2 | bias_empirical_bayes | bias_shrink4 | 1.254496 | 1.268266 | 0.013769 | 0.003153 | 0.013197 | 0.007515 | 0.000100 | 50 | 13 | 37 | False |
| valence | 4 | bias_empirical_bayes | bias_shrink4 | 1.251254 | 1.264810 | 0.013556 | 0.006611 | 0.012976 | 0.007134 | 0.000050 | 50 | 13 | 37 | False |
| valence | 2 | bias_shrink8 | bias_shrink4 | 1.255237 | 1.268266 | 0.013029 | 0.002413 | 0.012461 | 0.008018 | 0.000050 | 53 | 10 | 43 | False |
| valence | 1 | kernel_residual_shrink4 | bias_shrink4 | 1.256139 | 1.268932 | 0.012794 | 0.001733 | 0.012124 | 0.008227 | 0.000050 | 49 | 14 | 35 | False |
| valence | 4 | bias_shrink8 | bias_shrink4 | 1.252124 | 1.264810 | 0.012686 | 0.005741 | 0.012133 | 0.007858 | 0.000050 | 51 | 12 | 39 | False |
| valence | 1 | bias_empirical_bayes | bias_shrink4 | 1.257167 | 1.268932 | 0.011765 | 0.000705 | 0.011358 | 0.007585 | 0.000050 | 51 | 12 | 39 | False |
| valence | 1 | bias_shrink8 | bias_shrink4 | 1.257863 | 1.268932 | 0.011070 | 0.000009 | 0.010663 | 0.007671 | 0.000050 | 52 | 11 | 41 | False |
| valence | 1 | stimulus_only | bias_shrink4 | 1.257872 | 1.268932 | 0.011061 | 0.000000 | 0.010596 | 0.003549 | 0.001400 | 47 | 16 | 31 | False |


## Worst failure subjects for selected candidates

| target | subject_id | k_calibration | model | locked_reference_model | candidate_rmse | locked_rmse | delta_rmse_candidate_minus_locked | improvement_locked_minus_candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | 42 | 16 | kernel_residual_shrink4 | bias_shrink4 | 1.924969 | 1.747650 | 0.177319 | -0.177319 |
| arousal | 2 | 16 | kernel_residual_shrink4 | bias_shrink4 | 1.850398 | 1.697352 | 0.153046 | -0.153046 |
| arousal | 14 | 16 | kernel_residual_shrink4 | bias_shrink4 | 1.093865 | 0.944248 | 0.149617 | -0.149617 |
| arousal | 55 | 16 | kernel_residual_shrink4 | bias_shrink4 | 1.215329 | 1.107459 | 0.107870 | -0.107870 |
| arousal | 40 | 16 | kernel_residual_shrink4 | bias_shrink4 | 2.915243 | 2.820307 | 0.094936 | -0.094936 |
| arousal | 20 | 16 | kernel_residual_shrink4 | bias_shrink4 | 1.402426 | 1.322085 | 0.080341 | -0.080341 |
| arousal | 23 | 16 | kernel_residual_shrink4 | bias_shrink4 | 1.293846 | 1.223860 | 0.069986 | -0.069986 |
| arousal | 5 | 16 | kernel_residual_shrink4 | bias_shrink4 | 1.650657 | 1.595285 | 0.055372 | -0.055372 |
| arousal | 26 | 16 | kernel_residual_shrink4 | bias_shrink4 | 1.860844 | 1.805923 | 0.054921 | -0.054921 |
| arousal | 1 | 16 | kernel_residual_shrink4 | bias_shrink4 | 2.027675 | 1.980213 | 0.047462 | -0.047462 |
| arousal | 64 | 16 | kernel_residual_shrink4 | bias_shrink4 | 1.592448 | 1.562699 | 0.029748 | -0.029748 |
| arousal | 29 | 16 | kernel_residual_shrink4 | bias_shrink4 | 1.425203 | 1.396413 | 0.028790 | -0.028790 |
| arousal | 30 | 16 | kernel_residual_shrink4 | bias_shrink4 | 1.018774 | 0.995522 | 0.023252 | -0.023252 |
| arousal | 32 | 16 | kernel_residual_shrink4 | bias_shrink4 | 1.331702 | 1.320132 | 0.011570 | -0.011570 |
| arousal | 38 | 16 | kernel_residual_shrink4 | bias_shrink4 | 1.428552 | 1.419320 | 0.009232 | -0.009232 |
| arousal | 34 | 16 | kernel_residual_shrink4 | bias_shrink4 | 1.338964 | 1.337417 | 0.001547 | -0.001547 |
| arousal | 18 | 16 | kernel_residual_shrink4 | bias_shrink4 | 2.188025 | 2.191178 | -0.003153 | 0.003153 |
| arousal | 3 | 16 | kernel_residual_shrink4 | bias_shrink4 | 1.458800 | 1.463903 | -0.005103 | 0.005103 |
| arousal | 15 | 16 | kernel_residual_shrink4 | bias_shrink4 | 1.688290 | 1.695198 | -0.006908 | 0.006908 |
| arousal | 53 | 16 | kernel_residual_shrink4 | bias_shrink4 | 1.094049 | 1.105335 | -0.011286 | 0.011286 |
| valence | 18 | 16 | kernel_residual_shrink4 | bias_shrink4 | 1.907951 | 1.845915 | 0.062036 | -0.062036 |
| valence | 1 | 16 | kernel_residual_shrink4 | bias_shrink4 | 1.209997 | 1.155384 | 0.054613 | -0.054613 |
| valence | 29 | 16 | kernel_residual_shrink4 | bias_shrink4 | 0.933707 | 0.886673 | 0.047034 | -0.047034 |
| valence | 27 | 16 | kernel_residual_shrink4 | bias_shrink4 | 1.384442 | 1.339347 | 0.045096 | -0.045096 |
| valence | 44 | 16 | kernel_residual_shrink4 | bias_shrink4 | 1.484527 | 1.440200 | 0.044327 | -0.044327 |
| valence | 34 | 16 | kernel_residual_shrink4 | bias_shrink4 | 1.155715 | 1.121317 | 0.034398 | -0.034398 |
| valence | 20 | 16 | kernel_residual_shrink4 | bias_shrink4 | 0.984123 | 0.949980 | 0.034143 | -0.034143 |
| valence | 17 | 16 | kernel_residual_shrink4 | bias_shrink4 | 1.234319 | 1.203064 | 0.031256 | -0.031256 |
| valence | 23 | 16 | kernel_residual_shrink4 | bias_shrink4 | 1.092541 | 1.066119 | 0.026422 | -0.026422 |
| valence | 10 | 16 | kernel_residual_shrink4 | bias_shrink4 | 1.064261 | 1.043222 | 0.021039 | -0.021039 |
| valence | 63 | 16 | kernel_residual_shrink4 | bias_shrink4 | 1.188905 | 1.170877 | 0.018028 | -0.018028 |
| valence | 62 | 16 | kernel_residual_shrink4 | bias_shrink4 | 1.211369 | 1.196375 | 0.014994 | -0.014994 |
| valence | 58 | 16 | kernel_residual_shrink4 | bias_shrink4 | 1.010526 | 0.996866 | 0.013660 | -0.013660 |
| valence | 5 | 16 | kernel_residual_shrink4 | bias_shrink4 | 1.555610 | 1.542672 | 0.012937 | -0.012937 |
| valence | 47 | 16 | kernel_residual_shrink4 | bias_shrink4 | 1.911000 | 1.898069 | 0.012931 | -0.012931 |
| valence | 53 | 16 | kernel_residual_shrink4 | bias_shrink4 | 0.955053 | 0.944417 | 0.010636 | -0.010636 |
| valence | 26 | 16 | kernel_residual_shrink4 | bias_shrink4 | 1.579526 | 1.569265 | 0.010260 | -0.010260 |
| valence | 32 | 16 | kernel_residual_shrink4 | bias_shrink4 | 1.035544 | 1.028485 | 0.007059 | -0.007059 |
| valence | 45 | 16 | kernel_residual_shrink4 | bias_shrink4 | 0.958871 | 0.954549 | 0.004322 | -0.004322 |
| valence | 3 | 16 | kernel_residual_shrink4 | bias_shrink4 | 1.219576 | 1.216344 | 0.003232 | -0.003232 |


## Interpretation

- `GO_CONFIRMED_MODEL_FAMILY_CALIBRATION` means the model-family candidate beats the locked few-shot reference in pooled RMSE and paired subject-level tests.

- If confirmed, this should become the next locked personalization baseline. Future physiology, adapters, or deep models should be compared against this baseline, not only against stimulus-only.

- Failure subjects are preserved so we can inspect where the personalization model still regresses.
