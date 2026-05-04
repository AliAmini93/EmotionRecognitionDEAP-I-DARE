# Project State Delta - After I-DARE Trial Index Builder

## Add to Completed

- I-DARE trial index builder created:
  - `scripts/06_build_idare_trial_index.py`
- I-DARE trial index builder executed successfully.
- I-DARE trial index summary generated:
  - `docs/idare_trial_index_summary.md`
  - `docs/idare_trial_index_summary.json`
- Local regenerable trial index generated:
  - `.cache/idare_trial_index.csv`

## Important Note

`.cache/idare_trial_index.csv` is not tracked by git because `.cache/` is gitignored.

This is acceptable because the file is reproducible from:

```bash
python scripts/06_build_idare_trial_index.py
```

## Trial Index Result

```text
n_rows: 2016
n_subjects: 63
expected_subjects: 63
expected_rows: 2016
trials_per_subject_min: 32
trials_per_subject_max: 32
unique_stimuli: 32
issues: 0
warnings: 0
```

## Label Summary

Valence:

```text
score == 5 discard rows: 349
rows after discard: 1667
binary label 0 count: 812
binary label 1 count: 855
```

Arousal:

```text
score == 5 discard rows: 217
rows after discard: 1799
binary label 0 count: 1112
binary label 1 count: 687
```

## Update Current Goal

Finish the I-DARE loader path by validating real 5-second signal extraction from `.mat` files using the trial index.

## Update In Progress

- Preparing I-DARE window extraction smoke test.
- Next practical step:
  - create `scripts/07_smoke_idare_window_extraction.py`
  - generate `docs/idare_window_extraction_smoke_test.md`
  - generate `docs/idare_window_extraction_smoke_test.json`

## Update Next Steps

1. Commit current trial-index builder files:
   - `requirements.txt`
   - `scripts/06_build_idare_trial_index.py`
   - `docs/idare_trial_index_summary.md`
   - `docs/idare_trial_index_summary.json`
2. Commit this documentation delta.
3. Create I-DARE window extraction smoke test.
4. Validate exact sample slicing convention.
5. Validate EEG shape and EMG shape for extracted 5-second windows.
6. Decide whether to resample I-DARE EEG from 512Hz to 128Hz before the first model input.
7. Only after this, implement the reusable I-DARE dataset/loader code.
