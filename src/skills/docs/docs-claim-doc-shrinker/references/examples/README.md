# examples — docs-claim-doc-shrinker

Smoke fixtures for the EVAL.md blind prompts (T1–T8). Each scenario carries the minimum file set needed to drive the corresponding prompt.

| File | Used by | Purpose |
|------|---------|---------|
| [claim-identity.md](claim-identity.md) | T1, T2, T7 | Small claim-based identity doc — drives audit happy-path, compress happy-path, idempotency no-op |
| [claim-identity.audit.expected.md](claim-identity.audit.expected.md) | T1 | Expected `.shrink/...audit.md` shape produced by audit on `claim-identity.md` (all rows default `[x] keep`) |
| [claim-identity.audit.edited.md](claim-identity.audit.edited.md) | T2 | Same audit with several rows flipped to `[ ] cut` — drives compress happy-path |
| [claim-identity.compressed.expected.md](claim-identity.compressed.expected.md) | T2 | Expected rewrite covering only the kept claims |
| [narrative-essay.md](narrative-essay.md) | T3 | Narrative input — classifier-gate refusal scenario |
| [claim-identity.audit.hash-mismatch.md](claim-identity.audit.hash-mismatch.md) | T5 | Audit frontmatter `source_hash` deliberately set to a non-matching value — drives hash-mismatch refusal |
| [mixed-claim-narrative.md](mixed-claim-narrative.md) | T8 | Mixed doc (~50% claim, ~50% narrative) — drives `--accept-mixed` refusal then proceed |

T4, T6, and the `--accept-mixed` proceed variant of T8 are state scenarios (missing file, hostile writer stub, flag passed) that do not require additional fixture content.
