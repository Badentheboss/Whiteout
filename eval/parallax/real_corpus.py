"""Fetch reviewed real documentation pages and make inert local variants.

Snapshots stay ignored by Git. Each request is robots-checked and rate-limited;
the generated manifest preserves source URL, license, attribution, and seed.
"""
import json
import time
import urllib.robotparser
import urllib.request
from pathlib import Path
from urllib.parse import urlparse
from .config import DATA, ROOT, SEED
from .prepare import VECTORS, CATEGORIES, PAYLOAD

SOURCES = ROOT / 'data' / 'sources' / 'approved_docs.jsonl'
OUT = DATA / 'external-fixtures'
MANIFEST = DATA / 'external-manifest.jsonl'
AGENT = 'ParallaxResearch/0.1 (+https://github.com/Badentheboss/Whiteout)'

def robots_allows(url: str) -> bool:
 parsed = urlparse(url)
 robots = urllib.robotparser.RobotFileParser(f'{parsed.scheme}://{parsed.netloc}/robots.txt')
 try:
  robots.read()
  return robots.can_fetch(AGENT, url)
 except OSError:
  return False

def fetch(url: str) -> str:
 request = urllib.request.Request(url, headers={'User-Agent': AGENT, 'Accept': 'text/html'})
 with urllib.request.urlopen(request, timeout=30) as response:
  if response.status != 200:
   raise RuntimeError(f'HTTP {response.status}')
  return response.read().decode(response.headers.get_content_charset() or 'utf-8', errors='replace')

def inject(html: str, payload: str) -> str:
 body_close = html.lower().rfind('</body>')
 return html[:body_close] + payload + html[body_close:] if body_close >= 0 else html + payload

def main():
 OUT.mkdir(parents=True, exist_ok=True)
 sources = [json.loads(line) for line in SOURCES.read_text(encoding='utf-8').splitlines()]
 rows = []
 for source_index, source in enumerate(sources):
  if not robots_allows(source['url']):
   print(f"skipped robots: {source['source_id']}")
   continue
  try:
   html = fetch(source['url'])
  except Exception as error:
   print(f"skipped fetch {source['source_id']}: {error}")
   continue
  for vector_index, (vector, injection) in enumerate(VECTORS):
   page_id = f"external-{source['source_id']}-{vector}"
   path = OUT / f'{page_id}.html'
   path.write_text(inject(html, injection), encoding='utf-8')
   rows.append({'page_id':page_id, 'source_url':source['url'], 'snapshot_path':str(path.relative_to(ROOT)), 'license':source['license'], 'license_url':source['license_url'], 'attribution':source['attribution'], 'variant_id':f'{page_id}-s{SEED}', 'is_injected':True, 'vector':vector, 'payload_category':CATEGORIES[(source_index + vector_index) % len(CATEGORIES)], 'payload_text':PAYLOAD, 'ground_truth_node':'.injected' if vector != 'comment' else '<!--comment-->', 'seed':SEED, 'extractor_profiles':['raw-html','text-content','inner-text','accessibility-tree']})
  time.sleep(1)
 MANIFEST.write_text(''.join(json.dumps(row) + '\n' for row in rows), encoding='utf-8')
 print(f'prepared {len(rows)} real-page variants from {len(rows) // len(VECTORS)} sources: {MANIFEST}')

if __name__ == '__main__':
 main()
