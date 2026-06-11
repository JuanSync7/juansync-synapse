# horizontal-doc-discovery

Loaded at `[H]`. Horizontal docs (architecture, NFRs, scope) carry cross-cutting constraints the spec alone does not encode. Miss them and stories ship blind to deployment target / security model / latency budget — the orchestrator's worker subagent then writes correct code that violates an unstated invariant. Pick the wrong one when two exist and the plan inherits stale constraints. **Surface, do not resolve.**

## Precedence — halt at first match

| # | Source | Rationale |
|---|---|---|
| 1 | `--horizontal-docs <path>` flag | Explicit user override — never second-guess. |
| 2 | Nearest-ancestor `architecture.md` / NFRs / scope, walking up from the spec's directory | Co-located docs encode the bounded-context invariants of the spec being planned. |
| 3 | Root-level (`./docs/architecture.md`, `./architecture.md`) | Repo-wide defaults when no local override exists. |
| 4 | None found | Emit `WARN: no horizontal doc discovered; constraints derived from spec only` to `STORIES.md` top + each story. Do not block. |

**Halt on first match per tier.** If tier 2 produces an `architecture.md`, do not also fold in tier 3's root-level doc — that silently merges two source-of-truths.

## Standard search paths (per tier)

Check in order within each tier; halt the tier on first hit.

**Tier 1 — explicit flag**
- `<path>` as given (file or directory; if directory, look for `architecture.md`, `NFR.md`, `SCOPE.md` inside).

**Tier 2 — nearest ancestor (walk from spec dir up to repo root)**
- `./architecture.md`, `./NFR.md` / `./NFRs.md`, `./SCOPE.md` / `./scope.md`
- `./docs/architecture.md`, `./docs/NFR.md`, `./docs/SCOPE.md`
- `./docs/architecture/` (directory — read `index.md` or `README.md`)
- `./.delivery/horizontal/` (directory — read all `*.md`)

**Tier 3 — repo root**
- `/<repo>/docs/architecture.md`, `/<repo>/architecture.md`
- `/<repo>/docs/architecture/`, `/<repo>/.delivery/horizontal/`

## Reading `foundations: [...]` — structural, not heading-scrape

`architecture.md` MUST be read via YAML frontmatter parse. The field is:

```yaml
---
foundations: [auth, db, logger, feature-flags]
---
```

Read `frontmatter["foundations"]` as a list. **Never grep for `## Foundations` or `## Substrate` headings** — those names drift across repos (`## Bedrock`, `## Platform`, `## Core Services` all mean the same thing) and a missed rename silently downgrades the foundation cascade to tier 3 inference. If the frontmatter field is absent, treat as "architecture doc found but no declared foundations" — pass through to `[F]` cascade tier 3 (commonality heuristic).

## Conflict detection — what counts

A **conflict** = the spec asserts X and a horizontal doc asserts Y, where X and Y are mutually exclusive on the **same concern**. The concerns to scan:

- **Latency / throughput targets** (spec: "p99 < 100ms"; NFR: "p99 < 50ms")
- **Security model** (spec: "JWT bearer"; architecture: "mTLS only inside cluster")
- **Data-flow direction** (spec: "service calls DB direct"; architecture: "all writes via event bus")
- **Deployment target** (spec: "deploy as Lambda"; architecture: "container-only, no FaaS")
- **Persistence engine** (spec: "store in Redis"; architecture: "Postgres is system of record")
- **Auth boundary** (spec: "anonymous endpoint"; NFR: "all endpoints authenticated")

Difference without contradiction is **not** a conflict (spec adds detail the horizontal doc does not name). Conflict requires both docs to take a stance on the same concern and disagree.

## Serialization — `CONFLICT` block (literal shape)

Emit inline in the affected story's `Constraints` section, verbatim:

```
CONFLICT: <concern>
  spec        : <verbatim spec assertion>          (source: <spec path>:<line>)
  horizontal  : <verbatim horizontal assertion>    (source: <doc path>:<line>)
  resolution  : UNRESOLVED — planner did not pick. Surface to user before slice dispatch.
```

Also emit a top-level warning in `STORIES.md` frontmatter:

```yaml
conflicts:
  - story: TAG-NNN
    concern: <concern>
    spec_source: <path>:<line>
    horizontal_source: <path>:<line>
```

**Never silently pick one.** The planner's job is to make the contradiction loud enough that `[END]` surfaces it and the user resolves before handing the manifest to the orchestrator.
