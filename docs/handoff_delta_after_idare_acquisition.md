# Handoff Delta - After Verified I-DARE Acquisition

Use this file as a compact addendum if the full handoff bundle has not yet been regenerated.

## New Completed Work

I-DARE first-stage acquisition is complete.

Downloaded files:

```text
133
```

Downloaded local root:

```text
/mnt/HDD/AliWorks/I-DARE
```

Downloaded subset:

```text
EEG files
EMG files
label CSV files
metadata CSV files
```

Verification result:

```text
selected_files: 133
selected_total_size: 6.88 GB
verified_ok: 133
verify_failed: 0
```

Local disk usage:

```text
6.9G /mnt/HDD/AliWorks/I-DARE
```

## Files to Commit

```text
docs/idare_acquisition_status.md
docs/idare_download_report.md
docs/project_state.md
docs/chat_handoff_latest.md
```

The handoff bundle should be regenerated after these files are added locally.

## Immediate Next Step

Create and run:

```text
scripts/01_audit_datasets.py
```

First audit target:

```text
I-DARE
```

Expected audit report:

```text
docs/data_audit_idare.md
```

DEAP acquisition is still pending.
