import {config, VERSION, type DetectorId} from './config';
import {registry, modelName} from './detectors';
import type {Candidate, Scan} from './types';

type Target={node:Node; el:Element; attribute?:string; pseudo?:string};
const targets=new Map<string,Target>();
const ids=new WeakMap<Node,number>(); let nextId=1;
let undoSteps:(()=>void)[]=[];
export const owned=new WeakSet<Node>();
export const scanRoots:(Document|ShadowRoot)[]=[];
const normalize=(s:string)=>s.replace(/[\u200B-\u200F\u2060]/g,'').replace(/[\u{E0000}-\u{E007F}]/gu,c=>{
 const cp=c.codePointAt(0)!-0xE0000; return cp>=32&&cp<127?String.fromCharCode(cp):'';
});
function rgba(s:string):number[]|null {
 const m=s.match(/[\d.]+/g); if(!m||m.length<3)return null;
 return [...m.slice(0,3).map(Number), m.length>3?Number(m[3]):1];
}
const luminance=(v:number[])=>v.slice(0,3).map(x=>x/255).map(x=>x<=.04045?x/12.92:((x+.055)/1.055)**2.4).reduce((s,x,i)=>s+x*[.2126,.7152,.0722][i],0);
function background(el:Element):{rgb:number[];unknown:boolean} {
 const layers:number[][]=[]; let unknown=false;
 for(let p:Element|null=el;p;p=parent(p)) {
  const s=p.ownerDocument.defaultView!.getComputedStyle(p); if(s.backgroundImage!=='none')unknown=true;
  const c=rgba(s.backgroundColor); if(c)layers.push(c); if(c&&c[3]>=1)break;
 }
 let rgb=[255,255,255]; for(const c of layers.reverse())rgb=rgb.map((x,i)=>c[i]*c[3]+x*(1-c[3]));
 return {rgb,unknown};
}
function parent(el:Element):Element|null {
 return el.parentElement || ((el.getRootNode() as ShadowRoot).host ?? null);
}
function pathOf(el:Element):string {
 const parts:string[]=[]; let p:Element|null=el;
 while(p) {const siblings=p.parentElement?[...p.parentElement.children].filter(s=>s.tagName===p!.tagName):[p];
 parts.unshift(p.tagName.toLowerCase()+':nth-of-type('+(siblings.indexOf(p)+1)+')');p=p.parentElement;}
 return parts.join(' > ');
}
export async function scan(detector:DetectorId='rules'):Promise<Scan> {
 const start=performance.now();targets.clear(); const rows:Candidate[]=[]; const limitations:string[]=[]; let truncated=false;
 scanRoots.length=0;
 async function visit(root:Document|ShadowRoot, frame:string, prefix:string='',inherited:string[]=[]) {
  scanRoots.push(root);
  const doc=root.ownerDocument||root as Document; const view=doc.defaultView!; const walker=doc.createTreeWalker(root,NodeFilter.SHOW_ELEMENT|NodeFilter.SHOW_TEXT|NodeFilter.SHOW_COMMENT);
  let n:Node|null;let visited=0;
  const add=(node:Node,el:Element,text:string,kind:Candidate['kind'],attribute?:string)=>{
   if(!text.trim()||text.length>100000||owned.has(el)||el.closest('script,style,noscript,template'))return;
   if(rows.length>=config.maxCandidates){truncated=true;return;}
   if(!ids.has(node))ids.set(node,nextId++); const id=frame+':'+ids.get(node)+':'+kind+':'+(attribute||'');
   const reasons:string[]=[...inherited];const uncertain:string[]=[];
   const s=view.getComputedStyle(el,kind==='pseudo'?attribute:undefined);let rect=el.getBoundingClientRect();
   if(kind==='text') {const range=doc.createRange();range.selectNodeContents(node);rect=range.getBoundingClientRect();}
   let rendered=true, opacity=1;
   for(let p:Element|null=el;p;p=parent(p)) {
    const st=view.getComputedStyle(p);const r=p.getBoundingClientRect();opacity*=Number(st.opacity);
    if(st.display==='none'){reasons.push('display');rendered=false;}
    if(st.visibility==='hidden'||st.visibility==='collapse'){reasons.push('visibility');rendered=false;}
    if(st.clip==='rect(0px, 0px, 0px, 0px)'||/inset\(50%/.test(st.clipPath))reasons.push('clip');
    if(st.clipPath!=='none'&&!/inset\(50%/.test(st.clipPath))uncertain.push('complex-clip-path');
    if(['hidden','clip'].includes(st.overflow)&&(r.width<2||r.height<2))reasons.push('clip');
   }
   if(opacity<=config.opacityThreshold)reasons.push('opacity');
   if(parseFloat(s.fontSize)<config.minFontPx)reasons.push('tiny-font');
   // Below-the-fold text remains reachable through normal scrolling.
   if(rect.right < -config.offscreenMarginPx || rect.bottom < -config.offscreenMarginPx ||
      (['fixed','absolute'].includes(s.position)&&rect.left>Math.max(doc.documentElement.scrollWidth,view.innerWidth)+config.offscreenMarginPx))reasons.push('offscreen');
   if(kind==='comment')reasons.push('comment');
   if(kind==='attribute')reasons.push('attribute');
   const normalized=normalize(text); if(normalized!==text)reasons.push('unicode');
   const bg=background(el), fg=rgba(s.color);
   if(bg.unknown)uncertain.push('image-or-gradient-background');
   else if(fg) {const rgb=bg.rgb.map((b,i)=>fg[i]*fg[3]+b*(1-fg[3]));const a=luminance(rgb),b=luminance(bg.rgb);
    if((Math.max(a,b)+.05)/(Math.min(a,b)+.05)<config.contrastRatio)reasons.push('low-contrast');
   }
   if(rendered&&rect.width>1&&rect.height>1&&rect.top>=0&&rect.bottom<view.innerHeight&&rect.left>=0&&rect.right<view.innerWidth) {
    const points=[[.25,.5],[.5,.5],[.75,.5]];let covered=0;
    for(const [x,y] of points){const top=doc.elementsFromPoint(rect.x+rect.width*x,rect.y+rect.height*y).find(e=>!owned.has(e));
     if(top&&top!==el&&!el.contains(top)&&!top.contains(el)&&view.getComputedStyle(top).opacity==='1')covered++;}
    if(covered===points.length)reasons.push('occlusion');
   }
   if(kind==='pseudo'&&!reasons.length) return; // Visible pseudo text is outside the hidden-text threat model.
   rows.push({id,path:prefix+pathOf(el)+(kind==='text'?'/text()['+[...el.childNodes].filter(x=>x.nodeType===3).indexOf(node as ChildNode)+']':''),frame,kind,attribute,text,normalized,
     reasons:[...new Set(reasons)],hidden:reasons.length>0,uncertain,rect:{x:rect.x,y:rect.y,width:rect.width,height:rect.height},
     profiles:{'raw-html':kind!=='pseudo','text-content':kind==='text','inner-text':kind==='text'&&rendered,'accessibility-tree':null},score:null});
   targets.set(id,{node,el,attribute:kind==='attribute'?attribute:undefined,pseudo:kind==='pseudo'?attribute:undefined});
  };
  while((n=walker.nextNode())) {
   if(owned.has(n))continue;
   if(n.nodeType===1){
    const el=n as Element;
    for(const attr of ['alt','aria-label','title'])if(el.hasAttribute(attr))add(el,el,el.getAttribute(attr)!,'attribute',attr);
    if(!['SCRIPT','STYLE','HEAD','META','LINK'].includes(el.tagName)) for(const pseudo of ['::before','::after']) {
     const content=view.getComputedStyle(el,pseudo).content;
     if(content&&content!=='none'&&content!=='normal'&&content!=='""')add(el,el,content.slice(1,-1),'pseudo',pseudo);
    }
    if(el.shadowRoot)await visit(el.shadowRoot,frame,prefix+pathOf(el)+' >>> ',inherited);
    if(el.tagName==='IFRAME'){
     try {
      const child=(el as HTMLIFrameElement).contentDocument;
      if(child){
       const frameReasons=[...inherited];let opacity=1;
       for(let ancestor:Element|null=el;ancestor;ancestor=parent(ancestor)){
        const style=view.getComputedStyle(ancestor);opacity*=Number(style.opacity);
        if(style.display==='none'||style.visibility==='hidden'||style.visibility==='collapse')frameReasons.push('frame-hidden');
       }
       const box=el.getBoundingClientRect();
       if(opacity<=config.opacityThreshold||!el.clientWidth||!el.clientHeight||box.right<0||box.bottom<0)frameReasons.push('frame-hidden');
       await visit(child,frame+'/'+prefix+pathOf(el),'',frameReasons);
      }else limitations.push('inaccessible-frame:'+pathOf(el));
     }catch {limitations.push('inaccessible-frame:'+pathOf(el));}
    }
   } else {const el=n.parentElement;if(el)add(n,el,n.textContent||'',n.nodeType===8?'comment':'text');}
   if(++visited%config.batchSize===0)await new Promise(r=>setTimeout(r,0));
   if(truncated)break;
  }
 }
 await visit(document,'top');
 const inferenceStart=performance.now(); const findings=await registry[detector].select(rows);
 return {schema_version:2,version:VERSION,detector,model:detector==='rules'?'none':modelName,config:{...config},findings,candidates:rows,
 scan_ms:performance.now()-start,inference_ms:performance.now()-inferenceStart,truncated,limitations:[...new Set(limitations)]};
}
export function sanitize(findings:Candidate[]) {
 const result:{id:string;status:string}[]=[];
 for(const finding of findings) {
  const target=targets.get(finding.id);if(!target){result.push({id:finding.id,status:'stale'});continue;}
  const {node,el,attribute,pseudo}=target;
  if(!node.isConnected||(!pseudo&&(attribute?el.getAttribute(attribute):node.textContent)!==finding.text)) {
   result.push({id:finding.id,status:'changed-since-scan'});continue;
  }
  if(pseudo){
   // Only edit a literal inline rule uniquely owning this pseudo-element. Shared,
   // external, attr()/counter(), and inaccessible rules are explicitly unsupported.
   let changed=false;
   for(const sheet of Array.from(el.ownerDocument.styleSheets)) {
    const owner=sheet.ownerNode;
    if(!owner||owner.nodeName!=='STYLE')continue;
    const before=owner.textContent;
    try {
     for(const rule of Array.from(sheet.cssRules)) {
      if(!('selectorText' in rule))continue;
      const styleRule=rule as CSSStyleRule,selector=styleRule.selectorText;
      if(!selector.endsWith(pseudo)||selector.includes(','))continue;
      const base=selector.slice(0,-pseudo.length);let matches:NodeListOf<Element>;
      try {matches=el.ownerDocument.querySelectorAll(base);}catch {continue;}
      if(matches.length!==1||matches[0]!==el)continue;
      const value=styleRule.style.getPropertyValue('content');
      if(value!==el.ownerDocument.defaultView!.getComputedStyle(el,pseudo).content||value.slice(1,-1)!==finding.text)continue;
      styleRule.style.setProperty('content','""');
      // Updating CSSOM alone would leave the payload in raw HTML/textContent.
      const after=Array.from(sheet.cssRules).map(r=>r.cssText).join('\n');
      owner.textContent=after;
      undoSteps.push(()=>{if(owner.isConnected&&owner.textContent===after)owner.textContent=before;});
      changed=true;break;
     }
    }catch { /* inaccessible stylesheet: keep the unsupported outcome */ }
    if(changed)break;
   }
   result.push({id:finding.id,status:changed?'neutralized':'unsupported-pseudo-sanitization'});continue;
  }
  if(attribute){const old=el.getAttribute(attribute);el.setAttribute(attribute,'');undoSteps.push(()=>{if(old!==null&&el.isConnected&&el.getAttribute(attribute)==='')el.setAttribute(attribute,old);});}
  else {const old=node.textContent;node.textContent='';undoSteps.push(()=>{if(node.isConnected&&node.textContent==='')node.textContent=old;});}
  result.push({id:finding.id,status:'neutralized'});
 }
 return result;
}
export function undo(){for(const action of undoSteps.reverse())action();const count=undoSteps.length;undoSteps=[];return count;}
