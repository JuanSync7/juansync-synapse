# Decision Memo — docs-claim-claim-judge

> Artifact type: agent | Memo type: creation | Design doc: `.brainstorms/2026-05-13-shrink-skill/design.md`

---

## What I want

A single-claim entailment judge agent that answers one question per call: is this claim semantically preserved in this rewritten document? Returns a structured verdict (`entailed | partial | dropped`) with an evidence span and a confidence score. Designed for batch dispatch — one call per kept claim during the compress phase of `docs-claim-doc-shrinker`. The judge is the highest-reuse agent in this suite; its (claim, text) → verdict interface is deliberately clean so it can be lifted into test-coverage verification, doc-vs-code sync, and RAG eval workflows later.

---

## Why Claude needs it

Without a dedicated judge agent, the compress phase has no coverage verification. Claude would write the compressed doc and either trust it blindly (producing silent claim loss) or use ad-hoc inline checks (inconsistent thresholds, no caching, no structured evidence). Specifically: the shrinker has no principled way to abort a compress run that silently drops 30% of the user's kept claims. The judge closes that gap with a per-claim structured verdict before any write is committed.

---

## Injection shape

- **Policy:** Judgment rules for semantic entailment — what counts as `entailed` vs `partial` vs `dropped`, when to escalate low-confidence verdicts, how to handle empty rewritten docs.
- **Domain knowledge:** Entailment semantics for this workflow (paraphrase OK, qualifier-loss = partial, absent evidence = dropped). Not strict logical entailment.

---

## What it produces

| Output | Count | Mutable? | Purpose |
|---|---|---|---|
| `judge_verdict` object | 1 per call | no | Structured verdict consumed by shrinker's coverage report |

---

## Verbatim blocks

### Agent frontmatter

<!-- VERBATIM -->
```yaml
---
name: docs-claim-claim-judge
description: Judges whether a single claim is semantically preserved in a rewritten document. Returns entailed | partial | dropped with evidence span. Designed for batch dispatch (one call per claim).
domain: docs
subdomain: claim
scope: claim
role: judge
---
```

Path: `src/agents/docs/docs-claim-claim-judge.md`

### Input / Output

Input: `{ claim: Claim, rewritten_doc: string }`

Output schema (from Cross-cutting Schemas):

```yaml
# Judge verdict (one per claim per compress run)
judge_verdict:
  claim_id: string
  verdict: entailed | partial | dropped
  evidence_span: string | null  # substring of rewritten_doc, null when dropped
  confidence: float             # [0.0, 1.0]
```

### Determinism / Cache

Verdicts cached by `(sha256(claim.text), sha256(rewritten_doc))` — same input pair → same verdict. This makes re-runs idempotent and prevents LLM non-determinism from producing coverage flicker across identical compresses.

### Threshold (from `references/thresholds.yaml`)

```yaml
judge_confidence_floor: 0.6     # below this, escalate verdict to "partial"
```

### Vocab note — `role: judge`

`judge` is a REUSED role token. No new row is needed in `registry/AGENT_VOCABULARY.md` for this artifact. The existing `judge` role entry already covers it. The new vocabulary additions for this suite are: domain `docs`, subdomain `claim`, scopes `doc` and `claim`, roles `extractor` and `classifier`.

---

## Entailment semantics (preciseness)

- **Entailed:** claim is present in meaning in the rewritten doc; paraphrase is acceptable; exact wording not required.
- **Partial:** paraphrase present but a qualifier, hedge, or scope constraint from the original is lost.
- **Dropped:** no evidence span can be located; `evidence_span` is null.
- Threshold for the LLM judgment call: ~0.8 semantic match — this is a prompt-driven threshold, not a numeric score the user tunes directly. The `judge_confidence_floor: 0.6` threshold controls when a stated verdict is overridden to `partial` (not the match threshold itself).

---

## Boundary lens findings

This is the highest-reuse agent in the suite. Its interface is deliberately pure: `(claim, text) → verdict`. No side effects, no rewriting, no scoring quality.

**Confirmed non-scope:**
- Does NOT suggest rewrites or improvements.
- Does NOT score writing quality.
- Does NOT batch internally — each call handles exactly one claim. Batching is the caller's responsibility (shrinker compress phase iterates).

**Reuse trajectory (design interface accordingly):**
- Test coverage verification: judge whether a test file's assertion claims are preserved in refactored code.
- Doc-vs-code sync: judge whether API contract claims in docs are preserved in the implementation.
- RAG eval: judge whether retrieved context entails a query claim.

**Interface decision:** inputs are `{ claim: Claim, rewritten_doc: string }`. The `original_context` field (present in early Resolved notes) was dropped by the preciseness lens — judge only needs the claim and the target text. Do not add it back.

**Slug lock:** `docs-claim` subdomain locks this agent to the docs claim workflow for MVP. If a future general-purpose judge is needed, propose alias or migration to a broader subdomain (e.g., `meta-eval-claim-judge`) at promotion time. Do not widen the slug for MVP.

---

## Edge cases considered

| Edge case | Handling |
|---|---|
| Empty `rewritten_doc` | All claims marked `dropped`; do not crash |
| LLM confidence below `judge_confidence_floor: 0.6` | Override verdict to `partial` regardless of stated verdict |
| Same `(claim_text_hash, doc_hash)` pair on re-run | Return cached verdict — deterministic, no second LLM call |
| Malformed JSON from LLM | One retry, then surface structured error |
| `rewritten_doc` missing section headings | Not the judge's responsibility — shrinker validates heading presence before dispatching judge |

---

## Dependencies

| Artifact | Direction | Contract |
|---|---|---|
| `docs-claim-doc-shrinker` | consumed by | Compress phase calls judge once per kept claim; aborts write if `failed / total > coverage_abort_pct (0.20)` |
| `Claim` schema (Cross-cutting) | consumes | Input `claim` must conform to the `Claim` object schema; `claim_id` is echoed in `judge_verdict.claim_id` |
| `judge_verdict` schema (Cross-cutting) | produces | Output must conform exactly; schema versioning required; consumers reject unknown schema versions loudly |
| `references/thresholds.yaml` | consumes | Reads `judge_confidence_floor: 0.6` at runtime; threshold is not hard-coded in prompt |

---

## Open questions

None. All threads resolved during lens rotation.
