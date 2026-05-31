# I-DARE LOSO root-cause conclusion: calibration-dominant negative result

## One-sentence conclusion
Under strict LOSO, the current arousal high-disagreement residual target is dominated by subject calibration/domain shift, and global raw-EEG residual decoding is not supported by the locked gates.

## Decision
| result_type | scope | main_root_cause | not_primary_fixes | what_worked_partially | best_stable_nonpersonalized_reference | final_action | gaussian10_locked_gate_decision | neural_anchor_decision | final_roca_decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| calibration_dominant_negative_result | arousal high-disagreement residual under strict LOSO | subject calibration/domain shift plus weak transferable residual identifiability | generic gaussian augmentation; raw EEG neural capacity search; unanchored larger CNN search | k-shot/subject calibration improved residuals but did not beat locked B2 personalization bridge | fixed EEG bandpower is weak but more stable than raw neural anchor | stop blind global residual decoding search; write result or redesign task as explicitly personalized/calibrated | NO_GO_AUGMENTATION_DOES_NOT_FIX_LOSO | NO_GO_NEURAL_PIPELINE_NOT_ANCHORED | FINAL_CALIBRATION_DOMINANT_NEGATIVE_RESULT_FOR_GLOBAL_RAW_EEG_RESIDUAL_DECODING |

## Evidence rollup
| step | target | decision | final_decision | best_method | best_model_rmse_high | best_lift_vs_zero_high | best_lift_vs_fixed_same_eval_high | best_lift_vs_locked_bridge_rmse | passes_zero_gate | passes_fixed_reference_gate | passes_locked_bridge_gate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 06a3 | arousal | CALIBRATION_DOMINANT_NOT_GLOBAL_RESIDUAL_DECODING |  |  |  |  |  |  |  |  |  |
| 06a4 | arousal | GO_SUBJECT_ADAPTATION_IMPROVES_RESIDUAL_GATE |  | kshot_subject_mean_only |  |  |  |  |  |  |  |
| 06a4b | arousal | PARTIAL_GO_CALIBRATION_BEATS_FIXED_BUT_NOT_LOCKED_B2 |  | kshot_subject_mean_only |  |  |  | -0.0085344 |  |  |  |
| 06a5 | arousal | RERUN_REQUIRED_GAUSSIAN10_PRIOR_EVIDENCE_NOT_LOCKED_COMPARABLE |  |  |  |  |  |  |  |  | False |
| 06a5b | arousal | NO_GO_AUGMENTATION_DOES_NOT_FIX_LOSO |  | none_noaug_control | 3.26093 | 0.000704925 |  | -0.638662 | False | False | False |
| 06a6 | arousal | NO_GO_NEURAL_PIPELINE_NOT_ANCHORED |  | neural_noaug_anchor | 3.27553 | -0.0144894 | -0.0814068 | -0.65326 | False | False | False |
| 06a7 | arousal_high_disagreement_residual_LOSO |  | FINAL_CALIBRATION_DOMINANT_NEGATIVE_RESULT_FOR_GLOBAL_RAW_EEG_RESIDUAL_DECODING |  |  |  |  |  |  |  |  |

## Plain-language interpretation
- Old Gaussian augmentation looked promising in older/oracle-style reports, but the locked rerun did not fix LOSO.
- The raw neural pipeline did not even anchor to the weak fixed-bandpower reference under the high-disagreement locked gate.
- K-shot calibration helps because it captures subject bias/style, but it is not a new global physiology model and it did not beat the locked B2 bridge.
- The correct next research move is not another bigger CNN. It is either a paper/report conclusion, or a new task definition that explicitly allows calibration/personalization.

## Recommended next step
Write the calibration-dominant result into the manuscript/decision log. Only start 06a8 if the project explicitly accepts a personalized/calibrated protocol with a stated calibration budget.
