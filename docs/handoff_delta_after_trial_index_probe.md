# Handoff Delta — After I-DARE Trial Index Probe

## New Completed Work

The I-DARE trial/event alignment was probed using:

```text
scripts/05_probe_idare_trial_index.py
```

Generated outputs:

```text
docs/idare_trial_index_probe.md
docs/idare_trial_index_probe.json
```

## Main Findings

The probe confirmed:

```text
Stimuli_Specifications.csv rows: 100
I-DARE .mat event_begin/event_end pairs: 100
STIM_* rows: 32
Label stimulus IDs: 32
stim_rows_match_label_stimuli: true
```

Sample subjects checked:

```text
sbj_P_01
sbj_P_02
sbj_P_03
```

For each sampled subject:

```text
stim_rows_count: 32
labeled_stim_rows_count: 32
all_labeled_stim_eeg_4p5_to_5p5: true
all_labeled_stim_emg_4p5_to_5p5: true
```

## I-DARE Loader Design Decision

Use only `STIM_*` rows as emotional trials.

Do not use `BSL_*` or `SAM_*` rows as emotion-classification samples.

Map labels by stripping the `STIM_` prefix:

```text
STIM_3053 -> 3053
STIM_Dog_18 -> Dog_18
```

Use the row order in `Stimuli_Specifications.csv` as the event order for `event_begin` and `event_end`.

## Current Candidate Loader Design

1. Load `.mat` files with `h5py`.
2. Use raw `h5py` data orientation:
   - EEG: `time x channels`
   - EMG: `time x channels`
3. Use the 63 common EEG+EMG subjects for the main protocol.
4. For each subject:
   - read EEG file,
   - read EMG file,
   - read `Stimuli_Specifications.csv`,
   - keep only `STIM_*` rows,
   - extract matching EEG and EMG event windows,
   - attach valence and arousal scores from label CSV files.
5. Apply binary label rule:
   - score > 5 -> 1
   - score < 5 -> 0
   - score == 5 -> discard for that specific task
6. EEG will later be resampled from 512Hz to 128Hz.
7. EMG will be converted to feature-level descriptors.

## Immediate Next Step

Commit the probe scripts/reports and decision update, then update the handoff bundle.

After that, begin implementing the actual I-DARE trial index builder / dataset loader.

Do not start model training yet.
