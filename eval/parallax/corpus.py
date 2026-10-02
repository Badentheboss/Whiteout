"""Acquisition, provenance and inert replay for public licensed documentation."""
import argparse, hashlib, json, re, ssl, time, os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urldefrag
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.robotparser import RobotFileParser
import certifi
from bs4 import BeautifulSoup
from .config import DATA
from .sources import PROJECTS

AGENT='ParallaxResearch/0.2 (+https://github.com/Badentheboss/Whiteout)'
CTX=ssl.create_default_context(cafile=os.environ.get('PARALLAX_CA_BUNDLE') or certifi.where())
CACHE=DATA/'corpus'
def digest(b): return hashlib.sha256(b).hexdigest()
def write_json(path,value): path.write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding='utf-8')

class Client:
    def __init__(self):
        self.policies={};self.last={};self.events=[]
    def _get(self,url):
        host=urlsplit(url).netloc
        delay=max(0,1-(time.monotonic()-self.last.get(host,0)))
        if delay: time.sleep(delay)
        self.last[host]=time.monotonic()
        with urlopen(Request(url,headers={'User-Agent':AGENT}),context=CTX,timeout=20) as r:
            raw=r.read(4_000_001)
            if len(raw)>4_000_000: raise ValueError('response-too-large')
            return raw,r.geturl(),r.headers.get_content_type()
    def get(self,url):
        parts=urlsplit(url)
        if parts.scheme!='https': raise ValueError('only-public-https')
        origin=f'{parts.scheme}://{parts.netloc}'
        if origin not in self.policies:
            robot=RobotFileParser(origin+'/robots.txt')
            try:
                raw,_,_=self._get(origin+'/robots.txt');robot.parse(raw.decode('utf-8',errors='replace').splitlines())
                self.policies[origin]=robot
            except HTTPError as e:
                if e.code==404: robot.parse([]);self.policies[origin]=robot
                else: raise RuntimeError(f'robots-http-{e.code}') from e
        policy=self.policies[origin]
        if not policy.can_fetch(AGENT,url): raise RuntimeError('robots-disallowed')
        crawl=policy.crawl_delay(AGENT) or policy.crawl_delay('*') or 1
        host=parts.netloc
        if (wait:=crawl-(time.monotonic()-self.last.get(host,0)))>0:time.sleep(wait)
        raw,final,kind=self._get(url)
        if urlsplit(final).netloc!=host: raise RuntimeError('cross-origin-redirect-requires-review')
        return raw,final,kind

def acquire_project(entry,limit=10,review=None):
    project,seed,license_url,license_name=entry
    folder=CACHE/project;folder.mkdir(parents=True,exist_ok=True)
    client=Client();records=[];failures=[]
    try:
        license_path=folder/'LICENSE.source'
        if not license_path.exists():
            # Raw GitHub repository licenses are fetched without crawling.
            with urlopen(Request(license_url,headers={'User-Agent':AGENT}),context=CTX,timeout=20) as r:
                license_path.write_bytes(r.read(2_000_000))
        license_hash=digest(license_path.read_bytes())
        queue=[seed];seen=set();hashes=set()
        while queue and len(records)<limit and len(seen)<40:
            url=queue.pop(0)
            if url in seen:continue
            seen.add(url)
            try:
                key=digest(url.encode())[:16];raw_path=folder/(key+'.source.html')
                meta_path=folder/(key+'.meta.json')
                if raw_path.exists() and meta_path.exists():
                    raw=raw_path.read_bytes();meta=json.loads(meta_path.read_text());final=meta['final_url']
                else:
                    raw,final,kind=client.get(url)
                    if kind!='text/html':continue
                    raw_path.write_bytes(raw);meta={'final_url':final,'retrieved_at':datetime.now(timezone.utc).isoformat()}
                    write_json(meta_path,meta)
                soup=BeautifulSoup(raw,'html.parser')
                for a in soup.select('a[href]'):
                    link=urldefrag(urljoin(final,a['href']))[0];p=urlsplit(link)
                    if p.netloc==urlsplit(seed).netloc and p.scheme=='https' and not p.query and not re.search(r'\.(zip|pdf|png|jpg|svg|gz|xml|txt)$',p.path) and link not in seen and link not in queue:
                        queue.append(link)
                main=soup.select_one('main,article,[role=main]') or soup.body
                if main is None:continue
                content_hash=digest(re.sub(r'\s+',' ',main.get_text(' ',strip=True)).encode())
                if content_hash in hashes:continue
                hashes.add(content_hash)
                transformations=[];assets=[];missing=[]
                for script in soup.select('script,iframe,object,embed,base'):
                    script.decompose();transformations.append('active-content-removed')
                for tag in soup.find_all(True):
                    for attr in list(tag.attrs):
                        if attr.lower().startswith('on'):del tag[attr];transformations.append('event-handler-removed')
                for tag,attr in [(x,'href') for x in soup.select('link[rel=stylesheet][href]')]+[(x,'src') for x in soup.select('img[src]')]:
                    address=urljoin(final,tag.get(attr,''))
                    if address.startswith('data:'):continue
                    asset_id=digest(address.encode())[:16]+('.css' if attr=='href' else '.bin')
                    asset_path=folder/asset_id
                    try:
                        if urlsplit(address).netloc!=urlsplit(final).netloc:raise RuntimeError('third-party-asset')
                        if not asset_path.exists():
                            data,_,_=client.get(address);asset_path.write_bytes(data)
                        if attr=='href' and (b'url(' in asset_path.read_bytes() or b'@import' in asset_path.read_bytes()):
                            missing.append(address+'#nested-assets-not-replayed')
                        tag[attr]=asset_id
                        assets.append({'url':address,'path':str(asset_path.relative_to(DATA)),'sha256':digest(asset_path.read_bytes())})
                    except Exception as e:
                        missing.append(address+':'+str(e));tag.decompose() if attr=='href' else tag.attrs.pop(attr,None)
                for a in soup.select('a[href]'):
                    if not a['href'].startswith('#'):a['href']='#'
                if not soup.head:
                    head=soup.new_tag('head');soup.insert(0,head)
                csp=soup.new_tag('meta');csp['http-equiv']='Content-Security-Policy';csp['content']="default-src 'none'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; script-src 'none'; form-action 'none'; base-uri 'none'"
                soup.head.insert(0,csp)
                replay=folder/(key+'.html');replay.write_text(str(soup),encoding='utf-8')
                records.append({'schema_version':2,'page_id':project+'-'+key,'source_group':project,'source_url':final,
                 'license':license_name,'license_url':license_url,'license_sha256':license_hash,'attribution':project+' contributors',
                 'retrieved_at':meta['retrieved_at'],'content_hash':content_hash,'snapshot_path':str(replay.relative_to(DATA.parent)),
                 'source_sha256':digest(raw),'replay_sha256':digest(replay.read_bytes()),'assets':assets,'missing_assets':missing,
                 'transformations':sorted(set(transformations+['links-disabled','local-replay-csp'])),
                 'preservation_eligible':False,'category':review['category'] if review else 'documentation',
                 'source_review':review,'label_origin':'source-page-unreviewed'})
                print(project,len(records),flush=True)
            except Exception as e:
                failures.append({'url':url,'error_type':type(e).__name__,'reason':str(e)})
    except Exception as e: failures.append({'url':seed,'error_type':type(e).__name__,'reason':str(e)})
    return records,failures

def main():
    p=argparse.ArgumentParser();p.add_argument('--projects',type=int,default=30);p.add_argument('--pages-per-project',type=int,default=10)
    p.add_argument('--registry',help='Reviewed source registry JSONL for broader categories');a=p.parse_args()
    entries=[(entry,None) for entry in PROJECTS[:a.projects]]
    if a.registry:
        from .source_registry import reviewed_sources
        from .dataset import load
        approved=reviewed_sources(load(a.registry))
        entries=[((r['source_group'],r['source_url'],r['license_url'],r['license']),r) for r in approved]
    CACHE.mkdir(parents=True,exist_ok=True)
    records=[];failures=[]
    with ThreadPoolExecutor(max_workers=3) as pool:
        tasks=[pool.submit(acquire_project,e,a.pages_per_project,review) for e,review in entries]
        for task in as_completed(tasks):
            r,f=task.result();records.extend(r);failures.extend(f)
    unique={r['content_hash']:r for r in sorted(records,key=lambda r:r['page_id'])}
    records=list(unique.values())
    (DATA/'base-manifest.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in records),encoding='utf-8')
    write_json(DATA/'acquisition.json',{'pages':len(records),'projects':len({r['source_group'] for r in records}),'failures':failures,'limitations':['documentation-heavy','replay transformations exclude preservation claims','human review pending']})
    print(f'Acquired {len(records)} pages across {len({r["source_group"] for r in records})} projects')
if __name__=='__main__':main()
