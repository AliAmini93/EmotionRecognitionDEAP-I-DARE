# I-DARE Representation-Learning Feasibility Gate

This document closes the current fixed engineered EEG/EMG feature route for actionable personalization, while preserving the confirmed arousal high-disagreement EEG signal as a useful starting point for learned representations.

## Decision table

| target | representation_gate_decision | fixed_feature_actionability_status | physiology_signal_status | locked_challenge_baseline | locked_B2_rmse | positive_signal_to_preserve | recommended_first_experiment | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | GO_REPRESENTATION_LEARNING_REQUIRED | FIXED_FEATURE_ROUTE_EXHAUSTED_FOR_ACTIONABLE_PERSONALIZATION | DETECTION_SIGNAL_PRESENT_BUT_NOT_ACTIONABLE | B2_LOCKED_kernel_residual_shrink4_k16 | 1.657667 | eeg_bandpower/physio_eeg_bandpower_ridge on high-disagreement residuals | raw_or_time_frequency_EEG_arousal_high_disagreement_representation | Arousal has a confirmed high-disagreement EEG-bandpower residual signal, but direct correction/bridge/rescue/sample-reduction failed. The next route should learn a representation that can preserve the signal while correcting scale and direction. |
| valence | GO_REPRESENTATION_LEARNING_REQUIRED | FIXED_FEATURE_ROUTE_EXHAUSTED_FOR_ACTIONABLE_PERSONALIZATION | NO_ACTIONABLE_FIXED_FEATURE_SIGNAL | B2_LOCKED_kernel_residual_shrink4_k16 | 1.159189 | none_confirmed_with_current_fixed_features | multimodal_EEG_EMG_residual_representation_learning | Fixed features failed the actionable gates. The next route should test learned EEG/EMG representations rather than more linear correction on engineered features. |

## Evidence rollup

| target | locked_B2_kernel_residual_rmse | model_family_confirmatory_decision | physiology_vs_locked_status | direct_deviation_status | high_disagreement_confirmatory_status | high_disagreement_confirmed | high_disagreement_feature_block | high_disagreement_model | high_disagreement_lift | bridge_status | failure_rescue_status | sample_reduction_status | sample_reduction_best_lower_k_rmse | sample_reduction_delta_vs_locked_B2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | 1.657667 | GO_CONFIRMED_MODEL_FAMILY_CALIBRATION | CURRENT_PHYSIOLOGY_NO_GO_AGAINST_LOCKED_PERSONALIZATION | WEAK_SIGNAL_BUT_NOT_ACTIONABLE_WITH_CURRENT_FEATURES | GO_CONFIRMED_HIGH_DISAGREEMENT_PHYSIOLOGY | True | eeg_bandpower | physio_eeg_bandpower_ridge | 0.071725 | NO_GO_PHYSIOLOGY_BRIDGE_TO_LOCKED_PERSONALIZATION | NO_GO_FAILURE_SUBJECT_PHYSIOLOGY_RESCUE | NO_GO_PHYSIOLOGY_ASSISTED_SAMPLE_REDUCTION | 1.940719 | 0.283052 |
| valence | 1.159189 | GO_CONFIRMED_MODEL_FAMILY_CALIBRATION | CURRENT_PHYSIOLOGY_NO_GO_AGAINST_LOCKED_PERSONALIZATION | NO_GO_CURRENT_FIXED_FEATURES_FOR_DIRECT_DEVIATION | WEAK_OR_NO_GO_HIGH_DISAGREEMENT_PHYSIOLOGY | False | emg_lagged_interaction_experimental | physio_emg_lagged_interaction_experimental_ridge | 0.002009 | NO_GO_PHYSIOLOGY_BRIDGE_TO_LOCKED_PERSONALIZATION | NO_GO_FAILURE_SUBJECT_PHYSIOLOGY_RESCUE | NO_GO_PHYSIOLOGY_ASSISTED_SAMPLE_REDUCTION | 1.257912 | 0.098723 |

## Route matrix

| route | status | why | keep |
| --- | --- | --- | --- |
| A_fixed_engineered_features_plus_linear_or_kernel_correction | CLOSED_OR_DEPRIORITIZED | Zero-shot, after-fewshot, locked-baseline bridge, failure-subject rescue, and sample-reduction gates did not pass. | Use as historical baseline and sanity-check only. |
| B_high_disagreement_arousal_detection | KEEP_AS_SIGNAL_SOURCE_NOT_DIRECT_CORRECTION | Arousal high-disagreement EEG-bandpower passed confirmatory residual gates, but failed bridge/rescue/sample-reduction actionability. | Use for gating, uncertainty, curriculum, or targeted representation learning. |
| C_learned_EEG_or_EMG_representations | NEXT_PRIMARY_ROUTE | The fixed-feature bottleneck is now the most plausible blocker after repeated no-go actionability audits. | Raw/time-frequency/self-supervised/contrastive subject-adaptive representation learning. |
| D_cross_dataset_or_pretraining | SECONDARY_SUPPORTING_ROUTE | DEAP has limited per-subject calibration data, so representation learning may need pretraining or external affective physiology data. | Pretrain on available EEG/EMG datasets, then evaluate under locked I-DARE gates. |

## Success gates for future EEG/EMG claims

| gate | required_for_claim | metric |
| --- | --- | --- |
| G1_locked_personalization_incremental_value | Any new EEG/EMG model must beat or complement B2_LOCKED kernel_residual_shrink4 k=16, not merely stimulus-only. | pooled RMSE lift >= 0.02 plus paired subject CI/sign tests and stable win margin |
| G2_high_disagreement_residual_signal | If claiming targeted residual learning, evaluate high-disagreement residuals separately. | positive residual RMSE lift, residual Pearson > 0.1, permutation p < 0.05, paired subject support |
| G3_calibration_reduction | If claiming practical calibration savings, lower-k model must match locked k=16. | candidate RMSE within +0.02 of B2 plus subject-level stability |
| G4_no_degradation | Gating or targeted corrections must not improve one subset by harming pooled performance. | pooled and paired subject metrics remain non-inferior to B2 |

## Experiment backlog

| priority | experiment_id | title | input_representation | model_family | target | evaluation_gate | success_condition |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 06a | Arousal high-disagreement EEG representation prototype | EEG time-frequency tensors or raw/preprocessed EEG segments | small CNN/TCN/Transformer encoder with residual head | arousal deviation on high-disagreement trials | G2 then G1 | beats fixed EEG-bandpower residual model on high-disagreement arousal and does not degrade locked personalization when used as gate/correction |
| 2 | 06b | Subject-adaptive residual representation | EEG/EMG learned embeddings plus k-shot subject context | FiLM/adapters/prototypical or conditional residual head | rating minus stimulus mean / residual correction | G1 and G3 | beats B2 locked baseline or matches B2 with fewer calibration samples |
| 3 | 06c | Self-supervised physiology pretraining | raw EEG/EMG or time-frequency windows | masked reconstruction, contrastive predictive coding, subject-invariant contrastive learning | pretrained representation for downstream residual/deviation prediction | G1/G2/G3 | pretrained representation beats fixed-feature models under locked ROCA gates |
| 4 | 06d | Arousal high-disagreement uncertainty/gating model | confirmed EEG-bandpower signal plus locked model uncertainty/error features | risk classifier or mixture-of-experts gate | detect trials where locked personalization is likely wrong | G4 | improves high-disagreement arousal triage without worsening pooled RMSE |

## Bottom line

The current fixed-feature EEG/EMG route should not be used for new success claims unless it beats the locked B2 personalization baseline. The next primary scientific route is representation learning: raw/time-frequency EEG/EMG encoders, self-supervised pretraining, subject-adaptive residual heads, and targeted arousal high-disagreement gating.
