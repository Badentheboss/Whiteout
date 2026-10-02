# Metrics

Detection is measured per injection (a flag overlaps the ground-truth selector or covers at least the configured 60% payload-token overlap), plus node precision/recall/F1, broken down by vector, payload category, and extractor profile. The evaluator stores a chosen classifier operating point and is structured for a future PR curve; the 100-fixture local run is sufficient for vector coverage, not statistical in-the-wild claims.

Preservation is measured separately: pages with flags and flags/page on clean pages and hard negatives; sanitize screenshot pixel fraction/SSIM, visible `innerText`, interactive count, and click/navigation smoke tests. Overhead is cold/warm p50/p95 scan time, long tasks, heap delta, model size/inference time, Chrome/hardware/OS, each three times. The local run currently records page latency and asserts zero page-content network requests. Anything absent is explicitly unmeasured, not zero.

End-to-end attack success is whether a scripted naive agent emits the harmless canary with defense off/on. No real LLM agent runs without an explicitly provisioned budgeted key or local model.
