# EEG Arousal Oracle Diagnostic

This is a deliberately leaky diagnostic. The held-out test subject is used for checkpoint selection.

## Pooled trial-level metrics

```
       scope                 run_group    n  subjects      mae     rmse  accuracy  balanced_accuracy  macro_f1      mcc  pred_dev_std  true_dev_std  dev_pearson    auroc   tn  fp  fn  tp
pooled_trial stimulus_only_oracle_file 2016        63 1.579925 1.944205  0.801091           0.768623  0.773911 0.549367      0.000000      1.944205          NaN 0.816074 1157 172 229 458
pooled_trial    oracle_test_checkpoint 2016        63 1.467122 1.831047  0.804067           0.777560  0.779984 0.560260      0.642020      1.944205     0.337169 0.855132 1144 185 210 477
pooled_trial  stimulus_only_clean_file 2016        63 1.579925 1.944205  0.801091           0.768623  0.773911 0.549367      0.000000      1.944205          NaN 0.816074 1157 172 229 458
pooled_trial          clean_gaussian10 2016        63 1.614347 1.992522  0.797123           0.767371  0.770991 0.542694      0.383239      1.944205    -0.027220 0.811863 1144 185 224 463
```

## Best epoch summary

```
 min  median     mean  max
   1     3.0 4.968254   24
```

## Worst subjects

```
 test_subject  failure_score  delta_oracle_minus_stimulus_rmse  delta_oracle_minus_stimulus_macro_f1  delta_oracle_minus_clean_rmse  delta_oracle_minus_clean_macro_f1  oracle_test_checkpoint_rmse  clean_gaussian10_rmse  stimulus_only_oracle_file_rmse
           35       0.144748                          0.071771                              0.000000                       0.072977                           0.031047                     1.624536               1.551559                        1.552765
           26       0.133830                         -0.242367                             -0.133830                      -0.270937                          -0.133830                     1.855204               2.126141                        2.097571
           10       0.111335                          0.033818                             -0.032216                       0.045301                          -0.032216                     1.751188               1.705886                        1.717370
           63       0.109714                          0.008234                             -0.101480                      -0.006623                          -0.101480                     2.190881               2.197504                        2.182648
           64       0.095975                          0.060683                              0.000000                       0.035292                           0.030605                     1.570129               1.534837                        1.509447
           60       0.082931                          0.082931                              0.000000                      -0.102323                           0.000000                     2.498586               2.600909                        2.415656
           22       0.079660                          0.047928                             -0.031733                      -0.020922                           0.000000                     2.249849               2.270771                        2.201921
           57       0.074869                          0.009873                              0.048184                       0.064996                          -0.003889                     2.176505               2.111509                        2.166632
           25       0.066637                         -0.052000                             -0.063359                       0.003278                          -0.031143                     2.138027               2.134749                        2.190027
           33       0.048434                         -0.104329                              0.000000                       0.048434                          -0.027856                     1.604520               1.556087                        1.708850
            6       0.045953                         -0.291735                             -0.045953                      -0.338068                          -0.045953                     3.440777               3.778845                        3.732512
           15       0.045933                         -0.025394                             -0.045933                      -0.033898                          -0.045933                     1.669764               1.703662                        1.695158
           16       0.042309                         -0.069717                             -0.042309                      -0.038503                          -0.042309                     1.324002               1.362505                        1.393718
           56       0.033715                          0.033715                              0.000000                      -0.006534                           0.000000                     1.484157               1.490691                        1.450442
           47       0.030229                         -0.003204                             -0.030229                      -0.025987                           0.000000                     2.438600               2.464587                        2.441804
           48       0.029451                          0.029451                              0.000000                      -0.095974                           0.000000                     1.334153               1.430127                        1.304702
           53       0.020007                          0.020007                              0.000000                      -0.040392                          -0.037290                     1.137816               1.178208                        1.117809
           42       0.001471                         -0.218816                             -0.001471                      -0.172832                          -0.001471                     2.433518               2.606350                        2.652334
           45       0.001145                         -0.052976                              0.040270                       0.001145                           0.040270                     1.468973               1.467829                        1.521949
           13       0.000000                         -0.509325                              0.010774                      -0.592110                           0.010774                     1.907921               2.500031                        2.417245
```

## Interpretation

- If oracle beats clean by a lot, checkpoint selection / subject-specific validation is a major bottleneck.
- If oracle beats stimulus-only, EEG contains usable subject-specific residual signal under leaky selection.
- This result is not valid as clean cross-subject performance.
