# Decision Memo — docs-claim-doc-extractor

> Artifact type: agent | Memo type: creation | Design doc: `.brainstorms/2026-05-13-shrink-skill/design.md`

---

## What I want

An agent that reads a claim-based markdown document and extracts every atomic assertion from it as a structured list of claim objects, anchored to their source headings and line ranges. It also auto-detects contradictions and redundancies within the extracted claim set, emitting them as separate output fields. The extractor is read-only — it never modifies the source document and never decides which claims to keep or cut.

---

## Why Claude needs it

Without this agent, the shrinker skill has no reliable, schema-stable way to enumerate the claims in a doc. A freeform LLM pass produces inconsistent splits (compound sentences sometimes split, sometimes not), unstable IDs (no diffing between audit runs), and no contradiction/redundancy signal. The audit checklist cannot be generated without a deterministic, structured claim list as input.

---

## Injection shape

- **Domain knowledge:** Atomic-claim splitting rules, heading-anchor computation, hash-based ID generation, contradiction/redundancy detection heuristics.
- **Policy:** What constitutes one atomic assertion; when to split on conjunctions; how to compute heading anchors when no heading is present; confidence-free extraction (extraction is binary — a sentence either is or is not an atomic claim).

---

## What it produces

| Output | Count | Mutable? | Purpose |
|---|---|---|---|
| `claims` list | 1 per agent call | No | Structured claim objects fed to audit checklist generator (shrinker audit phase) and writer (compress phase) |
| `contradictions` list | 1 per agent call | No | Auto-flagged contradictions surfaced in `## Contradictions` section of audit checklist |
| `redundancies` list | 1 per agent call | No | Auto-flagged redundancies surfaced in `## Redundancies` section of audit checklist |

---

## Agent frontmatter (VERBATIM)

```yaml
---
name: docs-claim-doc-extractor
description: Extracts atomic claims from a claim-based markdown doc. Returns a list of claim objects anchored by source heading, plus auto-flagged contradictions and redundancies. Read-only.
domain: docs
subdomain: claim
scope: doc
role: extractor
---
```

Path: `src/agents/docs/docs-claim-doc-extractor.md`

---

## Input / Output contract (VERBATIM)

Input: `{ file_content: string, file_path: string }`

Output: `{ claims: [Claim], contradictions: [{id_a, id_b, reason}], redundancies: [{id_a, id_b, similarity}] }`

Atomic-claim rule: one assertion per claim; split compound sentences on independent conjunctions ("and"/"but"/"however") when each side stands alone; claim IDs are `sha256(heading_anchor + claim_text)[:8]` — stable across runs.

---

## Claim object schema (VERBATIM)

```yaml
# Claim object — extractor output, audit-checklist source, writer input
claim:
  id: string                  # deterministic hash(heading_anchor + claim_text)
  heading_anchor: string      # heading slug or "L<start>-L<end>" if no heading
  text: string                # one atomic assertion
  source_lines: [int, int]    # 1-indexed inclusive line range
```

---

## Audit checklist file shape — extractor feeds this (VERBATIM)

```markdown
---
source_path: <relative-path>
source_hash: <sha256-of-source-content>
audit_timestamp: <iso8601>
classifier:
  category: claim-based
  sub_type: identity
schema_version: "1"
---

## <Section Heading from source>
- [x] keep: <claim_id> — <claim text>
- [ ] cut:  <claim_id> — <claim text>
- [m] merge-with <other_id>: <claim_id> — <claim text>

## Contradictions
- (<id_a> ↔ <id_b>): <reason>

## Redundancies
- (<id_a> ≈ <id_b>): similarity <score>
```

---

## Vocab additions relevant to this agent (VERBATIM)

```
# registry/AGENT_VOCABULARY.md additions
## Domains
| `docs` | User-facing documentation agents |
## Subdomains
| `claim` | Agents that operate within the claim-based-doc workflow |
## Scopes
| `doc` | Operates on a single markdown doc |
## Roles
| `extractor` | Extracts atomic structured items from input |
```

---

## Edge cases considered

| Edge case | Handling |
|---|---|
| No headings in source | Anchor by line range: `L<start>-L<end>` (e.g., `L12-L18`) |
| Doc exceeds token budget | Chunk by heading, merge claim lists, apply deterministic ordering across chunks |
| Compound sentence with independent clauses | Split on "and"/"but"/"however" when each side stands alone as an atomic assertion |
| Empty claim list returned | Refuse — surface "doc has no extractable claims" to skill; no audit written |
| Re-extraction run (idempotency check) | IDs are deterministic from `sha256(heading_anchor + claim_text)[:8]` → stable across runs; shrinker diffs new vs prior claim list to compute Δ |
| Heading renamed in source between audit and compress | IDs invalidate → stale-source policy (hash mismatch) triggers refuse + re-audit prompt; no silent recovery |
| Malformed input (missing fields) | Validate schema before LLM call; return structured error, not empty response |
| LLM returns malformed JSON | One retry, then surface error to caller |

---

## Companion files anticipated

**References (loaded on-demand):**

| File | Loaded at | Purpose |
|---|---|---|
| `src/skills/docs/docs-claim-shrinker/references/claim-schema.md` | Agent prompt | Canonical claim object schema — shared source of truth across all 5 artifacts |
| `src/skills/docs/docs-claim-shrinker/references/thresholds.yaml` | Agent prompt (if needed) | Not directly consumed by extractor; referenced by skill dispatch |

---

## Dependencies

| Artifact | Direction | Contract |
|---|---|---|
| `docs-claim-doc-classifier` | Consumes (upstream) | Shrinker runs classifier before extractor; extractor is only called when `category=claim-based`. Classifier output not injected into extractor — extractor operates on raw content. |
| `docs-claim-shrinker` | Produces for | Extractor output (`claims`, `contradictions`, `redundancies`) feeds shrinker's audit phase → written to `.shrink/<file>.audit.md` |
| `docs-claim-doc-writer` | Produces for | `kept_claims` (filtered subset of extractor's `claims` list) is the primary writer input in the compress phase |
| `docs-claim-claim-judge` | Produces for (indirectly) | Judge receives individual `Claim` objects; the claim schema is defined by extractor output |

---

## Open questions

**Contradiction/redundancy bundling:** Detection is currently bundled into the extractor. This was a deliberate scoping decision — if reuse emerges (e.g., a standalone contradiction-detection workflow), split into its own agent. No action needed for MVP; note as a future change request candidate.

**Claim ID stability:** Resolved as hash-based (`sha256(heading_anchor + claim_text)[:8]`). If a user renames a heading in the source, IDs invalidate. This is correct behavior — it matches the stale-source policy (refuse + re-audit). No silent recovery.

**Per-claim confidence:** Dropped. Extraction is binary — either a sentence is an atomic claim or it is not. No confidence field on `Claim` objects (preciseness finding).
