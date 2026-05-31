# ROCA-I-DARE 06a6 Neural Anchor Against Fixed EEG-Bandpower

Purpose: check whether the raw-EEG neural pipeline can recover the simple fixed EEG-bandpower residual signal under LOSO.

## Decision
| target | decision | best_method | best_model_rmse_high | best_lift_vs_zero_high | fixed_bandpower_loaded | best_lift_vs_fixed_same_eval_high | best_lift_vs_locked_bridge_rmse | gaussian_delta_rmse_vs_noaug_positive_means_help | passes_zero_gate | passes_fixed_reference_gate | passes_locked_bridge_gate | anchor_close_to_fixed_reference_gate | interpretation | recommended_next_action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | NO_GO_NEURAL_PIPELINE_NOT_ANCHORED | neural_noaug_anchor | 3.62281 | 0.0103123 | True | -0.17557 | -1.00054 | -0.0420623 | False | False | False | False | The neural raw-EEG pipeline does not beat the practical gates under LOSO. This supports the diagnosis: weak residual identifiability plus subject calibration/domain shift. | Finalize the calibration-dominant negative result, unless a separate distillation/feature-anchor test is intentionally added. |

## Method metrics
| method | n_eval | n_high | zero_rmse_high | model_rmse_high | lift_vs_zero_high | fixed_rmse_same_eval_high | lift_vs_fixed_same_eval_high | locked_bridge_rmse_05ak | lift_vs_locked_bridge_rmse | pearson_high | sign_acc_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| neural_noaug_anchor | 192 | 67 | 3.63312 | 3.62281 | 0.0103123 | 3.44724 | -0.17557 | 2.62227 | -1.00054 | 0.16482 | 0.626866 |
| neural_gaussian_0p10_anchor | 192 | 67 | 3.63312 | 3.66487 | -0.03175 | 3.44724 | -0.217632 | 2.62227 | -1.0426 | 0.127166 | 0.358209 |

## Fixed bandpower loading audit
| path | exists | loaded | finite_rate | prediction_column | model_filter | merge_strategy | columns | error |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| docs/roca/idare_residual_physiology_feature_audit_current_predictions.csv | True | True | 1 | y_pred_deviation | physio_eeg_bandpower_ridge | row_order_after_filter | ["test_subject", "stimulus_id", "target", "feature_block", "model", "y_true_score", "train_stimulus_mean", "true_deviation_from_train_stimulus_mean", "y_pred_deviation", "y_pred_score"] |  |

## Fold metrics preview
| method | gaussian_std | best_epoch | best_val_loss | fit_n | val_n | test_n | final_train_loss | final_val_loss | fold | subject_id | n_high | zero_rmse_high | model_rmse_high | fixed_rmse_high | pearson_high | sign_acc_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| neural_noaug_anchor | 0 | 2 | 1.17616 | 1760 | 224 | 32 | 1.08837 | 1.17616 | 1 | 1 | 9 | 3.05427 | 3.19599 | 2.89654 | -0.633294 | 0.333333 |
| neural_noaug_anchor | 0 | 2 | 1.27967 | 1760 | 224 | 32 | 1.07922 | 1.27967 | 2 | 2 | 15 | 3.68067 | 3.63975 | 3.34451 | 0.287902 | 0.666667 |
| neural_noaug_anchor | 0 | 2 | 1.33828 | 1760 | 224 | 32 | 1.09311 | 1.33828 | 3 | 3 | 6 | 3.10819 | 3.02653 | 1.08204 | 0.401784 | 0.833333 |
| neural_noaug_anchor | 0 | 1 | 1.35064 | 1760 | 224 | 32 | 1.08936 | 1.38426 | 4 | 5 | 8 | 2.9091 | 2.90656 | 2.22277 | 0.0654343 | 0.75 |
| neural_noaug_anchor | 0 | 1 | 1.38846 | 1760 | 224 | 32 | 1.02936 | 1.39729 | 5 | 6 | 22 | 4.37945 | 4.3689 | 4.57198 | 0.19853 | 0.5 |
| neural_noaug_anchor | 0 | 1 | 1.04916 | 1760 | 224 | 32 | 1.11603 | 1.06921 | 6 | 7 | 7 | 2.66146 | 2.57036 | 2.57674 | -0.189021 | 1 |
| neural_gaussian_0p10_anchor | 0.1 | 2 | 1.10291 | 1760 | 224 | 32 | 1.08718 | 1.10291 | 1 | 1 | 9 | 3.05427 | 3.01195 | 2.89654 | 0.310055 | 0.666667 |
| neural_gaussian_0p10_anchor | 0.1 | 1 | 1.27777 | 1760 | 224 | 32 | 1.0702 | 1.29285 | 2 | 2 | 15 | 3.68067 | 3.70969 | 3.34451 | -0.0479749 | 0.2 |
| neural_gaussian_0p10_anchor | 0.1 | 2 | 1.25108 | 1760 | 224 | 32 | 1.09831 | 1.25108 | 3 | 3 | 6 | 3.10819 | 2.92851 | 1.08204 | -0.0794084 | 0.666667 |
| neural_gaussian_0p10_anchor | 0.1 | 1 | 1.02797 | 1760 | 224 | 32 | 1.12447 | 1.03934 | 4 | 5 | 8 | 2.9091 | 2.87312 | 2.22277 | -0.197684 | 0.75 |
| neural_gaussian_0p10_anchor | 0.1 | 1 | 0.838208 | 1760 | 224 | 32 | 1.09741 | 0.857826 | 5 | 6 | 22 | 4.37945 | 4.49908 | 4.57198 | 0.128201 | 0 |
| neural_gaussian_0p10_anchor | 0.1 | 2 | 1.08189 | 1760 | 224 | 32 | 1.11044 | 1.08189 | 6 | 7 | 7 | 2.66146 | 2.64592 | 2.57674 | -0.27486 | 0.714286 |

## Interpretation guide
- If neural LOSO is worse than fixed EEG-bandpower, the neural pipeline is not anchored and larger CNN search is unsafe.
- If neural matches fixed EEG-bandpower but still loses to locked B2, the problem is calibration/subject-style dominance, not architecture size.
- If neural beats fixed and locked B2, promote it to a confirmatory multi-seed run.
