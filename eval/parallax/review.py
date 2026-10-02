"""Human review records: pending is never silently converted to a negative label."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .dataset import load
from .metrics import confusion


def latest_reviews(rows, identity):
    latest = {}
    for row in rows:
        key = (row['rater'], *(row[field] for field in identity))
        latest[key] = row
    return list(latest.values())


def append_review(path, row, required_booleans):
    if not row.get('rater', '').strip():
        raise ValueError('A nonempty reviewer pseudonym is required')
    for field in required_booleans:
        if type(row.get(field)) is not bool:
            raise ValueError(f'{field} needs an explicit yes/no judgment')
    record = {**row, 'label_origin': 'human',
              'reviewed_at': datetime.now(timezone.utc).isoformat()}
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + '\n')
    return record


def node_metrics(candidates, findings, annotations):
    """Score only adjudicated candidate IDs; unreviewed nodes are not negatives."""
    known = {c['id'] for c in candidates}
    labels = {}
    conflicts = set()
    for row in latest_reviews(annotations, ['candidate_id']):
        key = row['candidate_id']
        if key not in known:
            raise ValueError('Annotation references an unknown candidate')
        if type(row.get('instruction')) is not bool or type(row.get('human_visible')) is not bool:
            raise ValueError('Pending node label cannot be scored')
        truth = row['instruction'] and not row['human_visible']
        if key in labels and labels[key] != truth:
            conflicts.add(key)
        labels[key] = truth
    reviewed = set(labels) - conflicts
    if not reviewed:
        return {'precision': None, 'recall': None, 'f1': None,
                'reason': 'No non-conflicting reviewed nodes', 'reviewed': 0,
                'conflicts': len(conflicts), 'total_candidates': len(known)}
    predicted = {c['id'] for c in findings} & reviewed
    truth = {key for key in reviewed if labels[key]}
    return {**confusion(predicted, truth), 'reviewed': len(reviewed),
            'conflicts': len(conflicts), 'total_candidates': len(known),
            'scope': 'reviewed candidates only; not whole-page recall'}


def prepare_sources(rows):
    seen = set()
    result = []
    for row in rows:
        if row['page_id'] in seen:
            continue
        seen.add(row['page_id'])
        result.append({key: row.get(key) for key in [
            'page_id', 'source_group', 'source_url', 'license_url', 'license_sha256',
            'content_hash', 'snapshot_path', 'category', 'missing_assets', 'transformations']})
        result[-1].update(rater='', terms_url='', terms_checked=None,
                          page_license_checked=None, asset_licenses_checked=None,
                          replay_faithful=None, notes='', status='pending')
    return result


def prepare_negatives(rows, count):
    # Round robin projects: no model-score cherry-picking and no review of test labels.
    buckets = {}
    for row in sorted(rows, key=lambda r: hashlib.sha256(r['id'].encode()).hexdigest()):
        if row['split'] == 'test':
            continue
        buckets.setdefault(row['source_group'], []).append(row)
    result = []
    while len(result) < count and any(buckets.values()):
        for group in sorted(buckets):
            if buckets[group] and len(result) < count:
                row = buckets[group].pop()
                result.append({**row, 'rater': '', 'instruction': None,
                               'human_visible': None, 'notes': '', 'status': 'pending',
                               'label_origin': 'pending-human-review'})
    return result


def main():
    parser = argparse.ArgumentParser(description='Prepare pending review forms; does not run a detector')
    parser.add_argument('kind', choices=['sources', 'negatives'])
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--count', type=int, default=300)
    args = parser.parse_args()
    if args.count < 1:
        raise ValueError('count must be positive')
    rows = load(args.input)
    queue = prepare_sources(rows) if args.kind == 'sources' else prepare_negatives(rows, args.count)
    with Path(args.output).open('x', encoding='utf-8') as stream:
        for row in queue:
            stream.write(json.dumps(row, ensure_ascii=False) + '\n')
    print(f'{len(queue)} pending forms; no human labels created')


if __name__ == '__main__':
    main()
