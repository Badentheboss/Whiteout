# Threat model

An attacker controls HTML/CSS/attributes in a page served to an AI browsing agent. Their objective is to cause an extractor (raw HTML, `textContent`, `innerText`, or accessibility-tree style extraction) to ingest an instruction that a normal viewer would not perceive. Parallax derives `divergence = agent-visible AND not human-visible`, then identifies instruction-like candidates.

In scope: display/visibility/opacity hiding, off-screen positioning, tiny text, low contrast/color matching, clipping, HTML comments, attributes, zero-width/Unicode tag characters, CSS pseudo-content, same-origin frames, and post-load mutations. The first implementation uses style, geometry, and simple contrast signals; occlusion and complete shadow-root traversal are documented goals but not certified by this small run.

Out of scope: plainly visible injections (including user comments), image/OCR attacks, cross-origin iframe internals, compromised browsers/extensions, agent tool execution, data theft itself, and all non-text modalities. A flag is a defensive warning, not proof of intent. Parallax protects one input-channel class and cannot make an agent safe against prompt injection generally.
