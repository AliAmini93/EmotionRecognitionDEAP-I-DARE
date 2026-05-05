<!-- NEW_CHAT_START_PROTOCOL_MARKER -->

## New Chat Start Protocol

Before continuing this project in a new chat, follow `docs/new_chat_start_protocol.md`.

Hard rule: every new script/training recipe/experiment runner must start with a smoke test first, such as `--max-runs 2 --epochs 1`, before any full run is proposed.

The new chat must also verify file/context access before claiming it has read project files.

Minimum expected facts:
- Temporary main score-5 policy: `midpoint_as_high`.
- `discard_midpoint` remains a secondary sanity / ablation candidate.
- Main baseline: valence macro F1 `0.3953`, arousal macro F1 `0.4825`.
- Discard-midpoint sanity: valence macro F1 `0.3877`, arousal macro F1 `0.4202`.
- Next technical step: cache-based EEG training-recipe stabilization, smoke-test first.
