# ROCA 06a5b Gaussian10 locked-gate rerun

Clean rerun of prior `gaussian_0p10` evidence under the current residual high-disagreement gate.

- no test-label checkpointing
- subject-level validation inside each LOSO fold
- train-only Gaussian noise augmentation
- compared against zero residual, fixed EEG-bandpower, and locked B2 scalar

## Decision
| target | decision | best_method | best_model_rmse_high | best_lift_vs_zero_high | best_lift_vs_fixed_same_eval_high | best_lift_vs_locked_bridge_rmse | gaussian_delta_rmse_vs_noaug | passes_zero_gate | passes_fixed_reference_gate | passes_locked_bridge_gate | interpretation | recommended_next_action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | NO_GO_AUGMENTATION_DOES_NOT_FIX_LOSO | none_noaug_control | 3.7218 | -0.103581 |  | -1.09954 | -0.0452921 | False | False | False | Clean locked-gate gaussian augmentation does not solve the LOSO residual problem. | Finalize diagnosis: weak residual identifiability plus subject calibration/domain shift; avoid further blind architecture search. |

## Method metrics
| method | n_eval | n_high | high_threshold | zero_rmse_high | model_rmse_high | lift_vs_zero_high | fixed_rmse_same_eval_high | lift_vs_fixed_same_eval_high | locked_bridge_rmse_05ak | lift_vs_locked_bridge_rmse | pearson_high | sign_acc_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| none_noaug_control | 192 | 68 | 2.20968 | 3.61822 | 3.7218 | -0.103581 |  |  | 2.62227 | -1.09954 | -0.444393 | 0.323529 |
| gaussian_0p10 | 192 | 68 | 2.20968 | 3.61822 | 3.7671 | -0.148873 |  |  | 2.62227 | -1.14483 | -0.247633 | 0.382353 |

## Fold metrics preview
| method | fold | test_subject | n | n_high | zero_rmse_high | model_rmse_high | lift_vs_zero_high | pearson_high | sign_acc_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| none_noaug_control | 1 | 1 | 32 | 9 | 3.04023 | 3.04761 | -0.0073837 | 0.141267 | 0.555556 |
| none_noaug_control | 2 | 2 | 32 | 15 | 3.67611 | 3.93571 | -0.259604 | 0.0257639 | 0.133333 |
| none_noaug_control | 3 | 3 | 32 | 6 | 3.07842 | 3.29781 | -0.219392 | -0.00910733 | 0 |
| none_noaug_control | 4 | 5 | 32 | 8 | 2.91682 | 2.69344 | 0.223376 | -0.0333087 | 1 |
| none_noaug_control | 5 | 6 | 32 | 23 | 4.32317 | 4.36873 | -0.0455651 | -0.222192 | 0.304348 |
| none_noaug_control | 6 | 7 | 32 | 7 | 2.6604 | 3.01712 | -0.356721 | 0.235605 | 0 |
| gaussian_0p10 | 1 | 1 | 32 | 9 | 3.04023 | 3.05254 | -0.0123062 | 0.131722 | 0.444444 |
| gaussian_0p10 | 2 | 2 | 32 | 15 | 3.67611 | 3.95073 | -0.274621 | -0.11092 | 0.533333 |
| gaussian_0p10 | 3 | 3 | 32 | 6 | 3.07842 | 3.21389 | -0.135469 | -0.171986 | 0.333333 |
| gaussian_0p10 | 4 | 5 | 32 | 8 | 2.91682 | 2.8696 | 0.0472226 | -0.0368882 | 0.625 |
| gaussian_0p10 | 5 | 6 | 32 | 23 | 4.32317 | 4.47226 | -0.149099 | 0.00773048 | 0.217391 |
| gaussian_0p10 | 6 | 7 | 32 | 7 | 2.6604 | 2.90629 | -0.245889 | -0.388869 | 0.285714 |

## Subject stats preview
| method | subject_id | n_high | zero_rmse_high | model_rmse_high | improvement_zero_minus_model | pearson_high | sign_acc_high |
| --- | --- | --- | --- | --- | --- | --- | --- |
| gaussian_0p10 | 1 | 9 | 3.04023 | 3.05254 | -0.0123062 | 0.131722 | 0.444444 |
| gaussian_0p10 | 2 | 15 | 3.67611 | 3.95073 | -0.274621 | -0.11092 | 0.533333 |
| gaussian_0p10 | 3 | 6 | 3.07842 | 3.21389 | -0.135469 | -0.171986 | 0.333333 |
| gaussian_0p10 | 5 | 8 | 2.91682 | 2.8696 | 0.0472226 | -0.0368882 | 0.625 |
| gaussian_0p10 | 6 | 23 | 4.32317 | 4.47226 | -0.149099 | 0.00773048 | 0.217391 |
| gaussian_0p10 | 7 | 7 | 2.6604 | 2.90629 | -0.245889 | -0.388869 | 0.285714 |
| none_noaug_control | 1 | 9 | 3.04023 | 3.04761 | -0.0073837 | 0.141267 | 0.555556 |
| none_noaug_control | 2 | 15 | 3.67611 | 3.93571 | -0.259604 | 0.0257639 | 0.133333 |
| none_noaug_control | 3 | 6 | 3.07842 | 3.29781 | -0.219392 | -0.00910733 | 0 |
| none_noaug_control | 5 | 8 | 2.91682 | 2.69344 | 0.223376 | -0.0333087 | 1 |
| none_noaug_control | 6 | 23 | 4.32317 | 4.36873 | -0.0455651 | -0.222192 | 0.304348 |
| none_noaug_control | 7 | 7 | 2.6604 | 3.01712 | -0.356721 | 0.235605 | 0 |