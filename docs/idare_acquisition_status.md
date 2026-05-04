# I-DARE Acquisition Status

## Status

I-DARE first-stage acquisition is complete.

Dataset files were downloaded into:

```text
/mnt/HDD/AliWorks/I-DARE
```

Downloaded first-stage subset:

```text
EEG files
EMG files
label CSV files
metadata CSV files
```

The download was performed using:

```text
scripts/download_idare_from_manifest.py
```

Source manifest:

```text
docs/idare_download_manifest.csv
```

Final verification report:

```text
docs/idare_download_report.md
```

---

## Final Verification Result

The full verification command was:

```bash
python scripts/download_idare_from_manifest.py --verify-only
```

Final result:

```text
selected_files: 133
selected_total_size: 6.88 GB
verified_ok: 133
verify_failed: 0
```

Downloaded file count:

```text
133
```

Local disk usage:

```text
6.9G /mnt/HDD/AliWorks/I-DARE
```

Available disk space after download:

```text
about 491G free on /mnt/HDD
```

---

## Local Folder Structure

Observed folder structure:

```text
/mnt/HDD/AliWorks/I-DARE
/mnt/HDD/AliWorks/I-DARE/labels
/mnt/HDD/AliWorks/I-DARE/metadata
/mnt/HDD/AliWorks/I-DARE/raw_downloads
/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG
/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG
```

---

## Downloaded Content

The first-stage I-DARE subset includes:

```text
EEG: 63 subject files
EMG: 64 subject files
Labels: 4 CSV files
Metadata: 2 CSV files
Total: 133 files
```

The downloaded subset excludes:

```text
SC&PPG modality
ET modality
Stimuli_Selection.pdf
```

These files are not required for the first EEG–EMG stage.

---

## Main Protocol Subject Decision

The main I-DARE protocol uses the 63 subjects with both EEG and EMG.

Subject 4 has EMG but no EEG and is excluded from the main EEG+EMG protocol.

Subject 4 remains downloaded and may be used only for optional EMG-only secondary analysis.

---

## Integrity Check

All first-stage downloaded files were verified using the checksum metadata stored in:

```text
docs/idare_download_manifest.csv
```

Verification result:

```text
verified_ok: 133
verification failures: 0
```

This means the local I-DARE first-stage files are ready for structural audit.

---

## Next Step

Create and run the dataset audit script:

```text
scripts/01_audit_datasets.py
```

The audit should inspect I-DARE first, because I-DARE has now been downloaded and verified.

DEAP acquisition is still pending.
