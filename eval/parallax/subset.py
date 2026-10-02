"""A declared development subset, not a replacement for the full benchmark."""
import argparse
from .dataset import load,save,VECTORS
from .config import DATA
def main():
    p=argparse.ArgumentParser();p.add_argument('--split',choices=['validation','test'],default='validation');a=p.parse_args()
    source=[r for r in load(DATA/'research-manifest.jsonl') if r['split']==a.split];result=[]
    for group in sorted({r['source_group'] for r in source}):
        rows=[r for r in source if r['source_group']==group]
        result.append(next(r for r in rows if not r['is_injected']))
        for vector in VECTORS:result.append(next(r for r in rows if r['vector']==vector))
    path=DATA/(a.split+'-subset.jsonl');save(path,result);print(path,len(result))
if __name__=='__main__':main()
