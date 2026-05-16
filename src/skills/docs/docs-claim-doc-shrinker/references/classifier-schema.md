# Classifier Output Schema

Returned by `docs-claim-doc-classifier` and consumed by the shrinker as the unconditional entry gate. Verbatim from design doc §4.

```yaml
classifier_output:
  schema_version: "1"
  category: claim-based | narrative | reference | tutorial | template | mixed
  sub_type: identity | style | principle | decision | null  # only when category=claim-based
  confidence: float            # [0.0, 1.0]
```

## Gate semantics (enforced by the shrinker, not the classifier)

| Condition | Shrinker action |
|---|---|
| `category != claim-based` AND `category != mixed` | REFUSE with the category refusal message |
| `confidence < classifier_confidence_floor` (0.6) | REFUSE with low-confidence message |
| `category == mixed` AND `--accept-mixed` not passed | REFUSE with mixed-doc message |
| `category == mixed` AND `--accept-mixed` passed | proceed; warn |
| `category == claim-based` AND `confidence >= 0.6` | proceed |

The classifier itself never refuses. It returns the verdict; the skill enforces the floor. This is intentional — a single hardcoded floor inside the agent would defeat the purpose of `thresholds.yaml`.

## Schema versioning

Downstream agents reject unknown `schema_version` values loudly. The current contract is `"1"`. Bumping the version is a coordinated change across all four agents + the skill.
