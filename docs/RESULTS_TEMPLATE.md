# Results template

Run ID: `[run id]` · Date: `[date]` · Agent: `[scripted naive / model]`

| Detector | Recall | Node F1 | Clean page FPR | Hard-negative FPR | p95 ms |
|---|---:|---:|---:|---:|---:|
| Rules | | | | | |
| Classifier | | | | | |

Include: PR curve, recall by vector/category, preservation screenshot diff, latency distribution, and failure gallery. Generate from `data/runs/results.parquet` with `python -m parallax.evaluate`; do not fill blanks without a matching run artifact.
