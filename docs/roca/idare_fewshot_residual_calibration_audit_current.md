# I-DARE Few-Shot Residual Subject Calibration Audit

This audit tests whether the subject-structured residual found in 05z can be exploited by a few calibration labels from the held-out subject.

## Models

- `stimulus_only`: LOSO stimulus prior.
- `stimulus_plus_fewshot_bias`: stimulus prior plus the mean residual estimated from k calibration trials of the same held-out subject.
- `stimulus_plus_fewshot_bias_shrink4`: conservative shrinkage version of the same subject-bias estimate.

## Verdict

| target | decision | best_model | best_k_calibration | best_lift_vs_stimulus_rmse | best_lift_vs_stimulus_residual_rmse | best_rmse | best_residual_rmse | rmse_win_margin | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | GO_FEWSHOT_SUBJECT_CALIBRATION | stimulus_plus_fewshot_bias_shrink4 | 16 | 0.210979 | 0.210979 | 1.733828 | 1.733828 | 17.000000 | few-shot subject bias beats stimulus-only in pooled and subject-level residual metrics |
| valence | WEAK_GO_FEWSHOT_CALIBRATION_NEEDS_CONFIRMATION | stimulus_plus_fewshot_bias_shrink4 | 16 | 0.014743 | 0.014743 | 1.241848 | 1.241848 | -15.000000 | few-shot calibration has positive pooled lift but does not meet practical margin |


## Main metrics

| target | k_calibration | model | n | rmse | lift_vs_stimulus_rmse | residual_rmse | lift_vs_stimulus_residual_rmse | pearson | ccc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | 0 | stimulus_only | 2016 | 1.944205 | 0.000000 | 1.944205 | 0.000000 | 0.634375 | 0.579381 |
| arousal | 0 | stimulus_plus_fewshot_bias | 2016 | 1.944205 | 0.000000 | 1.944205 | 0.000000 | 0.634375 | 0.579381 |
| arousal | 0 | stimulus_plus_fewshot_bias_shrink4 | 2016 | 1.944205 | 0.000000 | 1.944205 | 0.000000 | 0.634375 | 0.579381 |
| arousal | 1 | stimulus_only | 390600 | 1.943580 | 0.000000 | 1.943580 | 0.000000 | 0.634635 | 0.579619 |
| arousal | 1 | stimulus_plus_fewshot_bias | 390600 | 2.398344 | -0.454764 | 2.398344 | -0.454764 | 0.551137 | 0.551088 |
| arousal | 1 | stimulus_plus_fewshot_bias_shrink4 | 390600 | 1.885624 | 0.057956 | 1.885624 | 0.057956 | 0.661576 | 0.610755 |
| arousal | 2 | stimulus_only | 378000 | 1.944653 | 0.000000 | 1.944653 | 0.000000 | 0.634092 | 0.579234 |
| arousal | 2 | stimulus_plus_fewshot_bias | 378000 | 2.070690 | -0.126037 | 2.070690 | -0.126037 | 0.624857 | 0.620381 |
| arousal | 2 | stimulus_plus_fewshot_bias_shrink4 | 378000 | 1.852176 | 0.092477 | 1.852176 | 0.092477 | 0.676303 | 0.628602 |
| arousal | 4 | stimulus_only | 352800 | 1.944091 | 0.000000 | 1.944091 | 0.000000 | 0.634465 | 0.579472 |
| arousal | 4 | stimulus_plus_fewshot_bias | 352800 | 1.886481 | 0.057609 | 1.886481 | 0.057609 | 0.676699 | 0.663674 |
| arousal | 4 | stimulus_plus_fewshot_bias_shrink4 | 352800 | 1.806305 | 0.137786 | 1.806305 | 0.137786 | 0.695738 | 0.652088 |
| arousal | 8 | stimulus_only | 302400 | 1.943825 | 0.000000 | 1.943825 | 0.000000 | 0.634454 | 0.579597 |
| arousal | 8 | stimulus_plus_fewshot_bias | 302400 | 1.793275 | 0.150550 | 1.793275 | 0.150550 | 0.705715 | 0.686089 |
| arousal | 8 | stimulus_plus_fewshot_bias_shrink4 | 302400 | 1.765094 | 0.178731 | 1.765094 | 0.178731 | 0.712159 | 0.673343 |
| arousal | 16 | stimulus_only | 201600 | 1.944807 | 0.000000 | 1.944807 | 0.000000 | 0.633252 | 0.578583 |
| arousal | 16 | stimulus_plus_fewshot_bias | 201600 | 1.741675 | 0.203132 | 1.741675 | 0.203132 | 0.722204 | 0.697987 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 201600 | 1.733828 | 0.210979 | 1.733828 | 0.210979 | 0.723688 | 0.688585 |
| valence | 0 | stimulus_only | 2016 | 1.257774 | 0.000000 | 1.257774 | 0.000000 | 0.866307 | 0.858090 |
| valence | 0 | stimulus_plus_fewshot_bias | 2016 | 1.257774 | 0.000000 | 1.257774 | 0.000000 | 0.866307 | 0.858090 |
| valence | 0 | stimulus_plus_fewshot_bias_shrink4 | 2016 | 1.257774 | 0.000000 | 1.257774 | 0.000000 | 0.866307 | 0.858090 |
| valence | 1 | stimulus_only | 390600 | 1.257784 | 0.000000 | 1.257784 | 0.000000 | 0.866339 | 0.858108 |
| valence | 1 | stimulus_plus_fewshot_bias | 390600 | 1.721338 | -0.463555 | 1.721338 | -0.463555 | 0.767235 | 0.767224 |
| valence | 1 | stimulus_plus_fewshot_bias_shrink4 | 390600 | 1.266974 | -0.009191 | 1.266974 | -0.009191 | 0.864299 | 0.856834 |
| valence | 2 | stimulus_only | 378000 | 1.257453 | 0.000000 | 1.257453 | 0.000000 | 0.866350 | 0.858155 |
| valence | 2 | stimulus_plus_fewshot_bias | 378000 | 1.493984 | -0.236531 | 1.493984 | -0.236531 | 0.815245 | 0.813922 |
| valence | 2 | stimulus_plus_fewshot_bias_shrink4 | 378000 | 1.268301 | -0.010847 | 1.268301 | -0.010847 | 0.863978 | 0.856891 |
| valence | 4 | stimulus_only | 352800 | 1.258215 | 0.000000 | 1.258215 | 0.000000 | 0.866211 | 0.858014 |
| valence | 4 | stimulus_plus_fewshot_bias | 352800 | 1.361332 | -0.103117 | 1.361332 | -0.103117 | 0.844042 | 0.840479 |
| valence | 4 | stimulus_plus_fewshot_bias_shrink4 | 352800 | 1.264916 | -0.006701 | 1.264916 | -0.006701 | 0.864825 | 0.857971 |
| valence | 8 | stimulus_only | 302400 | 1.258336 | 0.000000 | 1.258336 | 0.000000 | 0.866171 | 0.857994 |
| valence | 8 | stimulus_plus_fewshot_bias | 302400 | 1.292301 | -0.033965 | 1.292301 | -0.033965 | 0.859036 | 0.853902 |
| valence | 8 | stimulus_plus_fewshot_bias_shrink4 | 302400 | 1.255858 | 0.002478 | 1.255858 | 0.002478 | 0.866860 | 0.860098 |
| valence | 16 | stimulus_only | 201600 | 1.256590 | 0.000000 | 1.256590 | 0.000000 | 0.866750 | 0.858534 |
| valence | 16 | stimulus_plus_fewshot_bias | 201600 | 1.253669 | 0.002922 | 1.253669 | 0.002922 | 0.867642 | 0.861540 |
| valence | 16 | stimulus_plus_fewshot_bias_shrink4 | 201600 | 1.241848 | 0.014743 | 1.241848 | 0.014743 | 0.870158 | 0.863310 |


## Binary metrics

| target | k_calibration | model | label_policy | accuracy | balanced_accuracy | macro_f1 | auroc | lift_vs_stimulus_accuracy | lift_vs_stimulus_balanced_accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | 0 | stimulus_only | midpoint_as_high | 0.759921 | 0.743164 | 0.745365 | 0.810002 | 0.000000 | 0.000000 |
| arousal | 0 | stimulus_plus_fewshot_bias | midpoint_as_high | 0.759921 | 0.743164 | 0.745365 | 0.810002 | 0.000000 | 0.000000 |
| arousal | 0 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_high | 0.759921 | 0.743164 | 0.745365 | 0.810002 | 0.000000 | 0.000000 |
| arousal | 0 | stimulus_only | midpoint_as_low | 0.801091 | 0.768623 | 0.773911 | 0.816074 | 0.000000 | 0.000000 |
| arousal | 0 | stimulus_plus_fewshot_bias | midpoint_as_low | 0.801091 | 0.768623 | 0.773911 | 0.816074 | 0.000000 | 0.000000 |
| arousal | 0 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_low | 0.801091 | 0.768623 | 0.773911 | 0.816074 | 0.000000 | 0.000000 |
| arousal | 1 | stimulus_only | midpoint_as_high | 0.760097 | 0.743289 | 0.745527 | 0.810153 | 0.000000 | 0.000000 |
| arousal | 1 | stimulus_plus_fewshot_bias | midpoint_as_high | 0.717937 | 0.708317 | 0.709920 | 0.786774 | -0.042161 | -0.034972 |
| arousal | 1 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_high | 0.763646 | 0.748308 | 0.750971 | 0.834935 | 0.003548 | 0.005019 |
| arousal | 1 | stimulus_only | midpoint_as_low | 0.801321 | 0.768871 | 0.774146 | 0.816305 | 0.000000 | 0.000000 |
| arousal | 1 | stimulus_plus_fewshot_bias | midpoint_as_low | 0.733449 | 0.718452 | 0.711462 | 0.797151 | -0.067873 | -0.050420 |
| arousal | 1 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_low | 0.800809 | 0.773124 | 0.775920 | 0.842788 | -0.000512 | 0.004253 |
| arousal | 2 | stimulus_only | midpoint_as_high | 0.759894 | 0.743237 | 0.745417 | 0.809951 | 0.000000 | 0.000000 |
| arousal | 2 | stimulus_plus_fewshot_bias | midpoint_as_high | 0.755714 | 0.744602 | 0.747092 | 0.826799 | -0.004180 | 0.001366 |
| arousal | 2 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_high | 0.768569 | 0.753885 | 0.756758 | 0.844313 | 0.008675 | 0.010649 |
| arousal | 2 | stimulus_only | midpoint_as_low | 0.800839 | 0.768497 | 0.773727 | 0.815922 | 0.000000 | 0.000000 |
| arousal | 2 | stimulus_plus_fewshot_bias | midpoint_as_low | 0.776939 | 0.760508 | 0.755899 | 0.837930 | -0.023899 | -0.007988 |
| arousal | 2 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_low | 0.803138 | 0.777384 | 0.779362 | 0.852764 | 0.002299 | 0.008887 |
| arousal | 4 | stimulus_only | midpoint_as_high | 0.759952 | 0.743341 | 0.745501 | 0.810003 | 0.000000 | 0.000000 |
| arousal | 4 | stimulus_plus_fewshot_bias | midpoint_as_high | 0.779280 | 0.767400 | 0.770595 | 0.852825 | 0.019328 | 0.024060 |
| arousal | 4 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_high | 0.775836 | 0.761754 | 0.764920 | 0.855674 | 0.015884 | 0.018414 |
| arousal | 4 | stimulus_only | midpoint_as_low | 0.801009 | 0.768698 | 0.773953 | 0.816092 | 0.000000 | 0.000000 |
| arousal | 4 | stimulus_plus_fewshot_bias | midpoint_as_low | 0.804334 | 0.787652 | 0.784581 | 0.864387 | 0.003325 | 0.018954 |
| arousal | 4 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_low | 0.808274 | 0.784776 | 0.785888 | 0.865024 | 0.007265 | 0.016078 |
| arousal | 8 | stimulus_only | midpoint_as_high | 0.759669 | 0.743139 | 0.745271 | 0.809547 | 0.000000 | 0.000000 |
| arousal | 8 | stimulus_plus_fewshot_bias | midpoint_as_high | 0.791227 | 0.778885 | 0.782492 | 0.867151 | 0.031558 | 0.035746 |
| arousal | 8 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_high | 0.783869 | 0.770289 | 0.773734 | 0.865478 | 0.024200 | 0.027150 |
| arousal | 8 | stimulus_only | midpoint_as_low | 0.800979 | 0.768789 | 0.773945 | 0.815793 | 0.000000 | 0.000000 |
| arousal | 8 | stimulus_plus_fewshot_bias | midpoint_as_low | 0.818429 | 0.801336 | 0.799297 | 0.877341 | 0.017450 | 0.032546 |
| arousal | 8 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_low | 0.813991 | 0.792465 | 0.792793 | 0.874578 | 0.013013 | 0.023676 |
| arousal | 16 | stimulus_only | midpoint_as_high | 0.759132 | 0.742960 | 0.744883 | 0.809590 | 0.000000 | 0.000000 |
| arousal | 16 | stimulus_plus_fewshot_bias | midpoint_as_high | 0.795809 | 0.783275 | 0.786957 | 0.875249 | 0.036677 | 0.040315 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_high | 0.790308 | 0.777179 | 0.780711 | 0.873008 | 0.031176 | 0.034219 |
| arousal | 16 | stimulus_only | midpoint_as_low | 0.800193 | 0.768011 | 0.773249 | 0.815071 | 0.000000 | 0.000000 |
| arousal | 16 | stimulus_plus_fewshot_bias | midpoint_as_low | 0.825595 | 0.807622 | 0.806742 | 0.884676 | 0.025402 | 0.039612 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_low | 0.819931 | 0.799451 | 0.799718 | 0.881714 | 0.019737 | 0.031440 |
| valence | 0 | stimulus_only | midpoint_as_high | 0.888393 | 0.897339 | 0.886520 | 0.953116 | 0.000000 | 0.000000 |
| valence | 0 | stimulus_plus_fewshot_bias | midpoint_as_high | 0.888393 | 0.897339 | 0.886520 | 0.953116 | 0.000000 | 0.000000 |
| valence | 0 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_high | 0.888393 | 0.897339 | 0.886520 | 0.953116 | 0.000000 | 0.000000 |
| valence | 0 | stimulus_only | midpoint_as_low | 0.866071 | 0.879559 | 0.865804 | 0.943286 | 0.000000 | 0.000000 |
| valence | 0 | stimulus_plus_fewshot_bias | midpoint_as_low | 0.866071 | 0.879559 | 0.865804 | 0.943286 | 0.000000 | 0.000000 |
| valence | 0 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_low | 0.866071 | 0.879559 | 0.865804 | 0.943286 | 0.000000 | 0.000000 |
| valence | 1 | stimulus_only | midpoint_as_high | 0.888564 | 0.897506 | 0.886692 | 0.953155 | 0.000000 | 0.000000 |
| valence | 1 | stimulus_plus_fewshot_bias | midpoint_as_high | 0.837517 | 0.846431 | 0.835193 | 0.922001 | -0.051047 | -0.051075 |
| valence | 1 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_high | 0.887768 | 0.896231 | 0.885816 | 0.956039 | -0.000796 | -0.001275 |
| valence | 1 | stimulus_only | midpoint_as_low | 0.866178 | 0.879666 | 0.865911 | 0.943311 | 0.000000 | 0.000000 |
| valence | 1 | stimulus_plus_fewshot_bias | midpoint_as_low | 0.823505 | 0.834129 | 0.822939 | 0.903974 | -0.042673 | -0.045537 |
| valence | 1 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_low | 0.864199 | 0.877952 | 0.863952 | 0.947373 | -0.001979 | -0.001714 |
| valence | 2 | stimulus_only | midpoint_as_high | 0.888317 | 0.897297 | 0.886457 | 0.953163 | 0.000000 | 0.000000 |
| valence | 2 | stimulus_plus_fewshot_bias | midpoint_as_high | 0.864280 | 0.872857 | 0.862115 | 0.940701 | -0.024037 | -0.024440 |
| valence | 2 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_high | 0.887802 | 0.896401 | 0.885880 | 0.955984 | -0.000516 | -0.000895 |
| valence | 2 | stimulus_only | midpoint_as_low | 0.866291 | 0.879750 | 0.866019 | 0.943396 | 0.000000 | 0.000000 |
| valence | 2 | stimulus_plus_fewshot_bias | midpoint_as_low | 0.845608 | 0.858042 | 0.845244 | 0.926460 | -0.020683 | -0.021708 |
| valence | 2 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_low | 0.864458 | 0.878127 | 0.864202 | 0.947766 | -0.001833 | -0.001623 |
| valence | 4 | stimulus_only | midpoint_as_high | 0.888472 | 0.897297 | 0.886610 | 0.952930 | 0.000000 | 0.000000 |
| valence | 4 | stimulus_plus_fewshot_bias | midpoint_as_high | 0.879600 | 0.887476 | 0.877493 | 0.949474 | -0.008872 | -0.009821 |
| valence | 4 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_high | 0.888348 | 0.896654 | 0.886407 | 0.955822 | -0.000125 | -0.000643 |
| valence | 4 | stimulus_only | midpoint_as_low | 0.865935 | 0.879551 | 0.865664 | 0.943203 | 0.000000 | 0.000000 |
| valence | 4 | stimulus_plus_fewshot_bias | midpoint_as_low | 0.856023 | 0.869809 | 0.855765 | 0.938833 | -0.009912 | -0.009742 |
| valence | 4 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_low | 0.863583 | 0.877516 | 0.863335 | 0.948135 | -0.002353 | -0.002035 |
| valence | 8 | stimulus_only | midpoint_as_high | 0.888499 | 0.897406 | 0.886624 | 0.953074 | 0.000000 | 0.000000 |
| valence | 8 | stimulus_plus_fewshot_bias | midpoint_as_high | 0.886091 | 0.894433 | 0.884105 | 0.954242 | -0.002407 | -0.002972 |
| valence | 8 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_high | 0.888568 | 0.897067 | 0.886634 | 0.956642 | 0.000069 | -0.000339 |
| valence | 8 | stimulus_only | midpoint_as_low | 0.866045 | 0.879670 | 0.865775 | 0.943210 | 0.000000 | 0.000000 |
| valence | 8 | stimulus_plus_fewshot_bias | midpoint_as_low | 0.861227 | 0.875076 | 0.860974 | 0.945924 | -0.004818 | -0.004594 |
| valence | 8 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_low | 0.863876 | 0.877754 | 0.863625 | 0.949384 | -0.002169 | -0.001916 |
| valence | 16 | stimulus_only | midpoint_as_high | 0.888383 | 0.897302 | 0.886542 | 0.953066 | 0.000000 | 0.000000 |
| valence | 16 | stimulus_plus_fewshot_bias | midpoint_as_high | 0.888452 | 0.896946 | 0.886549 | 0.956154 | 0.000069 | -0.000356 |
| valence | 16 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_high | 0.888537 | 0.897086 | 0.886643 | 0.957070 | 0.000154 | -0.000216 |
| valence | 16 | stimulus_only | midpoint_as_low | 0.866741 | 0.880191 | 0.866467 | 0.943624 | 0.000000 | 0.000000 |
| valence | 16 | stimulus_plus_fewshot_bias | midpoint_as_low | 0.864479 | 0.878194 | 0.864225 | 0.950082 | -0.002262 | -0.001997 |
| valence | 16 | stimulus_plus_fewshot_bias_shrink4 | midpoint_as_low | 0.865352 | 0.879047 | 0.865097 | 0.951132 | -0.001389 | -0.001144 |


## Subject win/loss

| target | k_calibration | model | subjects | rmse_wins | rmse_losses | rmse_win_margin | mean_delta_rmse_model_minus_stimulus | worst_regression_delta_rmse | best_gain_delta_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | 0 | stimulus_plus_fewshot_bias | 63 | 0 | 0 | 0 | 0.000000 | 0.000000 | 0.000000 |
| arousal | 0 | stimulus_plus_fewshot_bias_shrink4 | 63 | 0 | 0 | 0 | 0.000000 | 0.000000 | 0.000000 |
| arousal | 1 | stimulus_plus_fewshot_bias | 63 | 7 | 56 | -49 | 0.452380 | 0.981319 | -1.160343 |
| arousal | 1 | stimulus_plus_fewshot_bias_shrink4 | 63 | 30 | 33 | -3 | -0.045969 | 0.059057 | -0.520739 |
| arousal | 2 | stimulus_plus_fewshot_bias | 63 | 16 | 47 | -31 | 0.131178 | 0.598183 | -1.505107 |
| arousal | 2 | stimulus_plus_fewshot_bias_shrink4 | 63 | 32 | 31 | 1 | -0.076155 | 0.086370 | -0.877090 |
| arousal | 4 | stimulus_plus_fewshot_bias | 63 | 24 | 39 | -15 | -0.048149 | 0.328849 | -1.688197 |
| arousal | 4 | stimulus_plus_fewshot_bias_shrink4 | 63 | 34 | 29 | 5 | -0.119918 | 0.104769 | -1.264822 |
| arousal | 8 | stimulus_plus_fewshot_bias | 63 | 27 | 36 | -9 | -0.138591 | 0.205501 | -1.798154 |
| arousal | 8 | stimulus_plus_fewshot_bias_shrink4 | 63 | 37 | 26 | 11 | -0.161749 | 0.111683 | -1.573246 |
| arousal | 16 | stimulus_plus_fewshot_bias | 63 | 35 | 28 | 7 | -0.189560 | 0.112379 | -1.879565 |
| arousal | 16 | stimulus_plus_fewshot_bias_shrink4 | 63 | 40 | 23 | 17 | -0.195604 | 0.083655 | -1.778485 |
| valence | 0 | stimulus_plus_fewshot_bias | 63 | 0 | 0 | 0 | 0.000000 | 0.000000 | 0.000000 |
| valence | 0 | stimulus_plus_fewshot_bias_shrink4 | 63 | 0 | 0 | 0 | 0.000000 | 0.000000 | 0.000000 |
| valence | 1 | stimulus_plus_fewshot_bias | 63 | 0 | 63 | -63 | 0.453187 | 0.793909 | 0.153642 |
| valence | 1 | stimulus_plus_fewshot_bias_shrink4 | 63 | 17 | 46 | -29 | 0.009005 | 0.047363 | -0.095537 |
| valence | 2 | stimulus_plus_fewshot_bias | 63 | 4 | 59 | -55 | 0.230071 | 0.452613 | -0.057703 |
| valence | 2 | stimulus_plus_fewshot_bias_shrink4 | 63 | 20 | 43 | -23 | 0.010277 | 0.068218 | -0.143793 |
| valence | 4 | stimulus_plus_fewshot_bias | 63 | 7 | 56 | -49 | 0.099007 | 0.243893 | -0.179270 |
| valence | 4 | stimulus_plus_fewshot_bias_shrink4 | 63 | 21 | 42 | -21 | 0.005920 | 0.077515 | -0.237497 |
| valence | 8 | stimulus_plus_fewshot_bias | 63 | 20 | 43 | -23 | 0.031861 | 0.147959 | -0.259991 |
| valence | 8 | stimulus_plus_fewshot_bias_shrink4 | 63 | 22 | 41 | -19 | -0.003480 | 0.080319 | -0.267018 |
| valence | 16 | stimulus_plus_fewshot_bias | 63 | 22 | 41 | -19 | -0.004251 | 0.089937 | -0.310509 |
| valence | 16 | stimulus_plus_fewshot_bias_shrink4 | 63 | 24 | 39 | -15 | -0.015688 | 0.067489 | -0.313845 |


## Interpretation

- If few-shot subject-bias calibration beats stimulus-only, the residual is practically usable through subject adaptation.
- This still does not prove EEG/EMG value. It creates the next baseline that physiology must beat.
- The next audit after this should test physiology on top of the few-shot calibrated baseline, not only on top of stimulus-only.
