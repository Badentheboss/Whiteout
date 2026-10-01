import { build } from 'esbuild';
import { cpSync, mkdirSync, rmSync } from 'node:fs';

rmSync('dist', { recursive: true, force: true });
mkdirSync('dist', { recursive: true });
for (const entry of ['src/content.ts', 'src/service-worker.ts', 'src/popup.ts']) {
  await build({ entryPoints: [entry], bundle: true, format: 'esm', target: 'chrome120', outfile: `dist/${entry.split('/').pop().replace('.ts', '.js')}` });
}
cpSync('src/manifest.json', 'dist/manifest.json');
cpSync('src/popup.html', 'dist/popup.html');
