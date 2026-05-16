# EVAL — docs-claim-claim-judge

> Generated against the design doc at `change_requests/2026-05-13-juansync7-shrink-skill-design.md` §3.2, §4, §7. Regenerate with `/synapse-router-eval-writer src/agents/docs/docs-claim-claim-judge` when the agent body or design doc changes.

This EVAL is the acceptance contract that the agent body must satisfy. Failures here block promotion. Three layers: structural (does the artifact have the right shape), output (does it return the right schema and obey the policy), and blind prompts (does an unseen run produce the right answer).

---

## Structural Criteria

Binary checks against `docs-claim-claim-judge.md`. Each row PASS or FAIL.

| # | Check | Pass condition |
|---|-------|----------------|
| S1 | Frontmatter present | YAML `---` block at top of file |
| S2 | Frontmatter `name` | Equals `docs-claim-claim-judge` |
| S3 | Frontmatter `description` | Verbatim from design §7 (mentions single claim, semantic preservation, entailed/partial/dropped, evidence span, batch dispatch) |
| S4 | Frontmatter `domain` | `docs` |
| S5 | Frontmatter `subdomain` | `claim` |
| S6 | Frontmatter `scope` | `claim` (NOT `doc` — judge operates on a single claim's entailment status) |
| S7 | Frontmatter `role` | `judge` |
| S8 | "What this agent does" framing paragraph | Present before any rule list; conceptual model emphasising single-claim scope and batch-dispatch use; explains why semantic preservation is not strict logical entailment |
| S9 | Input contract | Names `claim: Claim` and `rewritten_doc: string` |
| S10 | Output contract — `judge_verdict` schema verbatim | Embeds the `judge_verdict` YAML schema verbatim from design §4 (claim_id, verdict, evidence_span, confidence) |
| S11 | Do list | Mirrors design §3.2 Do steps 1–4 (assess semantic preservation, classify verdict, return confidence, cache key) |
| S12 | Verdict enum | Lists `entailed | partial | dropped` and defines each: partial = qualifier/hedge lost; dropped = no evidence, evidence_span null |
| S13 | Confidence-floor escalation rule | States: if `confidence < judge_confidence_floor` (0.6), escalate verdict to `partial` regardless of stated verdict |
| S14 | Cache-key rule | States: cache by `(sha256(claim.text), sha256(rewritten_doc))` for re-run determinism |
| S15 | Empty-doc behavior | States: empty rewritten_doc must NOT crash; all claims `dropped` |
| S16 | Don't list | Includes explicit prohibitions: no rewrite suggestions, no style/quality scoring, no crash on empty rewritten_doc |
| S17 | Threshold reference | Cites `judge_confidence_floor: 0.6` and notes the value lives in `src/skills/docs/docs-claim-doc-shrinker/references/thresholds.yaml` (cross-suite link); agent does not hardcode |
| S18 | Loud failure preconditions | Explicit branches for malformed input and malformed model output (one retry then structured error) |
| S19 | Exit contract | Names success output (`judge_verdict` object per claim) and structured-error path |

**Verdict rule:** any FAIL in S1–S19 → REVISE.

---

## Output Criteria

Behavioral checks the agent's runtime output must satisfy. Evaluated against the blind prompts below.

| # | Check | Pass condition |
|---|-------|----------------|
| O1 | Returns valid `judge_verdict` | Object with four fields: `claim_id`, `verdict`, `evidence_span`, `confidence` |
| O2 | `verdict` enum strictness | Exactly one of `entailed`, `partial`, `dropped`; any other string is a FAIL |
| O3 | `claim_id` echo | Equals the input `claim.id` verbatim — no recomputation, no rehash |
| O4 | `confidence` range | Float in `[0.0, 1.0]` inclusive |
| O5 | Confidence-floor escalation | When raw confidence < 0.6, the returned `verdict` is `partial` regardless of the model's stated verdict (escalation from `entailed` and from `dropped` both land at `partial`) |
| O6 | `evidence_span` is substring of rewritten_doc | When `verdict ∈ {entailed, partial}` and rewritten_doc is non-empty, `evidence_span` is a verbatim substring of `rewritten_doc` (whitespace-exact) |
| O7 | `evidence_span` is null when dropped | When `verdict = dropped`, `evidence_span` is `null` (not `""`, not an excuse string) |
| O8 | Cache-key determinism | Two independent invocations with the same `(claim.text, rewritten_doc)` pair produce the same `verdict` and the same `evidence_span` — cache key is `(sha256(claim.text), sha256(rewritten_doc))` |
| O9 | Empty rewritten_doc → dropped | When `rewritten_doc = ""`, returns `verdict = dropped`, `evidence_span = null`; does not crash; confidence may still be reported |
| O10 | Paraphrase counts as entailed | A claim whose meaning is preserved with reordered or substituted wording is `entailed`, not `partial` (semantic preservation, not lexical match) |
| O11 | Lost qualifier → partial | A claim with a hedge (`usually`, `in most cases`, `if X`) whose qualifier is missing from the rewrite is `partial`, not `entailed` |
| O12 | No rewrite suggestion field | Output object does not include `suggested_rewrite`, `fix`, `improvement`, or any style/quality scoring field |
| O13 | Malformed input → structured error | On missing `claim.text` or non-string `rewritten_doc`, returns single-line `INPUT ERROR: ...`, not a guess |

---

## Blind Test Prompts

Six prompts. Each is a fresh agent invocation with no prior context. Fixtures live under `references/examples/`.

### T1 — Entailed verbatim

**Input:** Claim + rewritten_doc from `references/examples/entailed-verbatim.md`.

**Expected:**
```yaml
judge_verdict:
  claim_id: <echoed from input>
  verdict: entailed
  evidence_span: <verbatim substring of rewritten_doc containing the claim>
  confidence: ≥ 0.8
```

### T2 — Entailed paraphrase

**Input:** Claim + rewritten_doc from `references/examples/entailed-paraphrase.md`. The claim's wording differs from the rewrite but meaning is preserved.

**Expected:** `verdict: entailed`; `evidence_span` is a substring of `rewritten_doc` covering the paraphrased sentence; `confidence: ≥ 0.7`. A `partial` verdict here is a FAIL — paraphrase preserving semantics is entailment per the agent's mental model.

### T3 — Partial (hedge dropped)

**Input:** Claim + rewritten_doc from `references/examples/partial-hedge-dropped.md`. The claim is "We **usually** prefer reversible changes"; the rewrite says "We prefer reversible changes" — the qualifier is gone.

**Expected:** `verdict: partial`; `evidence_span` covers the unhedged rewrite sentence; `confidence ≥ 0.6`. `entailed` is a FAIL.

### T4 — Dropped

**Input:** Claim + rewritten_doc from `references/examples/dropped.md`. The claim asserts something absent from the rewrite.

**Expected:** `verdict: dropped`; `evidence_span: null`; `confidence ≥ 0.6`.

### T5 — Low-confidence escalation to partial

**Input:** Claim + rewritten_doc from `references/examples/low-confidence-escalation.md`. The rewrite is ambiguous enough that the raw confidence on `entailed` lands below 0.6.

**Expected:** Returned `verdict: partial` (escalated from raw `entailed`). The reported `confidence` may be `< 0.6`; the agent must still emit it honestly. A returned `verdict: entailed` is a FAIL — the floor escalation is non-optional.

### T6 — Empty rewritten_doc edge case

**Input:** Any claim with `rewritten_doc: ""`.

**Expected:** `verdict: dropped`; `evidence_span: null`. Agent must NOT crash, must NOT return a structured error (empty string is a valid input), and must NOT hallucinate evidence. The shrinker depends on this for its worst-case path (writer produced an empty result).

---

## Verdict Aggregation

- Any FAIL in S1–S19 → REVISE with structural findings.
- Any FAIL in O1–O13 → REVISE with output findings.
- Any FAIL in T1–T6 → REVISE with prompt-level findings.
- All PASS → APPROVE.
