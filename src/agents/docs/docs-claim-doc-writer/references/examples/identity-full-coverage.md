# Fixture — identity-full-coverage

Identity sub-type; no voice anchors. Tests T1: full coverage, all headings preserved.

## Kept Claims (input)

```yaml
kept_claims:
  - id: a1b2c3d4
    heading_anchor: who-i-am
    text: "Synapse is a composable library of agentic artifacts."
    source_lines: [3, 3]
  - id: b2c3d4e5
    heading_anchor: who-i-am
    text: "Synapse's unit of distribution is a versioned skill, agent, protocol, or tool."
    source_lines: [4, 4]
  - id: c3d4e5f6
    heading_anchor: who-i-am
    text: "Synapse is authored once and adopted by multiple harnesses."
    source_lines: [5, 5]
  - id: d4e5f6a7
    heading_anchor: what-i-value
    text: "Synapse values determinism over cleverness."
    source_lines: [8, 8]
  - id: e5f6a7b8
    heading_anchor: what-i-value
    text: "Synapse values loud failure over silent drift."
    source_lines: [9, 9]
  - id: f6a7b8c9
    heading_anchor: what-i-refuse
    text: "Synapse does not silently rewrite source files."
    source_lines: [13, 13]
```

## Original Doc (input)

```markdown
# Synapse Identity

## Who I am
- Synapse is a composable library of agentic artifacts that other AI coding harnesses adopt and run.
- The unit of distribution is a versioned skill, agent, protocol, or tool — each one self-contained.
- Synapse is authored once and adopted by multiple harnesses (Claude Code, Codex CLI, Gemini CLI).

## What I value
- Determinism over cleverness — predictable behavior beats elegant-but-surprising behavior every time.
- Loud failure over silent drift — when an invariant breaks, you should hear about it immediately.
- Composition over monoliths.

## What I refuse
- I do not silently rewrite source files; every mutation is audited and reversible.
- I do not promote unreviewed artifacts to stable.
```

## Voice Anchors (input)

(absent — identity sub-type does not receive voice anchors)

## Expected Behavior

- Output is `{ rewritten_doc: <string> }`.
- All four source headings present, in this exact order and depth:
  1. `# Synapse Identity`
  2. `## Who I am`
  3. `## What I value`
  4. `## What I refuse`
- All 6 kept claims semantically present in the rewrite (judge dispatch over each → `entailed` or `partial`, never `dropped`).
- "Composition over monoliths" (not in kept set) MAY appear if it traces to a kept claim; otherwise must be absent. (It does not trace — so absent.)
- "I do not promote unreviewed artifacts to stable" (not in kept set) must be absent.
- Output length ≥ 30% of source length.
