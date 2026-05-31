# I-DARE Few-shot Calibration Confirmatory Statistics

This report validates whether the few-shot subject-calibration result from 05aa is reliable at subject level, not only in pooled repeated predictions.

Positive improvement means `stimulus_only RMSE - fewshot_model RMSE`; positive is good for few-shot calibration.

## Decision rule

`GO_CONFIRMED_FEWSHOT_SUBJECT_CALIBRATION` requires pooled RMSE lift >= 0.02, positive paired mean subject improvement, bootstrap CI lower bound > 0, one-sided sign-flip p < 0.05, and subject win margin >= 3.

## Verdict

| target | decision | best_model | best_k_calibration | best_rmse | best_lift_vs_stimulus_rmse | mean_subject_rmse_improvement | ci95_low_mean_subject_rmse_improvement | signflip_p_one_sided_mean_gt_zero | rmse_wins | rmse_losses | rmse_win_margin | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | WEAK_GO_FEWSHOT_NEEDS_CAUTION | stimulus_plus_fewshot_bias | 16 | 1.751666 | 0.650859 | 0.632778 | 0.247419 | 0.033193 | 5 | 3 | 2 | win margin < 3 |
| valence | WEAK_GO_FEWSHOT_NEEDS_CAUTION | stimulus_plus_fewshot_bias_shrink4 | 16 | 1.283849 | 0.009078 | 0.005148 | -0.026164 | 0.391722 | 4 | 4 | 0 | pooled lift < 0.02; bootstrap CI lower bound is not > 0; sign-flip p is not < 0.05; win margin < 3 |


## Calibration curve summary

| target | k_calibration | model | rmse | lift_vs_stimulus_rmse | mean_improvement_stimulus_minus_model | ci95_low_mean_improvement | signflip_p_one_sided_mean_gt_zero | wins | losses | win_margin | passes_confirmatory_metric |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | 16 | stimulus_plus_fewshot_bias | 1.751666 | 0.650859 | 0.632778 | 0.247419 | 0.033193 | 5.000000 | 3.000000 | 2.000000 | 0 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 1.762086 | 0.640439 | 0.617328 | 0.239954 | 0.027395 | 6.000000 | 2.000000 | 4.000000 | 1 |
| arousal | 8 | stimulus_plus_fewshot_bias | 1.798035 | 0.615864 | 0.587868 | 0.192919 | 0.033193 | 5.000000 | 3.000000 | 2.000000 | 0 |
| arousal | 8 | stimulus_plus_fewshot_bias_shrink4 | 1.835907 | 0.577993 | 0.540733 | 0.200942 | 0.026795 | 6.000000 | 2.000000 | 4.000000 | 1 |
| arousal | 4 | stimulus_plus_fewshot_bias | 1.903374 | 0.503019 | 0.483464 | 0.075766 | 0.038592 | 5.000000 | 3.000000 | 2.000000 | 0 |
| arousal | 4 | stimulus_plus_fewshot_bias_shrink4 | 1.942828 | 0.463566 | 0.432223 | 0.150447 | 0.030394 | 5.000000 | 3.000000 | 2.000000 | 0 |
| arousal | 2 | stimulus_plus_fewshot_bias | 2.073218 | 0.340118 | 0.322720 | -0.137986 | 0.124775 | 5.000000 | 3.000000 | 2.000000 | 0 |
| arousal | 2 | stimulus_plus_fewshot_bias_shrink4 | 2.094399 | 0.318937 | 0.283960 | 0.098030 | 0.028194 | 6.000000 | 2.000000 | 4.000000 | 1 |
| arousal | 1 | stimulus_plus_fewshot_bias_shrink4 | 2.195794 | 0.213252 | 0.189797 | 0.056810 | 0.029394 | 5.000000 | 3.000000 | 2.000000 | 0 |
| arousal | 0 | stimulus_only | 2.411442 | 0.000000 |  |  |  |  |  |  |  |
| arousal | 0 | stimulus_plus_fewshot_bias | 2.411442 | 0.000000 |  |  |  |  |  |  |  |
| arousal | 0 | stimulus_plus_fewshot_bias_shrink4 | 2.411442 | 0.000000 |  |  |  |  |  |  |  |
| arousal | 1 | stimulus_only | 2.409046 | 0.000000 | 0.002414 | -0.000170 | 0.053989 | 6.000000 | 2.000000 | 4.000000 | 0 |
| arousal | 2 | stimulus_only | 2.413336 | 0.000000 | -0.001663 | -0.005944 | 0.746251 | 2.000000 | 6.000000 | -4.000000 | 0 |
| arousal | 4 | stimulus_only | 2.406393 | 0.000000 | 0.004181 | -0.003349 | 0.174765 | 5.000000 | 3.000000 | 2.000000 | 0 |
| arousal | 8 | stimulus_only | 2.413900 | 0.000000 | -0.002267 | -0.012995 | 0.659068 | 4.000000 | 4.000000 | 0.000000 | 0 |
| arousal | 16 | stimulus_only | 2.402525 | 0.000000 | 0.004184 | -0.014325 | 0.334733 | 4.000000 | 4.000000 | 0.000000 | 0 |
| arousal | 1 | stimulus_plus_fewshot_bias | 2.414961 | -0.005915 | -0.021364 | -0.468135 | 0.557089 | 4.000000 | 4.000000 | 0.000000 | 0 |
| valence | 16 | stimulus_plus_fewshot_bias_shrink4 | 1.283849 | 0.009078 | 0.005148 | -0.026164 | 0.391722 | 4.000000 | 4.000000 | 0.000000 | 0 |
| valence | 0 | stimulus_only | 1.289924 | 0.000000 |  |  |  |  |  |  |  |
| valence | 0 | stimulus_plus_fewshot_bias | 1.289924 | 0.000000 |  |  |  |  |  |  |  |
| valence | 0 | stimulus_plus_fewshot_bias_shrink4 | 1.289924 | 0.000000 |  |  |  |  |  |  |  |
| valence | 1 | stimulus_only | 1.288328 | 0.000000 | 0.001430 | -0.000355 | 0.105379 | 5.000000 | 3.000000 | 2.000000 | 0 |
| valence | 2 | stimulus_only | 1.289390 | 0.000000 | 0.000915 | -0.003379 | 0.362727 | 3.000000 | 5.000000 | -2.000000 | 0 |
| valence | 4 | stimulus_only | 1.292020 | 0.000000 | -0.001899 | -0.006685 | 0.751250 | 3.000000 | 5.000000 | -2.000000 | 0 |
| valence | 8 | stimulus_only | 1.288690 | 0.000000 | 0.001512 | -0.007175 | 0.402519 | 4.000000 | 4.000000 | 0.000000 | 0 |
| valence | 16 | stimulus_only | 1.292926 | 0.000000 | -0.003770 | -0.016816 | 0.675665 | 2.000000 | 6.000000 | -4.000000 | 0 |
| valence | 16 | stimulus_plus_fewshot_bias | 1.294167 | -0.001241 | -0.004983 | -0.040354 | 0.586883 | 4.000000 | 4.000000 | 0.000000 | 0 |
| valence | 8 | stimulus_plus_fewshot_bias_shrink4 | 1.295204 | -0.006515 | -0.004823 | -0.031071 | 0.624675 | 3.000000 | 5.000000 | -2.000000 | 0 |
| valence | 4 | stimulus_plus_fewshot_bias_shrink4 | 1.303563 | -0.011543 | -0.013653 | -0.035042 | 0.847231 | 3.000000 | 5.000000 | -2.000000 | 0 |
| valence | 2 | stimulus_plus_fewshot_bias_shrink4 | 1.304818 | -0.015427 | -0.015154 | -0.030360 | 0.942412 | 3.000000 | 5.000000 | -2.000000 | 0 |
| valence | 1 | stimulus_plus_fewshot_bias_shrink4 | 1.305410 | -0.017082 | -0.015889 | -0.024383 | 0.979604 | 2.000000 | 6.000000 | -4.000000 | 0 |
| valence | 8 | stimulus_plus_fewshot_bias | 1.334801 | -0.046112 | -0.043777 | -0.076101 | 0.974805 | 3.000000 | 5.000000 | -2.000000 | 0 |
| valence | 4 | stimulus_plus_fewshot_bias | 1.391988 | -0.099968 | -0.101565 | -0.132859 | 1.000000 | 0.000000 | 8.000000 | -8.000000 | 0 |
| valence | 2 | stimulus_plus_fewshot_bias | 1.537112 | -0.247722 | -0.247115 | -0.291738 | 1.000000 | 0.000000 | 8.000000 | -8.000000 | 0 |
| valence | 1 | stimulus_plus_fewshot_bias | 1.820565 | -0.532237 | -0.524816 | -0.581838 | 1.000000 | 0.000000 | 8.000000 | -8.000000 | 0 |


## Paired subject-level statistics

| target | k_calibration | model | metric | subjects | mean_improvement_stimulus_minus_model | median_improvement_stimulus_minus_model | ci95_low_mean_improvement | ci95_high_mean_improvement | signflip_p_one_sided_mean_gt_zero | wins | losses | ties | win_margin | sign_test_p_one_sided_wins_gt_losses | pooled_lift_vs_stimulus_rmse | passes_confirmatory_metric |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | 16 | stimulus_plus_fewshot_bias | residual_rmse | 8 | 0.632778 | 0.694810 | 0.235676 | 1.047130 | 0.033993 | 5 | 3 | 0 | 2 | 0.363281 | 0.650859 | 0 |
| arousal | 16 | stimulus_plus_fewshot_bias | rmse | 8 | 0.632778 | 0.694810 | 0.247419 | 1.047900 | 0.033193 | 5 | 3 | 0 | 2 | 0.363281 | 0.650859 | 0 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | residual_rmse | 8 | 0.617328 | 0.694730 | 0.236039 | 1.012627 | 0.029194 | 6 | 2 | 0 | 4 | 0.144531 | 0.640439 | 1 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | rmse | 8 | 0.617328 | 0.694730 | 0.239954 | 1.011073 | 0.027395 | 6 | 2 | 0 | 4 | 0.144531 | 0.640439 | 1 |
| arousal | 8 | stimulus_plus_fewshot_bias | residual_rmse | 8 | 0.587868 | 0.650614 | 0.191396 | 1.000438 | 0.033793 | 5 | 3 | 0 | 2 | 0.363281 | 0.615864 | 0 |
| arousal | 8 | stimulus_plus_fewshot_bias | rmse | 8 | 0.587868 | 0.650614 | 0.192919 | 0.987007 | 0.033193 | 5 | 3 | 0 | 2 | 0.363281 | 0.615864 | 0 |
| arousal | 8 | stimulus_plus_fewshot_bias_shrink4 | residual_rmse | 8 | 0.540733 | 0.598172 | 0.197768 | 0.868442 | 0.022196 | 6 | 2 | 0 | 4 | 0.144531 | 0.577993 | 1 |
| arousal | 8 | stimulus_plus_fewshot_bias_shrink4 | rmse | 8 | 0.540733 | 0.598172 | 0.200942 | 0.889450 | 0.026795 | 6 | 2 | 0 | 4 | 0.144531 | 0.577993 | 1 |
| arousal | 4 | stimulus_plus_fewshot_bias | residual_rmse | 8 | 0.483464 | 0.555364 | 0.076276 | 0.900821 | 0.035793 | 5 | 3 | 0 | 2 | 0.363281 | 0.503019 | 0 |
| arousal | 4 | stimulus_plus_fewshot_bias | rmse | 8 | 0.483464 | 0.555364 | 0.075766 | 0.901146 | 0.038592 | 5 | 3 | 0 | 2 | 0.363281 | 0.503019 | 0 |
| arousal | 4 | stimulus_plus_fewshot_bias_shrink4 | residual_rmse | 8 | 0.432223 | 0.519927 | 0.152742 | 0.717347 | 0.033593 | 5 | 3 | 0 | 2 | 0.363281 | 0.463566 | 0 |
| arousal | 4 | stimulus_plus_fewshot_bias_shrink4 | rmse | 8 | 0.432223 | 0.519927 | 0.150447 | 0.714128 | 0.030394 | 5 | 3 | 0 | 2 | 0.363281 | 0.463566 | 0 |
| arousal | 2 | stimulus_plus_fewshot_bias | residual_rmse | 8 | 0.322720 | 0.375350 | -0.132411 | 0.775291 | 0.117377 | 5 | 3 | 0 | 2 | 0.363281 | 0.340118 | 0 |
| arousal | 2 | stimulus_plus_fewshot_bias | rmse | 8 | 0.322720 | 0.375350 | -0.137986 | 0.776324 | 0.124775 | 5 | 3 | 0 | 2 | 0.363281 | 0.340118 | 0 |
| arousal | 2 | stimulus_plus_fewshot_bias_shrink4 | residual_rmse | 8 | 0.283960 | 0.329118 | 0.096313 | 0.484401 | 0.023595 | 6 | 2 | 0 | 4 | 0.144531 | 0.318937 | 1 |
| arousal | 2 | stimulus_plus_fewshot_bias_shrink4 | rmse | 8 | 0.283960 | 0.329118 | 0.098030 | 0.486525 | 0.028194 | 6 | 2 | 0 | 4 | 0.144531 | 0.318937 | 1 |
| arousal | 1 | stimulus_plus_fewshot_bias_shrink4 | residual_rmse | 8 | 0.189797 | 0.234014 | 0.058997 | 0.324897 | 0.030794 | 5 | 3 | 0 | 2 | 0.363281 | 0.213252 | 0 |
| arousal | 1 | stimulus_plus_fewshot_bias_shrink4 | rmse | 8 | 0.189797 | 0.234014 | 0.056810 | 0.321879 | 0.029394 | 5 | 3 | 0 | 2 | 0.363281 | 0.213252 | 0 |
| arousal | 1 | stimulus_only | residual_rmse | 8 | 0.002414 | 0.003046 | -0.000115 | 0.004724 | 0.051390 | 6 | 2 | 0 | 4 | 0.144531 | 0.000000 | 0 |
| arousal | 2 | stimulus_only | residual_rmse | 8 | -0.001663 | -0.002684 | -0.005987 | 0.003136 | 0.731654 | 2 | 6 | 0 | -4 | 0.964844 | 0.000000 | 0 |
| arousal | 4 | stimulus_only | residual_rmse | 8 | 0.004181 | 0.005158 | -0.003658 | 0.012083 | 0.180564 | 5 | 3 | 0 | 2 | 0.363281 | 0.000000 | 0 |
| arousal | 8 | stimulus_only | residual_rmse | 8 | -0.002267 | -0.001225 | -0.012883 | 0.008038 | 0.657868 | 4 | 4 | 0 | 0 | 0.636719 | 0.000000 | 0 |
| arousal | 16 | stimulus_only | residual_rmse | 8 | 0.004184 | 0.002655 | -0.014198 | 0.022546 | 0.344131 | 4 | 4 | 0 | 0 | 0.636719 | 0.000000 | 0 |
| arousal | 1 | stimulus_only | rmse | 8 | 0.002414 | 0.003046 | -0.000170 | 0.004777 | 0.053989 | 6 | 2 | 0 | 4 | 0.144531 | 0.000000 | 0 |
| arousal | 2 | stimulus_only | rmse | 8 | -0.001663 | -0.002684 | -0.005944 | 0.003136 | 0.746251 | 2 | 6 | 0 | -4 | 0.964844 | 0.000000 | 0 |
| arousal | 4 | stimulus_only | rmse | 8 | 0.004181 | 0.005158 | -0.003349 | 0.012140 | 0.174765 | 5 | 3 | 0 | 2 | 0.363281 | 0.000000 | 0 |
| arousal | 8 | stimulus_only | rmse | 8 | -0.002267 | -0.001225 | -0.012995 | 0.007775 | 0.659068 | 4 | 4 | 0 | 0 | 0.636719 | 0.000000 | 0 |
| arousal | 16 | stimulus_only | rmse | 8 | 0.004184 | 0.002655 | -0.014325 | 0.022297 | 0.334733 | 4 | 4 | 0 | 0 | 0.636719 | 0.000000 | 0 |
| arousal | 1 | stimulus_plus_fewshot_bias | residual_rmse | 8 | -0.021364 | -0.010594 | -0.481830 | 0.464781 | 0.530094 | 4 | 4 | 0 | 0 | 0.636719 | -0.005915 | 0 |
| arousal | 1 | stimulus_plus_fewshot_bias | rmse | 8 | -0.021364 | -0.010594 | -0.468135 | 0.468788 | 0.557089 | 4 | 4 | 0 | 0 | 0.636719 | -0.005915 | 0 |
| valence | 16 | stimulus_plus_fewshot_bias_shrink4 | residual_rmse | 8 | 0.005148 | 0.013279 | -0.026899 | 0.036133 | 0.371926 | 4 | 4 | 0 | 0 | 0.636719 | 0.009078 | 0 |
| valence | 16 | stimulus_plus_fewshot_bias_shrink4 | rmse | 8 | 0.005148 | 0.013279 | -0.026164 | 0.036469 | 0.391722 | 4 | 4 | 0 | 0 | 0.636719 | 0.009078 | 0 |
| valence | 1 | stimulus_only | residual_rmse | 8 | 0.001430 | 0.001180 | -0.000340 | 0.003299 | 0.106179 | 5 | 3 | 0 | 2 | 0.363281 | 0.000000 | 0 |
| valence | 2 | stimulus_only | residual_rmse | 8 | 0.000915 | -0.000860 | -0.003516 | 0.005594 | 0.346931 | 3 | 5 | 0 | -2 | 0.855469 | 0.000000 | 0 |
| valence | 4 | stimulus_only | residual_rmse | 8 | -0.001899 | -0.002711 | -0.006393 | 0.002639 | 0.753649 | 3 | 5 | 0 | -2 | 0.855469 | 0.000000 | 0 |
| valence | 8 | stimulus_only | residual_rmse | 8 | 0.001512 | -0.001151 | -0.007217 | 0.010790 | 0.396121 | 4 | 4 | 0 | 0 | 0.636719 | 0.000000 | 0 |
| valence | 16 | stimulus_only | residual_rmse | 8 | -0.003770 | -0.012717 | -0.016992 | 0.012288 | 0.663067 | 2 | 6 | 0 | -4 | 0.964844 | 0.000000 | 0 |
| valence | 1 | stimulus_only | rmse | 8 | 0.001430 | 0.001180 | -0.000355 | 0.003264 | 0.105379 | 5 | 3 | 0 | 2 | 0.363281 | 0.000000 | 0 |
| valence | 2 | stimulus_only | rmse | 8 | 0.000915 | -0.000860 | -0.003379 | 0.005643 | 0.362727 | 3 | 5 | 0 | -2 | 0.855469 | 0.000000 | 0 |
| valence | 4 | stimulus_only | rmse | 8 | -0.001899 | -0.002711 | -0.006685 | 0.002540 | 0.751250 | 3 | 5 | 0 | -2 | 0.855469 | 0.000000 | 0 |
| valence | 8 | stimulus_only | rmse | 8 | 0.001512 | -0.001151 | -0.007175 | 0.010912 | 0.402519 | 4 | 4 | 0 | 0 | 0.636719 | 0.000000 | 0 |
| valence | 16 | stimulus_only | rmse | 8 | -0.003770 | -0.012717 | -0.016816 | 0.012197 | 0.675665 | 2 | 6 | 0 | -4 | 0.964844 | 0.000000 | 0 |
| valence | 16 | stimulus_plus_fewshot_bias | residual_rmse | 8 | -0.004983 | 0.004469 | -0.040683 | 0.029406 | 0.597081 | 4 | 4 | 0 | 0 | 0.636719 | -0.001241 | 0 |
| valence | 16 | stimulus_plus_fewshot_bias | rmse | 8 | -0.004983 | 0.004469 | -0.040354 | 0.031744 | 0.586883 | 4 | 4 | 0 | 0 | 0.636719 | -0.001241 | 0 |
| valence | 8 | stimulus_plus_fewshot_bias_shrink4 | residual_rmse | 8 | -0.004823 | -0.009270 | -0.030114 | 0.023461 | 0.621876 | 3 | 5 | 0 | -2 | 0.855469 | -0.006515 | 0 |
| valence | 8 | stimulus_plus_fewshot_bias_shrink4 | rmse | 8 | -0.004823 | -0.009270 | -0.031071 | 0.022979 | 0.624675 | 3 | 5 | 0 | -2 | 0.855469 | -0.006515 | 0 |
| valence | 4 | stimulus_plus_fewshot_bias_shrink4 | residual_rmse | 8 | -0.013653 | -0.027635 | -0.035644 | 0.012266 | 0.844231 | 3 | 5 | 0 | -2 | 0.855469 | -0.011543 | 0 |
| valence | 4 | stimulus_plus_fewshot_bias_shrink4 | rmse | 8 | -0.013653 | -0.027635 | -0.035042 | 0.011365 | 0.847231 | 3 | 5 | 0 | -2 | 0.855469 | -0.011543 | 0 |
| valence | 2 | stimulus_plus_fewshot_bias_shrink4 | residual_rmse | 8 | -0.015154 | -0.023956 | -0.030478 | 0.001228 | 0.943211 | 3 | 5 | 0 | -2 | 0.855469 | -0.015427 | 0 |
| valence | 2 | stimulus_plus_fewshot_bias_shrink4 | rmse | 8 | -0.015154 | -0.023956 | -0.030360 | 0.001792 | 0.942412 | 3 | 5 | 0 | -2 | 0.855469 | -0.015427 | 0 |
| valence | 1 | stimulus_plus_fewshot_bias_shrink4 | residual_rmse | 8 | -0.015889 | -0.021954 | -0.024343 | -0.006357 | 0.981404 | 2 | 6 | 0 | -4 | 0.964844 | -0.017082 | 0 |
| valence | 1 | stimulus_plus_fewshot_bias_shrink4 | rmse | 8 | -0.015889 | -0.021954 | -0.024383 | -0.006692 | 0.979604 | 2 | 6 | 0 | -4 | 0.964844 | -0.017082 | 0 |
| valence | 8 | stimulus_plus_fewshot_bias | residual_rmse | 8 | -0.043777 | -0.048170 | -0.077226 | -0.012233 | 0.972406 | 3 | 5 | 0 | -2 | 0.855469 | -0.046112 | 0 |
| valence | 8 | stimulus_plus_fewshot_bias | rmse | 8 | -0.043777 | -0.048170 | -0.076101 | -0.012443 | 0.974805 | 3 | 5 | 0 | -2 | 0.855469 | -0.046112 | 0 |
| valence | 4 | stimulus_plus_fewshot_bias | residual_rmse | 8 | -0.101565 | -0.098513 | -0.132088 | -0.068935 | 1.000000 | 0 | 8 | 0 | -8 | 1.000000 | -0.099968 | 0 |
| valence | 4 | stimulus_plus_fewshot_bias | rmse | 8 | -0.101565 | -0.098513 | -0.132859 | -0.070771 | 1.000000 | 0 | 8 | 0 | -8 | 1.000000 | -0.099968 | 0 |
| valence | 2 | stimulus_plus_fewshot_bias | residual_rmse | 8 | -0.247115 | -0.251324 | -0.290331 | -0.201486 | 1.000000 | 0 | 8 | 0 | -8 | 1.000000 | -0.247722 | 0 |
| valence | 2 | stimulus_plus_fewshot_bias | rmse | 8 | -0.247115 | -0.251324 | -0.291738 | -0.201569 | 1.000000 | 0 | 8 | 0 | -8 | 1.000000 | -0.247722 | 0 |
| valence | 1 | stimulus_plus_fewshot_bias | residual_rmse | 8 | -0.524816 | -0.525720 | -0.579954 | -0.465667 | 1.000000 | 0 | 8 | 0 | -8 | 1.000000 | -0.532237 | 0 |
| valence | 1 | stimulus_plus_fewshot_bias | rmse | 8 | -0.524816 | -0.525720 | -0.581838 | -0.465797 | 1.000000 | 0 | 8 | 0 | -8 | 1.000000 | -0.532237 | 0 |


## Worst failure subjects for the selected candidates

| target | k_calibration | model | subject_id | ref_rmse | model_rmse | rmse_improvement | rmse_worse_than_stimulus | ref_residual_rmse | model_residual_rmse | residual_rmse_improvement |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | 16 | stimulus_plus_fewshot_bias | 1 | 2.256792 | 2.303422 | -0.046629 | 1 | 2.256792 | 2.303422 | -0.046629 |
| arousal | 16 | stimulus_plus_fewshot_bias | 5 | 1.660234 | 1.700733 | -0.040499 | 1 | 1.660234 | 1.700733 | -0.040499 |
| arousal | 16 | stimulus_plus_fewshot_bias | 9 | 1.801714 | 1.810582 | -0.008868 | 1 | 1.801714 | 1.810582 | -0.008868 |
| arousal | 16 | stimulus_plus_fewshot_bias | 8 | 2.495148 | 1.878388 | 0.616761 | 0 | 2.495148 | 1.878388 | 0.616761 |
| arousal | 16 | stimulus_plus_fewshot_bias | 2 | 2.569692 | 1.796833 | 0.772859 | 0 | 2.569692 | 1.796833 | 0.772859 |
| arousal | 16 | stimulus_plus_fewshot_bias | 7 | 2.053183 | 1.096140 | 0.957043 | 0 | 2.053183 | 1.096140 | 0.957043 |
| arousal | 16 | stimulus_plus_fewshot_bias | 3 | 2.317029 | 1.190542 | 1.126487 | 0 | 2.317029 | 1.190542 | 1.126487 |
| arousal | 16 | stimulus_plus_fewshot_bias | 6 | 3.607143 | 1.922074 | 1.685069 | 0 | 3.607143 | 1.922074 | 1.685069 |
| valence | 16 | stimulus_plus_fewshot_bias_shrink4 | 6 | 1.066357 | 1.123286 | -0.056928 | 1 | 1.066357 | 1.123286 | -0.056928 |
| valence | 16 | stimulus_plus_fewshot_bias_shrink4 | 5 | 1.509958 | 1.564280 | -0.054322 | 1 | 1.509958 | 1.564280 | -0.054322 |
| valence | 16 | stimulus_plus_fewshot_bias_shrink4 | 7 | 1.027368 | 1.057212 | -0.029845 | 1 | 1.027368 | 1.057212 | -0.029845 |
| valence | 16 | stimulus_plus_fewshot_bias_shrink4 | 3 | 1.299284 | 1.301389 | -0.002106 | 1 | 1.299284 | 1.301389 | -0.002106 |
| valence | 16 | stimulus_plus_fewshot_bias_shrink4 | 8 | 1.226566 | 1.197902 | 0.028664 | 0 | 1.226566 | 1.197902 | 0.028664 |
| valence | 16 | stimulus_plus_fewshot_bias_shrink4 | 1 | 1.267480 | 1.234015 | 0.033465 | 0 | 1.267480 | 1.234015 | 0.033465 |
| valence | 16 | stimulus_plus_fewshot_bias_shrink4 | 2 | 1.513334 | 1.471310 | 0.042024 | 0 | 1.513334 | 1.471310 | 0.042024 |
| valence | 16 | stimulus_plus_fewshot_bias_shrink4 | 9 | 1.322635 | 1.242403 | 0.080231 | 0 | 1.322635 | 1.242403 | 0.080231 |


## Interpretation

- Arousal should only stay in the GO path if the subject-paired tests confirm the 05aa win margin and CI evidence.

- Valence should remain weak/unstable unless paired subject evidence turns positive; a tiny pooled lift alone is not enough.

- Any future calibration model family in 05ae must beat the locked few-shot baseline confirmed here, not merely beat stimulus-only.
