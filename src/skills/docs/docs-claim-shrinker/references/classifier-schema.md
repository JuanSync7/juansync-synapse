# Classifier output schema

Verbatim from design doc §4. Returned by `docs-claim-doc-classifier`. Consumed by the SKILL.md entry gate.

```yaml
classifier_output:
  schema_version: "1"
  category: claim-based | narrative | reference | tutorial | template | mixed
  sub_type: identity | style | principle | decision | null  # only when category=claim-based
  confidence: float            # [0.0, 1.0]
```

## Gating rules (skill-side)

- `category != claim-based` AND `category != mixed` → refuse with category-redirect message (§9 refusal #1).
- `category == mixed` → require explicit `--accept-mixed` flag; otherwise refuse (§9 refusal #4).
- `confidence < classifier_confidence_floor` (from `thresholds.yaml`) → refuse with low-confidence variant of §9 refusal #1.

## Schema versioning

`schema_version: "1"` is required from day one — the classifier output is consumed by four downstream sites (skill orchestrator + three sibling agents reading classifier metadata from audit frontmatter), so any breaking change must bump the version, not silently mutate the shape.
