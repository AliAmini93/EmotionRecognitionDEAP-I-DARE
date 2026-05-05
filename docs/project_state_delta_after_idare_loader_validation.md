# Project State Delta - After I-DARE Loader Validation

## Add to Completed

- I-DARE PyTorch loader added:
  - `src/emotion_deap_idare/datasets/__init__.py`
  - `src/emotion_deap_idare/datasets/idare_loader.py`
- I-DARE loader validation added and executed:
  - `scripts/08_validate_idare_loader.py`
  - `docs/idare_loader_validation.md`
  - `docs/idare_loader_validation.json`
- I-DARE loader status documented:
  - `docs/idare_loader_status.md`
- I-DARE loader validation result:
  - Status: PASSED
  - Issues: 0
  - Warnings: 0
  - Valence rows after discard: 1667
  - Arousal rows after discard: 1799
  - EEG batch shape: `[4, 32, 640]`
  - EMG batch shape: `[4, 2, 10000]`
- Decision D008 accepted:
  - Use `IDARETrialDataset` as I-DARE loader v1 for controlled baseline smoke tests.

## Update Current Goal

Finish the first controlled I-DARE EEG-only model-forward smoke test before any full LOSO training.

## Update In Progress

- I-DARE acquisition, audit, trial index, signal extraction smoke test, and loader validation are complete.
- Next practical step:
  - create `scripts/09_smoke_idare_eeg_model_forward.py`
  - run a small EEG-only forward/loss/optimizer-step smoke test using `EEGSegmentClassifier-v1`

## Update Next Steps

1. Commit the I-DARE loader and validation reports.
2. Create:
   - `scripts/09_smoke_idare_eeg_model_forward.py`
3. Run EEG-only model-forward smoke test:
   - I-DARE `IDARETrialDataset`
   - task: valence first
   - batch EEG shape: `[B, 32, 640]`
   - model: `EEGSegmentClassifier-v1`
   - output logits shape: `[B, 2]`
   - compute CrossEntropyLoss
   - run one optimizer step
4. Generate:
   - `docs/idare_eeg_model_forward_smoke_test.md`
   - `docs/idare_eeg_model_forward_smoke_test.json`
5. Only after this smoke test passes, consider the first very small training-loop dry run.
6. Continue DEAP acquisition separately:
   - confirm/request official DEAP access
   - download `Data_preprocessed_python.zip`
   - audit DEAP before any DEAP experiments
