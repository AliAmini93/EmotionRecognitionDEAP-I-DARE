# New Chat Start Protocol

This file defines the required startup protocol for continuing the EmotionRecognitionDEAP-I-DARE project in a new chat.

## Mandatory First Behavior

A new chat must first summarize the current project state from the handoff/pasted context or from repository files before proposing new work.

The new chat must not jump directly into long-running experiments.

## Smoke-Test-First Rule

For every new script, training recipe, loader change, cache change, or experiment runner:

1. First create or run a minimal smoke test.
2. The smoke test should use a tiny run, for example:
   - `--max-runs 2`
   - `--epochs 1`
   - one fold or one task when possible
3. Only after the smoke test passes should the full run be proposed.
4. If the smoke test changes validation docs only because of rerunning validation, decide whether to revert those docs before commit.
5. Long-running commands must not be proposed before a smoke-test command has passed.

Reason: previous work showed that small issues such as HDF5 loading, cache-column naming, or report-string bugs can waste time if discovered only during full runs.

## File-Access Verification Rule

At the start of a new chat, the assistant must verify whether it actually has access to project files.

Valid ways to verify context:

- Read pasted handoff text.
- Read uploaded files.
- Use a connected GitHub/file connector if available.
- Ask the user to run terminal checks and paste outputs.

The assistant should not pretend it has read local files unless it has either received their contents or accessed them through a connector.

## Minimum Context Checks

Before continuing technical work, the assistant should confirm these facts from pasted text, repo files, or terminal output:

- Latest branch is clean or known dirty state is explained.
- Latest commits include the I-DARE EEG main baseline and discard-midpoint sanity baseline.
- EEG cache exists and was validated:
  - `.cache/idare_eeg_windows_32x640_float32.npy`
  - `.cache/idare_eeg_cache_index.csv`
  - cache shape `[2016, 32, 640]`
- Temporary main score-5 policy is `midpoint_as_high`.
- `discard_midpoint` remains a secondary sanity / ablation candidate.
- Next step is training-recipe stabilization, not final LOSO.

## Recommended First Terminal Checks

Ask the user to run these if direct file access is unavailable:

```bash
git status --short
git log --oneline -5

grep -n "D013\|midpoint_as_high\|discard_midpoint" docs/decision_log.md | tail -80

sed -n '1,220p' docs/idare_eeg_main_baseline_status.md
sed -n '1,220p' docs/idare_discard_midpoint_sanity_status.md

ls -lh .cache/idare_eeg_windows_32x640_float32.npy \
       .cache/idare_eeg_cache_index.csv
```

## New Chat Context Verification Prompt

Use this text at the start of a new chat:

```text
Before proposing commands, verify context access. Tell me whether you are using pasted handoff text, uploaded files, or GitHub/file connector. Then summarize exact facts from these files if available: docs/decision_log.md, docs/idare_eeg_main_baseline_status.md, docs/idare_discard_midpoint_sanity_status.md, docs/new_chat_start_protocol.md. If you cannot access them directly, ask me to paste terminal outputs. Do not claim you read local files unless you actually did.

Hard rule: every new script/training recipe/experiment runner must start with a smoke test first, such as --max-runs 2 --epochs 1, before any full run is proposed.
```

## Expected Facts The New Chat Should Know

The new chat should be able to state:

```text
latest main policy = midpoint_as_high
discard_midpoint = secondary sanity/ablation
main baseline valence macro F1 = 0.3953
main baseline arousal macro F1 = 0.4825
discard sanity valence macro F1 = 0.3877
discard sanity arousal macro F1 = 0.4202
next step = recipe stabilization, smoke-test first
```

## Next Technical Step

The next technical step should be recipe stabilization for cache-based EEG training using the temporary main policy `midpoint_as_high`.

Suggested script:

```text
scripts/20_run_idare_eeg_cache_recipe_stabilization.py
```

Suggested recipes:

- `ce_class_weighted`
- `balanced_sampler_ce`
- `focal_loss`
- `balanced_sampler_focal`

Primary evaluation priorities:

1. Fewer one-class final runs
2. Higher macro F1
3. Higher balanced accuracy
4. Stability across folds/seeds
