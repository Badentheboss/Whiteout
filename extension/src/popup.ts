const popupStatus=document.querySelector('#status')!; const report=document.querySelector('#report')!;
chrome.runtime.sendMessage({type:'parallax-latest-report'}).then((r:any)=>{ popupStatus.textContent=r ? `${r.findings.length} finding(s)` : 'No report yet'; report.textContent=r ? JSON.stringify(r.findings,null,2) : ''; });
