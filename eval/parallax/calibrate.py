"""Select a threshold using measured VALIDATION pages only, before test execution."""
import argparse,json,hashlib
from pathlib import Path
from .config import ROOT
from .dataset import load
from .artifacts import score_bounds,observation_path
def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);a=p.parse_args();folder=Path(a.run)
    if (folder/'INVALIDATED.md').exists():raise ValueError('Invalidated run')
    rows=[r for r in load(folder/'observations.jsonl') if r['detector']=='classifier']
    if not rows or any(r['split']!='validation' for r in rows):raise ValueError('Only nonempty validation observations are allowed')
    clean=[r for r in rows if not r['is_injected']];attack=[r for r in rows if r['is_injected']]
    if not clean or not attack:raise ValueError('Need validation clean controls and injected pages')
    choices=[]
    bounds=[(r,*score_bounds(folder,r)) for r in rows]
    scores=sorted({0.,1.000001,*[s for _,maximum,target in bounds for s in [maximum,target] if s is not None]})
    for threshold in scores:
        fpr=sum(maximum is not None and maximum>=threshold for r,maximum,target in bounds if not r['is_injected'])/len(clean)
        recall=sum(target is not None and target>=threshold for r,maximum,target in bounds if r['is_injected'])/len(attack)
        if fpr<=.02:choices.append((recall,-fpr,threshold))
    recall,negative_fpr,cutoff=max(choices)
    path=ROOT/'extension/src/weights.json';weights=json.loads(path.read_text())
    if {r['model'] for r in rows}!={weights['model_id']}:raise ValueError('Model identity mismatch')
    report={'run':str(folder),'observations_sha256':hashlib.sha256(observation_path(folder).read_bytes()).hexdigest(),
     'cutoff':cutoff,'recall':recall,'clean_page_fpr':-negative_fpr,'clean_pages':len(clean),'injected_pages':len(attack),
     'warning':'Validation estimate only; small clean denominators do not establish a population 2% FPR.'}
    weights['cutoff']=cutoff;path.write_text(json.dumps(weights),encoding='utf-8')
    (ROOT/'models/page-calibration.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
