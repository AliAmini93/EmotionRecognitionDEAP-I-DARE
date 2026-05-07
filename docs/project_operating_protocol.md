# Project Operating Protocol

## Status

This document defines the shared operating rules for this repository.

Every new chat/session should read this file together with:

1. `docs/project_status_current.md`
2. `docs/project_status_current.json`
3. `docs/research_scope_and_objectives.md`
4. `docs/smoke_and_evaluation_protocol.md`
5. The relevant per-phase status/freeze documents

The goal is to prevent documentation drift, inconsistent commits, accidental cache commits, and premature claims.

## Source of Truth Hierarchy

When files disagree, use this order:

| Priority | Source | Role |
|---:|---|---|
| 1 | `docs/project_status_current.md` and `docs/project_status_current.json` | Current roadmap, frozen phases, next allowed steps, intentionally not-started items |
| 2 | Per-phase status/freeze docs in `docs/*_status.md` | Phase-level interpretation and decision records |
| 3 | Experiment/build reports in `docs/*.md` and `docs/*.json` | Raw smoke/build evidence and metrics |
| 4 | Reusable scripts in `scripts/` | Reproducible implementation entry points |
| 5 | `README.md` | Proposal, high-level project framing, and method assumptions |
| 6 | Chat history / terminal output | Helpful context, but not a durable source of truth |

Rules:

- If `README.md` conflicts with newer status docs, treat README as proposal context unless explicitly updated.
- If a smoke report conflicts with a later status/freeze doc, report the mismatch before acting.
- If `docs/project_status_current.md/json` is stale, update it before starting a new phase.

## Evidence Levels

Use these terms consistently:

| Term | Meaning |
|---|---|
| `smoke` | Small stabilization run, usually partial folds/seeds/runs. Useful for debugging and direction, not final performance. |
| `frozen` | Current phase has been documented and closed for now. This does not imply final scientific performance. |
| `final LOSO` | Full leave-one-subject-out or final protocol-level claim. Not allowed unless explicitly run and documented. |
| `ablation` | Controlled comparison to test one modeling choice while keeping splits, seeds, recipes, and metrics disciplined. |
| `mainline` | Current practical default path, still subject to future ablations unless explicitly final. |

Rules:

- Treat current results as smoke/stabilization unless a status doc explicitly says otherwise.
- Do not call a result final just because it is committed.
- Do not start fusion or full paired BSL/STIM modeling unless the central roadmap allows it.

## What to Commit

Commit durable project artifacts:

| Category | Commit? | Examples |
|---|---|---|
| Reusable scripts | Yes | `scripts/NN_*.py` |
| Build reports | Yes | `docs/*_build_report.md`, `docs/*_build_report.json` |
| Smoke reports | Yes | `docs/*_smoke.md`, `docs/*_smoke.json`, `docs/*_predictions.csv` |
| Status/freeze docs | Yes | `docs/*_status.md`, `docs/*_status.json` |
| Central roadmap | Yes | `docs/project_status_current.md`, `docs/project_status_current.json` |
| Protocol docs | Yes | `docs/project_operating_protocol.md`, `docs/research_scope_and_objectives.md`, `docs/smoke_and_evaluation_protocol.md` |
| README/proposal notes | Yes, when method assumptions change | `README.md` |

## What Not to Commit

Do not commit temporary or local artifacts:

| Category | Commit? | Examples |
|---|---|---|
| Patch logs | No | `docs/create_*.log`, `docs/*_patch.log` |
| Downloaded one-off patch scripts | No | `$HOME/Downloads/*.py` |
| Raw data | No | raw EEG/EMG files, downloaded datasets |
| Cache arrays | No by default | `.cache/*.npy`, `.cache/*.csv` unless explicitly approved |
| Virtual environments | No | `.venv/` |
| Terminal transcripts | No by default | copied shell output logs |

If a log is scientifically meaningful, convert it into a concise report under `docs/` rather than committing the raw patch log.

## Patch Script Convention

When a patch script is used:

1. Keep the script in `$HOME/Downloads` unless it is a reusable project tool.
2. Write patch logs under `docs/`.
3. Inspect the log.
4. Remove the patch log before commit.
5. Commit only durable outputs.

Recommended pattern when the patch does not write its own log:

```bash
PATCH_FILE="$HOME/Downloads/some_patch.py"
LOG_FILE="docs/some_patch.log"

python "$PATCH_FILE" > "$LOG_FILE" 2>&1
PATCH_EXIT=$?

echo "PATCH_EXIT=${PATCH_EXIT}"
echo "----- PATCH LOG START -----"
cat "$LOG_FILE"
echo "----- PATCH LOG END -----"

if [ "$PATCH_EXIT" -ne 0 ]; then
  echo "Patch failed."
  exit "$PATCH_EXIT"
fi
```

If the patch script itself writes the log file, do not redirect stdout into the same file.

Before committing:

```bash
git restore --staged "$LOG_FILE" 2>/dev/null || true
rm -f "$LOG_FILE"
```

## Assistant/User Handoff Protocol

This project often advances through an external-run loop:

1. The assistant prepares a patch, command block, analysis script, or experiment plan.
2. The user runs it locally in the repository or with local/private data.
3. The user returns the requested outputs to the assistant.
4. The assistant analyzes those outputs and decides the next safe step.
5. Durable conclusions are written into repository docs.

This loop must be explicit. Every command block or patch should say what the assistant expects back.

### Required Return Payload

At the end of any instruction block, the assistant should specify one of these return types:

| Return type | When it is enough | What the user should send back |
|---|---|---|
| Terminal-only | Compile checks, git status, small sanity summaries, short smoke logs | Full terminal output from the command block |
| Files-only | The key result is a generated file, plot, table, image, CSV, JSON, or report | The requested files uploaded or pasted, plus a short note that the command finished |
| Terminal + files | The terminal output confirms execution, but files contain the evidence | Full terminal output and the requested files |
| GitHub-only | The change was committed/pushed and can be checked from GitHub | Commit hash, `git status --short`, and `git log --oneline -9` |
| Human decision | The next step needs project judgment rather than code execution | The user's decision, constraints, or preference |

The assistant should not assume terminal output is always sufficient. If a generated artifact is needed for interpretation, the assistant must ask for it explicitly.

### Output Location Rules

Generated outputs should be placed in predictable locations:

| Output kind | Preferred location | Commit? |
|---|---|---|
| Smoke/build Markdown report | `docs/` | Yes |
| Smoke/build JSON report | `docs/` | Yes |
| Prediction CSV diagnostics | `docs/` | Yes, after line-ending sanity |
| Status/freeze docs | `docs/` | Yes |
| Central roadmap updates | `docs/project_status_current.md/json` | Yes |
| Protocol docs | `docs/` | Yes |
| Patch logs | `docs/*.log` | No |
| One-off patch scripts | `$HOME/Downloads/` | No |
| Reusable project scripts | `scripts/` | Yes |
| Cache arrays / sidecars | `.cache/` | No by default |
| Temporary plots/images for assistant review | `docs/_scratch/` or `$HOME/Downloads/` | No by default |
| Final report figures/tables | `docs/` or a dedicated tracked report folder | Yes, if part of durable documentation |

If a temporary file is useful only for assistant review, do not commit it. If the analysis result is scientifically meaningful, summarize it in a tracked Markdown/JSON report.

### File Return Rules

When asking the user to send files back, the assistant should name the exact paths.

Examples:

```text
Please return:
1. Full terminal output
2. docs/some_smoke_report.md
3. docs/some_smoke_report.json
4. docs/some_predictions.csv
```

For images/plots:

```text
Please return:
1. Full terminal output
2. docs/some_plot.png
3. The Markdown/JSON report that explains how the plot was generated
```

For large CSV/JSON files:

- Prefer a concise Markdown/JSON summary committed under `docs/`.
- Ask for the full file only if row-level or artifact-level inspection is necessary.
- If a large file is required, request only the specific file and explain why it is needed.

### Analysis Documentation Rule

Any important analysis based on returned terminal output, CSVs, JSON files, plots, or images must become durable documentation.

Do not leave important interpretations only in chat.

Use one of these forms:

| Situation | Durable documentation |
|---|---|
| Build/cache result | `docs/*_build_report.md/json` |
| Training smoke result | `docs/*_smoke.md/json` |
| Cross-run comparison | `docs/*_comparison.md/json` |
| Phase decision | `docs/*_status.md/json` |
| Roadmap-level change | `docs/project_status_current.md/json` |
| Operating convention change | `docs/project_operating_protocol.md` |

### Assistant Response Template for External Runs

When the assistant gives a command block that the user will run locally, it should end with a clear handoff request:

```text
After this finishes, please send back:
1. The full terminal output
2. The generated files:
   - docs/example_report.md
   - docs/example_report.json
3. The final `git status --short` and `git log --oneline -9`

Do not commit:
- docs/example_patch.log
- one-off patch scripts
- cache arrays under `.cache/`
```

### User Return Template

When the user reports results back, the preferred structure is:

```text
Here is the terminal output:
<terminal output>

Generated files available:
- docs/example_report.md
- docs/example_report.json
- docs/example_predictions.csv

Commit/push status:
<git status/log output>

Notes:
<any concern, crash, closed terminal, missing file, or unexpected behavior>
```

If the terminal window closes or output is incomplete, the next assistant response should start with recovery commands rather than assuming success.

### Decision Rules After Returned Outputs

After receiving returned outputs, the assistant should:

1. Check whether the run completed.
2. Check whether expected files exist.
3. Check whether reports say `PASSED` or contain issues/warnings.
4. Check whether metrics and diagnostics are interpretable.
5. Check whether line endings or generated files need cleanup.
6. Decide whether to:
   - rerun,
   - inspect a file,
   - commit,
   - create a status/freeze doc,
   - update the central roadmap,
   - or stop and ask for a human decision.

The assistant should not move to the next scientific phase until the previous phase is documented and closed according to this protocol.


## Experiment / Build Lifecycle

A build or experiment phase is not considered closed until all required docs are updated.

### Phase Start Checklist

Before starting a new phase:

- Read `docs/project_status_current.md`.
- Read `docs/project_status_current.json`.
- Read this protocol.
- Read the relevant status/freeze docs.
- Confirm the phase is allowed by the central roadmap.
- Confirm what is intentionally not started.
- Confirm the label policy and whether it is final or just smoke default.

### During Run

For any build/training smoke:

- Use cache-backed inputs where possible.
- Avoid loading raw HDF5/MAT files inside training loops.
- Use subject-held-out validation first.
- Keep splits, seeds, recipes, and label policy explicit.
- Record majority baseline, macro F1, balanced accuracy, threshold sweep, and one-class collapse diagnostics where applicable.
- Standardize train/validation data using train-fold statistics only.

### Phase Closeout Checklist

Every completed phase should have:

1. Reusable script committed under `scripts/`, if new logic was created.
2. Smoke/build report `.md`.
3. Smoke/build report `.json`.
4. Predictions `.csv` when training predictions are part of diagnostics.
5. Status/freeze `.md` and `.json` when the phase is being closed.
6. Updated `docs/project_status_current.md`.
7. Updated `docs/project_status_current.json`.
8. Clear `next allowed step`.
9. Clear `intentionally not started`.
10. No patch logs staged or committed.
11. No `.cache` arrays staged or committed unless explicitly approved.

## When to Update `docs/project_status_current.md/json`

Update the central roadmap when any of these happen:

- A phase is frozen.
- A new mainline/ablation decision is made.
- A previous `missing` result becomes `present`.
- A next allowed step changes.
- A phase moves from `not started` to `started`, `completed`, or `frozen`.
- A method assumption changes.
- A stale/mismatch note is corrected.
- A new protocol/status document becomes a durable source of truth.

Do not leave the central roadmap stale after a phase-close commit.

## When to Update README

Update `README.md` only when high-level proposal/method framing changes.

Examples:

- Label policy assumptions change or become explicitly not final.
- A dataset-specific modeling principle becomes central to the project.
- The project scope or main research objective changes.
- Installation/running instructions change.

README should not be used as a detailed experiment ledger. Use `docs/project_status_current.md` and per-phase status docs for that.

## Git Commit Message Convention

Use these prefixes:

| Prefix | Use for |
|---|---|
| `exp:` | New experiment/build/training scripts and smoke outputs |
| `docs:` | Status docs, reports, roadmap updates, README notes, protocols |
| `fix:` | Small corrections to scripts, docs, line endings, stale notes |
| `refactor:` | Code reorganization without changing experiment meaning |
| `chore:` | Repository maintenance with no scientific content change |

Examples:

```text
exp: smoke I-DARE EMG response plus BSL stats arousal ablation
docs: freeze I-DARE EMG BSL stats ablation status
docs: update current project status roadmap
fix: normalize raw EMG smoke prediction CSV endings
docs: add project operating protocol
```

## Required Checks Before Commit

Run targeted checks on the files you are committing:

```bash
git status --short

git diff --check -- <files>
git diff --stat -- <files>
git diff -- <files>
```

For Python scripts:

```bash
python -m py_compile <script.py>
```

For JSON files:

```bash
python - <<'PY'
import json
from pathlib import Path

for p in [Path("docs/some_file.json")]:
    json.loads(p.read_text(encoding="utf-8"))
    print(f"OK: {p}")
PY
```

For prediction CSVs, normalize line endings if needed:

```bash
python - <<'PY'
from pathlib import Path

for p in [Path("docs/some_predictions.csv")]:
    data = p.read_bytes()
    fixed = data.replace(b"\\n", b"\n").replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    if fixed != data:
        p.write_bytes(fixed)
        print(f"[PATCH] normalized line endings: {p}")
    else:
        print(f"[OK] line endings clean: {p}")
PY
```

## Required Checks After Push

After every push:

```bash
git status --short
git log --oneline -9
```

Expected:

- `git status --short` is empty, unless there are intentionally untracked local-only files.
- `HEAD`, `origin/main`, and `origin/HEAD` point to the new commit.
- The latest commit message matches the change.

## Label Policy Rules

The label policy is not final.

Current smoke runs often use `midpoint_as_high`, but final claims must compare:

- `discard_midpoint`
- `midpoint_as_low`
- `midpoint_as_high`

A label-policy ablation must use fixed:

- splits
- seeds
- recipes
- metrics
- task set
- cache inputs

Do not lock `midpoint_as_high` as final until the label-policy ablation is complete and frozen.

## Fusion Rules

Do not start EEG+EMG fusion until:

1. EEG single-modality baseline and BSL-stats ablation are directly compared.
2. EMG single-modality baseline and BSL-stats ablation are directly compared.
3. The comparison is documented.
4. The central roadmap says fusion is the next allowed step.

Fusion smoke should start with current mainline representations only, not every exploratory ablation.

## Full Paired BSL/STIM Model Rules

Do not start a full `model(BSL, STIM, STIM-BSL)` neural architecture until:

1. The low-capacity `STIM-BSL + BSL stats` ablation is compared against `STIM-BSL`-only.
2. Gains are stable across tasks or clearly task-specific.
3. Calibration/threshold behavior is acceptable.
4. The decision is frozen in a status doc.
5. The central roadmap allows the paired model phase.

## Documentation Consistency Rules

Before closing a phase, check for contradictions:

- Does a previous status doc now contain stale language?
- Does README imply a method is final when it is only provisional?
- Does `project_status_current.md` list the new phase?
- Does `project_status_current.json` match the markdown?
- Are intentionally-not-started items still accurate?

If a stale note is found, fix it with a small `docs:` or `fix:` commit before starting the next scientific phase.

## New Chat Sync Protocol

Every new chat/session should begin with:

1. Read `docs/project_status_current.md`.
2. Read `docs/project_status_current.json`.
3. Read `docs/project_operating_protocol.md`.
4. Read only the relevant per-phase status docs.
5. Check recent `git log`.
6. Report:
   - current phase
   - frozen phases
   - next allowed step
   - intentionally not-started items
   - known documentation mismatches
   - whether the session is ready to act

Do not create patches or run experiments before this sync is complete.
