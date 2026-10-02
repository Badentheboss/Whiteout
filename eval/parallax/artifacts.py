"""Read sharded reports without loading a whole experiment's DOM candidates."""
import gzip,json
def observation_path(folder):
    path=folder/'observations.jsonl'
    return path if path.exists() else folder/'observations.jsonl.gz'
def report(folder,row):
    if 'candidates' in row:return row
    with gzip.open(folder/row['report_path'],'rt',encoding='utf-8') as f:return json.load(f)
def score_bounds(folder,row):
    if 'max_hidden_score' in row:return row['max_hidden_score'],row['best_payload_score']
    candidates=report(folder,row)['candidates']
    scores=[c['score'] for c in candidates if c['hidden'] and c['score'] is not None]
    hits=[c['score'] for c in candidates if c.get('ground_truth_match') and c['score'] is not None]
    return max(scores,default=None),max(hits,default=None)
