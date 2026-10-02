import {test,expect,chromium} from '@playwright/test';
import path from 'node:path';
test('packaged MV3 extension starts and exposes its private control API',async()=>{
 const ext=path.resolve('dist');
 const ctx=await chromium.launchPersistentContext('',{channel:'chromium',headless:true,args:[`--disable-extensions-except=${ext}`,`--load-extension=${ext}`]});
 try {
  const worker=ctx.serviceWorkers()[0]||await ctx.waitForEvent('serviceworker');
  const popup=await ctx.newPage();await popup.goto(`chrome-extension://${worker.url().split('/')[2]}/popup.html`);
  await expect(popup.locator('h1')).toHaveText('Parallax');
  expect(await popup.evaluate(()=>(globalThis as any).parallax.version)).toBe('0.2.0');
 }finally{await ctx.close();}
});
