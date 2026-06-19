# Persona Taxonomy

Naming and metadata rules for **persona / mode skills** — skills that present a named interaction
*stance* (a simulated advisor, a session format like "office-hour") rather than a transformation.
They have no `scope-role` function signature, so they do **not** follow
[`SKILL_TAXONOMY.md`](SKILL_TAXONOMY.md).

This class exists so persona skills have a validated home distinct from transformation skills.
**No persona artifacts exist yet** — this is scaffolding for the first one.

## Why a separate class

A transformation skill is graded on *artifact conformance* (did the output doc have the right
sections). A persona is graded on *in-character behavior and advice quality* (did it stay in voice,
was the guidance good, did it ask the questions the real persona would). Different shape, different
quality bar → different class.

## Naming convention

```
persona-{handle}
```

- **`persona`** — required namespace prefix (collision-safe in the flat skills namespace).
- **`handle`** — an evocative, memorable identifier. May be a *persona* (`yc-partner`,
  `staff-engineer`) or an interaction *mode/format* (`office-hour`, `retro`, `stand-up`).

Examples: `persona-office-hour`, `persona-yc-partner`.

## Home

`src/skills/persona/<persona-handle>/SKILL.md`.

## Frontmatter

```yaml
name: persona-<handle>   # must equal directory name
description: <when this persona/mode fires — the routing contract>
class: persona           # marks this as a persona, exempting it from scope/role validation
persona_kind: persona | mode   # who (character) vs. how (interaction format)
tags: [...]
```

`domain/subdomain/scope/role` are **not** required for this class.

## EVAL

Persona EVAL.md grades behavior, not structure: voice consistency, advice quality, and
in-character question-asking. Generated/maintained separately from transformation-skill evals.

## Registry

Listed in [`registry/PERSONA_REGISTRY.md`](../registry/PERSONA_REGISTRY.md).
