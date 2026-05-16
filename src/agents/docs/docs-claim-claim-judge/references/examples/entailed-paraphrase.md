# Fixture — entailed (paraphrase)

Pairs a claim with a `rewritten_doc` where the meaning is preserved but wording is reordered and synonyms substituted. Used by EVAL T2. The judge must NOT downgrade this to `partial` — semantic preservation is the bar.

## Claim

```yaml
claim:
  id: "b2c3d4e5"
  heading_anchor: "principles"
  text: "We optimize for reversibility."
  source_lines: [4, 4]
```

## Rewritten doc

```
# Engineering Practice

## Principles
- Reversibility is the optimization target for every change we ship.
- Reviews are shared work.
```

## Expected `judge_verdict`

```yaml
judge_verdict:
  claim_id: "b2c3d4e5"
  verdict: entailed
  evidence_span: "Reversibility is the optimization target for every change we ship."
  confidence: ">= 0.7"
```

A `partial` verdict here is a FAIL — see EVAL O10.
