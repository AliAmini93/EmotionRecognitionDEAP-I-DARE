# Current Project Status / Roadmap Index

## Status

This is the central project status index for the current smoke/stabilization phase.

It summarizes the latest frozen documentation and explicitly separates smoke evidence from final LOSO claims.

## Scope

- Project: cross-subject EEG/EMG emotion recognition on DEAP and I-DARE.
- Current evidence level: smoke/stabilization, not final performance.
- Current discipline: cache-backed runs, subject-held-out validation first, status docs frozen before moving to the next phase.
- Operating conventions: `docs/project_operating_protocol.md`
- Research scope/objectives: `docs/research_scope_and_objectives.md`
- Smoke/evaluation protocol: `docs/smoke_and_evaluation_protocol.md`

## Proposal Alignment

- The proposal's macro goal is to test whether EMG can add value to EEG in cross-subject emotion recognition.
- The current work is aligned with that goal because EEG-only, EMG-only, raw-vs-feature, and BSL-aware ablations are being isolated before fusion.
- I-DARE is treated as a trial-aware BSL/STIM dataset; therefore `STIM-BSL` and compact `BSL stats` are valid I-DARE-aware ablations.
- DEAP and I-DARE are not forced into identical architectures when the dataset structure differs.

## Label Policy Status

The original README proposal used `score > 5` with `score == 5` discarded. That was an initial harmonization assumption, not a final locked decision.

Current smoke runs mostly use `midpoint_as_high` because it preserves all trials and stabilizes early smoke comparisons. However, this is **not final**.

Label policy has now been tested in a controlled 144-run I-DARE ablation and reviewed.

Best smoke-level policies were mixed by modality/task:

- EEG valence: `discard_midpoint`
- EEG arousal: `midpoint_as_high`
- EMG valence: `midpoint_as_high`
- EMG arousal: `discard_midpoint`

No final global label policy is locked. `midpoint_as_high` remains only the practical continuity/default smoke policy, not a final paper policy.

## Phase Roadmap

| Area | Current state | Frozen? | Evidence | Next allowed step | Intentionally not started |
|---|---|---|---|---|---|
| Research scope / smoke-evaluation protocol | current governance docs added | yes | `docs/research_scope_and_objectives.md`<br>`docs/smoke_and_evaluation_protocol.md` | Use these before launching new objectives or ablations. | Treating planned ablations as permission to run all of them immediately. |
| DEAP modality audit / EMG feature path | completed enough for EMG feature-only smoke | yes | `docs/deap_emg_feature_only_status.md` | Broader DEAP EMG evaluation or align DEAP EEG path before fusion. | Final LOSO claim; raw EMG waveform mainline. |
| I-DARE EMG feature-only | cache-backed and smoke-tested for valence/arousal | yes | `docs/idare_emg_feature_only_status.md` | Use as main EMG representation unless a controlled ablation beats it. | Fusion claim; final LOSO claim. |
| I-DARE raw EMG-only | raw waveform cache and raw EMG-only smokes completed | yes | `docs/idare_raw_emg_only_status.md`<br>`docs/idare_emg_raw_vs_feature_smoke_comparison.md` | Keep as ablation; feature-level EMG remains mainline. | Raw EMG as mainline. |
| I-DARE EEG STIM-BSL-only standardized baseline | baseline-corrected STIM-BSL-only EEG comparator smoke-tested for valence/arousal with sidecar-compatible folds | yes | `docs/idare_eeg_stim_bsl_only_standardized_status.md` | Compare directly against EEG BSL-stats sidecar before changing the mainline. | EEG+EMG fusion; full paired BSL/STIM neural model. |
| I-DARE EEG BSL-stats ablation | response cache plus compact BSL stats sidecar smoke-tested for valence/arousal | yes | `docs/idare_eeg_bsl_stats_ablation_status.md` | Compare directly against STIM-BSL-only EEG before changing the mainline. | EEG+EMG fusion; full paired BSL/STIM neural model. |
| I-DARE EMG BSL-stats ablation | feature cache plus compact BSL stats sidecar smoke-tested for valence/arousal | yes | `docs/idare_emg_bsl_stats_ablation_status.md` | Compare directly against STIM-BSL-only EMG feature baseline before changing the mainline. | EEG+EMG fusion; full paired BSL/STIM neural model. |
| I-DARE single-modality BSL-stats vs baseline comparison | direct EEG/EMG BSL-stats sidecar vs baseline comparison documented | yes | `docs/idare_single_modality_bsl_stats_vs_baseline_comparison.md` | Human review before any broader standardized evaluation or fusion decision. | EEG+EMG fusion; full paired BSL/STIM neural model; final LOSO claim. |
| I-DARE single-modality BSL-stats vs baseline review | human review accepted comparison; mainlines unchanged | yes | `docs/idare_single_modality_bsl_stats_vs_baseline_review_status.md` | Stop here, handoff, or plan broader standardized single-modality evaluation only by explicit objective. | EEG+EMG fusion; full paired BSL/STIM neural model; final LOSO claim. |
| I-DARE broader standardized single-modality evaluation plan | planning only; no experiment authorized | yes | `docs/idare_broader_standardized_single_modality_evaluation_plan.md` | Review plan before creating any execution objective. | EEG+EMG fusion; full paired BSL/STIM neural model; final LOSO claim. |
| I-DARE broader standardized single-modality evaluation execution spec | run matrix specified; planning only; no experiment authorized | yes | `docs/idare_broader_standardized_single_modality_evaluation_execution_spec.md` | Review spec before creating an execution objective. | EEG+EMG fusion; full paired BSL/STIM neural model; final LOSO claim. |
| I-DARE broader standardized single-modality evaluation objective | short-term execution objective created for 96-run primary matrix | yes | `docs/idare_broader_standardized_single_modality_evaluation_objective.md` | Prepare execution commands or limited script patches; review before running. | EEG+EMG fusion; full paired BSL/STIM neural model; final LOSO claim. |
| I-DARE broader standardized single-modality evaluation primary report | 96-run primary matrix completed; combined report generated; pending human review | yes | `docs/idare_broader_standardized_single_modality_evaluation_report.md` | Human review / closeout decision before any mainline change or future objective. | EEG+EMG fusion; full paired BSL/STIM neural model; final LOSO claim. |
| I-DARE broader standardized single-modality evaluation review | human review accepted 96-run primary matrix; mainlines unchanged | yes | `docs/idare_broader_standardized_single_modality_evaluation_review_status.md` | Stop here, hand off, or create explicit future follow-up objective. | EEG+EMG fusion; full paired BSL/STIM neural model; final LOSO claim. |
| I-DARE controlled failure analysis objective | short-term post-hoc analysis objective created; no new training authorized | yes | `docs/idare_failure_analysis_objective.md` | Prepare read-only analysis script/command for existing JSON/CSV outputs. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; final label-policy lock. |
| I-DARE controlled failure analysis report | post-hoc failure analysis complete from existing outputs; pending human review | yes | `docs/idare_failure_analysis_report.md` | Human review / closeout before choosing calibration, fold-difficulty, robustness, or model-change objective. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work. |
| I-DARE failure analysis review | human review accepted failure-analysis report; root-cause diagnosis selected as next step | yes | `docs/idare_failure_analysis_review_status.md` | Create root-cause diagnostic objective and read-only report. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work. |
| I-DARE root-cause diagnostic objective | short-term objective created to localize likely causes of near-chance/mixed results; no new performance training authorized | yes | `docs/idare_root_cause_diagnostic_objective.md` | Prepare read-only root-cause diagnostic report from existing predictions. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; diagnostic sanity tests before report review. |
| I-DARE root-cause diagnostic report | read-only diagnostic report complete from existing predictions; pending human review | yes | `docs/idare_root_cause_diagnostic_report.md` | Human review / closeout before diagnostic sanity tests or any fix objective. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; new performance training. |
| I-DARE root-cause diagnostic review | human review accepted read-only root-cause report; diagnostic sanity tests selected next | yes | `docs/idare_root_cause_diagnostic_review_status.md` | Create/run diagnostic sanity tests objective. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; mainline change. |
| I-DARE diagnostic sanity tests objective | short-term diagnostic-only objective created; no performance training claim authorized | yes | `docs/idare_diagnostic_sanity_tests_objective.md` | Prepare reviewed diagnostic sanity command/script. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; broad hyperparameter search. |
| I-DARE diagnostic sanity tests report | diagnostic sanity tests complete; pending human review | yes | `docs/idare_diagnostic_sanity_tests_report.md` | Human review / closeout before the next diagnostic or fix objective. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; broad hyperparameter search. |
| I-DARE diagnostic sanity tests review | human review accepted sanity tests; calibration and subject-generalization selected next | yes | `docs/idare_diagnostic_sanity_tests_review_status.md` | Create/run calibration and subject-generalization diagnostic objective. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; mainline change. |
| I-DARE calibration and subject-generalization objective | short-term diagnostic objective created; no new performance training authorized | yes | `docs/idare_calibration_and_subject_generalization_objective.md` | Prepare reviewed read-only analysis command/script. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; broad hyperparameter search. |
| I-DARE calibration and subject-generalization report | read-only diagnostic report complete; pending human review | yes | `docs/idare_calibration_subject_generalization_report.md` | Human review / closeout before the next diagnostic or fix objective. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; broad hyperparameter search. |
| I-DARE calibration and subject-generalization review | human review accepted calibration-subject diagnostic; calibration protocol selected next | yes | `docs/idare_calibration_subject_generalization_review_status.md` | Create/run calibration protocol objective. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; mainline change. |
| I-DARE calibration protocol objective | short-term validation-only calibration protocol objective created; no new model training authorized | yes | `docs/idare_calibration_protocol_objective.md` | Prepare reviewed read-only calibration protocol analysis command/script. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; broad hyperparameter search. |
| I-DARE calibration protocol report | validation-only calibration protocol analysis complete; pending human review | yes | `docs/idare_calibration_protocol_report.md` | Human review / closeout before the next diagnostic or fix objective. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; broad hyperparameter search. |
| I-DARE calibration protocol review | human review accepted calibration protocol report; calibration rejected as primary fix | yes | `docs/idare_calibration_protocol_review_status.md` | Create/run representation and label-task redesign objective. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; mainline change. |
| I-DARE representation and label-task redesign objective | short-term diagnostic/design objective created; no new model training authorized | yes | `docs/idare_representation_label_task_redesign_objective.md` | Prepare reviewed read-only representation/label-task diagnostic command/script. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; broad hyperparameter search. |
| I-DARE representation and label-task redesign report | read-only representation/label-task diagnostic complete; pending human review | yes | `docs/idare_representation_label_task_redesign_report.md` | Human review / closeout before the selected next objective. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; broad hyperparameter search. |
| I-DARE representation and label-task redesign review | human review accepted blocker diagnosis; subject-relative task formulation selected next | yes | `docs/idare_representation_label_task_redesign_review_status.md` | Create/run subject-relative task formulation objective. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; mainline change. |
| I-DARE subject-relative task formulation objective | short-term diagnostic/design objective created; no new model training authorized | yes | `docs/idare_subject_relative_task_formulation_objective.md` | Prepare reviewed read-only subject-relative task formulation command/script. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; broad hyperparameter search. |
| I-DARE subject-relative task formulation report | read-only subject-relative formulation audit complete; pending human review | yes | `docs/idare_subject_relative_task_formulation_report.md` | Human review / closeout before any minimal controlled training objective. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; broad hyperparameter search. |
| I-DARE subject-relative task formulation review | human review accepted subject-relative formulation; minimal diagnostic training selected next | yes | `docs/idare_subject_relative_task_formulation_review_status.md` | Create/run minimal subject-relative training objective. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; mainline change. |
| I-DARE minimal subject-relative training objective | short-term 24-run diagnostic training objective created | yes | `docs/idare_minimal_subject_relative_training_objective.md` | Prepare reviewed implementation/run command for first-pass 24-run matrix. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; broad hyperparameter search. |
| I-DARE minimal subject-relative training report | 24-run first-pass subject-relative diagnostic training complete; pending human review | yes | `docs/idare_subject_relative_minimal_training_report.md` | Human review / closeout before optional second pass or next fix objective. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; broad hyperparameter search; mainline change. |
| I-DARE subject-relative minimal training review | human review accepted 24-run first pass; subject-relative q33 not sufficient alone | yes | `docs/idare_subject_relative_minimal_training_review_status.md` | Create/run representation/preprocessing diagnostic objective. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; mainline change. |
| I-DARE subject-relative representation/preprocessing objective | short-term diagnostic/design objective created; no new performance training authorized | yes | `docs/idare_subject_relative_representation_preprocessing_objective.md` | Prepare reviewed read-only representation/preprocessing diagnostic command/script. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; broad hyperparameter search. |
| I-DARE subject-relative representation/preprocessing report | read-only representation/preprocessing diagnostic complete; pending human review | yes | `docs/idare_subject_relative_representation_preprocessing_report.md` | Human review / closeout before selected preprocessing training or feature-engineering objective. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; broad hyperparameter search; mainline change. |
| I-DARE subject-relative representation/preprocessing review | human review accepted preprocessing diagnostic; minimal preprocessed training selected next | yes | `docs/idare_subject_relative_representation_preprocessing_review_status.md` | Create/run minimal subject-relative preprocessed training objective. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; mainline change. |
| I-DARE minimal subject-relative preprocessed training objective | short-term 24-run diagnostic training objective created | yes | `docs/idare_minimal_subject_relative_preprocessed_training_objective.md` | Prepare reviewed implementation/run command for the 24-run first pass. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; broad hyperparameter search. |
| I-DARE minimal subject-relative preprocessed training report | 24-run preprocessed subject-relative diagnostic training complete; pending human review | yes | `docs/idare_subject_relative_preprocessed_minimal_training_report.md` | Human review / closeout before optional second pass or next fix objective. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; broad hyperparameter search; mainline change. |
| I-DARE subject-relative preprocessed minimal training review | human review accepted insufficient intervention; feature-engineering path paused | yes | `docs/idare_subject_relative_preprocessed_minimal_training_review_status.md` | Create/run subject-variability intervention-failure analysis. | EEG+EMG fusion; final LOSO claim; SupCon/DG training; feature-engineering training; mainline change. |
| I-DARE subject-variability intervention-failure analysis objective | short-term read-only objective created to explain why subject-relative preprocessing failed | yes | `docs/idare_subject_variability_intervention_failure_analysis_objective.md` | Prepare reviewed read-only analysis command/script. | EEG+EMG fusion; final LOSO claim; SupCon/DG training; feature-engineering training; mainline change. |
| I-DARE subject-variability intervention-failure analysis report | read-only analysis complete; subject variability remains supported; intervention judged too weak | yes | `docs/idare_subject_variability_intervention_failure_analysis_report.md` | Human review / closeout before SupCon/DG design objective. | EEG+EMG fusion; final LOSO claim; direct SupCon/DG training; feature-engineering training; mainline change. |
| I-DARE subject-variability intervention-failure analysis review | human review accepted intervention-failure report; cautious SupCon/DG design selected next | yes | `docs/idare_subject_variability_intervention_failure_analysis_review_status.md` | Create/run cautious SupCon/DG design objective. | EEG+EMG fusion; final LOSO claim; direct SupCon/DG training; feature-engineering training; mainline change. |
| I-DARE cautious subject-variability SupCon/DG design objective | short-term design objective created; smoke tests and hyperparameter registry required; no training authorized | yes | `docs/idare_subject_variability_supcon_dg_design_objective.md` | Search/read project docs and generate implementation-ready design spec. | EEG+EMG fusion; final LOSO claim; direct SupCon/DG training before spec review; broad hyperparameter search; mainline change. |
| I-DARE subject-variability SupCon/DG design spec | cautious design/spec complete; pending human review; smoke tests required before training | yes | `docs/idare_subject_variability_supcon_dg_design_spec.md` | Human review / closeout before SupCon/DG smoke-test objective. | EEG+EMG fusion; final LOSO claim; direct SupCon/DG training; broad hyperparameter search; mainline change. |
| I-DARE subject-variability SupCon/DG design spec review | human review accepted cautious design for smoke tests only | yes | `docs/idare_subject_variability_supcon_dg_design_spec_review_status.md` | Create/run SupCon/DG smoke-tests objective. | EEG+EMG fusion; final LOSO claim; direct SupCon/DG training; broad hyperparameter search; mainline change. |
| I-DARE subject-variability SupCon/DG smoke-tests objective | short-term smoke-test-only objective created; no full training authorized | yes | `docs/idare_subject_variability_supcon_dg_smoke_tests_objective.md` | Prepare reviewed smoke-test implementation/run command. | EEG+EMG fusion; final LOSO claim; direct SupCon/DG training; broad hyperparameter search; mainline change. |
| I-DARE subject-variability SupCon/DG smoke-tests report | smoke tests complete; pending human review | yes | `docs/idare_subject_variability_supcon_dg_smoke_tests_report.md` | Human review / closeout before minimal first-pass training or smoke-fix objective. | EEG+EMG fusion; final LOSO claim; direct full SupCon/DG training; broad hyperparameter search; mainline change. |
| I-DARE subject-variability SupCon/DG smoke-tests review | human review accepted smoke tests; minimal first-pass training selected next | yes | `docs/idare_subject_variability_supcon_dg_smoke_tests_review_status.md` | Create/run minimal SupCon/DG first-pass objective. | EEG+EMG fusion; final LOSO claim; direct full SupCon/DG training; broad hyperparameter search; mainline change. |
| I-DARE minimal SupCon/DG first-pass training objective | short-term diagnostic training objective created | yes | `docs/idare_minimal_supcon_dg_first_pass_training_objective.md` | Prepare reviewed implementation/run command for minimal first-pass matrix. | EEG+EMG fusion; final LOSO claim; direct full SupCon/DG training; broad hyperparameter search; mainline change. |
| I-DARE minimal SupCon/DG first-pass training report | minimal first-pass SupCon/DG diagnostic training complete; pending human review | yes | `docs/idare_minimal_supcon_dg_first_pass_report.md` | Human review / closeout before second-pass confirmation, targeted ablation, or failure analysis. | EEG+EMG fusion; final LOSO claim; direct full SupCon/DG training; broad hyperparameter search; mainline change. |
| EEG+EMG fusion | not started intentionally | no | `docs/idare_eeg_bsl_stats_ablation_status.md`<br>`docs/idare_emg_bsl_stats_ablation_status.md` | Start only after current baseline/ablation status is indexed and compared cleanly. | All fusion experiments. |
| Full model(BSL, STIM, STIM-BSL) | not started intentionally | no | `docs/idare_baseline_modeling_literature_plan.md` | Only after low-capacity BSL-stats ablation beats STIM-BSL-only baselines consistently. | Two-branch or three-branch full paired neural model. |
| I-DARE controlled label-policy ablation objective | short-term objective created and executed for 144-run label-policy matrix | yes | `docs/idare_label_policy_ablation_objective.md` | Review status is frozen in `docs/idare_label_policy_ablation_review_status.md`. | EEG+EMG fusion; final LOSO claim; locking final label policy before review. |
| I-DARE label-policy ablation primary report | 144-run EEG/EMG mainline label-policy matrix completed; mixed task-specific winners | yes | `docs/idare_label_policy_ablation_report.md` | Reviewed in `docs/idare_label_policy_ablation_review_status.md`. | EEG+EMG fusion; final LOSO claim; locking final global label policy. |
| I-DARE label-policy ablation review | human review accepted 144-run matrix; no final global label policy locked | yes | `docs/idare_label_policy_ablation_review_status.md` | Stop here, hand off, or create explicit label-policy robustness objective. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work. |

## Key Frozen Results Snapshot

These rows summarize the best final macro-F1 row in each available smoke report. They are not final LOSO results.

Note: DEAP EMG feature rows are sourced from the frozen `docs/deap_emg_feature_only_status.md` status document.

| Report | Exists | Best task / recipe | Final macro F1 | Final balanced acc |
|---|---|---|---:|---:|
| DEAP EMG feature valence | present | valence / ce_class_weighted | 0.5394 | 0.5454 |
| DEAP EMG feature arousal | present | arousal / balanced_sampler_ce | 0.4911 | 0.4926 |
| I-DARE EMG feature valence | present | valence / ce_class_weighted | 0.5004 | 0.5083 |
| I-DARE EMG feature arousal | present | arousal / ce_class_weighted | 0.5223 | 0.5319 |
| I-DARE raw EMG valence | present | valence / ce_class_weighted | 0.4863 | 0.5000 |
| I-DARE raw EMG arousal | present | arousal / balanced_sampler_ce | 0.4464 | 0.4969 |
| I-DARE EEG STIM-BSL-only valence | present | valence / ce_class_weighted | 0.5112 | 0.5205 |
| I-DARE EEG STIM-BSL-only arousal | present | arousal / ce_class_weighted | 0.5307 | 0.5323 |
| I-DARE EEG + BSL stats valence | present | valence / ce_class_weighted | 0.4801 | 0.5191 |
| I-DARE EEG + BSL stats arousal | present | arousal / ce_class_weighted | 0.4943 | 0.5344 |
| I-DARE EMG + BSL stats valence | present | valence / ce_class_weighted | 0.5073 | 0.5136 |
| I-DARE EMG + BSL stats arousal | present | arousal / ce_class_weighted | 0.5319 | 0.5344 |

## Cache / Sidecar Build Snapshot

| Build | Exists | Status | Shape | NaN | Inf |
|---|---|---|---|---:|---:|
| DEAP EMG feature cache | yes | PASSED | `[15360, 22]` | NA | NA |
| I-DARE EMG feature cache | yes | PASSED | `[2016, 22]` | NA | NA |
| I-DARE raw EMG cache | yes | PASSED | `[2016, 2, 10000]` | 0 | 0 |
| I-DARE EEG BSL stats sidecar | yes | PASSED | `[2016, 229]` | 0 | 0 |
| I-DARE EMG BSL stats sidecar | yes | PASSED | `[2016, 22]` | 0 | 0 |

## Current Decisions

- Keep I-DARE EMG feature-level representation as the main EMG path for now; raw EMG remains an ablation.
- Keep I-DARE baseline-corrected `STIM-BSL` response as the practical mainline representation before any full paired BSL/STIM model.
- Treat compact BSL-stats sidecars as controlled I-DARE-aware ablations for both EEG and EMG.
- Do not start EEG+EMG fusion until the current EEG/EMG single-modality baselines and BSL-stats ablations are directly compared.
- Do not claim final performance from the smoke reports.
- Human review of the controlled I-DARE label-policy ablation is frozen in `docs/idare_label_policy_ablation_review_status.md`; winners are mixed, no final global label policy is locked, and `midpoint_as_high` remains only the practical continuity/default smoke policy.
- Human review of the broader standardized single-modality evaluation is frozen in `docs/idare_broader_standardized_single_modality_evaluation_review_status.md`; mainlines remain unchanged and fusion is not started.
- The broader standardized single-modality primary matrix is complete in `docs/idare_broader_standardized_single_modality_evaluation_report.md`; next step is human review / closeout, not fusion.
- Broader standardized single-modality evaluation now has an execution objective in `docs/idare_broader_standardized_single_modality_evaluation_objective.md`; only the 96-run primary matrix is in scope, and commands/scripts must be reviewed before running.
- Broader standardized single-modality evaluation now has a planning-only execution spec in `docs/idare_broader_standardized_single_modality_evaluation_execution_spec.md`; no run matrix is authorized yet.
- Broader standardized single-modality evaluation is only planned in `docs/idare_broader_standardized_single_modality_evaluation_plan.md`; no execution is authorized yet.
- Human review of the I-DARE single-modality BSL-stats-vs-baseline comparison is frozen in `docs/idare_single_modality_bsl_stats_vs_baseline_review_status.md`; mainlines are unchanged and fusion is not started.
- Direct I-DARE single-modality comparison is documented in `docs/idare_single_modality_bsl_stats_vs_baseline_comparison.md`; do not start fusion automatically from smoke-level comparison evidence.
 - The standardized I-DARE EEG `STIM-BSL`-only baseline comparator gap is closed by `docs/idare_eeg_stim_bsl_only_standardized_status.md`; comparison against EEG/EMG BSL-stats sidecars is now the next documentation step.

- A controlled I-DARE failure-analysis objective is defined in `docs/idare_failure_analysis_objective.md`; next work is read-only analysis of existing outputs, not new training or fusion.

- Controlled I-DARE failure analysis is complete in `docs/idare_failure_analysis_report.md`; next work is human review/closeout, not new training or fusion.

- Human review of the controlled I-DARE failure-analysis report is frozen in `docs/idare_failure_analysis_review_status.md`; blind training is paused and root-cause diagnosis is the selected next step.

- A controlled I-DARE root-cause diagnostic objective is defined in `docs/idare_root_cause_diagnostic_objective.md`; next work is a read-only diagnostic report from existing predictions, not new training or fusion.

- Controlled I-DARE root-cause diagnostic report is complete in `docs/idare_root_cause_diagnostic_report.md`; next work is human review/closeout, not new training or fusion.

- Human review of the I-DARE root-cause diagnostic report is frozen in `docs/idare_root_cause_diagnostic_review_status.md`; diagnostic sanity tests are selected as the next controlled step.

- A diagnostic-only I-DARE sanity-tests objective is defined in `docs/idare_diagnostic_sanity_tests_objective.md`; next work is a reviewed command/script, not performance training or fusion.

- Diagnostic-only I-DARE sanity tests are complete in `docs/idare_diagnostic_sanity_tests_report.md`; next work is human review/closeout before creating the next objective.

- Human review of the diagnostic sanity tests is frozen in `docs/idare_diagnostic_sanity_tests_review_status.md`; calibration and subject-generalization diagnostics are selected as the next controlled step.

- A calibration and subject-generalization objective is defined in `docs/idare_calibration_and_subject_generalization_objective.md`; next work is read-only analysis from existing outputs.

- Calibration and subject-generalization diagnostics are complete in `docs/idare_calibration_subject_generalization_report.md`; next work is human review/closeout before creating a fix objective.

- Human review of the calibration and subject-generalization report is frozen in `docs/idare_calibration_subject_generalization_review_status.md`; calibration protocol is selected as the next controlled step.

- A validation-only calibration protocol objective is defined in `docs/idare_calibration_protocol_objective.md`; next work is a read-only calibration protocol analysis command/script.

- Validation-only calibration protocol analysis is complete in `docs/idare_calibration_protocol_report.md`; diagnosis is `calibration_not_sufficient_as_primary_fix`, recommended next objective is `representation_label_task_redesign_objective`, and human review is required before any next step.

- Human review of the calibration protocol report is frozen in `docs/idare_calibration_protocol_review_status.md`; calibration is rejected as the primary fix.

- A representation and label-task redesign objective is defined in `docs/idare_representation_label_task_redesign_objective.md`; next work is a read-only diagnostic/design report command/script.

- Representation/label-task diagnostic report is complete in `docs/idare_representation_label_task_redesign_report.md`; diagnosis is `subject_relative_label_task_problem_supported` and recommended next objective is `subject_relative_task_formulation_objective`.

- Human review of the representation/label-task diagnostic is frozen in `docs/idare_representation_label_task_redesign_review_status.md`; subject-relative task formulation is selected next.

- A subject-relative task formulation objective is defined in `docs/idare_subject_relative_task_formulation_objective.md`; next work is a read-only task-formulation report command/script.

- Subject-relative task formulation report is complete in `docs/idare_subject_relative_task_formulation_report.md`; selected candidate is `subject_top_bottom_quantile_q33` and recommended next objective is `minimal_subject_relative_training_objective`.

- Human review of the subject-relative task formulation report is frozen in `docs/idare_subject_relative_task_formulation_review_status.md`; `subject_top_bottom_quantile_q33` is accepted as the first controlled formulation.

- A minimal subject-relative training objective is defined in `docs/idare_minimal_subject_relative_training_objective.md`; next work is a reviewed implementation/run command for the 24-run first-pass matrix.

- Minimal subject-relative first-pass training is complete in `docs/idare_subject_relative_minimal_training_report.md`; recommended next objective is `subject_relative_representation_preprocessing_objective` after human review.

- Human review of the minimal subject-relative training first pass is frozen in `docs/idare_subject_relative_minimal_training_review_status.md`; representation/preprocessing diagnosis is selected next.

- A subject-relative representation/preprocessing objective is defined in `docs/idare_subject_relative_representation_preprocessing_objective.md`; next work is a reviewed read-only diagnostic command/script.

- Subject-relative representation/preprocessing diagnosis is complete in `docs/idare_subject_relative_representation_preprocessing_report.md`; recommended next objective is `minimal_subject_relative_preprocessed_training_objective` after human review.

- Human review of the subject-relative representation/preprocessing diagnostic is frozen in `docs/idare_subject_relative_representation_preprocessing_review_status.md`; minimal subject-relative preprocessed training is selected next.

- A minimal subject-relative preprocessed training objective is defined in `docs/idare_minimal_subject_relative_preprocessed_training_objective.md`; next work is a reviewed implementation/run command for the 24-run first pass.

- Minimal subject-relative preprocessed training is complete in `docs/idare_subject_relative_preprocessed_minimal_training_report.md`; diagnosis is `preprocessed_subject_relative_first_pass_not_sufficient` and next work is human review/closeout.

- Human review of the subject-relative preprocessed minimal training report is frozen in `docs/idare_subject_relative_preprocessed_minimal_training_review_status.md`; the intervention is accepted as insufficient, but this does not invalidate the subject-variability diagnosis.

- A subject-variability intervention-failure analysis objective is defined in `docs/idare_subject_variability_intervention_failure_analysis_objective.md`; next work is read-only analysis explaining why the intervention failed before choosing SupCon/DG, feature engineering, or another fix.

- Subject-variability intervention-failure analysis is complete in `docs/idare_subject_variability_intervention_failure_analysis_report.md`; the failed preprocessing intervention is interpreted as too weak/incomplete, and SupCon/DG is justified only after a design/spec objective.

- Human review of the intervention-failure analysis is frozen in `docs/idare_subject_variability_intervention_failure_analysis_review_status.md`; cautious SupCon/DG design is selected next, but training is not authorized.

- A cautious subject-variability SupCon/DG design objective is defined in `docs/idare_subject_variability_supcon_dg_design_objective.md`; next work is to read existing project SupCon/DG notes and create an implementation-ready design spec with smoke tests and a staged hyperparameter registry.

- Cautious SupCon/DG design spec is complete in `docs/idare_subject_variability_supcon_dg_design_spec.md`; next work is human review/closeout, then smoke tests only—not full training.

- Human review of the cautious SupCon/DG design spec is frozen in `docs/idare_subject_variability_supcon_dg_design_spec_review_status.md`; only smoke tests are authorized next.

- A smoke-test-only SupCon/DG objective is defined in `docs/idare_subject_variability_supcon_dg_smoke_tests_objective.md`; full SupCon/DG training remains blocked until smoke-test review.

- SupCon/DG smoke tests are complete in `docs/idare_subject_variability_supcon_dg_smoke_tests_report.md`; diagnosis is `supcon_dg_smoke_tests_passed_ready_for_minimal_first_pass_objective`, and full training remains blocked until human review.

- Human review of SupCon/DG smoke tests is frozen in `docs/idare_subject_variability_supcon_dg_smoke_tests_review_status.md`; minimal first-pass training is selected, but full training remains blocked.

- A minimal SupCon/DG first-pass training objective is defined in `docs/idare_minimal_supcon_dg_first_pass_training_objective.md`; next work is a reviewed implementation/run command, not broad search.

- Minimal SupCon/DG first-pass diagnostic training is complete in `docs/idare_minimal_supcon_dg_first_pass_report.md`; diagnosis is `minimal_supcon_dg_first_pass_not_sufficient`, and full SupCon/DG training remains blocked pending review.

## Documentation Gap Closed by This File

Before this file, the project had strong per-phase status docs but no central status index. This file is the central map that links the proposal, frozen status documents, smoke reports, and next allowed steps.

## I-DARE SupCon/DG Failure Analysis Objective

- Human review of the minimal SupCon/DG first-pass is frozen in `docs/idare_minimal_supcon_dg_first_pass_review_status.md`.
- A read-only SupCon/DG failure-analysis objective is defined in `docs/idare_supcon_dg_failure_analysis_objective.md`.
- Next work is to prepare a reviewed read-only failure-analysis command/script.
- Blocked until review: direct full SupCon/DG training, broad hyperparameter search, EEG+EMG fusion, final LOSO claim, and mainline change.

## I-DARE SupCon/DG Failure Analysis Report

- Read-only SupCon/DG failure analysis is complete in `docs/idare_supcon_dg_failure_analysis_report.md`.
- Diagnosis: `supcon_dg_first_pass_failed_despite_valid_smokes`.
- Recommended next objective: `targeted_supcon_dg_pair_sampler_objective_ablation_design`.
- Human review is required before any new SupCon/DG training, targeted ablation, broad hyperparameter search, EEG+EMG fusion, final LOSO claim, or mainline change.

## I-DARE SupCon/DG Failure-analysis Review and Targeted Pair/Sampler Objective

Updated: `2026-05-08T10:06:00+00:00`

| Item | Status | Evidence | Next allowed step | Blocked |
|---|---|---|---|---|
| I-DARE SupCon/DG failure-analysis review | human review accepted first-pass failure analysis; targeted pair/sampler design selected | `docs/idare_supcon_dg_failure_analysis_review_status.md` | Create/use targeted SupCon/DG pair/sampler ablation design. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |
| I-DARE targeted SupCon/DG pair-sampler objective ablation design | short-term design objective created; no training authorized | `docs/idare_targeted_supcon_dg_pair_sampler_objective_ablation_design.md` | Prepare reviewed targeted pair/sampler ablation implementation command. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |

- A targeted SupCon/DG pair/sampler ablation design objective is defined in `docs/idare_targeted_supcon_dg_pair_sampler_objective_ablation_design.md`.
- The first-pass failure is interpreted as evidence that the pair/sampler/objective design needs targeted ablation before any full SupCon/DG training.

## I-DARE Targeted SupCon/DG Pair-Sampler Ablation Objective

Updated: `2026-05-08T10:14:18+00:00`

| Item | Status | Evidence | Next allowed step | Blocked |
|---|---|---|---|---|
| I-DARE targeted SupCon/DG pair-sampler design review | human review accepted design; minimal ablation selected | `docs/idare_targeted_supcon_dg_pair_sampler_ablation_design_review_status.md` | Prepare/run guardrailed targeted pair/sampler ablation. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |
| I-DARE targeted SupCon/DG pair-sampler ablation objective | short-term diagnostic ablation objective created; planned rows=120 | `docs/idare_targeted_supcon_dg_pair_sampler_ablation_objective.md` | Prepare/run guardrailed targeted pair/sampler ablation command. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |

- The targeted pair/sampler ablation objective is defined in `docs/idare_targeted_supcon_dg_pair_sampler_ablation_objective.md`.
- The run matrix is fixed in `docs/idare_targeted_supcon_dg_pair_sampler_ablation_run_matrix.csv`; this is not a broad hyperparameter search.

## I-DARE Targeted SupCon/DG Pair-Sampler Ablation Report

Updated: `2026-05-08T10:23:39+00:00`

| Item | Status | Evidence | Next allowed step | Blocked |
|---|---|---|---|---|
| I-DARE targeted SupCon/DG pair-sampler ablation report | complete pending human review; diagnosis=`targeted_pair_sampler_ablation_not_sufficient` | `docs/idare_targeted_supcon_dg_pair_sampler_ablation_report.md` | Human review / closeout before confirmation or failure-analysis objective. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |

- Targeted pair/sampler ablation is complete in `docs/idare_targeted_supcon_dg_pair_sampler_ablation_report.md`.
- Best aggregate candidate is `A5_cross_subject_supcon_vrex`; full training remains blocked pending review.

## I-DARE Targeted SupCon/DG Pair-Sampler Ablation Review and Failure Analysis Objective

Updated: `2026-05-08T10:30:45+00:00`

| Item | Status | Evidence | Next allowed step | Blocked |
|---|---|---|---|---|
| I-DARE targeted SupCon/DG pair-sampler ablation review | human review accepted insufficient ablation; failure analysis selected | `docs/idare_targeted_supcon_dg_pair_sampler_ablation_review_status.md` | Create/run pair-sampler failure-analysis objective. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |
| I-DARE SupCon/DG pair-sampler failure analysis objective | read-only objective created; no training authorized | `docs/idare_supcon_dg_pair_sampler_failure_analysis_objective.md` | Prepare reviewed read-only failure-analysis command. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |

- Human review of the targeted pair/sampler ablation is frozen in `docs/idare_targeted_supcon_dg_pair_sampler_ablation_review_status.md`.
- A read-only SupCon/DG pair-sampler failure-analysis objective is defined in `docs/idare_supcon_dg_pair_sampler_failure_analysis_objective.md`.

## I-DARE SupCon/DG Pair-Sampler Failure Analysis Report

Updated: `2026-05-08T10:40:16+00:00`

| Item | Status | Evidence | Next allowed step | Blocked |
|---|---|---|---|---|
| I-DARE SupCon/DG pair-sampler failure analysis report | complete pending human review; diagnosis=`pair_sampler_valid_but_not_primary_failure_mode` | `docs/idare_supcon_dg_pair_sampler_failure_analysis_report.md` | Human review / closeout before next objective. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |

- Read-only pair-sampler failure analysis is complete in `docs/idare_supcon_dg_pair_sampler_failure_analysis_report.md`.
- Recommended next objective is `representation_or_label_semantics_failure_analysis_objective` only after review/closeout.

## I-DARE SupCon/DG Pair-Sampler Failure Review and Representation/Label-Semantics Objective

Updated: `2026-05-08T10:44:24+00:00`

| Item | Status | Evidence | Next allowed step | Blocked |
|---|---|---|---|---|
| I-DARE SupCon/DG pair-sampler failure analysis review | human review accepted; diagnosis=`pair_sampler_valid_but_not_primary_failure_mode` | `docs/idare_supcon_dg_pair_sampler_failure_analysis_review_status.md` | Create/use representation or label-semantics failure-analysis objective. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |
| I-DARE representation or label-semantics failure-analysis objective | read-only objective created; no training authorized | `docs/idare_representation_or_label_semantics_failure_analysis_objective.md` | Prepare reviewed read-only analysis command/script. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |

- Human review of the pair-sampler failure analysis is frozen in `docs/idare_supcon_dg_pair_sampler_failure_analysis_review_status.md`.
- A read-only representation or label-semantics failure-analysis objective is defined in `docs/idare_representation_or_label_semantics_failure_analysis_objective.md`.
- The next allowed step is to prepare the analysis command/script; new training remains blocked.

## I-DARE Representation or Label-Semantics Failure Analysis Report

Updated: `2026-05-08T10:53:45+00:00`

| Item | Status | Evidence | Next allowed step | Blocked |
|---|---|---|---|---|
| I-DARE representation or label-semantics failure-analysis report | complete pending human review; diagnosis=`label_semantics_and_representation_transfer_joint_bottleneck` | `docs/idare_representation_or_label_semantics_failure_analysis_report.md` | Human review / closeout before next objective. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |

- Read-only representation or label-semantics failure analysis is complete in `docs/idare_representation_or_label_semantics_failure_analysis_report.md`.
- Recommended next objective is `label_semantics_task_redesign_or_stop_objective` only after human review/closeout.

## I-DARE Representation/Label-Semantics Review and Task-Redesign-or-Stop Objective

Updated: `2026-05-08T10:59:14+00:00`

| Item | Status | Evidence | Next allowed step | Blocked |
|---|---|---|---|---|
| I-DARE representation or label-semantics failure-analysis review | human review accepted; diagnosis=`label_semantics_and_representation_transfer_joint_bottleneck` | `docs/idare_representation_or_label_semantics_failure_analysis_review_status.md` | Create/use label-semantics task-redesign-or-stop objective. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |
| I-DARE label-semantics task-redesign-or-stop objective | read-only decision-analysis objective created; no training authorized | `docs/idare_label_semantics_task_redesign_or_stop_objective.md` | Prepare reviewed read-only report command/script. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |

- Human review of the representation/label-semantics failure analysis is frozen in `docs/idare_representation_or_label_semantics_failure_analysis_review_status.md`.
- A label-semantics task-redesign-or-stop objective is defined in `docs/idare_label_semantics_task_redesign_or_stop_objective.md`.

## I-DARE Label-Semantics Task-Redesign-or-Stop Report

Updated: `2026-05-08T11:06:28+00:00`

| Item | Status | Evidence | Next allowed step | Blocked |
|---|---|---|---|---|
| I-DARE label-semantics task-redesign-or-stop report | complete pending human review; diagnosis=`current_global_binary_loso_task_not_defensible_for_more_model_search` | `docs/idare_label_semantics_task_redesign_or_stop_report.md` | Human review / closeout before task redesign spec or stop/archive. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |

- Recommended next objective is `label_semantics_task_redesign_spec_objective` only after human review/closeout.
- Stop/archive is explicitly allowed if no defensible task redesign spec is accepted.

## I-DARE Label-Semantics Task-Redesign Spec Objective

Updated: `2026-05-08T11:10:33+00:00`

| Item | Status | Evidence | Next allowed step | Blocked |
|---|---|---|---|---|
| I-DARE label-semantics task-redesign-or-stop report review | human review accepted; diagnosis=`current_global_binary_loso_task_not_defensible_for_more_model_search` | `docs/idare_label_semantics_task_redesign_or_stop_report_review_status.md` | Create/use label-semantics task-redesign spec objective. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |
| I-DARE label-semantics task-redesign spec objective | design/spec objective created; no training authorized | `docs/idare_label_semantics_task_redesign_spec_objective.md` | Prepare reviewed task-redesign spec command/script. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |

- A label-semantics task-redesign spec objective is defined in `docs/idare_label_semantics_task_redesign_spec_objective.md`.
- Training remains blocked until this design/spec is reviewed.

## I-DARE Label-Semantics Task Redesign Spec

Updated: `2026-05-08T11:15:29+00:00`

| Item | Status | Evidence | Next allowed step | Blocked |
|---|---|---|---|---|
| I-DARE label-semantics task redesign spec | complete pending human review; selected=`subject_relative_ordinal_affect_regression_v1` | `docs/idare_label_semantics_task_redesign_spec.md` | Human review / closeout before redesigned-task smoke tests. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |

- Selected primary formulation: `subject_relative_ordinal_affect_regression_v1`.
- Recommended next objective is `label_semantics_redesigned_task_smoke_tests_objective` only after human review/closeout.
- No training is authorized by this spec.

