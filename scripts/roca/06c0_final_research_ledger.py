#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path('.')
PREFIX = ROOT / 'docs/roca/idare_06c0_final_research_ledger_current'

KEY_FILES = {
    'final_root_cause': ROOT / 'docs/roca/idare_06a7_final_loso_root_cause_report_current_decision_table.csv',
    'calibration_conclusion': ROOT / 'docs/roca/idare_06a7b_calibration_dominant_conclusion_current_conclusion_table.csv',
    'consolidated_synthesis': ROOT / 'docs/roca/idare_06b3_final_consolidated_roca_synthesis_current_decision_table.csv',
    'gaussian_locked_rerun': ROOT / 'docs/roca/idare_06a5b_gaussian10_locked_gate_rerun_current_decision_table.csv',
    'neural_anchor': ROOT / 'docs/roca/idare_06a6_neural_anchor_fixed_bandpower_current_decision_table.csv',
    'kshot_locked_bridge': ROOT / 'docs/roca/idare_06a4b_kshot_calibration_locked_bridge_confirm_current_decision_table.csv',
    'branch_consolidation': ROOT / 'docs/roca/idare_06b0_branch_consolidation_compact_audit_current_decision_table.csv',
}

MANUAL_PHASES = [
    {
        'phase': '00_git_state',
        'status': 'complete',
        'summary': 'ROCA is the active research branch; main was restored after accidental merge; historical branches were merged into ROCA and archived/deleted remotely.',
        'evidence': 'origin/roca-idare-killtest plus archive tags',
    },
    {
        'phase': '01_baselines_and_labels',
        'status': 'complete',
        'summary': 'Stimulus-only and label/task protocol baselines established; old literature-level LOSO difficulty was confirmed in this project-specific protocol.',
        'evidence': 'docs/roca/stimulus_only_baseline_current.*, docs/idare_label_task_protocol_*',
    },
    {
        'phase': '02_emg_only',
        'status': 'complete_negative',
        'summary': 'EMG-only, expanded EMG, nonlinear EMG, and augmented EMG probes did not rescue strict LOSO residual emotion recognition.',
        'evidence': 'docs/roca/emg_*_current.*, docs/idare_w1c_emg_baseline_*',
    },
    {
        'phase': '03_eeg_raw_deep',
        'status': 'complete_negative',
        'summary': 'Raw EEG residual/deep attempts, model-asset checks, residual training, multitask/sign auxiliary and oracle diagnostics did not provide a locked-gate global LOSO solution.',
        'evidence': 'docs/roca/eeg_*_current.*, docs/roca/idare_06a*_current.*',
    },
    {
        'phase': '04_augmentation',
        'status': 'complete_negative_under_locked_gate',
        'summary': 'Old gaussian_0p10 evidence was promising but non-comparable; clean locked rerun showed Gaussian augmentation does not fix LOSO.',
        'evidence': 'idare_06a5 and idare_06a5b reports',
    },
    {
        'phase': '05_calibration_personalization',
        'status': 'partial_positive_but_claim_shift',
        'summary': 'Subject calibration/k-shot/bias correction helped more than blind global models, but this changes the claim from pure zero-calibration LOSO to calibrated/personalized/adaptation-assisted recognition.',
        'evidence': 'idare_06a4b, 05aa-05af, personalization bridge reports',
    },
    {
        'phase': '06_final_conclusion',
        'status': 'locked_current_conclusion',
        'summary': 'Strict LOSO global raw EEG/EMG residual decoding remains unsupported by locked gates. The dominant issue is subject calibration/domain shift plus weak transferable residual identifiability.',
        'evidence': 'idare_06a7, idare_06a7b, idare_06b3 reports',
    },
]

REMAINING_ACTIONS = [
    {
        'priority': 1,
        'action': 'Generate paper/report claim section',
        'why': 'Turn the negative/partial-positive evidence into a defensible scientific narrative.',
        'success_condition': 'The text clearly separates pure LOSO failure from calibrated/personalized positive direction.',
    },
    {
        'priority': 2,
        'action': 'Choose exactly one next positive route',
        'why': 'Avoid another month of broad architecture search.',
        'success_condition': 'Route is either calibration-budget, UDA with unlabeled target data, or explicitly personalized EEG+EMG fusion.',
    },
    {
        'priority': 3,
        'action': 'Define allowed target-subject information budget',
        'why': 'Calibration/adaptation claims are only defensible if the evaluation protocol states exactly what target data is allowed.',
        'success_condition': 'A table states zero-calibration, unlabeled-target, and k-shot labeled-target settings separately.',
    },
    {
        'priority': 4,
        'action': 'Run only one small confirmatory experiment if a positive claim is required',
        'why': 'Current evidence already rules out blind raw EEG/EMG LOSO search.',
        'success_condition': 'The experiment is pre-gated against locked B2/personalization references and has a stop rule.',
    },
    {
        'priority': 5,
        'action': 'Clean local worktrees/branches only after confirming no uncommitted work',
        'why': 'Local branches with plus signs are checked out in other worktrees and cannot be safely deleted blindly.',
        'success_condition': 'git worktree list is reviewed; unused worktrees are removed intentionally.',
    },
]


def run(args: list[str], check: bool = False) -> str:
    p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if check and p.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(args)}\nSTDERR:\n{p.stderr}")
    return p.stdout.strip()


def read_csv_rows(path: Path, limit: int | None = None) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open('r', encoding='utf-8', errors='replace', newline='') as f:
        reader = csv.DictReader(f)
        rows: list[dict[str, str]] = []
        for row in reader:
            rows.append({str(k): '' if v is None else str(v) for k, v in row.items()})
            if limit is not None and len(rows) >= limit:
                break
        return rows


def count_csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open('r', encoding='utf-8', errors='replace', newline='') as f:
        reader = csv.reader(f)
        try:
            next(reader)
        except StopIteration:
            return 0
        return sum(1 for _ in reader)


def compact_value(x: Any, max_len: int = 500) -> str:
    txt = '' if x is None else str(x)
    txt = txt.replace('\n', ' ').replace('|', '/')
    if len(txt) > max_len:
        txt = txt[: max_len - 3] + '...'
    return txt


def classify_file(path: Path) -> str:
    name = path.name.lower()
    if 'decision_table' in name or 'conclusion_table' in name or 'verdict' in name:
        return 'decision_or_verdict'
    if 'main_metrics' in name or 'method_metrics' in name or 'metric_summary' in name:
        return 'metrics'
    if 'subject' in name or 'fold' in name:
        return 'subject_or_fold_detail'
    if path.suffix.lower() == '.md':
        return 'markdown_report'
    if path.suffix.lower() == '.json':
        return 'json_report'
    return 'artifact'


def build_artifact_inventory() -> list[dict[str, Any]]:
    patterns = [
        'docs/roca/*current*.csv',
        'docs/roca/*current*.md',
        'docs/roca/*current*.json',
        'docs/idare_*',
        'scripts/roca/*.py',
        'scripts/idare_*.py',
    ]
    paths: list[Path] = []
    for pat in patterns:
        paths.extend(ROOT.glob(pat))
    unique = sorted({p for p in paths if p.is_file()})

    rows: list[dict[str, Any]] = []
    for p in unique:
        rel = p.as_posix()
        kind = classify_file(p)
        size = p.stat().st_size
        row_count = count_csv_rows(p) if p.suffix.lower() == '.csv' else ''
        sample = ''
        if p.suffix.lower() == '.csv' and kind in {'decision_or_verdict', 'metrics'}:
            sample_rows = read_csv_rows(p, limit=2)
            if sample_rows:
                sample = json.dumps(sample_rows, ensure_ascii=False)[:900]
        elif p.suffix.lower() == '.md' and ('06a7' in rel or '06b3' in rel or 'conclusion' in rel):
            sample = p.read_text(encoding='utf-8', errors='replace')[:900].replace('\n', ' ')
        rows.append({
            'path': rel,
            'kind': kind,
            'size_bytes': size,
            'row_count': row_count,
            'sample': sample,
        })
    return rows


def build_key_decisions() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for label, path in KEY_FILES.items():
        rows = read_csv_rows(path, limit=3)
        out.append({
            'label': label,
            'path': path.as_posix(),
            'exists': path.exists(),
            'rows': rows,
        })
    return out


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text('', encoding='utf-8')
        return
    fields = list(rows[0].keys())
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: compact_value(r.get(k, '')) for k in fields})


def md_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return '_No rows._'
    lines = []
    lines.append('| ' + ' | '.join(columns) + ' |')
    lines.append('| ' + ' | '.join(['---'] * len(columns)) + ' |')
    for r in rows:
        lines.append('| ' + ' | '.join(compact_value(r.get(c, ''), 220) for c in columns) + ' |')
    return '\n'.join(lines)


def main() -> None:
    current_branch = run(['git', 'branch', '--show-current'])
    status = run(['git', 'status', '--short'])
    latest_roca = run(['git', 'log', '--oneline', '--decorate', '-12', 'origin/roca-idare-killtest'])
    remote_branches = run(['git', 'branch', '-r', '--sort=-committerdate']).splitlines()
    local_branches = run(['git', 'branch']).splitlines()
    worktrees = run(['git', 'worktree', 'list'])

    key_decisions = build_key_decisions()
    artifact_inventory = build_artifact_inventory()

    decision_rows = []
    decision_rows.append({
        'final_decision': 'ROCA_CURRENT_TRUTH_BRANCH_READY_FOR_RESEARCH_DECISION_PACK',
        'current_branch': current_branch,
        'clean_worktree': str(status == ''),
        'main_status': 'separate_restored_not_active_research_branch',
        'scientific_state': 'strict_LOSO_global_raw_EEG_EMG_residual_decoding_not_supported; calibration_personalization_is_the_only_partial_positive_route',
        'recommended_next_action': 'write final paper/report decision pack; choose one calibrated/adaptation-assisted route only if a positive model claim is required',
    })

    write_csv(Path(str(PREFIX) + '_decision_table.csv'), decision_rows)
    write_csv(Path(str(PREFIX) + '_phase_summary.csv'), MANUAL_PHASES)
    write_csv(Path(str(PREFIX) + '_remaining_actions.csv'), REMAINING_ACTIONS)
    write_csv(Path(str(PREFIX) + '_artifact_inventory.csv'), artifact_inventory)
    write_csv(Path(str(PREFIX) + '_key_decisions.csv'), [
        {
            'label': d['label'],
            'path': d['path'],
            'exists': d['exists'],
            'rows_json': json.dumps(d['rows'], ensure_ascii=False),
        }
        for d in key_decisions
    ])

    payload = {
        'generated_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'git': {
            'current_branch': current_branch,
            'status_short': status,
            'latest_roca': latest_roca,
            'remote_branches': remote_branches,
            'local_branches': local_branches,
            'worktrees': worktrees,
        },
        'decision': decision_rows[0],
        'phase_summary': MANUAL_PHASES,
        'remaining_actions': REMAINING_ACTIONS,
        'key_decisions': key_decisions,
        'artifact_inventory_count': len(artifact_inventory),
    }
    Path(str(PREFIX) + '.json').write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding='utf-8')

    lines: list[str] = []
    lines.append('# I-DARE / ROCA Final Research Ledger')
    lines.append('')
    lines.append(f"generated_at: `{payload['generated_at']}`")
    lines.append(f"current_branch: `{current_branch}`")
    lines.append(f"clean_worktree: `{status == ''}`")
    lines.append('')
    lines.append('## Final decision')
    lines.append('')
    lines.append(md_table(decision_rows, ['final_decision', 'scientific_state', 'recommended_next_action']))
    lines.append('')
    lines.append('## What happened across ROCA')
    lines.append('')
    lines.append(md_table(MANUAL_PHASES, ['phase', 'status', 'summary', 'evidence']))
    lines.append('')
    lines.append('## Key decision files read')
    lines.append('')
    key_flat = []
    for d in key_decisions:
        key_flat.append({
            'label': d['label'],
            'exists': d['exists'],
            'path': d['path'],
            'first_rows': json.dumps(d['rows'][:1], ensure_ascii=False),
        })
    lines.append(md_table(key_flat, ['label', 'exists', 'path', 'first_rows']))
    lines.append('')
    lines.append('## Remaining actions')
    lines.append('')
    lines.append(md_table(REMAINING_ACTIONS, ['priority', 'action', 'why', 'success_condition']))
    lines.append('')
    lines.append('## Git state')
    lines.append('')
    lines.append('### Latest ROCA commits')
    lines.append('')
    lines.append('```')
    lines.append(latest_roca)
    lines.append('```')
    lines.append('')
    lines.append('### Remote branches')
    lines.append('')
    lines.append('```')
    lines.append('\n'.join(remote_branches))
    lines.append('```')
    lines.append('')
    lines.append('### Worktrees')
    lines.append('')
    lines.append('```')
    lines.append(worktrees)
    lines.append('```')
    lines.append('')
    lines.append('## Artifact inventory')
    lines.append('')
    lines.append(f'Total indexed artifacts/scripts: `{len(artifact_inventory)}`')
    lines.append('')
    lines.append('See `_artifact_inventory.csv` for the full index.')

    Path(str(PREFIX) + '.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')

    print('ROCA step 06c0 completed.')
    for suffix in ['.md', '.json', '_decision_table.csv', '_phase_summary.csv', '_remaining_actions.csv', '_key_decisions.csv', '_artifact_inventory.csv']:
        print('wrote:', str(PREFIX) + suffix)
    print('\nDecision:')
    for r in decision_rows:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    print('\nNext actions:')
    for r in REMAINING_ACTIONS:
        print(f"- P{r['priority']}: {r['action']}")


if __name__ == '__main__':
    main()
