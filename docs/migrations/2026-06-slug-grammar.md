# Slug Grammar Migration — June 2026

Status: in progress. Branch: `chore/taxonomy/slug-grammar-migration`.

This is the authoritative reference for the artifact-naming reorganization. Downstream
edits (taxonomy files, vocab, hook, renames, registries, READMEs) all conform to this doc.

## Why

The old rule mandated a fixed four-slot slug `{domain}-{subdomain}-{scope}-{role}` with **all
four slots required**. Two problems surfaced:

1. **`subdomain` was forced even when it carried no signal**, producing doubling
   (`synapse-skill-skill-improver`, `delivery-plan-plan-writer`) and filler (`*-general-*`).
2. **The same concept landed in different slots across domains** — for doc skills `spec` was a
   *subdomain* and `doc` was the *scope*; elsewhere `spec` would be the *scope*. The name and the
   frontmatter disagreed about what the function signature was.

Separately, ~26 `src/skills` carried **legacy verb-first names** (`write-spec-docs`, `brainstorm`,
`patch-docs`) that did not match their own frontmatter (`scope: doc, role: writer`).

## The grammar (new)

```
{namespace}-{subdomain?}-{scope}-{role}
   required     optional    required required
```

- **Fixed tail.** The **last two tokens are always `scope-role`** — the function signature
  (`what it operates on` + `what it is`). Always present, always parseable: split the last two
  tokens off; everything before is namespace.
- **Variable head.** `subdomain` is **optional** — include it *only* when needed to disambiguate
  two artifacts that would otherwise collide on `{namespace}-{scope}-{role}`.
- **`namespace`** (= the `domain` field) is required: it is the collision-safe prefix demanded by
  Claude Code's flat `~/.claude/skills/` namespace. This is why we do **not** adopt bare
  single-verb names (gbrain-style) — ai-synapse is a *shared library*, not a closed runtime.
- **`name:` frontmatter must equal the directory name** and its last two tokens must equal
  `scope`-`role` from frontmatter.

### Classification vs. invocation

The slug carries *enough* structure for a human to read the function at a glance and for the slug
to be globally unique. The **routing contract is the `description` + triggers**, not the slug —
the LLM selects skills by description. The **registry is the queryable index**; the **vocabulary is
the schema**; the **frontmatter is the source of truth** the registry is built from.

### Similarity / dedup rule

`(scope, role)` is the **similarity signature**. Two artifacts sharing a `(scope, role)` pair in
the same namespace are presumptively redundant and must justify coexistence. Because `scope` and
`role` are controlled-vocabulary fields, "is there already a skill like this?" becomes a structured
query: *show every skill where `scope=X` AND `role=Y`*. `synapse-router-artifact-creator` should run
this check before scaffolding (see "Creator pre-check" below).

## Vocabulary reconciliation

**Decision: the document *type* is the `scope`** (a spec-writer operates on a spec). This removes
the `doc` redundancy and makes the name's fixed tail consistent with frontmatter.

New `scope` values added to `registry/SKILL_VOCABULARY.md`:
`spec`, `design`, `architecture`, `implementation`, `engineering-guide`, `postmortem`,
`test-plan`, `coverage`, `claim`, `test`, `build`, `rtl`.

Subdomains that were really *doc-type phases* (`spec`, `design`, `arch`, `impl`, `scope`,
`post-build`) are **demoted** — they move into `scope`, and the name omits the subdomain.

## Persona class (forward-looking)

A 7th artifact class for **persona / mode** skills (e.g. a simulated advisory "office-hour"),
which have **no `scope-role` transformation signature**. They get:
- their own home `src/skills/persona/` (and `persona` namespace prefix),
- a loose naming rule `persona-{handle}` (evocative handle, e.g. `persona-office-hour`),
- their own EVAL bar — graded on **in-character behavior + advice quality**, not artifact
  conformance.

No persona artifacts exist yet; this migration only **stands up the class scaffolding** so the
first one (when it arrives) has a validated home. Trigger to actually populate: ≥1 real persona.

## Rename map (legacy → new)

Conforming artifacts left **unchanged** (names already match frontmatter): all 11 agents, all 3
protocols, the 1 tool, the 6 `synapse/skills/*`, `delivery-orchestration-plan-executor`,
`delivery-plan-plan-writer`.

### docs/  (domain=docs; doc-type promoted to scope)

| old | new | scope | role |
|-----|-----|-------|------|
| write-scope-docs | docs-scope-writer | scope | writer |
| write-architecture-docs | docs-architecture-writer | architecture | writer |
| write-spec-docs | docs-spec-writer | spec | writer |
| write-spec-summary | docs-spec-summarizer | spec | summarizer |
| write-design-docs | docs-design-writer | design | writer |
| write-implementation-docs | docs-implementation-writer | implementation | writer |
| write-engineering-guide | docs-engineering-guide-writer | engineering-guide | writer |
| write-test-docs | docs-test-plan-writer | test-plan | writer |
| write-test-coverage | docs-coverage-writer | coverage | writer |
| write-postmortem | docs-postmortem-writer | postmortem | writer |
| patch-docs | docs-doc-patcher | doc | patcher |
| doc-authoring | docs-doc-router | doc | router |
| docs-claim-doc-shrinker | docs-claim-shrinker | claim | shrinker |

### code/  (domain=code; test family shares scope=test)

| old | new | scope | role |
|-----|-----|-------|------|
| test-lint | code-test-linter | test | linter |
| test-audit | code-test-auditor | test | auditor |
| test-fix | code-test-fixer | test | fixer |
| test-generate | code-test-generator | test | generator |
| test-evaluate | code-test-evaluator | test | evaluator |
| test-integrate | code-test-integrator | test | integrator |
| test-runner | code-test-runner | test | runner |
| write-module-tests | code-test-writer | test | writer |
| build-plan | code-build-planner | build | planner |

### creative / framework / hardware / meta / optimization

| old | new | scope | role |
|-----|-----|-------|------|
| create-animation-page | creative-page-animator | page | animator |
| langgraph-architect | framework-workflow-designer | workflow | designer |
| rtl-design-guard | hardware-rtl-auditor | rtl | auditor |
| brainstorm | meta-process-brainstormer | process | brainstormer |
| auto-research | optimization-process-researcher | process | researcher |

## Ripple checklist per rename

1. `git mv` the skill directory.
2. Update `name:` frontmatter (and `scope:` where reconciled; drop `subdomain:` if not in name).
3. `registry/SKILL_REGISTRY.md` — row link text + path.
4. domain `README.md` — row link text + path (+ Layer Chain diagram for docs).
5. `synapse/SKILLS_REGISTRY.yaml` — `name:` if pipeline-registered.
6. Cross-references: other skills' bodies, `Consumers` columns, pathway YAML, EVAL.md.
7. Top-level docs: `CLAUDE.md`, `README.md`, `GOVERNANCE.md`.

## Callability note — resolved by the alias layer

Structured slugs are less terse than the old verb names (`/brainstorm` →
`/meta-process-brainstormer`). The trade chosen: structure + glance-readability + global
uniqueness in the slug, terseness restored via **aliases** (see SKILL_TAXONOMY.md "Aliases").
`aliases: [brainstorm]` frontmatter → `cortex install` creates one extra symlink per alias with
a refuse-to-overwrite collision guard. Identity model: slug = immutable ID (governance surfaces
only ever use it), alias = mutable @handle (what a human types), description = display name
(what the LLM routes on). The old verb names were seeded as aliases on the 14 most-typed
renamed skills, restoring backward-compatible invocation.

## Two-clone note

`~/juansync-synapse` and `~/ai-synapse` are two checkouts of the same remote
(`JuanSync7/ai-synapse`). Migration is performed once here; the other clone receives it via
`git pull`. Do not hand-edit the second clone.
