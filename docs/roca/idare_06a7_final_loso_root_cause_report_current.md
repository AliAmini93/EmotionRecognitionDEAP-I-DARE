# I-DARE Final LOSO Root-Cause Report

## Final decision
| target | final_decision | primary_root_cause | ruled_out_as_primary_fix | what_did_help | fixed_feature_status | paper_claim | recommended_next_action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| arousal_high_disagreement_residual_LOSO | FINAL_CALIBRATION_DOMINANT_NEGATIVE_RESULT_FOR_GLOBAL_RAW_EEG_RESIDUAL_DECODING | subject calibration/domain shift plus weak transferable residual identifiability | generic Gaussian augmentation; raw EEG neural capacity search; unanchored larger CNNs | explicit subject calibration/k-shot bias correction helps, but does not beat the locked B2 personalization bridge | fixed EEG-bandpower remains a weak but more stable reference than raw neural anchor under the locked high-disagreement gate | Under strict LOSO, the current residual target is calibration-dominant. Global physiology decoding from raw EEG is not supported by the locked gates. | Stop blind architecture/augmentation search. Write the result as a calibration-dominant finding, or start a new explicitly personalized/calibrated target formulation. |

## Core interpretation
The locked evidence now points to one main diagnosis: the weak LOSO result is not primarily caused by missing Gaussian augmentation or by an under-sized raw EEG CNN. The current high-disagreement residual target is dominated by subject calibration/domain shift and weak transferable residual identifiability.

The old gaussian_0p10 result was useful as a clue, but the clean locked rerun did not reproduce it as a valid improvement under the current residual gate. The neural anchor also failed to reproduce even the fixed bandpower reference. So the safe conclusion is: stop blind deep/augmentation search and frame the result as calibration-dominant.

## Evidence rollup
| source | decision | best_method | best_model_rmse_high | best_lift_vs_zero_high | best_lift_vs_fixed_same_eval_high | best_lift_vs_locked_bridge_rmse | passes_zero_gate | passes_fixed_reference_gate | passes_locked_bridge_gate | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 06a1z_prior_map |  |  |  |  |  |  |  |  |  | Some EEG summary information can predict residuals when subject/stimulus distributions are easier, but much of that signal does not transfer cleanly to held-out subjects. |
| 06a3_identifiability | CALIBRATION_DOMINANT_NOT_GLOBAL_RESIDUAL_DECODING |  |  |  |  |  |  |  |  | Subject-style residual structure is repeatable, but shared stimulus residual structure is weak/non-repeatable. The viable route is explicit calibration/subject adaptation, not larger generic CNN search. |
| 06a4_subject_adaptation | GO_SUBJECT_ADAPTATION_IMPROVES_RESIDUAL_GATE | kshot_subject_mean_only |  |  |  |  |  |  |  | A normalization/adaptation candidate beats zero and the fixed EEG-bandpower reference on the high-disagreement residual gate. |
| 06a4b_locked_bridge_confirm | PARTIAL_GO_CALIBRATION_BEATS_FIXED_BUT_NOT_LOCKED_B2 | kshot_subject_mean_only |  |  |  | -0.0085344 |  |  |  | K-shot calibration strongly beats zero/fixed physiology, but it does not beat the locked B2 personalization bridge. This means the apparent 06a4 gain is mostly the same calibration effect that B2 already captures. Fixed EEG-bandpower plu... |
| 06a5_prior_aug_probe | RERUN_REQUIRED_GAUSSIAN10_PRIOR_EVIDENCE_NOT_LOCKED_COMPARABLE |  |  |  |  |  |  |  | False | Prior gaussian_0p10 evidence beats stimulus-only in the old score/oracle report, but it is not directly comparable to locked B2 or the current high-disagreement residual gate. It justifies a clean rerun under the current locked residual ... |
| 06a5b_gaussian10_locked_rerun | NO_GO_AUGMENTATION_DOES_NOT_FIX_LOSO | none_noaug_control | 3.26093 | 0.000704925 |  | -0.638662 | False | False | False | Clean locked-gate gaussian augmentation does not solve the LOSO residual problem. |
| 06a6_neural_anchor | NO_GO_NEURAL_PIPELINE_NOT_ANCHORED | neural_noaug_anchor | 3.27553 | -0.0144894 | -0.0814068 | -0.65326 | False | False | False | The neural raw-EEG pipeline does not beat the practical gates under LOSO. This supports the diagnosis: weak residual identifiability plus subject calibration/domain shift. |

## Method rollup
| source | method | n_eval | n_high | zero_rmse_high | model_rmse_high | lift_vs_zero_high | fixed_rmse_same_eval_high | lift_vs_fixed_same_eval_high | locked_bridge_rmse_05ak | lift_vs_locked_bridge_rmse | pearson_high | sign_acc_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 06a5b_gaussian10_locked_rerun | none_noaug_control | 2016 | 495 | 3.26163 | 3.26093 | 0.000704925 |  |  | 2.62227 | -0.638662 | 0.0967808 | 0.549495 |
| 06a5b_gaussian10_locked_rerun | gaussian_0p10 | 2016 | 495 | 3.26163 | 3.28025 | -0.0186151 |  |  | 2.62227 | -0.657982 | 0.0574436 | 0.555556 |
| 06a6_neural_anchor | neural_noaug_anchor | 2016 | 496 | 3.26104 | 3.27553 | -0.0144894 | 3.19412 | -0.0814068 | 2.62227 | -0.65326 | 0.0363288 | 0.467742 |
| 06a6_neural_anchor | neural_gaussian_0p10_anchor | 2016 | 496 | 3.26104 | 3.31088 | -0.0498385 | 3.19412 | -0.116756 | 2.62227 | -0.688609 | -0.0271953 | 0.493952 |
| 06a4b_locked_bridge_confirm | kshot_subject_mean_only |  |  |  |  |  |  |  | 2.62227 | -0.0085344 |  |  |
| 06a4b_locked_bridge_confirm | fixed_eeg_bandpower_plus_kshot_bias |  |  |  |  |  |  |  | 2.62227 | -0.0271478 |  |  |
| 06a4b_locked_bridge_confirm | kshot_subject_mean_only |  |  |  |  |  |  |  | 2.62227 | -0.0441002 |  |  |
| 06a4b_locked_bridge_confirm | fixed_eeg_bandpower_plus_kshot_bias |  |  |  |  |  |  |  | 2.62227 | -0.0621936 |  |  |
| 06a4b_locked_bridge_confirm | kshot_subject_mean_only |  |  |  |  |  |  |  | 2.62227 | -0.11468 |  |  |
| 06a4b_locked_bridge_confirm | fixed_eeg_bandpower_plus_kshot_bias |  |  |  |  |  |  |  | 2.62227 | -0.137827 |  |  |

## Next steps
| priority | step | title | purpose | success_condition |
| --- | --- | --- | --- | --- |
| 1 | paper_note | Write calibration-dominant negative-result section | Turn the ROCA evidence into a defensible project conclusion instead of running more blind models. | The manuscript/report separates old oracle/overlap gains from locked LOSO residual evidence. |
| 2 | optional_06a8 | Only if needed: explicit personalized/calibrated formulation | If the project needs a positive model, change the task to include allowed calibration context rather than pretending global LOSO residual decoding works. | Model is evaluated against locked B2 and reports calibration budget honestly. |
| 3 | archive | Archive failed global residual routes | Prevent repeated re-running of augmentation/deep searches that have already failed locked gates. | Decision log records gaussian_0p10 and neural anchor as no-go under current locked gate. |
