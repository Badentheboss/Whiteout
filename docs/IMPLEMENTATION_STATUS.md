# Implementation and evidence status

This is a research infrastructure release, **not completion of every acceptance criterion**.

## Executed evidence

- Final release smoke: `20261002T051915Z-0f56d16b`, with packaged extension/harness snapshots, completion record, 26 observations, and detailed per-page reports. Final verification: 12 Python tests and one packaged-extension Playwright test passed; dashboard rendering checked with Streamlit AppTest. Release ZIP: `store/parallax-0.2.0.zip` with SHA-256 sidecar.

- `20261002T044438Z-0d1fdf3a`: 78 validation pages × two detectors = 156 observations; 72 injections and six controls per detector, six projects, no failures. Both detectors found 63/72 injections (87.5%). Rules flagged 6/6 controls; classifier flagged 0/6. This small pilot cannot establish a population 2% FPR. Raw observations, metrics, figures, and calibration provenance are retained.
- `20261002T045423Z-0245970f`: 13 authored smoke pages × two detectors; all 12 injected vectors detected, all click tasks passed. Authored regression evidence only.
- Packaged extension regression tests exercise warn preservation, undo, duplicate nodes, tabs/frames, inaccessible frames, dynamic content, exact extraction removal, and a blocked transmission fixture.
- Optional local ONNX parity test passed against Python inference for English, French, punctuation, and Chinese samples.

The pilot predates the later Unicode-tag fixture correction, frame-observer improvements, and sparse linear-inference optimization. Its timing/recall must not be attributed to the final release without rerunning. Its extension snapshot remains available locally; do not overwrite historical evidence. One earlier run is explicitly invalidated because a shared build directory changed during execution; new runs snapshot their extension and harness.

## Implemented

Actual extension messaging/handshake; local rendering/classifier paths; targeted reversible sanitation; guarded inline pseudo-rule sanitation; source acquisition and provenance; 250 base controls/9,000 variants; project/family splits; TF-IDF training plus quantized MiniLM; validation calibration; immutable/resumable run infrastructure; extraction/screenshot/traffic/timing evidence; clustered intervals and PR curves; dashboard ratings; Windows scripts; CI and portable packaging.

## Still required before the full study is complete

### No-benchmark engineering follow-up

Added explicit pending review forms, balanced non-test review queues, reviewed-candidate node metrics with conflict exclusion, independent-rater agreement, offline shingle-duplicate screening, reviewed multi-category source intake, artifact path/checksum checks, and experiment freeze verification before browser startup. Extraction now reports unavailable AX/frame/shadow evidence as unknown rather than false. See `docs/REVIEW_PROTOCOL.md`. None of these additions creates human judgments, certifies new sources, or claims a new benchmark result. Existing release 0.2.0 evidence remains historical.

Prepared an opt-in payload revision (18 families, 54 machine-authored phrasings) and bounded before/after click/fill/navigation assertions. Neither new dataset generation, model retraining, nor benchmark execution was performed. Local pending forms contain 250 source reviews and 300 non-test content reviews; all remain unanswered.

Follow-up verification: 22 Python tests passed, Python compilation passed, dashboard AppTest loaded without exceptions, and the diff passed whitespace checks. Tests use small authored fixtures and existing model artifacts, not corpus benchmark execution. No tracked data, model weights, or extension release artifacts changed in this follow-up.

- Broader article/forum/store/interactive-app coverage and page-level terms/assets review. All 250 selected bases are documentation; all downloaded replays are excluded from preservation conclusions.
- At least 300 human-curated hidden examples. The 4,495 existing benign candidates are explicitly machine-labeled, not reviewed.
- More independent positive template families and wording diversity; semantic deduplication beyond exact hashes.
- Full 9,250-row execution with the frozen final release, including untouched held-out test reporting. Only pilot/smoke execution is claimed here.
- Human node ground truth for node precision/recall/F1, reviewed navigation tasks, and submitted 30-item ratings.
- An executed bounded generative local-agent study. The optional local-model command exists, but no suitable generative model was provisioned; scripted probes are not LLM security evidence.
- Broader extraction/frame mapping and multilingual tokenizer parity, complex occlusion/clip/background tests, and shared/external pseudo-source sanitation.

No resume-ready production security claim is justified by the current pilot. Publish limitations and unfavorable findings with any portfolio demo.
