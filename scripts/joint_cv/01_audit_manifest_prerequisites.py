#!/usr/bin/env python3
"""
Read-only prerequisite audit for canonical DEAP/I-DARE physical-trial manifests.

This script does NOT train a model, construct folds, modify datasets/caches,
or change Git state. It checks whether physical trial, stimulus identity,
presentation order, labels, and EEG/EMG availability can be recovered reliably.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import pickle
import re
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

DEFAULT_REPO = Path('/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE')
DEFAULT_DEAP = Path('/mnt/HDD/AliWorks/DEAP')
DEFAULT_IDARE = Path('/mnt/HDD/AliWorks/I-DARE')

TEXT_SUFFIXES = {
    '.md', '.txt', '.csv', '.json', '.py', '.sh', '.yaml', '.yml',
    '.toml', '.ini', '.cfg', '.rst',
}
DEAP_METADATA_SUFFIXES = {
    '.csv', '.tsv', '.txt', '.xls', '.xlsx', '.ods', '.mat', '.json',
    '.xml', '.arff', '.zip', '.rar', '.7z', '.pdf',
}
DEAP_METADATA_KEYWORDS = {
    'video', 'stim', 'stimulus', 'trial', 'order', 'rating', 'participant',
    'metadata', 'experiment', 'playlist', 'sequence', 'clip', 'movie',
}
REPO_MAPPING_PATTERNS = [
    re.compile(r'\bdeap\b.{0,120}\b(stimulus|video|trial[_ -]?order|presentation[_ -]?order)\b', re.I | re.S),
    re.compile(r'\b(stimulus|video|trial[_ -]?order|presentation[_ -]?order)\b.{0,120}\bdeap\b', re.I | re.S),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root', type=Path, default=DEFAULT_REPO)
    parser.add_argument('--deap-root', type=Path, default=DEFAULT_DEAP)
    parser.add_argument('--idare-root', type=Path, default=DEFAULT_IDARE)
    parser.add_argument('--out-dir', type=Path, default=None)
    parser.add_argument('--max-repo-text-bytes', type=int, default=2_000_000)
    parser.add_argument('--overwrite', action='store_true')
    return parser.parse_args()


def clean_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): clean_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean_json(v) for v in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        value = float(value)
        return value if math.isfinite(value) else None
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    return value


def run_command(command: list[str], cwd: Path | None = None) -> dict[str, Any]:
    proc = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return {
        'returncode': proc.returncode,
        'stdout': proc.stdout.strip(),
        'stderr': proc.stderr.strip(),
    }


def output_paths(out_dir: Path, overwrite: bool) -> dict[str, Path]:
    paths = {
        'json': out_dir / 'manifest_prerequisites_audit.json',
        'md': out_dir / 'manifest_prerequisites_audit.md',
        'deap_candidates': out_dir / 'deap_stimulus_mapping_candidates.csv',
        'repo_hits': out_dir / 'deap_mapping_repository_hits.csv',
        'idare_subjects': out_dir / 'idare_manifest_prerequisites_by_subject.csv',
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    if not overwrite:
        existing = [p for p in paths.values() if p.exists()]
        if existing:
            listing = '\n'.join(f'- {p}' for p in existing)
            raise FileExistsError(
                'Refusing to overwrite outputs. Review them or rerun with --overwrite:\n'
                + listing
            )
    return paths


def inspect_git(repo_root: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        'repo_root': str(repo_root),
        'exists': repo_root.exists(),
        'is_git_worktree': (repo_root / '.git').exists(),
    }
    if not result['is_git_worktree']:
        return result
    commands = {
        'branch': ['git', 'branch', '--show-current'],
        'head': ['git', 'rev-parse', 'HEAD'],
        'status_short': ['git', 'status', '--short'],
        'latest_commit': ['git', 'log', '-1', '--oneline'],
    }
    for key, command in commands.items():
        item = run_command(command, cwd=repo_root)
        result[key] = item['stdout']
        result[f'{key}_returncode'] = item['returncode']
        if item['stderr']:
            result[f'{key}_stderr'] = item['stderr']
    result['working_tree_clean_before_audit'] = result.get('status_short', '') == ''
    return result


def inspect_deap_pickle_schema(deap_python_dir: Path) -> dict[str, Any]:
    subject_files = sorted(deap_python_dir.glob('s??.dat'))
    result: dict[str, Any] = {
        'deap_python_dir': str(deap_python_dir),
        'subject_file_count': len(subject_files),
        'subject_files': [p.name for p in subject_files],
        'sample_file': None,
        'sample_keys': [],
        'data_shape': None,
        'labels_shape': None,
        'data_dtype': None,
        'labels_dtype': None,
        'nonstandard_keys': [],
        'load_error': None,
    }
    if not subject_files:
        return result

    sample_path = subject_files[0]
    result['sample_file'] = str(sample_path)
    try:
        with sample_path.open('rb') as handle:
            obj = pickle.load(handle, encoding='latin1')
        if not isinstance(obj, dict):
            result['load_error'] = f'Expected dict, got {type(obj).__name__}'
            return result
        keys = sorted(str(k) for k in obj.keys())
        result['sample_keys'] = keys
        result['nonstandard_keys'] = [k for k in keys if k not in {'data', 'labels'}]
        data = obj.get('data')
        labels = obj.get('labels')
        if hasattr(data, 'shape'):
            result['data_shape'] = list(data.shape)
        if hasattr(labels, 'shape'):
            result['labels_shape'] = list(labels.shape)
        if hasattr(data, 'dtype'):
            result['data_dtype'] = str(data.dtype)
        if hasattr(labels, 'dtype'):
            result['labels_dtype'] = str(labels.dtype)
    except Exception as exc:
        result['load_error'] = repr(exc)
    return result


def list_deap_metadata_candidates(deap_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not deap_root.exists():
        return rows
    for path in sorted(deap_root.rglob('*')):
        if not path.is_file() or path.suffix.lower() == '.dat':
            continue
        suffix = path.suffix.lower()
        name = path.name.lower()
        hits = sorted(k for k in DEAP_METADATA_KEYWORDS if k in name)
        if suffix in DEAP_METADATA_SUFFIXES or hits:
            rows.append({
                'path': str(path),
                'relative_path': str(path.relative_to(deap_root)),
                'suffix': suffix,
                'size_bytes': path.stat().st_size,
                'keyword_hits': ';'.join(hits),
                'candidate_reason': 'supported_metadata_extension' + ('+filename_keyword' if hits else ''),
            })
    return rows


def search_repo_for_deap_mapping(repo_root: Path, max_bytes: int) -> list[dict[str, Any]]:
    excluded = {'.git', '.venv', '.cache', '__pycache__', 'node_modules'}
    hits: list[dict[str, Any]] = []
    for path in sorted(repo_root.rglob('*')):
        if not path.is_file():
            continue
        if any(part in excluded for part in path.parts):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            size = path.stat().st_size
        except OSError:
            continue
        if size > max_bytes:
            continue
        try:
            text = path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        for pattern_id, pattern in enumerate(REPO_MAPPING_PATTERNS, start=1):
            match = pattern.search(text)
            if not match:
                continue
            start = max(0, match.start() - 120)
            end = min(len(text), match.end() + 220)
            snippet = re.sub(r'\s+', ' ', text[start:end]).strip()
            hits.append({
                'path': str(path),
                'relative_path': str(path.relative_to(repo_root)),
                'pattern_id': pattern_id,
                'size_bytes': size,
                'snippet': snippet,
            })
            break
    return hits


def assess_deap_mapping(
    metadata_rows: list[dict[str, Any]],
    repo_hits: list[dict[str, Any]],
    schema: dict[str, Any],
) -> dict[str, Any]:
    strong_files: list[str] = []
    weak_files: list[str] = []
    for row in metadata_rows:
        hits = set(filter(None, row['keyword_hits'].split(';')))
        if hits.intersection({'video', 'stimulus', 'stim', 'trial', 'order', 'sequence'}):
            strong_files.append(row['path'])
        else:
            weak_files.append(row['path'])

    embedded_key = bool(schema.get('nonstandard_keys'))
    if embedded_key:
        status = 'needs_manual_review'
        reason = (
            'The sample DEAP pickle has nonstandard keys that may encode stimulus '
            'identity or trial order; inspect them before constructing a manifest.'
        )
    elif strong_files:
        status = 'needs_manual_review'
        reason = (
            'Potential local DEAP stimulus/order metadata files were found. '
            'Their linkage to subject trial rows must be verified.'
        )
    elif repo_hits:
        status = 'needs_manual_review'
        reason = (
            'Repository text mentions a DEAP stimulus/video/order mapping. '
            'The referenced source must be located and verified.'
        )
    else:
        status = 'blocked_missing_stimulus_identity_mapping'
        reason = (
            'The available DEAP preprocessed Python sample exposes only data and '
            'labels, and no local stimulus/video/trial-order mapping candidate was '
            'found. A 1280-row physical-trial manifest can be created, but reliable '
            'DEAP stimulus_id and presentation_order cannot yet be claimed.'
        )
    return {
        'status': status,
        'reason': reason,
        'embedded_mapping_key_found': embedded_key,
        'strong_file_candidate_count': len(strong_files),
        'weak_file_candidate_count': len(weak_files),
        'repository_mapping_hit_count': len(repo_hits),
        'strong_file_candidates': strong_files,
    }


def audit_idare_trial_index(repo_root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    index_path = repo_root / '.cache' / 'idare_trial_index.csv'
    summary: dict[str, Any] = {
        'trial_index_path': str(index_path),
        'exists': index_path.exists(),
    }
    subject_rows: list[dict[str, Any]] = []
    if not index_path.exists():
        summary.update({'ready': False, 'blocking_reasons': ['idare_trial_index.csv is missing']})
        return summary, subject_rows

    df = pd.read_csv(index_path)
    summary['row_count'] = len(df)
    summary['columns'] = list(df.columns)
    required = {
        'subject_id', 'stimulus_id', 'event_index_0based',
        'valence_score', 'arousal_score', 'eeg_file', 'emg_file',
        'eeg_fs', 'emg_fs', 'eeg_duration_sec', 'emg_duration_sec',
    }
    missing_columns = sorted(required - set(df.columns))
    summary['missing_required_columns'] = missing_columns
    blocking: list[str] = []
    warnings: list[str] = []
    if missing_columns:
        blocking.append(f'Missing required columns: {missing_columns}')
        summary.update({'ready': False, 'blocking_reasons': blocking, 'warnings': warnings})
        return summary, subject_rows

    df = df.copy()
    df['subject_id'] = df['subject_id'].astype(str)
    df['stimulus_id'] = df['stimulus_id'].astype(str)
    duplicate_rows = int(df.duplicated(['subject_id', 'stimulus_id'], keep=False).sum())
    subject_counts = df.groupby('subject_id').size().sort_index()
    stimulus_counts = df.groupby('stimulus_id').size().sort_index()
    summary.update({
        'duplicate_subject_stimulus_rows': duplicate_rows,
        'subject_count': int(df['subject_id'].nunique()),
        'stimulus_count': int(df['stimulus_id'].nunique()),
        'trials_per_subject_min': int(subject_counts.min()),
        'trials_per_subject_max': int(subject_counts.max()),
        'subjects_per_stimulus_min': int(stimulus_counts.min()),
        'subjects_per_stimulus_max': int(stimulus_counts.max()),
    })

    reference_stimuli: tuple[str, ...] | None = None
    stimulus_set_mismatch = 0
    missing_eeg_total = 0
    missing_emg_total = 0
    duplicate_event_total = 0

    for subject_id, group in df.groupby('subject_id', sort=True):
        stimuli = tuple(sorted(group['stimulus_id'].unique()))
        if reference_stimuli is None:
            reference_stimuli = stimuli
        elif stimuli != reference_stimuli:
            stimulus_set_mismatch += 1
        missing_eeg = int(sum(not Path(p).exists() for p in group['eeg_file'].astype(str)))
        missing_emg = int(sum(not Path(p).exists() for p in group['emg_file'].astype(str)))
        duplicate_event = int(group['event_index_0based'].duplicated(keep=False).sum())
        missing_eeg_total += missing_eeg
        missing_emg_total += missing_emg
        duplicate_event_total += duplicate_event
        subject_rows.append({
            'subject_id': subject_id,
            'trial_count': len(group),
            'unique_stimuli': int(group['stimulus_id'].nunique()),
            'event_index_min': int(group['event_index_0based'].min()),
            'event_index_max': int(group['event_index_0based'].max()),
            'duplicate_event_indices': duplicate_event,
            'missing_eeg_paths': missing_eeg,
            'missing_emg_paths': missing_emg,
            'valence_min': float(group['valence_score'].min()),
            'valence_max': float(group['valence_score'].max()),
            'arousal_min': float(group['arousal_score'].min()),
            'arousal_max': float(group['arousal_score'].max()),
        })

    summary.update({
        'subject_stimulus_set_mismatch_count': stimulus_set_mismatch,
        'missing_eeg_path_count': missing_eeg_total,
        'missing_emg_path_count': missing_emg_total,
        'duplicate_event_index_rows': duplicate_event_total,
    })

    for task in ('valence', 'arousal'):
        score_col = f'{task}_score'
        scores = pd.to_numeric(df[score_col], errors='coerce')
        summary[f'{task}_missing_score_count'] = int(scores.isna().sum())
        summary[f'{task}_score_min'] = float(scores.min())
        summary[f'{task}_score_max'] = float(scores.max())
        summary[f'{task}_score_eq5_count'] = int(np.isclose(scores, 5.0).sum())

    if len(df) != 2016:
        blocking.append(f'Expected 2016 rows, found {len(df)}')
    if summary['subject_count'] != 63:
        blocking.append(f"Expected 63 subjects, found {summary['subject_count']}")
    if summary['stimulus_count'] != 32:
        blocking.append(f"Expected 32 stimuli, found {summary['stimulus_count']}")
    if summary['trials_per_subject_min'] != 32 or summary['trials_per_subject_max'] != 32:
        blocking.append(
            'Expected exactly 32 trials per subject, found range '
            f"{summary['trials_per_subject_min']}..{summary['trials_per_subject_max']}"
        )
    if duplicate_rows:
        blocking.append(f'Found {duplicate_rows} duplicated subject-stimulus rows')
    if stimulus_set_mismatch:
        blocking.append(f'{stimulus_set_mismatch} subjects have a different stimulus set')
    if missing_eeg_total or missing_emg_total:
        blocking.append(f'Missing referenced paths: EEG={missing_eeg_total}, EMG={missing_emg_total}')
    if duplicate_event_total:
        blocking.append(f'Found {duplicate_event_total} duplicated event-index rows')
    for task in ('valence', 'arousal'):
        if summary[f'{task}_missing_score_count']:
            blocking.append(f"{task}: {summary[f'{task}_missing_score_count']} missing scores")
        if summary[f'{task}_score_min'] < 1.0 or summary[f'{task}_score_max'] > 9.0:
            blocking.append(f'{task}: scores outside [1, 9]')
    if 'raw_event_name' not in df.columns:
        warnings.append('raw_event_name is absent; use stimulus_id plus event_index_0based.')
    summary.update({'blocking_reasons': blocking, 'warnings': warnings, 'ready': not blocking})
    return summary, subject_rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text('', encoding='utf-8')
        return
    fieldnames: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fieldnames.append(key)
    with path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return '_No rows._'
    lines = [
        '| ' + ' | '.join(columns) + ' |',
        '| ' + ' | '.join(['---'] * len(columns)) + ' |',
    ]
    for row in rows:
        vals = []
        for column in columns:
            value = str(row.get(column, '')).replace('|', '\\|').replace('\n', ' ')
            vals.append(value)
        lines.append('| ' + ' | '.join(vals) + ' |')
    return '\n'.join(lines)


def write_markdown(
    path: Path,
    git_info: dict[str, Any],
    deap_schema: dict[str, Any],
    deap_candidates: list[dict[str, Any]],
    repo_hits: list[dict[str, Any]],
    deap_mapping: dict[str, Any],
    idare_summary: dict[str, Any],
    idare_subject_rows: list[dict[str, Any]],
) -> None:
    deap_ready = deap_mapping['status'] != 'blocked_missing_stimulus_identity_mapping'
    idare_ready = bool(idare_summary.get('ready'))
    joint_ready = deap_ready and idare_ready
    lines = [
        '# Manifest Prerequisites Audit',
        '',
        'Read-only audit; no training or fold construction was performed.',
        '',
        '## Git Context',
        '',
        f"- Repository: `{git_info.get('repo_root')}`",
        f"- Branch: `{git_info.get('branch', '')}`",
        f"- HEAD: `{git_info.get('head', '')}`",
        f"- Working tree clean before audit: `{git_info.get('working_tree_clean_before_audit')}`",
        '',
        '## DEAP Prerequisites',
        '',
        f"- Subject files: `{deap_schema.get('subject_file_count')}`",
        f"- Sample pickle: `{deap_schema.get('sample_file')}`",
        f"- Sample keys: `{deap_schema.get('sample_keys')}`",
        f"- Data shape: `{deap_schema.get('data_shape')}`",
        f"- Labels shape: `{deap_schema.get('labels_shape')}`",
        f"- Nonstandard keys: `{deap_schema.get('nonstandard_keys')}`",
        f"- Metadata candidates: `{len(deap_candidates)}`",
        f"- Repository mapping hits: `{len(repo_hits)}`",
        f"- Stimulus-identity status: **{deap_mapping['status']}**",
        '',
        deap_mapping['reason'],
        '',
        '### DEAP Metadata Candidates',
        '',
        markdown_table(
            deap_candidates[:100],
            ['relative_path', 'suffix', 'size_bytes', 'keyword_hits', 'candidate_reason'],
        ),
        '',
        '### Repository Mentions Potentially Related to DEAP Mapping',
        '',
        markdown_table(
            repo_hits[:100],
            ['relative_path', 'pattern_id', 'size_bytes', 'snippet'],
        ),
        '',
        '## I-DARE Prerequisites',
        '',
        f"- Trial index: `{idare_summary.get('trial_index_path')}`",
        f"- Ready: `{idare_ready}`",
        f"- Rows: `{idare_summary.get('row_count')}`",
        f"- Subjects: `{idare_summary.get('subject_count')}`",
        f"- Stimuli: `{idare_summary.get('stimulus_count')}`",
        f"- Trials per subject: `{idare_summary.get('trials_per_subject_min')}..{idare_summary.get('trials_per_subject_max')}`",
        f"- Duplicate subject-stimulus rows: `{idare_summary.get('duplicate_subject_stimulus_rows')}`",
        f"- Subject stimulus-set mismatches: `{idare_summary.get('subject_stimulus_set_mismatch_count')}`",
        f"- Missing EEG paths: `{idare_summary.get('missing_eeg_path_count')}`",
        f"- Missing EMG paths: `{idare_summary.get('missing_emg_path_count')}`",
        f"- Duplicate chronology rows: `{idare_summary.get('duplicate_event_index_rows')}`",
        '',
        '### I-DARE Blocking Reasons',
        '',
    ]
    blockers = idare_summary.get('blocking_reasons', [])
    lines.extend([f'- {item}' for item in blockers] if blockers else ['- None.'])
    lines.extend([
        '',
        '### I-DARE Subject Preview',
        '',
        markdown_table(
            idare_subject_rows[:20],
            [
                'subject_id', 'trial_count', 'unique_stimuli',
                'event_index_min', 'event_index_max',
                'duplicate_event_indices', 'missing_eeg_paths', 'missing_emg_paths',
            ],
        ),
        '',
        '## Decision',
        '',
        f'- Safe to build I-DARE canonical physical-trial manifest: `{idare_ready}`',
        f'- Safe to claim DEAP stimulus-aware physical-trial manifest: `{deap_ready}`',
        f'- Safe to proceed directly to Joint-CV fold construction: `{joint_ready}`',
        '',
    ])
    if not joint_ready:
        lines.extend([
            'Joint-CV fold construction must remain blocked until DEAP stimulus '
            'identity and presentation order are supported by a verified mapping source.',
            '',
        ])
    path.write_text('\n'.join(lines), encoding='utf-8')


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    deap_root = args.deap_root.resolve()
    idare_root = args.idare_root.resolve()
    out_dir = (args.out_dir or (repo_root / 'docs' / 'joint_cv')).resolve()
    paths = output_paths(out_dir, args.overwrite)

    git_info = inspect_git(repo_root)
    deap_schema = inspect_deap_pickle_schema(deap_root / 'data_preprocessed_python')
    deap_candidates = list_deap_metadata_candidates(deap_root)
    repo_hits = search_repo_for_deap_mapping(repo_root, args.max_repo_text_bytes)
    deap_mapping = assess_deap_mapping(deap_candidates, repo_hits, deap_schema)
    idare_summary, idare_subject_rows = audit_idare_trial_index(repo_root)

    report = {
        'audit_type': 'physical_trial_manifest_prerequisites',
        'read_only': True,
        'repo_root': str(repo_root),
        'deap_root': str(deap_root),
        'idare_root': str(idare_root),
        'git': git_info,
        'deap': {
            'pickle_schema': deap_schema,
            'metadata_candidates': deap_candidates,
            'repository_mapping_hits': repo_hits,
            'stimulus_mapping_assessment': deap_mapping,
        },
        'idare': {
            'trial_index_summary': idare_summary,
            'subject_rows': idare_subject_rows,
        },
        'decision': {
            'idare_manifest_ready': bool(idare_summary.get('ready')),
            'deap_stimulus_aware_manifest_ready': (
                deap_mapping['status'] != 'blocked_missing_stimulus_identity_mapping'
            ),
            'joint_cv_fold_construction_ready': (
                bool(idare_summary.get('ready'))
                and deap_mapping['status'] != 'blocked_missing_stimulus_identity_mapping'
            ),
        },
    }

    paths['json'].write_text(
        json.dumps(clean_json(report), indent=2, ensure_ascii=False),
        encoding='utf-8',
    )
    write_csv(paths['deap_candidates'], deap_candidates)
    write_csv(paths['repo_hits'], repo_hits)
    write_csv(paths['idare_subjects'], idare_subject_rows)
    write_markdown(
        paths['md'],
        git_info,
        deap_schema,
        deap_candidates,
        repo_hits,
        deap_mapping,
        idare_summary,
        idare_subject_rows,
    )

    print('Manifest-prerequisite audit completed.')
    print(f"Branch: {git_info.get('branch')}")
    print(f"HEAD: {git_info.get('head')}")
    print(f"DEAP subject files: {deap_schema.get('subject_file_count')}")
    print(f"DEAP sample keys: {deap_schema.get('sample_keys')}")
    print(f'DEAP metadata candidates: {len(deap_candidates)}')
    print(f'DEAP repository mapping hits: {len(repo_hits)}')
    print(f"DEAP mapping status: {deap_mapping['status']}")
    print(f"I-DARE ready: {idare_summary.get('ready')}")
    print(f"I-DARE rows: {idare_summary.get('row_count')}")
    print('Joint-CV fold construction ready:', report['decision']['joint_cv_fold_construction_ready'])
    print(f"Markdown report: {paths['md']}")
    print(f"JSON report: {paths['json']}")


if __name__ == '__main__':
    main()

