# Wrong-Tool Redirects

Source of the Wrong-Tool Detection block in SKILL.md. The shrinker's contract — lossless density increase against a kept-claim set — is meaningful only for claim-based docs. Verbatim from design doc §8.

```markdown
## Wrong-Tool Detection
- Target is a **SKILL.md** → use `synapse-skill-skill-improver`
- Target is **narrative prose** (essays, blog posts, articles) → manual rewrite; claim-coverage destroys voice
- Target is **reference doc** (API, glossary) → completeness is the goal, not density
- Target is a **template** → already structural
- User wants **lossy summary / TL;DR** → general LLM rewrite; this skill is lossless on kept claims only
```

## Why each redirect

| Doc type | Why claim-coverage fails | Right tool |
|---|---|---|
| SKILL.md | Skills have their own structural eval loop. The shrinker would re-densify already-tuned prose and break flow-graph patterns. | `synapse-skill-skill-improver` runs the score-fix loop against an existing EVAL.md. |
| Narrative prose | Voice and pacing matter more than claim density. Atomic-claim extraction shreds the prose. | Manual rewrite. |
| Reference doc | An API table or glossary loses value when entries are merged. Completeness > density. | Manual rewrite. |
| Template | Structural placeholders are not claims. Extraction yields garbage. | No rewrite needed. |
| Lossy summary | The shrinker preserves every kept claim; a TL;DR drops claims by design. | A general-purpose LLM rewrite. |

The classifier enforces these redirects automatically — the shrinker never relies on the user to pick the right tool.
