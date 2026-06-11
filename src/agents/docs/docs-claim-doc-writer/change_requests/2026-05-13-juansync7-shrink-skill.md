# Decision Memo — docs-claim-doc-writer

> Artifact type: agent | Memo type: creation | Design doc: `.brainstorms/2026-05-13-shrink-skill/design.md`

---

## What I want

Rewrites a claim-based markdown doc compressed against a fixed kept-claim set. Does NOT generate docs from scratch. Does NOT introduce claims outside the input set. Preserves every section heading present in the original. For style-sub-type docs, preserves cadence and diction via voice anchors sampled from the source.

This agent is invoked by the `docs-claim-shrinker` compress phase after the user has edited the audit checklist. It produces the rewritten document that the judge then verifies claim-by-claim.

---

## Why Claude needs it

Without a dedicated writer agent, the shrinker would either (a) inline the rewrite prompt directly — losing isolation and making the entailment contract untestable — or (b) rely on a general LLM rewrite that has no awareness of the kept-claim set, routinely adding transitional context that introduces new claims and silently violating the no-hallucination contract. A dedicated agent with a hard-contract prompt is the only way to make the constraint machine-verifiable downstream by the judge.

---

## Injection shape

- **Policy:** Hard contract rules injected verbatim into the agent prompt — no opt-out parameters for claim coverage, heading preservation, or length floor.
- **Domain knowledge:** Voice anchor protocol for style-sub-type docs; `writer_length_sanity_pct` threshold; vocab note that `role=writer` is REUSED from the existing `AGENT_VOCABULARY.md` (no new vocabulary row needed for this role).

---

## What it produces

| Output | Count | Mutable? | Purpose |
|---|---|---|---|
| `rewritten_doc` (string) | 1 | No | Compressed markdown ready for judge verification and atomic write to source |

---

## Agent frontmatter

<!-- VERBATIM -->
```yaml
---
name: docs-claim-doc-writer
description: Rewrites a claim-based doc compressed against a fixed kept-claim set. Does NOT generate from scratch. Does NOT introduce claims outside the input set. Preserves section headings. For style-sub-type docs, preserves cadence via voice anchors.
domain: docs
subdomain: claim
scope: doc
role: writer
---
```

Path: `src/agents/docs/docs-claim-doc-writer.md`

---

## Input / Output contract

<!-- VERBATIM -->
```
Input:
  kept_claims:    [Claim]      # claims the user marked keep in the audit checklist
  original_doc:   string       # full source markdown (for heading extraction + voice sampling)
  voice_anchors:  [string]     # 3-5 sentences, only present for sub_type=style

Output:
  rewritten_doc:  string       # compressed markdown, section headings preserved
```

Claim object schema (from Cross-cutting — verbatim):

```yaml
claim:
  id: string                  # deterministic hash(heading_anchor + claim_text)
  heading_anchor: string      # heading slug or "L<start>-L<end>" if no heading
  text: string                # one atomic assertion
  source_lines: [int, int]    # 1-indexed inclusive line range
```

---

## Hard contract (verbatim into prompt)

<!-- VERBATIM -->
```
- MUST cover every claim in `kept_claims` (verified by judge downstream)
- MUST NOT introduce any assertion not in `kept_claims`
- MUST preserve every section heading present in `original_doc`
- For style sub-type: cadence and diction must echo `voice_anchors`
- Output length floor: ≥30% of original length (writer aborts and reports if would emit shorter)
```

Threshold constant (from `references/thresholds.yaml`):

```yaml
writer_length_sanity_pct: 0.30  # warn if output <30% of input length
voice_anchor_count_min: 3
voice_anchor_count_max: 5
```

Vocab note: `role=writer` is **REUSED** — already present in `AGENT_VOCABULARY.md`. No new vocabulary row needed for this artifact.

---

## Anti-confusion clause

**Description must lead with:** "Rewrites a claim-based doc compressed against a fixed kept-claim set; NOT a general docs writer; does NOT introduce claims outside input set."

This agent is the compress-phase rewriter only. It does not:
- Generate documentation from scratch
- Accept a free-form prompt or topic
- Decide which claims to keep or cut (that is the user's job via the audit checklist)
- Self-verify entailment (that is the judge's job)

Caller: `docs-claim-shrinker` compress phase exclusively.

---

## Edge cases considered

| Edge case | Handling |
|---|---|
| Writer would produce output < 30% of input length | Abort; surface `writer_length_sanity_pct` warning before judge stage; no write |
| Writer adds transitional context that introduces a new claim | Judge catches at verdict stage; coverage report flags `dropped` on that claim; shrinker aborts if > `coverage_abort_pct` failures |
| Section heading missing from output | Fail before judge stage — heading-preservation check is a pre-judge gate, not aspirational |
| `voice_anchors` absent for style sub-type | Skill passes anchors only for `sub_type=style`; writer omits voice-anchor instruction block for all other sub-types |
| `kept_claims` is empty list | Writer emits empty doc; judge returns all-`dropped`; shrinker aborts — do not produce empty output silently |
| `structure_preservation` flag | Removed as opt-out parameter (preciseness lens resolution); heading preservation is a hard contract, not a flag |

---

## Dependencies

| Artifact | Direction | Contract |
|---|---|---|
| `docs-claim-shrinker` | consumes from (caller) | Dispatches writer in compress phase after audit-checklist parse; passes `kept_claims`, `original_doc`, `voice_anchors` |
| `docs-claim-doc-extractor` | consumes from (indirect) | Writer's `kept_claims` input is a subset of extractor's claim list; claim schema must be identical |
| `docs-claim-claim-judge` | produces for | Judge receives `rewritten_doc` + each `kept_claim`; verifies entailment claim-by-claim; writer is informed of this contract but does not self-verify |

---

## Companion files anticipated

| File | Loaded at | Purpose |
|---|---|---|
| `references/thresholds.yaml` | writer prompt construction | Supplies `writer_length_sanity_pct`, `voice_anchor_count_min/max` without hard-coding in prompt |
| `references/claim-schema.md` | writer prompt construction | Canonical claim object definition; avoids re-stating schema in agent file |

---

## Open questions

1. **3-month reuse review checkpoint (maintenance lens):** Writer reuse is uncertain — it is the most coupled of the four agents, narrowly scoped to the shrinker compress phase. At the 3-month mark after merge, check whether any second consumer has emerged. If not, evaluate demotion to an inline prompt inside the shrinker to reduce maintenance surface. This is the only artifact in the set flagged for a circuit-breaker review; creator should note this checkpoint in the design doc.

2. **Voice-anchor logic evolution:** Voice anchors are specific to `sub_type=style`. As `SOUL.md` (the MVP test case) and related style docs evolve, the anchor-sampling heuristic may need tuning. Track as a design-doc open question alongside the 3-month checkpoint above.
