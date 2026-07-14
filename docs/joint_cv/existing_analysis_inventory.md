# Existing Analysis Inventory

This inventory was generated from the complete local Git history, including historical and later-reverted artifacts.

No model training was performed.

## Summary

- Unique candidate artifacts: `798`
- Current-tree artifacts: `781`
- Historical-only artifacts: `17`
- Automatically detected Strict Joint candidates: `0`
- Explicit pair-out artifacts: `9`

## Dataset Counts

| dataset | count |
| --- | --- |
| I-DARE | 570 |
| unspecified | 163 |
| DEAP+I-DARE | 65 |

## Protocol Counts

| protocol | count |
| --- | --- |
| unspecified | 332 |
| leave-one-subject-out | 262 |
| smoke-or-partial | 195 |
| leave-one-subject-stimulus-pair-out | 9 |

## Analysis-Type Counts

| analysis_type | count |
| --- | --- |
| model-or-training-result | 341 |
| prior-or-baseline | 302 |
| chance-or-null-analysis | 54 |
| other | 53 |
| label-audit | 21 |
| data-or-cache-audit | 19 |
| variance-decomposition | 8 |

## Automatically Detected Strict Joint Candidates

No artifact was automatically confirmed as Strict Joint CV.

## Pair-Out Warning

Every leave-one-subject-stimulus-pair-out artifact is classified as non-Strict-Joint because the target subject and target stimulus remain observable through other training cells.

| dataset | artifact_path | commit_sha | task | current_path_exists |
| --- | --- | --- | --- | --- |
| DEAP+I-DARE | docs/roca/idare_personalization_decision_synthesis_current.json | 4b42986d205dfd5dcc4865e57c038abc77f030dc | valence+arousal | yes |
| I-DARE | docs/roca/idare_residual_physiology_synthesis_current.json | 2a745ee1b69f58eb0ff12b59d3efc61f173a8cc9 | valence+arousal | yes |
| I-DARE | docs/roca/idare_residual_physiology_synthesis_current.md | 2a745ee1b69f58eb0ff12b59d3efc61f173a8cc9 | valence+arousal | yes |
| I-DARE | docs/roca/idare_residual_physiology_synthesis_current_prior_summary.csv | 2a745ee1b69f58eb0ff12b59d3efc61f173a8cc9 | valence+arousal | yes |
| DEAP+I-DARE | docs/roca/prior_baselines_no_global_current.json | 3845e7b45bf2e7beff7d59b56dbd4baf868adf1e | valence+arousal | yes |
| DEAP+I-DARE | docs/roca/prior_baselines_no_global_current.md | 3845e7b45bf2e7beff7d59b56dbd4baf868adf1e | valence+arousal | yes |
| DEAP+I-DARE | docs/roca/prior_baselines_no_global_current_binary_metrics.csv | 3845e7b45bf2e7beff7d59b56dbd4baf868adf1e | valence+arousal | yes |
| DEAP+I-DARE | docs/roca/prior_baselines_no_global_current_main_metrics.csv | 3845e7b45bf2e7beff7d59b56dbd4baf868adf1e | valence+arousal | yes |
| DEAP+I-DARE | scripts/roca/01c_prior_baselines_no_global.py | 3845e7b45bf2e7beff7d59b56dbd4baf868adf1e | valence+arousal | yes |

## Manual Review Requirement

This file is an automated first-pass inventory. The full row-level evidence is stored in:

- `docs/joint_cv/existing_analysis_inventory.csv`

Before reusing any result, inspect the exact script/report content, split construction, target-data visibility, and statistical unit.
