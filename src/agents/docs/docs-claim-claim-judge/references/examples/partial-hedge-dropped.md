# Fixture — partial (hedge dropped)

Pairs a hedged claim with a `rewritten_doc` that contains the unhedged core assertion. Used by EVAL T3. The qualifier ("usually") is meaningful information loss the human reviewer needs to see.

## Claim

```yaml
claim:
  id: "c3d4e5f6"
  heading_anchor: "principles"
  text: "We usually prefer reversible changes."
  source_lines: [5, 5]
```

## Rewritten doc

```
# Engineering Practice

## Principles
- We prefer reversible changes.
- Reviews are shared work.
```

## Expected `judge_verdict`

```yaml
judge_verdict:
  claim_id: "c3d4e5f6"
  verdict: partial
  evidence_span: "We prefer reversible changes."
  confidence: ">= 0.6"
```

An `entailed` verdict here is a FAIL — the "usually" hedge is gone, see EVAL O11.
