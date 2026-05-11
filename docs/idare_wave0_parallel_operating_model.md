# I-DARE Wave 0 Parallel Operating Model

## Status

Status: complete; pending human review. This launch pack authorizes organization only. Wave 1 experiments start only after human approval.

## Locked Scope

- Dataset: I-DARE only.
- Modalities: EEG and EMG separately.
- Goal: improve cross-subject single-modality performance before fusion.
- DEAP is frozen.
- Fusion is frozen.
- No new EEG rereference branch is active.
- No EEG downsampling rebuild branch is active.

## Preprocessing Decision

The preprocessing provenance follow-up resolved the prior blocker:

- EEG source audit: corrected and passed.
- Downsampling comparison: passed.
- Prior results: valid from preprocessing/downsampling standpoint.

Therefore, the project does not launch a re-reference/CAR branch and does not rebuild EEG caches for anti-aliased downsampling. The data used in prior I-DARE runs remains a valid reference point.

## Parallel Work Rule

Wave 1 has four independent screening branches plus one Control Tower chat:

- W1A: EEG Input Definition
- W1B: EEG Subject Normalization
- W1C: EMG Independent Baseline
- W1D: Feature Discriminability
- CONTROL: gate/synthesis only

W1A-W1D can run in parallel because their docs prefixes, git branches, and scientific questions are isolated.

## Sequential Work Rule

Wave 2 and Wave 3 do not start until Control Tower closes the relevant gate.

Mandatory sequential items:

- W2E Cross-Factor Integration starts only after W1A and W1B close.
- W2F Model Capacity starts only after the best Wave 1/W2E operating point is selected.
- Label/Midpoint Policy starts only if Control Tower activates it after Wave 1.
- Augmentation starts only after Wave 2 establishes a stable operating point.
- SupCon/DG revisit starts only if upstream assumptions change the operating point.

## Branch Isolation

Each branch writes only to its own docs prefix. Branch chats do not modify each other's files and do not push to main.

## Evidence Discipline

Every branch follows:

1. objective
2. smoke or read-only audit
3. first pass if authorized
4. diagnosis
5. closeout
6. Control Tower gate review

Negative results are preserved. Branches do not silently disappear.

## Main Forbidden Actions

- No DEAP.
- No fusion.
- No Wave 1 neural experiments.
- No broad hyperparameter search.
- No EEG rereference/downsampling alteration.
- No augmentation before Wave 3.
- No main pushes from branch chats.
