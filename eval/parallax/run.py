"""Immutable, resumable experiments against the actual packaged extension."""
import argparse, asyncio, hashlib, json, platform, sys, time, uuid, shutil, gzip
from datetime import datetime, timezone
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from threading import Thread
from importlib.metadata import distributions
from urllib.parse import urlsplit
import numpy as np
from PIL import Image
from skimage.metrics import structural_similarity
from .config import ROOT,DATA,RUNS
from .dataset import load,validate
from .browser import ExtensionBrowser
from .metrics import injection_hit,naive_agent,content_requests,overlap
from .extractors import extract as extraction, exposure, equality
from .interactions import execute as execute_task, validate_steps

class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args): pass

def pixel_metrics(a,b):
    from io import BytesIO
    x=np.array(Image.open(BytesIO(a)).convert('RGB'));y=np.array(Image.open(BytesIO(b)).convert('RGB'))
    if x.shape!=y.shape:return {'changed_fraction':None,'ssim':None,'reason':'shape-changed'}
    return {'changed_fraction':float(np.mean(np.max(np.abs(x.astype(float)-y),axis=2)>8)),
            'ssim':float(structural_similarity(x,y,channel_axis=2,data_range=255))}

async def run(args):
    manifest=Path(args.manifest).resolve();rows=load(manifest);validate(rows)
    lock_path=getattr(args,'lock',None)
    if lock_path:
        from .freeze import check
        lock=json.loads(Path(lock_path).read_text(encoding='utf-8'))
        failures=check(ROOT,lock)
        if failures:raise ValueError('Frozen files changed: '+', '.join(failures))
        if (ROOT/lock['manifest']).resolve()!=manifest:raise ValueError('Lock belongs to another manifest')
    if args.split!='all':rows=[r for r in rows if r['split']==args.split]
    if args.limit:rows=rows[:args.limit]
    if not rows:raise ValueError('No manifest rows selected')
    run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
    folder=Path(args.resume).resolve() if args.resume else RUNS/run_id
    folder.mkdir(parents=True,exist_ok=bool(args.resume));(folder/'pages').mkdir(exist_ok=True)
    packaged=folder/'extension'
    if not args.resume:shutil.copytree(ROOT/'extension/dist',packaged)
    fingerprint=hashlib.sha256(manifest.read_bytes()).hexdigest()
    extension_hash=hashlib.sha256()
    for asset in sorted(packaged.rglob('*')):
        if asset.is_file():extension_hash.update(str(asset.relative_to(packaged)).encode());extension_hash.update(asset.read_bytes())
    harness_hash=hashlib.sha256()
    for code in sorted(Path(__file__).parent.glob('*.py')):harness_hash.update(code.name.encode());harness_hash.update(code.read_bytes())
    if not args.resume:
        (folder/'harness').mkdir()
        for code in Path(__file__).parent.glob('*.py'):shutil.copyfile(code,folder/'harness'/code.name)
        shutil.copyfile(manifest,folder/'manifest.jsonl')
    config={'manifest_sha256':fingerprint,'harness_sha256':harness_hash.hexdigest(),'split':args.split,'limit':args.limit,'detectors':args.detectors,'repeats':3,
            'extension_sha256':extension_hash.hexdigest(),
            'freeze_sha256':hashlib.sha256(Path(lock_path).read_bytes()).hexdigest() if lock_path else None}
    metadata_path=folder/'metadata.json'
    if args.resume:
        previous=json.loads(metadata_path.read_text())
        if previous['config']!=config:raise ValueError('Resume configuration or extension mismatch')
        run_id=previous['run_id']
    else:
        metadata={'schema_version':2,'run_id':run_id,'created_at':datetime.now(timezone.utc).isoformat(),'config':config,
         'environment':{'os':platform.platform(),'cpu':platform.processor(),'machine':platform.machine(),
         'python':sys.version,'libraries':{d.metadata['Name']:d.version for d in distributions()}},
         'agent':'scripted-naive-v3','real_llm':None,'real_llm_reason':'not configured',
         'node_precision':None,'node_precision_reason':'source-page nodes need human labels'}
        metadata_path.write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    done=set()
    if (folder/'observations.jsonl').exists():
        done={(r['variant_id'],r['detector']) for r in load(folder/'observations.jsonl')}
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)))
    Thread(target=server.serve_forever,daemon=True).start()
    try:
        async with ExtensionBrowser(packaged) as browser:
            metadata=json.loads(metadata_path.read_text());metadata['browser']=browser.context.browser.version if browser.context.browser else 'persistent-chromium'
            metadata_path.write_text(json.dumps(metadata,indent=2),encoding='utf-8')
            requests=[]
            def capture(req):
                requests.append({'url':req.url,'method':req.method,'post_data':req.post_data})
            browser.context.on('request',capture)
            async def route(request_route):
                url=request_route.request.url;parts=urlsplit(url)
                if parts.scheme in ('chrome-extension','data','blob') or (parts.hostname=='127.0.0.1' and parts.port==server.server_port):
                    await request_route.continue_()
                else:await request_route.abort()
            await browser.context.route('**/*',route)
            for index,item in enumerate(rows):
                for detector in args.detectors:
                    if (item['variant_id'],detector) in done:continue
                    page=await browser.context.new_page()
                    started=len(requests)
                    try:
                        expected=item.get('variant_sha256')
                        if expected and hashlib.sha256((ROOT/item['snapshot_path']).read_bytes()).hexdigest()!=expected:
                            raise ValueError('Replay content hash mismatch')
                        await page.add_init_script("""window.__parallaxLongTasks=[];try {new PerformanceObserver(l=>window.__parallaxLongTasks.push(...l.getEntries().map(e=>e.duration))).observe({type:'longtask',buffered:true})}catch{}""")
                        url=f"http://127.0.0.1:{server.server_port}/"+Path(item['snapshot_path']).as_posix()
                        await page.goto(url,wait_until='load',timeout=30000);hello=await browser.ready(page)
                        interaction_before=None
                        steps=item.get('interaction_steps')
                        if steps:
                            validate_steps(steps)
                            interaction_before=await execute_task(page,steps)
                            # Discard task side effects before scan and screenshot measurements.
                            await page.goto(url,wait_until='load',timeout=30000);hello=await browser.ready(page)
                        cdp=await browser.context.new_cdp_session(page);await cdp.send('Performance.enable')
                        before=await extraction(page,cdp);shot_before=await page.screenshot()
                        await page.evaluate('window.__parallaxLongTasks=[]')
                        timings=[];report=None;initial_metrics=await cdp.send('Performance.getMetrics')
                        for repeat in range(3):
                            report=await asyncio.wait_for(browser.request(page,'scan',detector),timeout=120)
                            timings.append({'scan_ms':report['scan_ms'],'inference_ms':report['inference_ms'],'phase':'cold' if repeat==0 else 'warm'})
                        assert report['version']==hello['version']
                        for candidate in report['candidates']:
                            candidate['ground_truth_match']=bool(item['is_injected']) and overlap(candidate['normalized'],item.get('payload_text',''))
                            candidate['exposure_reasons']={}
                            for profile in ['raw-html','text-content','inner-text','accessibility-tree']:
                                candidate['profiles'][profile],candidate['exposure_reasons'][profile]=exposure(candidate,before,profile)
                        long_before=await page.evaluate('window.__parallaxLongTasks')
                        actions=(await browser.request(page,'sanitize',detector))['actions']
                        after=await extraction(page,cdp);shot_after=await page.screenshot()
                        task=item.get('task');task_success=None;task_reason='No reviewed interaction task for this source replay'
                        interaction_after=None
                        if steps:
                            interaction_after=await execute_task(page,steps)
                            task_success=interaction_after['success'];task_reason=interaction_after['reason']
                        elif task:
                            try:
                                await page.locator(task['selector']).click(timeout=3000)
                                task_success=(await page.locator(task['selector']).inner_text())==task['expected'];task_reason=None
                            except Exception as task_error:task_success=False;task_reason=str(task_error)
                        final_metrics=await cdp.send('Performance.getMetrics')
                        heap=lambda metrics:next((r['value'] for r in metrics['metrics'] if r['name']=='JSHeapUsedSize'),None)
                        h0,h1=heap(initial_metrics),heap(final_metrics)
                        # Any instrumentation traffic containing page content is counted, not assumed absent.
                        traffic=requests[started:];probes=[item.get('canary',''),item.get('payload_text','')]
                        leaks=content_requests(traffic,probes)
                        hit=injection_hit(report['findings'],item.get('payload_text','')) if item['is_injected'] else None
                        row={'schema_version':2,'run_id':run_id,'variant_id':item['variant_id'],'page_id':item['page_id'],
                         'source_group':item['source_group'],'split':item['split'],'vector':item.get('vector'),'payload_category':item.get('payload_category'),
                         'is_injected':item['is_injected'],'canary':item.get('canary'),'detector':detector,'model':report['model'],'hit':hit,'flag_count':len(report['findings']),
                         'truncated':report['truncated'],'detector_config':report['config'],'limitations':report['limitations'],'timings':timings,'findings':report['findings'],'candidates':report['candidates'],
                         'sanitization':actions,'preservation':{**pixel_metrics(shot_before,shot_after),'visible_text_equal':before['inner-text']==after['inner-text'],
                         'controls_equal':before['controls']==after['controls'],'accessibility_equal':equality(before['accessibility-tree'],after['accessibility-tree']),
                         'eligible':item.get('preservation_eligible',False)},
                         'interaction_task_success':task_success,'interaction_task_reason':task_reason,
                         'interaction_before':interaction_before,'interaction_after':interaction_after,
                         'interaction_preserved':interaction_after['success'] if interaction_before and interaction_before['success'] else None,
                         'heap_delta':None if h0 is None or h1 is None else h1-h0,'long_tasks_ms':long_before,
                         'network':{'attempts':traffic,'page_content_attempts':len(leaks),'coverage':'requests visible to Playwright context; not an OS-wide audit'},
                         'profiles':{p:profile_result(item,before,after,p) for p in ['raw-html','text-content','inner-text','accessibility-tree']}}
                        key=item['variant_id']+'-'+detector
                        scored=[c for c in row['candidates'] if c['hidden'] and c['score'] is not None]
                        row['max_hidden_score']=max((c['score'] for c in scored),default=None)
                        row['best_payload_score']=max((c['score'] for c in scored if c.get('ground_truth_match')),default=None)
                        detail={k:row.pop(k) for k in ['findings','candidates','sanitization']}
                        row['report_path']='pages/'+key+'-report.json.gz'
                        with gzip.open(folder/row['report_path'],'wt',encoding='utf-8') as f:json.dump(detail,f)
                        row['report_sha256']=hashlib.sha256((folder/row['report_path']).read_bytes()).hexdigest()
                        (folder/'pages'/f'{key}-before.png').write_bytes(shot_before)
                        (folder/'pages'/f'{key}-after.png').write_bytes(shot_after)
                        (folder/'pages'/f'{key}-extraction.json').write_text(json.dumps({'before':before,'after':after}),encoding='utf-8')
                        with (folder/'observations.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(row)+'\n')
                    except Exception as error:
                        with (folder/'errors.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps({'variant_id':item['variant_id'],'detector':detector,'error':str(error)})+'\n')
                    finally:await page.close()
                print(f'{index+1}/{len(rows)} {item["variant_id"]}',flush=True)
    finally:server.shutdown();server.server_close()
    completed=len(load(folder/'observations.jsonl')) if (folder/'observations.jsonl').exists() else 0
    planned=len(rows)*len(args.detectors)
    (folder/'completion.json').write_text(json.dumps({'planned':planned,'completed':completed,'status':'complete' if completed==planned else 'complete-with-failures','finished_at':datetime.now(timezone.utc).isoformat()},indent=2),encoding='utf-8')
    (DATA/'latest-run.txt').write_text(str(folder.relative_to(ROOT)),encoding='utf-8')
    print(folder)

def profile_result(item,before,after,profile):
    pre,post=before[profile],after[profile];canary=item.get('canary')
    return {'exposed':bool(canary and canary in pre) if pre is not None else None,
            'agent_off':naive_agent(pre) if pre is not None else None,
            'agent_on':naive_agent(post) if post is not None else None,
            'canary_success_off':naive_agent(pre)==canary if pre is not None and item['is_injected'] else None,
            'canary_success_on':naive_agent(post)==canary if post is not None and item['is_injected'] else None,
            'payload_remaining':bool(canary and canary in post) if post is not None else None,
            'unavailable_before':before.get('unavailable',{}).get(profile),
            'unavailable_after':after.get('unavailable',{}).get(profile)}

def main():
    p=argparse.ArgumentParser();p.add_argument('--manifest',default=str(DATA/'research-manifest.jsonl'));p.add_argument('--limit',type=int);p.add_argument('--split',choices=['all','train','validation','test'],default='validation');p.add_argument('--resume');p.add_argument('--lock',help='Verify an offline experiment lock before starting');p.add_argument('--detectors',nargs='+',default=['rules','classifier'],choices=['rules','classifier']);a=p.parse_args()
    asyncio.run(run(a))
if __name__=='__main__':main()
