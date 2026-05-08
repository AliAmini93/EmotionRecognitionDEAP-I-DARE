#!/usr/bin/env bash
# Prepare the broader I-DARE single-modality evaluation run.
# This script does NOT run the 96-run matrix.
# It does:
# - preflight checks
# - a limited fold-alignment patch for scripts/30 if needed
# - local commit for that patch if needed
# - creates /tmp/run_idare_broader_eval_primary_matrix.sh

cd /mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE || exit 1

LOG=/tmp/idare_prepare_broader_eval_run.log

{
  echo "===== 0) start status ====="
  git status --short --branch
  echo

  PY=".venv/bin/python"
  if [ ! -x "$PY" ]; then
    PY="python3"
  fi
  echo "PY=$PY"
  "$PY" - <<'PY'
import sys
print(sys.executable)
import numpy, pandas, torch
print("OK_IMPORTS")
PY
  echo

  echo "===== 1) require clean repo before prep ====="
  if [ -n "$(git status --porcelain)" ]; then
    echo "ERROR: repo is not clean. Stop before prep."
    git status --short --branch
    exit 1
  fi
  echo "OK_REPO_CLEAN"
  echo

  echo "===== 2) check required local caches ====="
  missing=0
  for f in \
    .cache/idare_eeg_windows_32x640_float32_baseline_corrected.npy \
    .cache/idare_eeg_cache_index_baseline_corrected.csv \
    .cache/idare_eeg_bsl_stats.npy \
    .cache/idare_eeg_bsl_stats_index.csv \
    .cache/idare_emg_features.npy \
    .cache/idare_emg_feature_cache_index.csv \
    .cache/idare_emg_bsl_stats.npy \
    .cache/idare_emg_bsl_stats_index.csv
  do
    if [ -f "$f" ]; then
      ls -lh "$f"
    else
      echo "MISSING: $f"
      missing=1
    fi
  done
  if [ "$missing" -ne 0 ]; then
    echo "ERROR: required cache missing"
    exit 1
  fi
  echo

  echo "===== 3) check scripts exist and compile ====="
  for s in \
    scripts/20_run_idare_eeg_cache_recipe_stabilization.py \
    scripts/34_run_idare_eeg_bsl_stats_ablation_smoke.py \
    scripts/30_run_idare_emg_feature_smoke.py \
    scripts/36_run_idare_emg_bsl_stats_ablation_smoke.py
  do
    if [ ! -f "$s" ]; then
      echo "ERROR: missing script $s"
      exit 1
    fi
    "$PY" -B -m py_compile "$s" || exit 1
    echo "OK_COMPILE: $s"
  done
  echo

  echo "===== 4) limited patch: align script 30 fold splitter with sidecar RNG ====="
  "$PY" - <<'PY'
from pathlib import Path

path = Path("scripts/30_run_idare_emg_feature_smoke.py")
text = path.read_text(encoding="utf-8")

if "sidecar-compatible numpy.default_rng" in text:
    print("OK_ALREADY_PATCHED")
    raise SystemExit(0)

lines = text.splitlines(keepends=True)
start = None
for i, line in enumerate(lines):
    if line.startswith("def make_subject_folds("):
        start = i
        break
if start is None:
    raise SystemExit("ERROR: make_subject_folds not found in script 30")

end = None
for j in range(start + 1, len(lines)):
    if lines[j].startswith("def ") or lines[j].startswith("class "):
        end = j
        break
if end is None:
    raise SystemExit("ERROR: could not find end of make_subject_folds in script 30")

new_block = [
    "def make_subject_folds(subjects: list[int], n_folds: int, seed: int) -> list[Fold]:\n",
    "    \"\"\"Build sidecar-compatible numpy.default_rng subject folds.\n",
    "\n",
    "    This keeps I-DARE EMG feature-only broader-eval folds aligned with\n",
    "    scripts/36_run_idare_emg_bsl_stats_ablation_smoke.py.\n",
    "    \"\"\"\n",
    "    subjects = sorted({int(s) for s in subjects})\n",
    "    if n_folds < 2:\n",
    "        raise ValueError(\"--folds must be >= 2\")\n",
    "    if n_folds > len(subjects):\n",
    "        raise ValueError(f\"--folds={n_folds} exceeds subject count={len(subjects)}\")\n",
    "    rng = np.random.default_rng(int(seed))\n",
    "    shuffled = np.asarray(subjects, dtype=int)\n",
    "    rng.shuffle(shuffled)\n",
    "    chunks = [list(chunk) for chunk in np.array_split(shuffled, n_folds)]\n",
    "    all_subjects = set(subjects)\n",
    "    folds: list[Fold] = []\n",
    "    for i, chunk in enumerate(chunks, start=1):\n",
    "        val_subjects = sorted(int(x) for x in chunk)\n",
    "        train_subjects = sorted(all_subjects - set(val_subjects))\n",
    "        folds.append(Fold(fold_id=i, val_subjects=val_subjects, train_subjects=train_subjects))\n",
    "    return folds\n",
    "\n",
]
path.write_text("".join(lines[:start] + new_block + lines[end:]), encoding="utf-8")
print(f"PATCHED script 30 lines {start+1}-{end}")
PY
  echo

  echo "===== 5) verify patch/compile/fold alignment ====="
  "$PY" -B -m py_compile scripts/30_run_idare_emg_feature_smoke.py || exit 1
  echo "OK_COMPILE_SCRIPT30"

  "$PY" - <<'PY'
from pathlib import Path
import csv
import importlib.util
import sys

script = Path("scripts/30_run_idare_emg_feature_smoke.py")
spec = importlib.util.spec_from_file_location("s30", script)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

subjects = set()
with Path(".cache/idare_emg_feature_cache_index.csv").open(newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        subjects.add(int(row["subject_id"]))

folds = mod.make_subject_folds(sorted(subjects), 6, 11)
expected = [6, 7, 8, 13, 28, 38, 43, 54, 58, 59, 65]
print("script30_fold1:", folds[0].val_subjects)
print("expected_sidecar_fold1:", expected)
if folds[0].val_subjects != expected:
    raise SystemExit("ERROR: script30 fold1 does not match sidecar-compatible fold1")
print("OK_SCRIPT30_FOLD_MATCH")
PY
  echo

  echo "===== 6) check CLI support ====="
  scripts=(
    scripts/20_run_idare_eeg_cache_recipe_stabilization.py
    scripts/34_run_idare_eeg_bsl_stats_ablation_smoke.py
    scripts/30_run_idare_emg_feature_smoke.py
    scripts/36_run_idare_emg_bsl_stats_ablation_smoke.py
  )
  for s in "${scripts[@]}"; do
    echo "--- $s --help key args ---"
    "$PY" "$s" --help | grep -E -- '--tasks|--recipes|--folds|--seeds|--epochs|--batch-size|--max-runs|--out-md|--out-json|--out-predictions-csv' || true
  done
  echo

  echo "===== 7) commit limited patch if needed ====="
  if git diff --quiet -- scripts/30_run_idare_emg_feature_smoke.py; then
    echo "NO_SCRIPT_PATCH_TO_COMMIT"
  else
    git diff --stat -- scripts/30_run_idare_emg_feature_smoke.py
    git diff -- scripts/30_run_idare_emg_feature_smoke.py | sed -n '1,140p'
    git add scripts/30_run_idare_emg_feature_smoke.py
    git commit -m "fix: align I-DARE EMG feature folds for broader eval"
    echo "PATCH_COMMIT_EXIT=$?"
  fi
  echo

  echo "===== 8) create reviewed runner script for 96-run primary matrix ====="
  cat > /tmp/run_idare_broader_eval_primary_matrix.sh <<'RUN'
#!/usr/bin/env bash
# Run the authorized 96-run I-DARE broader standardized single-modality primary matrix.
# This runs training. It does NOT commit or push.
# Log: /tmp/idare_broader_eval_primary_matrix_run.log

cd /mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE || exit 1

LOG=/tmp/idare_broader_eval_primary_matrix_run.log

{
  echo "===== 0) start broader primary matrix run ====="
  date -u
  git status --short --branch
  echo

  PY=".venv/bin/python"
  if [ ! -x "$PY" ]; then
    PY="python3"
  fi
  echo "PY=$PY"
  "$PY" - <<'PY'
import sys
print(sys.executable)
import numpy, pandas, torch
print("OK_IMPORTS")
print("cuda_available=", torch.cuda.is_available())
PY
  echo

  if [ -n "$(git status --porcelain)" ]; then
    echo "ERROR: repo is not clean. Commit/push prep patch before running."
    git status --short --branch
    exit 1
  fi

  run_cmd() {
    name="$1"
    shift
    echo
    echo "===== RUN: $name ====="
    date -u
    "$@"
    code=$?
    echo "EXIT_$name=$code"
    date -u
    if [ "$code" -ne 0 ]; then
      echo "ERROR: $name failed. Stop matrix."
      exit "$code"
    fi
  }

  run_cmd "EEG_B0_STIM_BSL_ONLY" \
    "$PY" scripts/20_run_idare_eeg_cache_recipe_stabilization.py \
      --cache-npy .cache/idare_eeg_windows_32x640_float32_baseline_corrected.npy \
      --cache-index .cache/idare_eeg_cache_index_baseline_corrected.csv \
      --tasks valence arousal \
      --label-policy midpoint_as_high \
      --recipes ce_class_weighted balanced_sampler_ce \
      --folds 6 \
      --seeds 11 \
      --epochs 12 \
      --lr 1e-3 \
      --batch-size 64 \
      --weight-decay 1e-3 \
      --grad-clip 1.0 \
      --max-runs 0 \
      --out-md docs/idare_broader_eval_eeg_stim_bsl_only_primary.md \
      --out-json docs/idare_broader_eval_eeg_stim_bsl_only_primary.json \
      --out-predictions-csv docs/idare_broader_eval_eeg_stim_bsl_only_primary_predictions.csv

  run_cmd "EEG_B1_STIM_BSL_PLUS_BSL_STATS" \
    "$PY" scripts/34_run_idare_eeg_bsl_stats_ablation_smoke.py \
      --eeg-npy .cache/idare_eeg_windows_32x640_float32_baseline_corrected.npy \
      --eeg-index .cache/idare_eeg_cache_index_baseline_corrected.csv \
      --bsl-stats-npy .cache/idare_eeg_bsl_stats.npy \
      --bsl-stats-index .cache/idare_eeg_bsl_stats_index.csv \
      --tasks valence arousal \
      --label-policy midpoint_as_high \
      --recipes ce_class_weighted balanced_sampler_ce \
      --folds 6 \
      --seeds 11 \
      --epochs 12 \
      --lr 1e-3 \
      --batch-size 64 \
      --max-runs 0 \
      --out-md docs/idare_broader_eval_eeg_bsl_stats_primary.md \
      --out-json docs/idare_broader_eval_eeg_bsl_stats_primary.json \
      --out-predictions-csv docs/idare_broader_eval_eeg_bsl_stats_primary_predictions.csv

  run_cmd "EMG_B0_FEATURE_ONLY" \
    "$PY" scripts/30_run_idare_emg_feature_smoke.py \
      --feature-npy .cache/idare_emg_features.npy \
      --feature-index .cache/idare_emg_feature_cache_index.csv \
      --tasks valence arousal \
      --label-policy midpoint_as_high \
      --recipes ce_class_weighted balanced_sampler_ce \
      --folds 6 \
      --seeds 11 \
      --epochs 20 \
      --lr 1e-3 \
      --batch-size 128 \
      --weight-decay 1e-3 \
      --grad-clip 1.0 \
      --hidden-dim 64 \
      --max-runs 0 \
      --out-md docs/idare_broader_eval_emg_feature_only_primary.md \
      --out-json docs/idare_broader_eval_emg_feature_only_primary.json \
      --out-predictions-csv docs/idare_broader_eval_emg_feature_only_primary_predictions.csv

  run_cmd "EMG_B1_FEATURE_PLUS_BSL_STATS" \
    "$PY" scripts/36_run_idare_emg_bsl_stats_ablation_smoke.py \
      --feature-npy .cache/idare_emg_features.npy \
      --feature-index .cache/idare_emg_feature_cache_index.csv \
      --bsl-stats-npy .cache/idare_emg_bsl_stats.npy \
      --bsl-stats-index .cache/idare_emg_bsl_stats_index.csv \
      --tasks valence arousal \
      --label-policy midpoint_as_high \
      --recipes ce_class_weighted balanced_sampler_ce \
      --folds 6 \
      --seeds 11 \
      --epochs 20 \
      --lr 1e-3 \
      --batch-size 128 \
      --hidden-dim 64 \
      --zclip 8.0 \
      --max-runs 0 \
      --out-md docs/idare_broader_eval_emg_bsl_stats_primary.md \
      --out-json docs/idare_broader_eval_emg_bsl_stats_primary.json \
      --out-predictions-csv docs/idare_broader_eval_emg_bsl_stats_primary_predictions.csv

  echo
  echo "===== validate generated outputs ====="
  for f in \
    docs/idare_broader_eval_eeg_stim_bsl_only_primary.json \
    docs/idare_broader_eval_eeg_bsl_stats_primary.json \
    docs/idare_broader_eval_emg_feature_only_primary.json \
    docs/idare_broader_eval_emg_bsl_stats_primary.json
  do
    "$PY" -m json.tool "$f" >/dev/null || exit 1
    echo "OK_JSON: $f"
  done

  ls -lh docs/idare_broader_eval_*_primary* 2>/dev/null || true

  echo
  echo "===== final status ====="
  git status --short --branch

  echo
  echo "MATRIX_RUN_DONE"
  date -u
} > "$LOG" 2>&1

cat "$LOG"
echo "LOG_SAVED_TO=$LOG"
RUN

  chmod +x /tmp/run_idare_broader_eval_primary_matrix.sh
  echo "RUNNER_CREATED=/tmp/run_idare_broader_eval_primary_matrix.sh"
  echo

  echo "===== 9) final status ====="
  git status --short --branch
  echo
  echo "NEXT:"
  echo "1) If status says [ahead 1], push the fold-alignment patch first."
  echo "2) Then run: bash /tmp/run_idare_broader_eval_primary_matrix.sh"
  echo "3) If terminal closes, run: cat /tmp/idare_broader_eval_primary_matrix_run.log"
} > "$LOG" 2>&1

cat "$LOG"
echo "LOG_SAVED_TO=$LOG"
