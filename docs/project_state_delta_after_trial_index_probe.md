# Project State Delta — I-DARE Trial Index Probe

## Add to Completed

- I-DARE HDF5 and mat73 structure probes were generated:
  - `scripts/02_probe_idare_hdf5_structure.py`
  - `docs/idare_hdf5_structure_probe.md`
  - `docs/idare_hdf5_structure_probe.json`
  - `scripts/03_probe_idare_mat73_loader.py`
  - `docs/idare_mat73_probe.md`
  - `docs/idare_mat73_probe.json`
- I-DARE MATLAB reference/event probe was generated:
  - `scripts/04_probe_idare_refs_and_events.py`
  - `docs/idare_refs_and_events_probe.md`
  - `docs/idare_refs_and_events_probe.json`
- I-DARE trial index probe was generated:
  - `scripts/05_probe_idare_trial_index.py`
  - `docs/idare_trial_index_probe.md`
  - `docs/idare_trial_index_probe.json`
- I-DARE trial/event alignment was confirmed for sample subjects 1, 2, and 3.
- I-DARE loader design was clarified:
  - use `STIM_*` rows only,
  - strip `STIM_` prefix for label matching,
  - use `Stimuli_Specifications.csv` row order as event order,
  - load `.mat` data with `h5py`,
  - treat raw data orientation as `time x channels`.

## Update In Progress

- Preparing I-DARE dataset loader / trial index builder.
- DEAP acquisition is still pending.

## Update Next Steps

1. Commit I-DARE probe scripts and reports.
2. Add D005 to `docs/decision_log.md`.
3. Refresh `docs/handoff_bundle_latest.md`.
4. Implement an I-DARE trial index builder.
5. Generate a clean machine-readable I-DARE trial index table.
6. Continue DEAP access/download process.
