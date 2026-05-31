# I-DARE Few-shot Calibration Confirmatory Statistics

This report validates whether the few-shot subject-calibration result from 05aa is reliable at subject level, not only in pooled repeated predictions.

Positive improvement means `stimulus_only RMSE - fewshot_model RMSE`; positive is good for few-shot calibration.

## Decision rule

`GO_CONFIRMED_FEWSHOT_SUBJECT_CALIBRATION` requires pooled RMSE lift >= 0.02, positive paired mean subject improvement, bootstrap CI lower bound > 0, one-sided sign-flip p < 0.05, and subject win margin >= 3.

## Verdict

| target | decision | best_model | best_k_calibration | best_rmse | best_lift_vs_stimulus_rmse | mean_subject_rmse_improvement | ci95_low_mean_subject_rmse_improvement | signflip_p_one_sided_mean_gt_zero | rmse_wins | rmse_losses | rmse_win_margin | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | GO_CONFIRMED_FEWSHOT_SUBJECT_CALIBRATION | stimulus_plus_fewshot_bias_shrink4 | 16 | 1.733828 | 0.210979 | 0.194921 | 0.110752 | 0.000050 | 37 | 26 | 11 | pooled lift, paired subject improvement, bootstrap CI, sign-flip test, and win margin all pass |
| valence | WEAK_GO_FEWSHOT_NEEDS_CAUTION | stimulus_plus_fewshot_bias_shrink4 | 16 | 1.241848 | 0.014743 | 0.016499 | -0.001030 | 0.044148 | 27 | 36 | -9 | pooled lift < 0.02; bootstrap CI lower bound is not > 0; win margin < 3 |


## Calibration curve summary

| target | k_calibration | model | rmse | lift_vs_stimulus_rmse | mean_improvement_stimulus_minus_model | ci95_low_mean_improvement | signflip_p_one_sided_mean_gt_zero | wins | losses | win_margin | passes_confirmatory_metric |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 1.733828 | 0.210979 | 0.194921 | 0.110752 | 0.000050 | 37.000000 | 26.000000 | 11.000000 | 1 |
| arousal | 16 | stimulus_plus_fewshot_bias | 1.741675 | 0.203132 | 0.188877 | 0.098870 | 0.000050 | 36.000000 | 27.000000 | 9.000000 | 1 |
| arousal | 8 | stimulus_plus_fewshot_bias_shrink4 | 1.765094 | 0.178731 | 0.161928 | 0.085049 | 0.000050 | 37.000000 | 26.000000 | 11.000000 | 1 |
| arousal | 8 | stimulus_plus_fewshot_bias | 1.793275 | 0.150550 | 0.138769 | 0.048747 | 0.002300 | 28.000000 | 35.000000 | -7.000000 | 0 |
| arousal | 4 | stimulus_plus_fewshot_bias_shrink4 | 1.806305 | 0.137786 | 0.119644 | 0.057433 | 0.000250 | 35.000000 | 28.000000 | 7.000000 | 1 |
| arousal | 2 | stimulus_plus_fewshot_bias_shrink4 | 1.852176 | 0.092477 | 0.075864 | 0.031916 | 0.000400 | 33.000000 | 30.000000 | 3.000000 | 1 |
| arousal | 1 | stimulus_plus_fewshot_bias_shrink4 | 1.885624 | 0.057956 | 0.046705 | 0.018700 | 0.001250 | 30.000000 | 33.000000 | -3.000000 | 0 |
| arousal | 4 | stimulus_plus_fewshot_bias | 1.886481 | 0.057609 | 0.047875 | -0.041388 | 0.181141 | 23.000000 | 40.000000 | -17.000000 | 0 |
| arousal | 0 | stimulus_only | 1.944205 | 0.000000 |  |  |  |  |  |  |  |
| arousal | 0 | stimulus_plus_fewshot_bias | 1.944205 | 0.000000 |  |  |  |  |  |  |  |
| arousal | 0 | stimulus_plus_fewshot_bias_shrink4 | 1.944205 | 0.000000 |  |  |  |  |  |  |  |
| arousal | 1 | stimulus_only | 1.943580 | 0.000000 | 0.000737 | 0.000137 | 0.009550 | 40.000000 | 23.000000 | 17.000000 | 0 |
| arousal | 2 | stimulus_only | 1.944653 | 0.000000 | -0.000291 | -0.001360 | 0.702065 | 28.000000 | 35.000000 | -7.000000 | 0 |
| arousal | 4 | stimulus_only | 1.944091 | 0.000000 | -0.000274 | -0.001579 | 0.655867 | 32.000000 | 31.000000 | 1.000000 | 0 |
| arousal | 8 | stimulus_only | 1.943825 | 0.000000 | 0.000178 | -0.001840 | 0.433428 | 32.000000 | 31.000000 | 1.000000 | 0 |
| arousal | 16 | stimulus_only | 1.944807 | 0.000000 | -0.000683 | -0.004082 | 0.642268 | 28.000000 | 35.000000 | -7.000000 | 0 |
| arousal | 2 | stimulus_plus_fewshot_bias | 2.070690 | -0.126037 | -0.131469 | -0.229971 | 0.992650 | 16.000000 | 47.000000 | -31.000000 | 0 |
| arousal | 1 | stimulus_plus_fewshot_bias | 2.398344 | -0.454764 | -0.451644 | -0.558160 | 1.000000 | 7.000000 | 56.000000 | -49.000000 | 0 |
| valence | 16 | stimulus_plus_fewshot_bias_shrink4 | 1.241848 | 0.014743 | 0.016499 | -0.001030 | 0.044148 | 27.000000 | 36.000000 | -9.000000 | 0 |
| valence | 16 | stimulus_plus_fewshot_bias | 1.253669 | 0.002922 | 0.005062 | -0.013327 | 0.312784 | 22.000000 | 41.000000 | -19.000000 | 0 |
| valence | 8 | stimulus_plus_fewshot_bias_shrink4 | 1.255858 | 0.002478 | 0.002893 | -0.012932 | 0.379481 | 22.000000 | 41.000000 | -19.000000 | 0 |
| valence | 0 | stimulus_only | 1.257774 | 0.000000 |  |  |  |  |  |  |  |
| valence | 0 | stimulus_plus_fewshot_bias | 1.257774 | 0.000000 |  |  |  |  |  |  |  |
| valence | 0 | stimulus_plus_fewshot_bias_shrink4 | 1.257774 | 0.000000 |  |  |  |  |  |  |  |
| valence | 1 | stimulus_only | 1.257784 | 0.000000 | 0.000004 | -0.000336 | 0.486026 | 26.000000 | 37.000000 | -11.000000 | 0 |
| valence | 2 | stimulus_only | 1.257453 | 0.000000 | 0.000301 | -0.000330 | 0.173091 | 33.000000 | 30.000000 | 3.000000 | 0 |
| valence | 4 | stimulus_only | 1.258215 | 0.000000 | -0.000468 | -0.001392 | 0.828359 | 27.000000 | 36.000000 | -9.000000 | 0 |
| valence | 8 | stimulus_only | 1.258336 | 0.000000 | -0.000587 | -0.002106 | 0.772311 | 30.000000 | 33.000000 | -3.000000 | 0 |
| valence | 16 | stimulus_only | 1.256590 | 0.000000 | 0.000811 | -0.001619 | 0.252787 | 29.000000 | 34.000000 | -5.000000 | 0 |
| valence | 4 | stimulus_plus_fewshot_bias_shrink4 | 1.264916 | -0.006701 | -0.006388 | -0.020453 | 0.793910 | 21.000000 | 42.000000 | -21.000000 | 0 |
| valence | 1 | stimulus_plus_fewshot_bias_shrink4 | 1.266974 | -0.009191 | -0.009001 | -0.015447 | 0.993700 | 18.000000 | 45.000000 | -27.000000 | 0 |
| valence | 2 | stimulus_plus_fewshot_bias_shrink4 | 1.268301 | -0.010847 | -0.009976 | -0.020041 | 0.961952 | 20.000000 | 43.000000 | -23.000000 | 0 |
| valence | 8 | stimulus_plus_fewshot_bias | 1.292301 | -0.033965 | -0.032448 | -0.051071 | 0.998750 | 18.000000 | 45.000000 | -27.000000 | 0 |
| valence | 4 | stimulus_plus_fewshot_bias | 1.361332 | -0.103117 | -0.099476 | -0.120894 | 1.000000 | 7.000000 | 56.000000 | -49.000000 | 0 |
| valence | 2 | stimulus_plus_fewshot_bias | 1.493984 | -0.236531 | -0.229770 | -0.255279 | 1.000000 | 4.000000 | 59.000000 | -55.000000 | 0 |
| valence | 1 | stimulus_plus_fewshot_bias | 1.721338 | -0.463555 | -0.453183 | -0.486519 | 1.000000 | 0.000000 | 63.000000 | -63.000000 | 0 |


## Paired subject-level statistics

| target | k_calibration | model | metric | subjects | mean_improvement_stimulus_minus_model | median_improvement_stimulus_minus_model | ci95_low_mean_improvement | ci95_high_mean_improvement | signflip_p_one_sided_mean_gt_zero | wins | losses | ties | win_margin | sign_test_p_one_sided_wins_gt_losses | pooled_lift_vs_stimulus_rmse | passes_confirmatory_metric |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | residual_rmse | 63 | 0.194921 | 0.048933 | 0.110282 | 0.290638 | 0.000050 | 37 | 26 | 0 | 11 | 0.103684 | 0.210979 | 1 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | rmse | 63 | 0.194921 | 0.048933 | 0.110752 | 0.293097 | 0.000050 | 37 | 26 | 0 | 11 | 0.103684 | 0.210979 | 1 |
| arousal | 16 | stimulus_plus_fewshot_bias | residual_rmse | 63 | 0.188877 | 0.040376 | 0.099054 | 0.290961 | 0.000050 | 36 | 27 | 0 | 9 | 0.156752 | 0.203132 | 1 |
| arousal | 16 | stimulus_plus_fewshot_bias | rmse | 63 | 0.188877 | 0.040376 | 0.098870 | 0.293806 | 0.000050 | 36 | 27 | 0 | 9 | 0.156752 | 0.203132 | 1 |
| arousal | 8 | stimulus_plus_fewshot_bias_shrink4 | residual_rmse | 63 | 0.161928 | 0.020452 | 0.086052 | 0.248912 | 0.000050 | 37 | 26 | 0 | 11 | 0.103684 | 0.178731 | 1 |
| arousal | 8 | stimulus_plus_fewshot_bias_shrink4 | rmse | 63 | 0.161928 | 0.020452 | 0.085049 | 0.247321 | 0.000050 | 37 | 26 | 0 | 11 | 0.103684 | 0.178731 | 1 |
| arousal | 8 | stimulus_plus_fewshot_bias | residual_rmse | 63 | 0.138769 | -0.027932 | 0.047510 | 0.243434 | 0.001850 | 28 | 35 | 0 | -7 | 0.843248 | 0.150550 | 0 |
| arousal | 8 | stimulus_plus_fewshot_bias | rmse | 63 | 0.138769 | -0.027932 | 0.048747 | 0.241965 | 0.002300 | 28 | 35 | 0 | -7 | 0.843248 | 0.150550 | 0 |
| arousal | 4 | stimulus_plus_fewshot_bias_shrink4 | residual_rmse | 63 | 0.119644 | 0.019884 | 0.058352 | 0.190428 | 0.000150 | 35 | 28 | 0 | 7 | 0.224981 | 0.137786 | 1 |
| arousal | 4 | stimulus_plus_fewshot_bias_shrink4 | rmse | 63 | 0.119644 | 0.019884 | 0.057433 | 0.190550 | 0.000250 | 35 | 28 | 0 | 7 | 0.224981 | 0.137786 | 1 |
| arousal | 2 | stimulus_plus_fewshot_bias_shrink4 | residual_rmse | 63 | 0.075864 | 0.003310 | 0.033034 | 0.124968 | 0.000700 | 33 | 30 | 0 | 3 | 0.400653 | 0.092477 | 1 |
| arousal | 2 | stimulus_plus_fewshot_bias_shrink4 | rmse | 63 | 0.075864 | 0.003310 | 0.031916 | 0.125962 | 0.000400 | 33 | 30 | 0 | 3 | 0.400653 | 0.092477 | 1 |
| arousal | 1 | stimulus_plus_fewshot_bias_shrink4 | residual_rmse | 63 | 0.046705 | -0.003643 | 0.018552 | 0.078103 | 0.000850 | 30 | 33 | 0 | -3 | 0.692672 | 0.057956 | 0 |
| arousal | 1 | stimulus_plus_fewshot_bias_shrink4 | rmse | 63 | 0.046705 | -0.003643 | 0.018700 | 0.078205 | 0.001250 | 30 | 33 | 0 | -3 | 0.692672 | 0.057956 | 0 |
| arousal | 4 | stimulus_plus_fewshot_bias | residual_rmse | 63 | 0.047875 | -0.093123 | -0.044123 | 0.154765 | 0.180391 | 23 | 40 | 0 | -17 | 0.988713 | 0.057609 | 0 |
| arousal | 4 | stimulus_plus_fewshot_bias | rmse | 63 | 0.047875 | -0.093123 | -0.041388 | 0.152819 | 0.181141 | 23 | 40 | 0 | -17 | 0.988713 | 0.057609 | 0 |
| arousal | 1 | stimulus_only | residual_rmse | 63 | 0.000737 | 0.000652 | 0.000135 | 0.001313 | 0.009050 | 40 | 23 | 0 | 17 | 0.021478 | 0.000000 | 0 |
| arousal | 2 | stimulus_only | residual_rmse | 63 | -0.000291 | -0.000340 | -0.001366 | 0.000788 | 0.701415 | 28 | 35 | 0 | -7 | 0.843248 | 0.000000 | 0 |
| arousal | 4 | stimulus_only | residual_rmse | 63 | -0.000274 | 0.000169 | -0.001554 | 0.001038 | 0.659817 | 32 | 31 | 0 | 1 | 0.500000 | 0.000000 | 0 |
| arousal | 8 | stimulus_only | residual_rmse | 63 | 0.000178 | 0.000333 | -0.001858 | 0.002192 | 0.432578 | 32 | 31 | 0 | 1 | 0.500000 | 0.000000 | 0 |
| arousal | 16 | stimulus_only | residual_rmse | 63 | -0.000683 | -0.002684 | -0.004115 | 0.002890 | 0.645368 | 28 | 35 | 0 | -7 | 0.843248 | 0.000000 | 0 |
| arousal | 1 | stimulus_only | rmse | 63 | 0.000737 | 0.000652 | 0.000137 | 0.001313 | 0.009550 | 40 | 23 | 0 | 17 | 0.021478 | 0.000000 | 0 |
| arousal | 2 | stimulus_only | rmse | 63 | -0.000291 | -0.000340 | -0.001360 | 0.000780 | 0.702065 | 28 | 35 | 0 | -7 | 0.843248 | 0.000000 | 0 |
| arousal | 4 | stimulus_only | rmse | 63 | -0.000274 | 0.000169 | -0.001579 | 0.001050 | 0.655867 | 32 | 31 | 0 | 1 | 0.500000 | 0.000000 | 0 |
| arousal | 8 | stimulus_only | rmse | 63 | 0.000178 | 0.000333 | -0.001840 | 0.002195 | 0.433428 | 32 | 31 | 0 | 1 | 0.500000 | 0.000000 | 0 |
| arousal | 16 | stimulus_only | rmse | 63 | -0.000683 | -0.002684 | -0.004082 | 0.002883 | 0.642268 | 28 | 35 | 0 | -7 | 0.843248 | 0.000000 | 0 |
| arousal | 2 | stimulus_plus_fewshot_bias | residual_rmse | 63 | -0.131469 | -0.256718 | -0.228902 | -0.021363 | 0.992200 | 16 | 47 | 0 | -31 | 0.999981 | -0.126037 | 0 |
| arousal | 2 | stimulus_plus_fewshot_bias | rmse | 63 | -0.131469 | -0.256718 | -0.229971 | -0.022261 | 0.992650 | 16 | 47 | 0 | -31 | 0.999981 | -0.126037 | 0 |
| arousal | 1 | stimulus_plus_fewshot_bias | residual_rmse | 63 | -0.451644 | -0.546181 | -0.556972 | -0.334449 | 1.000000 | 7 | 56 | 0 | -49 | 1.000000 | -0.454764 | 0 |
| arousal | 1 | stimulus_plus_fewshot_bias | rmse | 63 | -0.451644 | -0.546181 | -0.558160 | -0.335208 | 1.000000 | 7 | 56 | 0 | -49 | 1.000000 | -0.454764 | 0 |
| valence | 16 | stimulus_plus_fewshot_bias_shrink4 | residual_rmse | 63 | 0.016499 | -0.007383 | -0.000851 | 0.035951 | 0.044398 | 27 | 36 | 0 | -9 | 0.896316 | 0.014743 | 0 |
| valence | 16 | stimulus_plus_fewshot_bias_shrink4 | rmse | 63 | 0.016499 | -0.007383 | -0.001030 | 0.036279 | 0.044148 | 27 | 36 | 0 | -9 | 0.896316 | 0.014743 | 0 |
| valence | 16 | stimulus_plus_fewshot_bias | residual_rmse | 63 | 0.005062 | -0.021776 | -0.013184 | 0.025691 | 0.316334 | 22 | 41 | 0 | -19 | 0.994429 | 0.002922 | 0 |
| valence | 16 | stimulus_plus_fewshot_bias | rmse | 63 | 0.005062 | -0.021776 | -0.013327 | 0.025541 | 0.312784 | 22 | 41 | 0 | -19 | 0.994429 | 0.002922 | 0 |
| valence | 8 | stimulus_plus_fewshot_bias_shrink4 | residual_rmse | 63 | 0.002893 | -0.024621 | -0.013122 | 0.020751 | 0.376131 | 22 | 41 | 0 | -19 | 0.994429 | 0.002478 | 0 |
| valence | 8 | stimulus_plus_fewshot_bias_shrink4 | rmse | 63 | 0.002893 | -0.024621 | -0.012932 | 0.020912 | 0.379481 | 22 | 41 | 0 | -19 | 0.994429 | 0.002478 | 0 |
| valence | 1 | stimulus_only | residual_rmse | 63 | 0.000004 | -0.000253 | -0.000342 | 0.000362 | 0.489326 | 26 | 37 | 0 | -11 | 0.935041 | 0.000000 | 0 |
| valence | 2 | stimulus_only | residual_rmse | 63 | 0.000301 | 0.000375 | -0.000319 | 0.000925 | 0.176341 | 33 | 30 | 0 | 3 | 0.400653 | 0.000000 | 0 |
| valence | 4 | stimulus_only | residual_rmse | 63 | -0.000468 | -0.000569 | -0.001386 | 0.000492 | 0.830508 | 27 | 36 | 0 | -9 | 0.896316 | 0.000000 | 0 |
| valence | 8 | stimulus_only | residual_rmse | 63 | -0.000587 | -0.001802 | -0.002137 | 0.000923 | 0.773161 | 30 | 33 | 0 | -3 | 0.692672 | 0.000000 | 0 |
| valence | 16 | stimulus_only | residual_rmse | 63 | 0.000811 | -0.000747 | -0.001615 | 0.003221 | 0.256887 | 29 | 34 | 0 | -5 | 0.775019 | 0.000000 | 0 |
| valence | 1 | stimulus_only | rmse | 63 | 0.000004 | -0.000253 | -0.000336 | 0.000365 | 0.486026 | 26 | 37 | 0 | -11 | 0.935041 | 0.000000 | 0 |
| valence | 2 | stimulus_only | rmse | 63 | 0.000301 | 0.000375 | -0.000330 | 0.000916 | 0.173091 | 33 | 30 | 0 | 3 | 0.400653 | 0.000000 | 0 |
| valence | 4 | stimulus_only | rmse | 63 | -0.000468 | -0.000569 | -0.001392 | 0.000510 | 0.828359 | 27 | 36 | 0 | -9 | 0.896316 | 0.000000 | 0 |
| valence | 8 | stimulus_only | rmse | 63 | -0.000587 | -0.001802 | -0.002106 | 0.000915 | 0.772311 | 30 | 33 | 0 | -3 | 0.692672 | 0.000000 | 0 |
| valence | 16 | stimulus_only | rmse | 63 | 0.000811 | -0.000747 | -0.001619 | 0.003291 | 0.252787 | 29 | 34 | 0 | -5 | 0.775019 | 0.000000 | 0 |
| valence | 4 | stimulus_plus_fewshot_bias_shrink4 | residual_rmse | 63 | -0.006388 | -0.029209 | -0.020336 | 0.009218 | 0.790610 | 21 | 42 | 0 | -21 | 0.997424 | -0.006701 | 0 |
| valence | 4 | stimulus_plus_fewshot_bias_shrink4 | rmse | 63 | -0.006388 | -0.029209 | -0.020453 | 0.009146 | 0.793910 | 21 | 42 | 0 | -21 | 0.997424 | -0.006701 | 0 |
| valence | 1 | stimulus_plus_fewshot_bias_shrink4 | residual_rmse | 63 | -0.009001 | -0.018239 | -0.015384 | -0.001741 | 0.992550 | 18 | 45 | 0 | -27 | 0.999832 | -0.009191 | 0 |
| valence | 1 | stimulus_plus_fewshot_bias_shrink4 | rmse | 63 | -0.009001 | -0.018239 | -0.015447 | -0.001954 | 0.993700 | 18 | 45 | 0 | -27 | 0.999832 | -0.009191 | 0 |
| valence | 2 | stimulus_plus_fewshot_bias_shrink4 | residual_rmse | 63 | -0.009976 | -0.025623 | -0.020096 | 0.001230 | 0.963902 | 20 | 43 | 0 | -23 | 0.998886 | -0.010847 | 0 |
| valence | 2 | stimulus_plus_fewshot_bias_shrink4 | rmse | 63 | -0.009976 | -0.025623 | -0.020041 | 0.001150 | 0.961952 | 20 | 43 | 0 | -23 | 0.998886 | -0.010847 | 0 |
| valence | 8 | stimulus_plus_fewshot_bias | residual_rmse | 63 | -0.032448 | -0.064960 | -0.050994 | -0.011769 | 0.999150 | 18 | 45 | 0 | -27 | 0.999832 | -0.033965 | 0 |
| valence | 8 | stimulus_plus_fewshot_bias | rmse | 63 | -0.032448 | -0.064960 | -0.051071 | -0.011850 | 0.998750 | 18 | 45 | 0 | -27 | 0.999832 | -0.033965 | 0 |
| valence | 4 | stimulus_plus_fewshot_bias | residual_rmse | 63 | -0.099476 | -0.117442 | -0.120737 | -0.076227 | 1.000000 | 7 | 56 | 0 | -49 | 1.000000 | -0.103117 | 0 |
| valence | 4 | stimulus_plus_fewshot_bias | rmse | 63 | -0.099476 | -0.117442 | -0.120894 | -0.076166 | 1.000000 | 7 | 56 | 0 | -49 | 1.000000 | -0.103117 | 0 |
| valence | 2 | stimulus_plus_fewshot_bias | residual_rmse | 63 | -0.229770 | -0.229278 | -0.255243 | -0.203257 | 1.000000 | 4 | 59 | 0 | -55 | 1.000000 | -0.236531 | 0 |
| valence | 2 | stimulus_plus_fewshot_bias | rmse | 63 | -0.229770 | -0.229278 | -0.255279 | -0.203497 | 1.000000 | 4 | 59 | 0 | -55 | 1.000000 | -0.236531 | 0 |
| valence | 1 | stimulus_plus_fewshot_bias | residual_rmse | 63 | -0.453183 | -0.456134 | -0.486998 | -0.420315 | 1.000000 | 0 | 63 | 0 | -63 | 1.000000 | -0.463555 | 0 |
| valence | 1 | stimulus_plus_fewshot_bias | rmse | 63 | -0.453183 | -0.456134 | -0.486519 | -0.420430 | 1.000000 | 0 | 63 | 0 | -63 | 1.000000 | -0.463555 | 0 |


## Worst failure subjects for the selected candidates

| target | k_calibration | model | subject_id | ref_rmse | model_rmse | rmse_improvement | rmse_worse_than_stimulus | ref_residual_rmse | model_residual_rmse | residual_rmse_improvement |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 25 | 2.190027 | 2.286731 | -0.096704 | 1 | 2.190027 | 2.286731 | -0.096704 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 57 | 2.166632 | 2.237063 | -0.070431 | 1 | 2.166632 | 2.237063 | -0.070431 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 63 | 2.182648 | 2.252648 | -0.070001 | 1 | 2.182648 | 2.252648 | -0.070001 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 62 | 2.092926 | 2.161238 | -0.068312 | 1 | 2.092926 | 2.161238 | -0.068312 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 1 | 1.875733 | 1.941476 | -0.065744 | 1 | 1.875733 | 1.941476 | -0.065744 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 10 | 1.717370 | 1.778915 | -0.061545 | 1 | 1.717370 | 1.778915 | -0.061545 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 21 | 1.632203 | 1.692049 | -0.059846 | 1 | 1.632203 | 1.692049 | -0.059846 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 54 | 1.699383 | 1.756481 | -0.057099 | 1 | 1.699383 | 1.756481 | -0.057099 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 46 | 1.931161 | 1.987556 | -0.056395 | 1 | 1.931161 | 1.987556 | -0.056395 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 50 | 1.391328 | 1.442152 | -0.050824 | 1 | 1.391328 | 1.442152 | -0.050824 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 24 | 1.482572 | 1.530542 | -0.047970 | 1 | 1.482572 | 1.530542 | -0.047970 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 38 | 1.399220 | 1.445804 | -0.046584 | 1 | 1.399220 | 1.445804 | -0.046584 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 43 | 1.806890 | 1.844767 | -0.037877 | 1 | 1.806890 | 1.844767 | -0.037877 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 16 | 1.393718 | 1.430636 | -0.036918 | 1 | 1.393718 | 1.430636 | -0.036918 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 35 | 1.552765 | 1.585949 | -0.033184 | 1 | 1.552765 | 1.585949 | -0.033184 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 64 | 1.509447 | 1.538160 | -0.028714 | 1 | 1.509447 | 1.538160 | -0.028714 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 32 | 1.289103 | 1.316991 | -0.027889 | 1 | 1.289103 | 1.316991 | -0.027889 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 30 | 0.956852 | 0.978148 | -0.021296 | 1 | 0.956852 | 0.978148 | -0.021296 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 22 | 2.201921 | 2.220402 | -0.018481 | 1 | 2.201921 | 2.220402 | -0.018481 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 52 | 2.018432 | 2.036850 | -0.018418 | 1 | 2.018432 | 2.036850 | -0.018418 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 39 | 2.042019 | 2.060028 | -0.018009 | 1 | 2.042019 | 2.060028 | -0.018009 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 44 | 2.461962 | 2.479158 | -0.017196 | 1 | 2.461962 | 2.479158 | -0.017196 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 48 | 1.304702 | 1.320091 | -0.015389 | 1 | 1.304702 | 1.320091 | -0.015389 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 18 | 2.214446 | 2.222915 | -0.008469 | 1 | 2.214446 | 2.222915 | -0.008469 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 45 | 1.521949 | 1.525763 | -0.003814 | 1 | 1.521949 | 1.525763 | -0.003814 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 15 | 1.695158 | 1.698467 | -0.003309 | 1 | 1.695158 | 1.698467 | -0.003309 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 37 | 1.579094 | 1.572929 | 0.006165 | 0 | 1.579094 | 1.572929 | 0.006165 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 53 | 1.117809 | 1.106060 | 0.011749 | 0 | 1.117809 | 1.106060 | 0.011749 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 29 | 1.430352 | 1.399660 | 0.030692 | 0 | 1.430352 | 1.399660 | 0.030692 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 11 | 2.026536 | 1.987883 | 0.038653 | 0 | 2.026536 | 1.987883 | 0.038653 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 47 | 2.441804 | 2.393743 | 0.048062 | 0 | 2.441804 | 2.393743 | 0.048062 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 34 | 1.370932 | 1.321999 | 0.048933 | 0 | 1.370932 | 1.321999 | 0.048933 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 36 | 1.613742 | 1.560025 | 0.053717 | 0 | 1.613742 | 1.560025 | 0.053717 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 12 | 1.330165 | 1.269368 | 0.060798 | 0 | 1.330165 | 1.269368 | 0.060798 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 56 | 1.450442 | 1.382165 | 0.068277 | 0 | 1.450442 | 1.382165 | 0.068277 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 31 | 2.348248 | 2.266326 | 0.081922 | 0 | 2.348248 | 2.266326 | 0.081922 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 40 | 2.919192 | 2.829191 | 0.090001 | 0 | 2.919192 | 2.829191 | 0.090001 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 17 | 1.443008 | 1.352958 | 0.090050 | 0 | 1.443008 | 1.352958 | 0.090050 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 33 | 1.708850 | 1.616351 | 0.092499 | 0 | 1.708850 | 1.616351 | 0.092499 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 27 | 1.535351 | 1.388942 | 0.146408 | 0 | 1.535351 | 1.388942 | 0.146408 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 61 | 1.864916 | 1.714359 | 0.150557 | 0 | 1.864916 | 1.714359 | 0.150557 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 5 | 1.754836 | 1.588060 | 0.166776 | 0 | 1.754836 | 1.588060 | 0.166776 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 9 | 2.170411 | 1.994553 | 0.175858 | 0 | 2.170411 | 1.994553 | 0.175858 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 8 | 1.918789 | 1.716306 | 0.202484 | 0 | 1.918789 | 1.716306 | 0.202484 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 60 | 2.415656 | 2.196721 | 0.218935 | 0 | 2.415656 | 2.196721 | 0.218935 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 65 | 2.028683 | 1.803927 | 0.224755 | 0 | 2.028683 | 1.803927 | 0.224755 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 23 | 1.444427 | 1.216530 | 0.227897 | 0 | 1.444427 | 1.216530 | 0.227897 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 26 | 2.097571 | 1.803435 | 0.294136 | 0 | 2.097571 | 1.803435 | 0.294136 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 20 | 1.606107 | 1.301936 | 0.304172 | 0 | 1.606107 | 1.301936 | 0.304172 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 19 | 1.864916 | 1.548926 | 0.315990 | 0 | 1.864916 | 1.548926 | 0.315990 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 7 | 1.625285 | 1.300340 | 0.324945 | 0 | 1.625285 | 1.300340 | 0.324945 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 59 | 2.058506 | 1.719248 | 0.339258 | 0 | 2.058506 | 1.719248 | 0.339258 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 58 | 1.584113 | 1.210528 | 0.373585 | 0 | 1.584113 | 1.210528 | 0.373585 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 28 | 1.736794 | 1.344493 | 0.392301 | 0 | 1.736794 | 1.344493 | 0.392301 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 3 | 1.853346 | 1.428104 | 0.425242 | 0 | 1.853346 | 1.428104 | 0.425242 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 49 | 2.383641 | 1.784366 | 0.599275 | 0 | 2.383641 | 1.784366 | 0.599275 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 14 | 1.796657 | 0.925726 | 0.870931 | 0 | 1.796657 | 0.925726 | 0.870931 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 42 | 2.652334 | 1.772502 | 0.879832 | 0 | 2.652334 | 1.772502 | 0.879832 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 41 | 2.469025 | 1.582878 | 0.886147 | 0 | 2.469025 | 1.582878 | 0.886147 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 13 | 2.417245 | 1.507276 | 0.909970 | 0 | 2.417245 | 1.507276 | 0.909970 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 2 | 2.732513 | 1.679059 | 1.053455 | 0 | 2.732513 | 1.679059 | 1.053455 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 55 | 2.461650 | 1.117968 | 1.343681 | 0 | 2.461650 | 1.117968 | 1.343681 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 6 | 3.732512 | 1.960206 | 1.772307 | 0 | 3.732512 | 1.960206 | 1.772307 |
| valence | 16 | stimulus_plus_fewshot_bias_shrink4 | 47 | 1.813891 | 1.875620 | -0.061729 | 1 | 1.813891 | 1.875620 | -0.061729 |
| valence | 16 | stimulus_plus_fewshot_bias_shrink4 | 50 | 1.286616 | 1.340867 | -0.054251 | 1 | 1.286616 | 1.340867 | -0.054251 |
| valence | 16 | stimulus_plus_fewshot_bias_shrink4 | 40 | 1.426676 | 1.480447 | -0.053771 | 1 | 1.426676 | 1.480447 | -0.053771 |
| valence | 16 | stimulus_plus_fewshot_bias_shrink4 | 25 | 1.542422 | 1.596167 | -0.053745 | 1 | 1.542422 | 1.596167 | -0.053745 |
| valence | 16 | stimulus_plus_fewshot_bias_shrink4 | 49 | 1.332953 | 1.384349 | -0.051397 | 1 | 1.332953 | 1.384349 | -0.051397 |
| valence | 16 | stimulus_plus_fewshot_bias_shrink4 | 6 | 1.157093 | 1.205385 | -0.048292 | 1 | 1.157093 | 1.205385 | -0.048292 |
| valence | 16 | stimulus_plus_fewshot_bias_shrink4 | 28 | 1.275220 | 1.321738 | -0.046517 | 1 | 1.275220 | 1.321738 | -0.046517 |
| valence | 16 | stimulus_plus_fewshot_bias_shrink4 | 5 | 1.494527 | 1.540464 | -0.045937 | 1 | 1.494527 | 1.540464 | -0.045937 |
| valence | 16 | stimulus_plus_fewshot_bias_shrink4 | 10 | 1.000419 | 1.045739 | -0.045320 | 1 | 1.000419 | 1.045739 | -0.045320 |
| valence | 16 | stimulus_plus_fewshot_bias_shrink4 | 11 | 1.449116 | 1.494165 | -0.045049 | 1 | 1.449116 | 1.494165 | -0.045049 |
| valence | 16 | stimulus_plus_fewshot_bias_shrink4 | 63 | 1.137451 | 1.180676 | -0.043225 | 1 | 1.137451 | 1.180676 | -0.043225 |
| valence | 16 | stimulus_plus_fewshot_bias_shrink4 | 38 | 1.610803 | 1.653307 | -0.042504 | 1 | 1.610803 | 1.653307 | -0.042504 |
| valence | 16 | stimulus_plus_fewshot_bias_shrink4 | 60 | 1.249867 | 1.288623 | -0.038756 | 1 | 1.249867 | 1.288623 | -0.038756 |
| valence | 16 | stimulus_plus_fewshot_bias_shrink4 | 30 | 0.980511 | 1.017901 | -0.037391 | 1 | 0.980511 | 1.017901 | -0.037391 |
| valence | 16 | stimulus_plus_fewshot_bias_shrink4 | 19 | 1.318271 | 1.355407 | -0.037136 | 1 | 1.318271 | 1.355407 | -0.037136 |
| valence | 16 | stimulus_plus_fewshot_bias_shrink4 | 59 | 1.388102 | 1.423255 | -0.035153 | 1 | 1.388102 | 1.423255 | -0.035153 |
| valence | 16 | stimulus_plus_fewshot_bias_shrink4 | 65 | 0.960190 | 0.993838 | -0.033648 | 1 | 0.960190 | 0.993838 | -0.033648 |


## Interpretation

- Arousal should only stay in the GO path if the subject-paired tests confirm the 05aa win margin and CI evidence.

- Valence should remain weak/unstable unless paired subject evidence turns positive; a tiny pooled lift alone is not enough.

- Any future calibration model family in 05ae must beat the locked few-shot baseline confirmed here, not merely beat stimulus-only.
