# Risks and release checks

| Risk | Signal | Implemented check / mitigation |
|---|---|---|
| sr-only false positives | hard-negative FPR | classifier requires instruction-like score; local fixture includes sr-only label |
| Threshold evasion | per-vector recall floor | vector breakdown emitted to Parquet |
| Extractor mismatch | profile disagreement | manifest retains raw HTML/textContent/innerText/a11y profiles |
| Gradient/image contrast | unresolvable background | report as uncertain; V1 only resolves CSS background colors |
| Shadow DOM/iframe gaps | missed-frame audit | content script runs all same-origin frames; shadow traversal is V2 hardening |
| SPA churn | duplicate scans / latency | debounced MutationObserver |
| MV3 worker suspension | missing report | session storage only, popup gracefully reports none |
| Template leakage | train/test shared wording | site/template family split required before classifier training |
| Regression | p95 latency increase | results include p50/p95 fields; add CI threshold once baseline grows |
