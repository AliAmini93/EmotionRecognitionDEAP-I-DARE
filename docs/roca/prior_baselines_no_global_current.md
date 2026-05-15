# Prior baselines without global baseline

This report computes non-global prior baselines for DEAP and I-DARE.

## Protocols

- `leave_one_subject_out`: stimulus-only prior, train excludes the test subject.
- `leave_one_stimulus_out`: subject-only prior, train excludes the test stimulus.
- `leave_one_subject_stimulus_pair_out`: exact leave-one-cell-out additive subject+stimulus prior.

Important: strict unseen-subject plus unseen-stimulus has no legal non-global subject/stimulus prior; it collapses to global, which is intentionally excluded here.

## Continuous score metrics

| dataset | target | protocol | model | n | mae | rmse | pearson | spearman | ccc | y_true_std | y_pred_std | residual_std | rmse_over_y_std |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DEAP | arousal | leave_one_stimulus_out | subject_only | 1280 | 1.602227 | 1.946617 | 0.275062 | 0.217886 | 0.168755 | 2.019710 | 0.692370 | 1.946617 | 0.963810 |
| DEAP | arousal | leave_one_subject_out | stimulus_only | 1280 | 1.540102 | 1.903864 | 0.340653 | 0.304448 | 0.238558 | 2.019710 | 0.825273 | 1.903864 | 0.942642 |
| DEAP | arousal | leave_one_subject_stimulus_pair_out | subject_stimulus_additive_loo_cell | 1280 | 1.431684 | 1.810603 | 0.450897 | 0.434604 | 0.374834 | 2.019710 | 1.079181 | 1.810603 | 0.896467 |
| DEAP | valence | leave_one_stimulus_out | subject_only | 1280 | 1.811642 | 2.132338 | 0.104375 | 0.082146 | 0.043598 | 2.129983 | 0.466162 | 2.132338 | 1.001105 |
| DEAP | valence | leave_one_subject_out | stimulus_only | 1280 | 1.223532 | 1.563746 | 0.679400 | 0.662833 | 0.639399 | 2.129983 | 1.498118 | 1.563746 | 0.734159 |
| DEAP | valence | leave_one_subject_stimulus_pair_out | subject_stimulus_additive_loo_cell | 1280 | 1.201777 | 1.527061 | 0.698212 | 0.702197 | 0.666890 | 2.129983 | 1.569589 | 1.527061 | 0.716936 |
| I-DARE | arousal | leave_one_stimulus_out | subject_only | 2016 | 1.998016 | 2.384906 | 0.324873 | 0.290142 | 0.222370 | 2.514611 | 0.995479 | 2.384906 | 0.948419 |
| I-DARE | arousal | leave_one_subject_out | stimulus_only | 2016 | 1.579925 | 1.944205 | 0.634375 | 0.598500 | 0.579381 | 2.514611 | 1.631972 | 1.944205 | 0.773163 |
| I-DARE | arousal | leave_one_subject_stimulus_pair_out | subject_stimulus_additive_loo_cell | 2016 | 1.374343 | 1.715681 | 0.731644 | 0.730750 | 0.704979 | 2.514611 | 1.911598 | 1.715681 | 0.682285 |
| I-DARE | valence | leave_one_stimulus_out | subject_only | 2016 | 2.180812 | 2.569822 | -0.059524 | -0.063233 | -0.017809 | 2.517903 | 0.385486 | 2.569822 | 1.020620 |
| I-DARE | valence | leave_one_subject_out | stimulus_only | 2016 | 1.022065 | 1.257774 | 0.866307 | 0.841357 | 0.858090 | 2.517903 | 2.192729 | 1.257774 | 0.499532 |
| I-DARE | valence | leave_one_subject_stimulus_pair_out | subject_stimulus_additive_loo_cell | 2016 | 0.982584 | 1.236653 | 0.871171 | 0.865430 | 0.864579 | 2.517903 | 2.225565 | 1.236653 | 0.491144 |


## Binary metrics

| dataset | target | protocol | model | label_policy | binary_source | binary_n | accuracy | balanced_accuracy | macro_f1 | auroc | n_low | n_high | true_high_rate | pred_high_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DEAP | arousal | leave_one_stimulus_out | subject_only | discard_midpoint | class_prior_probability | 1263 | 0.581948 | 0.551711 | 0.548239 | 0.617783 | 526 | 737 | 0.583531 | 0.689628 |
| DEAP | arousal | leave_one_stimulus_out | subject_only | discard_midpoint | score_threshold | 1263 | 0.604909 | 0.586626 | 0.587143 | 0.617103 | 526 | 737 | 0.583531 | 0.623911 |
| DEAP | arousal | leave_one_stimulus_out | subject_only | midpoint_as_high | class_prior_probability | 1280 | 0.581250 | 0.543671 | 0.537421 | 0.619159 | 526 | 754 | 0.589063 | 0.718750 |
| DEAP | arousal | leave_one_stimulus_out | subject_only | midpoint_as_high | score_threshold | 1280 | 0.603906 | 0.584747 | 0.585318 | 0.613129 | 526 | 754 | 0.589063 | 0.622656 |
| DEAP | arousal | leave_one_stimulus_out | subject_only | midpoint_as_low | class_prior_probability | 1280 | 0.627344 | 0.608523 | 0.609034 | 0.621791 | 543 | 737 | 0.575781 | 0.640625 |
| DEAP | arousal | leave_one_stimulus_out | subject_only | midpoint_as_low | score_threshold | 1280 | 0.603125 | 0.586522 | 0.586856 | 0.618515 | 543 | 737 | 0.575781 | 0.622656 |
| DEAP | arousal | leave_one_subject_out | stimulus_only | discard_midpoint | class_prior_probability | 1263 | 0.646873 | 0.619044 | 0.619107 | 0.665313 | 526 | 737 | 0.583531 | 0.686461 |
| DEAP | arousal | leave_one_subject_out | stimulus_only | discard_midpoint | score_threshold | 1263 | 0.676960 | 0.659793 | 0.661609 | 0.665336 | 526 | 737 | 0.583531 | 0.629454 |
| DEAP | arousal | leave_one_subject_out | stimulus_only | midpoint_as_high | class_prior_probability | 1280 | 0.648438 | 0.618809 | 0.619321 | 0.664307 | 526 | 754 | 0.589063 | 0.687500 |
| DEAP | arousal | leave_one_subject_out | stimulus_only | midpoint_as_high | score_threshold | 1280 | 0.678125 | 0.659817 | 0.661705 | 0.664488 | 526 | 754 | 0.589063 | 0.631250 |
| DEAP | arousal | leave_one_subject_out | stimulus_only | midpoint_as_low | class_prior_probability | 1280 | 0.653906 | 0.630378 | 0.630679 | 0.663521 | 543 | 737 | 0.575781 | 0.675000 |
| DEAP | arousal | leave_one_subject_out | stimulus_only | midpoint_as_low | score_threshold | 1280 | 0.671094 | 0.654756 | 0.656365 | 0.660605 | 543 | 737 | 0.575781 | 0.631250 |
| DEAP | arousal | leave_one_subject_stimulus_pair_out | subject_stimulus_additive_loo_cell | discard_midpoint | class_prior_probability | 1263 | 0.699129 | 0.678516 | 0.681266 | 0.738192 | 526 | 737 | 0.583531 | 0.653207 |
| DEAP | arousal | leave_one_subject_stimulus_pair_out | subject_stimulus_additive_loo_cell | discard_midpoint | score_threshold | 1263 | 0.699921 | 0.691169 | 0.691221 | 0.735556 | 526 | 737 | 0.583531 | 0.584323 |
| DEAP | arousal | leave_one_subject_stimulus_pair_out | subject_stimulus_additive_loo_cell | midpoint_as_high | class_prior_probability | 1280 | 0.693750 | 0.670780 | 0.673604 | 0.737682 | 526 | 754 | 0.589063 | 0.659375 |
| DEAP | arousal | leave_one_subject_stimulus_pair_out | subject_stimulus_additive_loo_cell | midpoint_as_high | score_threshold | 1280 | 0.699219 | 0.690081 | 0.689804 | 0.732837 | 526 | 754 | 0.589063 | 0.585156 |
| DEAP | arousal | leave_one_subject_stimulus_pair_out | subject_stimulus_additive_loo_cell | midpoint_as_low | class_prior_probability | 1280 | 0.684375 | 0.666532 | 0.668513 | 0.736331 | 543 | 737 | 0.575781 | 0.642969 |
| DEAP | arousal | leave_one_subject_stimulus_pair_out | subject_stimulus_additive_loo_cell | midpoint_as_low | score_threshold | 1280 | 0.695312 | 0.686695 | 0.687211 | 0.732978 | 543 | 737 | 0.575781 | 0.585156 |
| DEAP | valence | leave_one_stimulus_out | subject_only | discard_midpoint | class_prior_probability | 1264 | 0.505538 | 0.476949 | 0.458372 | 0.523873 | 556 | 708 | 0.560127 | 0.734968 |
| DEAP | valence | leave_one_stimulus_out | subject_only | discard_midpoint | score_threshold | 1264 | 0.567247 | 0.539949 | 0.526930 | 0.523823 | 556 | 708 | 0.560127 | 0.731804 |
| DEAP | valence | leave_one_stimulus_out | subject_only | midpoint_as_high | class_prior_probability | 1280 | 0.507812 | 0.472475 | 0.447150 | 0.520281 | 556 | 724 | 0.565625 | 0.765625 |
| DEAP | valence | leave_one_stimulus_out | subject_only | midpoint_as_high | score_threshold | 1280 | 0.567187 | 0.537690 | 0.525836 | 0.522208 | 556 | 724 | 0.565625 | 0.729688 |
| DEAP | valence | leave_one_stimulus_out | subject_only | midpoint_as_low | class_prior_probability | 1280 | 0.503125 | 0.481332 | 0.468205 | 0.523108 | 572 | 708 | 0.553125 | 0.703125 |
| DEAP | valence | leave_one_stimulus_out | subject_only | midpoint_as_low | score_threshold | 1280 | 0.565625 | 0.541691 | 0.527862 | 0.524898 | 572 | 708 | 0.553125 | 0.729688 |
| DEAP | valence | leave_one_subject_out | stimulus_only | discard_midpoint | class_prior_probability | 1264 | 0.742089 | 0.739463 | 0.738885 | 0.837221 | 556 | 708 | 0.560127 | 0.550633 |
| DEAP | valence | leave_one_subject_out | stimulus_only | discard_midpoint | score_threshold | 1264 | 0.780063 | 0.783400 | 0.779088 | 0.839343 | 556 | 708 | 0.560127 | 0.506329 |
| DEAP | valence | leave_one_subject_out | stimulus_only | midpoint_as_high | class_prior_probability | 1280 | 0.751563 | 0.747625 | 0.747416 | 0.833812 | 556 | 724 | 0.565625 | 0.562500 |
| DEAP | valence | leave_one_subject_out | stimulus_only | midpoint_as_high | score_threshold | 1280 | 0.775781 | 0.779885 | 0.774642 | 0.836153 | 556 | 724 | 0.565625 | 0.505469 |
| DEAP | valence | leave_one_subject_out | stimulus_only | midpoint_as_low | class_prior_probability | 1280 | 0.764062 | 0.764391 | 0.762614 | 0.833435 | 572 | 708 | 0.553125 | 0.525000 |
| DEAP | valence | leave_one_subject_out | stimulus_only | midpoint_as_low | score_threshold | 1280 | 0.777344 | 0.779923 | 0.776577 | 0.835293 | 572 | 708 | 0.553125 | 0.505469 |
| DEAP | valence | leave_one_subject_stimulus_pair_out | subject_stimulus_additive_loo_cell | discard_midpoint | class_prior_probability | 1264 | 0.789557 | 0.788593 | 0.787307 | 0.853580 | 556 | 708 | 0.560127 | 0.542722 |
| DEAP | valence | leave_one_subject_stimulus_pair_out | subject_stimulus_additive_loo_cell | discard_midpoint | score_threshold | 1264 | 0.782437 | 0.783009 | 0.780684 | 0.856417 | 556 | 708 | 0.560127 | 0.529272 |
| DEAP | valence | leave_one_subject_stimulus_pair_out | subject_stimulus_additive_loo_cell | midpoint_as_high | class_prior_probability | 1280 | 0.785937 | 0.784272 | 0.783037 | 0.851492 | 556 | 724 | 0.565625 | 0.550000 |
| DEAP | valence | leave_one_subject_stimulus_pair_out | subject_stimulus_additive_loo_cell | midpoint_as_high | score_threshold | 1280 | 0.778906 | 0.779935 | 0.776913 | 0.853226 | 556 | 724 | 0.565625 | 0.528906 |
| DEAP | valence | leave_one_subject_stimulus_pair_out | subject_stimulus_additive_loo_cell | midpoint_as_low | class_prior_probability | 1280 | 0.785937 | 0.785172 | 0.784165 | 0.850108 | 572 | 708 | 0.553125 | 0.537500 |
| DEAP | valence | leave_one_subject_stimulus_pair_out | subject_stimulus_additive_loo_cell | midpoint_as_low | score_threshold | 1280 | 0.778906 | 0.778984 | 0.777408 | 0.852725 | 572 | 708 | 0.553125 | 0.528906 |
| I-DARE | arousal | leave_one_stimulus_out | subject_only | discard_midpoint | class_prior_probability | 1799 | 0.645914 | 0.594248 | 0.593498 | 0.660025 | 1112 | 687 | 0.381879 | 0.259033 |
| I-DARE | arousal | leave_one_stimulus_out | subject_only | discard_midpoint | score_threshold | 1799 | 0.648138 | 0.586032 | 0.580583 | 0.664719 | 1112 | 687 | 0.381879 | 0.216787 |
| I-DARE | arousal | leave_one_stimulus_out | subject_only | midpoint_as_high | class_prior_probability | 2016 | 0.595238 | 0.584676 | 0.584232 | 0.658788 | 1112 | 904 | 0.448413 | 0.388889 |
| I-DARE | arousal | leave_one_stimulus_out | subject_only | midpoint_as_high | score_threshold | 2016 | 0.604663 | 0.577390 | 0.558323 | 0.651826 | 1112 | 904 | 0.448413 | 0.227679 |
| I-DARE | arousal | leave_one_stimulus_out | subject_only | midpoint_as_low | class_prior_probability | 2016 | 0.689980 | 0.593290 | 0.590671 | 0.632705 | 1329 | 687 | 0.340774 | 0.166667 |
| I-DARE | arousal | leave_one_stimulus_out | subject_only | midpoint_as_low | score_threshold | 2016 | 0.666667 | 0.583694 | 0.583698 | 0.647621 | 1329 | 687 | 0.340774 | 0.212798 |
| I-DARE | arousal | leave_one_subject_out | stimulus_only | discard_midpoint | class_prior_probability | 1799 | 0.814341 | 0.786121 | 0.795276 | 0.838019 | 1112 | 687 | 0.381879 | 0.312952 |
| I-DARE | arousal | leave_one_subject_out | stimulus_only | discard_midpoint | score_threshold | 1799 | 0.814341 | 0.786121 | 0.795276 | 0.844989 | 1112 | 687 | 0.381879 | 0.312952 |
| I-DARE | arousal | leave_one_subject_out | stimulus_only | midpoint_as_high | class_prior_probability | 2016 | 0.762897 | 0.752690 | 0.755265 | 0.808554 | 1112 | 904 | 0.448413 | 0.375000 |
| I-DARE | arousal | leave_one_subject_out | stimulus_only | midpoint_as_high | score_threshold | 2016 | 0.759921 | 0.743164 | 0.745365 | 0.810002 | 1112 | 904 | 0.448413 | 0.312500 |
| I-DARE | arousal | leave_one_subject_out | stimulus_only | midpoint_as_low | class_prior_probability | 2016 | 0.801091 | 0.768623 | 0.773911 | 0.804127 | 1329 | 687 | 0.340774 | 0.312500 |
| I-DARE | arousal | leave_one_subject_out | stimulus_only | midpoint_as_low | score_threshold | 2016 | 0.801091 | 0.768623 | 0.773911 | 0.816074 | 1329 | 687 | 0.340774 | 0.312500 |
| I-DARE | arousal | leave_one_subject_stimulus_pair_out | subject_stimulus_additive_loo_cell | discard_midpoint | class_prior_probability | 1799 | 0.852140 | 0.835055 | 0.840551 | 0.915927 | 1112 | 687 | 0.381879 | 0.348527 |
| I-DARE | arousal | leave_one_subject_stimulus_pair_out | subject_stimulus_additive_loo_cell | discard_midpoint | score_threshold | 1799 | 0.851584 | 0.833215 | 0.839480 | 0.916427 | 1112 | 687 | 0.381879 | 0.343524 |
| I-DARE | arousal | leave_one_subject_stimulus_pair_out | subject_stimulus_additive_loo_cell | midpoint_as_high | class_prior_probability | 2016 | 0.814980 | 0.808696 | 0.811043 | 0.882003 | 1112 | 904 | 0.448413 | 0.407242 |
| I-DARE | arousal | leave_one_subject_stimulus_pair_out | subject_stimulus_additive_loo_cell | midpoint_as_high | score_threshold | 2016 | 0.797619 | 0.784579 | 0.788528 | 0.879835 | 1112 | 904 | 0.448413 | 0.344246 |
| I-DARE | arousal | leave_one_subject_stimulus_pair_out | subject_stimulus_additive_loo_cell | midpoint_as_low | class_prior_probability | 2016 | 0.836310 | 0.809398 | 0.814590 | 0.888878 | 1329 | 687 | 0.340774 | 0.316964 |
| I-DARE | arousal | leave_one_subject_stimulus_pair_out | subject_stimulus_additive_loo_cell | midpoint_as_low | score_threshold | 2016 | 0.829861 | 0.811890 | 0.811122 | 0.889332 | 1329 | 687 | 0.340774 | 0.344246 |
| I-DARE | valence | leave_one_stimulus_out | subject_only | discard_midpoint | class_prior_probability | 1667 | 0.446311 | 0.443418 | 0.437724 | 0.419032 | 812 | 855 | 0.512897 | 0.610678 |
| I-DARE | valence | leave_one_stimulus_out | subject_only | discard_midpoint | score_threshold | 1667 | 0.503899 | 0.506650 | 0.499516 | 0.439200 | 812 | 855 | 0.512897 | 0.393521 |
| I-DARE | valence | leave_one_stimulus_out | subject_only | midpoint_as_high | class_prior_probability | 2016 | 0.570437 | 0.488200 | 0.413023 | 0.461713 | 812 | 1204 | 0.597222 | 0.920635 |
| I-DARE | valence | leave_one_stimulus_out | subject_only | midpoint_as_high | score_threshold | 2016 | 0.477679 | 0.492940 | 0.477521 | 0.436728 | 812 | 1204 | 0.597222 | 0.420139 |
| I-DARE | valence | leave_one_stimulus_out | subject_only | midpoint_as_low | class_prior_probability | 2016 | 0.534226 | 0.480779 | 0.431491 | 0.462331 | 1161 | 855 | 0.424107 | 0.150794 |
| I-DARE | valence | leave_one_stimulus_out | subject_only | midpoint_as_low | score_threshold | 2016 | 0.525298 | 0.508786 | 0.508284 | 0.456774 | 1161 | 855 | 0.424107 | 0.389881 |
| I-DARE | valence | leave_one_subject_out | stimulus_only | discard_midpoint | class_prior_probability | 1667 | 0.956209 | 0.955885 | 0.956148 | 0.981047 | 812 | 855 | 0.512897 | 0.524295 |
| I-DARE | valence | leave_one_subject_out | stimulus_only | discard_midpoint | score_threshold | 1667 | 0.956209 | 0.955885 | 0.956148 | 0.981840 | 812 | 855 | 0.512897 | 0.524295 |
| I-DARE | valence | leave_one_subject_out | stimulus_only | midpoint_as_high | class_prior_probability | 2016 | 0.901290 | 0.898113 | 0.897553 | 0.954229 | 812 | 1204 | 0.597222 | 0.593750 |
| I-DARE | valence | leave_one_subject_out | stimulus_only | midpoint_as_high | score_threshold | 2016 | 0.888393 | 0.897339 | 0.886520 | 0.953116 | 812 | 1204 | 0.597222 | 0.531250 |
| I-DARE | valence | leave_one_subject_out | stimulus_only | midpoint_as_low | class_prior_probability | 2016 | 0.887897 | 0.892189 | 0.886595 | 0.944306 | 1161 | 855 | 0.424107 | 0.468750 |
| I-DARE | valence | leave_one_subject_out | stimulus_only | midpoint_as_low | score_threshold | 2016 | 0.866071 | 0.879559 | 0.865804 | 0.943286 | 1161 | 855 | 0.424107 | 0.531250 |
| I-DARE | valence | leave_one_subject_stimulus_pair_out | subject_stimulus_additive_loo_cell | discard_midpoint | class_prior_probability | 1667 | 0.956209 | 0.955885 | 0.956148 | 0.984609 | 812 | 855 | 0.512897 | 0.524295 |
| I-DARE | valence | leave_one_subject_stimulus_pair_out | subject_stimulus_additive_loo_cell | discard_midpoint | score_threshold | 1667 | 0.955609 | 0.955239 | 0.955541 | 0.984216 | 812 | 855 | 0.512897 | 0.526095 |
| I-DARE | valence | leave_one_subject_stimulus_pair_out | subject_stimulus_additive_loo_cell | midpoint_as_high | class_prior_probability | 2016 | 0.905258 | 0.902838 | 0.901787 | 0.960460 | 812 | 1204 | 0.597222 | 0.590774 |
| I-DARE | valence | leave_one_subject_stimulus_pair_out | subject_stimulus_additive_loo_cell | midpoint_as_high | score_threshold | 2016 | 0.888889 | 0.897354 | 0.886950 | 0.957570 | 812 | 1204 | 0.597222 | 0.533730 |
| I-DARE | valence | leave_one_subject_stimulus_pair_out | subject_stimulus_additive_loo_cell | midpoint_as_low | class_prior_probability | 2016 | 0.885417 | 0.888803 | 0.883945 | 0.951333 | 1161 | 855 | 0.424107 | 0.463294 |
| I-DARE | valence | leave_one_subject_stimulus_pair_out | subject_stimulus_additive_loo_cell | midpoint_as_low | score_threshold | 2016 | 0.864583 | 0.878422 | 0.864342 | 0.951987 | 1161 | 855 | 0.424107 | 0.533730 |


## Sanity checks

| name | value | expected_near | abs_diff | pass_1e_minus_6 |
| --- | --- | --- | --- | --- |
| I-DARE LOSO stimulus-only valence RMSE should match previous variance decomposition | 1.257774 | 1.257774 | 0.000000 | True |
| I-DARE LOSO stimulus-only arousal RMSE should match previous variance decomposition | 1.944205 | 1.944205 | 0.000000 | True |
| DEAP LOSO stimulus-only valence RMSE should match previous DEAP stimulus-only run | 1.563746 | 1.563746 | 0.000000 | True |
| DEAP LOSO stimulus-only arousal RMSE should match previous DEAP stimulus-only run | 1.903864 | 1.903864 | 0.000000 | True |
