"""Human ratings are append-only and never synthesized as real validation."""
import json
import math
from itertools import combinations
from pathlib import Path
from sklearn.metrics import cohen_kappa_score,precision_recall_fscore_support,roc_auc_score
def inter_rater(rows):
    latest={}
    for row in rows:
        if not all(k in row for k in ['rater','variant_id','candidate_id']):continue
        latest[(row['rater'],row['variant_id'],row['candidate_id'])]=row
    raters=sorted({key[0] for key in latest});results=[]
    for left,right in combinations(raters,2):
        shared=sorted({key[1:] for key in latest if key[0]==left}&{key[1:] for key in latest if key[0]==right})
        for field in ['human_visible','instruction']:
            pairs=[(latest[(left,*key)][field],latest[(right,*key)][field]) for key in shared
                   if type(latest[(left,*key)].get(field)) is bool and type(latest[(right,*key)].get(field)) is bool]
            if not pairs:continue
            a,b=zip(*pairs)
            kappa=float(cohen_kappa_score(a,b)) if len(set(a+b))>1 else None
            results.append({'raters':[left,right],'field':field,'shared_items':len(pairs),
                            'agreement':sum(x==y for x,y in pairs)/len(pairs),
                            'kappa':kappa if kappa is not None and math.isfinite(kappa) else None})
    return {'pairs':results,'reason':None if results else 'Two raters must review overlapping items'}
def agreement(rows):
    if not rows:return {'count':0,'reason':'No human ratings'}
    # Re-rating an item replaces its statistical vote, while the audit log stays append-only.
    unique={}
    for index,r in enumerate(rows):unique[(r.get('rater','anonymous'),r.get('variant_id',index),r.get('candidate_id',index))]=r
    rows=list(unique.values())
    truth=[int(r['instruction']) for r in rows];pred=[int(r.get('predicted_instruction',r['score']>=r.get('cutoff',.5))) for r in rows]
    precision,recall,f1,_=precision_recall_fscore_support(truth,pred,average='binary',zero_division=0)
    return {'count':len(rows),'visibility_kappa':float(cohen_kappa_score([not r['human_visible'] for r in rows],[r['hidden'] for r in rows])) if len({r['human_visible'] for r in rows})>1 else None,
      'instruction_precision':float(precision),'instruction_recall':float(recall),'instruction_f1':float(f1),
      'auroc':float(roc_auc_score(truth,[r['score'] for r in rows])) if len(set(truth))>1 else None,
      'inter_rater':inter_rater(rows)}
