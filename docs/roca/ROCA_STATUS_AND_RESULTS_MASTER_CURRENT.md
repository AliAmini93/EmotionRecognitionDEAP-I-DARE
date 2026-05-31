# ROCA Master Status and Results Report

Generated for branch: `roca-idare-killtest`

Purpose: this file is the human-readable, single-entry status report for the I-DARE EEG/EMG emotion-recognition work on ROCA. It is intentionally a repository-backed report: every conclusion below points to artifacts already committed in this branch. It should be used instead of relying on chat memory.

## 1. Current source of truth

- Current active research branch: `roca-idare-killtest`.
- `main` was accidentally merged with ROCA once and then reverted/restored. It is not the active I-DARE research branch.
- Historical `idare/*` branches were consolidated into ROCA, tagged for archive, and deleted remotely after confirming they were merged.
- The latest ledger state is recorded in:
  - `docs/roca/idare_06c0_final_research_ledger_current.md`
  - `docs/roca/idare_06c0_final_research_ledger_current_decision_table.csv`
  - `docs/roca/idare_06c0_final_research_ledger_current_artifact_inventory.csv`

Decision from the final ledger:

> `ROCA_CURRENT_TRUTH_BRANCH_READY_FOR_RESEARCH_DECISION_PACK`

Scientific state:

> Strict LOSO global raw EEG/EMG residual decoding is not supported by the locked gates. Calibration/personalization is the only partial-positive route observed so far.

## 2. Exhaustive evidence coverage

This master report is not meant to duplicate every row of every CSV. The exhaustive inventory is already committed as:

- `docs/roca/idare_06c0_final_research_ledger_current_artifact_inventory.csv`

That file indexes the committed project artifacts by path, kind, size, row count, and sample. This master report summarizes those artifacts by scientific phase and decision.

Primary ledger files:

| Role | File |
|---|---|
| Final research ledger | `docs/roca/idare_06c0_final_research_ledger_current.md` |
| Exhaustive artifact inventory | `docs/roca/idare_06c0_final_research_ledger_current_artifact_inventory.csv` |
| Phase summary | `docs/roca/idare_06c0_final_research_ledger_current_phase_summary.csv` |
| Key decisions | `docs/roca/idare_06c0_final_research_ledger_current_key_decisions.csv` |
| Remaining actions | `docs/roca/idare_06c0_final_research_ledger_current_remaining_actions.csv` |
| Final root-cause report | `docs/roca/idare_06a7_final_loso_root_cause_report_current.md` |
| Calibration-dominant conclusion | `docs/roca/idare_06a7b_calibration_dominant_conclusion_current.md` |
| Consolidated historical-branch synthesis | `docs/roca/idare_06b3_final_consolidated_roca_synthesis_current.md` |

## 3. Phase-by-phase project state

| Phase | Status | What was done | Result |
|---|---:|---|---|
| Git / branch consolidation | Complete | ROCA remained the active truth branch; historical `idare/*` branches were merged into ROCA as historical evidence and archived/deleted remotely. | Historical branches did not overturn the locked-gate ROCA conclusion. |
| Label/task/baseline protocol | Complete | Stimulus-only baselines, label/task reconciliation, prior baseline checks, and protocol audits were generated. | The project-specific protocol confirmed that LOSO is hard and that stimulus/subject effects are strong. |
| EMG-only route | Complete negative | EMG-only, expanded EMG, nonlinear EMG, and augmented EMG probes were run. | EMG alone did not rescue strict LOSO residual emotion recognition. |
| EEG raw/deep route | Complete negative | Raw EEG residual learning, stabilized residual training, multitask/sign auxiliary learning, oracle diagnostics, architecture/input audits, and neural anchor tests were run. | Raw EEG neural capacity/augmentation did not produce a locked-gate global LOSO solution. |
| EEG/EMG augmentation route | Complete negative under locked gate | Gaussian/noise augmentation looked promising in older non-comparable/oracle reports, then was rerun under locked current gate. | Clean locked rerun showed Gaussian augmentation does not fix LOSO. |
| Representation / normalization / DG historical routes | Merged as evidence | Strict non-transductive normalization, representation redesign smoke/confirmation, and early Wave 1 checks were consolidated. | Useful historical evidence, but not enough to reverse the final locked-gate conclusion. |
| Calibration / personalization | Partial positive, claim shift required | k-shot/subject bias calibration and personalization bridge analyses were run. | Calibration helped more than blind global modeling, but the claim changes from pure zero-calibration LOSO to calibrated/personalized/adaptation-assisted recognition. |
| Final scientific conclusion | Locked current conclusion | 06a7, 06a7b, 06b3, and 06c0 syntheses were created. | The dominant issue is subject calibration/domain shift plus weak transferable residual identifiability. |

## 4. Key locked-gate decisions

| Question | Evidence file | Decision | Interpretation |
|---|---|---|---|
| Does generic Gaussian augmentation fix LOSO? | `docs/roca/idare_06a5b_gaussian10_locked_gate_rerun_current_decision_table.csv` | `NO_GO_AUGMENTATION_DOES_NOT_FIX_LOSO` | Under the clean locked gate, Gaussian augmentation was worse than the no-augmentation control on the high-disagreement residual target. |
| Does a raw EEG neural anchor beat practical gates? | `docs/roca/idare_06a6_neural_anchor_fixed_bandpower_current_decision_table.csv` | `NO_GO_NEURAL_PIPELINE_NOT_ANCHORED` | Raw neural EEG did not beat zero/fixed/locked bridge references; Gaussian augmentation again did not help. |
| Does k-shot/subject calibration help? | `docs/roca/idare_06a4b_kshot_calibration_locked_bridge_confirm_current_decision_table.csv` | `PARTIAL_GO_CALIBRATION_BEATS_FIXED_BUT_NOT_LOCKED_B2` | Calibration helps, but it does not beat the locked B2 personalization bridge and changes the claim away from pure zero-calibration LOSO. |
| Do historical branches change the conclusion? | `docs/roca/idare_06b3_final_consolidated_roca_synthesis_current_decision_table.csv` | `NO` | Historical branches are useful evidence, but they do not overturn the final ROCA locked-gate conclusion. |
| What is the final root cause? | `docs/roca/idare_06a7_final_loso_root_cause_report_current_decision_table.csv` | `FINAL_CALIBRATION_DOMINANT_NEGATIVE_RESULT_FOR_GLOBAL_RAW_EEG_RESIDUAL_DECODING` | The current residual target is calibration-dominant: subject domain shift and weak transferable residual identifiability dominate. |
| What is the current project state? | `docs/roca/idare_06c0_final_research_ledger_current_decision_table.csv` | `ROCA_CURRENT_TRUTH_BRANCH_READY_FOR_RESEARCH_DECISION_PACK` | ROCA is ready for a research decision pack, not for another broad blind model search. |

## 5. What has effectively been ruled out as the primary fix

The following directions have been tested enough under this project protocol that they should not be repeated blindly:

1. **Pure global strict-LOSO raw EEG residual decoding** as the main positive claim.
2. **EMG-only rescue** under the current residual target.
3. **Generic Gaussian/noise augmentation** as a fix for LOSO.
4. **Unanchored larger CNN/raw neural capacity search**.
5. **Repeating historical representation/normalization branches as if they are current positive evidence**.
6. **Using older oracle/non-comparable results as final proof**.

These can still be cited as historical attempts, ablations, or negative evidence, but not as the main route to a positive claim.

## 6. What partially worked

The partial positive route is calibration/personalization:

- Subject calibration and k-shot/bias correction improved residual behavior compared with blind global models.
- However, the best calibrated/personalized route does not support the same claim as pure zero-calibration LOSO.
- Any future positive result must explicitly state the target-subject information budget: zero-calibration, unlabeled target adaptation, or k-shot labeled calibration.

This is scientifically defensible only if the paper/report is honest about the claim shift.

## 7. Current final scientific statement

A defensible current statement is:

> Under strict LOSO, the current high-disagreement residual emotion-recognition target is calibration-dominant. Global raw EEG/EMG residual decoding is not supported by the locked gates. The dominant failure mode is subject calibration/domain shift plus weak transferable residual identifiability. Calibration/personalization is the only partial-positive direction observed so far, but it must be reported as calibrated/personalized/adaptation-assisted recognition rather than pure zero-calibration LOSO.

## 8. Remaining work

| Priority | Action | Why | Success condition |
|---:|---|---|---|
| 1 | Generate paper/report claim section | Convert the negative and partial-positive evidence into a defensible scientific narrative. | The text separates pure LOSO failure from calibrated/personalized positive direction. |
| 2 | Choose exactly one next positive route | Avoid another broad architecture-search month. | Route is either calibration-budget, UDA with unlabeled target data, or explicitly personalized EEG+EMG fusion. |
| 3 | Define allowed target-subject information budget | Calibration/adaptation claims need a clear protocol. | A table states zero-calibration, unlabeled-target, and k-shot labeled-target settings separately. |
| 4 | Run only one small confirmatory experiment if a positive claim is required | Current evidence already rules out blind raw EEG/EMG LOSO search. | The experiment is gated against locked B2/personalization references and has a stop rule. |
| 5 | Clean local worktrees/branches only after confirming no uncommitted work | Local worktrees may still hold checked-out old branches. | `git worktree list` is reviewed; unused worktrees are removed intentionally. |

## 9. Recommended next decision

The next project decision should not be "try ten more methods." It should be one of these:

1. **Write the result as a calibration-dominant negative/partial-positive finding.**
2. **If a positive model is required, choose exactly one calibrated/adaptation-assisted protocol and run one pre-gated confirmatory experiment.**
3. **Do not continue blind global raw EEG/EMG LOSO architecture or augmentation search unless the target formulation is changed.**

## 10. Maintenance rule for this file

When a new ROCA experiment is committed, update this file or regenerate a newer `ROCA_STATUS_AND_RESULTS_MASTER_*` report. The update must cite committed artifacts, not chat memory.
