# I-DARE Few-Shot Residual Subject Calibration Audit

This audit tests whether the subject-structured residual found in 05z can be exploited by a few calibration labels from the held-out subject.

## Models

- `stimulus_only`: LOSO stimulus prior.
- `stimulus_plus_fewshot_bias`: stimulus prior plus the mean residual estimated from k calibration trials of the same held-out subject.
- `stimulus_plus_fewshot_bias_shrink4`: conservative shrinkage version of the same subject-bias estimate.

## Verdict

| target | decision | best_model | best_k_calibration | best_lift_vs_stimulus_rmse | best_lift_vs_stimulus_residual_rmse | best_rmse | best_residual_rmse | rmse_win_margin | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | GO_FEWSHOT_SUBJECT_CALIBRATION | stimulus_plus_fewshot_bias | 16 | 0.650859 | 0.650859 | 1.751666 | 1.751666 | 4.000000 | few-shot subject bias beats stimulus-only in pooled and subject-level residual metrics |
| valence | WEAK_GO_FEWSHOT_CALIBRATION_NEEDS_CONFIRMATION | stimulus_plus_fewshot_bias_shrink4 | 16 | 0.009078 | 0.009078 | 1.283849 | 1.283849 | 0.000000 | few-shot calibration has positive pooled lift but does not meet practical margin |


## Main metrics

| target | k_calibration | model | n | rmse | lift_vs_stimulus_rmse | residual_rmse | lift_vs_stimulus_residual_rmse | pearson | ccc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | 0 | stimulus_only | 256 | 2.411442 | 0.000000 | 2.411442 | 0.000000 | 0.320173 | 0.267534 |
| arousal | 0 | stimulus_plus_fewshot_bias | 256 | 2.411442 | 0.000000 | 2.411442 | 0.000000 | 0.320173 | 0.267534 |
| arousal | 0 | stimulus_plus_fewshot_bias_shrink4 | 256 | 2.411442 | 0.000000 | 2.411442 | 0.000000 | 0.320173 | 0.267534 |
| arousal | 1 | stimulus_only | 12400 | 2.409046 | 0.000000 | 2.409046 | 0.000000 | 0.322076 | 0.269042 |
| arousal | 1 | stimulus_plus_fewshot_bias | 12400 | 2.414961 | -0.005915 | 2.414961 | -0.005915 | 0.565136 | 0.563360 |
| arousal | 1 | stimulus_plus_fewshot_bias_shrink4 | 12400 | 2.195794 | 0.213252 | 2.195794 | 0.213252 | 0.472100 | 0.399959 |
| arousal | 2 | stimulus_only | 12000 | 2.413336 | 0.000000 | 2.413336 | 0.000000 | 0.318924 | 0.266544 |
| arousal | 2 | stimulus_plus_fewshot_bias | 12000 | 2.073218 | 0.340118 | 2.073218 | 0.340118 | 0.625014 | 0.623064 |
| arousal | 2 | stimulus_plus_fewshot_bias_shrink4 | 12000 | 2.094399 | 0.318937 | 2.094399 | 0.318937 | 0.536732 | 0.462822 |
| arousal | 4 | stimulus_only | 11200 | 2.406393 | 0.000000 | 2.406393 | 0.000000 | 0.322912 | 0.270586 |
| arousal | 4 | stimulus_plus_fewshot_bias | 11200 | 1.903374 | 0.503019 | 1.903374 | 0.503019 | 0.673327 | 0.668039 |
| arousal | 4 | stimulus_plus_fewshot_bias_shrink4 | 11200 | 1.942828 | 0.463566 | 1.942828 | 0.463566 | 0.620368 | 0.555615 |
| arousal | 8 | stimulus_only | 9600 | 2.413900 | 0.000000 | 2.413900 | 0.000000 | 0.311840 | 0.261887 |
| arousal | 8 | stimulus_plus_fewshot_bias | 9600 | 1.798035 | 0.615864 | 1.798035 | 0.615864 | 0.699123 | 0.688397 |
| arousal | 8 | stimulus_plus_fewshot_bias_shrink4 | 9600 | 1.835907 | 0.577993 | 1.835907 | 0.577993 | 0.668293 | 0.617903 |
| arousal | 16 | stimulus_only | 6400 | 2.402525 | 0.000000 | 2.402525 | 0.000000 | 0.322788 | 0.270440 |
| arousal | 16 | stimulus_plus_fewshot_bias | 6400 | 1.751666 | 0.650859 | 1.751666 | 0.650859 | 0.714839 | 0.702061 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 6400 | 1.762086 | 0.640439 | 1.762086 | 0.640439 | 0.702038 | 0.666745 |
| valence | 0 | stimulus_only | 256 | 1.289924 | 0.000000 | 1.289924 | 0.000000 | 0.876018 | 0.871970 |
| valence | 0 | stimulus_plus_fewshot_bias | 256 | 1.289924 | 0.000000 | 1.289924 | 0.000000 | 0.876018 | 0.871970 |
| valence | 0 | stimulus_plus_fewshot_bias_shrink4 | 256 | 1.289924 | 0.000000 | 1.289924 | 0.000000 | 0.876018 | 0.871970 |
| valence | 1 | stimulus_only | 12400 | 1.288328 | 0.000000 | 1.288328 | 0.000000 | 0.876360 | 0.872238 |
| valence | 1 | stimulus_plus_fewshot_bias | 12400 | 1.820565 | -0.532237 | 1.820565 | -0.532237 | 0.777302 | 0.775761 |
| valence | 1 | stimulus_plus_fewshot_bias_shrink4 | 12400 | 1.305410 | -0.017082 | 1.305410 | -0.017082 | 0.873233 | 0.869544 |
| valence | 2 | stimulus_only | 12000 | 1.289390 | 0.000000 | 1.289390 | 0.000000 | 0.876099 | 0.872123 |
| valence | 2 | stimulus_plus_fewshot_bias | 12000 | 1.537112 | -0.247722 | 1.537112 | -0.247722 | 0.829698 | 0.829334 |
| valence | 2 | stimulus_plus_fewshot_bias_shrink4 | 12000 | 1.304818 | -0.015427 | 1.304818 | -0.015427 | 0.873301 | 0.869922 |
| valence | 4 | stimulus_only | 11200 | 1.292020 | 0.000000 | 1.292020 | 0.000000 | 0.875451 | 0.871516 |
| valence | 4 | stimulus_plus_fewshot_bias | 11200 | 1.391988 | -0.099968 | 1.391988 | -0.099968 | 0.856969 | 0.855285 |
| valence | 4 | stimulus_plus_fewshot_bias_shrink4 | 11200 | 1.303563 | -0.011543 | 1.303563 | -0.011543 | 0.873457 | 0.870152 |
| valence | 8 | stimulus_only | 9600 | 1.288690 | 0.000000 | 1.288690 | 0.000000 | 0.876486 | 0.872365 |
| valence | 8 | stimulus_plus_fewshot_bias | 9600 | 1.334801 | -0.046112 | 1.334801 | -0.046112 | 0.868132 | 0.865564 |
| valence | 8 | stimulus_plus_fewshot_bias_shrink4 | 9600 | 1.295204 | -0.006515 | 1.295204 | -0.006515 | 0.875480 | 0.872028 |
| valence | 16 | stimulus_only | 6400 | 1.292926 | 0.000000 | 1.292926 | 0.000000 | 0.875619 | 0.871166 |
| valence | 16 | stimulus_plus_fewshot_bias | 6400 | 1.294167 | -0.001241 | 1.294167 | -0.001241 | 0.875781 | 0.872330 |
| valence | 16 | stimulus_plus_fewshot_bias_shrink4 | 6400 | 1.283849 | 0.009078 | 1.283849 | 0.009078 | 0.877656 | 0.873832 |


## Binary metrics

| target | k_calibration | model | label_policy | accuracy | balanced_accuracy | macro_f1 | auroc | lift_vs_stimulus_accuracy | lift_vs_stimulus_balanced_accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | 0 | stimulus_only | midpoint_as_high | 0.617188 | 0.619048 | 0.616977 | 0.651812 | 0.000000 | 0.000000 |
| arousal | 0 | stimulus_plus_fewshot_bias | midpoint_as_high | 0.617188 | 0.619048 | 0.616977 | 0.651812 | 0.000000 | 0.000000 |
| arousal | 0 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_high | 0.617188 | 0.619048 | 0.616977 | 0.651812 | 0.000000 | 0.000000 |
| arousal | 0 | stimulus_only | midpoint_as_low | 0.613281 | 0.606732 | 0.605915 | 0.611080 | 0.000000 | 0.000000 |
| arousal | 0 | stimulus_plus_fewshot_bias | midpoint_as_low | 0.613281 | 0.606732 | 0.605915 | 0.611080 | 0.000000 | 0.000000 |
| arousal | 0 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_low | 0.613281 | 0.606732 | 0.605915 | 0.611080 | 0.000000 | 0.000000 |
| arousal | 1 | stimulus_only | midpoint_as_high | 0.618306 | 0.620101 | 0.618072 | 0.652395 | 0.000000 | 0.000000 |
| arousal | 1 | stimulus_plus_fewshot_bias | midpoint_as_high | 0.694274 | 0.696284 | 0.694040 | 0.774115 | 0.075968 | 0.076183 |
| arousal | 1 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_high | 0.671210 | 0.673502 | 0.670782 | 0.727232 | 0.052903 | 0.053400 |
| arousal | 1 | stimulus_only | midpoint_as_low | 0.614516 | 0.607922 | 0.607132 | 0.613110 | 0.000000 | 0.000000 |
| arousal | 1 | stimulus_plus_fewshot_bias | midpoint_as_low | 0.708710 | 0.703536 | 0.702637 | 0.782723 | 0.094194 | 0.095614 |
| arousal | 1 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_low | 0.656290 | 0.650299 | 0.649435 | 0.702143 | 0.041774 | 0.042377 |
| arousal | 2 | stimulus_only | midpoint_as_high | 0.617250 | 0.619145 | 0.617049 | 0.651079 | 0.000000 | 0.000000 |
| arousal | 2 | stimulus_plus_fewshot_bias | midpoint_as_high | 0.723417 | 0.725181 | 0.723351 | 0.806147 | 0.106167 | 0.106036 |
| arousal | 2 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_high | 0.689167 | 0.691399 | 0.688914 | 0.758028 | 0.071917 | 0.072254 |
| arousal | 2 | stimulus_only | midpoint_as_low | 0.612500 | 0.605952 | 0.605143 | 0.608971 | 0.000000 | 0.000000 |
| arousal | 2 | stimulus_plus_fewshot_bias | midpoint_as_low | 0.739583 | 0.738164 | 0.735500 | 0.815027 | 0.127083 | 0.132212 |
| arousal | 2 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_low | 0.674583 | 0.670291 | 0.668805 | 0.737314 | 0.062083 | 0.064338 |
| arousal | 4 | stimulus_only | midpoint_as_high | 0.618214 | 0.620206 | 0.618085 | 0.653086 | 0.000000 | 0.000000 |
| arousal | 4 | stimulus_plus_fewshot_bias | midpoint_as_high | 0.745714 | 0.747700 | 0.745673 | 0.834344 | 0.127500 | 0.127494 |
| arousal | 4 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_high | 0.709286 | 0.710842 | 0.709280 | 0.801325 | 0.091071 | 0.090636 |
| arousal | 4 | stimulus_only | midpoint_as_low | 0.614107 | 0.608048 | 0.607135 | 0.612576 | 0.000000 | 0.000000 |
| arousal | 4 | stimulus_plus_fewshot_bias | midpoint_as_low | 0.760536 | 0.760497 | 0.757163 | 0.843534 | 0.146429 | 0.152449 |
| arousal | 4 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_low | 0.704107 | 0.704411 | 0.700683 | 0.790579 | 0.090000 | 0.096364 |
| arousal | 8 | stimulus_only | midpoint_as_high | 0.612187 | 0.614080 | 0.611959 | 0.647087 | 0.000000 | 0.000000 |
| arousal | 8 | stimulus_plus_fewshot_bias | midpoint_as_high | 0.756042 | 0.758217 | 0.755879 | 0.848708 | 0.143854 | 0.144136 |
| arousal | 8 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_high | 0.728750 | 0.730000 | 0.728747 | 0.828269 | 0.116563 | 0.115920 |
| arousal | 8 | stimulus_only | midpoint_as_low | 0.609271 | 0.602308 | 0.601519 | 0.604806 | 0.000000 | 0.000000 |
| arousal | 8 | stimulus_plus_fewshot_bias | midpoint_as_low | 0.771250 | 0.770357 | 0.767445 | 0.857503 | 0.161979 | 0.168050 |
| arousal | 8 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_low | 0.727708 | 0.729524 | 0.724709 | 0.824316 | 0.118437 | 0.127216 |
| arousal | 16 | stimulus_only | midpoint_as_high | 0.619062 | 0.620696 | 0.618977 | 0.653546 | 0.000000 | 0.000000 |
| arousal | 16 | stimulus_plus_fewshot_bias | midpoint_as_high | 0.759687 | 0.761935 | 0.759545 | 0.853458 | 0.140625 | 0.141239 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_high | 0.745938 | 0.747463 | 0.745924 | 0.846212 | 0.126875 | 0.126767 |
| arousal | 16 | stimulus_only | midpoint_as_low | 0.611406 | 0.605786 | 0.604710 | 0.609120 | 0.000000 | 0.000000 |
| arousal | 16 | stimulus_plus_fewshot_bias | midpoint_as_low | 0.774062 | 0.773464 | 0.770549 | 0.863943 | 0.162656 | 0.167678 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_low | 0.752344 | 0.753866 | 0.749474 | 0.849878 | 0.140937 | 0.148079 |
| valence | 0 | stimulus_only | midpoint_as_high | 0.929688 | 0.931431 | 0.929164 | 0.969607 | 0.000000 | 0.000000 |
| valence | 0 | stimulus_plus_fewshot_bias | midpoint_as_high | 0.929688 | 0.931431 | 0.929164 | 0.969607 | 0.000000 | 0.000000 |
| valence | 0 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_high | 0.929688 | 0.931431 | 0.929164 | 0.969607 | 0.000000 | 0.000000 |
| valence | 0 | stimulus_only | midpoint_as_low | 0.882812 | 0.889163 | 0.882784 | 0.942303 | 0.000000 | 0.000000 |
| valence | 0 | stimulus_plus_fewshot_bias | midpoint_as_low | 0.882812 | 0.889163 | 0.882784 | 0.942303 | 0.000000 | 0.000000 |
| valence | 0 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_low | 0.882812 | 0.889163 | 0.882784 | 0.942303 | 0.000000 | 0.000000 |
| valence | 1 | stimulus_only | midpoint_as_high | 0.930081 | 0.931883 | 0.929543 | 0.970082 | 0.000000 | 0.000000 |
| valence | 1 | stimulus_plus_fewshot_bias | midpoint_as_high | 0.869355 | 0.873039 | 0.868820 | 0.940348 | -0.060726 | -0.058845 |
| valence | 1 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_high | 0.927823 | 0.929633 | 0.927272 | 0.969766 | -0.002258 | -0.002250 |
| valence | 1 | stimulus_only | midpoint_as_low | 0.883387 | 0.889635 | 0.883363 | 0.942685 | 0.000000 | 0.000000 |
| valence | 1 | stimulus_plus_fewshot_bias | midpoint_as_low | 0.841694 | 0.844289 | 0.841301 | 0.909860 | -0.041694 | -0.045346 |
| valence | 1 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_low | 0.881210 | 0.887311 | 0.881180 | 0.943241 | -0.002177 | -0.002324 |
| valence | 2 | stimulus_only | midpoint_as_high | 0.928833 | 0.930523 | 0.928291 | 0.969108 | 0.000000 | 0.000000 |
| valence | 2 | stimulus_plus_fewshot_bias | midpoint_as_high | 0.901917 | 0.903601 | 0.901218 | 0.958953 | -0.026917 | -0.026922 |
| valence | 2 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_high | 0.927250 | 0.928818 | 0.926683 | 0.968995 | -0.001583 | -0.001705 |
| valence | 2 | stimulus_only | midpoint_as_low | 0.882583 | 0.888906 | 0.882559 | 0.942420 | 0.000000 | 0.000000 |
| valence | 2 | stimulus_plus_fewshot_bias | midpoint_as_low | 0.864167 | 0.869385 | 0.864085 | 0.931014 | -0.018417 | -0.019521 |
| valence | 2 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_low | 0.880333 | 0.886659 | 0.880309 | 0.944047 | -0.002250 | -0.002246 |
| valence | 4 | stimulus_only | midpoint_as_high | 0.929821 | 0.931413 | 0.929300 | 0.969234 | 0.000000 | 0.000000 |
| valence | 4 | stimulus_plus_fewshot_bias | midpoint_as_high | 0.918304 | 0.919886 | 0.917713 | 0.966807 | -0.011518 | -0.011527 |
| valence | 4 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_high | 0.927589 | 0.929242 | 0.927061 | 0.969437 | -0.002232 | -0.002171 |
| valence | 4 | stimulus_only | midpoint_as_low | 0.881875 | 0.888370 | 0.881847 | 0.941668 | 0.000000 | 0.000000 |
| valence | 4 | stimulus_plus_fewshot_bias | midpoint_as_low | 0.873393 | 0.879462 | 0.873347 | 0.940418 | -0.008482 | -0.008908 |
| valence | 4 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_low | 0.879375 | 0.885729 | 0.879341 | 0.944455 | -0.002500 | -0.002642 |
| valence | 8 | stimulus_only | midpoint_as_high | 0.929896 | 0.931666 | 0.929374 | 0.970035 | 0.000000 | 0.000000 |
| valence | 8 | stimulus_plus_fewshot_bias | midpoint_as_high | 0.925625 | 0.927563 | 0.925097 | 0.969297 | -0.004271 | -0.004103 |
| valence | 8 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_high | 0.927917 | 0.929790 | 0.927395 | 0.970372 | -0.001979 | -0.001876 |
| valence | 8 | stimulus_only | midpoint_as_low | 0.881771 | 0.888233 | 0.881739 | 0.942444 | 0.000000 | 0.000000 |
| valence | 8 | stimulus_plus_fewshot_bias | midpoint_as_low | 0.878646 | 0.884760 | 0.878599 | 0.946929 | -0.003125 | -0.003473 |
| valence | 8 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_low | 0.879792 | 0.886106 | 0.879754 | 0.947712 | -0.001979 | -0.002127 |
| valence | 16 | stimulus_only | midpoint_as_high | 0.924687 | 0.926416 | 0.924171 | 0.967892 | 0.000000 | 0.000000 |
| valence | 16 | stimulus_plus_fewshot_bias | midpoint_as_high | 0.923125 | 0.924970 | 0.922614 | 0.967975 | -0.001563 | -0.001446 |
| valence | 16 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_high | 0.923125 | 0.925004 | 0.922618 | 0.968274 | -0.001563 | -0.001412 |
| valence | 16 | stimulus_only | midpoint_as_low | 0.880469 | 0.886800 | 0.880427 | 0.942204 | 0.000000 | 0.000000 |
| valence | 16 | stimulus_plus_fewshot_bias | midpoint_as_low | 0.879062 | 0.885215 | 0.879013 | 0.949248 | -0.001406 | -0.001585 |
| valence | 16 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_low | 0.879219 | 0.885387 | 0.879170 | 0.948819 | -0.001250 | -0.001412 |


## Subject win/loss

| target | k_calibration | model | subjects | rmse_wins | rmse_losses | rmse_win_margin | mean_delta_rmse_model_minus_stimulus | worst_regression_delta_rmse | best_gain_delta_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | 0 | stimulus_plus_fewshot_bias | 8 | 0 | 0 | 0 | 0.000000 | 0.000000 | 0.000000 |
| arousal | 0 | stimulus_plus_fewshot_bias_shrink4 | 8 | 0 | 0 | 0 | 0.000000 | 0.000000 | 0.000000 |
| arousal | 1 | stimulus_plus_fewshot_bias | 8 | 4 | 4 | 0 | 0.023778 | 0.832596 | -1.057003 |
| arousal | 1 | stimulus_plus_fewshot_bias_shrink4 | 8 | 5 | 3 | 2 | -0.187383 | 0.045802 | -0.529611 |
| arousal | 2 | stimulus_plus_fewshot_bias | 8 | 5 | 3 | 2 | -0.324383 | 0.660139 | -1.457579 |
| arousal | 2 | stimulus_plus_fewshot_bias_shrink4 | 8 | 6 | 2 | 4 | -0.285623 | 0.069172 | -0.793743 |
| arousal | 4 | stimulus_plus_fewshot_bias | 8 | 5 | 3 | 2 | -0.479283 | 0.205698 | -1.458739 |
| arousal | 4 | stimulus_plus_fewshot_bias_shrink4 | 8 | 5 | 3 | 2 | -0.428042 | 0.045917 | -1.121847 |
| arousal | 8 | stimulus_plus_fewshot_bias | 8 | 5 | 3 | 2 | -0.590135 | 0.100696 | -1.592042 |
| arousal | 8 | stimulus_plus_fewshot_bias_shrink4 | 8 | 6 | 2 | 4 | -0.543000 | 0.033289 | -1.421183 |
| arousal | 16 | stimulus_plus_fewshot_bias | 8 | 6 | 2 | 4 | -0.628594 | 0.057950 | -1.644713 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 8 | 7 | 1 | 6 | -0.613143 | 0.033694 | -1.586454 |
| valence | 0 | stimulus_plus_fewshot_bias | 8 | 0 | 0 | 0 | 0.000000 | 0.000000 | 0.000000 |
| valence | 0 | stimulus_plus_fewshot_bias_shrink4 | 8 | 0 | 0 | 0 | 0.000000 | 0.000000 | 0.000000 |
| valence | 1 | stimulus_plus_fewshot_bias | 8 | 0 | 8 | -8 | 0.526246 | 0.639155 | 0.395396 |
| valence | 1 | stimulus_plus_fewshot_bias_shrink4 | 8 | 0 | 8 | -8 | 0.017319 | 0.032050 | 0.000697 |
| valence | 2 | stimulus_plus_fewshot_bias | 8 | 0 | 8 | -8 | 0.248030 | 0.361451 | 0.108881 |
| valence | 2 | stimulus_plus_fewshot_bias_shrink4 | 8 | 2 | 6 | -4 | 0.016069 | 0.044581 | -0.032099 |
| valence | 4 | stimulus_plus_fewshot_bias | 8 | 0 | 8 | -8 | 0.099667 | 0.164284 | 0.031966 |
| valence | 4 | stimulus_plus_fewshot_bias_shrink4 | 8 | 3 | 5 | -2 | 0.011754 | 0.045299 | -0.047546 |
| valence | 8 | stimulus_plus_fewshot_bias | 8 | 3 | 5 | -2 | 0.045289 | 0.121231 | -0.025290 |
| valence | 8 | stimulus_plus_fewshot_bias_shrink4 | 8 | 3 | 5 | -2 | 0.006334 | 0.060886 | -0.067365 |
| valence | 16 | stimulus_plus_fewshot_bias | 8 | 3 | 5 | -2 | 0.001213 | 0.063252 | -0.101649 |
| valence | 16 | stimulus_plus_fewshot_bias_shrink4 | 8 | 4 | 4 | 0 | -0.008918 | 0.046833 | -0.103395 |


## Interpretation

- If few-shot subject-bias calibration beats stimulus-only, the residual is practically usable through subject adaptation.
- This still does not prove EEG/EMG value. It creates the next baseline that physiology must beat.
- The next audit after this should test physiology on top of the few-shot calibrated baseline, not only on top of stimulus-only.
