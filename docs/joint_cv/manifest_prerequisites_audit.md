# Manifest Prerequisites Audit

Read-only audit; no training or fold construction was performed.

## Git Context

- Repository: `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE`
- Branch: `joint-cv-capacity-audit`
- HEAD: `78946cb168b5839dac88703ddfcad584137a046f`
- Working tree clean before audit: `False`

## DEAP Prerequisites

- Subject files: `32`
- Sample pickle: `/mnt/HDD/AliWorks/DEAP/data_preprocessed_python/s01.dat`
- Sample keys: `['data', 'labels']`
- Data shape: `[40, 40, 8064]`
- Labels shape: `[40, 4]`
- Nonstandard keys: `[]`
- Metadata candidates: `0`
- Repository mapping hits: `38`
- Stimulus-identity status: **needs_manual_review**

Repository text mentions a DEAP stimulus/video/order mapping. The referenced source must be located and verified.

### DEAP Metadata Candidates

_No rows._

### Repository Mentions Potentially Related to DEAP Mapping

| relative_path | pattern_id | size_bytes | snippet |
| --- | --- | --- | --- |
| README.md | 1 | 9825 | US_LABEL_POLICY_NOTE_END --> ### Windowing فعلی **Main protocol:** \| Dataset \| Windowing \| \|---------\|-----------\| \| DEAP \| `60s trial → 12 windows × 5s` \| \| I-DARE \| `5s stimulus block → 1 window` \| - Overlap در main protocol استفاده نمی‌شود. **Ablation بعدی:** - `4s / 5s / 6s` window - در صورت نیاز، `50%` overlap فقط به‌عنوان ablation --- ## 4. مسیر کلی آزمایش‌ها ### Phase 0 — Data Protoco |
| docs/chat_handoff_latest.md | 1 | 9970 | rule: ```text label = 1 if score > 5 label = 0 if score < 5 score == 5 is discarded for that task ``` ### Windowing DEAP: ```text 60s trial -> 12 non-overlapping 5s windows ``` I-DARE: ```text one natural 5s STIM window per emotional stimulus ``` ### EMG - Main EMG path is feature-level, not raw waveform. - Raw EMG may be considered later as an ablation. ### Fusion Fusion location remains an experimental question: ```text 1. segment-level EEG-EMG fusion |
| docs/dataset_acquisition_plan.md | 1 | 13921 | ping 5-second windows ``` At 128Hz: ```text 5 seconds = 640 samples 12 windows = 7680 samples ``` Important detail: DEAP preprocessed data has 8064 samples per trial. The audit must verify how these samples correspond to baseline/stimulus duration in the selected official preprocessed archive. The implementation should not blindly use all 8064 samples as 60 seconds. The audit should explicitly determine: ```text - whether the usable stimulus portion is |
| docs/decision_log.md | 1 | 16449 | rotocol Date: 2026-05-04 Decision: Use 5-second non-overlapping windows as the main segmentation strategy. Reason: - DEAP 60s trials become 12 windows. - I-DARE stimulus blocks are naturally 5s. - Avoids inflated results from overlap in the main protocol. Status: Accepted. --- ## D002 - Keep EMG feature-level in the main model Date: 2026-05-04 Decision: Use window-level EMG feature |
| docs/handoff_bundle_latest.md | 1 | 295409 | tasks: binary valence and binary arousal. - Label rule: label = 1 if score > 5 else 0; score == 5 is discarded. - Main DEAP windowing: 60s trial -> 12 non-overlapping 5s windows. - Main I-DARE windowing: one natural 5s stimulus window. - EEG model starts with EEGSegmentClassifier-v1. - EMG will initially be feature-level, not raw waveform. - Fusion location is an experimental question: 1. segment-level EEG-EMG fusion 2. modality-specific s |
| docs/idare_baseline_modeling_literature_plan.md | 1 | 7742 | ning question is whether the model should explicitly see BSL and STIM as paired inputs. ## Dataset contrast: I-DARE vs DEAP \| Dataset \| Stimulus unit \| Baseline structure \| Modeling implication \| \|---\|---\|---\|---\| \| I-DARE \| 32 emotional pictures per subject \| A dedicated black-screen BSL immediately precedes each picture STIM \| Trial-wise paired modeling is mea |
| docs/joint_cv/existing_analysis_inventory.csv | 2 | 369178 | . Artifact was later deleted or reverted from a newer history state.,2026-05-13T19:29:39+03:00,Add ROCA label audit and stimulus-only baseline,A,yes,yes DEAP+I-DARE,docs/roca/local_setup_audit_current.txt,9f1fcae25efc34c18ea06ecab3cfb5fb138be84f,model-or-training-result,smoke-or-partial,unspecified,unspecified,unknown,unknown,no,unknown,context-only,Automated historical inve |
| docs/next_chat_prompt.md | 1 | 6873 | tasks: binary valence and binary arousal. - Label rule: label = 1 if score > 5 else 0; score == 5 is discarded. - Main DEAP windowing: 60s trial -> 12 non-overlapping 5s windows. - Main I-DARE windowing: one natural 5s stimulus window. - EEG model starts with EEGSegmentClassifier-v1. - EMG will initially be feature-level, not raw waveform. - Fusion location is an experimental question: 1. segment-level EEG-EMG fusion 2. modality-specific s |
| docs/proposal_v1_1.md | 1 | 28574 | . Median Frequency ``` Input shape: ```text x_emg_feat: [B, N_emg, F] ``` Default: ```text N_emg = 2 F = 7 ``` For DEAP: ```text 12 windows per trial -> [B, 12, N_emg, 7] ``` For I-DARE: ```text 1 stimulus window -> [B, 1, N_emg, 7] ``` --- ## 6.4 Channel-Shared EMG Encoder To reduce dependence on channel identity, each EMG channel is passed through the same MLP: ```text x_emg_feat: [B, N_emg, 7] shared MLP per chann |
| docs/roca/deap_stimulus_only_loso_current.json | 1 | 5559 | { "protocol": "DEAP stimulus-only LOSO baseline", "deap_dir": "/mnt/HDD/AliWorks/DEAP/data_preprocessed_python", "label_policy": "midpoint_as_low", "subjects": 32, "stimuli": 40, "trials": 1280, "models": [ "global_mean", "stimu |
| docs/roca/deap_stimulus_only_loso_current.md | 1 | 1830 | # DEAP Stimulus-Only LOSO Baseline This report computes a strict cross-subject / LOSO stimulus-only baseline for DEAP. ## Configuration - deap_dir: `/mnt/HDD/AliWorks/DEAP/data_preprocessed_python` - label_policy: `midpoint_as_low` - models: `global_mean`, `stimulus_only` - targets: `valence`, `arousal` - leaka |
| docs/roca/deap_stimulus_only_loso_midpoint_high_current.json | 1 | 5666 | { "protocol": "DEAP stimulus-only LOSO baseline", "deap_dir": "/mnt/HDD/AliWorks/DEAP/data_preprocessed_python", "label_policy": "midpoint_as_high", "subjects": 32, "stimuli": 40, "trials": 1280, "models": [ "global_mean", "stim |
| docs/roca/deap_stimulus_only_loso_midpoint_high_current.md | 1 | 1831 | # DEAP Stimulus-Only LOSO Baseline This report computes a strict cross-subject / LOSO stimulus-only baseline for DEAP. ## Configuration - deap_dir: `/mnt/HDD/AliWorks/DEAP/data_preprocessed_python` - label_policy: `midpoint_as_high` - models: `global_mean`, `stimulus_only` - targets: `valence`, `arousal` - leak |
| docs/roca/idare_06a0_deep_data_and_prior_model_inventory_current.json | 1 | 37949 | rived pseudo-subject IDs, so inventory must separate DEAP raw from project-derived tables." }, { "item": "DEAP trials per participant", "expected": "40 music-video trials", "why_it_matters": "Representation learning should preserve trial identity and avoid stimulus leakage in cross-subject evaluation." }, { "item": "DEAP preprocessed signal shape", "expec |
| docs/roca/idare_06a0_deep_data_and_prior_model_inventory_current.md | 1 | 54181 | ; project outputs may have more rows/subjects if merged or using derived pseudo-subject IDs, so inventory must separate DEAP raw from project-derived tables. \| \| DEAP trials per participant \| 40 music-video trials \| Representation learning should preserve trial identity and avoid stimulus leakage in cross-subject evaluation. \| \| DEAP preprocessed signal shape \| usually 40 trials x 40 channels x 8064 samples per subject fil |
| docs/roca/idare_06a0_deep_data_and_prior_model_inventory_current_expected_deap_spec.csv | 1 | 1280 | ; project outputs may have more rows/subjects if merged or using derived pseudo-subject IDs, so inventory must separate DEAP raw from project-derived tables." DEAP trials per participant,40 music-video trials,Representation learning should preserve trial identity and avoid stimulus leakage in cross-subject evaluation. DEAP preprocessed signal shape,usually 40 trials x 40 channels x 8064 samples per subject file,8064 s |
| docs/roca/idare_06a0_deep_data_and_prior_model_inventory_current_prior_dl_candidates.csv | 1 | 1305601 | TIM \| Trial-wise paired modeling is meaningful: `BSL`, `STIM`, and `STIM-BSL` all have interpretable roles. \| \|\| L25: \| DEAP \| 40 one-minute music videos per subject \| DEAP preprocessed Python contains a short baseline segment before the 60s stimulus signal \| Baseline correction is appropriate, but DEAP is less naturally a paired 5s ...",27 docs/project_status_current.md,99911,0.0953,"deep,conv,temporal,representation,loso,cross-subject,neural","accuracy,acc,rmse,ma |
| docs/roca/idare_06a0b_prior_deep_learning_forensic_review_current.json | 1 | 189175 | "implication": "Representation learning is possible locally, but current EEG window is 640 samples, not the full DEAP 60s stimulus; input policy must be explicit.", "risk": "A model on 5s windows may fail for reasons unrelated to physiology if the useful affect dynamics are outside the window.", "recommended_action": "Before 06a1, verif |
| docs/roca/idare_06a0b_prior_deep_learning_forensic_review_current.md | 1 | 15959 | from 06a0 inventory. \| Representation learning is possible locally, but current EEG window is 640 samples, not the full DEAP 60s stimulus; input policy must be explicit. \| A model on 5s windows may fail for reasons unrelated to physiology if the useful affect dynamics are outside the window. \| Before 06a1, verify cache index alignment and whether 640-samp |
| docs/roca/idare_06a0b_prior_deep_learning_forensic_review_current_candidate_forensics.csv | 1 | 1395482 | TIM \| Trial-wise paired modeling is meaningful: `BSL`, `STIM`, and `STIM-BSL` all have interpretable roles. \| \|\| L25: \| DEAP \| 40 one-minute music videos per subject \| DEAP preprocessed Python contains a short baseline segment before the 60s stimulus signal \| Baseline correction is appropriate, but DEAP is less naturally a paired 5s BSL/STIM design. \| \|\| L37: \| I-DARE dataset paper, Frontiers in Human Neuroscience 2024, DOI `10.3389/fnhum.2024.1347327`, PMC `PMC1098 |
| docs/roca/idare_06a0b_prior_deep_learning_forensic_review_current_decision_table.csv | 1 | 4590 | from 06a0 inventory.","Representation learning is possible locally, but current EEG window is 640 samples, not the full DEAP 60s stimulus; input policy must be explicit.",A model on 5s windows may fail for reasons unrelated to physiology if the useful affect dynamics are outside the window.,"Before 06a1, verify cache index alignment and whether 640-sample |
| docs/roca/idare_06a1b_input_window_policy_audit_current.json | 1 | 486224 | "640 samples at 128 Hz is 5 seconds, which matches the I-DARE 5s stimulus-window policy; it is shorter only relative to DEAP's 60s video stimulus.", "risk_for_06a1": "For I-DARE this is the intended full stimulus window; remaining risk is whether this 5s stimulus contains enough residual-relevant physiology.", "decision": "I_DARE_5S_FULL_STIMULUS_WINDOW_CONFIRMED", "required_before_final_claim": "Document that 640 sa |
| docs/roca/idare_06a1b_input_window_policy_audit_current.md | 1 | 16613 | 640 samples at 128 Hz is 5 seconds, which matches the I-DARE 5s stimulus-window policy; it is shorter only relative to DEAP's 60s video stimulus. \| For I-DARE this is the intended full stimulus window; remaining risk is whether this 5s stimulus contains enough residual-relevant physiology. \| I_DARE_5S_FULL_STIMULUS_WINDOW_CONFIRMED \| Document that 640 samples represent the full 5s I-DARE stimulus after 512Hz-to-128Hz downsampling, with preceding 5s BSL used fo |
| docs/roca/idare_06a1b_input_window_policy_audit_current_decision_table.csv | 1 | 2445 | "640 samples at 128 Hz is 5 seconds, which matches the I-DARE 5s stimulus-window policy; it is shorter only relative to DEAP's 60s video stimulus.",For I-DARE this is the intended full stimulus window; remaining risk is whether this 5s stimulus contains enough residual-relevant physiology.,I_DARE_5S_FULL_STIMULUS_WINDOW_CONFIRMED,"Document that 640 samples represent the full 5s I-DARE stimulus after 512Hz-to-128Hz downsampling, with preceding 5s BSL used for b |
| docs/roca/idare_06a1b_input_window_policy_audit_current_script_usage_audit.csv | 1 | 10538 | uts may have more rows/subjects if merged or using derived pseudo-subject IDs, so inventory must \|\| L347: {""item"": ""DEAP trials per participant"", ""expected"": ""40 music-video trials"", ""why_it_matters"": ""Representation learning should preserve trial identity and avoid stimulus leakage in cross-subject evaluation.""}, \|\| L348: {""item"": ""DEAP preprocessed signal shape"", ""expected"": "" |
| docs/roca/idare_06a1z_prior_experiment_map_and_root_cause_autopsy_current_candidate_experiment_files.csv | 1 | 1372166 | L9: ""implication"": ""Representation learning is possible locally, but current EEG window is 640 samples, not the full DEAP 60s stimulus; input policy must be explicit."", \|\| L14: ""topic"": ""prior_deep_model_scope"", \|\| L15: ""finding"": ""Candidate scripts/logs indicate prior deep experiments were mostly smoke/stabilization/oracle/architecture ablatio |
| docs/roca/idare_06c0_final_research_ledger_current_artifact_inventory.csv | 1 | 209189 | "", ""implication"": ""Representation learning is possible locally, but current EEG window is 640 samples, not the full DEAP 60s stimulus; input policy must be explicit."", ""risk"": ""A model on 5s windows may fail for reasons unrelated to physiology if the useful affect dynamics are outside the window."", ""reco..." docs/roca/idare_06a0b_prior_deep_lear |
| docs/roca/idare_residual_physiology_audit_lock_current.md | 1 | 5433 | odel/architecture optimization is scientifically justified. ## Dataset target Current target dataset: - I-DARE only. DEAP stimulus-only LOSO was used as external sanity/context, not the immediate modeling target. ## Current known stimulus-only problem Stimulus-only prior is strong enough that raw accuracy can be misleading. Therefore future physiological models must be evaluated against: - stimulus-only baseline; - residual prediction over train-subjec |
| docs/roca/prior_baselines_no_global_current.json | 1 | 50630 | "expected_near": 1.9442049821165959, "abs_diff": 0.0, "pass_1e_minus_6": true }, { "name": "DEAP LOSO stimulus-only valence RMSE should match previous DEAP stimulus-only run", "value": 1.5637460592350514, "expected_near": 1.5637460592350514, "abs_diff": 0.0, "pass_1e_minus_6": true }, { "name": "DEAP LOSO stimulus-only arousal RMSE should match |
| docs/roca/prior_baselines_no_global_current.md | 1 | 18104 | # Prior baselines without global baseline This report computes non-global prior baselines for DEAP and I-DARE. ## Protocols - `leave_one_subject_out`: stimulus-only prior, train excludes the test subject. - `leave_one_stimulus_out`: subject-only prior, train excludes the test stimulus. - `leave_one_subject_stimulus_pair_out`: exact leave-one-cell-out additive subject+stimulus |
| docs/roca/prior_baselines_no_global_current_main_metrics.csv | 1 | 4737 | ,mae,rmse,pearson,spearman,ccc,y_true_mean,y_true_std,y_pred_mean,y_pred_std,residual_mean,residual_std,rmse_over_y_std DEAP,arousal,leave_one_stimulus_out,subject_only,"For each held-out stimulus, predict each subject by train-stimulus mean of the same subject.",1280,1.602226762820513,1.9466171605903066,0.27506221341242837,0.21788576125357456,0.16875485798492598,5.1567109375,2.01971007608589,5.1567109375,0.6923700889216955,-3.087807787238717e-17,1.946 |
| scripts/joint_cv/01_audit_manifest_prerequisites.py | 1 | 25008 | standard_keys')) if embedded_key: status = 'needs_manual_review' reason = ( 'The sample DEAP pickle has nonstandard keys that may encode stimulus ' 'identity or trial order; inspect them before constructing a manifest.' ) elif strong_files: status = 'needs_manual_review' reason = ( 'Potential local DEAP stimulus/order metadata files were found. ' |
| scripts/roca/01_deap_stimulus_only_loso.py | 1 | 15842 | gs.out_prefix}_subject_metrics.csv" out_trial = ROCA_DIR / f"{args.out_prefix}_trial_labels.csv" print("[INFO] DEAP stimulus-only LOSO baseline") print(f"[INFO] deap_dir={args.deap_dir}") print(f"[INFO] label_policy={args.label_policy}") trial_df, issues = build_trial_table(args.deap_dir) trial_df.to_csv(out_trial, index=Fals |
| scripts/roca/01c_prior_baselines_no_global.py | 1 | 23279 | ut", "stimulus_only", "rmse"), "expected_near": 1.9442049821165959, }) checks.append({ "name": "DEAP LOSO stimulus-only valence RMSE should match previous DEAP stimulus-only run", "value": pick("DEAP", "valence", "leave_one_subject_out", "stimulus_only", "rmse"), "expected_near": 1.5637460592350514, }) checks.append({ "name": "DEAP LOSO stimulus-only aro |
| scripts/roca/06a0_idare_deep_data_and_prior_model_inventory.py | 1 | 23746 | ; project outputs may have more rows/subjects if merged or using derived pseudo-subject IDs, so inventory must separate DEAP raw from project-derived tables."}, {"item": "DEAP trials per participant", "expected": "40 music-video trials", "why_it_matters": "Representation learning should preserve trial identity and avoid stimulus leakage in cross-subject evaluation."}, {"item": "DEAP preprocessed signal shape", "expected": "usually 40 tr |
| scripts/roca/06a0b_idare_prior_deep_learning_forensic_review.py | 1 | 22292 | "implication": "Representation learning is possible locally, but current EEG window is 640 samples, not the full DEAP 60s stimulus; input policy must be explicit.", "risk": "A model on 5s windows may fail for reasons unrelated to physiology if the useful affect dynamics are outside the window.", "recommended_action": "Before 06a1, v |
| scripts/roca/06a1b_idare_input_window_policy_audit.py | 1 | 21582 | "640 samples at 128 Hz is 5 seconds, which matches the I-DARE 5s stimulus-window policy; it is shorter only relative to DEAP's 60s video stimulus.", "risk_for_06a1": "For I-DARE this is the intended full stimulus window; remaining risk is whether this 5s stimulus contains enough residual-relevant physiology.", "decision": "I_DARE_5S_FULL_STIMULUS_WINDOW_CONFIRMED", "required_before_final_claim": "Document |
| working_proposal_v1_1.md | 1 | 17257 | score > 5 else 0 score == 5 -> discard ``` The midpoint score is discarded to reduce label noise. ### Windowing #### DEAP ```text 60s trial -> 12 windows × 5s stride = 5s overlap = 0 in the main protocol ``` #### I-DARE ```text 5s stimulus block -> 1 window ``` If event structure allows it, internal subwindows may be explored later. However, the main sequence-modeling claim is made on DEAP, not I-DARE. ### Normalization - Normalization statistics must |

## I-DARE Prerequisites

- Trial index: `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE/.cache/idare_trial_index.csv`
- Ready: `True`
- Rows: `2016`
- Subjects: `63`
- Stimuli: `32`
- Trials per subject: `32..32`
- Duplicate subject-stimulus rows: `0`
- Subject stimulus-set mismatches: `0`
- Missing EEG paths: `0`
- Missing EMG paths: `0`
- Duplicate chronology rows: `0`

### I-DARE Blocking Reasons

- None.

### I-DARE Subject Preview

| subject_id | trial_count | unique_stimuli | event_index_min | event_index_max | duplicate_event_indices | missing_eeg_paths | missing_emg_paths |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 32 | 32 | 5 | 98 | 0 | 0 | 0 |
| 10 | 32 | 32 | 5 | 98 | 0 | 0 | 0 |
| 11 | 32 | 32 | 5 | 98 | 0 | 0 | 0 |
| 12 | 32 | 32 | 5 | 98 | 0 | 0 | 0 |
| 13 | 32 | 32 | 5 | 98 | 0 | 0 | 0 |
| 14 | 32 | 32 | 5 | 98 | 0 | 0 | 0 |
| 15 | 32 | 32 | 5 | 98 | 0 | 0 | 0 |
| 16 | 32 | 32 | 5 | 98 | 0 | 0 | 0 |
| 17 | 32 | 32 | 5 | 98 | 0 | 0 | 0 |
| 18 | 32 | 32 | 5 | 98 | 0 | 0 | 0 |
| 19 | 32 | 32 | 5 | 98 | 0 | 0 | 0 |
| 2 | 32 | 32 | 5 | 98 | 0 | 0 | 0 |
| 20 | 32 | 32 | 5 | 98 | 0 | 0 | 0 |
| 21 | 32 | 32 | 5 | 98 | 0 | 0 | 0 |
| 22 | 32 | 32 | 5 | 98 | 0 | 0 | 0 |
| 23 | 32 | 32 | 5 | 98 | 0 | 0 | 0 |
| 24 | 32 | 32 | 5 | 98 | 0 | 0 | 0 |
| 25 | 32 | 32 | 5 | 98 | 0 | 0 | 0 |
| 26 | 32 | 32 | 5 | 98 | 0 | 0 | 0 |
| 27 | 32 | 32 | 5 | 98 | 0 | 0 | 0 |

## Decision

- Safe to build I-DARE canonical physical-trial manifest: `True`
- Safe to claim DEAP stimulus-aware physical-trial manifest: `True`
- Safe to proceed directly to Joint-CV fold construction: `True`
