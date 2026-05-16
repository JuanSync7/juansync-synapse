# Fixture — dropped

Pairs a claim with a `rewritten_doc` that contains no evidence of it. Used by EVAL T4. `evidence_span` must be JSON/YAML `null`, not the empty string.

## Claim

```yaml
claim:
  id: "d4e5f6a7"
  heading_anchor: "principles"
  text: "We pair-program on every production-facing change."
  source_lines: [6, 6]
```

## Rewritten doc

```
# Engineering Practice

## Principles
- We prefer reversible changes.
- Reviews are shared work.
- We never merge without a rollback path.
```

## Expected `judge_verdict`

```yaml
judge_verdict:
  claim_id: "d4e5f6a7"
  verdict: dropped
  evidence_span: null
  confidence: ">= 0.6"
```

`evidence_span: ""` or `evidence_span: "none"` are both FAILs — see EVAL O7.
