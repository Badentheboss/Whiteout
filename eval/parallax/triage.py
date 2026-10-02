"""AI-assisted review aids. Never writes human labels or legal approvals."""
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

from .config import DATA, ROOT
from .dataset import load


def model_score(text, weights):
    text = re.sub(r'CANARY-[A-Z0-9-]+', 'token', text, flags=re.I).lower()
    tokens = re.findall(r'\w{2,}', text, flags=re.UNICODE)
    learned = weights['features']
    values = []
    for n in (1, 2):
        for i in range(len(tokens) - n + 1):
            term = ' '.join(tokens[i:i+n])
            pair = learned.get(term)
            if pair:
                values.append((pair[0], pair[1]))
    norm = math.sqrt(sum(value * value for value, _ in values)) or 1
    logit = weights['intercept'] + sum(value / norm * coef for value, coef in values)
    return 1 / (1 + math.exp(-max(-60, min(60, logit))))


def source_assessments():
    rows = [r for r in load(DATA / 'research-manifest.jsonl') if not r['is_injected']]
    projects = defaultdict(list)
    for row in rows:
        projects[row['source_group']].append(row)
    result = []
    for group, pages in sorted(projects.items()):
        first = pages[0]
        license_path = DATA / 'licenses' / f'{group}.txt'
        actual_hash = hashlib.sha256(license_path.read_bytes()).hexdigest() if license_path.exists() else None
        license_matches = actual_hash == first.get('license_sha256')
        assets = {asset['path'] for page in pages for asset in page.get('assets', [])}
        missing = {item for page in pages for item in page.get('missing_assets', [])}
        result.append({
            'source_group': group, 'pages': len(pages), 'category': first.get('category'),
            'license_claim': first.get('license'), 'license_url': first.get('license_url'),
            'license_evidence_file': str(license_path.relative_to(ROOT)) if license_path.exists() else None,
            'license_evidence_sha256': actual_hash, 'manifest_license_sha256': first.get('license_sha256'),
            'license_hash_matches': license_matches, 'attribution': first.get('attribution'),
            'unique_bundled_assets': len(assets), 'unique_missing_asset_references': len(missing),
            'robots_and_crawl_delay': 'acquisition tool enforces robots and crawl-delay; manifest is not per-page proof',
            'page_terms_reviewed': False, 'third_party_asset_rights_reviewed': False,
            'local_private_experiment': 'conditional-recommendation' if license_matches else 'hold-license-evidence-mismatch',
            'redistribution': 'not-approved', 'human_approval': None,
            'basis': 'Repository license evidence is not proof that hosted documentation text/assets use that license; local-only research recommendation is not legal advice or human approval.'
        })
    return result


def main():
    destination = ROOT / 'reviews'
    destination.mkdir(exist_ok=True)
    source_rows = source_assessments()
    (destination / 'source-assessment-ai.json').write_text(json.dumps({
        'schema_version': 1, 'assessment_origin': 'AI-assisted evidence triage; not human/legal review',
        'summary': {'projects': len(source_rows), 'conditional_local_only': sum(r['local_private_experiment'] == 'conditional-recommendation' for r in source_rows),
                    'human_approvals': 0, 'redistribution_approved': 0},
        'projects': source_rows
    }, indent=2), encoding='utf-8')
    (DATA / 'source-assessment-summary.json').write_text(json.dumps({
        'schema_version': 1,
        'assessment_origin': 'AI-assisted triage; not a human or legal approval',
        'scope': 'Conditional local/private research processing only; do not redistribute source replays or bundled assets based on this assessment.',
        'summary': {'projects': len(source_rows),
                    'license_evidence_hash_matches': sum(r['license_hash_matches'] for r in source_rows),
                    'conditional_local_only': sum(r['local_private_experiment'] == 'conditional-recommendation' for r in source_rows),
                    'human_approvals': 0, 'redistribution_approved': 0,
                    'page_terms_reviewed': 0, 'third_party_asset_rights_reviewed': 0},
        'projects': [{k: r[k] for k in ['source_group', 'pages', 'license_claim', 'license_url',
                                        'license_evidence_sha256', 'license_hash_matches',
                                        'local_private_experiment', 'redistribution']}
                     for r in source_rows],
        'limitations': [
            'A repository license file does not establish rights to all hosted documentation text or assets.',
            'Robots/crawl-delay compliance is enforced during acquisition but is not itself a copyright or terms grant.',
            'A qualified human must check current site terms, page-specific notices, third-party asset rights, and attribution before any redistribution.'
        ]
    }, indent=2), encoding='utf-8')

    queue = load(destination / 'negatives-pending.jsonl')
    weights = json.loads((ROOT / 'extension/src/weights.json').read_text(encoding='utf-8'))
    suggestions = []
    for row in queue:
        score = model_score(row['text'], weights)
        suggestions.append({
            'id': row['id'], 'source_group': row['source_group'], 'split': row['split'],
            'text': row['text'], 'ai_instruction_suggestion': score >= weights['cutoff'],
            'score': score, 'threshold': weights['cutoff'], 'model_id': weights['model_id'],
            'scorer': 'offline reconstruction of shipped TF-IDF/logistic model; Unicode tokenization may differ slightly from browser runtime',
            'human_instruction': None, 'human_visible': None, 'rater': '',
            'status': 'pending-human-review',
            'warning': 'AI suggestion only, not a human label; candidates overlap model training sources and cannot validate model accuracy.'
        })
    with (destination / 'negatives-ai-suggestions.jsonl').open('w', encoding='utf-8') as stream:
        for row in suggestions:
            stream.write(json.dumps(row, ensure_ascii=False) + '\n')
    print(json.dumps({'source_projects': len(source_rows), 'source_local_only_recommendations': sum(r['local_private_experiment'] == 'conditional-recommendation' for r in source_rows),
                      'source_human_approvals': 0, 'negative_ai_suggestions': len(suggestions),
                      'negative_human_judgments': 0, 'output': str(destination)}, indent=2))


if __name__ == '__main__':
    main()
