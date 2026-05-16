# Test fixtures — docs-claim-doc-writer

Smoke-test inputs for the writer. Each fixture has expected behavior documented in `../../EVAL.md` (T1–T6).

Each fixture file uses a three-block layout:

1. **Front block (`## Kept Claims (input)`)** — the `kept_claims` list passed to the agent.
2. **Body block (`## Original Doc (input)`)** — the `original_doc` string.
3. **(Optional) Anchor block (`## Voice Anchors (input)`)** — 3–5 anchor sentences for style-sub-type fixtures only.
4. **Expected block (`## Expected Behavior`)** — what a passing rewrite (or refusal) looks like.

| Fixture | Sub-type | Voice anchors? | Expected behavior |
|---------|----------|----------------|-------------------|
| [identity-full-coverage.md](identity-full-coverage.md) | identity | no | Full rewrite covering all 6 kept claims; all 4 headings preserved; length ≥ 30% |
| [leakage-temptation.md](leakage-temptation.md) | principle | no | Rewrite with NO connecting assertion beyond the 4 kept claims; tempting "natural" sentence MUST be absent |
| [heading-rename-refusal.md](heading-rename-refusal.md) | identity | no | All source headings preserved verbatim; `structure_preservation: false` (if simulated) ignored |
| [length-floor-abort.md](length-floor-abort.md) | principle | no | `LENGTH FLOOR ERROR: <n>% of source, floor is 30%`; NO `rewritten_doc` emitted |
| [style-voice-anchors.md](style-voice-anchors.md) | style | yes (4) | Full rewrite covering all 5 claims; voice matches anchors; anchor sentences NOT echoed in output |
| [principle-neutral-voice.md](principle-neutral-voice.md) | principle | no | Neutral expository prose; all headings preserved; all claims covered; no agent-invented voice |

## How to use

1. Pass the fixture's front block as `kept_claims`, body block as `original_doc`, and (if present) anchor block as `voice_anchors`.
2. Compare agent output against the fixture's "Expected Behavior" section and the corresponding EVAL T-row.
3. For coverage checks (T1, T2, T5, T6), dispatch `docs-claim-claim-judge` once per kept claim against `rewritten_doc` and confirm `verdict ∈ {entailed, partial}` for all. Any `dropped` is a writer FAIL.
4. For O3 (heading preservation), do a textual diff of source headings vs. rewrite headings — must be identical in name, depth, and order.

These fixtures are deliberately small so the gatekeeper and any downstream eval runner can execute the full T1–T6 suite cheaply.
