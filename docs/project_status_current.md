# Current Project Status / Roadmap Index

## Status

This is the central project status index for the current smoke/stabilization phase.

It summarizes the latest frozen documentation and explicitly separates smoke evidence from final LOSO claims.

## Scope

- Project: cross-subject EEG/EMG emotion recognition on DEAP and I-DARE.
- Current evidence level: smoke/stabilization, not final performance.
- Current discipline: cache-backed runs, subject-held-out validation first, status docs frozen before moving to the next phase.

## Proposal Alignment

- The proposal's macro goal is to test whether EMG can add value to EEG in cross-subject emotion recognition.
- The current work is aligned with that goal because EEG-only, EMG-only, raw-vs-feature, and BSL-aware ablations are being isolated before fusion.
- I-DARE is treated as a trial-aware BSL/STIM dataset; therefore `STIM-BSL` and compact `BSL stats` are valid I-DARE-aware ablations.
- DEAP and I-DARE are not forced into identical architectures when the dataset structure differs.

## Label Policy Status

The original README proposal used `score > 5` with `score == 5` discarded. That was an initial harmonization assumption, not a final locked decision.

Current smoke runs mostly use `midpoint_as_high` because it preserves all trials and stabilizes early smoke comparisons. However, this is **not final**.

Label policy is now an explicit future ablation:

- `discard_midpoint`: score `> 5` is high, score `== 5` discarded.
- `midpoint_as_low`: score `> 5` is high, score `== 5` low.
- `midpoint_as_high`: score `>= 5` is high.

Final claims should not lock to `midpoint_as_high` until these policies are compared under fixed splits, seeds, recipes, and metrics.

## Phase Roadmap

| Area | Current state | Frozen? | Evidence | Next allowed step | Intentionally not started |
|---|---|---|---|---|---|
| DEAP modality audit / EMG feature path | completed enough for EMG feature-only smoke | yes | `docs/deap_emg_feature_only_status.md` | Broader DEAP EMG evaluation or align DEAP EEG path before fusion. | Final LOSO claim; raw EMG waveform mainline. |
| I-DARE EMG feature-only | cache-backed and smoke-tested for valence/arousal | yes | `docs/idare_emg_feature_only_status.md` | Use as main EMG representation unless a controlled ablation beats it. | Fusion claim; final LOSO claim. |
| I-DARE raw EMG-only | raw waveform cache and raw EMG-only smokes completed | yes | `docs/idare_raw_emg_only_status.md`<br>`docs/idare_emg_raw_vs_feature_smoke_comparison.md` | Keep as ablation; feature-level EMG remains mainline. | Raw EMG as mainline. |
| I-DARE EEG BSL-stats ablation | response cache plus compact BSL stats sidecar smoke-tested for valence/arousal | yes | `docs/idare_eeg_bsl_stats_ablation_status.md` | Compare directly against STIM-BSL-only EEG before changing the mainline. | EEG+EMG fusion; full paired BSL/STIM neural model. |
| I-DARE EMG BSL-stats ablation | feature cache plus compact BSL stats sidecar smoke-tested for valence/arousal | yes | `docs/idare_emg_bsl_stats_ablation_status.md` | Compare directly against STIM-BSL-only EMG feature baseline before changing the mainline. | EEG+EMG fusion; full paired BSL/STIM neural model. |
| EEG+EMG fusion | not started intentionally | no | `docs/idare_eeg_bsl_stats_ablation_status.md`<br>`docs/idare_emg_bsl_stats_ablation_status.md` | Start only after current baseline/ablation status is indexed and compared cleanly. | All fusion experiments. |
| Full model(BSL, STIM, STIM-BSL) | not started intentionally | no | `docs/idare_baseline_modeling_literature_plan.md` | Only after low-capacity BSL-stats ablation beats STIM-BSL-only baselines consistently. | Two-branch or three-branch full paired neural model. |
| Label-policy ablation | planned / not final | no | `README.md`<br>`training smoke JSON reports` | Run controlled comparison of discard_midpoint, midpoint_as_low, and midpoint_as_high using fixed splits/seeds. | Locking midpoint_as_high as the final paper policy. |

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

## Documentation Gap Closed by This File

Before this file, the project had strong per-phase status docs but no central status index. This file is the central map that links the proposal, frozen status documents, smoke reports, and next allowed steps.
