# I-DARE Baseline-Correction Feasibility Audit

This diagnostic is metadata/cache-index only.

It does not train a model, build a cache, modify cache files, or load raw MATLAB/HDF5 files.

## Inputs

- stimuli_specs: `/mnt/HDD/AliWorks/I-DARE/metadata/Stimuli_Specifications.csv`
- cache_index: `.cache/idare_eeg_cache_index.csv`

## Stimuli Specifications Summary

- rows: `100`
- event/stimulus column: `Stimulus`
- subject duration columns: `64`
- STIM rows: `32`
- BSL_<stimulus> rows: `32`
- event kind counts: `{"BSL_GLOBAL": 1, "BSL_STIM": 32, "EYC": 1, "INSTRUCTION": 2, "SAM": 32, "STIM": 32}`

## Cache Index Summary

- rows: `2016`
- stimulus column: `stimulus_id`
- cached stimulus count: `32`
- baseline metadata evidence columns: `[]`
- baseline metadata interpretation: No explicit cache-index columns indicate baseline correction. This is not proof of absence in the NPY values, but there is no metadata evidence.

## Pair Feasibility Summary

| Check | Total | Pass | Fail | All pass |
|---|---:|---:|---:|---|
| Has STIM row | 32 | 32 | 0 | `true` |
| Has matching BSL row | 32 | 32 | 0 | `true` |
| BSL immediately before STIM | 32 | 32 | 0 | `true` |
| BSL mean duration 4.5-5.5s | 32 | 32 | 0 | `true` |
| STIM mean duration 4.5-5.5s | 32 | 32 | 0 | `true` |

## Per-Stimulus Pair Preview

| Stimulus | STIM idx | BSL idx | BSL before STIM | STIM mean sec | BSL mean sec |
|---|---:|---:|---|---:|---:|
| 1441 | 57 | 56 | `true` | 4.9979 | 4.9944 |
| 1750 | 51 | 50 | `true` | 4.9967 | 4.9973 |
| 2314 | 48 | 47 | `true` | 4.9971 | 4.9950 |
| 2491 | 72 | 71 | `true` | 4.9958 | 4.9977 |
| 3053 | 9 | 8 | `true` | 4.9973 | 4.9955 |
| 3063 | 96 | 95 | `true` | 4.9969 | 4.9953 |
| 3080 | 99 | 98 | `true` | 4.9969 | 4.9969 |
| 3170 | 81 | 80 | `true` | 4.9963 | 4.9972 |
| 4220 | 90 | 89 | `true` | 4.9970 | 4.9984 |
| 5760 | 93 | 92 | `true` | 4.9951 | 4.9959 |
| 8080 | 84 | 83 | `true` | 4.9960 | 4.9964 |
| 8370 | 36 | 35 | `true` | 4.9968 | 4.9970 |
| 8492 | 54 | 53 | `true` | 4.9964 | 4.9975 |
| 9220 | 42 | 41 | `true` | 4.9957 | 4.9966 |
| 9331 | 66 | 65 | `true` | 4.9965 | 4.9965 |
| 9360 | 75 | 74 | `true` | 4.9971 | 4.9970 |
| Angry_face_1 | 30 | 29 | `true` | 4.9980 | 4.9954 |
| Beach_1 | 69 | 68 | `true` | 4.9967 | 4.9973 |
| Depressed_pose_4 | 27 | 26 | `true` | 4.9965 | 4.9965 |
| Dog_18 | 15 | 14 | `true` | 4.9967 | 4.9972 |
| Dog_26 | 33 | 32 | `true` | 4.9969 | 4.9968 |
| Dog_6 | 39 | 38 | `true` | 4.9967 | 4.9971 |
| Dummy_1 | 6 | 5 | `true` | 4.9964 | 4.9961 |
| Flowers_6 | 60 | 59 | `true` | 4.9957 | 4.9959 |
| Garbage_dump_6 | 24 | 23 | `true` | 4.9968 | 4.9977 |
| Lake_12 | 45 | 44 | `true` | 4.9964 | 4.9967 |
| Lake_3 | 78 | 77 | `true` | 4.9968 | 4.9958 |
| Miserable_pose_3 | 18 | 17 | `true` | 4.9958 | 4.9973 |
| Pinecone_1 | 21 | 20 | `true` | 4.9968 | 4.9971 |
| Snow_1 | 87 | 86 | `true` | 4.9975 | 4.9971 |
| Tumor_1 | 12 | 11 | `true` | 4.9977 | 4.9974 |
| Yarn_1 | 63 | 62 | `true` | 4.9970 | 4.9962 |

## Feasibility Decision

- can_map_stim_to_bsl_for_all_audited_ids: `true`
- all_bsl_immediately_before_stim: `true`
- all_bsl_mean_durations_4p5_to_5p5: `true`
- all_stim_mean_durations_4p5_to_5p5: `true`
- feasible_for_future_baseline_corrected_cache: `true`

Recommendation: Feasible to build a separate baseline-corrected I-DARE EEG cache in a future step. Do not overwrite the current cache.

## Notes

- This audit only checks metadata/index feasibility.
- It does not inspect NPY signal values and cannot prove whether numerical baseline correction was already applied.
- A future baseline-corrected cache should be written to a new filename and smoke-tested before any broader run.
- Training loops should continue reading cache files only; raw MATLAB/HDF5 access should stay outside training.
