# Parallax

Parallax is a defensive Chrome MV3 prototype for finding text an automated page extractor may consume even though a human cannot see it. It is not a general prompt-injection solution and does not inspect image attacks, visible comments, cross-origin iframe internals, or network/tool execution.

## Quick start

```sh
npm install --prefix extension
python3 -m venv .venv && .venv/bin/pip install -r eval/requirements.txt
npm run build
PYTHONPATH=eval .venv/bin/python -m parallax.prepare
PYTHONPATH=eval .venv/bin/python -m parallax.run
PYTHONPATH=eval .venv/bin/python -m parallax.evaluate
PYTHONPATH=eval .venv/bin/python -m parallax.dashboard
```

The committed data are a deterministic 100-page, project-authored CC0 local benchmark: 20 pages each across recipe, documentation, storefront, forum, and task-board layouts, with ten hidden-text vectors rotated across classes. It is a reproducible evaluation corpus, not a claim that these are 100 real web pages. Source URLs, license, snapshot path, injection vector, payload, ground-truth selector, seed, and extractor profiles are required for each `data/manifest.jsonl` row. Add real pages only after checking robots.txt, terms, and licenses; commit source URL and fetch instructions rather than unlicensed snapshots.

The evaluation harness uses an installed Google Chrome channel rather than Playwright's separately downloaded Chromium. This makes the run friendlier to managed campus PCs; Chrome must already be installed and permitted to launch.

## Optional real-document upgrade

`data/sources/approved_docs.jsonl` is a reviewed registry of 25 public documentation pages from Python, MDN, Django, Flask, and FastAPI, with source attribution and license URLs. Run `python -m parallax.real_corpus` only from a network that permits it: it checks each site's `robots.txt`, uses a named user agent, rate-limits to one request per second, stores snapshots only under ignored `data/external-fixtures/`, and writes a 250-variant provenance manifest. Run it with `PARALLAX_MANIFEST=data/external-manifest.jsonl python -m parallax.run`. These source-derived files are never committed; review each fetched page and its license before publishing derived artifacts.

`npm run package` writes the unpacked extension zip to `store/`. Load `extension/dist` through `chrome://extensions` → Developer mode → Load unpacked. The extension uses only `storage`, analyzes locally, sends no page text to a server, and retains reports only for the current browser session.

## Detector modes

Rules flags DOM text whose extractor visibility diverges from CSS/geometry-based human visibility. Classifier mode adds a compact instruction-likeness lexical baseline; it is a placeholder for a trained, on-device ONNX encoder, not a claim of ML performance. Warn outlines candidates and attaches a reason. Sanitize hides only flagged candidate elements and should be run with screenshot, visible-text, interactive-count, and click-smoke preservation checks.

## Data and benchmark licenses

Local fixtures: CC0-1.0 (project-authored). Chrome documentation is CC-BY-4.0; Playwright is Apache-2.0. Public benchmark methodology is cited in `DECISIONS.md`; no benchmark data are redistributed.
