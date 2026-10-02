# Research decisions, v0.2

- Replace copied detector code with extension-owned messaging and a version/configuration handshake.
- Use bundled Chromium persistent contexts with `channel="chromium"`, following https://playwright.dev/python/docs/chrome-extensions. Managed Chrome is not a fallback.
- Keep localhost content-script scope and inert canaries. Acquisition is a separate networked phase; inference is packaged and local.
- Split whole source projects and payload families before generation; report observed coverage, not target counts.
- Compare TF-IDF/logistic with partially fine-tuned MiniLM. Candidate validation is followed by page-level threshold selection; freeze before final test use.
- Preserve old outputs as superseded demonstrations. Never fill unavailable privacy, node-label, or agent metrics with success values.
- Exclude degraded replays from preservation conclusions. Sanitize only uniquely owned literal inline pseudo rules; report other pseudo sources as unsupported.
- Cache source HTML/assets and provenance locally; terms and redistribution review remain pending.

MiniLM: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2 (Apache-2.0). Exact revision and exported SHA-256 are in `models/encoder-report.json`.
