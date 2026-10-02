# Versions checked 2026-10-01

| Component | Pinned | Verification |
|---|---:|---|
| Chrome extension platform | Manifest V3 | [Chrome manifest docs](https://developer.chrome.com/docs/extensions/reference/manifest) |
| Playwright | 1.63.0 | [npm](https://www.npmjs.com/package/playwright) |
| ONNX Runtime Web (future model option) | 1.30.0 | [npm](https://www.npmjs.com/package/onnxruntime-web) |
| Streamlit | 1.64.0 | [PyPI](https://pypi.org/project/streamlit/) |
| pandas | 2.3.3 | PyPI checked during environment setup |
| scikit-learn | 1.7.2 | PyPI checked during environment setup |

MV3's service worker cannot access the DOM; DOM analysis remains in the content script. Manifest V3 disallows remotely hosted executable code, so any future ONNX model must be packaged with the extension.

Source-license verification (2026-10-01): Python documentation is PSF-licensed; MDN documentation is CC-BY-SA 2.5 or later with attribution/share-alike requirements; Django documentation is BSD-3-Clause; Flask documentation is BSD-3-Clause; FastAPI is MIT. See `data/sources/approved_docs.jsonl` for per-source attribution and license links.
