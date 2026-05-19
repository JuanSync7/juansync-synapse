# Judge verdict schema

Verbatim from design doc §4. Returned by `docs-claim-claim-judge` once per kept claim per compress run.

```yaml
judge_verdict:
  claim_id: string
  verdict: entailed | partial | dropped
  evidence_span: string | null  # substring of rewritten_doc, null when dropped
  confidence: float             # [0.0, 1.0]
```

## Verdict semantics

- `entailed` — claim is semantically preserved (paraphrase is acceptable; strict logical entailment is NOT required).
- `partial` — qualifier or hedge lost in rewrite, OR judge confidence below `judge_confidence_floor` (escalation rule).
- `dropped` — no evidence found in rewritten_doc; `evidence_span` is null.

## Confidence escalation

If `confidence < judge_confidence_floor` (from `thresholds.yaml`), the judge MUST escalate verdict to `partial` regardless of its stated verdict. Below-floor `entailed` is not trusted.

## Coverage aggregation (skill-side)

The skill counts `partial` AND `dropped` as failures. If failure ratio exceeds `coverage_abort_pct` (from `thresholds.yaml`), the atomic write is aborted and §9 refusal #5 is emitted with the coverage report path.
