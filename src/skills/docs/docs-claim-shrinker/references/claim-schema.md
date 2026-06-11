# Claim object schema

Verbatim from design doc §4. Shared shape for extractor output, audit-checklist source, and writer input.

```yaml
claim:
  id: string                  # deterministic hash(heading_anchor + claim_text)
  heading_anchor: string      # heading slug or "L<start>-L<end>" if no heading
  text: string                # one atomic assertion
  source_lines: [int, int]    # 1-indexed inclusive line range
```

## ID derivation

`id = sha256(heading_anchor + claim_text)[:8]`

Determinism rule: the same source text must always produce the same claim text (and thus the same ID). No per-run non-determinism is acceptable. If a heading is renamed in the source, IDs for claims under that heading change — this is intentional and surfaced as a hash-mismatch refusal during `compress`.

## Atomic-claim splitting (extractor contract)

- One assertion per claim.
- Split compound sentences at independent conjunctions: `and`, `but`, `however`.
- For headingless regions, use anchor `L<start>-L<end>`.
