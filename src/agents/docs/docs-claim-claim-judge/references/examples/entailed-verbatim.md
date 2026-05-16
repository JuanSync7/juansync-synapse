# Fixture — entailed (verbatim)

Pairs a single `claim` with a `rewritten_doc` where the claim text appears verbatim. Used by EVAL T1.

## Claim

```yaml
claim:
  id: "a1b2c3d4"
  heading_anchor: "principles"
  text: "We never merge a change without a rollback path."
  source_lines: [3, 3]
```

## Rewritten doc

```
# Engineering Practice

## Principles
- We never merge a change without a rollback path.
- Review is shared work.
```

## Expected `judge_verdict`

```yaml
judge_verdict:
  claim_id: "a1b2c3d4"
  verdict: entailed
  evidence_span: "We never merge a change without a rollback path."
  confidence: ">= 0.8"
```
