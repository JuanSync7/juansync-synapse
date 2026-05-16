# EVAL — docs-claim-doc-extractor

> Generated against the design doc at `change_requests/2026-05-13-juansync7-shrink-skill-design.md` §3.2, §4, §7. Regenerate with `/synapse-router-eval-writer src/agents/docs/docs-claim-doc-extractor` when the agent body or design doc changes.

This EVAL is the acceptance contract that the agent body must satisfy. Failures here block promotion. Three layers: structural (does the artifact have the right shape), output (does it return the right schema and obey the policy), and blind prompts (does an unseen run produce the right answer).

---

## Structural Criteria

Binary checks against `docs-claim-doc-extractor.md`. Each row PASS or FAIL.

| # | Check | Pass condition |
|---|-------|----------------|
| S1 | Frontmatter present | YAML `---` block at top of file |
| S2 | Frontmatter `name` | Equals `docs-claim-doc-extractor` |
| S3 | Frontmatter `description` | Verbatim from design §7 (mentions atomic claims, anchored by heading, contradictions and redundancies, read-only) |
| S4 | Frontmatter `domain` | `docs` |
| S5 | Frontmatter `subdomain` | `claim` |
| S6 | Frontmatter `scope` | `doc` |
| S7 | Frontmatter `role` | `extractor` |
| S8 | "What this agent does" framing paragraph | Present before any rule list; conceptual model, not mechanics; explains why determinism matters |
| S9 | Input contract | Names `file_content: string` and `file_path: string` |
| S10 | Output contract — Claim schema verbatim | Embeds the `claim` YAML schema verbatim from design §4 (id, heading_anchor, text, source_lines) |
| S11 | Output contract — extractor return shape | Documents `{ claims, contradictions, redundancies }` with the contradiction triple `(id_a, id_b, reason)` and redundancy triple `(id_a, id_b, similarity)` |
| S12 | Atomic-claim splitting rule | States explicitly: split on independent conjunctions `and`/`but`/`however` only when each side is a standalone assertion; do NOT split on `or`/`because`/subordinating conjunctions |
| S13 | Deterministic ID rule | States `id = sha256(heading_anchor + claim_text)[:8]` and that no per-run signal (timestamps, line numbers, file path, session) enters the hash |
| S14 | Headingless-region anchor convention | States `L<start>-L<end>` (1-indexed inclusive) for content with no preceding heading |
| S15 | Chunking + merge rule for over-budget docs | States: chunk by top-level heading, merge in source order, re-run contradiction/redundancy across merged set |
| S16 | Don't list — keep/cut, confidence, non-determinism | Includes "no keep/cut", "no per-claim confidence", and explicit prohibition on non-deterministic IDs |
| S17 | Loud failure preconditions | Has explicit branches for empty/binary input and malformed model output (one retry then structured error) |
| S18 | Threshold reference | Cites `idempotency_delta_floor_pct` from `src/skills/docs/docs-claim-doc-shrinker/references/thresholds.yaml` and notes the cross-suite link; agent does not hardcode numeric gates |
| S19 | Exit contract | Names success output (`extractor_output`) and structured-error path; explicitly notes empty-claims is success not refuse |

**Verdict rule:** any FAIL in S1–S19 → REVISE.

---

## Output Criteria

Behavioral checks the agent's runtime output must satisfy. Evaluated against the blind prompts below.

| # | Check | Pass condition |
|---|-------|----------------|
| O1 | Returns valid `extractor_output` | Object with three fields: `claims` (list), `contradictions` (list), `redundancies` (list) |
| O2 | Claim schema fidelity | Every claim has `id`, `heading_anchor`, `text`, `source_lines`; no extra fields |
| O3 | Claim ID format | 8 lowercase hex characters, derived from `sha256(heading_anchor + text)[:8]`; reproducible by an external verifier |
| O4 | Determinism across runs | Two independent invocations on the same input produce identical claim list (same IDs, same text, same anchors, same order) and identical contradiction/redundancy lists |
| O5 | Atomic claim splitting | Compound sentence "We optimize for reversibility and we never merge without a rollback path" splits into two claims; "We optimize for reversibility because speed kills" stays as one (subordinating `because`) |
| O6 | Headingless-region anchor | Pre-heading preamble lines yield anchor of the form `L<n>-L<m>` matching their actual line range |
| O7 | Source line range | `source_lines` is `[start, end]`, both 1-indexed inclusive, both within the file's line count |
| O8 | Ordering | `claims` list is ordered by `source_lines[0]` ascending, ties broken by source position |
| O9 | Contradiction detection | A doc with "X is required" in §A and "X is forbidden" in §B emits a contradiction pair referencing both claim IDs with a one-line reason |
| O10 | Redundancy detection | A doc with two near-paraphrased claims emits a redundancy pair with `similarity ≥ 0.85` and the correct two IDs |
| O11 | No keep/cut decision | All extracted claims are returned; agent does not pre-filter or mark any claim as cut |
| O12 | No per-claim confidence | Claim objects have no `confidence` field |
| O13 | Empty input → structured error | On empty `file_content`, returns single-line `INPUT ERROR: ...`, not a guess |
| O14 | Empty claim list → success | A doc with no claims (e.g., a table-only file) returns `extractor_output` with `claims: []`, not a refusal |
| O15 | Code block exclusion | Prose embedded inside a fenced code block is NOT extracted as a claim |
| O16 | No reasoning_summary field | Output object does not include `reasoning_summary`, `notes`, or `analysis` |

---

## Blind Test Prompts

Four prompts. Each is a fresh agent invocation with no prior context. Fixtures live under `references/examples/`.

### T1 — Small claim-based doc with 3 headings

**Input:** Contents of `references/examples/small-claim-doc.md` plus `file_path: "references/examples/small-claim-doc.md"`.

**Expected:** `extractor_output.claims` matches `references/examples/small-claim-doc.expected.md` row-for-row on `(heading_anchor, text)` pairs. Every claim ID equals the first 8 hex chars of `sha256(heading_anchor + text)`. Both `contradictions` and `redundancies` are empty (`[]`). Order is positional.

### T2 — Compound-sentence splitting

**Input:** Contents of `references/examples/compound-sentence.md`.

**Expected:** The line "We optimize for reversibility and we never merge a change without a rollback path." produces TWO claims (each side is a standalone assertion). The line "We hold each other accountable because review is shared work." produces ONE claim (subordinating `because`). The line "We revise this list when it stops describing how we work, but we do so deliberately." produces TWO claims (independent `but` with standalone sides).

### T3 — Known contradiction

**Input:** Contents of `references/examples/known-contradiction.md`.

**Expected:** `contradictions` contains exactly one pair, with `id_a` and `id_b` matching the IDs of the two contradictory claims (one under §"Allowed", one under §"Forbidden"), and `reason` a single-line plain-text description naming the contradicted predicate. `redundancies` is empty.

### T4 — Known redundancy

**Input:** Contents of `references/examples/known-redundancy.md`.

**Expected:** `redundancies` contains exactly one pair with `similarity ≥ 0.85`, naming the two near-paraphrased claim IDs. `contradictions` is empty.

---

## Verdict Aggregation

- Any FAIL in S1–S19 → REVISE with structural findings.
- Any FAIL in O1–O16 → REVISE with output findings.
- Any FAIL in T1–T4 → REVISE with prompt-level findings.
- All PASS → APPROVE.
