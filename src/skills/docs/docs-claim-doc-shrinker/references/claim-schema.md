# Claim Schema

Shared cross-cutting object used by the extractor (output), the audit checklist (source rows), the writer (input), and the judge (per-claim verdict). Verbatim from design doc §4.

Loaded by the shrinker at extractor dispatch and writer dispatch so that both sides agree on field names and types.

```yaml
# Claim object — extractor output, audit-checklist source, writer input
claim:
  id: string                  # deterministic hash(heading_anchor + claim_text)
  heading_anchor: string      # heading slug or "L<start>-L<end>" if no heading
  text: string                # one atomic assertion
  source_lines: [int, int]    # 1-indexed inclusive line range
```

## Determinism contract

`id = sha256(heading_anchor + claim_text)[:8]`. The same source text under the same heading must always produce the same id. Renaming a heading invalidates every claim id under it — this is intentional and surfaces as the hash-mismatch refusal in the compress phase.

## Atomicity contract

One assertion per claim. The extractor splits compound sentences at independent conjunctions ("and"/"but"/"however"). The writer must cover every kept claim; the judge evaluates entailment claim-by-claim.
