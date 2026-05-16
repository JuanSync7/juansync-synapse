# Test fixtures — docs-claim-claim-judge

Smoke-test inputs for the judge. Each fixture pairs a single `claim` object with a `rewritten_doc` string and the expected `judge_verdict`. EVAL T1–T6 reference these files.

| Fixture | Scenario | Expected verdict | Expected evidence_span | Notes |
|---------|----------|------------------|------------------------|-------|
| [entailed-verbatim.md](entailed-verbatim.md) | Claim text appears verbatim in rewrite | `entailed` | verbatim substring | confidence ≥ 0.8 |
| [entailed-paraphrase.md](entailed-paraphrase.md) | Meaning preserved, wording reordered + synonyms | `entailed` | substring covering the paraphrase | `partial` here is a FAIL |
| [partial-hedge-dropped.md](partial-hedge-dropped.md) | "usually" qualifier lost in rewrite | `partial` | unhedged rewrite sentence | `entailed` here is a FAIL |
| [dropped.md](dropped.md) | Claim absent from rewrite entirely | `dropped` | `null` (NOT `""`) | confidence ≥ 0.6 |
| [low-confidence-escalation.md](low-confidence-escalation.md) | Ambiguous rewrite; raw confidence < 0.6 | `partial` (escalated from `entailed`) | closest candidate substring | confidence reported as raw < 0.6 |
| [empty-rewritten-doc.md](empty-rewritten-doc.md) | `rewritten_doc = ""` (writer produced nothing) | `dropped` | `null` | MUST NOT crash, MUST NOT emit `INPUT ERROR` |

## How to use

1. Read the fixture's `## Claim` block and parse the YAML into the `claim` input.
2. Read the fixture's `## Rewritten doc` fenced block and pass its contents (whitespace-exact, empty string allowed) as `rewritten_doc`.
3. Invoke the judge with `{ claim, rewritten_doc }`.
4. Compare the returned `judge_verdict` against the expected block in the fixture.
5. `evidence_span` must be a verbatim substring of `rewritten_doc` when non-null. `evidence_span: null` is mandatory when `verdict = dropped`.
6. For the low-confidence-escalation fixture, the returned `verdict` MUST be `partial` even if the model's raw assessment was `entailed` — see EVAL O5.

These fixtures are deliberately small so the gatekeeper and any downstream eval runner can execute the full T1–T6 suite cheaply.
