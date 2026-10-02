# Results template

Run ID: `[run id]` · Date: `[date]` · Agent: `[scripted naive / model]`

| Detector | Recall | Node F1 | Clean page FPR | Hard-negative FPR | p95 ms |
|---|---:|---:|---:|---:|---:|
| Rules | | | | | |
| Classifier | | | | | |

Include: PR curve, recall by vector/category, preservation screenshot diff, latency distribution, and failure gallery. Generate with `python -m parallax.evaluate --run data/runs/<run-id>`; do not fill blanks without matching artifacts. `data/runs/results.parquet` is a superseded v0.1 demonstration, not a valid result source.
