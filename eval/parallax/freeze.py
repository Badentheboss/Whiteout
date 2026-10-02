"""Content-addressed experiment lock; no browser, training, or benchmark execution."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .config import ROOT
from .dataset import load, validate


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()


def safe_path(root, relative):
    target = (root / relative).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError(f'Path escapes project: {relative}')
    return target


def capture(root, manifest):
    root = root.resolve()
    manifest = manifest.resolve()
    relative = str(manifest.relative_to(root))
    rows = load(manifest)
    validate(rows)
    files = {relative}
    for directory in ['extension/dist', 'eval/parallax']:
        folder = root / directory
        if not folder.is_dir():
            raise ValueError(f'Missing {directory}; build first')
        files.update(str(p.relative_to(root)) for p in folder.rglob('*')
                     if p.is_file() and '__pycache__' not in p.parts)
    if 'extension/dist/manifest.json' not in files:
        raise ValueError('Packaged extension manifest missing')
    for row in rows:
        source = safe_path(root, row['snapshot_path'])
        if not source.is_file():
            raise ValueError(f'Missing replay: {source}')
        if not row.get('variant_sha256') or digest(source) != row['variant_sha256']:
            raise ValueError(f'Replay hash missing or changed: {source}')
        files.add(str(source.relative_to(root)))
        for asset in row.get('assets', []):
            path = safe_path(root, 'data/' + asset['path'])
            if digest(path) != asset['sha256']:
                raise ValueError(f'Asset hash changed: {path}')
            files.add(str(path.relative_to(root)))
    return {'schema_version': 1, 'created_at': datetime.now(timezone.utc).isoformat(),
            'manifest': relative, 'rows': len(rows),
            'files': {name: digest(safe_path(root, name)) for name in sorted(files)},
            'meaning': 'Artifact identity only; not evidence of dataset quality or completed experiments'}


def check(root, lock):
    failures = []
    for name, expected in lock['files'].items():
        path = safe_path(root, name)
        if not path.is_file() or digest(path) != expected:
            failures.append(name)
    # Extra executable artifacts can change behavior even when original files match.
    for directory in ['extension/dist', 'eval/parallax']:
        for path in (root / directory).rglob('*'):
            name = str(path.relative_to(root))
            if path.is_file() and '__pycache__' not in path.parts and name not in lock['files']:
                failures.append(name)
    return sorted(set(failures))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['create', 'check'])
    parser.add_argument('--lock', required=True)
    parser.add_argument('--manifest')
    args = parser.parse_args()
    path = Path(args.lock)
    if args.action == 'create':
        if not args.manifest:
            parser.error('--manifest is required to create a lock')
        value = capture(ROOT, Path(args.manifest))
        with path.open('x', encoding='utf-8') as stream:
            json.dump(value, stream, indent=2)
        print('Lock saved. No dataset run was started.')
    else:
        failures = check(ROOT, json.loads(path.read_text(encoding='utf-8')))
        if failures:
            raise SystemExit('Freeze mismatch:\n' + '\n'.join(failures))
        print('Frozen artifacts match. No dataset run was started.')


if __name__ == '__main__':
    main()
