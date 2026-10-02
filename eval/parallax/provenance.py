"""Record corpus coverage and retain license evidence with derived metadata."""
import json,shutil
from collections import Counter
from .config import DATA
from .dataset import load
def main():
    rows=load(DATA/'research-manifest.jsonl');clean=[r for r in rows if not r['is_injected']]
    folder=DATA/'licenses';folder.mkdir(exist_ok=True)
    for group in {r['source_group'] for r in clean}:
        shutil.copyfile(DATA/'corpus'/group/'LICENSE.source',folder/(group+'.txt'))
    summary={'base_pages':len(clean),'source_projects':len({r['source_group'] for r in clean}),
     'injected_variants':len(rows)-len(clean),'clean_by_split':dict(Counter(r['split'] for r in clean)),
     'categories':dict(Counter(r['category'] for r in clean)),'preservation_eligible':sum(r['preservation_eligible'] for r in clean),
     'heuristic_hard_negatives':len(load(DATA/'hard-negatives.jsonl')),'human_curated_hard_negatives':0,
     'limitations':['All acquired sources are documentation projects.','License evidence is retained, but page-level terms/assets require human review before redistribution.',
     'Scripts and navigation are disabled; source replays cannot establish interactive preservation.','Content hashing does not prove semantic independence; translated/versioned related pages may remain within a source group.']}
    (DATA/'coverage.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
