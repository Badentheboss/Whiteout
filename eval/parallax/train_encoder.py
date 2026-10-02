"""CPU fine-tuning and quantized ONNX export of a compact instruction classifier."""
import hashlib,json,ssl,urllib.request
import certifi,numpy as np,torch
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score
from transformers import AutoTokenizer,AutoModel
from onnxruntime.quantization import quantize_dynamic,QuantType
from .train import mask,operating_point

def train_encoder(train,val,folder):
    torch.manual_seed(42);torch.set_num_threads(2)
    model_id='sentence-transformers/all-MiniLM-L6-v2'
    ctx=ssl.create_default_context(cafile=certifi.where())
    revision='1110a243fdf4706b3f48f1d95db1a4f5529b4d41'
    downloaded=folder/'minilm-source';downloaded.mkdir(exist_ok=True)
    for name in ['config.json','tokenizer.json','tokenizer_config.json','special_tokens_map.json','vocab.txt','model.safetensors']:
        path=downloaded/name
        if not path.exists():
            with urllib.request.urlopen(f'https://huggingface.co/{model_id}/resolve/{revision}/{name}',context=ctx,timeout=120) as r:
                path.write_bytes(r.read())
    encoder=AutoModel.from_pretrained(downloaded,attn_implementation='eager')
    tokenizer=AutoTokenizer.from_pretrained(downloaded)
    # Fine-tune only the final encoder block and head, preserving a modest CPU budget.
    for parameter in encoder.parameters():parameter.requires_grad=False
    for parameter in encoder.encoder.layer[-1].parameters():parameter.requires_grad=True
    head=torch.nn.Linear(encoder.config.hidden_size,1)
    class Classifier(torch.nn.Module):
        def __init__(self):super().__init__();self.encoder=encoder;self.head=head
        def embed(self,ids,mask_):
            hidden=self.encoder(input_ids=ids,attention_mask=mask_,return_dict=False)[0]
            pooled=(hidden*mask_.unsqueeze(-1)).sum(1)/mask_.sum(1,keepdim=True).clamp(min=1)
            return torch.nn.functional.normalize(pooled,p=2,dim=1)
        def forward(self,input_ids,attention_mask):return torch.sigmoid(self.head(self.embed(input_ids,attention_mask))).squeeze(-1)
    net=Classifier();net.train()
    optimizer=torch.optim.AdamW([p for p in net.parameters() if p.requires_grad],lr=2e-4)
    order=np.random.default_rng(42).permutation(len(train))[:1024]
    for start in range(0,len(order),16):
        batch=[train[i] for i in order[start:start+16]]
        data=tokenizer([mask(r['text']) for r in batch],padding='max_length',truncation=True,max_length=128,return_tensors='pt')
        labels=torch.tensor([r['label'] for r in batch],dtype=torch.float32)
        optimizer.zero_grad();loss=torch.nn.functional.binary_cross_entropy(net(data['input_ids'],data['attention_mask']),labels)
        loss.backward();optimizer.step()
    net.eval()
    def embeddings(rows):
        values=[]
        with torch.no_grad():
            for start in range(0,len(rows),32):
                batch=tokenizer([mask(r['text']) for r in rows[start:start+32]],padding='max_length',truncation=True,max_length=128,return_tensors='pt')
                values.append(net.embed(batch['input_ids'],batch['attention_mask']).numpy())
        return np.concatenate(values)
    x=embeddings(train);xv=embeddings(val);y=np.array([r['label'] for r in train]);yv=np.array([r['label'] for r in val])
    lr=LogisticRegression(C=2,class_weight='balanced',max_iter=1000,random_state=42).fit(x,y)
    with torch.no_grad():
        head.weight.copy_(torch.tensor(lr.coef_,dtype=torch.float32));head.bias.copy_(torch.tensor(lr.intercept_,dtype=torch.float32))
    sample=tokenizer(['Example'],padding='max_length',max_length=128,return_tensors='pt')
    raw=folder/'minilm.onnx';out=folder/'minilm-int8.onnx'
    torch.onnx.export(net,(sample['input_ids'],sample['attention_mask']),str(raw),input_names=['input_ids','attention_mask'],output_names=['scores'],
       dynamic_axes={'input_ids':{0:'batch'},'attention_mask':{0:'batch'},'scores':{0:'batch'}},opset_version=17,dynamo=False)
    quantize_dynamic(str(raw),str(out),weight_type=QuantType.QInt8)
    import onnxruntime as ort
    session=ort.InferenceSession(str(out),providers=['CPUExecutionProvider'])
    scores=[]
    for start in range(0,len(val),32):
        batch=tokenizer([mask(r['text']) for r in val[start:start+32]],padding='max_length',truncation=True,max_length=128,return_tensors='np')
        scores.extend(session.run(None,{k:batch[k] for k in ['input_ids','attention_mask']})[0].tolist())
    scores=np.array(scores);cutoff=operating_point(yv,scores)
    (folder/'vocab.json').write_text(json.dumps(tokenizer.get_vocab()),encoding='utf-8')
    report={'revision':revision,'model_id':model_id,'license':'Apache-2.0','trained':'last encoder block + linear classification head',
      'quantized_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'bytes':out.stat().st_size,
      'validation_ap':float(average_precision_score(yv,scores)),'cutoff':cutoff,'max_tokens':128,
      'recall':float((scores[yv==1]>=cutoff).mean()),'candidate_fpr':float((scores[yv==0]>=cutoff).mean())}
    (folder/'encoder-report.json').write_text(json.dumps(report,indent=2))
    return report
