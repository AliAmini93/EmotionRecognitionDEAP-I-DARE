# ROCA 06a5b Gaussian10 locked-gate rerun

Clean rerun of prior `gaussian_0p10` evidence under the current residual high-disagreement gate.

- no test-label checkpointing
- subject-level validation inside each LOSO fold
- train-only Gaussian noise augmentation
- compared against zero residual, fixed EEG-bandpower, and locked B2 scalar

## Decision
| target | decision | best_method | best_model_rmse_high | best_lift_vs_zero_high | best_lift_vs_fixed_same_eval_high | best_lift_vs_locked_bridge_rmse | gaussian_delta_rmse_vs_noaug | passes_zero_gate | passes_fixed_reference_gate | passes_locked_bridge_gate | interpretation | recommended_next_action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | NO_GO_AUGMENTATION_DOES_NOT_FIX_LOSO | none_noaug_control | 3.26093 | 0.000704925 |  | -0.638662 | -0.01932 | False | False | False | Clean locked-gate gaussian augmentation does not solve the LOSO residual problem. | Finalize diagnosis: weak residual identifiability plus subject calibration/domain shift; avoid further blind architecture search. |

## Method metrics
| method | n_eval | n_high | high_threshold | zero_rmse_high | model_rmse_high | lift_vs_zero_high | fixed_rmse_same_eval_high | lift_vs_fixed_same_eval_high | locked_bridge_rmse_05ak | lift_vs_locked_bridge_rmse | pearson_high | sign_acc_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| none_noaug_control | 2016 | 495 | 2.20968 | 3.26163 | 3.26093 | 0.000704925 |  |  | 2.62227 | -0.638662 | 0.0967808 | 0.549495 |
| gaussian_0p10 | 2016 | 495 | 2.20968 | 3.26163 | 3.28025 | -0.0186151 |  |  | 2.62227 | -0.657982 | 0.0574436 | 0.555556 |

## Fold metrics preview
| method | fold | test_subject | n | n_high | zero_rmse_high | model_rmse_high | lift_vs_zero_high | pearson_high | sign_acc_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| none_noaug_control | 1 | 1 | 32 | 9 | 3.04023 | 3.04768 | -0.00744853 | 0.141333 | 0.555556 |
| none_noaug_control | 2 | 2 | 32 | 15 | 3.67611 | 4.13876 | -0.462655 | -0.176832 | 0.333333 |
| none_noaug_control | 3 | 3 | 32 | 6 | 3.07842 | 2.08563 | 0.992785 | 0.656105 | 1 |
| none_noaug_control | 4 | 5 | 32 | 8 | 2.91682 | 2.26927 | 0.647551 | -0.674544 | 1 |
| none_noaug_control | 5 | 6 | 32 | 23 | 4.32317 | 3.8629 | 0.460267 | 0.181839 | 1 |
| none_noaug_control | 6 | 7 | 32 | 7 | 2.6604 | 3.01715 | -0.356747 | 0.235584 | 0 |
| none_noaug_control | 7 | 8 | 32 | 10 | 2.78607 | 2.58071 | 0.205356 | 0.444101 | 0.8 |
| none_noaug_control | 8 | 9 | 32 | 10 | 3.56298 | 3.66769 | -0.104707 | -0.0890634 | 0.2 |
| none_noaug_control | 9 | 10 | 32 | 6 | 2.9146 | 2.97778 | -0.0631758 | -0.30893 | 0.5 |
| none_noaug_control | 10 | 11 | 32 | 9 | 3.27691 | 3.74554 | -0.46863 | -0.511415 | 0.222222 |
| none_noaug_control | 11 | 12 | 32 | 3 | 2.29166 | 2.3042 | -0.0125353 | -0.247013 | 0.333333 |
| none_noaug_control | 12 | 13 | 32 | 13 | 3.38116 | 3.22454 | 0.156613 | -0.306441 | 0.923077 |
| none_noaug_control | 13 | 14 | 32 | 7 | 2.81134 | 2.65552 | 0.155817 | -0.680487 | 0.857143 |
| none_noaug_control | 14 | 15 | 32 | 5 | 3.00896 | 2.98906 | 0.0198992 | 0.125761 | 0.6 |
| none_noaug_control | 15 | 16 | 32 | 3 | 2.97322 | 2.42075 | 0.552461 | 0.760842 | 0.666667 |
| none_noaug_control | 16 | 17 | 32 | 5 | 2.63888 | 2.31651 | 0.322367 | 0.27554 | 0.8 |
| none_noaug_control | 17 | 18 | 32 | 12 | 3.22311 | 3.05827 | 0.16484 | 0.275444 | 0.75 |
| none_noaug_control | 18 | 19 | 32 | 9 | 3.12554 | 3.18496 | -0.0594188 | -0.0206687 | 0.333333 |
| none_noaug_control | 19 | 20 | 32 | 6 | 2.98403 | 2.86493 | 0.119093 | -0.174528 | 0.666667 |
| none_noaug_control | 20 | 21 | 32 | 4 | 3.21208 | 2.57764 | 0.634438 | 0.688738 | 0.75 |
| none_noaug_control | 21 | 22 | 32 | 12 | 3.10837 | 3.24481 | -0.136444 | -0.262698 | 0.333333 |
| none_noaug_control | 22 | 23 | 32 | 4 | 2.61899 | 2.66474 | -0.0457464 | 0.404724 | 0.5 |
| none_noaug_control | 23 | 24 | 32 | 3 | 2.32937 | 2.25769 | 0.07168 | -0.0209655 | 0.666667 |
| none_noaug_control | 24 | 25 | 32 | 9 | 3.56426 | 3.66113 | -0.0968723 | -0.431258 | 0.333333 |
| none_noaug_control | 25 | 26 | 32 | 11 | 2.95758 | 2.88007 | 0.0775098 | -0.425248 | 0.636364 |
| none_noaug_control | 26 | 27 | 32 | 6 | 2.85584 | 2.41729 | 0.438546 | 0.877877 | 1 |
| none_noaug_control | 27 | 28 | 32 | 9 | 2.81036 | 2.45605 | 0.354309 | 0.00735298 | 1 |
| none_noaug_control | 28 | 29 | 32 | 5 | 2.64115 | 2.7115 | -0.070351 | -0.472579 | 0.4 |
| none_noaug_control | 29 | 30 | 32 | 1 | 2.42623 | 2.28227 | 0.143961 |  | 1 |
| none_noaug_control | 30 | 31 | 32 | 13 | 3.31257 | 3.28612 | 0.026454 | -0.257991 | 0.692308 |

## Subject stats preview
| method | subject_id | n_high | zero_rmse_high | model_rmse_high | improvement_zero_minus_model | pearson_high | sign_acc_high |
| --- | --- | --- | --- | --- | --- | --- | --- |
| gaussian_0p10 | 1 | 9 | 3.04023 | 3.05245 | -0.0122156 | 0.131731 | 0.444444 |
| gaussian_0p10 | 2 | 15 | 3.67611 | 3.95183 | -0.275729 | -0.11083 | 0.533333 |
| gaussian_0p10 | 3 | 6 | 3.07842 | 3.21391 | -0.135489 | -0.171992 | 0.333333 |
| gaussian_0p10 | 5 | 8 | 2.91682 | 2.86975 | 0.0470671 | -0.0368767 | 0.625 |
| gaussian_0p10 | 6 | 23 | 4.32317 | 4.08014 | 0.243023 | 0.0388212 | 0.913043 |
| gaussian_0p10 | 7 | 7 | 2.6604 | 4.13711 | -1.4767 | -0.376732 | 0 |
| gaussian_0p10 | 8 | 10 | 2.78607 | 2.58031 | 0.205751 | 0.440539 | 0.8 |
| gaussian_0p10 | 9 | 10 | 3.56298 | 3.67079 | -0.107811 | -0.0891876 | 0.2 |
| gaussian_0p10 | 10 | 6 | 2.9146 | 2.97824 | -0.0636442 | -0.320113 | 0.5 |
| gaussian_0p10 | 11 | 9 | 3.27691 | 3.75146 | -0.474552 | -0.510358 | 0.111111 |
| gaussian_0p10 | 12 | 3 | 2.29166 | 2.3052 | -0.0135315 | -0.346381 | 0.333333 |
| gaussian_0p10 | 13 | 13 | 3.38116 | 3.22952 | 0.151635 | -0.31219 | 0.923077 |
| gaussian_0p10 | 14 | 7 | 2.81134 | 2.63691 | 0.174426 | -0.343758 | 0.571429 |
| gaussian_0p10 | 15 | 5 | 3.00896 | 3.09188 | -0.082915 | -0.158566 | 0.4 |
| gaussian_0p10 | 16 | 3 | 2.97322 | 2.24618 | 0.727038 | 0.973601 | 1 |
| gaussian_0p10 | 17 | 5 | 2.63888 | 2.51029 | 0.128582 | 0.693879 | 0.8 |
| gaussian_0p10 | 18 | 12 | 3.22311 | 3.05668 | 0.166436 | 0.288521 | 0.75 |
| gaussian_0p10 | 19 | 9 | 3.12554 | 3.22773 | -0.102185 | 0.0305233 | 0.333333 |
| gaussian_0p10 | 20 | 6 | 2.98403 | 2.86052 | 0.123505 | -0.173015 | 0.666667 |
| gaussian_0p10 | 21 | 4 | 3.21208 | 3.02852 | 0.183563 | 0.396353 | 0.75 |
| gaussian_0p10 | 22 | 12 | 3.10837 | 3.21166 | -0.10329 | -0.205133 | 0.333333 |
| gaussian_0p10 | 23 | 4 | 2.61899 | 2.75214 | -0.133146 | -0.123223 | 0.25 |
| gaussian_0p10 | 24 | 3 | 2.32937 | 2.0919 | 0.237469 | 0.754222 | 1 |
| gaussian_0p10 | 25 | 9 | 3.56426 | 3.66433 | -0.10007 | -0.433957 | 0.333333 |
| gaussian_0p10 | 26 | 11 | 2.95758 | 2.8881 | 0.0694885 | -0.252214 | 0.454545 |
| gaussian_0p10 | 27 | 6 | 2.85584 | 2.83708 | 0.0187565 | 0.413905 | 0.5 |
| gaussian_0p10 | 28 | 9 | 2.81036 | 2.32344 | 0.486927 | 0.175893 | 0.888889 |
| gaussian_0p10 | 29 | 5 | 2.64115 | 2.60589 | 0.035252 | -0.671477 | 0.6 |
| gaussian_0p10 | 30 | 1 | 2.42623 | 2.28518 | 0.141048 |  | 1 |
| gaussian_0p10 | 31 | 13 | 3.31257 | 3.34246 | -0.0298885 | -0.116016 | 0.461538 |
| gaussian_0p10 | 32 | 2 | 2.41785 | 2.52785 | -0.109998 |  | 0.5 |
| gaussian_0p10 | 33 | 5 | 2.98841 | 2.88492 | 0.103493 | -0.298098 | 0.6 |
| gaussian_0p10 | 34 | 3 | 2.30855 | 2.2208 | 0.0877454 | 0.814378 | 0.666667 |
| gaussian_0p10 | 35 | 5 | 3.06011 | 3.34745 | -0.287343 | -0.846091 | 0 |
| gaussian_0p10 | 36 | 5 | 2.74564 | 2.4926 | 0.253045 | -0.0242575 | 1 |
| gaussian_0p10 | 37 | 4 | 3.12059 | 3.07643 | 0.0441649 | 0.475252 | 0.75 |
| gaussian_0p10 | 38 | 5 | 2.68902 | 2.4756 | 0.213427 | 0.84755 | 0.6 |
| gaussian_0p10 | 39 | 10 | 3.05362 | 3.06121 | -0.00759272 | -0.372889 | 0.6 |
| gaussian_0p10 | 40 | 16 | 3.86526 | 4.36809 | -0.502826 | -0.161596 | 0.375 |
| gaussian_0p10 | 41 | 13 | 3.63258 | 3.06732 | 0.565266 | 0.311604 | 1 |