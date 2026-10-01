# Decisions

| Decision | Alternatives | Reason | Reversal |
|---|---|---|---|
| Use raw TS + esbuild instead of WXT/Plasmo | WXT, Plasmo | Minimal audit surface and reproducible static MV3 output | Adopt WXT if multi-browser packaging becomes necessary |
| Ship local five-fixture run, not claim a 100-page corpus | scrape 100 pages | Empty repo and time-bound execution; fabricated corpus/results are unacceptable | Add reviewed sources through prepare manifest |
| Rules score is lexical baseline, not an ML model | bundled ONNX model | A trained/exported model needs labeled data and model-card review | Add ONNX Runtime Web after held-out training run |
| No host permissions | broad host permissions | Static content-script matches provide least privilege for user-loaded pages; no network | Add optional host permissions only with user-visible scope |
| Treat sr-only as benign in classifier path | flag all invisible text | Accessibility labels are expected hidden content and main FP risk | Add explicit semantic hard-negative taxonomy |
| Use harmless CANARY payloads and localhost | live audit / credentials | Keeps evaluation inert and defensive | Never reverse for production testing |

## Benchmark notes

Methodological inspiration is limited to public descriptions of AgentDojo, InjecAgent, BIPIA, WASP, and deepset prompt-injection work: payload categories and evaluating attack success separately from detection. No benchmark examples or data are bundled. Before incorporating any material, record its exact license and attribution here.
