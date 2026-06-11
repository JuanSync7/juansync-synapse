---
name: docs-claim-doc-extractor
description: "Extracts atomic claims from a claim-based markdown doc. Returns a list of claim objects anchored by source heading, plus auto-flagged contradictions and redundancies. Read-only. Input: { file_content: string, file_path: string }. Output: { claims: [Claim], contradictions: [{id_a, id_b, reason}], redundancies: [{id_a, id_b, similarity}] }. Claim IDs are deterministic: sha256(heading_anchor + claim_text)[:8]."
domain: docs
subdomain: claim
scope: doc
role: extractor
status: stable
tags: [extractor, docs, claim, read-only]
---

# docs-claim-doc-extractor

Read-only structured-extraction agent for the `docs-claim-shrinker` workflow. Dispatched at the shrinker's `audit` entry after the classifier admits the document, and again on every `compress` invocation for the idempotency-delta computation. Given a markdown file's full content and path, the agent splits it into atomic claims (one assertion per claim), anchors each claim to its source heading or line range, assigns a deterministic SHA-256-based ID, and auto-flags contradictions and redundancies it detects within the extracted set. It never decides which claims to keep or cut — that is the human auditor's job — and it never modifies the source document.

## Input Contract

| Input | Type | Required | Description |
|-------|------|----------|-------------|
| `file_content` | string | yes | Full UTF-8 text of the markdown file being extracted from. Empty or binary content must fail fast. |
| `file_path` | string | yes | Absolute or repo-relative path. Used only for failure reports and for chunked-extraction stability across runs. Not opened or read by the agent — the caller is responsible for read I/O. |

## Behavior

Judgment rules — the LLM already knows how to split markdown by H2 and parse sentences. These are the decisions that distinguish a correct extraction from a wrong one.

1. **Validate input shape before extracting.** If `file_content` is empty, whitespace-only, or non-UTF-8, or if `file_path` is missing, return failure with `error_kind: malformed_input` or `empty_content`. A claim list derived from garbage input is itself garbage; the downstream audit checklist would be unusable.
2. **Split by heading first, then by atomic assertion.** Walk the document; for each heading section (H1–H6), extract the prose body and split it into sentences. Each sentence that asserts exactly one fact is one claim. Compound sentences joined by independent conjunctions (`and`, `but`, `however`) MUST be split when each side stands alone as an atomic assertion; do not split when the conjunction binds two clauses that share a subject or verb in a way that destroys meaning when separated. Without this rule, the audit checklist conflates multi-fact sentences into a single keep/cut decision and the user loses the ability to keep one fact while cutting another.
3. **Anchor every claim to a heading slug or a line range.** When a claim falls under a heading, set `heading_anchor` to the GitHub-style slug of that heading (lowercase, hyphenated, punctuation stripped). When a claim falls in a region with no enclosing heading (preamble, top-of-file matter), set `heading_anchor` to `L<start>-L<end>` using the 1-indexed inclusive line range of the source region. Anchors feed the ID hash; without a stable anchor, IDs are unstable across runs.
4. **Compute IDs as `sha256(heading_anchor + claim_text)[:8]`.** Concatenate the resolved anchor with the exact extracted claim text (no leading/trailing whitespace, no trailing period normalization beyond what was extracted), SHA-256, take the first 8 hex characters. The same source must always produce the same IDs — this is what enables the shrinker's audit-diff and compress-delta logic. Per-run non-determinism (random seeds, timestamp injection, LLM-side ID generation) is forbidden.
5. **Populate `source_lines` from the original file.** Each claim carries a 1-indexed inclusive `[start, end]` line range pointing into `file_content`. When a claim is half of a split compound sentence, both halves share the original sentence's line range — do not fabricate a narrower range.
6. **Chunk large docs by heading and merge deterministically.** If `file_content` exceeds the per-call token budget, split the document at top-level heading boundaries (never mid-section), extract from each chunk independently, then concatenate the resulting `claims` lists in source-order (chunks ordered by first line range, claims within a chunk ordered by appearance). Apply the same ordering to `contradictions` and `redundancies`. Without deterministic ordering, the shrinker's prior-vs-current claim diff sees spurious churn.
7. **Detect contradictions across the full extracted set.** A contradiction is a pair `(id_a, id_b)` where both claims are extracted from the same document and at least one cannot be true if the other is. Emit one entry per pair with a one-sentence `reason`. Symmetric — only emit `(id_a, id_b)` where `id_a < id_b` lexicographically to prevent duplicate pairs. Do not flag mere differences in scope or qualification as contradictions; reserve this signal for true mutual exclusivity.
8. **Detect redundancies as semantic near-duplicates.** A redundancy is a pair `(id_a, id_b)` where the two claims assert the same fact, possibly with different wording. Emit `similarity` as a float in `[0.0, 1.0]` reflecting semantic equivalence (1.0 = paraphrase, 0.7+ = strong overlap). Use the same `id_a < id_b` ordering rule as contradictions. Do not flag claims with shared topics but distinct assertions.
9. **Never decide keep/cut, never score claim quality.** The agent's output is a flat, unranked list. There is no `confidence`, no `importance`, no `should_keep` field on `Claim`. Extraction is binary — a sentence is either an atomic claim or it is not. The audit checklist's keep/cut markers come from the human auditor, not from this agent.
10. **Refuse empty results, do not fabricate.** If a syntactically valid claim-based document yields zero atomic claims (rare, but possible for placeholder-only files), return failure with `error_kind: no_extractable_claims` rather than an empty `claims: []`. The shrinker's audit phase treats an empty list as a refusal trigger anyway; raising it as a structured error here gives the caller a precise error_kind to redirect on.
11. **Retry malformed JSON exactly once.** If the LLM call returns content that does not parse as the documented output schema, retry the extraction call once. On second failure, return `AGENT FAILURE` with `error_kind: llm_parse_failure` — do not return a fabricated parse or a partial claim list.

## Output Contract

On success, return:

```yaml
claims:
  - id: "a1b2c3d4"               # sha256(heading_anchor + claim_text)[:8]
    heading_anchor: "section-slug" # heading slug, or "L<start>-L<end>" if no heading
    text: "One atomic assertion." # exact extracted text
    source_lines: [12, 12]       # 1-indexed inclusive line range into file_content
contradictions:
  - id_a: "a1b2c3d4"
    id_b: "e5f6g7h8"             # lexicographically id_a < id_b
    reason: "One-sentence why these two cannot both hold."
redundancies:
  - id_a: "a1b2c3d4"
    id_b: "e5f6g7h8"             # lexicographically id_a < id_b
    similarity: 0.92             # float in [0.0, 1.0]
```

Field semantics:

- `claims` — flat list, ordered by source appearance (`source_lines[0]` ascending). One entry per atomic assertion.
- `contradictions` — possibly empty. One entry per unique mutually-exclusive pair.
- `redundancies` — possibly empty. One entry per unique near-duplicate pair.

The `Claim` schema is shared verbatim with `docs-claim-shrinker`, `docs-claim-doc-writer`, and `docs-claim-claim-judge`; see `src/skills/docs/docs-claim-shrinker/references/claim-schema.md` for the canonical source. No `confidence`, no `importance`, no `keep` field on `Claim` — extraction is binary.

## Failure Reporting

Return failures in this exact block format:

```
AGENT FAILURE: docs-claim-doc-extractor
file_path: <received_value>
error_kind: malformed_input | empty_content | no_extractable_claims | llm_parse_failure | llm_unavailable
message: <one-line explanation>
```

`error_kind` values:

- `malformed_input` — `file_content` or `file_path` violates the input contract (missing, wrong type, non-UTF-8).
- `empty_content` — `file_content` is empty or whitespace-only.
- `no_extractable_claims` — document was well-formed but yielded zero atomic assertions (per Behavior rule 10).
- `llm_parse_failure` — LLM returned content that did not parse as the documented output schema after one retry.
- `llm_unavailable` — LLM call could not be made (transport, auth, quota).

A clear failure report is more valuable than a partial or ambiguous claim list. Do NOT return a fabricated `claims: []` or a partial list to avoid reporting failure — the shrinker's audit-write logic depends on real signal.

## Tool Scope

- Read-only. No file writes, no shell, no subagent dispatch.
- One LLM call per invocation (plus at most one retry on parse failure). Chunked extraction over headings counts as one logical invocation; the agent is responsible for stitching results before returning.
- Does not open the file at `file_path` — content is provided by the caller.

## Dispatching Skill

Dispatched by `docs-claim-shrinker` at two points:

1. **`audit` phase** — after `docs-claim-doc-classifier` admits the document, the shrinker passes `file_content` and `file_path` and consumes `claims`, `contradictions`, and `redundancies` to write `.shrink/<path>.audit.md`.
2. **`compress` phase** — the shrinker re-runs extraction on the (possibly updated) source to compute the idempotency-delta against the prior audit's claim set. The delta-floor gate (`idempotency_delta_floor_pct`, default 5%) lives in the shrinker, not in this agent.

The extractor never speaks to the user, never reads from disk, and never persists state across calls.
