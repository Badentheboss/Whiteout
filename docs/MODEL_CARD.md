# Model card — local instruction classifier

Filters rendering-divergent candidates, not arbitrary malicious content. It has no tool/network authority.

Training uses source-group negatives and authored instruction families; canaries become TOKEN. Baseline: TF-IDF unigrams/bigrams with class-balanced logistic regression. MiniLM candidate: last encoder block and head fine-tuned for one bounded CPU epoch, followed by a balanced logistic head on pooled embeddings. Export: int8 ONNX, 128 tokens, offscreen browser batches of 16. Reports retain upstream revision, model hash/size, validation counts/cutoffs, and selection.

Current text-validation selection chooses TF-IDF on a recall tie; it is smaller and has fewer observed negative errors. MiniLM remains packaged for comparison. Candidate FPR is **not** clean-page FPR. `parallax.calibrate` uses measured validation pages before test freeze; a small-sample empirical 2% target is not a population guarantee.

Limits: small authored positive set; heuristic negatives; English-heavy encoder; truncation; browser WordPiece needs broader multilingual parity tests; no robustness certification. Never select thresholds on final test data. CPU-local, no paid service. MiniLM's Apache-2.0 license and ONNX Runtime's license are retained under `models/`.
