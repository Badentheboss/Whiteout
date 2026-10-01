chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'parallax-report' && sender.tab?.id) chrome.storage.session.set({ [`report:${sender.tab.id}`]: message.report, latestReport: message.report });
  if (message.type === 'parallax-latest-report') {
    chrome.storage.session.get('latestReport').then(result => sendResponse(result.latestReport || null));
    return true;
  }
});
