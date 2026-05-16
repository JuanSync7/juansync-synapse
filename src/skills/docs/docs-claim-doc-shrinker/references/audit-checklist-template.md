# Audit Checklist Template

Shape of the per-document checklist written to `.shrink/<file>.audit.md` at the end of the audit phase. The user edits this file between `audit` and `compress`. Verbatim from design doc §4.

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

## Field rules

- `source_path` — relative to repo root.
- `source_hash` — `sha256` of the source file content at audit time. The compress phase recomputes this hash and refuses on mismatch.
- `audit_timestamp` — ISO 8601 UTC.
- `classifier.category` — always `claim-based` (audit cannot complete on any other category) or `mixed` when `--accept-mixed` was passed.
- `schema_version` — `"1"`. Mismatched versions are a loud failure during compress.

## Row marker semantics

| Marker | Meaning | Compress treatment |
|---|---|---|
| `- [x] keep:` | retain claim | feed to writer; verify entailment in judge |
| `- [ ] cut:` | drop claim | not passed to writer |
| `- [m] merge-with <other_id>:` | merge into another kept claim | both ids fed to writer with merge note |

Default for every claim at write time is `- [x] keep`. The user converts to `cut`/`merge` by hand before running compress.

## Headless mode

When run with no human edit step (CI, scripted batch), every row stays `- [x] keep`. The compress phase still runs but becomes a near-no-op against the idempotency delta floor; the shrinker emits an explicit warning that the checklist was not human-audited.
