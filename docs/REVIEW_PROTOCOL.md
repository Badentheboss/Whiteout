# Finish the study without inventing evidence

## What can be prepared without running a dataset

The review-form, lexical-duplicate audit, and freeze commands are offline preparation tools. They do not start a browser, train a model, execute an agent, or run the dataset benchmark. Existing run results remain unchanged. Python/Chromium regression tests use tiny authored fixtures; they are not benchmark runs.

### Human source and label review

On Windows, `scripts\prepare-review.cmd` creates pending source forms and a source-balanced queue of up to 300 non-test benign candidates in `reviews/`. It refuses to overwrite existing queues. On other systems use:

```sh
python -m parallax.review sources --input data/research-manifest.jsonl --output reviews/sources-pending.jsonl
python -m parallax.review negatives --input data/hard-negatives.jsonl --output reviews/negatives-pending.jsonl --count 300
```

Create `reviews/` first. Set `PYTHONPATH=eval` and use the virtual-environment Python. Review source terms and licenses separately from content labels. Record reviewer/date and evidence URLs; a repository license is not automatically a page/asset license. Record degraded rendering, disabled scripts, and missing assets. Do not mark an interactive replay faithful merely because it loads.

For each content example, determine human visibility from its actual page/context and separately whether it attempts to instruct the agent. Accessibility labels, collapsed content, skip links, and legitimate installation instructions can be benign. Uncertainty stays pending. Do not infer intent from a canary or detector score. The pending queue is **not** a set of reviewed labels and is not automatically imported into training.

For the 30-item dashboard exercise, review the same sampled items independently under different reviewer pseudonyms. Unreviewed select boxes prevent unchecked defaults becoming negative labels. The dashboard shows saved before screenshots and detector details separately. Missing screenshots require the complete evidence bundle. Use notes for ambiguous cases; do not submit a visibility judgment from text alone. Ratings are append-only; repeat votes replace prior votes statistically without erasing history.

The dashboard reports model-vs-human metrics and pairwise inter-rater agreement separately. Node metrics score only explicitly reviewed, non-conflicting candidate IDs. Unreviewed nodes are not false positives or true negatives. These partial metrics cannot establish whole-page recall; a human must also identify missed nodes outside the detector's candidate set.

### Diverse source intake

Copy `docs/source-registry.example.jsonl`, replace the deliberately invalid placeholder, and supply reviewed entries in documentation/article/forum/storefront/interactive-app categories. Entries require HTTPS provenance, reviewer/date, rationale, and affirmative terms/page/asset-license checks. `parallax.corpus --registry <file>` will consume that registry **when acquisition is authorized later**. This command downloads content; do not run it as part of the no-dataset-work pass. No new sources have been certified or acquired by adding this interface.

### Near-duplicate and freeze checks

```sh
python -m parallax.corpus_audit --manifest data/research-manifest.jsonl --output reviews/corpus-audit.json
python -m parallax.freeze create --manifest data/research-manifest.jsonl --lock reviews/experiment-lock.json
python -m parallax.freeze check --lock reviews/experiment-lock.json
```

The audit checks local base hashes/provenance and screens five-word shingle Jaccard similarity for related content, including cross-split matches. Review matches and group related sources **before** regenerating splits. This is not semantic deduplication or license approval. Freeze requires existing hashed replays/assets, a built extension, and the harness; it locks exact content and detects changes or added executable files. It is not a quality certification. Outputs refuse overwrite.

When dataset execution is authorized, pass `--lock reviews/experiment-lock.json` to `parallax.run` along with the same manifest. A mismatch stops before browser launch. Code changes require a new lock; do not silently reuse historical run configurations.

## Work that still requires people or experiments

### Prepared payload revision and interaction tasks

An opt-in v3 payload library contains 18 split-disjoint families, six categories, and three distinct phrasings per family (54 machine-authored strings). It is not generated into the current dataset or trained into the shipped weights. When generation/training is authorized, use `parallax.dataset --expanded-payloads` and `parallax.train --expanded-payloads --encoder`, review the new material, and make a new freeze. Existing manifests retain compatibility. New family names do not by themselves establish semantic independence; human review is still needed.

Manifest rows can declare `interaction_steps`: at most 20 `click`, `fill`, `assert_text`, or `assert_url` steps. Selectors must match exactly one control. URL assertions are local paths/query/fragments; no arbitrary JavaScript is accepted. The harness executes tasks before sanitation, reloads to remove side effects, then executes them after sanitation. Preservation stays null if the baseline task fails. Example:

```json
{"interaction_steps":[{"action":"click","selector":"#submit"},{"action":"assert_text","selector":"#status","value":"Saved"}]}
```

Only attach tasks to reviewed local replays; network blocking remains active during execution. Task definitions are preparation—not measured preservation until a run occurs.

Actual human labels/ratings, source-license judgments, independent payload-family review, faithful interactive source replays, completed final benchmark measurements, and a bounded generative-agent experiment are not replaced by these tools. Existing 0.2.0 release/pilot artifacts stay historical; harness improvements do not retroactively change their results.
