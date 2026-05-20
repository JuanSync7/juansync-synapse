# Audit checklist file template

Verbatim shape from design doc §4. The `audit` subcommand writes this file to `.shrink/<path>.audit.md`. The `compress` subcommand reads it and refuses if missing or if `source_hash` no longer matches the live source.

```markdown
---
source_path: <relative-path>
source_hash: <sha256-of-source-content>
audit_timestamp: <iso8601>
classifier:
  category: claim-based
  sub_type: identity
schema_version: "1"
---

## <Section Heading from source>
- [x] keep: <claim_id> — <claim text>
- [ ] cut:  <claim_id> — <claim text>
- [m] merge-with <other_id>: <claim_id> — <claim text>

## Contradictions
- (<id_a> ↔ <id_b>): <reason>

## Redundancies
- (<id_a> ≈ <id_b>): similarity <score>
```

## Marker semantics

| Marker | Meaning | Compress behavior |
|---|---|---|
| `[x]` | keep | claim is included in `kept_claims` passed to writer |
| `[ ]` | cut | claim is excluded; not verified by judge |
| `[m]` | merge | claim is kept; writer should fuse with the linked `other_id` claim |

## Default-keep-all (headless mode)

If no human edits the checklist before `compress`, every claim defaults to `[x] keep`. This produces a near-no-op compress. The skill MUST emit a warning in headless mode — silent compression without a human edit step violates P2.
