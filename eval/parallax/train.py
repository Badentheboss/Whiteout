"""Train TF-IDF and a MiniLM embedding head; validation chooses the shipped model."""
import argparse, hashlib, json, re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_recall_curve, average_precision_score
from .config import DATA, ROOT
from .dataset import TEMPLATES, load, save

BENIGN={
'train':['Search this site','Skip to main content','Open navigation menu','Documentation version selector','Reply to this discussion','Example: print the output','Ignore missing files when copying','System prompt is a research topic','This article describes instruction injection','Return value of the function'],
'validation':['Go to next section','Expand the table of contents','Send feedback about documentation','Previous page','Assistant is the name of a software package','The output is shown below'],
'test':['Accessible name for this button','Jump to the article','Collapse code example','Read the previous chapter','Follow the installation guide','Tool calls are discussed in this section']}
def mask(text):return re.sub(r'CANARY-[A-Z0-9-]+','TOKEN',text,flags=re.I)
def training_rows():
    rows=[]
    for split,indexes in [('train',[0,1,2]),('validation',[3]),('test',[4])]:
        for category,templates in TEMPLATES.items():
            for i in indexes:
                for j in range(12):
                    rows.append({'text':mask(templates[i].format(token='CANARY-'+str(j))),'label':1,'split':split,'family':category+'-'+str(i),'label_origin':'authored'})
        for text in BENIGN[split]:
            rows.append({'text':text,'label':0,'split':split,'family':'benign-'+split,'label_origin':'authored'})
        rows.append({'text':'Reference identifier CANARY-EXAMPLE for this documented test case','label':0,'split':split,'family':'canary-mention-'+split,'label_origin':'authored'})
    path=DATA/'hard-negatives.jsonl'
    if path.exists():
        rows.extend({**r,'text':mask(r['text'])} for r in load(path) if r['split']!='test')
    # Exact duplicate texts do not increase effective training sample size.
    unique={}
    for r in rows:unique.setdefault((r['split'],mask(r['text'])),r)
    return list(unique.values())

def operating_point(y,scores):
    choices=[]
    for cutoff in sorted(set([0.,1.000001,*scores.tolist()])):
        predicted=scores>=cutoff
        fpr=float(predicted[y==0].mean()) if (y==0).any() else 0
        recall=float(predicted[y==1].mean()) if (y==1).any() else 0
        if fpr<=.02:choices.append((recall,-fpr,float(cutoff)))
    return max(choices)[2]

def main():
    p=argparse.ArgumentParser();p.add_argument('--encoder',action='store_true');a=p.parse_args()
    rows=training_rows();save(DATA/'training-texts.jsonl',rows)
    train=[r for r in rows if r['split']=='train'];val=[r for r in rows if r['split']=='validation']
    texts=[mask(r['text']) for r in train];y=np.array([r['label'] for r in train]);yv=np.array([r['label'] for r in val])
    vec=TfidfVectorizer(ngram_range=(1,2),max_features=12000,strip_accents=None)
    x=vec.fit_transform(texts);model=LogisticRegression(C=2,class_weight='balanced',random_state=42,max_iter=1000).fit(x,y)
    scores=model.predict_proba(vec.transform([mask(r['text']) for r in val]))[:,1];cutoff=operating_point(yv,scores)
    params={'model_id':'tfidf-logistic-v2','backend':'linear','intercept':float(model.intercept_[0]),'cutoff':cutoff,
       'features':{term:[float(vec.idf_[i]),float(model.coef_[0,i])] for term,i in vec.vocabulary_.items()}}
    model_dir=ROOT/'models';model_dir.mkdir(exist_ok=True)
    (model_dir/'linear.json').write_text(json.dumps(params),encoding='utf-8')
    reports={'linear':{'validation_ap':float(average_precision_score(yv,scores)),'cutoff':cutoff,
        'recall':float((scores[yv==1]>=cutoff).mean()),'candidate_fpr':float((scores[yv==0]>=cutoff).mean())},
        'training_examples':len(train),'validation_examples':len(val),'limitations':['negative labels include heuristic candidates','candidate FPR does not establish clean-page FPR','only the final encoder block is fine-tuned; small authored positive set']}
    if a.encoder:
        from .train_encoder import train_encoder
        encoder_report=train_encoder(train,val,model_dir)
        reports['minilm']=encoder_report
        # Tie prefers smaller model. Page-level validation remains a separate gate.
        if encoder_report['recall']>reports['linear']['recall']:
            params={'model_id':'minilm-head-int8-v2','backend':'minilm','cutoff':encoder_report['cutoff'],'features':{},'intercept':0.}
    (ROOT/'extension/src/weights.json').write_text(json.dumps(params),encoding='utf-8')
    reports['selected']=params['model_id']
    reports['training_data_sha256']=hashlib.sha256((DATA/'training-texts.jsonl').read_bytes()).hexdigest()
    (model_dir/'training-report.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')
    print(json.dumps(reports,indent=2))
if __name__=='__main__':main()
