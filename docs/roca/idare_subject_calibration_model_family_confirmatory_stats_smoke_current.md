# I-DARE Subject-Calibration Model-Family Confirmatory Statistics

This report validates whether the 05ae model-family winner beats the locked few-shot reference at paired subject level.

Positive improvement means `locked_reference_RMSE - candidate_RMSE`; positive is good for the candidate.

## Confirmatory verdict

| target | decision | best_candidate_model | best_k_calibration | locked_reference_model | best_rmse | locked_reference_rmse | best_lift_vs_locked_reference_rmse | mean_subject_improvement_locked_minus_model | ci95_low_mean_subject_improvement | signflip_p_one_sided_mean_gt_zero | wins | losses | win_margin | confirmatory_pass | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | WEAK_GO_MODEL_FAMILY_NEEDS_CAUTION | bias_shrink1 | 2 | bias_shrink4 | 1.933934 | 2.061966 | 0.128032 | 0.136182 | -0.017131 | 0.088946 | 5 | 3 | 2 | False | bootstrap CI lower bound is not > 0; sign-flip p is not < 0.05; win margin < 3 |
| valence | WEAK_GO_MODEL_FAMILY_NEEDS_CAUTION | kernel_residual_shrink4 | 8 | bias_shrink4 | 1.277145 | 1.302379 | 0.025234 | 0.037121 | -0.011222 | 0.252387 | 2 | 6 | -4 | False | bootstrap CI lower bound is not > 0; sign-flip p is not < 0.05; win margin < 3 |


## Model-family calibration curve / paired subject statistics

| target | k_calibration | model | locked_reference_model | candidate_rmse_pooled | locked_reference_rmse_pooled | pooled_lift_vs_locked_reference_rmse | lift_vs_stimulus_rmse | mean_subject_improvement_locked_minus_model | ci95_low_mean_subject_improvement | signflip_p_one_sided_mean_gt_zero | wins | losses | win_margin | passes_confirmatory_metric |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | 2 | bias_shrink1 | bias_shrink4 | 1.933934 | 2.061966 | 0.128032 | 0.473961 | 0.136182 | -0.017131 | 0.088946 | 5 | 3 | 2 | False |
| arousal | 1 | bias_shrink1 | bias_shrink4 | 2.115343 | 2.231848 | 0.116504 | 0.300405 | 0.110598 | -0.060049 | 0.131893 | 4 | 4 | 0 | False |
| arousal | 2 | bias_empirical_bayes | bias_shrink4 | 1.955441 | 2.061966 | 0.106525 | 0.452454 | 0.118566 | -0.046117 | 0.118144 | 5 | 3 | 2 | False |
| arousal | 2 | bias_shrink2 | bias_shrink4 | 1.966360 | 2.061966 | 0.095606 | 0.441535 | 0.096056 | 0.010274 | 0.051597 | 5 | 3 | 2 | False |
| arousal | 8 | affine_residual_ridge4 | bias_shrink4 | 1.732570 | 1.815023 | 0.082453 | 0.675277 | 0.111436 | -0.064633 | 0.192140 | 5 | 3 | 2 | False |
| arousal | 1 | bias_shrink2 | bias_shrink4 | 2.154332 | 2.231848 | 0.077515 | 0.261416 | 0.071344 | -0.005513 | 0.078446 | 5 | 3 | 2 | False |
| arousal | 16 | affine_residual_ridge4 | bias_shrink4 | 1.710733 | 1.785587 | 0.074854 | 0.729361 | 0.106703 | -0.042481 | 0.196040 | 5 | 3 | 2 | False |
| arousal | 1 | bias_empirical_bayes | bias_shrink4 | 2.158133 | 2.231848 | 0.073715 | 0.257616 | 0.073759 | -0.123056 | 0.259937 | 4 | 4 | 0 | False |
| arousal | 4 | bias_shrink1 | bias_shrink4 | 1.864870 | 1.936899 | 0.072029 | 0.537357 | 0.080526 | -0.009441 | 0.079296 | 5 | 3 | 2 | False |
| arousal | 16 | affine_residual_ridge1 | bias_shrink4 | 1.720450 | 1.785587 | 0.065137 | 0.719644 | 0.097932 | -0.053148 | 0.203290 | 4 | 4 | 0 | False |
| arousal | 4 | bias_empirical_bayes | bias_shrink4 | 1.872890 | 1.936899 | 0.064009 | 0.529337 | 0.073641 | -0.021896 | 0.098095 | 5 | 3 | 2 | False |
| arousal | 4 | bias_shrink2 | bias_shrink4 | 1.874201 | 1.936899 | 0.062698 | 0.528026 | 0.067006 | 0.006175 | 0.053447 | 5 | 3 | 2 | False |
| arousal | 8 | bias_shrink1 | bias_shrink4 | 1.754790 | 1.815023 | 0.060233 | 0.653056 | 0.066526 | 0.009399 | 0.051397 | 5 | 3 | 2 | False |
| arousal | 8 | bias_mean | bias_shrink4 | 1.757249 | 1.815023 | 0.057774 | 0.650597 | 0.066305 | -0.004313 | 0.075496 | 5 | 3 | 2 | False |
| arousal | 8 | bias_empirical_bayes | bias_shrink4 | 1.757639 | 1.815023 | 0.057384 | 0.650207 | 0.064302 | 0.004650 | 0.051747 | 5 | 3 | 2 | False |
| arousal | 8 | bias_trimmed_mean | bias_shrink4 | 1.763964 | 1.815023 | 0.051060 | 0.643883 | 0.058973 | -0.014526 | 0.099945 | 5 | 3 | 2 | False |
| arousal | 8 | bias_shrink2 | bias_shrink4 | 1.768652 | 1.815023 | 0.046371 | 0.639195 | 0.050059 | 0.010454 | 0.033848 | 5 | 3 | 2 | False |
| arousal | 8 | bias_huber | bias_shrink4 | 1.770063 | 1.815023 | 0.044960 | 0.637784 | 0.053281 | -0.023537 | 0.142893 | 5 | 3 | 2 | False |
| arousal | 8 | affine_residual_ridge1 | bias_shrink4 | 1.775828 | 1.815023 | 0.039195 | 0.632019 | 0.071125 | -0.114782 | 0.263037 | 3 | 5 | -2 | False |
| arousal | 16 | bias_mean | bias_shrink4 | 1.757219 | 1.785587 | 0.028368 | 0.682875 | 0.032902 | -0.006569 | 0.097045 | 5 | 3 | 2 | False |
| arousal | 16 | bias_shrink1 | bias_shrink4 | 1.758647 | 1.785587 | 0.026939 | 0.681446 | 0.030758 | -0.000989 | 0.064247 | 5 | 3 | 2 | False |
| arousal | 16 | bias_empirical_bayes | bias_shrink4 | 1.760431 | 1.785587 | 0.025156 | 0.679663 | 0.029293 | -0.003118 | 0.072496 | 5 | 3 | 2 | False |
| arousal | 16 | bias_shrink2 | bias_shrink4 | 1.764786 | 1.785587 | 0.020800 | 0.675307 | 0.023469 | 0.001311 | 0.058347 | 5 | 3 | 2 | False |
| arousal | 4 | bias_mean | bias_shrink4 | 1.919860 | 1.936899 | 0.017039 | 0.482367 | 0.027785 | -0.067685 | 0.291035 | 5 | 3 | 2 | False |
| arousal | 4 | bias_trimmed_mean | bias_shrink4 | 1.919860 | 1.936899 | 0.017039 | 0.482367 | 0.027785 | -0.067685 | 0.294485 | 5 | 3 | 2 | False |
| arousal | 16 | bias_huber | bias_shrink4 | 1.769541 | 1.785587 | 0.016046 | 0.670553 | 0.021967 | -0.026930 | 0.251537 | 5 | 3 | 2 | False |
| arousal | 16 | bias_trimmed_mean | bias_shrink4 | 1.772623 | 1.785587 | 0.012964 | 0.667471 | 0.019090 | -0.035211 | 0.281236 | 5 | 3 | 2 | False |
| arousal | 8 | bias_median | bias_shrink4 | 1.806675 | 1.815023 | 0.008349 | 0.601172 | 0.015127 | -0.075936 | 0.387181 | 4 | 4 | 0 | False |
| arousal | 16 | bias_median | bias_shrink4 | 1.783577 | 1.785587 | 0.002010 | 0.656517 | 0.004772 | -0.053477 | 0.446378 | 3 | 5 | -2 | False |
| arousal | 16 | bias_shrink4 | bias_shrink4 | 1.785587 | 1.785587 | 0.000000 | 0.654507 | 0.000000 | 0.000000 | 1.000000 | 0 | 0 | 0 | False |
| arousal | 8 | bias_shrink4 | bias_shrink4 | 1.815023 | 1.815023 | 0.000000 | 0.592823 | 0.000000 | 0.000000 | 1.000000 | 0 | 0 | 0 | False |
| arousal | 4 | bias_shrink4 | bias_shrink4 | 1.936899 | 1.936899 | 0.000000 | 0.465328 | 0.000000 | 0.000000 | 1.000000 | 0 | 0 | 0 | False |
| arousal | 2 | bias_shrink4 | bias_shrink4 | 2.061966 | 2.061966 | 0.000000 | 0.345929 | 0.000000 | 0.000000 | 1.000000 | 0 | 0 | 0 | False |
| arousal | 1 | bias_shrink4 | bias_shrink4 | 2.231848 | 2.231848 | 0.000000 | 0.183901 | 0.000000 | 0.000000 | 1.000000 | 0 | 0 | 0 | False |
| arousal | 0 | stimulus_only | stimulus_only | 2.411442 | 2.411442 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 1.000000 | 0 | 0 | 0 | False |
| arousal | 4 | affine_residual_ridge4 | bias_shrink4 | 1.937027 | 1.936899 | -0.000128 | 0.465200 | 0.025581 | -0.150414 | 0.396880 | 4 | 4 | 0 | False |
| arousal | 2 | bias_huber | bias_shrink4 | 2.064740 | 2.061966 | -0.002774 | 0.343155 | 0.018426 | -0.181156 | 0.431678 | 4 | 4 | 0 | False |
| arousal | 2 | bias_mean | bias_shrink4 | 2.064740 | 2.061966 | -0.002774 | 0.343155 | 0.018426 | -0.183341 | 0.439578 | 4 | 4 | 0 | False |
| arousal | 2 | bias_median | bias_shrink4 | 2.064740 | 2.061966 | -0.002774 | 0.343155 | 0.018426 | -0.181156 | 0.434178 | 4 | 4 | 0 | False |
| arousal | 2 | bias_trimmed_mean | bias_shrink4 | 2.064740 | 2.061966 | -0.002774 | 0.343155 | 0.018426 | -0.182788 | 0.432478 | 4 | 4 | 0 | False |
| arousal | 1 | kernel_residual_shrink4 | bias_shrink4 | 2.239343 | 2.231848 | -0.007495 | 0.176406 | -0.005912 | -0.013594 | 0.899105 | 3 | 5 | -2 | False |
| arousal | 2 | affine_residual_ridge4 | bias_shrink4 | 2.074385 | 2.061966 | -0.012419 | 0.333510 | 0.011768 | -0.230579 | 0.454177 | 4 | 4 | 0 | False |
| arousal | 4 | bias_huber | bias_shrink4 | 1.949682 | 1.936899 | -0.012783 | 0.452545 | -0.002079 | -0.106672 | 0.517624 | 4 | 4 | 0 | False |
| arousal | 4 | bias_median | bias_shrink4 | 1.970979 | 1.936899 | -0.034080 | 0.431248 | -0.021880 | -0.133159 | 0.640518 | 3 | 5 | -2 | False |
| arousal | 16 | bias_shrink8 | bias_shrink4 | 1.840283 | 1.785587 | -0.054696 | 0.599811 | -0.058778 | -0.107794 | 0.971951 | 3 | 5 | -2 | False |
| arousal | 16 | kernel_residual_shrink4 | bias_shrink4 | 1.842917 | 1.785587 | -0.057330 | 0.597176 | -0.053151 | -0.112577 | 0.924454 | 2 | 6 | -4 | False |
| arousal | 1 | bias_shrink8 | bias_shrink4 | 2.304331 | 2.231848 | -0.072484 | 0.111417 | -0.065501 | -0.118092 | 0.960402 | 3 | 5 | -2 | False |
| arousal | 2 | kernel_residual_shrink4 | bias_shrink4 | 2.136922 | 2.061966 | -0.074955 | 0.270974 | -0.068992 | -0.128604 | 0.996500 | 1 | 7 | -6 | False |
| arousal | 8 | bias_shrink8 | bias_shrink4 | 1.912808 | 1.815023 | -0.097784 | 0.495039 | -0.098811 | -0.169710 | 0.972801 | 3 | 5 | -2 | False |
| arousal | 8 | kernel_residual_shrink4 | bias_shrink4 | 1.928202 | 1.815023 | -0.113179 | 0.479644 | -0.112051 | -0.192436 | 0.996050 | 1 | 7 | -6 | False |
| arousal | 4 | bias_shrink8 | bias_shrink4 | 2.051237 | 1.936899 | -0.114338 | 0.350990 | -0.112336 | -0.201298 | 0.972301 | 3 | 5 | -2 | False |
| arousal | 2 | bias_shrink8 | bias_shrink4 | 2.178543 | 2.061966 | -0.116576 | 0.229352 | -0.109227 | -0.193968 | 0.972351 | 3 | 5 | -2 | False |
| arousal | 4 | kernel_residual_shrink4 | bias_shrink4 | 2.063471 | 1.936899 | -0.126572 | 0.338756 | -0.122599 | -0.224698 | 0.981851 | 2 | 6 | -4 | False |
| arousal | 4 | affine_residual_ridge1 | bias_shrink4 | 2.078544 | 1.936899 | -0.141645 | 0.323683 | -0.099416 | -0.340106 | 0.778611 | 3 | 5 | -2 | False |
| arousal | 1 | affine_residual_ridge1 | bias_shrink4 | 2.387212 | 2.231848 | -0.155364 | 0.028537 | -0.138708 | -0.501167 | 0.753012 | 4 | 4 | 0 | False |
| arousal | 1 | affine_residual_ridge4 | bias_shrink4 | 2.387212 | 2.231848 | -0.155364 | 0.028537 | -0.138708 | -0.503192 | 0.749163 | 4 | 4 | 0 | False |
| arousal | 1 | bias_huber | bias_shrink4 | 2.387212 | 2.231848 | -0.155364 | 0.028537 | -0.138708 | -0.503192 | 0.756362 | 4 | 4 | 0 | False |
| arousal | 1 | bias_mean | bias_shrink4 | 2.387212 | 2.231848 | -0.155364 | 0.028537 | -0.138708 | -0.505004 | 0.756112 | 4 | 4 | 0 | False |
| arousal | 1 | bias_median | bias_shrink4 | 2.387212 | 2.231848 | -0.155364 | 0.028537 | -0.138708 | -0.504075 | 0.755412 | 4 | 4 | 0 | False |
| arousal | 1 | bias_trimmed_mean | bias_shrink4 | 2.387212 | 2.231848 | -0.155364 | 0.028537 | -0.138708 | -0.500042 | 0.755362 | 4 | 4 | 0 | False |
| arousal | 2 | affine_residual_ridge1 | bias_shrink4 | 2.236925 | 2.061966 | -0.174958 | 0.170970 | -0.142913 | -0.446234 | 0.795960 | 3 | 5 | -2 | False |
| arousal | 1 | stimulus_only | bias_shrink4 | 2.415749 | 2.231848 | -0.183901 | 0.000000 | -0.165778 | -0.283722 | 0.972601 | 3 | 5 | -2 | False |
| arousal | 2 | stimulus_only | bias_shrink4 | 2.407895 | 2.061966 | -0.345929 | 0.000000 | -0.315114 | -0.539917 | 0.984301 | 1 | 7 | -6 | False |
| arousal | 4 | stimulus_only | bias_shrink4 | 2.402227 | 1.936899 | -0.465328 | 0.000000 | -0.431427 | -0.735991 | 0.971701 | 3 | 5 | -2 | False |
| arousal | 8 | stimulus_only | bias_shrink4 | 2.407847 | 1.815023 | -0.592823 | 0.000000 | -0.554642 | -0.899462 | 0.980501 | 2 | 6 | -4 | False |
| arousal | 16 | stimulus_only | bias_shrink4 | 2.440094 | 1.785587 | -0.654507 | 0.000000 | -0.622473 | -1.036405 | 0.974951 | 2 | 6 | -4 | False |
| valence | 8 | kernel_residual_shrink4 | bias_shrink4 | 1.277145 | 1.302379 | 0.025234 | 0.017223 | 0.037121 | -0.011222 | 0.252387 | 2 | 6 | -4 | False |
| valence | 16 | kernel_residual_shrink4 | bias_shrink4 | 1.251556 | 1.275479 | 0.023923 | 0.029599 | 0.039425 | -0.030102 | 0.227789 | 3 | 5 | -2 | False |
| valence | 4 | kernel_residual_shrink4 | bias_shrink4 | 1.283587 | 1.302229 | 0.018642 | 0.005686 | 0.024509 | -0.007998 | 0.182841 | 5 | 3 | 2 | False |
| valence | 4 | bias_shrink8 | bias_shrink4 | 1.287037 | 1.302229 | 0.015192 | 0.002236 | 0.014575 | 0.006922 | 0.011749 | 7 | 1 | 6 | False |
| valence | 4 | bias_empirical_bayes | bias_shrink4 | 1.287101 | 1.302229 | 0.015129 | 0.002173 | 0.014408 | 0.002821 | 0.027299 | 7 | 1 | 6 | False |
| valence | 1 | stimulus_only | bias_shrink4 | 1.290067 | 1.304540 | 0.014473 | 0.000000 | 0.013601 | -0.000714 | 0.064397 | 5 | 3 | 2 | False |
| valence | 2 | kernel_residual_shrink4 | bias_shrink4 | 1.289038 | 1.303303 | 0.014266 | 0.005512 | 0.016924 | -0.001533 | 0.113094 | 5 | 3 | 2 | False |
| valence | 4 | stimulus_only | bias_shrink4 | 1.289274 | 1.302229 | 0.012956 | 0.000000 | 0.011945 | -0.016087 | 0.210339 | 5 | 3 | 2 | False |
| valence | 1 | bias_empirical_bayes | bias_shrink4 | 1.291608 | 1.304540 | 0.012932 | -0.001541 | 0.012321 | 0.003776 | 0.024599 | 6 | 2 | 4 | False |
| valence | 1 | bias_shrink8 | bias_shrink4 | 1.291826 | 1.304540 | 0.012714 | -0.001759 | 0.012143 | 0.005297 | 0.014849 | 6 | 2 | 4 | False |
| valence | 2 | bias_shrink8 | bias_shrink4 | 1.290929 | 1.303303 | 0.012375 | 0.003621 | 0.011742 | -0.000307 | 0.048048 | 6 | 2 | 4 | False |
| valence | 2 | bias_empirical_bayes | bias_shrink4 | 1.292292 | 1.303303 | 0.011012 | 0.002258 | 0.010308 | -0.006658 | 0.128994 | 6 | 2 | 4 | False |
| valence | 8 | bias_empirical_bayes | bias_shrink4 | 1.291896 | 1.302379 | 0.010483 | 0.002472 | 0.010683 | 0.000432 | 0.033348 | 7 | 1 | 6 | False |
| valence | 8 | bias_shrink8 | bias_shrink4 | 1.292055 | 1.302379 | 0.010324 | 0.002313 | 0.010452 | 0.004405 | 0.008000 | 7 | 1 | 6 | False |


## Worst failure subjects for selected candidates

| target | subject_id | k_calibration | model | locked_reference_model | candidate_rmse | locked_rmse | delta_rmse_candidate_minus_locked | improvement_locked_minus_candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | 1 | 2 | bias_shrink1 | bias_shrink4 | 2.524095 | 2.348719 | 0.175376 | -0.175376 |
| arousal | 9 | 2 | bias_shrink1 | bias_shrink4 | 1.872174 | 1.787453 | 0.084720 | -0.084720 |
| arousal | 5 | 2 | bias_shrink1 | bias_shrink4 | 1.722313 | 1.664000 | 0.058313 | -0.058313 |
| arousal | 8 | 2 | bias_shrink1 | bias_shrink4 | 2.133820 | 2.199903 | -0.066084 | 0.066084 |
| arousal | 2 | 2 | bias_shrink1 | bias_shrink4 | 2.084241 | 2.241353 | -0.157112 | 0.157112 |
| arousal | 7 | 2 | bias_shrink1 | bias_shrink4 | 1.231931 | 1.536832 | -0.304902 | 0.304902 |
| arousal | 3 | 2 | bias_shrink1 | bias_shrink4 | 1.397925 | 1.767363 | -0.369438 | 0.369438 |
| arousal | 6 | 2 | bias_shrink1 | bias_shrink4 | 2.170086 | 2.680413 | -0.510327 | 0.510327 |
| valence | 5 | 8 | kernel_residual_shrink4 | bias_shrink4 | 1.584907 | 1.563384 | 0.021523 | -0.021523 |
| valence | 8 | 8 | kernel_residual_shrink4 | bias_shrink4 | 1.260845 | 1.247421 | 0.013424 | -0.013424 |
| valence | 9 | 8 | kernel_residual_shrink4 | bias_shrink4 | 1.299579 | 1.289767 | 0.009812 | -0.009812 |
| valence | 2 | 8 | kernel_residual_shrink4 | bias_shrink4 | 1.560698 | 1.551581 | 0.009116 | -0.009116 |
| valence | 3 | 8 | kernel_residual_shrink4 | bias_shrink4 | 1.306376 | 1.303903 | 0.002473 | -0.002473 |
| valence | 1 | 8 | kernel_residual_shrink4 | bias_shrink4 | 1.208030 | 1.205938 | 0.002092 | -0.002092 |
| valence | 6 | 8 | kernel_residual_shrink4 | bias_shrink4 | 1.006166 | 1.115140 | -0.108974 | 0.108974 |
| valence | 7 | 8 | kernel_residual_shrink4 | bias_shrink4 | 0.802574 | 1.049008 | -0.246434 | 0.246434 |


## Interpretation

- `GO_CONFIRMED_MODEL_FAMILY_CALIBRATION` means the model-family candidate beats the locked few-shot reference in pooled RMSE and paired subject-level tests.

- If confirmed, this should become the next locked personalization baseline. Future physiology, adapters, or deep models should be compared against this baseline, not only against stimulus-only.

- Failure subjects are preserved so we can inspect where the personalization model still regresses.
