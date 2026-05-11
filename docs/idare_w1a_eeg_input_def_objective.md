# W1A EEG Input Definition Objective

## Branch

`idare/wave1/eeg-input-definition`

## Worktree

`/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-w1a`

## Scope

This objective is limited to W1A:

- I-DARE only.
- EEG only.
- arousal only.
- within-subject pairwise affect preference ranking.
- ridge classifier only.
- normalization fixed to current/default none.
- existing 6-fold subject-held-out structure.
- maximum 18 registered runs.
- no neural training.
- no normalization ablation.
- no DEAP.
- no EEG+EMG fusion.
- no rereference/CAR.
- no downsampling rebuild.
- no cache overwrite.
- no push to main.

## Scientific Question

Is the current EEG input definition hiding useful signal?

## Registered Cells

| Cell | Input definition | Model | Task | Folds | Runs |
|---|---|---|---|---:|---:|
| A1 | current STIM-BSL summary | ridge classifier | arousal | 6 | 6 |
| A2 | BSL-stats sidecar | ridge classifier | arousal | 6 | 6 |
| A3 | STIM-BSL summary + BSL-stats concat | ridge classifier | arousal | 6 | 6 |

Total registered runs: `18`.

## Comparison References

- `REF-PW-EEG-ARO-001`: pairwise EEG arousal ridge summary_diff, balanced accuracy `0.5216709095`.
- `REF-BSL-EEG-ARO-001`: binary EEG arousal + BSL-stats, balanced accuracy `0.5427`.

## Gates

- moderate pass: any W1A cell mean balanced accuracy `>= 0.53`.
- strong pass: any W1A cell mean balanced accuracy `>= 0.55`.

## Input Policy

The runner must validate required input files before running. If required cache/input files are missing, the runner must stop and emit a W1A blocker report. It must not rebuild preprocessing, overwrite cache, or modify files outside the W1A docs prefix.

## Allowed Outputs

Only files matching:

`docs/idare_w1a_eeg_input_def_*`

are allowed for this branch setup/run/closeout.

`docs/project_status_current.*` may only be touched later if explicitly validated and required by branch closeout policy.

## Stop Conditions

Stop and notify Control Tower if:

- required cache/input files are missing,
- output validation fails,
- any file outside the W1A prefix is created unexpectedly,
- preprocessing changes are needed,
- normalization ablation is needed,
- neural training is needed,
- thresholds need changing,
- DEAP or fusion is needed,
- main branch needs to be touched,
- a gate threshold is reached,
- pairwise reopen or Wave 2 is suggested.
