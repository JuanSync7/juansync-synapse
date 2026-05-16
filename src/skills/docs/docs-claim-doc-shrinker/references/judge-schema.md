# Judge Verdict Schema

Returned by `docs-claim-claim-judge` for each kept claim during the compress phase. Verbatim from design doc §4.

```yaml
# Judge verdict (one per claim per compress run)
judge_verdict:
  claim_id: string
  verdict: entailed | partial | dropped
  evidence_span: string | null  # substring of rewritten_doc, null when dropped
  confidence: float             # [0.0, 1.0]
```

## Verdict semantics

| Verdict | Meaning |
|---|---|
| `entailed` | Claim is semantically preserved in the rewrite. Paraphrase is acceptable; strict logical entailment is not required. |
| `partial` | A qualifier or hedge is lost in the rewrite. The core assertion survives but is degraded. |
| `dropped` | No evidence of the claim in the rewrite. `evidence_span` is null. |

## Confidence floor

When the judge returns `confidence < judge_confidence_floor` (0.6), the shrinker escalates the verdict to `partial` regardless of the stated verdict. This is the skill's responsibility; the judge does not self-escalate.

## Coverage rule

The shrinker counts a `dropped` verdict as a failure. If failures exceed `coverage_abort_pct` (20%) of the kept-claim count, the compress aborts before any write. `partial` does not count as a failure but is reported in the coverage table.

## Determinism

The judge caches verdicts by `(sha256(claim.text), sha256(rewritten_doc))` so that two compress runs against an unchanged rewrite reproduce the same verdicts.
