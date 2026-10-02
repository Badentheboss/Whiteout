"""Human ratings are append-only and never synthesized as real validation."""
import json
from pathlib import Path
from sklearn.metrics import cohen_kappa_score,precision_recall_fscore_support,roc_auc_score
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
      'auroc':float(roc_auc_score(truth,[r['score'] for r in rows])) if len(set(truth))>1 else None}
