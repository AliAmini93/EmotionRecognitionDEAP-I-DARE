# Handoff Delta - After I-DARE Trial Index Builder

## What Changed

A reproducible I-DARE trial index builder was created and successfully executed.

New script:

```text
scripts/06_build_idare_trial_index.py
```

New documentation outputs:

```text
docs/idare_trial_index_summary.md
docs/idare_trial_index_summary.json
```

Generated local cache output:

```text
.cache/idare_trial_index.csv
```

Note:

```text
.cache/ is gitignored, so .cache/idare_trial_index.csv is not committed.
It can be regenerated from the script.
```

## Trial Index Result

The trial index creation passed with no issues and no warnings.

Core result:

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

This means the index contains:

```text
63 common EEG+EMG subjects × 32 emotional STIM trials = 2016 rows
```

## Label Result

Valence:

```text
total rows: 2016
score == 5 discard rows: 349
rows after discard: 1667
binary label 0 count: 812
binary label 1 count: 855
```

Arousal:

```text
total rows: 2016
score == 5 discard rows: 217
rows after discard: 1799
binary label 0 count: 1112
binary label 1 count: 687
```

## Duration Check

EEG:

```text
min duration: 4.982421875 s
max duration: 5.064453125 s
mean duration: 4.994547526041667 s
all trials in 4.5s to 5.5s range: true
```

EMG:

```text
min duration: 4.985 s
max duration: 5.067 s
mean duration: 4.996669642857143 s
all trials in 4.5s to 5.5s range: true
```

## Loader Assumptions Confirmed

- Use only `STIM_*` rows as emotional trials.
- Strip the `STIM_` prefix to match labels.
- Use the 63 common EEG+EMG subjects.
- Use `score > 5` as positive class.
- Mark `score == 5` as discard separately for valence and arousal.
- Preserve raw event begin/end values in the trial index.
- Final Python slicing convention should be finalized during window extraction.

## Immediate Next Step

Do not start training yet.

Next practical step:

```text
Create a small I-DARE window extraction smoke test.
```

Suggested next script:

```text
scripts/07_smoke_idare_window_extraction.py
```

The smoke test should:
1. Load `.cache/idare_trial_index.csv`.
2. Pick a few rows from subject 1.
3. Read EEG and EMG `.mat` files with `h5py`.
4. Extract the indexed 5-second EEG/EMG segment.
5. Confirm shapes and durations.
6. Decide final sample slicing convention.
7. Optionally resample EEG 512Hz to 128Hz for model compatibility.
8. Generate a report:
   - `docs/idare_window_extraction_smoke_test.md`
   - `docs/idare_window_extraction_smoke_test.json`

Still do not train models until the window extraction smoke test is clean.
