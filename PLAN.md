# Parallax v1 plan

## Intent
Parallax protects AI browsing workflows from a narrow but important class of attack: instructions which are exposed to an extractor but concealed from a person. The player-facing equivalent here is clear feedback without changing normal pages: warn first, explain why, and make sanitization opt-in.

## Eight-week path

| Week | Milestone | Exit condition |
|---|---|---|
| 1 | Scaffold, threat model, data provenance | MV3 build and decision log |
| 2 | Corpus builder and seeded local injector | Schema-valid manifest |
| 3 | Visibility/rules baseline | Chromium vector tests |
| 4 | Metrics and preservation harness | Detection + no-network reports |
| 5 | Classifier experiment | Held-out site/template evaluation |
| 6 | Dashboard and rating workflow | Reviewable failure gallery |
| 7 | Adaptive attacks and analysis | Risk gates and figures |
| 8 | Store package and resume write-up | Submission-ready package |

The committed run deliberately covers five CC0 local fixtures—not a claimed 100-page web corpus. `parallax prepare` is the reproducible path for adding sources after license/terms review. Every source must stay provenance-tagged, site-split from training, and snapshot only when allowed.

## System

The content script owns DOM/geometry inspection because the MV3 service worker has no DOM. It scans document and same-origin frames selected by Chrome, observes mutations with debounce, and passes an in-memory report to the service worker for session-only popup retrieval. Detector A flags extraction/human-visibility divergence. Detector B additionally gates candidates through an on-device instruction-likeness score. A registry reserves an LLM-judge/screenshot detector without enabling it. The Python harness serves fixtures only on localhost, opens Chromium with the packed extension, records flags and latency, and evaluates rows into Parquet.

## Success gates

Per-vector recall, hard-negative false-positive rate, sanitize visual/interaction parity, and p95 scan latency are release gates. This small seed run establishes pipeline health only; it cannot establish production rates.
