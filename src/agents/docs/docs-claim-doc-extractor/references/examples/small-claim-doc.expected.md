# Expected `extractor_output` — small-claim-doc.md

Computed deterministically: `id = sha256(heading_anchor + claim_text)[:8]` (lowercase hex).

```yaml
extractor_output:
  claims:
    - id: "9c6bacb3"
      heading_anchor: "who-i-am"
      text: "I am a composable library of agentic artifacts."
      source_lines: [4, 4]
    - id: "5cfacfe4"
      heading_anchor: "who-i-am"
      text: "My unit of distribution is a versioned skill, agent, protocol, or tool."
      source_lines: [5, 5]
    - id: "cbba9bb5"
      heading_anchor: "what-i-value"
      text: "Determinism over cleverness."
      source_lines: [8, 8]
    - id: "a2385ea5"
      heading_anchor: "what-i-value"
      text: "Loud failure over silent drift."
      source_lines: [9, 9]
    - id: "d076e62e"
      heading_anchor: "what-i-refuse"
      text: "I do not silently rewrite source files."
      source_lines: [12, 12]
    - id: "5a91e3dd"
      heading_anchor: "what-i-refuse"
      text: "I do not promote unreviewed artifacts to stable."
      source_lines: [13, 13]
  contradictions: []
  redundancies: []
```

## ID derivation table (verifier reference)

| Claim | Anchor | Hash input (`anchor + text`) | First 8 hex |
|-------|--------|------------------------------|-------------|
| 1 | `who-i-am` | `who-i-amI am a composable library of agentic artifacts.` | `9c6bacb3` |
| 2 | `who-i-am` | `who-i-amMy unit of distribution is a versioned skill, agent, protocol, or tool.` | `5cfacfe4` |
| 3 | `what-i-value` | `what-i-valueDeterminism over cleverness.` | `cbba9bb5` |
| 4 | `what-i-value` | `what-i-valueLoud failure over silent drift.` | `a2385ea5` |
| 5 | `what-i-refuse` | `what-i-refuseI do not silently rewrite source files.` | `d076e62e` |
| 6 | `what-i-refuse` | `what-i-refuseI do not promote unreviewed artifacts to stable.` | `5a91e3dd` |

A reviewer can reproduce any ID with: `python3 -c 'import hashlib; print(hashlib.sha256(b"<anchor><text>").hexdigest()[:8])'`.
