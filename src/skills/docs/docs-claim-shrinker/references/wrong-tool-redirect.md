# Wrong-tool redirects

Loaded at `[NEW]`. Verbatim from design doc §8. Surface and exit before dispatching any agent.

```markdown
## Wrong-Tool Detection
- Target is a **SKILL.md** → use `synapse-skill-improver`
- Target is **narrative prose** (essays, blog posts, articles) → manual rewrite; claim-coverage destroys voice
- Target is **reference doc** (API, glossary) → completeness is the goal, not density
- Target is a **template** → already structural
- User wants **lossy summary / TL;DR** → general LLM rewrite; this skill is lossless on kept claims only
```

## How redirects are applied

The classifier gate enforces these structurally for the `narrative`, `reference`, `template` cases — the refusal message from §9 #1 names the category and adds the appropriate redirect text. The SKILL.md and TL;DR cases are intent-level and surfaced at `[NEW]` before the classifier runs, since the user's stated goal already disqualifies the skill.
