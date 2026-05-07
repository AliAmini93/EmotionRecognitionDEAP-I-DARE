# Smoke and Evaluation Protocol

## Status

This document defines how the project moves from objectives to audit, smoke, broader/full evaluation, freeze decisions, and future literature/method review.

Core principle: **Smoke pass is permission to proceed to broader/full evaluation or comparison; it is not a final scientific claim.**

## Workflow

1. Define objective and scope
2. Run audit / feasibility check
3. Run smoke test
4. Make smoke decision
5. Run broader/full evaluation when allowed
6. Interpret result
7. Freeze/document/update roadmap
8. Move to next allowed objective

## Evidence Levels and Allowed Claims

| Level | Meaning | Allowed claim |
|---|---|---|
| audit | Checks data, labels, index, shapes, paths, subject grouping, cache availability, and leakage risks. | The data/protocol path is usable or not usable yet. |
| smoke | Small stabilization run with limited folds/seeds/runs to test execution, diagnostics, and plausibility. | The pipeline is healthy enough for comparison or broader evaluation, or it needs fixing. |
| comparison_smoke | Small controlled comparison between two already-defined choices. | A path is promising/weak at smoke level only. |
| broader_full_evaluation | Larger controlled run with fixed protocol, more folds/seeds/recipes, or full LOSO if declared. | A stronger empirical claim, still bounded by the declared protocol. |
| final_LOSO | Full leave-one-subject-out or final protocol-level evaluation explicitly declared and documented. | Final paper-level claim for that protocol. |

## Smoke Pass Criteria

- Run completes without crash.
- Expected reports and outputs are produced.
- Input shapes, dtypes, labels, and subject splits are sane.
- No NaN/Inf or they are explicitly documented and handled.
- No subject leakage is detected.
- Majority baseline is recorded.
- Macro F1 and balanced accuracy are recorded.
- Threshold sweep diagnostics are recorded when relevant.
- One-class collapse is recorded.
- Artifacts are suitable for commit according to the operating protocol.

## What Smoke Pass Does Not Mean

- High metric alone is not sufficient.
- Threshold-tuned gain alone is not sufficient.
- One lucky fold is not sufficient.
- A committed report is not a final result.

## Failure Taxonomy and Required Action

| Failure type | Examples | Required action |
|---|---|---|
| engineering_fail | missing file<br>path error<br>JSON serialization error<br>CSV line endings<br>script crash | Fix implementation/artifacts and rerun the same smoke. |
| data_protocol_fail | label mismatch<br>cache/index mismatch<br>subject leakage<br>wrong baseline pairing<br>NaN/Inf not handled | Stop training, audit data/protocol, document issue, rerun only after correction. |
| scientific_weak_result | metrics near majority baseline<br>no improvement over baseline<br>unstable thresholds | Document as finding; run only limited ablation if it can change a decision. |
| inconclusive_result | mixed fold behavior<br>small gains but calibration sensitivity<br>task-specific conflict | Create comparison/status doc and request human decision or one targeted ablation. |
| repeated_scientific_failure | multiple healthy runs fail to improve<br>several ablations all weak<br>architecture assumption appears wrong | Stop patching blindly; create literature/method review task. |

## Under-Analysis / Over-Analysis Control

### Avoid under-analysis

- Do not move to the next phase without status/freeze docs.
- Do not ignore collapse, threshold instability, or majority baseline.
- Do not skip direct comparison when changing mainline.

### Avoid over-analysis

- Do not run large literature review for a simple engineering fail.
- Do not add new model families before baseline comparison is documented.
- Do not run an ablation if its result cannot change a decision.

## Literature / Method Review Triggers

- A full/broader test fails scientifically while the pipeline is healthy.
- Several controlled ablations fail or remain inconclusive.
- A major method/architecture decision is needed.
- Dataset-specific modeling assumptions need external justification.
- The next step is no longer obvious from current project docs.

## Stop Criteria

- An ablation shows no useful signal in smoke and has no clear decision impact.
- A path repeatedly underperforms a simpler baseline under fair comparisons.
- A method requires capacity/data not available in the current project.
- The central roadmap says the phase is intentionally not started.

## Documentation Requirements

- Every completed phase needs reports, status/freeze docs if closed, and project_status_current updates.
- Every important interpretation from terminal output, CSV/JSON, plot, or image must become durable docs.
- Every next phase must have a next allowed step and intentionally-not-started statement.

## Current Project Application

- Current work remains smoke/stabilization unless a status doc says otherwise.
- Fusion remains not-started until single-modality comparisons are documented.
- Full paired BSL/STIM model remains not-started until low-capacity BSL-stats evidence is interpreted.
- Label policy remains open until controlled ablation is done.

## Short-Term Objective Decision Rule

For every short-term objective:

```text
audit pass -> smoke
smoke pass -> broader/full evaluation or controlled comparison
broader/full pass -> freeze/update roadmap
engineering fail -> fix and rerun same smoke
data/protocol fail -> stop, audit, document, correct
scientific weak result -> document finding, compare fairly, or stop
repeated scientific failure -> literature/method review
```
