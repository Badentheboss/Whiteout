"""Offline coverage/provenance and near-duplicate screening; no detector execution."""
import argparse
import json
from itertools import combinations

from bs4 import BeautifulSoup
from .dataset import load, validate
from .freeze import safe_path, digest
from .config import ROOT
from .metrics import tokens


def shingles(text, width=5):
    words = tokens(text)
    return {tuple(words[i:i+width]) for i in range(max(0,len(words)-width+1))}


def near_duplicates(pages, threshold=.85):
    """Exact shingle Jaccard screen. Related-content flag, not semantic proof."""
    if not 0 < threshold <= 1:
        raise ValueError('threshold must be in (0,1]')
    prepared = [(page,shingles(page['text'])) for page in pages]
    matches = []
    for (left,a),(right,b) in combinations(prepared,2):
        if not a or not b or min(len(a),len(b))/max(len(a),len(b)) < threshold:
            continue
        score=len(a & b)/len(a | b)
        if score >= threshold:
            matches.append({'left':left['page_id'],'right':right['page_id'],
                            'jaccard':score,'cross_split':left['split']!=right['split'],
                            'action':'Review; group related sources before regenerating splits'})
    return matches


def audit(root, rows):
    validate(rows)
    bases={row['page_id']:row for row in rows if not row['is_injected']}
    failures=[];pages=[];categories={}
    for row in bases.values():
        category=row.get('category','unknown');categories[category]=categories.get(category,0)+1
        for field in ['license_url','license_sha256','retrieved_at','attribution','source_sha256']:
            if not row.get(field):failures.append({'page_id':row['page_id'],'reason':'Missing provenance: '+field})
        path=safe_path(root,row['snapshot_path'])
        if not path.exists():
            failures.append({'page_id':row['page_id'],'reason':'Replay not available locally'});continue
        if digest(path)!=row.get('variant_sha256'):
            failures.append({'page_id':row['page_id'],'reason':'Replay checksum missing or changed'})
        soup=BeautifulSoup(path.read_text(encoding='utf-8'),'html.parser')
        main=soup.select_one('main,article,[role=main]') or soup.body or soup
        pages.append({**row,'text':main.get_text(' ',strip=True)})
    duplicates=near_duplicates(pages)
    return {'base_pages':len(bases),'projects':len({r['source_group'] for r in bases.values()}),
            'categories':categories,'failures':failures,'near_duplicates':duplicates,
            'cross_split_near_duplicates':sum(r['cross_split'] for r in duplicates),
            'limitations':['Lexical similarity does not establish semantic independence',
                           'Terms and asset-license review cannot be inferred from checksums'],
            'benchmark_executed':False}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--manifest',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args();result=audit(ROOT,load(args.manifest))
    with open(args.output,'x',encoding='utf-8') as stream:json.dump(result,stream,indent=2)
    print('Offline audit written; no detector, training or agent was run')


if __name__=='__main__':main()
