# Chrome Web Store listing

**Name:** Parallax — Hidden Prompt Injection Defense

**Summary:** Locally warns about text that automated extractors may see but people cannot.

**Description:** Parallax scans pages on-device for hidden, instruction-like text and explains the hiding signal. It can warn or optionally sanitize flagged nodes. It does not send page text to a server and is a research prototype, not a complete defense against prompt injection.

**Permission justification:** `storage` retains the current tab’s local report during the browser session so the popup can render it. Static content-script access is required to inspect pages the user opens. No remote code or content collection.
