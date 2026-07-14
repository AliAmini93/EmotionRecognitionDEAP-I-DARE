# Correction to Manifest Prerequisites Audit

The earlier readiness decision was too permissive.

- Earlier DEAP mapping status: `needs_manual_review`
- Earlier combined Joint-CV ready value: `True`
- Correct rule: only a **verified** DEAP mapping may set DEAP stimulus-aware readiness to true.
- Corrected DEAP verdict: **UNVERIFIED_TRIAL_POSITION_AS_STIMULUS_ID**
- Corrected DEAP Joint-CV readiness: `False`
- I-DARE readiness remains: `True`

The earlier 38 repository hits were mostly generic mentions of DEAP trials/windowing and do not constitute a verified subject-trial-to-video mapping.
