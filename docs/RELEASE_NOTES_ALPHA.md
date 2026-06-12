# Alpha Release Notes

First tagged alpha of the ai-synapse framework. The scaffolding — install, registries,
governance, taxonomy, validation, pipeline metadata — is stable and enforced; individual
skills vary in maturity (see the `Status` column in `registry/SKILL_REGISTRY.md`).

## Highlights

- **Slug grammar**: `{namespace}-{subdomain?}-{scope}-{role}` — fixed machine-checked
  `scope-role` tail, optional subdomain. Full rationale and iteration history in
  [`wiki/NAMING_RATIONALE.md`](../wiki/NAMING_RATIONALE.md); migration record in
  [`docs/migrations/2026-06-slug-grammar.md`](migrations/2026-06-slug-grammar.md).
- **Aliases**: terse invocation handles (`/brainstorm` → `meta-process-brainstormer`)
  materialized at install with frontmatter rewritten for harness consistency and a
  refuse-to-overwrite collision guard. 14 legacy verb-names seeded as aliases.
- **Persona class**: scaffolded home (`src/skills/persona/`, `PERSONA_TAXONOMY.md`,
  `PERSONA_REGISTRY.md`) for interaction-mode skills with no scope-role signature. Empty
  until the first persona lands.
- **Two-layer validation**: pre-commit hook (changed artifacts) + `./cortex validate`
  (full sweep) — now covering skills, agents, protocols, tools, pathways, and scripts.

## Known limitations (alpha)

1. **Most skills are `draft` status.** Drafts have not passed gatekeeper certification;
   their EVAL.md may be a placeholder (e.g. `hardware-rtl-auditor`). Promotion criteria:
   `GOVERNANCE.md`.
2. **Alias harness behavior verified at install level, not yet in a live harness
   session.** Materialized aliases are self-consistent (dir name == frontmatter name), but
   how each harness's skill list renders the alias+canonical pair (one entry, two entries)
   has not been observed live across Claude Code / Codex / Gemini. If double-listing is
   disruptive in your harness, remove the alias dirs (`cortex clean` + reinstall without
   aliases) and report it.
3. **In-flight work in `src/protocols/delivery/` and `src/skills/delivery/
   delivery-program-orchestrator/`** may show validation errors until that workstream
   merges; it is not part of the framework core.
4. **Windows**: `cortex` and `make` require bash (WSL or Git Bash); native PowerShell
   support is on the roadmap.

## Validation status at tag time

`./cortex validate` runs fully clean: **0 errors, 0 warnings** across skills, agents,
protocols, tools, pathways, scripts, and registries (down from 121 errors at the start of
the pre-alpha debt cleanup — script frontmatter, `src/tools/testing/` suite conformance,
`*.eval.md` companion misdetection, and a stale external-suite registry row).
