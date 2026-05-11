# I-DARE Wave 0 Control Tower Policy

## Status

Status: complete; pending human review.

## Role

The Control Tower chat owns coordination, not experiments.

## Responsibilities

1. Maintain the frozen baseline registry.
2. Maintain the branch registry.
3. Detect file-prefix and scope conflicts.
4. Track branch status and best-result leaderboard.
5. Review branch closeouts.
6. Authorize Wave 2 and Wave 3 gates.
7. Decide whether pairwise reference should be reopened under controlled criteria.
8. Preserve negative and archived results.

## Forbidden

- No training.
- No cache building.
- No branch-owned output generation.
- No silent changes to thresholds.
- No DEAP.
- No fusion.
- No direct push to main except a reviewed synthesis/merge step.

## Gate Review Template

```text
WAVE N GATE REVIEW

Inputs:
- Branch closeout docs reviewed:
- Baseline comparisons:
- Best cells:
- Failed cells:
- Cross-branch interactions:
- Scope violations:
- Reopen triggers:

Decision:
- proceed / hold / redesign / stop

Authorized next branches:
- ...

Notes:
- ...
```

## Pairwise Reopen Rule

The pairwise branch stays closed as reference-only unless a changed input definition, changed normalization, or Wave 2 interaction cell reaches at least 0.53 balanced accuracy. Reopening must be controlled and documented; no ad hoc continuation is allowed.
