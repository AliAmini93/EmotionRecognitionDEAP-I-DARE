#!/usr/bin/env bash
# Fix and prepare EMG rerun for the broader I-DARE evaluation.
# This does not rerun training by itself.
# It:
# - patches scripts/30 so folds use the authorized seed 11 instead of the old fixed fold seed
# - commits only that script patch
# - creates /tmp/rerun_idare_broader_eval_emg_primary.sh

cd /mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE || exit 1

LOG=/tmp/idare_fix_prepare_emg_rerun.log

{
  echo "===== 0) start status ====="
  git status --short --branch
  echo

  PY=".venv/bin/python"
  if [ ! -x "$PY" ]; then PY="python3"; fi
  echo "PY=$PY"
  echo

  echo "===== 1) patch script 30 fold seed usage ====="
  "$PY" - <<'PY'
from pathlib import Path
import re

path = Path("scripts/30_run_idare_emg_feature_smoke.py")
text = path.read_text(encoding="utf-8")
old = text

# Keep the sidecar-compatible np.default_rng splitter if it was already added.
if "sidecar-compatible numpy.default_rng" not in text:
    lines = text.splitlines(keepends=True)
    start = None
    for i, line in enumerate(lines):
        if line.startswith("def make_subject_folds("):
            start = i
            break
    if start is None:
        raise SystemExit("ERROR: make_subject_folds not found")

    end = None
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("def ") or lines[j].startswith("class "):
            end = j
            break
    if end is None:
        raise SystemExit("ERROR: make_subject_folds end not found")

    block = [
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
    text = "".join(lines[:start] + block + lines[end:])

# The previous script can still call make_subject_folds with a fixed fold seed.
# For the authorized matrix, folds must use the authorized seed argument.
patterns = [
    (r"make_subject_folds\(([^,\n]+),\s*args\.folds,\s*20260505\)", r"make_subject_folds(\1, args.folds, args.seeds[0])"),
    (r"make_subject_folds\(([^,\n]+),\s*args\.folds,\s*seed=20260505\)", r"make_subject_folds(\1, args.folds, seed=args.seeds[0])"),
    (r"make_subject_folds\(([^,\n]+),\s*args\.folds,\s*int\(20260505\)\)", r"make_subject_folds(\1, args.folds, args.seeds[0])"),
]
changed_seed = False
for pat, repl in patterns:
    text2, n = re.subn(pat, repl, text)
    if n:
        changed_seed = True
        text = text2

# A conservative fallback for the exact common line.
exact = "folds = make_subject_folds(subjects, args.folds, 20260505)"
if exact in text:
    text = text.replace(exact, "folds = make_subject_folds(subjects, args.folds, args.seeds[0])")
    changed_seed = True

if text == old:
    print("NO_CHANGE_TO_SCRIPT30")
else:
    path.write_text(text, encoding="utf-8")
    print("PATCHED_SCRIPT30")

# Fail if the old fixed fold seed is still used in make_subject_folds call context.
if "make_subject_folds(subjects, args.folds, 20260505)" in text:
    raise SystemExit("ERROR: fixed fold seed still present")
PY
  echo

  echo "===== 2) inspect fold related lines ====="
  grep -n "make_subject_folds(subjects" scripts/30_run_idare_emg_feature_smoke.py || true
  grep -n "20260505" scripts/30_run_idare_emg_feature_smoke.py || true
  echo

  echo "===== 3) compile and verify authorized fold1 ====="
  "$PY" -B -m py_compile scripts/30_run_idare_emg_feature_smoke.py
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
    for row in csv.DictReader(f):
        subjects.add(int(row["subject_id"]))

folds = mod.make_subject_folds(sorted(subjects), 6, 11)
expected = [6, 7, 8, 13, 28, 38, 43, 54, 58, 59, 65]
print("script30_fold1_seed11:", folds[0].val_subjects)
print("expected_sidecar_fold1:", expected)
if folds[0].val_subjects != expected:
    raise SystemExit("ERROR: script30 seed11 fold1 still mismatched")
print("OK_SCRIPT30_SEED11_FOLD_MATCH")
PY
  echo

  echo "===== 4) commit script patch if changed ====="
  if git diff --quiet -- scripts/30_run_idare_emg_feature_smoke.py; then
    echo "NO_SCRIPT30_DIFF_TO_COMMIT"
  else
    git diff --stat -- scripts/30_run_idare_emg_feature_smoke.py
    git diff -- scripts/30_run_idare_emg_feature_smoke.py | sed -n '1,180p'
    git add scripts/30_run_idare_emg_feature_smoke.py
    git commit -m "fix: use authorized seed for I-DARE EMG feature folds"
    echo "PATCH_COMMIT_EXIT=$?"
  fi
  echo

  echo "===== 5) create EMG rerun script ====="
  cat > /tmp/rerun_idare_broader_eval_emg_primary.sh <<'RUN'
#!/usr/bin/env bash
# Rerun only EMG B0 and EMG B1 for the broader I-DARE primary matrix.
# This overwrites prior EMG broader-eval outputs.
# It does not commit or push.

cd /mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE || exit 1

LOG=/tmp/idare_broader_eval_emg_rerun.log

{
  echo "===== 0) start EMG rerun ====="
  date -u
  git status --short --branch
  echo

  PY=".venv/bin/python"
  if [ ! -x "$PY" ]; then PY="python3"; fi
  echo "PY=$PY"

  echo "===== 1) remove previous invalid EMG broader-eval outputs ====="
  rm -f \
    docs/idare_broader_eval_emg_feature_only_primary.md \
    docs/idare_broader_eval_emg_feature_only_primary.json \
    docs/idare_broader_eval_emg_feature_only_primary_predictions.csv \
    docs/idare_broader_eval_emg_bsl_stats_primary.md \
    docs/idare_broader_eval_emg_bsl_stats_primary.json \
    docs/idare_broader_eval_emg_bsl_stats_primary_predictions.csv
  echo "OK_REMOVED_OLD_EMG_OUTPUTS"
  echo

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
      echo "ERROR: $name failed. Stop."
      exit "$code"
    fi
  }

  run_cmd "EMG_B0_FEATURE_ONLY_RERUN" \
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

  run_cmd "EMG_B1_FEATURE_PLUS_BSL_STATS_RERUN" \
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
      --max-runs 24 \
      --out-md docs/idare_broader_eval_emg_bsl_stats_primary.md \
      --out-json docs/idare_broader_eval_emg_bsl_stats_primary.json \
      --out-predictions-csv docs/idare_broader_eval_emg_bsl_stats_primary_predictions.csv

  echo
  echo "===== validate EMG outputs ====="
  for f in \
    docs/idare_broader_eval_emg_feature_only_primary.json \
    docs/idare_broader_eval_emg_bsl_stats_primary.json
  do
    "$PY" -m json.tool "$f" >/dev/null
    echo "OK_JSON: $f"
  done

  "$PY" - <<'PY'
import json
from pathlib import Path

for p in [
    Path("docs/idare_broader_eval_emg_feature_only_primary.json"),
    Path("docs/idare_broader_eval_emg_bsl_stats_primary.json"),
]:
    data = json.loads(p.read_text(encoding="utf-8"))
    runs = data.get("runs", [])
    print(p.name, "n_runs=", len(runs), "status=", data.get("status"))
    if len(runs) != 24:
        raise SystemExit(f"ERROR: {p} expected 24 runs, got {len(runs)}")
    first = runs[0]
    print("  first_run=", {
        "task": first.get("task"),
        "recipe": first.get("recipe"),
        "fold_id": first.get("fold_id") or first.get("fold"),
        "seed": first.get("seed"),
        "val_subjects": first.get("val_subjects"),
    })
PY

  ls -lh docs/idare_broader_eval_emg_*_primary* 2>/dev/null || true

  echo
  echo "===== final status ====="
  git status --short --branch
  echo
  echo "EMG_RERUN_DONE"
  date -u
} > "$LOG" 2>&1

cat "$LOG"
echo "LOG_SAVED_TO=$LOG"
RUN

  chmod +x /tmp/rerun_idare_broader_eval_emg_primary.sh
  echo "RERUN_SCRIPT=/tmp/rerun_idare_broader_eval_emg_primary.sh"
  echo

  echo "===== 6) final status ====="
  git status --short --branch
  echo
  echo "NEXT:"
  echo "1) If ahead, push the script patch."
  echo "2) Then run: bash /tmp/rerun_idare_broader_eval_emg_primary.sh"
  echo "3) If terminal closes, run: cat /tmp/idare_broader_eval_emg_rerun.log"
} > "$LOG" 2>&1

cat "$LOG"
echo "LOG_SAVED_TO=$LOG"
