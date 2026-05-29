# I-DARE Subject Calibration Model-Family Comparison

This report tests whether any subject-calibration family improves over the locked 05ad few-shot baseline.

The locked reference is `bias_shrink4` for k>0 and `stimulus_only` for k=0.

A new model is only interesting if it beats the locked few-shot baseline at the same calibration size.

## Verdict

| target | decision | best_candidate_model | best_k_calibration | best_rmse | locked_reference_model | locked_reference_rmse | best_lift_vs_locked_reference_rmse | rmse_win_margin_vs_locked | mean_delta_rmse_model_minus_locked | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | GO_MODEL_FAMILY_BEATS_LOCKED_FEWSHOT | kernel_residual_shrink4 | 16 | 1.657667 | bias_shrink4 | 1.734361 | 0.076694 | 31.000000 | -0.076916 | candidate beats locked few-shot baseline in pooled and subject-level metrics |
| valence | GO_MODEL_FAMILY_BEATS_LOCKED_FEWSHOT | kernel_residual_shrink4 | 16 | 1.159189 | bias_shrink4 | 1.246118 | 0.086929 | 23.000000 | -0.091414 | candidate beats locked few-shot baseline in pooled and subject-level metrics |


## Best ranking by lift over locked reference

| target | k_calibration | model | n | rmse | lift_vs_stimulus_rmse | locked_reference_model | locked_reference_rmse | lift_vs_locked_reference_rmse | pearson | spearman | ccc | rmse_wins_vs_locked | rmse_losses_vs_locked | rmse_win_margin_vs_locked | mean_delta_rmse_model_minus_locked | worst_regression_delta_rmse | best_gain_delta_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | 16 | kernel_residual_shrink4 | 100800 | 1.657667 | 0.288276 | bias_shrink4 | 1.734361 | 0.076694 | 0.753635 | 0.743985 | 0.712969 | 47 | 16 | 31 | -0.076916 | 0.177319 | -0.524911 |
| arousal | 16 | affine_residual_ridge4 | 100800 | 1.669731 | 0.276213 | bias_shrink4 | 1.734361 | 0.064630 | 0.750199 | 0.743753 | 0.732253 | 35 | 28 | 7 | -0.080289 | 0.128024 | -0.774153 |
| arousal | 16 | affine_residual_ridge1 | 100800 | 1.675424 | 0.270520 | bias_shrink4 | 1.734361 | 0.058937 | 0.748771 | 0.742700 | 0.732086 | 34 | 29 | 5 | -0.074858 | 0.140673 | -0.776712 |
| arousal | 8 | kernel_residual_shrink4 | 151200 | 1.732998 | 0.210161 | bias_shrink4 | 1.766245 | 0.033247 | 0.725100 | 0.716966 | 0.679312 | 42 | 21 | 21 | -0.032882 | 0.287111 | -0.380441 |
| arousal | 4 | kernel_residual_shrink4 | 176400 | 1.798294 | 0.145603 | bias_shrink4 | 1.803261 | 0.004967 | 0.699268 | 0.690993 | 0.649897 | 38 | 25 | 13 | -0.006953 | 0.293323 | -0.232828 |
| arousal | 16 | bias_shrink4 | 100800 | 1.734361 | 0.211583 | bias_shrink4 | 1.734361 | 0.000000 | 0.724839 | 0.721029 | 0.689612 | 0 | 0 | 0 | 0.000000 | 0.000000 | 0.000000 |
| arousal | 8 | bias_shrink4 | 151200 | 1.766245 | 0.176914 | bias_shrink4 | 1.766245 | 0.000000 | 0.711624 | 0.705780 | 0.672950 | 0 | 0 | 0 | 0.000000 | 0.000000 | 0.000000 |
| arousal | 4 | bias_shrink4 | 176400 | 1.803261 | 0.140636 | bias_shrink4 | 1.803261 | 0.000000 | 0.696945 | 0.689062 | 0.653391 | 0 | 0 | 0 | 0.000000 | 0.000000 | 0.000000 |
| arousal | 2 | bias_shrink4 | 189000 | 1.848195 | 0.095374 | bias_shrink4 | 1.848195 | 0.000000 | 0.677899 | 0.668361 | 0.630254 | 0 | 0 | 0 | 0.000000 | 0.000000 | 0.000000 |
| arousal | 1 | bias_shrink4 | 195300 | 1.890484 | 0.054084 | bias_shrink4 | 1.890484 | 0.000000 | 0.659493 | 0.646134 | 0.608650 | 0 | 0 | 0 | 0.000000 | 0.000000 | 0.000000 |
| arousal | 0 | stimulus_only | 2016 | 1.944205 | 0.000000 | stimulus_only | 1.944205 | 0.000000 | 0.634375 | 0.598500 | 0.579381 | 0 | 0 | 0 | 0.000000 | 0.000000 | 0.000000 |
| arousal | 16 | bias_empirical_bayes | 100800 | 1.734540 | 0.211404 | bias_shrink4 | 1.734361 | -0.000179 | 0.724876 | 0.721916 | 0.692456 | 21 | 42 | -21 | -0.000578 | 0.007801 | -0.036617 |
| arousal | 1 | kernel_residual_shrink4 | 195300 | 1.890702 | 0.053866 | bias_shrink4 | 1.890484 | -0.000217 | 0.659374 | 0.645663 | 0.607746 | 40 | 23 | 17 | -0.000927 | 0.057103 | -0.036189 |
| arousal | 16 | bias_shrink2 | 100800 | 1.734584 | 0.211360 | bias_shrink4 | 1.734361 | -0.000223 | 0.725027 | 0.722645 | 0.694697 | 19 | 44 | -25 | -0.000932 | 0.011675 | -0.068494 |
| arousal | 4 | bias_empirical_bayes | 176400 | 1.804173 | 0.139724 | bias_shrink4 | 1.803261 | -0.000912 | 0.696773 | 0.690018 | 0.658886 | 21 | 42 | -21 | -0.000250 | 0.037955 | -0.120511 |
| arousal | 8 | bias_empirical_bayes | 151200 | 1.767369 | 0.175790 | bias_shrink4 | 1.766245 | -0.001124 | 0.711381 | 0.706644 | 0.677078 | 22 | 41 | -19 | -0.000287 | 0.022007 | -0.081324 |
| arousal | 4 | bias_shrink2 | 176400 | 1.804659 | 0.139238 | bias_shrink4 | 1.803261 | -0.001398 | 0.697153 | 0.691357 | 0.664039 | 19 | 44 | -25 | -0.000569 | 0.061911 | -0.276848 |
| arousal | 8 | bias_shrink2 | 151200 | 1.767765 | 0.175394 | bias_shrink4 | 1.766245 | -0.001520 | 0.711612 | 0.707662 | 0.680665 | 19 | 44 | -25 | -0.000703 | 0.035041 | -0.164721 |
| arousal | 2 | kernel_residual_shrink4 | 189000 | 1.850254 | 0.093315 | bias_shrink4 | 1.848195 | -0.002059 | 0.677051 | 0.666998 | 0.625946 | 40 | 23 | 17 | -0.000788 | 0.186682 | -0.112861 |
| arousal | 16 | bias_shrink1 | 100800 | 1.737064 | 0.208879 | bias_shrink4 | 1.734361 | -0.002703 | 0.724500 | 0.723097 | 0.697039 | 18 | 45 | -27 | 0.001056 | 0.019203 | -0.088452 |
| arousal | 2 | bias_empirical_bayes | 189000 | 1.851054 | 0.092515 | bias_shrink4 | 1.848195 | -0.002859 | 0.676984 | 0.668706 | 0.635417 | 20 | 43 | -23 | 0.002929 | 0.057351 | -0.131223 |
| arousal | 8 | affine_residual_ridge4 | 151200 | 1.769557 | 0.173602 | bias_shrink4 | 1.766245 | -0.003312 | 0.718896 | 0.714509 | 0.706535 | 24 | 39 | -15 | -0.017384 | 0.285210 | -0.811087 |
| arousal | 1 | bias_empirical_bayes | 195300 | 1.894475 | 0.050093 | bias_shrink4 | 1.890484 | -0.003991 | 0.658036 | 0.645584 | 0.612179 | 21 | 42 | -21 | 0.005730 | 0.048257 | -0.103833 |
| arousal | 2 | bias_shrink2 | 189000 | 1.853122 | 0.090447 | bias_shrink4 | 1.848195 | -0.004927 | 0.676924 | 0.669783 | 0.640964 | 18 | 45 | -27 | 0.005242 | 0.100432 | -0.343576 |
| arousal | 1 | bias_shrink2 | 195300 | 1.897816 | 0.046752 | bias_shrink4 | 1.890484 | -0.007332 | 0.657308 | 0.645972 | 0.616593 | 16 | 47 | -31 | 0.011390 | 0.091636 | -0.313566 |
| arousal | 16 | bias_mean | 100800 | 1.741925 | 0.204019 | bias_shrink4 | 1.734361 | -0.007563 | 0.723404 | 0.723175 | 0.699114 | 13 | 50 | -37 | 0.005584 | 0.028251 | -0.092085 |
| arousal | 16 | bias_shrink8 | 100800 | 1.743440 | 0.202504 | bias_shrink4 | 1.734361 | -0.009079 | 0.721604 | 0.716456 | 0.679299 | 36 | 27 | 9 | 0.011006 | 0.175103 | -0.015447 |
| arousal | 8 | bias_shrink1 | 151200 | 1.775915 | 0.167244 | bias_shrink4 | 1.766245 | -0.009670 | 0.709634 | 0.707332 | 0.683856 | 16 | 47 | -31 | 0.006067 | 0.066220 | -0.227302 |
| arousal | 1 | bias_shrink8 | 195300 | 1.905049 | 0.039518 | bias_shrink4 | 1.890484 | -0.014565 | 0.652794 | 0.637749 | 0.598168 | 37 | 26 | 11 | 0.009815 | 0.232809 | -0.039409 |
| arousal | 8 | bias_shrink8 | 151200 | 1.782399 | 0.160760 | bias_shrink4 | 1.766245 | -0.016155 | 0.705490 | 0.698642 | 0.658160 | 39 | 24 | 15 | 0.017646 | 0.300794 | -0.036958 |
| arousal | 16 | bias_huber | 100800 | 1.751849 | 0.194095 | bias_shrink4 | 1.734361 | -0.017488 | 0.720485 | 0.720926 | 0.697370 | 14 | 49 | -35 | 0.014576 | 0.065950 | -0.087279 |
| arousal | 4 | bias_shrink1 | 176400 | 1.823701 | 0.120197 | bias_shrink4 | 1.803261 | -0.020439 | 0.692167 | 0.689030 | 0.667707 | 17 | 46 | -29 | 0.016066 | 0.120150 | -0.405148 |
| arousal | 2 | bias_shrink8 | 189000 | 1.869968 | 0.073601 | bias_shrink4 | 1.848195 | -0.021773 | 0.668436 | 0.657235 | 0.614584 | 38 | 25 | 13 | 0.017790 | 0.330595 | -0.053446 |
| arousal | 4 | bias_shrink8 | 176400 | 1.826762 | 0.117135 | bias_shrink4 | 1.803261 | -0.023501 | 0.687422 | 0.678742 | 0.635677 | 37 | 26 | 11 | 0.022266 | 0.370031 | -0.048879 |
| arousal | 16 | bias_trimmed_mean | 100800 | 1.757982 | 0.187961 | bias_shrink4 | 1.734361 | -0.023621 | 0.718697 | 0.719102 | 0.695845 | 12 | 51 | -39 | 0.020286 | 0.067092 | -0.089168 |
| arousal | 8 | bias_mean | 151200 | 1.794000 | 0.149159 | bias_shrink4 | 1.766245 | -0.027756 | 0.705378 | 0.705261 | 0.685767 | 15 | 48 | -33 | 0.023001 | 0.113645 | -0.245728 |
| arousal | 8 | affine_residual_ridge1 | 151200 | 1.806901 | 0.136258 | bias_shrink4 | 1.766245 | -0.040656 | 0.709432 | 0.707172 | 0.700221 | 20 | 43 | -23 | 0.017837 | 0.362710 | -0.842293 |
| arousal | 8 | bias_trimmed_mean | 151200 | 1.809499 | 0.133659 | bias_shrink4 | 1.766245 | -0.043255 | 0.700571 | 0.700979 | 0.682277 | 11 | 52 | -41 | 0.037437 | 0.172955 | -0.229506 |
| arousal | 2 | bias_shrink1 | 189000 | 1.893410 | 0.050159 | bias_shrink4 | 1.848195 | -0.045215 | 0.665429 | 0.662129 | 0.642349 | 16 | 47 | -31 | 0.042146 | 0.234361 | -0.576967 |
| arousal | 8 | bias_huber | 151200 | 1.812678 | 0.130481 | bias_shrink4 | 1.766245 | -0.046434 | 0.699652 | 0.700085 | 0.681688 | 11 | 52 | -41 | 0.040525 | 0.157300 | -0.228911 |


## Worst failure subjects for best candidate

| target | subject_id | best_candidate_model | k_calibration | locked_reference_model | candidate_rmse | locked_rmse | delta_rmse_candidate_minus_locked | candidate_lift_vs_stimulus_rmse | locked_lift_vs_stimulus_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | 42 | kernel_residual_shrink4 | 16 | bias_shrink4 | 1.924969 | 1.747650 | 0.177319 | 0.687281 | 0.864600 |
| arousal | 2 | kernel_residual_shrink4 | 16 | bias_shrink4 | 1.850398 | 1.697352 | 0.153046 | 0.882289 | 1.035336 |
| arousal | 14 | kernel_residual_shrink4 | 16 | bias_shrink4 | 1.093865 | 0.944248 | 0.149617 | 0.714397 | 0.864014 |
| arousal | 55 | kernel_residual_shrink4 | 16 | bias_shrink4 | 1.215329 | 1.107459 | 0.107870 | 1.239220 | 1.347090 |
| arousal | 40 | kernel_residual_shrink4 | 16 | bias_shrink4 | 2.915243 | 2.820307 | 0.094936 | 0.018003 | 0.112940 |
| arousal | 20 | kernel_residual_shrink4 | 16 | bias_shrink4 | 1.402426 | 1.322085 | 0.080341 | 0.223263 | 0.303605 |
| arousal | 23 | kernel_residual_shrink4 | 16 | bias_shrink4 | 1.293846 | 1.223860 | 0.069986 | 0.161092 | 0.231077 |
| arousal | 5 | kernel_residual_shrink4 | 16 | bias_shrink4 | 1.650657 | 1.595285 | 0.055372 | 0.130956 | 0.186329 |
| arousal | 26 | kernel_residual_shrink4 | 16 | bias_shrink4 | 1.860844 | 1.805923 | 0.054921 | 0.251097 | 0.306018 |
| arousal | 1 | kernel_residual_shrink4 | 16 | bias_shrink4 | 2.027675 | 1.980213 | 0.047462 | -0.107281 | -0.059819 |
| arousal | 64 | kernel_residual_shrink4 | 16 | bias_shrink4 | 1.592448 | 1.562699 | 0.029748 | -0.087397 | -0.057649 |
| arousal | 29 | kernel_residual_shrink4 | 16 | bias_shrink4 | 1.425203 | 1.396413 | 0.028790 | 0.026893 | 0.055683 |
| arousal | 30 | kernel_residual_shrink4 | 16 | bias_shrink4 | 1.018774 | 0.995522 | 0.023252 | -0.058534 | -0.035282 |
| arousal | 32 | kernel_residual_shrink4 | 16 | bias_shrink4 | 1.331702 | 1.320132 | 0.011570 | -0.036261 | -0.024691 |
| arousal | 38 | kernel_residual_shrink4 | 16 | bias_shrink4 | 1.428552 | 1.419320 | 0.009232 | -0.045339 | -0.036107 |
| arousal | 34 | kernel_residual_shrink4 | 16 | bias_shrink4 | 1.338964 | 1.337417 | 0.001547 | 0.030068 | 0.031615 |
| arousal | 18 | kernel_residual_shrink4 | 16 | bias_shrink4 | 2.188025 | 2.191178 | -0.003153 | 0.018189 | 0.015036 |
| arousal | 3 | kernel_residual_shrink4 | 16 | bias_shrink4 | 1.458800 | 1.463903 | -0.005103 | 0.422759 | 0.417656 |
| arousal | 15 | kernel_residual_shrink4 | 16 | bias_shrink4 | 1.688290 | 1.695198 | -0.006908 | 0.013856 | 0.006947 |
| arousal | 53 | kernel_residual_shrink4 | 16 | bias_shrink4 | 1.094049 | 1.105335 | -0.011286 | 0.034127 | 0.022841 |
| arousal | 27 | kernel_residual_shrink4 | 16 | bias_shrink4 | 1.378094 | 1.392538 | -0.014444 | 0.171336 | 0.156891 |
| arousal | 52 | kernel_residual_shrink4 | 16 | bias_shrink4 | 1.956674 | 1.972373 | -0.015699 | 0.006753 | -0.008945 |
| arousal | 56 | kernel_residual_shrink4 | 16 | bias_shrink4 | 1.372986 | 1.392568 | -0.019582 | 0.076920 | 0.057338 |
| arousal | 8 | kernel_residual_shrink4 | 16 | bias_shrink4 | 1.695960 | 1.716806 | -0.020845 | 0.225983 | 0.205138 |
| arousal | 17 | kernel_residual_shrink4 | 16 | bias_shrink4 | 1.329588 | 1.354772 | -0.025183 | 0.117999 | 0.092816 |
| arousal | 25 | kernel_residual_shrink4 | 16 | bias_shrink4 | 2.240368 | 2.272631 | -0.032263 | -0.039125 | -0.071388 |
| arousal | 13 | kernel_residual_shrink4 | 16 | bias_shrink4 | 1.480032 | 1.516186 | -0.036154 | 0.949000 | 0.912846 |
| arousal | 28 | kernel_residual_shrink4 | 16 | bias_shrink4 | 1.324604 | 1.364547 | -0.039944 | 0.426403 | 0.386459 |
| arousal | 48 | kernel_residual_shrink4 | 16 | bias_shrink4 | 1.283350 | 1.333718 | -0.050368 | 0.004788 | -0.045579 |
| arousal | 47 | kernel_residual_shrink4 | 16 | bias_shrink4 | 2.392262 | 2.443580 | -0.051319 | 0.084869 | 0.033550 |


## Model family

- `stimulus_only`
- `bias_mean`
- `bias_shrink1`
- `bias_shrink2`
- `bias_shrink4`
- `bias_shrink8`
- `bias_empirical_bayes`
- `bias_median`
- `bias_huber`
- `bias_trimmed_mean`
- `affine_residual_ridge1`
- `affine_residual_ridge4`
- `kernel_residual_shrink4`



## Interpretation

- If `GO_MODEL_FAMILY_BEATS_LOCKED_FEWSHOT` appears, we have a calibration method worth confirming in the next step.
- If only `WEAK_GO` appears, it means pooled gain exists but subject-level stability is not yet enough.
- If `NO_GO` appears, the simple locked shrinkage few-shot baseline is still the strongest honest baseline.
