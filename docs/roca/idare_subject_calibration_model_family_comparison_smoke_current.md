# I-DARE Subject Calibration Model-Family Comparison

This report tests whether any subject-calibration family improves over the locked 05ad few-shot baseline.

The locked reference is `bias_shrink4` for k>0 and `stimulus_only` for k=0.

A new model is only interesting if it beats the locked few-shot baseline at the same calibration size.

## Verdict

| target | decision | best_candidate_model | best_k_calibration | best_rmse | locked_reference_model | locked_reference_rmse | best_lift_vs_locked_reference_rmse | rmse_win_margin_vs_locked | mean_delta_rmse_model_minus_locked | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | WEAK_GO_MODEL_FAMILY_NEEDS_CONFIRMATION | bias_shrink1 | 2 | 1.933934 | bias_shrink4 | 2.061966 | 0.128032 | 2.000000 | -0.136182 | subject win margin < 3 |
| valence | WEAK_GO_MODEL_FAMILY_NEEDS_CONFIRMATION | kernel_residual_shrink4 | 8 | 1.277145 | bias_shrink4 | 1.302379 | 0.025234 | -4.000000 | -0.037121 | subject win margin < 3 |


## Best ranking by lift over locked reference

| target | k_calibration | model | n | rmse | lift_vs_stimulus_rmse | locked_reference_model | locked_reference_rmse | lift_vs_locked_reference_rmse | pearson | spearman | ccc | rmse_wins_vs_locked | rmse_losses_vs_locked | rmse_win_margin_vs_locked | mean_delta_rmse_model_minus_locked | worst_regression_delta_rmse | best_gain_delta_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | 2 | bias_shrink1 | 4800 | 1.933934 | 0.473961 | bias_shrink4 | 2.061966 | 0.128032 | 0.633074 | 0.633015 | 0.605072 | 5 | 3 | 2 | -0.136182 | 0.175376 | -0.510327 |
| arousal | 1 | bias_shrink1 | 4960 | 2.115343 | 0.300405 | bias_shrink4 | 2.231848 | 0.116504 | 0.539700 | 0.536772 | 0.498515 | 4 | 4 | 0 | -0.110598 | 0.224853 | -0.496407 |
| arousal | 2 | bias_empirical_bayes | 4800 | 1.955441 | 0.452454 | bias_shrink4 | 2.061966 | 0.106525 | 0.625286 | 0.624589 | 0.599993 | 5 | 3 | 2 | -0.118566 | 0.246106 | -0.479025 |
| arousal | 2 | bias_shrink2 | 4800 | 1.966360 | 0.441535 | bias_shrink4 | 2.061966 | 0.095606 | 0.608581 | 0.606622 | 0.555322 | 5 | 3 | 2 | -0.096056 | 0.075620 | -0.323398 |
| arousal | 8 | affine_residual_ridge4 | 3840 | 1.732570 | 0.675277 | bias_shrink4 | 1.815023 | 0.082453 | 0.720005 | 0.718346 | 0.705496 | 5 | 3 | 2 | -0.111436 | 0.176604 | -0.632820 |
| arousal | 1 | bias_shrink2 | 4960 | 2.154332 | 0.261416 | bias_shrink4 | 2.231848 | 0.077515 | 0.504981 | 0.505132 | 0.441802 | 5 | 3 | 2 | -0.071344 | 0.078950 | -0.248105 |
| arousal | 16 | affine_residual_ridge4 | 2560 | 1.710733 | 0.729361 | bias_shrink4 | 1.785587 | 0.074854 | 0.727739 | 0.723800 | 0.705243 | 5 | 3 | 2 | -0.106703 | 0.105171 | -0.619787 |
| arousal | 1 | bias_empirical_bayes | 4960 | 2.158133 | 0.257616 | bias_shrink4 | 2.231848 | 0.073715 | 0.523404 | 0.520527 | 0.489925 | 4 | 4 | 0 | -0.073759 | 0.360777 | -0.437012 |
| arousal | 4 | bias_shrink1 | 4480 | 1.864870 | 0.537357 | bias_shrink4 | 1.936899 | 0.072029 | 0.669069 | 0.671034 | 0.647533 | 5 | 3 | 2 | -0.080526 | 0.083239 | -0.297775 |
| arousal | 16 | affine_residual_ridge1 | 2560 | 1.720450 | 0.719644 | bias_shrink4 | 1.785587 | 0.065137 | 0.724533 | 0.720971 | 0.702974 | 4 | 4 | 0 | -0.097932 | 0.118144 | -0.618875 |
| arousal | 4 | bias_empirical_bayes | 4480 | 1.872890 | 0.529337 | bias_shrink4 | 1.936899 | 0.064009 | 0.666174 | 0.666962 | 0.645578 | 5 | 3 | 2 | -0.073641 | 0.106335 | -0.291356 |
| arousal | 4 | bias_shrink2 | 4480 | 1.874201 | 0.528026 | bias_shrink4 | 1.936899 | 0.062698 | 0.657557 | 0.657920 | 0.618060 | 5 | 3 | 2 | -0.067006 | 0.042487 | -0.227385 |
| arousal | 8 | bias_shrink1 | 3840 | 1.754790 | 0.653056 | bias_shrink4 | 1.815023 | 0.060233 | 0.707378 | 0.708771 | 0.683897 | 5 | 3 | 2 | -0.066526 | 0.032616 | -0.208108 |
| arousal | 8 | bias_mean | 3840 | 1.757249 | 0.650597 | bias_shrink4 | 1.815023 | 0.057774 | 0.713118 | 0.715393 | 0.700770 | 5 | 3 | 2 | -0.066305 | 0.054944 | -0.229002 |
| arousal | 8 | bias_empirical_bayes | 3840 | 1.757639 | 0.650207 | bias_shrink4 | 1.815023 | 0.057384 | 0.706522 | 0.707284 | 0.683411 | 5 | 3 | 2 | -0.064302 | 0.038560 | -0.198570 |
| arousal | 8 | bias_trimmed_mean | 3840 | 1.763964 | 0.643883 | bias_shrink4 | 1.815023 | 0.051060 | 0.714171 | 0.715576 | 0.704653 | 5 | 3 | 2 | -0.058973 | 0.064389 | -0.253664 |
| arousal | 8 | bias_shrink2 | 3840 | 1.768652 | 0.639195 | bias_shrink4 | 1.815023 | 0.046371 | 0.699382 | 0.700123 | 0.664890 | 5 | 3 | 2 | -0.050059 | 0.017607 | -0.149755 |
| arousal | 8 | bias_huber | 3840 | 1.770063 | 0.637784 | bias_shrink4 | 1.815023 | 0.044960 | 0.713099 | 0.714574 | 0.704373 | 5 | 3 | 2 | -0.053281 | 0.086421 | -0.245831 |
| arousal | 8 | affine_residual_ridge1 | 3840 | 1.775828 | 0.632019 | bias_shrink4 | 1.815023 | 0.039195 | 0.707276 | 0.707432 | 0.695736 | 3 | 5 | -2 | -0.071125 | 0.235316 | -0.619855 |
| arousal | 16 | bias_mean | 2560 | 1.757219 | 0.682875 | bias_shrink4 | 1.785587 | 0.028368 | 0.713558 | 0.714251 | 0.696592 | 5 | 3 | 2 | -0.032902 | 0.040578 | -0.151515 |
| arousal | 16 | bias_shrink1 | 2560 | 1.758647 | 0.681446 | bias_shrink4 | 1.785587 | 0.026939 | 0.710111 | 0.710808 | 0.687077 | 5 | 3 | 2 | -0.030758 | 0.027489 | -0.125064 |
| arousal | 16 | bias_empirical_bayes | 2560 | 1.760431 | 0.679663 | bias_shrink4 | 1.785587 | 0.025156 | 0.709592 | 0.709836 | 0.686709 | 5 | 3 | 2 | -0.029293 | 0.031263 | -0.118460 |
| arousal | 16 | bias_shrink2 | 2560 | 1.764786 | 0.675307 | bias_shrink4 | 1.785587 | 0.020800 | 0.706018 | 0.706566 | 0.676925 | 5 | 3 | 2 | -0.023469 | 0.016654 | -0.088457 |
| arousal | 4 | bias_mean | 4480 | 1.919860 | 0.482367 | bias_shrink4 | 1.936899 | 0.017039 | 0.673387 | 0.676299 | 0.668907 | 5 | 3 | 2 | -0.027785 | 0.154946 | -0.196127 |
| arousal | 4 | bias_trimmed_mean | 4480 | 1.919860 | 0.482367 | bias_shrink4 | 1.936899 | 0.017039 | 0.673387 | 0.676322 | 0.668907 | 5 | 3 | 2 | -0.027785 | 0.154946 | -0.196127 |
| arousal | 16 | bias_huber | 2560 | 1.769541 | 0.670553 | bias_shrink4 | 1.785587 | 0.016046 | 0.712468 | 0.712547 | 0.699703 | 5 | 3 | 2 | -0.021967 | 0.078774 | -0.173099 |
| arousal | 16 | bias_trimmed_mean | 2560 | 1.772623 | 0.667471 | bias_shrink4 | 1.785587 | 0.012964 | 0.713714 | 0.713224 | 0.702749 | 5 | 3 | 2 | -0.019090 | 0.094827 | -0.173085 |
| arousal | 8 | bias_median | 3840 | 1.806675 | 0.601172 | bias_shrink4 | 1.815023 | 0.008349 | 0.708939 | 0.709263 | 0.704182 | 4 | 4 | 0 | -0.015127 | 0.169937 | -0.258470 |
| arousal | 16 | bias_median | 2560 | 1.783577 | 0.656517 | bias_shrink4 | 1.785587 | 0.002010 | 0.714165 | 0.713345 | 0.705766 | 3 | 5 | -2 | -0.004772 | 0.094992 | -0.192191 |
| arousal | 16 | bias_shrink4 | 2560 | 1.785587 | 0.654507 | bias_shrink4 | 1.785587 | 0.000000 | 0.696319 | 0.696352 | 0.655799 | 0 | 0 | 0 | 0.000000 | 0.000000 | 0.000000 |
| arousal | 8 | bias_shrink4 | 3840 | 1.815023 | 0.592823 | bias_shrink4 | 1.815023 | 0.000000 | 0.679307 | 0.677431 | 0.626384 | 0 | 0 | 0 | 0.000000 | 0.000000 | 0.000000 |
| arousal | 4 | bias_shrink4 | 4480 | 1.936899 | 0.465328 | bias_shrink4 | 1.936899 | 0.000000 | 0.625566 | 0.623326 | 0.561453 | 0 | 0 | 0 | 0.000000 | 0.000000 | 0.000000 |
| arousal | 2 | bias_shrink4 | 4800 | 2.061966 | 0.345929 | bias_shrink4 | 2.061966 | 0.000000 | 0.553656 | 0.552044 | 0.480153 | 0 | 0 | 0 | 0.000000 | 0.000000 | 0.000000 |
| arousal | 1 | bias_shrink4 | 4960 | 2.231848 | 0.183901 | bias_shrink4 | 2.231848 | 0.000000 | 0.450178 | 0.454289 | 0.380043 | 0 | 0 | 0 | 0.000000 | 0.000000 | 0.000000 |
| arousal | 0 | stimulus_only | 256 | 2.411442 | 0.000000 | stimulus_only | 2.411442 | 0.000000 | 0.320173 | 0.321021 | 0.267534 | 0 | 0 | 0 | 0.000000 | 0.000000 | 0.000000 |
| arousal | 4 | affine_residual_ridge4 | 4480 | 1.937027 | 0.465200 | bias_shrink4 | 1.936899 | -0.000128 | 0.664820 | 0.663196 | 0.660333 | 4 | 4 | 0 | -0.025581 | 0.278824 | -0.459475 |
| arousal | 2 | bias_huber | 4800 | 2.064740 | 0.343155 | bias_shrink4 | 2.061966 | -0.002774 | 0.639248 | 0.642036 | 0.638610 | 4 | 4 | 0 | -0.018426 | 0.436315 | -0.411135 |
| arousal | 2 | bias_mean | 4800 | 2.064740 | 0.343155 | bias_shrink4 | 2.061966 | -0.002774 | 0.639248 | 0.642036 | 0.638610 | 4 | 4 | 0 | -0.018426 | 0.436315 | -0.411135 |
| arousal | 2 | bias_median | 4800 | 2.064740 | 0.343155 | bias_shrink4 | 2.061966 | -0.002774 | 0.639248 | 0.642036 | 0.638610 | 4 | 4 | 0 | -0.018426 | 0.436315 | -0.411135 |
| arousal | 2 | bias_trimmed_mean | 4800 | 2.064740 | 0.343155 | bias_shrink4 | 2.061966 | -0.002774 | 0.639248 | 0.642036 | 0.638610 | 4 | 4 | 0 | -0.018426 | 0.436315 | -0.411135 |


## Worst failure subjects for best candidate

| target | subject_id | best_candidate_model | k_calibration | locked_reference_model | candidate_rmse | locked_rmse | delta_rmse_candidate_minus_locked | candidate_lift_vs_stimulus_rmse | locked_lift_vs_stimulus_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | 1 | bias_shrink1 | 2 | bias_shrink4 | 2.524095 | 2.348719 | 0.175376 | -0.245348 | -0.069972 |
| arousal | 9 | bias_shrink1 | 2 | bias_shrink4 | 1.872174 | 1.787453 | 0.084720 | -0.080052 | 0.004669 |
| arousal | 5 | bias_shrink1 | 2 | bias_shrink4 | 1.722313 | 1.664000 | 0.058313 | -0.054541 | 0.003772 |
| arousal | 8 | bias_shrink1 | 2 | bias_shrink4 | 2.133820 | 2.199903 | -0.066084 | 0.361789 | 0.295705 |
| arousal | 2 | bias_shrink1 | 2 | bias_shrink4 | 2.084241 | 2.241353 | -0.157112 | 0.493569 | 0.336457 |
| arousal | 7 | bias_shrink1 | 2 | bias_shrink4 | 1.231931 | 1.536832 | -0.304902 | 0.813996 | 0.509094 |
| arousal | 3 | bias_shrink1 | 2 | bias_shrink4 | 1.397925 | 1.767363 | -0.369438 | 0.914537 | 0.545100 |
| arousal | 6 | bias_shrink1 | 2 | bias_shrink4 | 2.170086 | 2.680413 | -0.510327 | 1.406415 | 0.896088 |
| valence | 5 | kernel_residual_shrink4 | 8 | bias_shrink4 | 1.584907 | 1.563384 | 0.021523 | -0.059568 | -0.038045 |
| valence | 8 | kernel_residual_shrink4 | 8 | bias_shrink4 | 1.260845 | 1.247421 | 0.013424 | -0.011679 | 0.001746 |
| valence | 9 | kernel_residual_shrink4 | 8 | bias_shrink4 | 1.299579 | 1.289767 | 0.009812 | 0.068158 | 0.077970 |
| valence | 2 | kernel_residual_shrink4 | 8 | bias_shrink4 | 1.560698 | 1.551581 | 0.009116 | -0.025524 | -0.016407 |
| valence | 3 | kernel_residual_shrink4 | 8 | bias_shrink4 | 1.306376 | 1.303903 | 0.002473 | -0.039803 | -0.037329 |
| valence | 1 | kernel_residual_shrink4 | 8 | bias_shrink4 | 1.208030 | 1.205938 | 0.002092 | 0.015204 | 0.017296 |
| valence | 6 | kernel_residual_shrink4 | 8 | bias_shrink4 | 1.006166 | 1.115140 | -0.108974 | 0.075334 | -0.033640 |
| valence | 7 | kernel_residual_shrink4 | 8 | bias_shrink4 | 0.802574 | 1.049008 | -0.246434 | 0.206589 | -0.039845 |


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
