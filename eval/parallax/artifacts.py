"""Read sharded reports without loading a whole experiment's DOM candidates."""
import gzip,json,hashlib
from pathlib import Path
def artifact_path(folder,name):
    root=Path(folder).resolve();path=(root/name).resolve()
    if not path.is_relative_to(root):raise ValueError('Artifact path escapes run directory')
    return path
def observation_path(folder):
    path=folder/'observations.jsonl'
    return path if path.exists() else folder/'observations.jsonl.gz'
def report(folder,row):
    if 'candidates' in row:return row
    path=artifact_path(folder,row['report_path'])
    expected=row.get('report_sha256')
    if expected and hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
        raise ValueError('Detailed report checksum mismatch')
    with gzip.open(path,'rt',encoding='utf-8') as f:return json.load(f)
def score_bounds(folder,row):
    if 'max_hidden_score' in row:return row['max_hidden_score'],row['best_payload_score']
    candidates=report(folder,row)['candidates']
    scores=[c['score'] for c in candidates if c['hidden'] and c['score'] is not None]
    hits=[c['score'] for c in candidates if c.get('ground_truth_match') and c['score'] is not None]
    return max(scores,default=None),max(hits,default=None)
