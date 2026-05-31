# I-DARE / ROCA Final Research Ledger

generated_at: `2026-05-31T12:42:11+00:00`
current_branch: `roca-idare-killtest`
clean_worktree: `False`

## Final decision

| final_decision | scientific_state | recommended_next_action |
| --- | --- | --- |
| ROCA_CURRENT_TRUTH_BRANCH_READY_FOR_RESEARCH_DECISION_PACK | strict_LOSO_global_raw_EEG_EMG_residual_decoding_not_supported; calibration_personalization_is_the_only_partial_positive_route | write final paper/report decision pack; choose one calibrated/adaptation-assisted route only if a positive model claim is required |

## What happened across ROCA

| phase | status | summary | evidence |
| --- | --- | --- | --- |
| 00_git_state | complete | ROCA is the active research branch; main was restored after accidental merge; historical branches were merged into ROCA and archived/deleted remotely. | origin/roca-idare-killtest plus archive tags |
| 01_baselines_and_labels | complete | Stimulus-only and label/task protocol baselines established; old literature-level LOSO difficulty was confirmed in this project-specific protocol. | docs/roca/stimulus_only_baseline_current.*, docs/idare_label_task_protocol_* |
| 02_emg_only | complete_negative | EMG-only, expanded EMG, nonlinear EMG, and augmented EMG probes did not rescue strict LOSO residual emotion recognition. | docs/roca/emg_*_current.*, docs/idare_w1c_emg_baseline_* |
| 03_eeg_raw_deep | complete_negative | Raw EEG residual/deep attempts, model-asset checks, residual training, multitask/sign auxiliary and oracle diagnostics did not provide a locked-gate global LOSO solution. | docs/roca/eeg_*_current.*, docs/roca/idare_06a*_current.* |
| 04_augmentation | complete_negative_under_locked_gate | Old gaussian_0p10 evidence was promising but non-comparable; clean locked rerun showed Gaussian augmentation does not fix LOSO. | idare_06a5 and idare_06a5b reports |
| 05_calibration_personalization | partial_positive_but_claim_shift | Subject calibration/k-shot/bias correction helped more than blind global models, but this changes the claim from pure zero-calibration LOSO to calibrated/personalized/adaptation-assisted recognition. | idare_06a4b, 05aa-05af, personalization bridge reports |
| 06_final_conclusion | locked_current_conclusion | Strict LOSO global raw EEG/EMG residual decoding remains unsupported by locked gates. The dominant issue is subject calibration/domain shift plus weak transferable residual identifiability. | idare_06a7, idare_06a7b, idare_06b3 reports |

## Key decision files read

| label | exists | path | first_rows |
| --- | --- | --- | --- |
| final_root_cause | True | docs/roca/idare_06a7_final_loso_root_cause_report_current_decision_table.csv | [{"target": "arousal_high_disagreement_residual_LOSO", "final_decision": "FINAL_CALIBRATION_DOMINANT_NEGATIVE_RESULT_FOR_GLOBAL_RAW_EEG_RESIDUAL_DECODING", "primary_root_cause": "subject calibration/domain shift plus ... |
| calibration_conclusion | True | docs/roca/idare_06a7b_calibration_dominant_conclusion_current_conclusion_table.csv | [{"result_type": "calibration_dominant_negative_result", "scope": "arousal high-disagreement residual under strict LOSO", "main_root_cause": "subject calibration/domain shift plus weak transferable residual identifiab... |
| consolidated_synthesis | True | docs/roca/idare_06b3_final_consolidated_roca_synthesis_current_decision_table.csv | [{"target": "I-DARE EEG/EMG emotion recognition under LOSO", "current_branch": "roca-consolidate-branches", "consolidated_branch_tip": "a64315d", "origin_consolidated_tip": "a64315d", "origin_roca_tip": "fe4c7b3", "or... |
| gaussian_locked_rerun | True | docs/roca/idare_06a5b_gaussian10_locked_gate_rerun_current_decision_table.csv | [{"target": "arousal", "decision": "NO_GO_AUGMENTATION_DOES_NOT_FIX_LOSO", "best_method": "none_noaug_control", "best_model_rmse_high": "3.2609287381060668", "best_lift_vs_zero_high": "0.0007049251602690987", "best_li... |
| neural_anchor | True | docs/roca/idare_06a6_neural_anchor_fixed_bandpower_current_decision_table.csv | [{"target": "arousal", "decision": "NO_GO_NEURAL_PIPELINE_NOT_ANCHORED", "best_method": "neural_noaug_anchor", "best_model_rmse_high": "3.275527238845825", "best_lift_vs_zero_high": "-0.014489412307739258", "fixed_ban... |
| kshot_locked_bridge | True | docs/roca/idare_06a4b_kshot_calibration_locked_bridge_confirm_current_decision_table.csv | [{"target": "arousal", "decision": "PARTIAL_GO_CALIBRATION_BEATS_FIXED_BUT_NOT_LOCKED_B2", "high_threshold": "2.2096774193548385", "high_threshold_source": "05ajb_confirmatory_threshold", "locked_bridge_rmse_05ak": "2... |
| branch_consolidation | True | docs/roca/idare_06b0_branch_consolidation_compact_audit_current_decision_table.csv | [{"decision": "DO_NOT_MERGE_OLD_BRANCHES_WHOLESALE", "why": "old wave/postwave branches contain useful evidence but also outdated objectives, old protocols, and non-current claims", "action": "cherry-pick only missing... |

## Remaining actions

| priority | action | why | success_condition |
| --- | --- | --- | --- |
| 1 | Generate paper/report claim section | Turn the negative/partial-positive evidence into a defensible scientific narrative. | The text clearly separates pure LOSO failure from calibrated/personalized positive direction. |
| 2 | Choose exactly one next positive route | Avoid another month of broad architecture search. | Route is either calibration-budget, UDA with unlabeled target data, or explicitly personalized EEG+EMG fusion. |
| 3 | Define allowed target-subject information budget | Calibration/adaptation claims are only defensible if the evaluation protocol states exactly what target data is allowed. | A table states zero-calibration, unlabeled-target, and k-shot labeled-target settings separately. |
| 4 | Run only one small confirmatory experiment if a positive claim is required | Current evidence already rules out blind raw EEG/EMG LOSO search. | The experiment is pre-gated against locked B2/personalization references and has a stop rule. |
| 5 | Clean local worktrees/branches only after confirming no uncommitted work | Local branches with plus signs are checked out in other worktrees and cannot be safely deleted blindly. | git worktree list is reviewed; unused worktrees are removed intentionally. |

## Git state

### Latest ROCA commits

```
b6ec1d1 (HEAD -> roca-idare-killtest, origin/roca-idare-killtest) Merge consolidated I-DARE historical evidence into ROCA
660b799 (tag: archive/roca-consolidate-branches-before-delete) Add I-DARE final consolidated ROCA synthesis
a64315d Merge historical I-DARE evidence from origin/idare/wave1/feature-discriminability
3959275 Merge historical I-DARE evidence from origin/idare/wave1/emg-baseline-ablation
aaebd45 Merge historical I-DARE evidence from origin/idare/wave1/eeg-subject-normalization
0293e10 Merge historical I-DARE evidence from origin/idare/wave1/eeg-input-definition
17a171f Merge historical I-DARE evidence from origin/idare/postwave1/strict-ntd-norm-smoke
b0cd753 Merge historical I-DARE evidence from origin/idare/postwave1/representation-redesign-smoke
c44dee6 Merge historical I-DARE evidence from origin/idare/postwave1/representation-redesign-confirmation
10ad9c7 Merge historical I-DARE evidence from origin/idare/postwave1/root-cause-triage
ba067e0 Merge historical I-DARE evidence from origin/idare/postwave1/label-task-protocol-reconciliation
fe1e58e Merge historical I-DARE evidence from origin/idare/postwave1/idare-prior-best-cell-confirmation
```

### Remote branches

```
origin/roca-idare-killtest
  origin/HEAD -> origin/main
  origin/main
```

### Worktrees

```
/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE                             b6ec1d1 [roca-idare-killtest]
/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-control                     e6b021c [idare/control-tower]
/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-data-augmentation           f9728de [idare/postwave1/data-augmentation-track]
/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-idare-prior-best-confirm    2b72f40 [idare/postwave1/idare-prior-best-cell-confirmation]
/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-label-task-protocol         19188db [idare/postwave1/label-task-protocol-reconciliation]
/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-repr-redesign-confirmation  79438a0 [idare/postwave1/representation-redesign-confirmation]
/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-repr-redesign-smoke         2fd7f18 [idare/postwave1/representation-redesign-smoke]
/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage           86b239a [idare/postwave1/root-cause-triage]
/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-strict-ntd-smoke            908dd55 [idare/postwave1/strict-ntd-norm-smoke]
/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-w1a                         195c148 [idare/wave1/eeg-input-definition]
/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-w1b                         91f6573 [idare/wave1/eeg-subject-normalization]
/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-w1c                         5a008c8 [idare/wave1/emg-baseline-ablation]
/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-w1d                         f35d1a2 [idare/wave1/feature-discriminability]
```

## Artifact inventory

Total indexed artifacts/scripts: `1705`

See `_artifact_inventory.csv` for the full index.
