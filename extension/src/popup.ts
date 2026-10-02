import {VERSION} from './config';
let last:unknown=null;
const api={
 version:VERSION,
 tabs:()=>chrome.tabs.query({}),
 request:async(tabId:number,action:string,detector='rules')=>chrome.tabs.sendMessage(tabId,{type:'parallax',action,detector},{frameId:0})
};
(globalThis as any).parallax=api; // Available only in this extension-owned page.
for(const action of ['scan','warn','sanitize','undo'])document.getElementById(action)!.addEventListener('click',async()=>{
 try {
 const [tab]=await chrome.tabs.query({active:true,currentWindow:true});if(!tab?.id)throw new Error('No active tab');
 last=await api.request(tab.id,action,(document.getElementById('detector') as HTMLSelectElement).value);
 document.getElementById('status')!.textContent=(last as any).error || ((last as any).findings?.length??0)+' findings';
 document.getElementById('report')!.textContent=JSON.stringify(last,null,2);
 }catch(e){document.getElementById('status')!.textContent=String(e);}
});
document.getElementById('export')!.addEventListener('click',()=>{
 if(!last)return;const url=URL.createObjectURL(new Blob([JSON.stringify(last,null,2)],{type:'application/json'}));
 const a=document.createElement('a');a.href=url;a.download='parallax-report.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
});
