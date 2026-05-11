# I-DARE Wave 0 Parallel Launch Pack Report

## Status

Status: complete; pending human review.

## Executive Decision

Wave 0 launch pack is ready. After human review, the project may open one Control Tower chat and four Wave 1 branch chats.

Decision: `ready_to_open_control_tower_and_wave1_branch_chats_after_human_review`

Recommended next objective: `idare_wave1_parallel_branch_objectives`

## Preprocessing Decision

The preprocessing blocker is resolved:

| Check | Result |
|---|---|
| Corrected EEG source audit | `True` |
| EEG downsampling comparison | `True` |
| Prior result preprocessing validity | `True` |

Therefore:

- No EEG re-reference/CAR branch is active.
- No EEG downsampling rebuild branch is active.
- Prior I-DARE results remain valid from the preprocessing/downsampling standpoint.

## Parallel Wave 1 Branches

| Branch | Can run in parallel? | Why |
|---|---:|---|
| W1A EEG Input Definition | yes | Isolated EEG input-definition screen |
| W1B EEG Subject Normalization | yes | Isolated EEG normalization screen |
| W1C EMG Independent Baseline | yes | Separate modality and formulation |
| W1D Feature Discriminability | yes | Read-only, no training |

## Sequential / Deferred Branches

| Branch | Start condition |
|---|---|
| W2E EEG Cross-Factor Integration | Mandatory after W1A and W1B closeout |
| W2F Model Capacity Probe | After best Wave 1/W2E operating point |
| W2 Label/Midpoint Policy | After Wave 1 gate if activated |
| W3 Augmentation | After Wave 2 stable operating point |
| W3 Pre-Fusion Readiness | After EEG and EMG best configs are known |
| SupCon/DG Revisit | Only if Wave 2 changes the landscape |

## Key Guardrails

- No DEAP.
- No fusion.
- No EEG re-reference/downsampling changes.
- No augmentation before Wave 3.
- No Wave 1 neural training.
- No broad hyperparameter search.
- No branch pushes to main.
- Per-subject normalization must be labeled transductive when applicable.

## Files Created

- `docs/idare_wave0_parallel_operating_model.md`
- `docs/idare_wave0_baseline_registry.csv`
- `docs/idare_wave0_branch_registry.csv`
- `docs/idare_wave0_gate_criteria.csv`
- `docs/idare_wave0_control_tower_policy.md`
- `docs/idare_wave0_chat_bootstrap_prompts.md`
- `docs/idare_wave0_parallel_launch_pack_report.md`
- `docs/idare_wave0_parallel_launch_pack_report.json`

## Next Allowed Step

Open the Control Tower chat and branch chats after human review.
