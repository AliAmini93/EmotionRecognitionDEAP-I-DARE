# ROCA-I-DARE 06a6 Neural Anchor Against Fixed EEG-Bandpower

Purpose: check whether the raw-EEG neural pipeline can recover the simple fixed EEG-bandpower residual signal under LOSO.

## Decision
| target | decision | best_method | best_model_rmse_high | best_lift_vs_zero_high | fixed_bandpower_loaded | best_lift_vs_fixed_same_eval_high | best_lift_vs_locked_bridge_rmse | gaussian_delta_rmse_vs_noaug_positive_means_help | passes_zero_gate | passes_fixed_reference_gate | passes_locked_bridge_gate | anchor_close_to_fixed_reference_gate | interpretation | recommended_next_action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | NO_GO_NEURAL_PIPELINE_NOT_ANCHORED | neural_noaug_anchor | 3.27553 | -0.0144894 | True | -0.0814068 | -0.65326 | -0.0353491 | False | False | False | False | The neural raw-EEG pipeline does not beat the practical gates under LOSO. This supports the diagnosis: weak residual identifiability plus subject calibration/domain shift. | Finalize the calibration-dominant negative result, unless a separate distillation/feature-anchor test is intentionally added. |

## Method metrics
| method | n_eval | n_high | zero_rmse_high | model_rmse_high | lift_vs_zero_high | fixed_rmse_same_eval_high | lift_vs_fixed_same_eval_high | locked_bridge_rmse_05ak | lift_vs_locked_bridge_rmse | pearson_high | sign_acc_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| neural_noaug_anchor | 2016 | 496 | 3.26104 | 3.27553 | -0.0144894 | 3.19412 | -0.0814068 | 2.62227 | -0.65326 | 0.0363288 | 0.467742 |
| neural_gaussian_0p10_anchor | 2016 | 496 | 3.26104 | 3.31088 | -0.0498385 | 3.19412 | -0.116756 | 2.62227 | -0.688609 | -0.0271953 | 0.493952 |

## Fixed bandpower loading audit
| path | exists | loaded | finite_rate | prediction_column | model_filter | merge_strategy | columns | error |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| docs/roca/idare_residual_physiology_feature_audit_current_predictions.csv | True | True | 1 | y_pred_deviation | physio_eeg_bandpower_ridge | row_order_after_filter | ["test_subject", "stimulus_id", "target", "feature_block", "model", "y_true_score", "train_stimulus_mean", "true_deviation_from_train_stimulus_mean", "y_pred_deviation", "y_pred_score"] |  |

## Fold metrics preview
| method | gaussian_std | best_epoch | best_val_loss | fit_n | val_n | test_n | final_train_loss | final_val_loss | fold | subject_id | n_high | zero_rmse_high | model_rmse_high | fixed_rmse_high | pearson_high | sign_acc_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| neural_noaug_anchor | 0 | 4 | 1.30469 | 1760 | 224 | 32 | 0.946603 | 1.46102 | 1 | 1 | 9 | 3.05427 | 2.07724 | 2.89654 | 0.780043 | 0.777778 |
| neural_noaug_anchor | 0 | 4 | 1.31011 | 1760 | 224 | 32 | 0.931557 | 1.34126 | 2 | 2 | 15 | 3.68067 | 3.98423 | 3.34451 | 0.239206 | 0.2 |
| neural_noaug_anchor | 0 | 1 | 1.48418 | 1760 | 224 | 32 | 0.914391 | 1.54052 | 3 | 3 | 6 | 3.10819 | 3.06112 | 1.08204 | -0.893396 | 1 |
| neural_noaug_anchor | 0 | 1 | 1.25741 | 1760 | 224 | 32 | 0.954389 | 1.47528 | 4 | 5 | 8 | 2.9091 | 3.05698 | 2.22277 | 0.631287 | 0 |
| neural_noaug_anchor | 0 | 1 | 1.18557 | 1760 | 224 | 32 | 0.960305 | 1.34244 | 5 | 6 | 22 | 4.37945 | 4.42264 | 4.57198 | 0.212176 | 0.0909091 |
| neural_noaug_anchor | 0 | 3 | 0.96675 | 1760 | 224 | 32 | 0.954491 | 1.04833 | 6 | 7 | 7 | 2.66146 | 2.82521 | 2.57674 | -0.477549 | 0.714286 |
| neural_noaug_anchor | 0 | 1 | 1.19428 | 1760 | 224 | 32 | 0.919216 | 1.29621 | 7 | 8 | 10 | 2.78018 | 2.77883 | 3.09392 | 0.175338 | 0.6 |
| neural_noaug_anchor | 0 | 2 | 1.2692 | 1760 | 224 | 32 | 0.922033 | 1.43256 | 8 | 9 | 10 | 3.54704 | 2.73039 | 2.73058 | -0.0962692 | 0.9 |
| neural_noaug_anchor | 0 | 4 | 0.925954 | 1760 | 224 | 32 | 0.982683 | 1.03613 | 9 | 10 | 7 | 2.83551 | 2.99064 | 2.9768 | -0.530361 | 0.285714 |
| neural_noaug_anchor | 0 | 3 | 1.09144 | 1760 | 224 | 32 | 0.959351 | 1.18227 | 10 | 11 | 9 | 3.29289 | 3.52166 | 3.05165 | -0.25399 | 0.444444 |
| neural_noaug_anchor | 0 | 5 | 1.33015 | 1760 | 224 | 32 | 0.958721 | 1.37361 | 11 | 12 | 3 | 2.31394 | 2.71758 | 2.42195 | -0.680661 | 0.333333 |
| neural_noaug_anchor | 0 | 1 | 1.07624 | 1760 | 224 | 32 | 0.949066 | 1.18501 | 12 | 13 | 13 | 3.37182 | 3.38399 | 2.46461 | -0.368285 | 0.307692 |
| neural_noaug_anchor | 0 | 1 | 1.07055 | 1760 | 224 | 32 | 0.960701 | 1.31003 | 13 | 14 | 7 | 2.81984 | 2.76611 | 2.46199 | -0.384988 | 1 |
| neural_noaug_anchor | 0 | 5 | 1.16528 | 1760 | 224 | 32 | 0.950937 | 1.30387 | 14 | 15 | 5 | 3.00781 | 3.30931 | 3.21522 | -0.57915 | 0.2 |
| neural_noaug_anchor | 0 | 4 | 0.916352 | 1760 | 224 | 32 | 0.972261 | 1.01139 | 15 | 16 | 4 | 2.80961 | 2.20822 | 2.66755 | 0.779066 | 0.75 |
| neural_noaug_anchor | 0 | 2 | 1.10062 | 1760 | 224 | 32 | 0.953564 | 1.4118 | 16 | 17 | 5 | 2.63698 | 2.60103 | 3.02012 | 0.953461 | 0.4 |
| neural_noaug_anchor | 0 | 1 | 1.18374 | 1760 | 224 | 32 | 0.936406 | 1.38486 | 17 | 18 | 11 | 3.29189 | 3.34026 | 2.87994 | -0.0495052 | 0.272727 |
| neural_noaug_anchor | 0 | 4 | 0.971859 | 1760 | 224 | 32 | 0.975599 | 1.09003 | 18 | 19 | 9 | 3.10079 | 3.33411 | 3.20888 | 0.24389 | 0.333333 |
| neural_noaug_anchor | 0 | 1 | 1.0404 | 1760 | 224 | 32 | 0.980851 | 1.33546 | 19 | 20 | 6 | 3.02052 | 3.17427 | 3.1125 | -0.68519 | 0 |
| neural_noaug_anchor | 0 | 1 | 1.17333 | 1760 | 224 | 32 | 0.965145 | 1.3188 | 20 | 21 | 4 | 3.20197 | 3.14443 | 3.15176 | 0.683921 | 1 |

## Interpretation guide
- If neural LOSO is worse than fixed EEG-bandpower, the neural pipeline is not anchored and larger CNN search is unsafe.
- If neural matches fixed EEG-bandpower but still loses to locked B2, the problem is calibration/subject-style dominance, not architecture size.
- If neural beats fixed and locked B2, promote it to a confirmatory multi-seed run.
