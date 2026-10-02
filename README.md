# Parallax: rendering evidence and local instruction detection

Research question: **Can browser-rendering evidence plus a small local classifier detect hidden instructions while preserving legitimate content?**

Experimental localhost-scoped Chrome extension, Python harness, and Streamlit dashboard—not a proven prompt-injection defense. Version 0.1 results are **superseded demonstrations**. Do not cite their attack-success/privacy numbers. See [the correction](data/runs/SUPERSEDED.md).

See [implementation status](docs/IMPLEMENTATION_STATUS.md) for completed evidence and outstanding acceptance criteria. This release does not claim the full study is finished.

## Windows quick start

Extract the repository ZIP first. Open Command Prompt inside `Whiteout-main`, not Python's `>>>` prompt. Install Python 3.12 and Node.js LTS if your administrator permits them, then run:

```bat
scripts\setup.cmd
scripts\run-smoke.cmd
scripts\dashboard.cmd
```

The dashboard is at `http://127.0.0.1:8501`. Opening it does not run an experiment. Results save automatically to unique `data\runs` directories. Preserve the entire directory, including `pages`, for screenshots and extraction evidence. The dashboard also exports observations.

For a complete portable evidence bundle: `python -m parallax.export_run --run data/runs/<run-id> --output store/my-run.zip`. This includes detailed reports, screenshots, extractions, and the run's packaged extension snapshot where available.

On managed PCs, blocked installations require administrator help. Never disable TLS verification. Automation uses Playwright's bundled Chromium, not installed Chrome/Edge, following [official guidance](https://playwright.dev/python/docs/chrome-extensions).

## macOS/Linux quick start

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r eval/requirements.txt
.venv/bin/python -m playwright install chromium
npm ci --prefix extension
npm run build
export PYTHONPATH="$PWD/eval"
.venv/bin/python -m parallax.smoke
.venv/bin/python -m parallax.run --manifest data/smoke-manifest.jsonl
.venv/bin/python -m parallax.evaluate
.venv/bin/python -m streamlit run eval/parallax/dashboard.py --server.address 127.0.0.1
```

The 13-page smoke corpus is authored diagnostic material, not real-site generalization evidence. For a popup demo: serve the repository with `.venv/bin/python -m http.server 8765 --bind 127.0.0.1`, load **extension/dist** at `chrome://extensions` → Developer mode → Load unpacked, then visit `http://127.0.0.1:8765/data/smoke/demo-1.html`. Try Scan, Highlight, Sanitize, Undo, and the example button. Load neither the ZIP nor an empty directory.

## Research pipeline

Use the virtual environment Python and `PYTHONPATH=eval` (Windows: `set PYTHONPATH=%CD%\eval`).

```sh
python -m parallax.corpus
python -m parallax.dataset
python -m parallax.provenance
python -m pip install -r eval/requirements-training.txt
python -m parallax.train --encoder
npm run build
python -m parallax.subset --split validation
python -m parallax.run --manifest data/validation-subset.jsonl
python -m parallax.evaluate
python -m parallax.calibrate --run data/runs/<validation-run-id>
npm run build
# Freeze configuration before inspecting test results.
python -m parallax.run --split test
python -m parallax.evaluate
```

`python -m parallax.run --split all` executes all 9,250 rows, both detectors, three scans each. It is a separate long experiment. Resume with the same arguments plus `--resume data/runs/<run-id>`; packaged-extension and manifest hashes must match. Completed rows are retained; failures are recorded. Generated variants are not completed experiments.

Acquisition collected 290 distinct-content pages from 29 projects; balanced selection retains 250 controls plus 9,000 variants. All are documentation, not the requested broader mix of forums, stores, articles, and apps. See [data card](docs/DATA_CARD.md), [model card](docs/MODEL_CARD.md), and [benchmark card](docs/BENCHMARK_CARD.md).

## Detectors and evidence

- A: rendering divergence from DOM/CSS, geometry, comments, attributes, Unicode, pseudo-content, open shadow roots, and same-origin frames.
- B: A plus a trained TF-IDF/logistic classifier or partially fine-tuned, quantized MiniLM candidate. Validation selects the model; larger is not automatically better.
- The harness calls the shipped extension through its private popup messaging API and verifies version/configuration.
- Warn uses extension-owned overlays. Sanitize blanks exact text/comment/attribute content and supports guarded undo. Unique literal inline pseudo-content rules can be rewritten; shared/external pseudo sources remain unsupported.
- Runs retain findings, extractor outputs, timings, screenshots, observed traffic attempts, failures, configuration, and environment. Missing measurements remain null with reasons.

## Tests and release

```sh
PYTHONPATH=eval .venv/bin/python -m pytest eval/tests -q
npm test
npm run package
```

Packaging creates `store/parallax-0.2.0.zip` and a SHA-256 file, without overwriting an existing release. Extract and load the folder containing `manifest.json`. The 0.1 ZIP is historical and superseded. CI runs the small deterministic suite, not the full study. No paid endpoint or store account is required.

## Boundaries

Default extension scope is localhost only. Browser-visible traffic logging is not an OS-wide privacy proof. Downloaded replays disable scripts/navigation and have incomplete assets; none currently supports preservation conclusions. The scripted agent is **not an LLM**. Independent source review, human labels, diverse coverage, complete experiments, and a bounded local-model agent study remain necessary for strong security claims.

If a suitable generative model is already installed locally, run `python -m parallax.local_agent --model /path/to/model --run data/runs/<run-id> --max-items 8`. This performs no automatic model download; it records truncated-context title-task and canary outcomes, not full tool-use security.
