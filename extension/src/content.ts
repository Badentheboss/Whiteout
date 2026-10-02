import {VERSION,config,type DetectorId} from './config';
import {scan,sanitize,undo,owned,scanRoots} from './engine';
let tail:Promise<unknown>=Promise.resolve(); let overlay:HTMLElement|null=null;let timer:number|undefined;
function clearOverlay(){overlay?.remove();overlay=null;}
async function execute(request:any) {
 if(request.action==='hello')return {version:VERSION,schema_version:2,config,url:location.href};
 if(request.action==='undo'){observer.disconnect();const count=undo();clearOverlay();observe();return {count};}
 observer.disconnect();clearOverlay();
 try {
  const report=await scan(request.detector||'rules');
  if(request.action==='sanitize')return {...report,actions:sanitize(report.findings)};
  if(request.action==='warn') {
   overlay=document.createElement('div');owned.add(overlay);const shadow=overlay.attachShadow({mode:'closed'});
   const banner=document.createElement('div');
   banner.textContent='Parallax: '+report.findings.length+' hidden-content candidates. Review the extension report before sanitizing.';
   banner.style.cssText='position:fixed;top:12px;right:12px;max-width:360px;padding:12px;background:#17223b;color:white;font:14px/1.5 system-ui;border-radius:8px;z-index:2147483647;pointer-events:none';
   shadow.append(banner);
   for(const f of report.findings.filter(f=>f.frame==='top')) {
    const marker=document.createElement('div');marker.style.cssText='position:fixed;pointer-events:none;z-index:2147483647;border:2px solid #e5484d;box-sizing:border-box;left:'+f.rect.x+'px;top:'+f.rect.y+'px;width:'+f.rect.width+'px;height:'+f.rect.height+'px';
    marker.title=f.reasons.join(', ');shadow.append(marker);
   }
   document.documentElement.append(overlay);
  }
  return report;
 } finally {observe();}
}
function observe(){
 const options={subtree:true,childList:true,characterData:true,attributes:true};
 observer.observe(document.documentElement,options);
 for(const root of scanRoots)observer.observe(root,options);
}
const observer=new MutationObserver(()=>{
 clearTimeout(timer);timer=window.setTimeout(()=>{tail=tail.then(()=>execute({action:'scan',detector:'rules'})).then(report=>chrome.runtime.sendMessage({type:'report',report})).catch(()=>{});},config.mutationDebounceMs);
});
observe();
chrome.runtime.onMessage.addListener((request,_sender,reply)=>{
 if(request.type!=='parallax')return;
 tail=tail.then(()=>execute(request)).then(reply).catch(error=>reply({error:String(error)}));return true;
});
chrome.runtime.sendMessage({type:'ready',version:VERSION}).catch(()=>{});
