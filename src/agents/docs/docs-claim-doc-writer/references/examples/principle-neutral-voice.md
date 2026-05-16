# Fixture — principle-neutral-voice

Principle sub-type; no voice anchors. Tests T6 / O10: agent must write in neutral expository prose and must NOT synthesize voice anchors of its own.

## Kept Claims (input)

```yaml
kept_claims:
  - id: prn00001
    heading_anchor: data-handling
    text: "User data is encrypted at rest with per-tenant keys."
    source_lines: [3, 3]
  - id: prn00002
    heading_anchor: data-handling
    text: "Per-tenant keys are rotated every 90 days."
    source_lines: [4, 4]
  - id: prn00003
    heading_anchor: access-control
    text: "Production database access requires two-person authorization."
    source_lines: [8, 8]
  - id: prn00004
    heading_anchor: access-control
    text: "Access grants expire automatically after 8 hours."
    source_lines: [9, 9]
```

## Original Doc (input)

```markdown
# Data Handling Principles

## Data Handling
- User data is encrypted at rest with per-tenant keys, isolated per customer account.
- Per-tenant keys are rotated every 90 days as part of the standard key-management lifecycle.
- We do not store payment card numbers; we tokenize via the payment processor.

## Access Control
- Production database access requires two-person authorization through our break-glass tool.
- Access grants expire automatically after 8 hours and require a new request to renew.
- All access events are logged to an append-only audit stream.
```

## Voice Anchors (input)

(absent — principle sub-type does not receive voice anchors)

## Expected Behavior

- Output is `{ rewritten_doc: <string> }`.
- All headings preserved: `# Data Handling Principles`, `## Data Handling`, `## Access Control`.
- All 4 kept claims covered (judge → entailed/partial for each).
- Voice is neutral expository — declarative third-person/passive where natural; no stylistic flourishes the agent might import from training.
- The non-kept claims ("we tokenize via the payment processor", "all access events are logged…") are absent.
- The agent does NOT emit a synthesized voice-anchor block, style commentary, or any meta-content beyond the rewritten document itself.
- Output length ≥ 30% of source length.
