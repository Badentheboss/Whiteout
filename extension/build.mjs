import { build } from 'esbuild';
import { cpSync, mkdirSync, rmSync, existsSync, readdirSync } from 'node:fs';

rmSync('dist', { recursive: true, force: true });
mkdirSync('dist', { recursive: true });
for (const entry of ['src/content.ts', 'src/service-worker.ts', 'src/popup.ts', 'src/offscreen.ts']) {
  await build({ entryPoints: [entry], bundle: true, format: 'esm', target: 'chrome120', outfile: `dist/${entry.split('/').pop().replace('.ts', '.js')}` });
}
cpSync('src/manifest.json', 'dist/manifest.json');
cpSync('src/popup.html', 'dist/popup.html');
cpSync('src/offscreen.html', 'dist/offscreen.html');
mkdirSync('dist/ort',{recursive:true});
for(const name of ['ort-wasm-simd-threaded.mjs','ort-wasm-simd-threaded.wasm'])cpSync('node_modules/onnxruntime-web/dist/'+name,'dist/ort/'+name);
mkdirSync('dist/models',{recursive:true});
for(const name of ['minilm-int8.onnx','vocab.json','encoder-report.json','MINILM-LICENSE.txt','training-report.json'])if(existsSync('../models/'+name))cpSync('../models/'+name,'dist/models/'+name);
cpSync('../models/ONNXRUNTIME-LICENSE.txt','dist/ort/LICENSE');
