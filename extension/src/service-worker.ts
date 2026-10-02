let opening:Promise<void>|undefined;
chrome.runtime.onMessage.addListener((message,sender,reply)=>{
 if(message.type==='classify') {
  (async()=>{
   if(!await chrome.offscreen.hasDocument()) {
    opening??=chrome.offscreen.createDocument({url:'offscreen.html',reasons:[chrome.offscreen.Reason.WORKERS],justification:'Run the packaged local instruction model.'});
    await opening;opening=undefined;
   }
   reply(await chrome.runtime.sendMessage({type:'offscreen-score',texts:message.texts}));
  })().catch(e=>reply({error:String(e)}));return true;
 }
 if(message.type==='report'&&sender.tab?.id!==undefined) {
  chrome.storage.session.set({['report:'+sender.tab.id]:message.report});
  chrome.action.setBadgeText({tabId:sender.tab.id,text:String(message.report.findings?.length||'')});
 }
});
chrome.tabs.onRemoved.addListener(id=>chrome.storage.session.remove('report:'+id));
chrome.tabs.onUpdated.addListener((id,change)=>{if(change.status==='loading'){chrome.storage.session.remove('report:'+id);chrome.action.setBadgeText({tabId:id,text:''});}});
