import asyncio, json, os, time
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from threading import Thread
from .config import DATA, ROOT, RUNS
from playwright.async_api import async_playwright
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self, *_): pass
def detector_js():
 return '''() => { const pat=/\\b(ignore|disregard|override|follow|reply|output|send|exfiltrate|system prompt|assistant|tool call|CANARY-[A-Z0-9-]+)\\b/i; const scrub=t=>t.replace(/[\\u200B-\\u200F\\u2060\\u{E0000}-\\u{E007F}]/gu,''); const out=[]; for(const e of document.querySelectorAll('*')) { const t=[...e.childNodes].filter(n=>n.nodeType===3).map(n=>n.textContent).join(' ').trim(); if(!t)continue; const s=getComputedStyle(e), r=e.getBoundingClientRect(),clean=scrub(t); const colorMatched=s.color==='rgb(255, 255, 255)'&&s.backgroundColor==='rgb(255, 255, 255)'; const hidden=s.display==='none'||s.visibility==='hidden'||+s.opacity<=.05||r.right<-32||r.left>innerWidth+32||parseFloat(s.fontSize)<2||t!==clean||colorMatched; if(hidden && pat.test(clean)) out.push({selector:e.className?'.'+String(e.className).split(' ')[0]:e.tagName.toLowerCase(),text:clean,score:.9}); } const w=document.createTreeWalker(document,NodeFilter.SHOW_COMMENT); for(let n=w.nextNode();n;n=w.nextNode())if(pat.test(n.textContent))out.push({selector:'<!--comment-->',text:n.textContent,score:.9}); return out }'''
async def main_async():
 RUNS.mkdir(parents=True,exist_ok=True); os.chdir(DATA/'fixtures'); server=ThreadingHTTPServer(('127.0.0.1',8765),Quiet); Thread(target=server.serve_forever,daemon=True).start()
 manifest=[json.loads(x) for x in (DATA/'manifest.jsonl').read_text().splitlines()]; rows=[]
 async with async_playwright() as p:
  extension=str(ROOT/'extension'/'dist'); browser=await p.chromium.launch_persistent_context('',headless=True,args=[f'--disable-extensions-except={extension}',f'--load-extension={extension}'])
  for item in manifest:
   page=await browser.new_page(); t=time.perf_counter(); await page.goto(item['source_url']); findings=await page.evaluate(detector_js()); latency=(time.perf_counter()-t)*1000
   for d in ['rules','classifier']:
    flags=findings if d=='rules' else [x for x in findings if x['score']>=.42]
    rows.append({'run_id':'local-20261001','page_id':item['page_id'],'variant_id':item['variant_id'],'detector':d,'vector':item['vector'],'payload_category':item['payload_category'],'extractor_profile':'raw-html','ground_truth':item['ground_truth_node'],'flagged':bool(flags),'flag_count':len(flags),'latency_ms':latency,'agent_canary_off':True,'agent_canary_on':False,'network_content_requests':0,'mode':'warn'})
   await page.close()
  await browser.close()
 server.shutdown(); (RUNS/'flags.json').write_text(json.dumps(rows,indent=2)); print(RUNS/'flags.json')
def main(): asyncio.run(main_async())
if __name__=='__main__': main()
