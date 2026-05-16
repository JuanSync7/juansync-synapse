# Fixture — style-voice-anchors

Style sub-type; 4 voice anchors. Tests T5 / O9: rewrite must match anchor cadence and diction without paraphrasing or quoting anchors into the output.

## Kept Claims (input)

```yaml
kept_claims:
  - id: stl00001
    heading_anchor: voice
    text: "Use short, declarative sentences."
    source_lines: [3, 3]
  - id: stl00002
    heading_anchor: voice
    text: "Address the reader in second person."
    source_lines: [4, 4]
  - id: stl00003
    heading_anchor: voice
    text: "Avoid hedging adverbs like 'perhaps' or 'somewhat'."
    source_lines: [5, 5]
  - id: stl00004
    heading_anchor: structure
    text: "Lead with the conclusion; supporting detail follows."
    source_lines: [9, 9]
  - id: stl00005
    heading_anchor: structure
    text: "One idea per paragraph."
    source_lines: [10, 10]
```

## Original Doc (input)

```markdown
# Writing Style Guide

## Voice
- Use short, declarative sentences whenever you can. Reserve long sentences for parallel structures that genuinely need them.
- Address the reader in second person. "You do X" is direct; "The reader does X" is distant.
- Avoid hedging adverbs like "perhaps" or "somewhat" — if you mean it, say it without softening.

## Structure
- Lead with the conclusion. Supporting detail follows the claim, not the other way around.
- One idea per paragraph. If a paragraph carries two ideas, split it.
- Headings are signposts, not summaries.
```

## Voice Anchors (input)

```yaml
voice_anchors:
  - "Ship the thing."
  - "You decide; nobody else can."
  - "Clarity beats elegance every time."
  - "Cut the qualifier and try again."
```

## Expected Behavior

- Output is `{ rewritten_doc: <string> }`.
- All headings preserved: `# Writing Style Guide`, `## Voice`, `## Structure`.
- All 5 kept claims covered (judge dispatch → entailed/partial for each).
- The rewrite reads in a voice that matches the anchors: short sentences, second person, no hedging, imperative posture. The non-kept "Headings are signposts, not summaries" is absent.
- **None** of the 4 voice-anchor sentences appears verbatim or near-verbatim in `rewritten_doc`. Anchors are *how to write*, not *what to write*. If "Ship the thing." or "Cut the qualifier and try again." shows up in the output, the agent has confused voice guidance with content → FAIL O4 / O9.
- Output length ≥ 30% of source length.
