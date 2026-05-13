# Protocol Skeleton

Fill in this skeleton when drafting a new protocol. Delete the Configuration section if the protocol has no modes.

---

```markdown
---
name: <protocol-name>
description: "<trigger/routing contract — when this protocol fires, not a workflow summary>"
domain: <pick from PROTOCOL_TAXONOMY.md>
type: <pick from PROTOCOL_TAXONOMY.md>
tags: [<lowercase, hyphenated>]
---

# <Protocol Name>

<One paragraph: WHY this protocol exists. What behavioral gap it fills. What goes wrong without it. Zero-overhead — only active when injected.>

## Contract

<Imperative rules. Every instruction:
- Uses commitment language (MUST/NEVER/STOP/BEFORE/AFTER/THEN/DO NOT)
- Names a specific trigger moment (not "when appropriate")
- Contains no weak signal words (consider, may want to, ideally, generally)
- Either defines a trigger, states a constraint, or specifies an output format>

## Failure Assertion

If [precondition] is not met, STOP and output:
`PROTOCOL FAILURE: <protocol-name> — [specific reason describing what precondition failed]`

## Configuration
<!-- Optional — only if protocol has modes (e.g., shallow/deep, strict/lenient).
     Each mode must have a default. Delete this section if not needed. -->

| Mode | Behavior | Default |
|------|----------|---------|
| `<mode-name>` | <what changes> | <yes/no> |
```
