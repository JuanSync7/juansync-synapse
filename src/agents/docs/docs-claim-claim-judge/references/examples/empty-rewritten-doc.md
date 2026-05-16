# Fixture — empty rewritten_doc edge case

Worst-case path for the shrinker: the writer produced an empty string. The judge must NOT crash and must NOT emit a structured error — empty string is a valid string. Every claim is `dropped`. Used by EVAL T6.

## Claim

```yaml
claim:
  id: "f6a7b8c9"
  heading_anchor: "principles"
  text: "We never merge without a rollback path."
  source_lines: [3, 3]
```

## Rewritten doc

```

```

(Empty string. Zero characters.)

## Expected `judge_verdict`

```yaml
judge_verdict:
  claim_id: "f6a7b8c9"
  verdict: dropped
  evidence_span: null
  confidence: ">= 0.6"   # absence is unambiguous; confidence is typically high
```

A crash, a structured `INPUT ERROR`, or a hallucinated `evidence_span` are all FAILs — see EVAL O9.
