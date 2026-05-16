# Fixture — low-confidence escalation to partial

Pairs a claim with an ambiguous `rewritten_doc` where raw confidence on `entailed` lands below `judge_confidence_floor` (0.6). The agent MUST escalate the verdict to `partial`. Used by EVAL T5.

## Claim

```yaml
claim:
  id: "e5f6a7b8"
  heading_anchor: "principles"
  text: "We treat documentation as part of the change, not a follow-up."
  source_lines: [7, 7]
```

## Rewritten doc

```
# Engineering Practice

## Principles
- Documentation matters.
- Reviews are shared work.
```

The rewrite says "Documentation matters" — adjacent in topic but doesn't clearly preserve the "part of the change, not a follow-up" assertion. A model genuinely uncertain whether this entails the claim will land confidence in the 0.4–0.55 range.

## Expected `judge_verdict`

```yaml
judge_verdict:
  claim_id: "e5f6a7b8"
  verdict: partial          # escalated from raw entailed by the confidence floor
  evidence_span: "Documentation matters."
  confidence: "< 0.6"        # raw, not rounded up after escalation
```

A returned `verdict: entailed` is a FAIL — the floor escalation is non-optional, see EVAL O5.
