# I-DARE Minimal SupCon/DG First-pass Review Status

## Status

Human review accepted the minimal SupCon/DG first-pass result as **not sufficient**.

- Created at: `2026-05-08T09:55:30+00:00`
- Reviewed report: `docs/idare_minimal_supcon_dg_first_pass_report.md`
- Accepted diagnosis: `minimal_supcon_dg_first_pass_not_sufficient`
- Accepted next objective: `supcon_dg_failure_analysis_objective`
- Runs reviewed: `72`
- Prediction rows reviewed: `19632`

## Review Decision

The first-pass SupCon/DG intervention is scientifically useful but not yet a fix.

The run completed and produced valid outputs, but the aggregate result does not justify moving to direct full SupCon/DG training, broad hyperparameter search, EEG+EMG fusion, mainline changes, or any final LOSO claim.

The correct next step is a **read-only failure analysis** to determine why the intervention did not improve robustly.

## Key Evidence

Best recomputed cell from `docs/idare_minimal_supcon_dg_first_pass_runs.csv`:

```json
{
  "method": "CE_plus_VREx",
  "modality": "EMG",
  "task": "valence",
  "n_runs": 6,
  "mean_macro_f1": 0.5064987409626325,
  "mean_balanced_accuracy": 0.5151315622001712,
  "mean_accuracy": 0.5185094553335976
}
```

## Next Selected Step

Create and run:

- `docs/idare_supcon_dg_failure_analysis_objective.md`
- `docs/idare_supcon_dg_failure_analysis_objective.json`

This next step must explain failure modes before any new training matrix is authorized.
