# EEG Valence Oracle Diagnostic

This is a deliberately leaky diagnostic. The held-out test subject is used for checkpoint selection.

## Pooled trial-level metrics

```
       scope                 run_group    n  subjects      mae     rmse  accuracy  balanced_accuracy  macro_f1      mcc  pred_dev_std  true_dev_std  dev_pearson    auroc  tn  fp  fn  tp
pooled_trial stimulus_only_oracle_file 2016        63 1.022065 1.257774  0.866071           0.879559  0.865804 0.751793      0.000000      1.257774          NaN 0.943286 918 243  27 828
pooled_trial    oracle_test_checkpoint 2016        63 0.974643 1.215291  0.866071           0.879868  0.865827 0.752597      0.313236      1.257774     0.257874 0.952116 916 245  25 830
pooled_trial  stimulus_only_clean_file 2016        63 1.022065 1.257774  0.866071           0.879559  0.865804 0.751793      0.000000      1.257774          NaN 0.943286 918 243  27 828
pooled_trial          clean_gaussian10 2016        63 1.025882 1.264473  0.863591           0.877406  0.863348 0.747770      0.169264      1.257774     0.028393 0.947374 913 248  27 828
```

## Best epoch summary

```
 min  median     mean  max
   1     4.0 4.746032   37
```

## Worst subjects

```
 test_subject  failure_score  delta_oracle_minus_stimulus_rmse  delta_oracle_minus_stimulus_macro_f1  delta_oracle_minus_clean_rmse  delta_oracle_minus_clean_macro_f1  oracle_test_checkpoint_rmse  clean_gaussian10_rmse  stimulus_only_oracle_file_rmse
           61       0.079505                         -0.014943                             -0.031089                       0.048416                          -0.031089                     1.781642               1.733226                        1.796585
           49       0.060504                         -0.191552                             -0.060504                      -0.196437                          -0.060504                     1.141401               1.337838                        1.332953
           53       0.059470                         -0.041022                              0.031097                       0.059470                           0.031097                     1.076899               1.017429                        1.117921
           12       0.036469                         -0.008575                             -0.031158                       0.005311                          -0.031158                     1.174561               1.169251                        1.183136
           40       0.034091                          0.033273                              0.000000                       0.000817                           0.000000                     1.459949               1.459132                        1.426676
           57       0.031965                         -0.187024                             -0.031965                      -0.187958                          -0.031965                     1.119148               1.307106                        1.306172
           23       0.031158                         -0.037804                             -0.031158                      -0.029697                          -0.031158                     1.008165               1.037861                        1.045969
           44       0.030913                         -0.025157                             -0.030913                      -0.012665                          -0.030913                     1.526369               1.539035                        1.551526
           26       0.030600                         -0.058241                             -0.030600                      -0.245062                           0.030729                     1.485674               1.730736                        1.543915
           64       0.027791                         -0.002674                              0.000000                       0.027791                           0.000000                     1.218381               1.190590                        1.221055
           17       0.025862                          0.009545                              0.000000                       0.016316                           0.000000                     1.205598               1.189281                        1.196052
           56       0.015049                         -0.002338                              0.000000                       0.015049                           0.000000                     1.096173               1.081124                        1.098511
           10       0.014569                          0.014569                              0.000000                      -0.003571                           0.000000                     1.014987               1.018559                        1.000419
            6       0.010829                          0.010829                              0.000000                      -0.021814                           0.000000                     1.167922               1.189736                        1.157093
           47       0.006769                          0.006769                              0.000000                      -0.001735                           0.000000                     1.820660               1.822395                        1.813891
           63       0.005680                          0.005680                              0.000000                      -0.077860                           0.030913                     1.143131               1.220990                        1.137451
           30       0.004778                          0.004778                              0.000000                      -0.050742                           0.000000                     0.985289               1.036030                        0.980511
           28       0.004042                          0.004042                              0.000000                      -0.042030                           0.000000                     1.279263               1.321293                        1.275220
           39       0.001818                         -0.007673                              0.000000                       0.001818                           0.000000                     1.167864               1.166045                        1.175536
           65       0.001556                          0.001556                              0.000000                      -0.009506                           0.000000                     0.961746               0.971252                        0.960190
```

## Interpretation

- If oracle beats clean by a lot, checkpoint selection / subject-specific validation is a major bottleneck.
- If oracle beats stimulus-only, EEG contains usable subject-specific residual signal under leaky selection.
- This result is not valid as clean cross-subject performance.
