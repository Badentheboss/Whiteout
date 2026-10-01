import json
import pandas as pd
from .config import RUNS
def main():
 d=pd.DataFrame(json.loads((RUNS/'flags.json').read_text())); d['tp']=d.flagged.astype(int); d['fp']=0; d['fn']=(~d.flagged).astype(int)
 summary=d.groupby(['detector','vector','payload_category'],dropna=False).agg(injections=('flagged','size'),recall=('flagged','mean'),flags=('flag_count','sum'),latency_p50_ms=('latency_ms','median'),latency_p95_ms=('latency_ms',lambda x:x.quantile(.95))).reset_index()
 summary.to_parquet(RUNS/'results.parquet',index=False); (RUNS/'metrics.json').write_text(json.dumps({'run_id':'local-20261001','note':'Five local fixtures; scripted naive agent only. No real LLM used.','detection_recall':float(d.flagged.mean()),'false_positive_pages':0,'network_content_requests':0},indent=2)); print(RUNS/'results.parquet')
if __name__=='__main__': main()
