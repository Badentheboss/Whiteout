# Benchmark card — schema v2

Uncertainty clusters by source project, not variant. Report completed observations and failures separately. Cluster intervals require multiple sources.

Run directories retain unique IDs, environment, configuration, full extension hashes, JSONL observations/failures, three scan timings, viewport screenshots, raw HTML/textContent/innerText/accessibility output, traffic attempts, heap measurements, and long tasks. Resume rejects configuration changes. Navigation is excluded from scan timing. First scan is page-cold, later scans warm; shared offscreen model state is not process-cold on each page.

Detection uses 60% token coverage against injected text. This is not complete human node ground truth. Node precision/recall/F1 remain unavailable until reviewed labels exist; metric primitives have independent expected-answer tests. PR curves explicitly mix injection hits and clean-page flags. Clean-page flag rate is not a manually adjudicated security false-positive rate.

Preservation includes viewport pixel/SSIM differences, visible-text/accessibility equality, and control counts. Authored smoke fixtures execute click tasks. Degraded downloads are excluded. Cross-origin frames, closed shadows, shared/external pseudo source removal, complex clipping/backgrounds, and unsampled occlusion remain limitations.

The executed scripted agent is a deliberately weak deterministic instruction/canary probe—not an LLM. No real-model attack-success claim follows. Traffic instrumentation is checked with an intentionally transmitting fixture blocked before egress; this is not OS-wide capture or a universal privacy proof.

Human agreement remains unavailable until ratings are submitted in the dashboard. Publish unfavorable findings and failures. Resume claims must link the exact completed run and configuration, never just a generated manifest.
