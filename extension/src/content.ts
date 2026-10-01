import { config } from './config';
import { registry } from './detectors';
import type { Finding } from './types';
let findings: Finding[] = [];
function apply() {
  findings = registry[config.detector].detect(document);
  if (config.mode === 'sanitize') for (const finding of findings) { const el=document.querySelector(finding.selector); if (el) { (el as HTMLElement).dataset.parallaxSanitized='true'; (el as HTMLElement).style.setProperty('display','none','important'); finding.sanitized=true; } }
  chrome.runtime.sendMessage({ type:'parallax-report', report:{url:location.href, scannedAt:new Date().toISOString(), findings} }).catch(()=>undefined);
  document.querySelectorAll('[data-parallax-flag]').forEach(e=>e.remove());
  for (const f of findings) { const el=document.querySelector(f.selector) as HTMLElement | null; if (el && f.vector !== 'comment') { el.dataset.parallaxFlag='true'; el.title=`Parallax: ${f.reasons.join(', ')}`; el.style.outline='2px solid #e5484d'; } }
}
let timer: number | undefined; new MutationObserver(()=>{ clearTimeout(timer); timer=window.setTimeout(apply,config.mutationDebounceMs); }).observe(document.documentElement,{subtree:true,childList:true,characterData:true,attributes:true});
apply();
chrome.runtime.onMessage.addListener((msg,_,reply)=>{ if(msg.type==='parallax-get-report') reply({ findings }); });
