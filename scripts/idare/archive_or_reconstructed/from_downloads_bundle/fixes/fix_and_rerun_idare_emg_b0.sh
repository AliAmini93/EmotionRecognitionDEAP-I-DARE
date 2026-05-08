#!/usr/bin/env bash
# Fix script30 fold call and rerun ONLY EMG feature-only broader evaluation.
# This:
# - patches scripts/30_run_idare_emg_feature_smoke.py so folds use args.seeds[0]
# - commits the patch if needed
# - reruns EMG-B0 only and overwrites its previous invalid broader-eval outputs
# - does NOT commit/push generated reports

cd /mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE || exit 1

LOG=/tmp/idare_fix_and_rerun_emg_b0.log

{
  echo "===== 0) start status ====="
  git status --short --branch
  echo

  PY=".venv/bin/python"
  if [ ! -x "$PY" ]; then PY="python3"; fi
  echo "PY=$PY"
  echo

  echo "===== 1) patch script30 call-site seed ====="
  "$PY" - <<'PY'
from pathlib import Path

path = Path("scripts/30_run_idare_emg_feature_smoke.py")
text = path.read_text(encoding="utf-8")
old = text

# The broader evaluation must use the authorized seed from --seeds.
# Current stale call-site may still use seed=20240506.
text = text.replace(
    "folds = make_subject_folds(subjects, args.folds, seed=20240506)",
    "folds = make_subject_folds(subjects, args.folds, seed=args.seeds[0])",
)
text = text.replace(
    "folds = make_subject_folds(subjects, args.folds, 20240506)",
    "folds = make_subject_folds(subjects, args.folds, args.seeds[0])",
)

if text == old:
    print("NO_TEXT_REPLACEMENT_MADE")
else:
    path.write_text(text, encoding="utf-8")
    print("PATCHED_SCRIPT30_CALL_SITE")

if "seed=20240506" in text or "args.folds, 20240506" in text:
    raise SystemExit("ERROR: stale fixed fold seed still present")
PY
  echo

  echo "===== 2) inspect/compile ====="
  grep -n "make_subject_folds(subjects" scripts/30_run_idare_emg_feature_smoke.py || true
  grep -n "20240506\|20260505" scripts/30_run_idare_emg_feature_smoke.py || true
  "$PY" -B -m py_compile scripts/30_run_idare_emg_feature_smoke.py
  echo "OK_COMPILE_SCRIPT30"
  echo

  echo "===== 3) commit script patch if changed ====="
  if git diff --quiet -- scripts/30_run_idare_emg_feature_smoke.py; then
    echo "NO_SCRIPT30_DIFF_TO_COMMIT"
  else
    git diff --stat -- scripts/30_run_idare_emg_feature_smoke.py
    git diff -- scripts/30_run_idare_emg_feature_smoke.py | sed -n '1,120p'
    git add scripts/30_run_idare_emg_feature_smoke.py
    git commit -m "fix: use requested seed for I-DARE EMG feature folds"
    echo "PATCH_COMMIT_EXIT=$?"
  fi
  echo

  echo "===== 4) remove invalid EMG feature-only outputs ====="
  rm -f \
    docs/idare_broader_eval_emg_feature_only_primary.md \
    docs/idare_broader_eval_emg_feature_only_primary.json \
    docs/idare_broader_eval_emg_feature_only_primary_predictions.csv
  echo "OK_REMOVED_EMG_B0_OUTPUTS"
  echo

  echo "===== 5) rerun EMG-B0 feature-only with authorized folds ====="
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
    --max-runs 24 \
    --out-md docs/idare_broader_eval_emg_feature_only_primary.md \
    --out-json docs/idare_broader_eval_emg_feature_only_primary.json \
    --out-predictions-csv docs/idare_broader_eval_emg_feature_only_primary_predictions.csv
  echo "EMG_B0_RERUN_EXIT=$?"
  echo

  echo "===== 6) validate EMG-B0 output ====="
  "$PY" -m json.tool docs/idare_broader_eval_emg_feature_only_primary.json >/dev/null
  echo "OK_JSON_EMG_B0"

  "$PY" - <<'PY'
import json
from pathlib import Path

p = Path("docs/idare_broader_eval_emg_feature_only_primary.json")
data = json.loads(p.read_text(encoding="utf-8"))
runs = data.get("runs", [])
print("n_runs=", len(runs))
if len(runs) != 24:
    raise SystemExit(f"ERROR: expected 24 runs, got {len(runs)}")
first = runs[0]
val_subjects = first.get("val_subjects")
print("first_run=", {
    "task": first.get("task"),
    "recipe": first.get("recipe"),
    "fold_id": first.get("fold_id") or first.get("fold"),
    "seed": first.get("seed"),
    "val_subjects": val_subjects,
})
expected = [6, 7, 8, 13, 28, 38, 43, 54, 58, 59, 65]
if val_subjects != expected:
    raise SystemExit(f"ERROR: EMG-B0 fold1 still mismatched: {val_subjects}")
print("OK_EMG_B0_FOLD1_MATCHES_BSL_STATS")
PY

  ls -lh docs/idare_broader_eval_emg_feature_only_primary*
  echo

  echo "===== 7) final status ====="
  git status --short --branch
  echo
  echo "DONE_FIX_AND_EMG_B0_RERUN"
} > "$LOG" 2>&1

cat "$LOG"
echo "LOG_SAVED_TO=$LOG"
