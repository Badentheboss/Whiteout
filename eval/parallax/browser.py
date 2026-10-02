"""Drive the shipped extension through its private popup API."""
from pathlib import Path
from playwright.async_api import async_playwright
from .config import ROOT

class ExtensionBrowser:
    def __init__(self,extension_path=None):
        self.extension_path=Path(extension_path) if extension_path else ROOT/'extension/dist'
    async def __aenter__(self):
        self.p = await async_playwright().start()
        try:
            self.context = await self.p.chromium.launch_persistent_context(
                "", channel="chromium", headless=True,
                args=[f"--disable-extensions-except={self.extension_path}",
                      f"--load-extension={self.extension_path}"],
                viewport={"width": 1280, "height": 900})
            worker = (self.context.service_workers or
                      [await self.context.wait_for_event("serviceworker", timeout=15000)])[0]
            extension_id = worker.url.split("/")[2]
            self.control = await self.context.new_page()
            await self.control.goto(f"chrome-extension://{extension_id}/popup.html")
            await self.control.wait_for_function("globalThis.parallax?.version === '0.2.0'")
            return self
        except Exception as error:
            await self.p.stop()
            raise RuntimeError("Extension startup failed. Build extension/dist and install the supported browser with "
                               "python -m playwright install chromium. Managed Chrome is not an extension-test fallback.") from error

    async def tab_id(self, page):
        # URL alone cannot identify two tabs showing the same page.
        await page.bring_to_front()
        tabs = await self.control.evaluate("chrome.tabs.query({active:true,lastFocusedWindow:true})")
        for tab in tabs:
            try:
                hello = await self.control.evaluate("id=>parallax.request(id,'hello')", tab['id'])
                if hello.get('url') == page.url:
                    return tab['id']
            except Exception:
                continue
        raise RuntimeError('No extension-connected tab for ' + page.url)

    async def request(self, page, action="scan", detector="rules"):
        tab_id = await self.tab_id(page)
        result = await self.control.evaluate(
            "([id,action,detector])=>parallax.request(id,action,detector)", [tab_id,action,detector])
        if result.get("error"):
            raise RuntimeError(result["error"])
        return result

    async def ready(self, page):
        for _ in range(30):
            try:
                hello = await self.request(page, "hello")
                assert hello["version"] == "0.2.0" and hello["schema_version"] == 2
                required={'contrastRatio':1.35,'minFontPx':2,'payloadTokenOverlap':.6,'maxCandidates':12000}
                if any(hello.get('config',{}).get(k)!=v for k,v in required.items()):
                    raise RuntimeError('Extension configuration mismatch')
                return hello
            except Exception:
                await page.wait_for_timeout(100)
        raise RuntimeError("Extension content-script handshake timed out")

    async def __aexit__(self, *args):
        await self.context.close()
        await self.p.stop()
