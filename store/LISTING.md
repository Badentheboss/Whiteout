# Chrome Web Store listing

**Name:** Parallax — Hidden Prompt Injection Defense

**Summary:** Locally warns about text that automated extractors may see but people cannot.

**Description:** Parallax scans pages on-device for hidden, instruction-like text and explains the hiding signal. It can warn or optionally sanitize flagged nodes. It does not send page text to a server and is a research prototype, not a complete defense against prompt injection.

**Permission justification:** `storage` retains per-tab session reports; `activeTab` supports user-triggered popup actions; `offscreen` hosts packaged local ONNX inference. Static content scripts are restricted to localhost research replays. No remote model code or telemetry. This is draft listing text, not a submitted or approved store listing.
