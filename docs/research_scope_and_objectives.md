# Research Scope and Objective Registry

## Status

This document defines the durable research scope, objective hierarchy, and ablation registry for the project.

It is not an experiment ledger. It tells future chats why each phase exists and how short-term work maps to medium- and long-term goals.

## Source Documents

- README.md: `README.md` (present)
- project_status_current.md: `docs/project_status_current.md` (present)
- project_status_current.json: `docs/project_status_current.json` (present)
- project_operating_protocol.md: `docs/project_operating_protocol.md` (present)
- deap_emg_feature_only_status.md: `docs/deap_emg_feature_only_status.md` (present)
- idare_emg_feature_only_status.md: `docs/idare_emg_feature_only_status.md` (present)
- idare_raw_emg_only_status.md: `docs/idare_raw_emg_only_status.md` (present)
- idare_eeg_bsl_stats_ablation_status.md: `docs/idare_eeg_bsl_stats_ablation_status.md` (present)
- idare_emg_bsl_stats_ablation_status.md: `docs/idare_emg_bsl_stats_ablation_status.md` (present)
- idare_baseline_modeling_literature_plan.md: `docs/idare_baseline_modeling_literature_plan.md` (present)

## In Scope

- Cross-subject emotion recognition within each dataset.
- DEAP and I-DARE as the main datasets.
- Binary valence and binary arousal classification.
- EEG-only, EMG-only, and EEG+EMG fusion after readiness.
- Dataset-aware modeling when the dataset structure justifies it.
- I-DARE trial-aware BSL/STIM modeling through STIM-BSL and compact BSL-stats ablations.
- DEAP temporal modeling of 12 x 5s windows inside each 60s trial.
- Controlled ablations of representation, label policy, architecture, augmentation, and regularization.

## Out of Scope for the Current Proposal/Phase

- Cross-dataset transfer between DEAP and I-DARE.
- Final paper-level performance claims from smoke runs.
- EEG+EMG fusion before single-modality readiness and comparison.
- Full paired model(BSL, STIM, STIM-BSL) before low-capacity BSL-stats evidence is interpreted.
- Locking midpoint_as_high as the final label policy before label-policy ablation.
- Promoting raw EMG to mainline without evidence against feature-level EMG.

## Long-Term Objectives

| ID | Objective | Definition | Success evidence |
|---|---|---|---|
| L1 | Quantify EMG value added to EEG | Test whether EMG improves cross-subject emotion recognition when combined with EEG. | Controlled EEG-only, EMG-only, and EEG+EMG evaluations under fixed protocol. |
| L2 | Build reproducible EEG/EMG pipelines for DEAP and I-DARE | Create cache-backed, documented, reproducible pipelines for EEG-only, EMG-only, and multimodal experiments. | Reusable scripts, reports, frozen status docs, and central roadmap updates. |
| L3 | Use dataset structure responsibly | Do not force DEAP and I-DARE into identical modeling assumptions when their trial structures differ. | DEAP sequence modeling and I-DARE BSL/STIM-aware ablations are evaluated separately. |
| L4 | Reach defensible final evaluation | Move from smoke/stabilization to broader/full evaluation and eventually final LOSO only after stability. | Explicit transition from smoke to full/broader testing and documented decisions. |

## Medium-Term Objectives

| ID | Objective | Status | Supports |
|---|---|---|---|
| M1 | Stabilize EEG-only baselines | active/planned | L1, L2, L4 |
| M2 | Stabilize EMG-only baselines | active/frozen in parts | L1, L2, L4 |
| M3 | Determine current I-DARE EEG and EMG mainline representations | active/frozen in parts | L2, L3 |
| M4 | Compare EMG raw waveform and feature-level representations | frozen smoke evidence | L1, L2 |
| M5 | Evaluate I-DARE BSL-aware modeling | BSL-stats smoke frozen; direct comparison still needed | L2, L3 |
| M6 | Evaluate DEAP temporal sequence modeling | planned/not started in current frozen roadmap | L1, L3, L4 |
| M7 | Evaluate EEG+EMG fusion | not started intentionally | L1, L2, L4 |
| M8 | Run controlled label-policy ablation | planned/not final | L2, L4 |
| M9 | Run EEGSegmentEncoder/Classifier architecture ablations | planned after baseline stabilization | L2, L4 |
| M10 | Evaluate data augmentation | planned controlled ablation | L2, L4 |
| M11 | Evaluate SupCon / VREx / domain generalization | planned after baseline stabilization | L1, L2, L4 |

## Short-Term Objective Template

Every new short-term objective should be declared using these fields before experiments start:

- `id`
- `linked_medium_objective`
- `question`
- `input_artifacts`
- `expected_outputs`
- `smoke_pass_criteria`
- `full_or_broader_pass_criteria`
- `failure_taxonomy`
- `next_allowed_step`
- `intentionally_not_started`
- `docs_to_update_on_close`

## Ablation Registry

This registry lists controlled ablation families. It is not permission to run all of them immediately.

| Family | Status | Items | Activation rule |
|---|---|---|---|
| Label policy | planned/not final | `discard_midpoint`<br>`midpoint_as_low`<br>`midpoint_as_high` | Run only under fixed splits, seeds, recipes, and metrics. |
| Windowing | planned | `4s`<br>`5s`<br>`6s`<br>`optional 50% overlap` | Run after baseline windowing path is stable. |
| DEAP temporal sequence modeling | planned | `independent 5s windows`<br>`12-window trial sequence`<br>`EEG-only without sequence`<br>`EEG-only with sequence`<br>`EEG+EMG without sequence`<br>`EEG+EMG with sequence` | Run after DEAP single-modality baselines are established. |
| EEGSegmentEncoder/Classifier architecture | planned after baseline stabilization | `OldEncoder vs EEGSegmentClassifier`<br>`temporal stem variants`<br>`stem fusion concat/sum/attn/lightweight MoE`<br>`channel position none/learnable/coord`<br>`channel mixer none/MHA/graph_bias`<br>`raw-only vs raw+spectral`<br>`GN vs BN`<br>`modelsize lite vs base` | Run as controlled ablations only after a stable EEG baseline exists. |
| EMG representation | active/frozen in parts | `feature-level EMG`<br>`raw waveform EMG`<br>`EMG BSL-stats sidecar` | Feature-level EMG remains mainline unless controlled evidence changes it. |
| I-DARE BSL-aware modeling | active/frozen in parts | `STIM-only`<br>`STIM-BSL`<br>`STIM-BSL + BSL stats`<br>`later model(BSL, STIM, STIM-BSL)` | Full paired model is allowed only after BSL-stats evidence is compared against STIM-BSL-only baselines. |
| Data augmentation | planned controlled ablation | `noise/jitter/scaling/window-level augmentations if justified`<br>`dataset-appropriate augmentation only` | Run only after a stable baseline and with augmentation leakage checks. |
| SupCon / Domain Generalization | planned after baseline stabilization | `CE only`<br>`CE + affective SupCon`<br>`CE + VREx`<br>`CE + SupCon + VREx` | Run only after baseline/fusion readiness; positive pairs must respect affective response, not stimulus identity alone. |

## Current Priority Filter

- Do not start an ablation unless it is linked to a medium-term objective.
- Do not run an ablation if the result cannot change a decision.
- Do not start fusion before single-modality readiness is documented.
- Prefer direct comparison docs before adding new model families.
- Treat planned ablations as registry items, not permission to run them immediately.

## Current Next Allowed Focus

- Directly compare BSL-stats ablations against corresponding STIM-BSL-only baselines for EEG and EMG.
- Keep fusion not-started until this comparison is documented.
- Keep label policy open for future controlled ablation.

## Design Principle

- DEAP comparability matters, but DEAP and I-DARE should not be forced into identical architectures when the dataset structure differs.
- I-DARE-aware BSL/STIM modeling is valid, but it must be introduced through controlled ablations and documented mainline decisions.
- Planned architecture, augmentation, SupCon, and domain-generalization work should wait until relevant baselines are stable.
- Negative results are still findings if the pipeline is healthy and the comparison is fair.
