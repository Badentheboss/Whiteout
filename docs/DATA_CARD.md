# Data card — acquired corpus v2

`data/coverage.json` records 250 selected pages from 29 documentation projects, 9,000 variants, and 4,495 heuristic benign candidates. Base splits: 146 train / 52 validation / 52 test. Acquisition collected 290 pages before balanced selection. Six payload categories, 12 vectors, three seeds per base. Source groups and families split before generation; canaries are randomized and masked in training.

Provenance retains URLs, retrieval dates, content/source/replay hashes, attribution, license URLs/hashes, assets, transformations, and missing assets. `data/acquisition.json` records actual skip causes. Trusted certificates use certifi; TLS stays enabled. Snapshots remain in ignored `data/corpus/`; license evidence is in `data/licenses/`.

Limitations:

- Documentation-only coverage does not meet five-category diversity.
- Exact content hashing is not semantic deduplication. Related versions/translations may remain within a source group.
- Only 30 authored positive families exist; thousands of variants do not imply independent semantic diversity.
- Seeds change placement and token; substantial held-out wording diversity remains incomplete.
- Machine-derived benign candidates are **not** 300 human-curated hidden examples. Accessibility and collapsed-section candidates need review.
- Zero downloaded replays are preservation-eligible: scripts/navigation are disabled and assets are incomplete.
- Repository licenses do not establish every page/asset's terms. Human redistribution review remains pending; snapshots are not published as approved data.

Reacquisition can change upstream content. Exact reproduction needs the retained local cache, manifest, and hashes. Generated counts must not be called completed tests.
