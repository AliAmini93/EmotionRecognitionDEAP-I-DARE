# ROCA 06a5 - Augmentation locked-gate probe

Purpose: inspect prior augmentation evidence and decide whether `gaussian_0p10` deserves a current locked-gate rerun.

## Decision
| target | decision | gaussian10_rmse | stimulus_only_rmse | lift_vs_stimulus_rmse | locked_bridge_rmse_05ak | kshot_06a4b_best_rmse | passes_stimulus_gate | passes_locked_bridge_gate | passes_kshot_06a4b_gate | interpretation | recommended_next_action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | RERUN_REQUIRED_GAUSSIAN10_PRIOR_EVIDENCE_NOT_LOCKED_COMPARABLE | 1.83105 | 1.9442 | 0.113158 | 2.62227 | 2.6308 | True | True | True | Prior gaussian_0p10 evidence beats stimulus-only and appears better than the locked B2 bridge. This is strong enough to justify a real 06a5 rerun under the current residual locked gate. | Run a proper locked-gate gaussian_0p10 residual experiment with no test-label checkpointing, subject-level validation, fixed zero/fixed/B2 references, and paired subject bootstrap. |

## Prior gaussian_0p10 oracle/smoke evidence
| target | path | available | model_augmentation_config | model_n | model_mae | model_rmse | model_pearson | model_balanced_accuracy | model_macro_f1 | model_auroc | model_dev_rmse | model_dev_pearson | model_dev_sign_acc | model_pred_dev_std | model_lift_vs_stimulus_rmse | model_lift_vs_stimulus_balanced_accuracy | model_lift_vs_stimulus_auroc | model_lift_vs_stimulus_dev_rmse | stimulus_mae | stimulus_rmse | stimulus_pearson | stimulus_balanced_accuracy | stimulus_macro_f1 | stimulus_auroc | stimulus_dev_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | docs/roca/eeg_gaussian10_arousal_test_oracle_main_metrics_current.csv | True | gaussian_0p10 | 2016 | 1.46712 | 1.83105 | 0.685691 | 0.77756 | 0.779984 | 0.855132 | 1.83105 | 0.337169 | 0.623016 | 0.64202 | 0.113158 | 0.00893734 | 0.0390582 | 0.113158 | 1.57993 | 1.9442 | 0.634375 | 0.768623 | 0.773911 | 0.816074 | 1.9442 |
| valence | docs/roca/eeg_gaussian10_valence_test_oracle_main_metrics_current.csv | True | gaussian_0p10 | 2016 | 0.974643 | 1.21529 | 0.875817 | 0.879868 | 0.865827 | 0.952116 | 1.21529 | 0.257874 | 0.584325 | 0.313236 | 0.0424825 | 0.000308264 | 0.00883036 | 0.0424825 | 1.02207 | 1.25777 | 0.866307 | 0.879559 | 0.865804 | 0.943286 | 1.25777 |

## Locked bridge reference
| path | available | target | decision | locked_bridge_rmse_05ak | best_candidate_rmse | best_lift_vs_zero | best_lift_vs_fixed_same_eval | best_lift_vs_locked_bridge_rmse | best_passes_locked_bridge_gate | recommended_next_action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| docs/roca/idare_06a4b_kshot_calibration_locked_bridge_confirm_current_decision_table.csv | True | arousal | PARTIAL_GO_CALIBRATION_BEATS_FIXED_BUT_NOT_LOCKED_B2 | 2.62227 | 2.6308 | 0.61055 | 0.539197 | -0.0085344 | False | Do not claim a new physiology/deep gain. Either test augmentation under locked gates or write the calibration-dominant conclusion. |

## Ranked augmentation matrix evidence
| augmentation_config | target | model | n | rmse | pearson | balanced_accuracy | auroc | dev_rmse | dev_pearson | dev_sign_acc | pred_dev_std | lift_vs_stimulus_rmse | lift_vs_stimulus_balanced_accuracy | lift_vs_stimulus_auroc | lift_vs_stimulus_dev_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gaussian_0p10 | arousal | eeg_bc_residual_huber_norm_augmented_smoke | 192 | 2.30606 | 0.496487 | 0.623411 | 0.698243 | 2.30606 | 0.467055 | 0.692708 | 0.226875 | 0.0769568 | -0.00458716 | 0.0505692 | 0.0769568 |
| gaussian_0p05 | arousal | eeg_bc_residual_huber_norm_augmented_smoke | 192 | 2.34841 | 0.450758 | 0.635459 | 0.660219 | 2.34841 | 0.0929563 | 0.572917 | 0.33946 | 0.0346001 | 0.00746104 | 0.0125456 | 0.0346001 |
| gain_0p10 | arousal | eeg_bc_residual_huber_norm_augmented_smoke | 192 | 2.37271 | 0.439878 | 0.618824 | 0.660661 | 2.37271 | 0.0216094 | 0.53125 | 0.245934 | 0.0103077 | -0.00917431 | 0.0129877 | 0.0103077 |
| none | arousal | eeg_bc_residual_huber_norm_augmented_smoke | 192 | 2.44358 | 0.444016 | 0.627998 | 0.656682 | 2.44358 | 0.0467274 | 0.458333 | 0.271399 | -0.0605641 | 0 | 0.00900851 | -0.0605641 |
| gaussian_0p05_gain_0p10 | arousal | eeg_bc_residual_huber_norm_augmented_smoke | 192 | 2.4491 | 0.434165 | 0.617387 | 0.657677 | 2.4491 | -0.0220293 | 0.526042 | 0.275916 | -0.0660817 | -0.0106113 | 0.0100033 | -0.0660817 |
| gaussian_0p05_shift16 | arousal | eeg_bc_residual_huber_norm_augmented_smoke | 192 | 2.46456 | 0.393941 | 0.618824 | 0.615342 | 2.46456 | -0.28949 | 0.369792 | 0.272577 | -0.0815433 | -0.00917431 | -0.0323312 | -0.0815433 |

## Prior augmentation evidence rows
_No prior augmentation evidence rows found._

## Interpretation
Prior gaussian_0p10 evidence beats stimulus-only and appears better than the locked B2 bridge. This is strong enough to justify a real 06a5 rerun under the current residual locked gate.

## Recommended next action
Run a proper locked-gate gaussian_0p10 residual experiment with no test-label checkpointing, subject-level validation, fixed zero/fixed/B2 references, and paired subject bootstrap.


## Critical comparability correction

The prior `gaussian_0p10` result is promising, but it came from the old score/oracle report and is not directly comparable to locked B2 or the current high-disagreement residual gate. For decision-making, the locked-B2/k-shot pass flags are treated as **not passed** until a clean locked-gate rerun is completed.
