# Fixture — leakage-temptation

Principle sub-type; no voice anchors. Tests T2: no extra-claim leakage even when an "obvious connecting context" sentence is tempting.

## Kept Claims (input)

```yaml
kept_claims:
  - id: 11112222
    heading_anchor: review-policy
    text: "Every pull request requires one human reviewer before merge."
    source_lines: [3, 3]
  - id: 22223333
    heading_anchor: review-policy
    text: "Reviewers must read every file in the diff."
    source_lines: [4, 4]
  - id: 33334444
    heading_anchor: merge-policy
    text: "Merges to main are blocked until CI passes."
    source_lines: [8, 8]
  - id: 44445555
    heading_anchor: merge-policy
    text: "Squash-merge is the default; merge commits require justification."
    source_lines: [9, 9]
```

## Original Doc (input)

```markdown
# Review and Merge Policy

## Review Policy
- Every pull request requires one human reviewer before merge.
- Reviewers must read every file in the diff and acknowledge each one.
- LGTM is not a substitute for a real read.

## Merge Policy
- Merges to main are blocked until CI passes (lint, type, tests).
- Squash-merge is the default; merge commits require justification in the PR description.
- Force-push to main is permanently disabled.
```

## Voice Anchors (input)

(absent)

## Expected Behavior

- Output is `{ rewritten_doc: <string> }`.
- All headings (`# Review and Merge Policy`, `## Review Policy`, `## Merge Policy`) present in order.
- The 4 kept claims are covered.
- The tempting "natural connecting context" sentences that are NOT in the kept set MUST be absent:
  - "LGTM is not a substitute for a real read." (omitted from kept set on purpose)
  - "Force-push to main is permanently disabled." (omitted on purpose)
  - Any agent-invented bridge like "This two-stage policy ensures quality" → FAIL O4.
- If the agent introduces any of these, the writer's no-leakage contract is broken — the judge cannot catch it because the judge only verifies claims that are *in* the input set.
